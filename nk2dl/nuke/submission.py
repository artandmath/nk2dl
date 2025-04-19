"""Nuke script submission to Deadline.

This module provides functionality for submitting Nuke scripts to Deadline render farm.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

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
                use_dependencies: bool = False,
                write_nodes_as_tasks: bool = False):
        """Initialize a Nuke script submission.
        
        Args:
            script_path: Path to the Nuke script (.nk file)
            frame_range: Frame range to render (e.g. "1-100", "f-l")
            output_path: Override for output path
            job_name: Custom job name
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
            use_dependencies: Whether to create dependencies based on write node render order
            write_nodes_as_tasks: Whether to submit write nodes as separate tasks for the same job
        """
        # Validate that use_dependencies and write_nodes_as_tasks are not both True
        if use_dependencies and write_nodes_as_tasks:
            raise SubmissionError("Cannot use both dependencies and write nodes as tasks features simultaneously")
            
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
        self.job_name = job_name if job_name else self.script_path.stem
        self.batch_name = batch_name
        self.department = department
        self.comment = comment
        
        # Nuke-specific options
        self.use_nuke_x = use_nuke_x
        self.use_batch_mode = use_batch_mode
        self.render_threads = render_threads
        self.use_gpu = use_gpu
        self.gpu_override = gpu_override
        self.max_ram_usage = max_ram_usage
        self.enforce_render_order = enforce_render_order
        self.min_stack_size = min_stack_size
        self.continue_on_error = continue_on_error
        self.reload_plugins = reload_plugins
        self.use_profiler = use_profiler
        self.profile_dir = profile_dir
        self.use_proxy = use_proxy
        self.write_nodes = write_nodes
        self.render_mode = render_mode
        self.use_dependencies = use_dependencies
        self.write_nodes_as_tasks = write_nodes_as_tasks
        
        # Initialize frame range
        if frame_range:
            self.fr = FrameRange(frame_range)
            # If frame range contains tokens, try to substitute them from script
            if self.fr.has_tokens:
                try:
                    with open(self.script_path, 'r') as f:
                        script_content = f.read()
                    self.fr.substitute_tokens_from_script(script_content)
                except Exception as e:
                    logger.warning(f"Failed to substitute frame range tokens: {e}")
                    
            # Validate frame range syntax
            if not self.fr.is_valid_syntax():
                raise SubmissionError(f"Invalid frame range syntax: {frame_range}")
        else:
            # Get frame range from script if not specified
            try:
                with open(self.script_path, 'r') as f:
                    script_content = f.read()
                    
                # Extract frame range from script
                first_frame_match = re.search(r'first_frame\s+(\d+)', script_content)
                last_frame_match = re.search(r'last_frame\s+(\d+)', script_content)
                
                if first_frame_match and last_frame_match:
                    first_frame = int(first_frame_match.group(1))
                    last_frame = int(last_frame_match.group(1))
                    self.frame_range = f"{first_frame}-{last_frame}"
                    self.fr = FrameRange(self.frame_range)
                else:
                    raise SubmissionError("Could not determine frame range from script. Please specify a frame range.")
            except Exception as e:
                raise SubmissionError(f"Failed to get frame range from script: {e}")
    
    def prepare_job_info(self) -> Dict[str, Any]:
        """Prepare job information for Deadline submission.
        
        Returns:
            Dictionary containing job information
        """
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
        
        return job_info
    
    def get_nuke_version(self) -> str:
        """Get the current Nuke version if running inside Nuke.
        
        Returns:
            Version string in format "MAJOR.MINOR" (e.g. "13.0")
        """
        try:
            import nuke
            major = nuke.NUKE_VERSION_MAJOR
            minor = nuke.NUKE_VERSION_MINOR
            return f"{major}.{minor}"
        except (ImportError, AttributeError):
            # Not running inside Nuke or can't get version
            logger.debug("Could not detect Nuke version, using default")
            return "10.0"  # Default version
    
    def prepare_plugin_info(self) -> Dict[str, Any]:
        """Prepare plugin information for Deadline submission.
        
        Returns:
            Dictionary containing plugin information
        """
        plugin_info = {
            "SceneFile": str(self.script_path.absolute()),
            "Version": self.get_nuke_version(),  # Get Nuke version programmatically
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
            plugin_info["WriteNodesAsSeparateTasks"] = "1"
            
            # Get write node frame ranges
            write_node_info = self._get_write_node_frame_ranges()
            
            # Add write node info to plugin info
            for i, (node_name, start_frame, end_frame) in enumerate(write_node_info):
                plugin_info[f"WriteNode{i}"] = node_name
                plugin_info[f"WriteNode{i}StartFrame"] = str(start_frame)
                plugin_info[f"WriteNode{i}EndFrame"] = str(end_frame)
        elif self.write_nodes and not self.use_dependencies:
            # For regular submission with specific write nodes
            plugin_info["WriteNodes"] = ",".join(self.write_nodes)
            
        if self.output_path:
            plugin_info["OutputFilePath"] = self.output_path
            
        return plugin_info
    
    def _get_write_node_frame_ranges(self) -> List[tuple]:
        """Get frame ranges for each write node.
        
        Returns:
            List of tuples (node_name, start_frame, end_frame)
        """
        write_node_info = []
        
        try:
            with open(self.script_path, 'r') as f:
                script_content = f.read()
                
            # Use fr.start_frame and fr.end_frame as defaults
            default_start = self.fr.start_frame
            default_end = self.fr.end_frame
            
            # Get write nodes by render order
            write_nodes_by_order = self._get_write_nodes_by_render_order()
            
            # Flatten the list of write nodes
            all_write_nodes = []
            for render_order in sorted(write_nodes_by_order.keys()):
                all_write_nodes.extend(write_nodes_by_order[render_order])
            
            # For each write node, try to extract its frame range
            # In a real implementation, this would use more sophisticated Nuke script parsing
            # For now, we'll just use the global frame range for all write nodes
            for node_name in all_write_nodes:
                write_node_info.append((node_name, default_start, default_end))
                
            return write_node_info
            
        except Exception as e:
            logger.warning(f"Failed to get write node frame ranges: {e}")
            # Return empty list on error
            return []
    
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
            elif self.use_dependencies and self.write_nodes and len(self.write_nodes) > 1:
                # Parse the Nuke script for write nodes and their render orders
                write_nodes_by_order = self._get_write_nodes_by_render_order()
                
                # Process in ascending render order
                previous_job_ids = []
                job_id = None
                
                for render_order in sorted(write_nodes_by_order.keys()):
                    current_job_ids = []
                    
                    # Submit each node in this render order group
                    for write_node in write_nodes_by_order[render_order]:
                        # Clone job info for this write node
                        node_job_info = job_info.copy()
                        node_plugin_info = plugin_info.copy()
                        
                        # Update job name to include write node
                        node_job_info["Name"] = f"{self.job_name} - {write_node}"
                        
                        # Specify which write node to render
                        node_plugin_info["WriteNodes"] = write_node
                        
                        # Set dependencies if we have previous jobs
                        if previous_job_ids:
                            # Set dependencies as individual entries, not as a list
                            for i, dep_id in enumerate(previous_job_ids):
                                node_job_info[f"JobDependency{i}"] = dep_id
                            
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
            
    def _get_write_nodes_by_render_order(self) -> Dict[int, List[str]]:
        """Parse the Nuke script to get write nodes grouped by render order.
        
        Returns:
            Dictionary mapping render orders to lists of write node names
        """
        write_nodes_by_order = {}
        
        try:
            with open(self.script_path, 'r') as f:
                script_content = f.read()
                
            # Find all Write nodes
            # This is a simplified approach - a proper implementation would use Nuke Python API
            # when available or more sophisticated parsing
            write_node_pattern = r'Write \{(.*?)\}'
            render_order_pattern = r'render_order\s+(\d+)'
            name_pattern = r'name\s+([\w\d_]+)'
            
            for write_match in re.finditer(write_node_pattern, script_content, re.DOTALL):
                write_node_text = write_match.group(1)
                
                # Get node name
                name_match = re.search(name_pattern, write_node_text)
                if not name_match:
                    continue
                node_name = name_match.group(1)
                
                # Get render order, default to 0
                render_order = 0
                render_order_match = re.search(render_order_pattern, write_node_text)
                if render_order_match:
                    render_order = int(render_order_match.group(1))
                
                # Add to dictionary
                if render_order not in write_nodes_by_order:
                    write_nodes_by_order[render_order] = []
                write_nodes_by_order[render_order].append(node_name)
            
            # If we're filtering to specific write nodes, only keep those
            if self.write_nodes:
                write_nodes_set = set(self.write_nodes)
                for order in write_nodes_by_order:
                    write_nodes_by_order[order] = [
                        node for node in write_nodes_by_order[order] 
                        if node in write_nodes_set
                    ]
                    # Remove empty lists
                    if not write_nodes_by_order[order]:
                        del write_nodes_by_order[order]
            
            return write_nodes_by_order
            
        except Exception as e:
            logger.warning(f"Failed to parse write nodes: {e}")
            # Fall back to treating all nodes as render order 0
            if self.write_nodes:
                return {0: self.write_nodes}
            return {0: []}


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