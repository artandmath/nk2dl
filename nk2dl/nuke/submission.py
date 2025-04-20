"""Nuke script submission to Deadline.

This module provides functionality for submitting Nuke scripts to Deadline render farm.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import re

from ..common.config import config
from ..common.errors import SubmissionError
from ..common.logging import logger
from ..common.framerange import FrameRange
from ..deadline.connection import get_connection


class NukeSubmission:
    """Handles submission of Nuke scripts to Deadline."""

    def __init__(self, 
                script_path: str,
                frame_range: str = "",
                output_path: str = "",
                job_name: Optional[str] = None,
                batch_name: Optional[str] = None,
                priority: Optional[int] = None,
                pool: Optional[str] = None,
                group: Optional[str] = None,
                chunk_size: Optional[int] = None,
                department: Optional[str] = None,
                comment: Optional[str] = None,
                use_nuke_x: bool = False,
                use_batch_mode: bool = True,
                render_threads: Optional[int] = None,
                use_gpu: bool = False,
                gpu_override: Optional[str] = None,
                max_ram_usage: Optional[int] = None,
                enforce_render_order: bool = True,
                min_stack_size: Optional[int] = None,
                continue_on_error: bool = False,
                reload_plugins: bool = False,
                use_profiler: bool = False,
                profile_dir: Optional[str] = None,
                use_proxy: bool = False,
                write_nodes: Optional[List[str]] = None,
                render_mode: str = "full",
                render_order_dependencies: bool = False,
                job_dependencies: Optional[str] = None,
                write_nodes_as_tasks: bool = False,
                use_nodes_frame_list: bool = False,
                script_is_open: bool = False):
        """Initialize a Nuke script submission.
        
        Args:
            script_path: Path to the Nuke script (.nk file)
            frame_range: Frame range to render (e.g. "1-100", "f-l")
            output_path: Override for output path
            job_name: Custom job name or template with tokens
            batch_name: Batch name for grouping jobs
            priority: Job priority (0-100)
            pool: Deadline pool
            group: Deadline group
            chunk_size: Number of frames per task
            department: Department name
            comment: Job comment
            use_nuke_x: Whether to use NukeX for rendering
            use_batch_mode: Whether to use batch mode
            render_threads: Number of threads to use
            use_gpu: Whether to use GPU for rendering
            gpu_override: Specific GPU to use
            max_ram_usage: Maximum RAM usage in MB
            enforce_render_order: Whether to enforce write node render order
            min_stack_size: Minimum stack size in MB
            continue_on_error: Whether to continue rendering on error
            reload_plugins: Whether to reload plugins between tasks
            use_profiler: Whether to use performance profiler
            profile_dir: Directory for performance profile output
            use_proxy: Whether to use proxy mode
            write_nodes: List of write nodes to render
            render_mode: Render mode (full, proxy)
            render_order_dependencies: Whether to create dependencies based on write node render order
            job_dependencies: Comma or space delimited job IDs to add as dependencies
            write_nodes_as_tasks: Whether to submit write nodes as separate tasks for the same job
            use_nodes_frame_list: Whether to use the frame range defined in write nodes with use_limit enabled
            script_is_open: Whether the script is already open in the current Nuke session
        """
        # Validate that render_order_dependencies and write_nodes_as_tasks are not both True
        if render_order_dependencies and write_nodes_as_tasks:
            raise SubmissionError("Cannot use both dependencies and write nodes as tasks features simultaneously")
        
        # Check if write_nodes_as_tasks is enabled with a custom frame range but use_nodes_frame_list is disabled
        if write_nodes_as_tasks and frame_range and not use_nodes_frame_list and not frame_range.lower() in ['f-l', 'first-last', 'f', 'l', 'first', 'last', 'i', 'input', 'h', 'hero']:
            raise SubmissionError("Custom frame list is not supported when submitting write nodes as separate tasks. "
                                 "Please use global (f-l) or input (i) frame ranges, or enable use_nodes_frame_list.")
            
        # Check if we're running inside Nuke - this is required
        self._ensure_nuke_available()
            
        self.script_path = Path(script_path)
        if not self.script_path.exists():
            raise SubmissionError(f"Nuke script does not exist: {script_path}")
            
        self.frame_range = frame_range
        self.output_path = output_path
        
        # Get default values from config
        self.priority = priority if priority is not None else config.get('submission.priority', 50)
        self.pool = pool if pool is not None else config.get('submission.pool', 'nuke')
        self.group = group if group is not None else config.get('submission.group', 'none')
        self.chunk_size = chunk_size if chunk_size is not None else config.get('submission.chunk_size', 10)
        
        # Optional job properties
        # Store the script filename (with extension) for token replacement
        self.script_filename = self.script_path.name
        self.script_stem = self.script_path.stem
        
        # Store the batch_name template for later processing
        self.batch_name_template = batch_name if batch_name else config.get('submission.batch_name_template', "{stem}")
        # Process batch name tokens first (since job name might depend on batch name)
        self.batch_name = self._replace_batch_name_tokens(self.batch_name_template)
        
        self.department = department if department is not None else config.get('submission.department')
        self.comment = comment if comment is not None else config.get('submission.comment')
        
        # Store the job_name template for later processing
        self.job_name_template = job_name if job_name else config.get('submission.job_name_template', "{batch} / {write} / {file}")
        
        # Nuke-specific options
        self.use_nuke_x = use_nuke_x if isinstance(use_nuke_x, bool) else config.get('submission.use_nuke_x', False)
        self.use_batch_mode = use_batch_mode if isinstance(use_batch_mode, bool) else config.get('submission.use_batch_mode', True)
        self.render_threads = render_threads if render_threads is not None else config.get('submission.render_threads')
        self.use_gpu = use_gpu if isinstance(use_gpu, bool) else config.get('submission.use_gpu', False)
        self.gpu_override = gpu_override if gpu_override is not None else config.get('submission.gpu_override')
        self.max_ram_usage = max_ram_usage if max_ram_usage is not None else config.get('submission.max_ram_usage')
        self.enforce_render_order = enforce_render_order if isinstance(enforce_render_order, bool) else config.get('submission.enforce_render_order', True)
        self.min_stack_size = min_stack_size if min_stack_size is not None else config.get('submission.min_stack_size')
        self.continue_on_error = continue_on_error if isinstance(continue_on_error, bool) else config.get('submission.continue_on_error', False)
        self.reload_plugins = reload_plugins if isinstance(reload_plugins, bool) else config.get('submission.reload_plugins', False)
        self.use_profiler = use_profiler if isinstance(use_profiler, bool) else config.get('submission.use_profiler', False)
        self.profile_dir = profile_dir if profile_dir is not None else config.get('submission.profile_dir')
        self.use_proxy = use_proxy if isinstance(use_proxy, bool) else config.get('submission.use_proxy', False)
        self.write_nodes = write_nodes
        self.render_mode = render_mode if render_mode else config.get('submission.render_mode', 'full')
        self.render_order_dependencies = render_order_dependencies if isinstance(render_order_dependencies, bool) else config.get('submission.render_order_dependencies', False)
        self.job_dependencies = job_dependencies
        self.write_nodes_as_tasks = write_nodes_as_tasks if isinstance(write_nodes_as_tasks, bool) else config.get('submission.write_nodes_as_tasks', False)
        self.use_nodes_frame_list = use_nodes_frame_list if isinstance(use_nodes_frame_list, bool) else config.get('submission.use_nodes_frame_list', False)
        self.script_is_open = script_is_open
        
        # Initialize frame range
        if frame_range:
            self.fr = FrameRange(frame_range)
            # If frame range contains tokens, try to substitute them
            if self.fr.has_tokens:
                try:
                    # For input token, we need to specify the write node
                    if 'i' in frame_range or 'input' in frame_range:
                        if write_nodes and len(write_nodes) == 1:
                            self._get_frame_range_from_nuke(write_nodes[0])
                        else:
                            # Can't determine input frame range without a specific write node
                            raise SubmissionError("The 'i/input' token requires exactly one write node to be specified")
                    else:
                        self._get_frame_range_from_nuke()
                except Exception as e:
                    logger.warning(f"Failed to substitute frame range tokens: {e}")
                    
            # Validate frame range syntax
            if not self.fr.is_valid_syntax():
                raise SubmissionError(f"Invalid frame range syntax: {frame_range}")
        else:
            # Get frame range from Nuke script
            self._get_frame_range_from_nuke()
        
        # For job_name we'll do the replacement later when we have access to more information

    def _replace_job_name_tokens(self, template: str, write_node: Optional[str] = None) -> str:
        """Replace tokens in job name template.
        
        Supported tokens:
        - {stem}, {basestem}, {base_stem}: Script name without extension
        - {s}, {nk}, {script}, {scriptname}, {script_name}, {nukescript}, {nuke_script}: Full script name with extension
        - {b}, {bn}, {batch}, {batchname}, {batch_name}: Batch name
        - {w}, {wn}, {writenode}, {write}, {write_node}, {write_name}: Write node name
        - {o}, {fn}, {file}, {filename}, {file_name}, {output}: Output filename
        - {r}, {ro}, {renderorder}, {render_order}: Render order
        - {x}, {f}, {fr}, {range}, {framerange}: Frame range

        Args:
            template: Job name template with tokens
            write_node: Specific write node to use for token replacement

        Returns:
            Job name with tokens replaced
        """
        import nuke
        
        # Start with the template
        job_name = template
        
        # Batch name tokens
        batch_name_tokens = ["{b}", "{bn}", "{batch}", "{batchname}", "{batch_name}"]
        for token in batch_name_tokens:
            job_name = job_name.replace(token, self.batch_name)
            
        # Script stem tokens (without extension)
        stem_tokens = ["{stem}", "{basestem}", "{base_stem}"]
        for token in stem_tokens:
            job_name = job_name.replace(token, self.script_stem)
        
        # Full script name tokens (with extension)
        script_name_tokens = ["{s}", "{nk}", "{script}", "{scriptname}", "{script_name}", "{nukescript}", "{nuke_script}"]
        for token in script_name_tokens:
            job_name = job_name.replace(token, self.script_filename)
        
        # Frame range tokens
        frame_range_tokens = ["{x}", "{f}", "{fr}", "{range}", "{framerange}"]
        for token in frame_range_tokens:
            job_name = job_name.replace(token, self.frame_range)
            
        # If we have a specific write node, we can replace write node related tokens
        if write_node:
            node = nuke.toNode(write_node)
            if node and node.Class() == "Write":
                # Write node name tokens
                write_node_tokens = ["{w}", "{wn}", "{write}", "{writenode}", "{write_node}", "{write_name}"]
                for token in write_node_tokens:
                    job_name = job_name.replace(token, write_node)
                
                # Render order tokens
                render_order = "0"
                if 'render_order' in node.knobs():
                    render_order = str(int(node['render_order'].value()))
                
                render_order_tokens = ["{r}", "{ro}", "{renderorder}", "{render_order}"]
                for token in render_order_tokens:
                    job_name = job_name.replace(token, render_order)
                
                # Output filename tokens
                output_file = ""
                try:
                    # Try to get the node's file path
                    if 'file' in node.knobs():
                        # Evaluate the file knob to get the actual path
                        output_file = node['file'].evaluate()
                        # Get just the filename without the directory path
                        output_filename = os.path.basename(output_file)
                        
                        output_tokens = ["{o}", "{fn}", "{file}", "{filename}", "{file_name}", "{output}"]
                        for token in output_tokens:
                            job_name = job_name.replace(token, output_filename)
                except:
                    logger.warning(f"Failed to get output filename for write node {write_node}")
        
        return job_name

    def _replace_batch_name_tokens(self, template: str) -> str:
        """Replace tokens in batch name template.
        
        Supported tokens:
        - {stem}, {basestem}, {base_stem}: Script name without extension (e.g., 'renderWithDeadline_v001')
        - {s}, {nk}, {script}, {scriptname}, {script_name}, {nukescript}, {nuke_script}: Full script name with extension (e.g., 'renderWithDeadline_v001.nk')

        Args:
            template: Batch name template with tokens

        Returns:
            Batch name with tokens replaced
        """
        # Start with the template
        batch_name = template
        
        # Script stem tokens (without extension)
        stem_tokens = ["{stem}", "{basestem}", "{base_stem}"]
        for token in stem_tokens:
            batch_name = batch_name.replace(token, self.script_stem)
        
        # Full script name tokens (with extension)
        script_name_tokens = ["{s}", "{nk}", "{script}", "{scriptname}", "{script_name}", "{nukescript}", "{nuke_script}"]
        for token in script_name_tokens:
            batch_name = batch_name.replace(token, self.script_filename)
        
        return batch_name

    def _ensure_nuke_available(self) -> None:
        """Ensure that Nuke API is available.
        
        Raises:
            SubmissionError: If Nuke API is not available
        """
        try:
            import nuke
        except (ImportError, ModuleNotFoundError):
            raise SubmissionError(f"Module '{__name__}' must be run from within Nuke or nuke should be available in the system path. "
                                  f"The Nuke Python API is required.")
    
    def _get_frame_range_from_nuke(self, write_node_name: Optional[str] = None) -> None:
        """Get frame range from Nuke script using Nuke API.
        
        Args:
            write_node_name: Optional name of a write node for 'input' token
        """
        import nuke
        
        try:
            if not self.script_is_open:
                # Open the script
                nuke.scriptOpen(str(self.script_path.absolute()))
            
            # Use token substitution with the write node if specified
            if self.fr.has_tokens:
                self.fr.substitute_tokens_from_nuke(write_node_name)
                self.frame_range = str(self.fr)
            else:
                # Get frame range from root
                root = nuke.root()
                first_frame = int(root['first_frame'].value())
                last_frame = int(root['last_frame'].value())
                
                self.frame_range = f"{first_frame}-{last_frame}"
                self.fr = FrameRange(self.frame_range)
            
            logger.debug(f"Got frame range from Nuke API: {self.frame_range}")
        except Exception as e:
            raise SubmissionError(f"Failed to get frame range from Nuke API: {e}")
    
    def prepare_job_info(self) -> Dict[str, Any]:
        """Prepare job information for Deadline submission.
        
        Returns:
            Dictionary containing job information
        """
        # Process job_name with tokens if it's for a specific write node
        if self.write_nodes and len(self.write_nodes) == 1:
            self.job_name = self._replace_job_name_tokens(self.job_name_template, self.write_nodes[0])
        else:
            self.job_name = self._replace_job_name_tokens(self.job_name_template)
            
        job_info = {
            "Name": self.job_name,
            "Plugin": "Nuke",
            "Frames": self.frame_range,
            "ChunkSize": self.chunk_size,
            "Pool": self.pool,
            "Group": self.group,
            "Priority": self.priority
        }
        
        # Add optional fields if specified
        if self.batch_name:
            job_info["BatchName"] = self.batch_name
        if self.department:
            job_info["Department"] = self.department
        if self.comment:
            job_info["Comment"] = self.comment
            
        # If using write nodes as tasks, set special frame range
        if self.write_nodes_as_tasks and self.write_nodes:
            # When using write nodes as tasks, frames should be 0 to (number of write nodes - 1)
            job_info["Frames"] = f"0-{len(self.write_nodes) - 1}"
            
            # Set chunk size to 1 to ensure each task processes one write node
            job_info["ChunkSize"] = 1
        
        # Add user-specified job dependencies if any
        if self.job_dependencies:
            # Parse dependencies (can be comma or space separated)
            dep_list = re.split(r'[,\s]+', self.job_dependencies.strip())
            
            # Add each dependency with proper indexing
            for i, dep_id in enumerate(dep_list):
                if dep_id:  # Skip empty strings
                    job_info[f"JobDependency{i}"] = dep_id
        
        return job_info
    
    def get_nuke_version(self) -> str:
        """Get the current Nuke version.
        
        Returns:
            Version string in format "MAJOR.MINOR" (e.g. "13.0")
        """
        import nuke
        major = nuke.NUKE_VERSION_MAJOR
        minor = nuke.NUKE_VERSION_MINOR
        return f"{major}.{minor}"
    
    def prepare_plugin_info(self) -> Dict[str, Any]:
        """Prepare plugin information for Deadline submission.
        
        Returns:
            Dictionary containing plugin information
        """
        plugin_info = {
            "SceneFile": str(self.script_path.absolute()),
            "Version": self.get_nuke_version(),
            "UseNukeX": "1" if self.use_nuke_x else "0",
            "BatchMode": "1" if self.use_batch_mode else "0",
            "EnforceRenderOrder": "1" if self.enforce_render_order else "0",
            "ContinueOnError": "1" if self.continue_on_error else "0",
            "RenderMode": self.render_mode.capitalize()
        }
        
        # Add optional plugin settings
        if self.render_threads is not None:
            plugin_info["NukeThreadLimit"] = str(self.render_threads)
        if self.use_gpu:
            plugin_info["UseGpu"] = "1"
        if self.gpu_override:
            plugin_info["GpuOverride"] = self.gpu_override
        if self.max_ram_usage is not None:
            plugin_info["RamUse"] = str(self.max_ram_usage)
        if self.min_stack_size is not None:
            plugin_info["StackSize"] = str(self.min_stack_size)
        if self.reload_plugins:
            plugin_info["ReloadPlugins"] = "1"
        if self.use_profiler:
            plugin_info["PerformanceProfiler"] = "1"
            if self.profile_dir:
                plugin_info["PerformanceProfilerDir"] = self.profile_dir
        if self.use_proxy:
            plugin_info["UseProxy"] = "1"
        
        # Handle write nodes differently based on submission mode
        if self.write_nodes_as_tasks and self.write_nodes:
            # Use WriteNodesAsSeparateJobs instead of WriteNodesAsSeparateTasks to match Thinkbox naming
            plugin_info["WriteNodesAsSeparateJobs"] = "True"
            
            # Get write node frame ranges
            write_node_info = self._get_write_node_frame_ranges()
            
            # Add write node info to plugin info
            for i, (node_name, start_frame, end_frame) in enumerate(write_node_info):
                plugin_info[f"WriteNode{i}"] = node_name
                
                # If using node's frame list
                if self.use_nodes_frame_list:
                    plugin_info[f"WriteNode{i}StartFrame"] = str(start_frame)
                    plugin_info[f"WriteNode{i}EndFrame"] = str(end_frame)
                else:
                    # When not using node's frame list, use 0 for start and end frames like Thinkbox does
                    plugin_info[f"WriteNode{i}StartFrame"] = "0"
                    plugin_info[f"WriteNode{i}EndFrame"] = "0"
                
            # If using node's frame list, set the flag in plugin info
            if self.use_nodes_frame_list:
                plugin_info["UseNodeFrameList"] = "1"
        elif self.write_nodes and not self.render_order_dependencies:
            # For regular submission with specific write nodes
            plugin_info["WriteNodes"] = ",".join(self.write_nodes)
            
        if self.output_path:
            plugin_info["OutputFilePath"] = self.output_path
            
        return plugin_info
    
    def _get_write_node_frame_ranges(self) -> List[Tuple[str, int, int]]:
        """Get frame ranges for each write node using Nuke API.
        
        Returns:
            List of tuples (node_name, start_frame, end_frame)
        """
        import nuke
        
        write_node_info = []
        
        # Parse frame range to get default start and end frames
        if '-' in self.frame_range:
            parts = self.frame_range.split('-')
            try:
                default_start = int(parts[0])
                default_end = int(parts[1])
            except (ValueError, IndexError):
                # If parsing fails, use reasonable defaults
                default_start = 1
                default_end = 100
        else:
            try:
                # Single frame case
                default_start = default_end = int(self.frame_range)
            except ValueError:
                # If parsing fails, use reasonable defaults
                default_start = 1
                default_end = 100
        
        try:
            # If the script is not currently open, we need to open it
            if not self.script_is_open:
                # Open the script
                nuke.scriptOpen(str(self.script_path.absolute()))
            
            # Get write nodes by render order
            write_nodes_by_order = self._get_write_nodes_by_render_order()
            
            # Flatten the list of write nodes
            all_write_nodes = []
            for render_order in sorted(write_nodes_by_order.keys()):
                all_write_nodes.extend(write_nodes_by_order[render_order])
            
            # For each write node, extract its frame range
            for node_name in all_write_nodes:
                node = nuke.toNode(node_name)
                if node and node.Class() == "Write":
                    # Check if we should use the node's frame range
                    if self.use_nodes_frame_list and 'use_limit' in node.knobs() and node['use_limit'].value():
                        # Get node's frame range from knobs
                        if 'first' in node.knobs() and 'last' in node.knobs():
                            node_start = int(node['first'].value())
                            node_end = int(node['last'].value())
                            write_node_info.append((node_name, node_start, node_end))
                            continue
                    # If not using node's frame range, try to get input frame range
                    elif re.search(r'\b(i|input)\b', self.frame_range):
                        try:
                            # Get frame range from input
                            node_start = node.firstFrame()
                            node_end = node.lastFrame()
                            write_node_info.append((node_name, node_start, node_end))
                            continue
                        except:
                            # If we can't get input range, fall back to defaults
                            pass
                
                # Fall back to default frame range
                write_node_info.append((node_name, default_start, default_end))
            
            return write_node_info
        except Exception as e:
            raise SubmissionError(f"Failed to get write node frame ranges: {e}")
    
    def _get_write_nodes_by_render_order(self) -> Dict[int, List[str]]:
        """Get write nodes grouped by render order using Nuke API.
        
        Returns:
            Dictionary mapping render orders to lists of write node names
        """
        import nuke
        
        write_nodes_by_order = {}
        
        try:
            # If the script is not currently open, we need to open it
            if not self.script_is_open:
                # Open the script
                nuke.scriptOpen(str(self.script_path.absolute()))
            
            # Find all Write nodes
            for node in nuke.allNodes('Write'):
                node_name = node.name()
                
                # Get render order, default to 0
                render_order = 0
                if 'render_order' in node.knobs():
                    render_order = int(node['render_order'].value())
                
                # Add to dictionary
                if render_order not in write_nodes_by_order:
                    write_nodes_by_order[render_order] = []
                write_nodes_by_order[render_order].append(node_name)
            
            # If we're filtering to specific write nodes, only keep those
            if self.write_nodes:
                write_nodes_set = set(self.write_nodes)
                for order in list(write_nodes_by_order.keys()):
                    write_nodes_by_order[order] = [
                        node for node in write_nodes_by_order[order] 
                        if node in write_nodes_set
                    ]
                    # Remove empty lists
                    if not write_nodes_by_order[order]:
                        del write_nodes_by_order[order]
            
            return write_nodes_by_order
        except Exception as e:
            raise SubmissionError(f"Failed to get write nodes by render order: {e}")    
    
    def submit(self) -> str:
        """Submit the Nuke script to Deadline.
        
        Returns:
            Job ID of the submitted job
            
        Raises:
            SubmissionError: If submission fails
        """
        try:
            # Prepare job and plugin information
            job_info = self.prepare_job_info()
            plugin_info = self.prepare_plugin_info()
            
            # Get Deadline connection
            deadline = get_connection()
            
            # If using write nodes as tasks
            if self.write_nodes_as_tasks and self.write_nodes and len(self.write_nodes) > 1:
                # Handle submission with write nodes as tasks
                # Submit as a single job
                job_id = deadline.submit_job(job_info, plugin_info)
                logger.info(f"Job submitted with write nodes as tasks. Job ID: {job_id}")
                return job_id
            
            # If using dependencies and we need to handle write nodes with different render orders
            elif self.render_order_dependencies and self.write_nodes and len(self.write_nodes) > 1:
                # Parse the Nuke script for write nodes and their render orders
                write_nodes_by_order = self._get_write_nodes_by_render_order()
                
                # Get write node frame ranges if use_nodes_frame_list is enabled
                write_node_frames = {}
                if self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range):
                    write_node_info = self._get_write_node_frame_ranges()
                    for node_name, start_frame, end_frame in write_node_info:
                        write_node_frames[node_name] = (start_frame, end_frame)
                
                # Process in ascending render order
                previous_job_ids = []
                job_id = None
                
                # Count existing dependencies from the user-specified ones
                dependency_count = 0
                if self.job_dependencies:
                    dependency_count = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
                
                for render_order in sorted(write_nodes_by_order.keys()):
                    current_job_ids = []
                    
                    # Submit each node in this render order group
                    for write_node in write_nodes_by_order[render_order]:
                        # Clone job info for this write node
                        node_job_info = job_info.copy()
                        node_plugin_info = plugin_info.copy()
                        
                        # Update job name to include write node
                        node_job_info["Name"] = self._replace_job_name_tokens(self.job_name_template, write_node)
                        
                        # Specify which write node to render
                        node_plugin_info["WriteNodes"] = write_node
                        
                        # Override frame range if use_nodes_frame_list is enabled and frame range is available
                        if (self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range)) and write_node in write_node_frames:
                            start_frame, end_frame = write_node_frames[write_node]
                            node_job_info["Frames"] = f"{start_frame}-{end_frame}"
                        
                        # Set dependencies if we have previous jobs
                        if previous_job_ids:
                            # Set dependencies as individual entries, with index continuing from user dependencies
                            for i, dep_id in enumerate(previous_job_ids):
                                node_job_info[f"JobDependency{i + dependency_count}"] = dep_id
                            
                        # Submit to Deadline
                        job_id = deadline.submit_job(node_job_info, node_plugin_info)
                        current_job_ids.append(job_id)
                    
                    # Update previous_job_ids for next render order group
                    previous_job_ids = current_job_ids
                
                logger.info(f"Jobs submitted with dependencies. Last Job ID: {job_id}")
                return job_id
            else:
                # Regular submission without dependencies or write nodes as tasks
                job_id = deadline.submit_job(job_info, plugin_info)
                logger.info(f"Job submitted successfully. Job ID: {job_id}")
                return job_id
                
        except Exception as e:
            raise SubmissionError(f"Failed to submit job: {e}")


def submit_nuke_script(script_path: str, **kwargs) -> str:
    """Submit a Nuke script to Deadline.
    
    This is a convenience function for submitting a Nuke script without
    creating a NukeSubmission instance directly.
    
    Args:
        script_path: Path to the Nuke script
        **kwargs: Additional arguments to pass to NukeSubmission
        
    Returns:
        Job ID of the submitted job
    """
    submission = NukeSubmission(script_path, **kwargs)
    return submission.submit() 