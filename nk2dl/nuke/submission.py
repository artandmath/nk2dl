"""Nuke script submission to Deadline.

This module provides functionality for submitting Nuke scripts to Deadline render farm.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import re
import itertools

from ..common.config import config
from ..common.errors import SubmissionError
from ..common.logging import logger
from ..common.framerange import FrameRange
from ..deadline.connection import get_connection
from . import utils as nuke_utils

class NukeSubmission:
    """Handles submission of Nuke scripts to Deadline."""

    def __init__(self, 
                # nk2dl specific parameters
                script_path: str,
                script_is_open: bool = False,
                submit_alphabetically: bool = False,
                submit_in_render_order: bool = False,
                graph_scope_variables: Optional[Union[List[str], List[List[str]]]] = None,
                
                # Job Info parameters
                job_name: Optional[str] = None,
                batch_name: Optional[str] = None,
                priority: Optional[int] = None,
                pool: Optional[str] = None,
                group: Optional[str] = None,
                chunk_size: Optional[int] = None,
                department: Optional[str] = None,
                comment: Optional[str] = None,
                concurrent_tasks: Optional[int] = None,
                extra_info: Optional[List[str]] = None,
                frame_range: str = "",
                job_dependencies: Optional[str] = None,
                
                # Plugin Info parameters
                output_path: str = "",
                nuke_version: Optional[Union[str, int, float]] = None,
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
                write_nodes_as_tasks: bool = False,
                write_nodes_as_separate_jobs: bool = False,
                render_order_dependencies: bool = False,
                use_nodes_frame_list: bool = False):
        """Initialize a Nuke script submission.
        
        Args:
            # nk2dl specific parameters
            script_path: Path to the Nuke script file
            script_is_open: Whether the script is already open in the current Nuke session
            submit_alphabetically: Whether to sort write nodes alphabetically by name
            submit_in_render_order: Whether to sort write nodes by render order
            graph_scope_variables: List of graph scope variables to use for rendering. Can be provided in two formats:
                                  
                                  1. Flat list format (all combinations will be generated):
                                     ["key1:value1,value2,...", "key2:valueA,valueB,..."]
                                  
                                  2. Nested list format (specific combinations):
                                     [
                                        ["key1:value1,value2", "key2:valueA"],  # First set of combinations
                                        ["key1:value3", "key2:valueB"]          # Second set of combinations
                                     ]
                                     
                                  If no values are provided for a key (e.g., "key:" or just "key"), 
                                  all available values for that key will be used.
            
            # Job Info parameters
            job_name: Job name template (defaults to config value)
            batch_name: Batch name template (defaults to config value)
            priority: Job priority (defaults to config value)
            pool: Worker pool (defaults to config value)
            group: Worker group (defaults to config value)
            chunk_size: Number of frames per task (defaults to config value)
            department: Department (defaults to config value)
            comment: Job comment (defaults to config value)
                     Can include tokens like {script}, {ss}, {write}, {file}, etc.
            concurrent_tasks: Number of parallel tasks for the job (defaults to 1)
            extra_info: List of extra info fields with optional tokens for customization
                       Each item supports the same tokens as job_name
            frame_range: Frame range to render (defaults to Nuke script settings)
            job_dependencies: Comma or space separated list of job IDs
            
            # Plugin Info parameters
            output_path: Output directory for rendered files
            nuke_version: Version of Nuke to use for rendering. Can be:
                          - String: "15.1"
                          - Float: 15.1 (converts to "15.1")
                          - Int: 15 (converts to "15.0")
                          If None, uses config or current Nuke version
            use_nuke_x: Whether to use NukeX for rendering
            use_batch_mode: Whether to use batch mode
            render_threads: Number of render threads
            use_gpu: Whether to use GPU for rendering
            gpu_override: Specific GPU to use
            max_ram_usage: Maximum RAM usage (MB)
            enforce_render_order: Whether to enforce write node render order
            min_stack_size: Minimum stack size (MB)
            continue_on_error: Whether to continue rendering on error
            reload_plugins: Whether to reload plugins between tasks
            use_profiler: Whether to use the performance profiler
            profile_dir: Directory for performance profile files
            use_proxy: Whether to use proxy mode for rendering
            write_nodes: List of write nodes to render
            render_mode: Render mode (full, proxy)
            write_nodes_as_tasks: Whether to submit write nodes as separate tasks
            write_nodes_as_separate_jobs: Whether to submit write nodes as separate jobs
            render_order_dependencies: Whether to set job dependencies based on render order
            use_nodes_frame_list: Whether to use the frame range defined in write nodes with use_limit enabled
        """
        # If render_order_dependencies is True, implicitly set write_nodes_as_separate_jobs to True as well
        if render_order_dependencies:
            write_nodes_as_separate_jobs = True
            
        # Check if write_nodes_as_tasks and write_nodes_as_separate_jobs are not both True
        if write_nodes_as_tasks and write_nodes_as_separate_jobs:
            raise SubmissionError("Cannot use both write_nodes_as_tasks and write_nodes_as_separate_jobs or render_order_dependencies simultaneously")
        
        # Check if write_nodes_as_tasks is enabled with a custom frame range but use_nodes_frame_list is disabled
        if write_nodes_as_tasks and frame_range and not use_nodes_frame_list and not frame_range.lower() in ['f-l', 'first-last', 'f', 'm', 'l', 'first', 'middle', 'last', 'i', 'input']:
            raise SubmissionError("Custom frame list is not supported when submitting write nodes as separate tasks. "
                                 "Please use global (f-l) or input (i) frame ranges, or enable use_nodes_frame_list.")
            
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
        self.concurrent_tasks = concurrent_tasks if concurrent_tasks is not None else config.get('submission.concurrent_tasks', 1)
        
        # Optional job properties
        # Store the script filename (with extension) for token replacement
        self.script_filename = self.script_path.name
        self.script_stem = self.script_path.stem
        
        # Store the batch_name template for later processing
        self.batch_name_template = batch_name if batch_name else config.get('submission.batch_name_template', "{script_stem}")
        # Process batch name tokens first (since job name might depend on batch name)
        self.batch_name = self._replace_batch_name_tokens(self.batch_name_template)
        
        self.department = department if department is not None else config.get('submission.department')
        
        # Load comment value or template
        self.comment_template = comment if comment is not None else config.get('submission.comment_template', "")
        # We'll process comment tokens later when preparing job info
        self.comment = self.comment_template
        
        # Load ExtraInfo templates
        self.extra_info = extra_info if extra_info is not None else config.get('submission.extra_info_templates', [])
        
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
        self.write_nodes_as_separate_jobs = write_nodes_as_separate_jobs if isinstance(write_nodes_as_separate_jobs, bool) else config.get('submission.write_nodes_as_separate_jobs', False)
        self.submit_alphabetically = submit_alphabetically if isinstance(submit_alphabetically, bool) else config.get('submission.submit_alphabetically', False)
        self.submit_in_render_order = submit_in_render_order if isinstance(submit_in_render_order, bool) else config.get('submission.submit_in_render_order', False)
        self.use_nodes_frame_list = use_nodes_frame_list if isinstance(use_nodes_frame_list, bool) else config.get('submission.use_nodes_frame_list', False)
        self.script_is_open = script_is_open
        
        # Store Nuke version
        self.nuke_version = nuke_version
        
        # Store GSV settings
        self.graph_scope_variables = graph_scope_variables
        self.gsv_combinations = []
        
        # If GSV is provided, check Nuke version compatibility
        if self.graph_scope_variables:
            # Check Nuke version for GSV support (requires 15.2+)
            nuke_version_str = nuke_utils.nuke_version(self.nuke_version) if self.nuke_version else nuke_utils.nuke_version()
            try:
                major, minor = map(int, nuke_version_str.split('.')[:2])
                supports_gsv = (major > 15) or (major == 15 and minor >= 2)
            except ValueError:
                supports_gsv = False
                
            if not supports_gsv:
                logger.warning(f"Graph Scope Variables (GSV) were specified but are not supported in Nuke {nuke_version_str}. "
                              f"GSV requires Nuke 15.2 or higher. GSV will be ignored.")
                self.graph_scope_variables = None
        
        # Initialize frame range
        if frame_range:
            self.fr = FrameRange(frame_range)
            # If frame range contains tokens, try to substitute them
            if self.fr.has_tokens:
                # First ensure we can query the script
                nuke = self._ensure_script_can_be_queried()
                
                try:
                    # Only substitute tokens if it's not "i" or "input"
                    if not re.search(r'\b(i|input)\b', frame_range):
                        self._get_frame_range_from_nuke()
                    else:
                        # For input token, we need to specify the write node
                        if write_nodes and len(write_nodes) == 1:
                            self._get_frame_range_from_nuke(write_nodes[0])
                        else:
                            logger.debug(f"Input token found in frame_range object and multiple write nodes specified. We will resolve the input token later."
                                         f"writenodes: {write_nodes} frame_range: \"{frame_range}\"")

                except Exception as e:
                    logger.warning(f"Failed to substitute frame range tokens: {e}")
            
            # Validate frame range syntax
            if not self.fr.is_valid_syntax():
                raise SubmissionError(f"Invalid frame range syntax: {frame_range}")
        else:
            # Get frame range from Nuke script
            self._get_frame_range_from_nuke()
        
        # For job_name we'll do the replacement later when we have access to more information
        
        # If we have GSVs, parse them
        if self.graph_scope_variables:
            self._parse_graph_scope_variables()

    def _ensure_script_can_be_queried(self):
        """Ensure the script is open in Nuke before trying to access nodes or GSVs.
        
        Loading the nuke module is a time-consuming operation, so we only do it only if necessary.

        Returns:
            The nuke module
        """
        nuke = nuke_utils.nuke_module()
        
        # If the script is not currently open, we need to open it
        if not self.script_is_open:
            # Open the script
            nuke.scriptOpen(str(self.script_path.absolute()))
            # Mark as open now
            self.script_is_open = True
        
        return nuke

    def _get_node_pretty_path(self, node, gsv_combination=None) -> str:
        """Get a node's file path while preserving frame number placeholders.
        
        When Nuke evaluates a file path with node['file'].evaluate(), it replaces
        frame number placeholders (e.g., '####', '%04d') with the actual frame number.
        This function evaluates the path but restores those placeholders.
        
        Args:
            node: A Nuke node with a 'file' knob
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            The evaluated file path with frame number placeholders preserved
        """
        # Apply GSV values if provided
        if gsv_combination:
            nuke = self._ensure_script_can_be_queried()
            root_node = nuke.root()
            if 'gsv' in root_node.knobs():
                gsv_knob = root_node['gsv']
                # Apply each GSV value
                for key, value in gsv_combination:
                    try:
                        gsv_knob.setGsvValue(f'__default__.{key}', value)
                    except Exception as e:
                        logger.warning(f"Failed to set GSV value {key}={value}: {e}")
        
        return nuke_utils.node_pretty_path(node)

    def _replace_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Generic token replacement function for any field.
        
        Args:
            template: Template string with tokens
            write_node: Optional write node name for write-node specific tokens
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            String with tokens replaced
        """
        
        # Apply GSV values if provided
        if gsv_combination:
            # Ensure the script is open
            nuke = self._ensure_script_can_be_queried()

            # Check Nuke version before attempting to use GSV
            nuke_version_str = nuke_utils.nuke_version(self.nuke_version) if self.nuke_version else nuke_utils.nuke_version()
            try:
                major, minor = map(int, nuke_version_str.split('.')[:2])
                supports_gsv = (major > 15) or (major == 15 and minor >= 2)
            except ValueError:
                supports_gsv = False
            
            if supports_gsv:
                # Ensure the script is open
                nuke = self._ensure_script_can_be_queried()

                root_node = nuke.root()
                if 'gsv' in root_node.knobs():
                    gsv_knob = root_node['gsv']
                    # Apply each GSV value
                    for key, value in gsv_combination:
                        try:
                            gsv_knob.setGsvValue(f'__default__.{key}', value)
                        except Exception as e:
                            logger.warning(f"Failed to set GSV value {key}={value}: {e}")
        
        # Start with the template
        result = template
        
        # Define token groups
        script_stem_tokens = ["{ss}", "{nss}", "{nks}", "{sstem}", "{nstem}", "{nkstem}", "{scriptstem}", "{script_stem}", "{nukescriptstem}", "{nukescript_stem}", "{nuke_script_stem}"]
        script_name_tokens = ["{s}", "{ns}", "{nk}", "{script}", "{scriptname}", "{script_name}", "{nukescript}", "{nuke_script}"]
        file_stem_tokens = ["{fs}", "{fns}", "{os}", "{fstem}", "{ostem}", "{filestem}", "{file_stem}", "{filenamestem}", "{filename_stem}", "{outputstem}", "{output_stem}"]
        batch_name_tokens = ["{b}", "{bn}", "{batch}", "{batchname}", "{batch_name}"]
        write_node_tokens = ["{w}", "{wn}", "{write}", "{writenode}", "{write_node}", "{write_name}"]
        output_tokens = ["{o}", "{fn}", "{file}", "{filename}", "{file_name}", "{output}"]
        render_order_tokens = ["{r}", "{ro}", "{renderorder}", "{render_order}"]
        frame_range_tokens = ["{x}", "{f}", "{fr}", "{range}", "{framerange}"]
        gsv_tokens = ["{g}", "{gsv}", "{gsvs}", "{GSVs}", "{graphscopevars}", "{graphscopevariables}", "{graph_scope_vars}", "{graph_scope_variables}"]
        
        # Include all token groups
        allowed_token_groups = [
            script_stem_tokens,
            script_name_tokens,
            file_stem_tokens,
            batch_name_tokens,
            frame_range_tokens,
            write_node_tokens,
            output_tokens,
            render_order_tokens,
            gsv_tokens
        ]
        
        # Replace tokens with their values
        for token_group in allowed_token_groups:
            for token in token_group:
                # Skip token replacement if it's not in the template
                if token not in result:
                    continue
                
                # Initialize value to empty string as a fallback
                value = ""
                
                # Get the value for each token type
                if token in script_stem_tokens:
                    value = self.script_stem
                elif token in script_name_tokens:
                    value = self.script_filename
                elif token in file_stem_tokens:
                    # File stem tokens require a write node to get output path
                    if write_node:
                        # Ensure the script is open
                        nuke = self._ensure_script_can_be_queried()

                        node = nuke.toNode(write_node)
                        if node and node.Class() == "Write":
                            try:
                                output_file = self._get_node_pretty_path(node, gsv_combination)
                                # Extract stem from the output path
                                output_stem = os.path.splitext(os.path.basename(output_file))[0]
                                value = output_stem
                            except:
                                logger.warning(f"Failed to get output filename stem for write node {write_node}")
                                value = self.script_stem  # Fallback to script stem
                        else:
                            value = self.script_stem  # Fallback to script stem
                    else:
                        value = self.script_stem  # Fallback to script stem
                elif token in batch_name_tokens:
                    value = self.batch_name
                elif token in frame_range_tokens:
                    value = self.frame_range
                elif token in gsv_tokens:
                    # Check Nuke version before attempting to use GSV tokens
                    nuke_version_str = nuke_utils.nuke_version(self.nuke_version) if self.nuke_version else nuke_utils.nuke_version()
                    try:
                        major, minor = map(int, nuke_version_str.split('.')[:2])
                        supports_gsv = (major > 15) or (major == 15 and minor >= 2)
                    except ValueError:
                        supports_gsv = False
                    
                    if supports_gsv and gsv_combination:
                        # Format as key1=value1,key2=value2
                        value = ",".join([f"{key}={val}" for key, val in gsv_combination])
                    else:
                        value = ""  # Empty string if no GSV combination or not supported
                elif write_node and token in write_node_tokens + output_tokens + render_order_tokens:
                    # Ensure the script is open
                    nuke = self._ensure_script_can_be_queried()

                    node = nuke.toNode(write_node)
                    if node and node.Class() == "Write":
                        if token in write_node_tokens:
                            value = write_node
                        elif token in render_order_tokens:
                            value = "0"  # Default value
                            if 'render_order' in node.knobs():
                                value = str(int(node['render_order'].value()))
                        elif token in output_tokens:
                            # Try to get output filename
                            try:
                                output_file = self._get_node_pretty_path(node, gsv_combination)
                                value = os.path.basename(output_file)
                            except:
                                logger.warning(f"Failed to get output filename for write node {write_node}")
                                value = ""
                
                # Replace the token with its value
                result = result.replace(token, value)
        
        return result

    def _replace_batch_name_tokens(self, template: str) -> str:
        """Replace tokens in batch name template.
        
        Supported tokens (ONLY these are allowed):
        - Script stem tokens: {ss}, {nss}, {nks}, {sstem}, {nstem}, {nkstem}, {scriptstem}, {script_stem}, {nukescriptstem}, {nukescript_stem}, {nuke_script_stem}
        - Script name tokens: {s}, {ns}, {nk}, {script}, {scriptname}, {script_name}, {nukescript}, {nuke_script}
        
        Args:
            template: Batch name template with tokens

        Returns:
            Batch name with tokens replaced
            
        Raises:
            ValueError: If a restricted token is used in batch_name
        """
        nuke = nuke_utils.nuke_module()
        
        # Start with the template
        result = template
        
        # Define token groups
        script_stem_tokens = ["{ss}", "{nss}", "{nks}", "{sstem}", "{nstem}", "{nkstem}", "{scriptstem}", "{script_stem}", "{nukescriptstem}", "{nukescript_stem}", "{nuke_script_stem}"]
        script_name_tokens = ["{s}", "{ns}", "{nk}", "{script}", "{scriptname}", "{script_name}", "{nukescript}", "{nuke_script}"]
        
        # Define allowed tokens for batch name
        # Batch name can ONLY use script name and script stem tokens
        allowed_token_groups = [script_stem_tokens, script_name_tokens]
        
        # Replace tokens with their values
        for token_group in allowed_token_groups:
            for token in token_group:
                # Skip token replacement if it's not in the template
                if token not in result:
                    continue
                
                # Get the value for each token type
                if token in script_stem_tokens:
                    value = self.script_stem
                elif token in script_name_tokens:
                    value = self.script_filename
                else:
                    # Skip tokens that don't match any of the allowed groups
                    continue
                
                # Replace the token with its value
                result = result.replace(token, value)
        
        return result

    def _replace_job_name_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in job name template.
        
        Supported tokens:
        - Script stem tokens: {ss}, {nss}, {nks}, {sstem}, {nstem}, {nkstem}, {scriptstem}, {script_stem}, {nukescriptstem}, {nukescript_stem}, {nuke_script_stem}
        - Script name tokens: {s}, {ns}, {nk}, {script}, {scriptname}, {script_name}, {nukescript}, {nuke_script}
        - Batch name tokens: {b}, {bn}, {batch}, {batchname}, {batch_name}
        - Write node tokens: {w}, {wn}, {writenode}, {write}, {write_node}, {write_name}
        - File stem tokens: {fs}, {fns}, {os}, {fstem}, {ostem}, {filestem}, {file_stem}, {filenamestem}, {filename_stem}, {outputstem}, {output_stem}
        - Output tokens: {o}, {fn}, {file}, {filename}, {file_name}, {output}
        - Render order tokens: {r}, {ro}, {renderorder}, {render_order}
        - Frame range tokens: {x}, {f}, {fr}, {range}, {framerange}

        Args:
            template: Job name template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            Job name with tokens replaced
        """
        return self._replace_tokens(template, write_node, gsv_combination)

    def _replace_comment_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in comment template.
        
        Supports the same tokens as job_name.

        Args:
            template: Comment template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            Comment with tokens replaced
        """
        return self._replace_tokens(template, write_node, gsv_combination)

    def _replace_extrainfo_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in extrainfo template.
        
        Supports the same tokens as job_name.

        Args:
            template: ExtraInfo template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            ExtraInfo with tokens replaced
        """
        return self._replace_tokens(template, write_node, gsv_combination)
    
    def _get_frame_range_from_nuke(self, write_node_name: Optional[str] = None) -> None:
        """Get frame range from Nuke script using Nuke API.
        
        Args:
            write_node_name: Optional name of a write node for 'input' token
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_queried()
        
        try:
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
    
    def _parse_graph_scope_variables(self) -> None:
        """Parse graph scope variables and get all possible combinations.
        
        This method handles two formats for graph_scope_variables:
        1. Flat list: ["key1:value1,value2", "key2:valueA,valueB"] - generates all combinations
        2. Nested list: [["key1:value1", "key2:valueA"], ["key1:value2", "key2:valueB"]] - uses specific combinations
        
        After parsing, gsv_combinations will contain tuples of (key, value) pairs for each combination.
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_queried()
        
        try:
            # Check Nuke version for GSV support (requires 15.2+)
            nuke_version_str = nuke_utils.nuke_version(self.nuke_version) if self.nuke_version else nuke_utils.nuke_version()
            try:
                major, minor = map(int, nuke_version_str.split('.')[:2])
                supports_gsv = (major > 15) or (major == 15 and minor >= 2)
            except ValueError:
                supports_gsv = False
                
            if not supports_gsv:
                logger.warning(f"Graph Scope Variables (GSV) are not supported in Nuke {nuke_version_str}. Requires Nuke 15.2 or higher.")
                # Set an empty list for GSV combinations to avoid future processing
                self.gsv_combinations = []
                return
            
            # Get the root node to access GSV knob
            root_node = nuke.root()
            if not 'gsv' in root_node.knobs():
                raise SubmissionError("This Nuke script doesn't have Graph Scope Variables (GSV) knob. GSV requires Nuke 15.2 or higher.")
            
            gsv_knob = root_node['gsv']
            
            # Check if we have a flat list or nested list format
            if self.graph_scope_variables and isinstance(self.graph_scope_variables[0], list):
                # Nested list format - specific combinations provided
                self._parse_nested_gsv_format(gsv_knob)
            else:
                # Flat list format - generate all combinations
                self._parse_flat_gsv_format(gsv_knob)
            
            if not self.gsv_combinations:
                raise SubmissionError("Failed to generate valid GSV combinations.")
                
            logger.debug(f"Generated {len(self.gsv_combinations)} GSV combinations")
            
        except Exception as e:
            raise SubmissionError(f"Failed to parse graph scope variables: {e}")
    
    def _parse_flat_gsv_format(self, gsv_knob) -> None:
        """Parse flat list GSV format and generate all combinations.
        
        Args:
            gsv_knob: The GSV knob from the Nuke script
        """
        # Parse each GSV string in format "key:value1,value2,..."
        gsv_sets = []
        for gsv_string in self.graph_scope_variables:
            if ":" in gsv_string:
                key, values_str = gsv_string.split(":", 1)
            else:
                # If no colon, assume key with all values
                key = gsv_string
                values_str = ""
            
            # Get the available values for this key
            available_values = gsv_knob.getListOptions(key)
            
            # If values_str is empty, use all available values
            if not values_str:
                if not available_values:
                    raise SubmissionError(f"No values found for GSV key '{key}'. Please check if the variable exists in the script.")

                selected_values = available_values
            else:
                # Otherwise, use the specified values
                selected_values = [v.strip() for v in values_str.split(",") if v.strip()]
                
                # Validate the selected values exist in available values if available values is not empty
                if available_values:
                    invalid_values = [v for v in selected_values if v not in available_values]
                    if invalid_values:
                        raise SubmissionError(f"Invalid values for GSV key '{key}': {', '.join(invalid_values)}. Available values are: {', '.join(available_values)}")
            
            # Add the key and its selected values to our set
            gsv_sets.append([(key, value) for value in selected_values])
        
        # Generate all combinations of GSV values
        self.gsv_combinations = list(itertools.product(*gsv_sets))

    def _parse_nested_gsv_format(self, gsv_knob) -> None:
        """Parse nested list GSV format with specific combinations.
        
        Args:
            gsv_knob: The GSV knob from the Nuke script
        """
        for gsv_set in self.graph_scope_variables:
            # Process each specific combination set
            current_combination = []
            
            for gsv_string in gsv_set:
                if ":" in gsv_string:
                    key, values_str = gsv_string.split(":", 1)
                else:
                    # If no colon, assume key with all values
                    key = gsv_string
                    values_str = ""
                
                # Get the available values for this key
                available_values = gsv_knob.getListOptions(key)

                # Process values for this key in the current set
                if not values_str:
                    if not available_values:
                        raise SubmissionError(f"No values found for GSV key '{key}'. Please check if the variable exists in the script.")
                
                    # If no values specified, use all available values
                    # For this format, this expands to multiple combinations within this set
                    for value in available_values:
                        current_combination.append((key, value))
                else:
                    # Parse the comma-separated values
                    for value in [v.strip() for v in values_str.split(",") if v.strip()]:
                        # Validate the value exists if available values is not empty
                        if available_values:
                            if value not in available_values:
                                raise SubmissionError(f"Invalid value '{value}' for GSV key '{key}'. Available values are: {', '.join(available_values)}")
                        
                        current_combination.append((key, value))
            
            # If we have a valid combination, add it
            if current_combination:
                # For nested format with multiple values per key in a set, we need to generate
                # all combinations within this set
                keys_to_values = {}
                for key, value in current_combination:
                    if key not in keys_to_values:
                        keys_to_values[key] = []
                    keys_to_values[key].append(value)
                
                # Generate all combinations within this specific set
                keys = list(keys_to_values.keys())
                value_combinations = itertools.product(*[keys_to_values[k] for k in keys])
                
                # Add each combination as a separate entry
                for values in value_combinations:
                    combination = [(keys[i], values[i]) for i in range(len(keys))]
                    self.gsv_combinations.append(tuple(combination))

    def _get_gsv_job_name(self, gsv_combination, write_node=None) -> str:
        """Generate a job name that includes GSV information.
        
        Args:
            gsv_combination: Tuple of (key, value) pairs for GSV
            write_node: Optional write node name
            
        Returns:
            Job name with GSV information
        """
        # Start with the standard job name
        if write_node:
            job_name = self._replace_job_name_tokens(self.job_name_template, write_node)
        else:
            job_name = self._replace_job_name_tokens(self.job_name_template)
        
        # Return just the job name without GSV info
        return job_name

    def _is_movie_format(self, write_node) -> bool:
        """Check if a write node is outputting a movie format that should be rendered on a single machine.
        
        Args:
            write_node: The Nuke write node to check
            
        Returns:
            True if the node is outputting a movie format, False otherwise
        """
        nuke = self._ensure_script_can_be_queried()
        node = nuke.toNode(write_node)
        
        if node and node.Class() == "Write" and 'file_type' in node.knobs():
            file_type = node['file_type'].value()
            movie_formats = ['mov', 'mxf']
            return file_type.lower() in movie_formats
            
        return False

    def prepare_job_info(self, gsv_combination=None) -> Dict[str, Any]:
        """Prepare job information for Deadline submission.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV
            
        Returns:
            Dictionary containing job information
        """
        # Process job_name with tokens if it's for a specific write node
        if self.write_nodes and len(self.write_nodes) == 1:
            self.job_name = self._replace_job_name_tokens(self.job_name_template, self.write_nodes[0], gsv_combination)
        else:
            self.job_name = self._replace_job_name_tokens(self.job_name_template, None, gsv_combination)
        
        # Create base job info dictionary
        job_info = {
            "Name": self.job_name,
            "Plugin": "Nuke",
            "Frames": self.frame_range,
            "ChunkSize": self.chunk_size,
            "ConcurrentTasks": self.concurrent_tasks,
            "Pool": self.pool,
            "Group": self.group,
            "Priority": self.priority
        }
        
        # Note: check for movie format is now done in prepare_plugin_info
        # and ChunkSize is updated in submit() when needed
            
        # Add optional fields if specified
        if self.batch_name:
            job_info["BatchName"] = self.batch_name
        if self.department:
            job_info["Department"] = self.department
        if self.comment:
            # Process comment tokens if it contains any
            if any(token in self.comment for token in ["{", "}"]):
                if self.write_nodes and len(self.write_nodes) == 1:
                    job_info["Comment"] = self._replace_comment_tokens(self.comment, self.write_nodes[0], gsv_combination)
                else:
                    job_info["Comment"] = self._replace_comment_tokens(self.comment, None, gsv_combination)
            else:
                job_info["Comment"] = self.comment
                
        # Add OutputFilename entries to job info
        self._add_output_filenames_to_job_info(job_info, gsv_combination)
        
        # Process extra_info fields if any
        if self.extra_info:
            for i, extra_info_item in enumerate(self.extra_info):
                # Process tokens if the item contains any
                if any(token in extra_info_item for token in ["{", "}"]):
                    if self.write_nodes and len(self.write_nodes) == 1:
                        job_info[f"ExtraInfo{i}"] = self._replace_extrainfo_tokens(extra_info_item, self.write_nodes[0], gsv_combination)
                    else:
                        job_info[f"ExtraInfo{i}"] = self._replace_extrainfo_tokens(extra_info_item, None, gsv_combination)
                else:
                    job_info[f"ExtraInfo{i}"] = extra_info_item
            
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
        
    def _add_output_filenames_to_job_info(self, job_info: Dict[str, Any], gsv_combination=None) -> None:
        """Add OutputFilename# entries to job info.
        
        This allows the Deadline Monitor to display the "View Output Image" context menu option.
        
        Args:
            job_info: The job info dictionary to update
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
        """
        nuke = nuke_utils.nuke_module()
        
        # Different handling based on submission mode
        if self.write_nodes_as_tasks and self.write_nodes:
            # For write nodes as tasks: add all specified write nodes
            for i, write_node_name in enumerate(self.write_nodes):
                node = nuke.toNode(write_node_name)
                if node and node.Class() == "Write" and not node['disable'].value():
                    output_path = self._get_node_pretty_path(node, gsv_combination)
                    if output_path:
                        job_info[f"OutputFilename{i}"] = output_path
                        
        elif self.write_nodes and len(self.write_nodes) == 1:
            # For a single write node: add just that one
            write_node_name = self.write_nodes[0]
            node = nuke.toNode(write_node_name)
            if node and node.Class() == "Write" and not node['disable'].value():
                output_path = self._get_node_pretty_path(node, gsv_combination)
                if output_path:
                    job_info["OutputFilename0"] = output_path
                    
        elif not self.write_nodes:
            # If no write node specified: find all enabled write nodes
            write_nodes = []
            for node in nuke.allNodes('Write'):
                if not node['disable'].value():
                    write_nodes.append(node)
            
            # Add outputs for all enabled write nodes
            for i, node in enumerate(write_nodes):
                output_path = self._get_node_pretty_path(node, gsv_combination)
                if output_path:
                    job_info[f"OutputFilename{i}"] = output_path
        
        # If using dependencies, don't add OutputFilename entries as they'll be set per job
        # They are added in the submit method when handling each write node
        
    def prepare_plugin_info(self, gsv_combination=None) -> Dict[str, Any]:
        """Prepare plugin information for Deadline submission.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV
            
        Returns:
            Dictionary containing plugin information
        """
        plugin_info = {
            "SceneFile": str(self.script_path.absolute()),
            "Version": nuke_utils.nuke_version(self.nuke_version),
            "UseNukeX": "1" if self.use_nuke_x else "0",
            "BatchMode": "1" if self.use_batch_mode else "0",
            "EnforceRenderOrder": "1" if self.enforce_render_order else "0",
            "ContinueOnError": "1" if self.continue_on_error else "0",
            "RenderMode": self.render_mode.capitalize()
        }
        
        # Add BatchModeIsMovie flag if needed - single write node that outputs a movie format
        # Note: When this is set, we need to update ChunkSize in job_info, but that's done in submit()
        if (self.write_nodes and len(self.write_nodes) == 1 and 
            not self.write_nodes_as_tasks and 
            self._is_movie_format(self.write_nodes[0])):
            plugin_info["BatchModeIsMovie"] = "True"
        
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
            write_node_info = self._get_write_node_frame_ranges(gsv_combination)
            
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
            # Use individual WriteNode0, WriteNode1, etc. entries instead of comma-separated list
            for i, node_name in enumerate(self.write_nodes):
                plugin_info[f"WriteNode{i}"] = node_name
        
        if self.output_path:
            plugin_info["OutputFilePath"] = self.output_path
        
        # Add GSV information to plugin info if provided
        if gsv_combination:
            # Set GraphScopeVariablesEnabled to 1
            plugin_info["GraphScopeVariablesEnabled"] = "1"
            
            # Create a single comma-separated string for all GSV key-value pairs
            gsv_string = ",".join([f"{key}:{value}" for key, value in gsv_combination])
            plugin_info["GraphScopeVariables"] = gsv_string
            
            # Remove individual GSV entries to avoid redundancy
            # Don't add the individual entries that were causing duplication
        
        return plugin_info
    
    def _get_write_node_frame_ranges(self, gsv_combination=None) -> List[Tuple[str, int, int]]:
        """Get frame ranges for each write node using Nuke API.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            List of tuples (node_name, start_frame, end_frame)
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_queried()
        
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
            # Apply GSV values if provided
            if gsv_combination:
                root_node = nuke.root()
                if 'gsv' in root_node.knobs():
                    gsv_knob = root_node['gsv']
                    # Apply each GSV value
                    for key, value in gsv_combination:
                        try:
                            gsv_knob.setGsvValue(f'__default__.{key}', value)
                        except Exception as e:
                            logger.warning(f"Failed to set GSV value {key}={value}: {e}")
            
            # Get write nodes by render order
            write_nodes_by_order = self._get_write_nodes_by_render_order(gsv_combination)
            
            # Flatten the list of write nodes
            all_write_nodes = []
            for render_order in sorted(write_nodes_by_order.keys()):
                all_write_nodes.extend(write_nodes_by_order[render_order])
            
            # Check if we're using input frame range
            is_input_frame_range = re.search(r'\b(i|input)\b', self.frame_range)
            
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
                    # If we have the input token or render_order_dependencies is true with input token, 
                    # try to get input frame range
                    elif is_input_frame_range:
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
    
    def _get_write_nodes_by_render_order(self, gsv_combination=None) -> Dict[int, List[str]]:
        """Get write nodes grouped by render order using Nuke API.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            Dictionary mapping render orders to lists of write node names
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_queried()
        
        write_nodes_by_order = {}
        write_nodes_info = []
        
        try:
            # Apply GSV values if provided
            if gsv_combination:
                root_node = nuke.root()
                if 'gsv' in root_node.knobs():
                    gsv_knob = root_node['gsv']
                    # Apply each GSV value
                    for key, value in gsv_combination:
                        try:
                            gsv_knob.setGsvValue(f'__default__.{key}', value)
                        except Exception as e:
                            logger.warning(f"Failed to set GSV value {key}={value}: {e}")
            
            # Find all Write nodes
            for node in nuke.allNodes('Write'):
                node_name = node.name()
                
                # Get render order, default to 0
                render_order = 0
                if 'render_order' in node.knobs():
                    render_order = int(node['render_order'].value())
                
                # Store node information for sorting
                write_nodes_info.append((node_name, render_order))
            
            # If we're filtering to specific write nodes, only keep those
            if self.write_nodes:
                write_nodes_set = set(self.write_nodes)
                write_nodes_info = [
                    (node_name, render_order) for node_name, render_order in write_nodes_info
                    if node_name in write_nodes_set
                ]
            
            # Handle sorting based on options
            if self.submit_in_render_order and self.submit_alphabetically:
                # Sort by render order first, then alphabetically within render order groups
                write_nodes_info.sort(key=lambda x: (x[1], x[0]))
            elif self.submit_in_render_order:
                # Sort by render order only
                write_nodes_info.sort(key=lambda x: x[1])
            elif self.submit_alphabetically:
                # Sort alphabetically by node name
                write_nodes_info.sort(key=lambda x: x[0])
            # Otherwise, keep the original order (or filtered order if write_nodes was specified)
            
            # Group by render order for later processing
            for node_name, render_order in write_nodes_info:
                if render_order not in write_nodes_by_order:
                    write_nodes_by_order[render_order] = []
                write_nodes_by_order[render_order].append(node_name)
            
            return write_nodes_by_order
        except Exception as e:
            raise SubmissionError(f"Failed to get write nodes by render order: {e}")

    def _get_sorted_write_nodes(self, gsv_combination=None) -> List[str]:
        """Get write nodes sorted according to submission options.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            List of write node names sorted as specified by options
        """
        write_nodes_by_order = self._get_write_nodes_by_render_order(gsv_combination)
        sorted_nodes = []
        
        # Process the write nodes based on the sorting options
        if self.submit_in_render_order:
            # Go through render orders in ascending order
            for render_order in sorted(write_nodes_by_order.keys()):
                nodes_in_order = write_nodes_by_order[render_order]
                
                # If also sorting alphabetically, sort this group
                if self.submit_alphabetically:
                    nodes_in_order.sort()
                
                sorted_nodes.extend(nodes_in_order)
        else:
            # Collect all nodes
            all_nodes = []
            for render_order in sorted(write_nodes_by_order.keys()):
                all_nodes.extend(write_nodes_by_order[render_order])
            
            # If sorting alphabetically, sort the collected nodes
            if self.submit_alphabetically:
                all_nodes.sort()
            
            sorted_nodes = all_nodes
            
        return sorted_nodes

    def submit(self) -> str:
        """Submit the Nuke script to Deadline.
        
        Returns:
            Job ID of the submitted job
            
        Raises:
            SubmissionError: If submission fails
        """
        try:
            # Get Deadline connection
            deadline = get_connection()
            
            # If write_nodes_as_separate_jobs is True but no write nodes are provided,
            # automatically get all enabled write nodes from the script
            if (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and not self.write_nodes:
                # Ensure the script is open
                nuke = self._ensure_script_can_be_queried()
                
                # Get all enabled Write nodes
                enabled_write_nodes = []
                for node in nuke.allNodes('Write'):
                    if not node['disable'].value():
                        enabled_write_nodes.append(node.name())
                
                if enabled_write_nodes:
                    self.write_nodes = enabled_write_nodes
                    logger.info(f"Automatically using {len(enabled_write_nodes)} enabled Write nodes: {', '.join(enabled_write_nodes)}")
                else:
                    logger.warning("No enabled Write nodes found in the script. Switching to normal submission.")
                    self.write_nodes_as_separate_jobs = False
                    self.render_order_dependencies = False
            
            # If using GSVs, submit multiple jobs for each combination
            if self.graph_scope_variables and self.gsv_combinations:
                submitted_job_ids = []
                
                for gsv_combination in self.gsv_combinations:
                    # Prepare job and plugin info with GSV information
                    job_info = self.prepare_job_info(gsv_combination)
                    plugin_info = self.prepare_plugin_info(gsv_combination)
                    
                    # If using write nodes as tasks with GSVs
                    if self.write_nodes_as_tasks and self.write_nodes and len(self.write_nodes) > 1:
                        # Simply submit as a single job with all write nodes as tasks
                        job_id = deadline.submit_job(job_info, plugin_info)
                        submitted_job_ids.append(job_id)
                        logger.info(f"GSV job submitted with write nodes as tasks. Job ID: {job_id}")
                    
                    # If using separate jobs or dependencies with GSVs
                    elif (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and self.write_nodes and len(self.write_nodes) > 1:
                        # Get write node frame ranges if use_nodes_frame_list is enabled
                        write_node_frames = {}
                        if self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range):
                            write_node_info = self._get_write_node_frame_ranges(gsv_combination)
                            for node_name, start_frame, end_frame in write_node_info:
                                write_node_frames[node_name] = (start_frame, end_frame)
                        
                        # Get sorted write nodes
                        sorted_write_nodes = self._get_sorted_write_nodes(gsv_combination)
                        
                        # Track job IDs by render order
                        jobs_by_render_order = {}
                        job_id = None
                        
                        # Count existing dependencies from the user-specified ones
                        dependency_count = 0
                        if self.job_dependencies:
                            dependency_count = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
                        
                        # Get render orders for all write nodes
                        nuke = nuke_utils.nuke_module()
                        write_node_render_orders = {}
                        for write_node in sorted_write_nodes:
                            node_obj = nuke.toNode(write_node)
                            render_order = 0
                            if node_obj and 'render_order' in node_obj.knobs():
                                render_order = int(node_obj['render_order'].value())
                            write_node_render_orders[write_node] = render_order
                        
                        # Find all unique render orders and sort them
                        unique_render_orders = sorted(set(write_node_render_orders.values()))
                        
                        # Submit each node based on sorting options
                        last_processed_render_order = None
                        for write_node in sorted_write_nodes:
                            # Get render order for this node
                            render_order = write_node_render_orders[write_node]
                            
                            # Clone job info for this write node and GSV combination
                            node_job_info = job_info.copy()
                            node_plugin_info = plugin_info.copy()
                            
                            # Check if this is a movie format and set BatchModeIsMovie if needed
                            # Skip for write_nodes_as_tasks as mentioned in the requirements
                            if not self.write_nodes_as_tasks and self._is_movie_format(write_node):
                                node_plugin_info["BatchModeIsMovie"] = "True"
                                # Set a very large chunk size to ensure entire movie renders on one machine
                                node_job_info["ChunkSize"] = "1000000"
                            
                            # Update job name to include write node
                            node_job_info["Name"] = self._get_gsv_job_name(gsv_combination, write_node)
                            
                            # Update comment with tokens for this write node
                            if "Comment" in node_job_info and any(token in node_job_info["Comment"] for token in ["{", "}"]):
                                node_job_info["Comment"] = self._replace_comment_tokens(self.comment, write_node, gsv_combination)
                            
                            # Update ExtraInfo fields with tokens for this write node
                            for i, extra_info_item in enumerate(self.extra_info):
                                extra_info_key = f"ExtraInfo{i}"
                                if extra_info_key in node_job_info and any(token in extra_info_item for token in ["{", "}"]):
                                    node_job_info[extra_info_key] = self._replace_extrainfo_tokens(extra_info_item, write_node, gsv_combination)
                            
                            # Add output filename for this write node
                            node_obj = nuke.toNode(write_node)
                            if node_obj and node_obj.Class() == "Write" and not node_obj['disable'].value():
                                output_path = self._get_node_pretty_path(node_obj, gsv_combination)
                                if output_path:
                                    node_job_info["OutputFilename0"] = output_path
                            
                            # Specify which write node to render
                            node_plugin_info["WriteNode"] = write_node
                            
                            # Override frame range if use_nodes_frame_list is enabled and frame range is available
                            if (self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range)) and write_node in write_node_frames:
                                start_frame, end_frame = write_node_frames[write_node]
                                node_job_info["Frames"] = f"{start_frame}-{end_frame}"
                            
                            # Set dependencies if using render_order_dependencies
                            if self.render_order_dependencies:
                                # Find the index of the current render order in our sorted list
                                current_index = unique_render_orders.index(render_order)
                                
                                # If this is not the lowest render order
                                if current_index > 0:
                                    # Get the immediate previous render order
                                    previous_order = unique_render_orders[current_index - 1]
                                    
                                    # Add all jobs from the previous render order as dependencies
                                    if previous_order in jobs_by_render_order:
                                        for i, dep_id in enumerate(jobs_by_render_order[previous_order]):
                                            node_job_info[f"JobDependency{i + dependency_count}"] = dep_id
                            
                            # Submit to Deadline
                            job_id = deadline.submit_job(node_job_info, node_plugin_info)
                            
                            # Track job ID by render order
                            if render_order not in jobs_by_render_order:
                                jobs_by_render_order[render_order] = []
                            jobs_by_render_order[render_order].append(job_id)
                            
                            # Track last processed render order
                            last_processed_render_order = render_order
                            
                            # Add to submitted job IDs list
                            submitted_job_ids.append(job_id)
                    
                    else:
                        # Regular submission without separate jobs/tasks
                        job_id = deadline.submit_job(job_info, plugin_info)
                        submitted_job_ids.append(job_id)
                
                logger.info(f"Submitted {len(submitted_job_ids)} jobs with GSV combinations. Last Job ID: {submitted_job_ids[-1]}")
                return submitted_job_ids[-1]  # Return the last submitted job ID
            
            # Standard submission without GSVs
            else:
                # Prepare job and plugin information
                job_info = self.prepare_job_info()
                plugin_info = self.prepare_plugin_info()
                
                # If using write nodes as tasks
                if self.write_nodes_as_tasks and self.write_nodes and len(self.write_nodes) > 1:
                    # Handle submission with write nodes as tasks
                    # Submit as a single job
                    job_id = deadline.submit_job(job_info, plugin_info)
                    logger.info(f"Job submitted with write nodes as tasks. Job ID: {job_id}")
                    return job_id
                
                # If using separate jobs or dependencies
                elif (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and self.write_nodes and len(self.write_nodes) > 1:
                    # Get write node frame ranges if use_nodes_frame_list is enabled
                    write_node_frames = {}
                    if self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range):
                        write_node_info = self._get_write_node_frame_ranges()
                        for node_name, start_frame, end_frame in write_node_info:
                            write_node_frames[node_name] = (start_frame, end_frame)
                    
                    # Get sorted write nodes
                    sorted_write_nodes = self._get_sorted_write_nodes()
                    
                    # Track job IDs by render order
                    jobs_by_render_order = {}
                    job_id = None
                    
                    # Count existing dependencies from the user-specified ones
                    dependency_count = 0
                    if self.job_dependencies:
                        dependency_count = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
                    
                    # Get render orders for all write nodes
                    nuke = nuke_utils.nuke_module()
                    write_node_render_orders = {}
                    for write_node in sorted_write_nodes:
                        node_obj = nuke.toNode(write_node)
                        render_order = 0
                        if node_obj and 'render_order' in node_obj.knobs():
                            render_order = int(node_obj['render_order'].value())
                        write_node_render_orders[write_node] = render_order
                    
                    # Find all unique render orders and sort them
                    unique_render_orders = sorted(set(write_node_render_orders.values()))
                    
                    # Submit each node based on sorting options
                    last_processed_render_order = None
                    for write_node in sorted_write_nodes:
                        # Get render order for this node
                        render_order = write_node_render_orders[write_node]
                        
                        # Clone job info for this write node
                        node_job_info = job_info.copy()
                        node_plugin_info = plugin_info.copy()
                        
                        # Check if this is a movie format and set BatchModeIsMovie if needed
                        # Skip for write_nodes_as_tasks as mentioned in the requirements
                        if not self.write_nodes_as_tasks and self._is_movie_format(write_node):
                            node_plugin_info["BatchModeIsMovie"] = "True"
                            # Set a very large chunk size to ensure entire movie renders on one machine
                            node_job_info["ChunkSize"] = "1000000"
                        
                        # Update job name to include write node
                        node_job_info["Name"] = self._replace_job_name_tokens(self.job_name_template, write_node)
                        
                        # Update comment with tokens for this write node
                        if "Comment" in node_job_info and any(token in node_job_info["Comment"] for token in ["{", "}"]):
                            node_job_info["Comment"] = self._replace_comment_tokens(self.comment, write_node)
                        
                        # Update ExtraInfo fields with tokens for this write node
                        for i, extra_info_item in enumerate(self.extra_info):
                            extra_info_key = f"ExtraInfo{i}"
                            if extra_info_key in node_job_info and any(token in extra_info_item for token in ["{", "}"]):
                                node_job_info[extra_info_key] = self._replace_extrainfo_tokens(extra_info_item, write_node)
                        
                        # Add output filename for this write node
                        node_obj = nuke.toNode(write_node)
                        if node_obj and node_obj.Class() == "Write" and not node_obj['disable'].value():
                            output_path = self._get_node_pretty_path(node_obj)
                            if output_path:
                                node_job_info["OutputFilename0"] = output_path
                        
                        # Specify which write node to render
                        node_plugin_info["WriteNode"] = write_node
                        
                        # Override frame range if use_nodes_frame_list is enabled and frame range is available
                        if (self.use_nodes_frame_list or re.search(r'\b(i|input)\b', self.frame_range)) and write_node in write_node_frames:
                            start_frame, end_frame = write_node_frames[write_node]
                            node_job_info["Frames"] = f"{start_frame}-{end_frame}"
                        
                        # Set dependencies if using render_order_dependencies
                        if self.render_order_dependencies:
                            # Find the index of the current render order in our sorted list
                            current_index = unique_render_orders.index(render_order)
                            
                            # If this is not the lowest render order
                            if current_index > 0:
                                # Get the immediate previous render order
                                previous_order = unique_render_orders[current_index - 1]
                                
                                # Add all jobs from the previous render order as dependencies
                                if previous_order in jobs_by_render_order:
                                    for i, dep_id in enumerate(jobs_by_render_order[previous_order]):
                                        node_job_info[f"JobDependency{i + dependency_count}"] = dep_id
                        
                        # Submit to Deadline
                        job_id = deadline.submit_job(node_job_info, node_plugin_info)
                        
                        # Track job ID by render order
                        if render_order not in jobs_by_render_order:
                            jobs_by_render_order[render_order] = []
                        jobs_by_render_order[render_order].append(job_id)
                        
                        # Track last processed render order
                        last_processed_render_order = render_order
                    
                    logger.info(f"Jobs submitted as separate jobs. Last Job ID: {job_id}")
                    return job_id
                else:
                    # Regular submission without separate jobs/tasks
                    job_id = deadline.submit_job(job_info, plugin_info)
                    logger.info(f"Job submitted successfully. Job ID: {job_id}")
                    return job_id
                    
        except Exception as e:
            raise SubmissionError(f"Failed to submit job: {e}")


def submit_nuke_script(script_path: str, **kwargs) -> str:
    """Submit a Nuke script to Deadline.
    
    Args:
        script_path: Path to the Nuke script file
        **kwargs: Additional submission parameters
        
          # nk2dl specific parameters
          - script_is_open: Whether the script is already open in the current Nuke session
          - submit_alphabetically: Whether to sort write nodes alphabetically by name
          - submit_in_render_order: Whether to sort write nodes by render order
          - graph_scope_variables: List of graph scope variables in either flat format:
            ["key1:value1,value2", "key2:valueA,valueB"] - generates all combinations
            Or nested format:
            [["key1:value1", "key2:valueA"], ["key1:value2", "key2:valueB"]] - specific combinations
            
          # Job Info parameters
          - job_name: Job name template (defaults to config value)
          - batch_name: Batch name template (defaults to config value)
          - priority: Job priority (defaults to config value)
          - pool: Worker pool (defaults to config value)
          - group: Worker group (defaults to config value)
          - chunk_size: Number of frames per task (defaults to config value)
          - department: Department (defaults to config value)
          - comment: Job comment (defaults to config value)
          - concurrent_tasks: Number of parallel tasks for the job (defaults to 1)
          - extra_info: List of extra info fields
          - frame_range: Frame range to render (defaults to Nuke script settings)
          - job_dependencies: Comma or space separated list of job IDs
          
          # Plugin Info parameters
          - output_path: Output directory for rendered files
          - nuke_version: Version of Nuke to use for rendering. Can be:
                          - String: "15.1"
                          - Float: 15.1 (converts to "15.1")
                          - Int: 15 (converts to "15.0")
                          If None, uses config or current Nuke version
          - use_nuke_x: Whether to use NukeX for rendering
          - use_batch_mode: Whether to use batch mode
          - render_threads: Number of render threads
          - use_gpu: Whether to use GPU for rendering
          - gpu_override: Specific GPU to use
          - max_ram_usage: Maximum RAM usage (MB)
          - enforce_render_order: Whether to enforce write node render order
          - min_stack_size: Minimum stack size (MB)
          - continue_on_error: Whether to continue rendering on error
          - reload_plugins: Whether to reload plugins between tasks
          - use_profiler: Whether to use the performance profiler
          - profile_dir: Directory for performance profile files
          - use_proxy: Whether to use proxy mode for rendering
          - write_nodes: List of write nodes to render
          - render_mode: Render mode (full, proxy)
          - write_nodes_as_tasks: Whether to submit write nodes as separate tasks
          - write_nodes_as_separate_jobs: Whether to submit write nodes as separate jobs
          - render_order_dependencies: Whether to set job dependencies based on render order
          - use_nodes_frame_list: Whether to use node-specific frame lists
    
    Returns:
        Submission ID for the submitted job
    """
    submission = NukeSubmission(script_path=script_path, **kwargs)
    return submission.submit() 