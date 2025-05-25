"""Nuke script submission to Deadline.

This module provides functionality for submitting Nuke scripts to Deadline render farm.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import re
import itertools
import datetime
import logging
import sys
import tempfile
import uuid

from ..common.config import config
from ..common.errors import SubmissionError
from ..common.logging import setup_logging
from ..common.framerange import FrameRange
from ..deadline.connection import get_connection
from . import utils as nuke_utils

# Use a more specific logger for the submission module
logger = setup_logging('nk2dl.submission')


class WriteNode:
    """Handles configuration for a single write node with optional overrides.
    
    This class provides a flexible way to specify write nodes with optional overrides
    for both job info and plugin info parameters in Deadline submissions.
    
    Supports the following input formats:
    - Single string: The name of a write node
    - Dictionary: Write node name as 'write_node' key with overrides for submission
    
    The dictionary can contain both direct Deadline job/plugin info keys or nk2dl
    submission variables that will be translated to the appropriate Deadline keys.
    
    Examples:
        # Simple write node name
        WriteNode('Write1')
        
        # Write node with direct Deadline parameter overrides
        WriteNode({
            'write_node': 'Write1',
            'Priority': 90,           # Direct Deadline job info parameter
            'ChunkSize': 5,           # Direct Deadline job info parameter
            'UseGpu': '1',            # Direct Deadline plugin info parameter
            'RamUse': '16000'         # Direct Deadline plugin info parameter
        })
        
        # Write node with nk2dl parameter name overrides (automatically translated)
        WriteNode({
            'write_node': 'Write1',
            'priority': 90,           # Translated to 'Priority'
            'chunk_size': 5,          # Translated to 'ChunkSize'
            'use_gpu': True,          # Translated to 'UseGpu': '1'
            'ram_use': 16000          # Translated to 'RamUse': '16000'
        })
        
        # Mixed direct and translated parameters
        WriteNode({
            'write_node': 'Write1',
            'priority': 90,           # Translated parameter
            'ChunkSize': 5,           # Direct parameter
            'use_gpu': True,          # Translated parameter
            'RamUse': '16000'         # Direct parameter
        })
    
    This class handles automatic translation between nk2dl parameters and Deadline job/plugin
    info keys, type conversions (e.g. boolean to "0"/"1"), and separation of job info vs. 
    plugin info parameters.
    """
    
    # Translation table from nk2dl variables to Deadline job/plugin info keys
    NK2DL_TO_DEADLINE = {
        # Job Info parameters
        'priority': 'Priority',
        'pool': 'Pool',
        'group': 'Group',
        'chunk_size': 'ChunkSize',
        'department': 'Department',
        'user_name': 'UserName',
        'comment': 'Comment',
        'concurrent_tasks': 'ConcurrentTasks',
        'frames': 'Frames',
        'job_dependencies': 'JobDependency0',  # Note: multiple dependencies need special handling
        'on_job_complete': 'OnJobComplete',
        'submit_suspended': 'InitialStatus',  # Will be set to "Suspended" if True
        'limit_groups': 'LimitGroups',
        'task_timeout': 'TaskTimeoutSeconds',
        'enable_auto_timeout': 'EnableAutoTimeout',
        'limit_worker_tasks': 'LimitConcurrentTasks',
        'batch_name': 'BatchName',
        'pre_job_script': 'PreJobScript',
        'post_job_script': 'PostJobScript',
        'pre_task_script': 'PreTaskScript',
        'post_task_script': 'PostTaskScript',
        
        # Plugin Info parameters
        'nuke_version': 'Version',
        'use_nuke_x': 'UseNukeX',  # Will be set to "1" if True, "0" if False
        'batch_mode': 'BatchMode',  # Will be set to "1" if True, "0" if False
        'threads': 'Threads',
        'use_gpu': 'UseGpu',  # Will be set to "1" if True, "0" if False
        'gpu_override': 'GpuOverride',
        'ram_use': 'RamUse',
        'enforce_render_order': 'EnforceRenderOrder',  # Will be set to "1" if True, "0" if False
        'stack_size': 'StackSize',
        'continue_on_error': 'ContinueOnError',  # Will be set to "1" if True, "0" if False
        'reload_plugins': 'ReloadPlugins',  # Will be set to "1" if True, "0" if False
        'performance_profiler': 'PerformanceProfiler',  # Will be set to "1" if True, "0" if False
        'performance_profiler_path': 'PerformanceProfilerDir',
        'output_file_path': 'OutputFilePath',
        'render_mode': 'RenderMode',  # Will be capitalized
        'views': 'Views',  # Will be comma-joined if list
    }
    
    # Boolean parameters that need translation to "0"/"1"
    BOOLEAN_PARAMS = {
        'use_nuke_x', 'batch_mode', 'use_gpu', 'enforce_render_order', 
        'continue_on_error', 'reload_plugins', 'performance_profiler' 
    }
    
    # List of known Deadline Plugin Info keys (and future ones could be added)
    PLUGIN_INFO_KEYS = {
        'Version', 'UseNukeX', 'BatchMode', 'EnforceRenderOrder', 'ContinueOnError',
        'RenderMode', 'SceneFile', 'BatchModeIsMovie', 'Views', 'Threads',
        'UseGpu', 'GpuOverride', 'RamUse', 'StackSize', 'ReloadPlugins',
        'PerformanceProfiler', 'PerformanceProfilerDir', 
        'WriteNode', 'WriteNodesAsSeparateJobs', 'OutputFilePath',
        'GraphScopeVariablesEnabled', 'GraphScopeVariables',
        'ScriptJob', 'ScriptFilename'
    }
    
    # Add prefixes for keys that have numeric suffixes
    PLUGIN_INFO_KEY_PREFIXES = {
        'WriteNode'
    }
    
    def __init__(self, write_node_input=None):
        """Initialize from various input formats.
        
        Args:
            write_node_input: Flexible input format for write node(s)
        """
        self.name = None
        self.overrides = {}
        # Separate dictionaries for job info and plugin info for clearer organization
        self.job_info_overrides = {}
        self.plugin_info_overrides = {}
        self._parse_input(write_node_input)
        
    def _parse_input(self, input_value):
        """Parse the input value into write node name and overrides."""
        # Handle None case
        if input_value is None:
            return
            
        # Single string case
        if isinstance(input_value, str):
            self.name = input_value
            
        # Dictionary case
        elif isinstance(input_value, dict):
            self._parse_dict(input_value)
            
        # Other cases are invalid
        else:
            raise ValueError(f"Invalid write node input format: {type(input_value)}")
    
    def _parse_dict(self, dict_input):
        """Parse dictionary input format and translate nk2dl variables to Deadline keys."""
        if 'write_node' in dict_input:
            self.name = dict_input['write_node']
            # Process all other keys as overrides
            for key, value in dict_input.items():
                if key != 'write_node':
                    self._add_override(key, value)
            
            # Combine job and plugin info overrides for backward compatibility
            self.overrides = {**self.job_info_overrides, **self.plugin_info_overrides}
        else:
            raise ValueError("Dictionary input must contain 'write_node' key")
    
    def _is_plugin_info_key(self, key):
        """Determine if a key belongs to plugin info rather than job info."""
        # Check direct match
        if key in self.PLUGIN_INFO_KEYS:
            return True
        
        # Check prefix match for keys with numeric suffixes
        for prefix in self.PLUGIN_INFO_KEY_PREFIXES:
            if key.startswith(prefix) and key[len(prefix):].isdigit():
                return True
        
        return False
    
    def _add_override(self, key, value):
        """Add an override, translating nk2dl variable names if necessary."""
        # Check if it's a nk2dl variable that needs translation
        if key in self.NK2DL_TO_DEADLINE:
            deadline_key = self.NK2DL_TO_DEADLINE[key]
            
            # Handle special cases
            if key == 'submit_suspended' and value:
                self.job_info_overrides[deadline_key] = "Suspended"
            elif key == 'render_mode':
                self.plugin_info_overrides[deadline_key] = value.capitalize()
            elif key == 'views' and isinstance(value, list):
                self.plugin_info_overrides[deadline_key] = ",".join(value)
            elif key in self.BOOLEAN_PARAMS:
                self.plugin_info_overrides[deadline_key] = "1" if value else "0"
            else:
                # Check if this translated key is a plugin info key
                if self._is_plugin_info_key(deadline_key):
                    self.plugin_info_overrides[deadline_key] = str(value) if not isinstance(value, str) else value
                else:
                    self.job_info_overrides[deadline_key] = str(value) if not isinstance(value, str) else value
        else:
            # Assume it's already a valid Deadline key
            # Determine if it's a plugin info or job info key
            if self._is_plugin_info_key(key):
                self.plugin_info_overrides[key] = str(value) if not isinstance(value, str) else value
            else:
                self.job_info_overrides[key] = str(value) if not isinstance(value, str) else value


class WriteNodes:
    """Collection of WriteNode objects with utility methods.
    
    This class manages a collection of WriteNode objects and provides methods to
    access their properties and overrides. It supports multiple input formats
    to make it flexible for various use cases.
    
    Examples:
        # Single write node as string
        write_nodes = WriteNodes("Write1")
        
        # Multiple write nodes as list of strings
        write_nodes = WriteNodes(["Write1", "Write2", "Write3"])
        
        # Single write node with overrides
        write_nodes = WriteNodes({
            'write_node': 'Write1',
            'priority': 90,
            'use_gpu': True
        })
        
        # Multiple write nodes with individual overrides
        write_nodes = WriteNodes([
            {
                'write_node': 'Write1',
                'priority': 90,
                'chunk_size': 5
            },
            {
                'write_node': 'Write2',
                'priority': 80,
                'use_gpu': True
            },
            "Write3"  # Mix of dict and string formats is supported
        ])
    
    The class provides methods to get write node names and retrieve overrides
    for specific write nodes when submitting to Deadline.
    """
    
    def __init__(self, input_value=None):
        self.nodes = []
        self._parse_input(input_value)
        
    def _parse_input(self, input_value):
        # Handle None case
        if input_value is None:
            return
            
        # List of strings or dictionaries
        if isinstance(input_value, list):
            for item in input_value:
                if isinstance(item, (str, dict)):
                    self.nodes.append(WriteNode(item))
                else:
                    raise ValueError(f"Invalid item in write_nodes list: {type(item)}")
        else:
            # Single WriteNode
            self.nodes.append(WriteNode(input_value))
    
    def get_names(self):
        """Get list of all write node names."""
        return [node.name for node in self.nodes if node.name]
        
    def get_overrides(self, write_node_name):
        """Get overrides for a specific write node."""
        for node in self.nodes:
            if node.name == write_node_name:
                return node.overrides
        return {}
    
    def get_job_info_overrides(self, write_node_name):
        """Get job info overrides for a specific write node."""
        for node in self.nodes:
            if node.name == write_node_name:
                return node.job_info_overrides
        return {}
    
    def get_plugin_info_overrides(self, write_node_name):
        """Get plugin info overrides for a specific write node."""
        for node in self.nodes:
            if node.name == write_node_name:
                return node.plugin_info_overrides
        return {}
    
    def __bool__(self):
        """Return True if there are any nodes defined."""
        return bool(self.nodes)
    
    def __len__(self):
        """Return the number of nodes."""
        return len(self.nodes)


class NukeSubmission:
    """Handles submission of Nuke scripts to Deadline."""

    def __init__(self, 
                # nk2dl specific parameters
                script_path: str,
                script_is_open: bool = False,
                use_parser_instead_of_nuke: bool = False,
                submit_writes_alphabetically: bool = False,
                submit_writes_in_render_order: bool = False,
                submit_script_as_auxiliary_file: Optional[bool] = None,
                render_settings_from_metadata: bool = False,

                # Build job parameters
                submission_is_build_job: bool = False,
                build_job_name: Optional[str] = None,   
                build_job_script_path: Optional[str] = None,
                pre_build_job_script: Optional[Union[str, List[str]]] = None,
                post_build_job_script: Optional[Union[str, List[str]]] = None,
                build_job_as_auxiliary_file: Optional[bool] = None,
                delete_build_job_script: Optional[bool] = None,

                # Script copying and submission parameters
                copy_script: Optional[bool] = None,
                copy_script_path: Optional[Union[str, List[str], Dict[int, str]]] = None,
                submit_copied_script: Optional[bool] = None,

                # ScriptJob parameters
                script_job_script_path: Optional[str] = None,
                
                # Machine list parameters
                machine_list: Optional[List[str]] = None,
                machine_list_is_a_deny_list: Optional[bool] = None,
                machine_allow_list: Optional[List[str]] = None,
                machine_deny_list: Optional[List[str]] = None,
                machine_limit: Optional[int] = None,
                
                # Job Info parameters
                job_name: Optional[str] = None,
                batch_name: Optional[str] = None,
                priority: Optional[int] = None,
                pool: Optional[str] = None,
                group: Optional[str] = None,
                chunk_size: Optional[int] = None,
                department: Optional[str] = None,
                user_name: Optional[str] = None,
                comment: Optional[str] = None,
                concurrent_tasks: Optional[int] = None,
                extra_info: Optional[List[str]] = None,
                frames: str = "",
                job_dependencies: Optional[str] = None,
                on_job_complete: Optional[str] = None,
                submit_suspended: bool = False,
                limit_groups: Optional[str] = None,
                task_timeout: Optional[int] = None,
                enable_auto_timeout: bool = False,
                limit_worker_tasks: bool = False,
                pre_job_script: Optional[str] = None,
                post_job_script: Optional[str] = None,
                pre_task_script: Optional[str] = None,
                post_task_script: Optional[str] = None,
                
                # Plugin Info parameters
                output_file_path: str = "",
                parse_output_paths_to_deadline: bool = False,
                nuke_version: Optional[Union[str, int, float]] = None,
                use_nuke_x: bool = False,
                batch_mode: bool = True,
                threads: Optional[int] = None,
                use_gpu: bool = False,
                gpu_override: Optional[str] = None,
                ram_use: Optional[int] = None,
                enforce_render_order: bool = True,
                stack_size: Optional[int] = None,
                continue_on_error: bool = False,
                reload_plugins: bool = False,
                performance_profiler: bool = False,
                performance_profiler_path: Optional[str] = None,
                write_nodes: Optional[Union[str, List[str], Dict[str, Any], List[Dict[str, Any]]]] = None,
                render_mode: str = "full",
                write_nodes_as_tasks: bool = False,
                write_nodes_as_separate_jobs: bool = False,
                render_order_dependencies: bool = False,
                use_node_frame_list: bool = False,
                views: Optional[List[str]] = None,
                
                # Graph Scope Variables parameters (Nuke 15.2+)
                graph_scope_variables: Optional[Union[List[str], List[List[str]]]] = None,
                
                # Environment Variables parameters
                use_current_environment: bool = False,
                environment_keys: Optional[List[str]] = None,
                environment: Optional[Dict[str, str]] = None,
                omit_environment_keys: Optional[List[str]] = None):
        
        """Initialize a Nuke script submission.
        
        Args:
            # nk2dl specific parameters
            script_path: Path to the Nuke script file
            script_is_open: Whether this script path is already open in the current Nuke session
                              (can also be also true if submitted script mirrors current Nuke session)
            use_parser_instead_of_nuke: Whether to use a parser instead of Nuke for parsing script
            submit_writes_alphabetically: Whether to sort write nodes alphabetically by name
            submit_writes_in_render_order: Whether to sort write nodes by render order
            submit_script_as_auxiliary_file: Whether to submit the script as an auxiliary file
            render_settings_from_metadata: Whether to extract submission settings from write node metadata.
                                        Metadata keys starting with 'input/nk2dl/' will be used as submission settings.
                                        For example, 'input/nk2dl/priority' will set the job priority. This is useful
                                        for pipeline integrations where artists can set job parameters directly in their
                                        Nuke scripts. Only works when write_nodes_as_separate_jobs is True.
            
            # Build job parameters
            submission_is_build_job: Whether to submit as a Python script job that calls submit_nuke_script.
                                   A build job script is generated at submission.
                                   WARNING: setting submission_is_build_job=True as the default will result 
                                   in infinite job submissions.
            build_job_script_path: Full path template for the build job script file.
                                 Contains both directory and filename with tokens.
                                 Supports tokens for both directory and filename parts:
                                 - Script directory tokens: {sdir}, {nkdir}, {scriptdir}, {nukescriptdir}
                                 - Script stem tokens: {ss}, {basename}, {stem}, {sstem}, {scriptstem}
                                 - Script name tokens: {s}, {script}, {scriptname}
                                 - Date tokens: {YYYY}, {YY}, {MM}, {DD}, {hh}, {mm}, {ss}
                                 Example: "{scriptdir}/build_jobs/{stem}_{YYYY}-{MM}-{DD}.py"
            pre_build_job_script: Path to a script to run before the build job starts,
                                or list [script_path, arg1, arg2, ...] where the first item is the script path
                                and remaining items are arguments. Script runs within the generated build job script.
            post_build_job_script: Path to a script to run after the build job completes,
                                 or list [script_path, arg1, arg2, ...] where the first item is the script path
                                 and remaining items are arguments. Script runs within the generated build job script
                                 and receives the submission results.
            build_job_as_auxiliary_file: Whether to submit the build job script as an auxiliary file (default: True)
            delete_build_job_script: Whether to delete the build job script after successful submission (default: True)

            # Script copying and submission parameters
            copy_script: Whether to copy the script before submission
            copy_script_path: Optional file path template(s) for copying the script (includes both directory and filename). Can be:
                            - String: Single file path template (e.g., "{outdir}/.farm/{scriptname}")
                            - List: Multiple file path templates
                            - Dict: With integer keys for multiple file path templates
                            Supports tokens: {script}, {output}, {basename}, {YYYY}, {MM}, {DD}, etc.
            submit_copied_script: Whether to submit the copied script
            submit_script_as_auxiliary_file: Whether to submit the script as an auxiliary file
            render_settings_from_metadata: Whether to extract submission settings from write node metadata.
                                        Metadata keys starting with 'input/nk2dl/' will be used as submission settings.
                                        For example, 'input/nk2dl/priority' will set the job priority. This is useful
                                        for pipeline integrations where artists can set job parameters directly in their
                                        Nuke scripts. Only works when write_nodes_as_separate_jobs is True.
            
            # ScriptJob parameters
            script_job_script_path: Path to a Python script to submit as a script job. When specified, 
                                   sets ScriptJob=True and ScriptFilename to the provided path.
                                   ScriptJob is built in functionality of the Deadline Nuke plugin.
                                   It runs the script as a Python script job in the nuke script editor as a
                                   terminal session but cannot take any arguments.
                                   Consider using the build job parameters instead as the build job script
                                   can use pre and post build job scripts to run the python scripts with arguments.
            
            # Machine list parameters
            machine_list: List of machine names to allow or deny
            machine_list_is_a_deny_list: Whether the machine list is a deny list
            machine_allow_list: List of machine names to allow
            machine_deny_list: List of machine names to deny
            machine_limit: Maximum number of machines to use
            
            # Job Info parameters
            job_name: Job name template (defaults to config value)
            batch_name: Batch name template (defaults to config value)
            priority: Job priority (defaults to config value)
            pool: Worker pool (defaults to config value)
            group: Worker group (defaults to config value)
            chunk_size: Number of frames per task (defaults to config value)
            department: Department (defaults to config value)
            user_name: User name (defaults to config value)
            comment: Job comment (defaults to config value)
                     Can include tokens like {script}, {ss}, {write}, {file}, etc.
            concurrent_tasks: Number of parallel tasks for the job (defaults to 1)
            extra_info: List of extra info fields with optional tokens for customization
                        Each item supports the same tokens as job_name
            frames: Frame range to render (defaults to Nuke script settings)
            job_dependencies: Comma or space separated list of job IDs
            on_job_complete: Optional job completion script
            submit_suspended: Whether to submit the job suspended
            limit_groups: Optional comma-separated list of group names to limit
            task_timeout: Optional task timeout in seconds
            enable_auto_timeout: Whether to enable auto timeout
            limit_worker_tasks: Whether to limit concurrent tasks
            pre_job_script: Path to a script to run before the job starts. Can include tokens like {script}.
            post_job_script: Path to a script to run after the job completes. Can include tokens like {script}.
            pre_task_script: Path to a script to run before each task starts. Can include tokens like {script}.
            post_task_script: Path to a script to run after each task completes. Can include tokens like {script}.
            
            # Plugin Info parameters
            output_file_path: Output directory for rendered files
            parse_output_paths_to_deadline: Whether to parse output paths to add as OutputFilename entries in job info.
                                           Defaults to True if script_is_open is True
            nuke_version: Version of Nuke to use for rendering. Can be:
                          - String: "15.1"
                          - Float: 15.1 (converts to "15.1")
                          - Int: 15 (converts to "15.0")
                          If None, uses config or current Nuke version
            use_nuke_x: Whether to use NukeX for rendering
            batch_mode: Whether to use batch mode
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
            write_nodes: Write nodes to render. Can be provided in multiple formats:
                       - Single string: The name of a write node
                       - List of strings: Multiple write node names
                       - Dictionary: Write node name with overrides, must contain 'write_node' key
                       - List of dictionaries: Multiple write nodes with their individual overrides
                       
                       The dictionary format allows overriding job and plugin info parameters
                       on a per-write-node basis. You can use either direct Deadline parameter
                       names or nk2dl parameter names (which will be translated).
                       
                       Examples:
                       ```python
                       # Simple list of write nodes (original format)
                       write_nodes = ['Write1', 'Write2']
                       
                       # Single write node with overrides
                       write_nodes = {
                           'write_node': 'Write1',   # Required key
                           'priority': 90,           # Override job priority
                           'use_gpu': True           # Enable GPU rendering
                       }
                       
                       # Multiple write nodes with individual settings
                       write_nodes = [
                           {
                               'write_node': 'Write1',
                               'priority': 90,       # Higher priority
                               'chunk_size': 5       # Smaller chunks
                           },
                           {
                               'write_node': 'Write2',
                               'priority': 50,       # Lower priority
                               'ram_use': 16000,     # More RAM
                               'threads': 16         # More threads
                           },
                           'Write3'  # Regular write node without overrides
                       ]
                       ```
            render_mode: Render mode (full, proxy)
            write_nodes_as_tasks: Whether to submit write nodes as 1 task per write node
            write_nodes_as_separate_jobs: Whether to submit write nodes as separate jobs
            render_order_dependencies: Whether to set job dependencies based on render order
            use_nodes_frame_list: Whether to use the frame range defined in write nodes with use_limit enabled
            views: List of view names to render. If None, all views will be rendered.
            
            # Graph Scope Variables parameters (Nuke 15.2+)
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
            
            # Environment Variables parameters
            use_current_environment: Whether to use the current environment variables
            environment_keys: List of environment variables to include.
                            Can use the special token "{config:extend}" as the first item
                            to include config values and then extend them with the rest of the list.
            environment: Dictionary of environment variables to add to jobs.
                       Can use the special key "{config}" with value "extend"
                       to include config values and then extend/override them with the rest of the dictionary.
            omit_environment_keys: List of environment variables to omit from jobs.
                                 Can use the special token "{config:extend}" as the first item
                                 to include config values and then extend them with the rest of the list.
        """

        self.script_will_close = False
        self.nuke_module = None
        self.submission_is_build_job = submission_is_build_job
        self.render_settings_from_metadata = render_settings_from_metadata

        # Initialize build job settings
        self.build_job_script_path = build_job_script_path if build_job_script_path is not None else config.get('submission.build_job_script_path', None)
        self.build_job_name_template = build_job_name if build_job_name else config.get('submission.build_job_name_template', "{buildjob} >> {nukescript}")
        self.pre_build_job_script = pre_build_job_script
        self.post_build_job_script = post_build_job_script
        self.build_job_as_auxiliary_file = build_job_as_auxiliary_file if build_job_as_auxiliary_file is not None else config.get('submission.build_job_as_auxiliary_file', True)
        self.delete_build_job_script = delete_build_job_script if delete_build_job_script is not None else config.get('submission.delete_build_job_script', True)

        # If render_order_dependencies is True, implicitly set write_nodes_as_separate_jobs to True as well
        if render_order_dependencies:
            write_nodes_as_separate_jobs = True
                                    
        # Check if write_nodes_as_tasks and write_nodes_as_separate_jobs are not both True
        if write_nodes_as_tasks and write_nodes_as_separate_jobs:
            raise SubmissionError("Cannot use both write_nodes_as_tasks and write_nodes_as_separate_jobs or render_order_dependencies simultaneously")
        
        # Parse write_nodes parameter using the new WriteNodes class
        try:
            self.write_nodes_config = WriteNodes(write_nodes)
            # Set self.write_nodes to be the list of names for backward compatibility
            self.write_nodes = self.write_nodes_config.get_names()
        except ValueError as e:
            raise SubmissionError(f"Invalid write_nodes format: {e}")
        
        # Check if write_nodes_as_tasks is enabled with a custom frame range but use_node_frame_list is disabled
        if write_nodes_as_tasks and frames and not use_node_frame_list and not (
            frames.lower() in ['f-l', 'first-last', 'f', 'm', 'l', 'first', 'middle', 'last', 'i', 'input'] or
            re.match(r'^\d+\-\d+$', frames)  # Allow numeric frame ranges like "1001-1100"
        ):
            raise SubmissionError("Custom frame list is not supported when submitting write nodes as separate tasks. "
                                 "Please use global (f-l) or input (i) frame ranges, or enable use_node_frame_list.")
            

        self.use_parser_instead_of_nuke = use_parser_instead_of_nuke
        self.script_is_open = script_is_open

        self.script_path = Path(script_path)
        if not self.script_path.exists():
            raise SubmissionError(f"Nuke script does not exist: {script_path}")
            
        self.frames = frames
        self.output_file_path = output_file_path
        
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
        self.batch_name_template = batch_name if batch_name else config.get('submission.batch_name_template', "{scriptname}")
        # Process batch name tokens first (since job name might depend on batch name)
        self.batch_name = self._replace_batch_name_tokens(self.batch_name_template)
        
        self.department = department if department is not None else config.get('submission.department')
        self.user_name = user_name if user_name is not None else config.get('submission.user_name')
        
        # Load comment value or template
        self.comment_template = comment if comment is not None else config.get('submission.comment_template', "")
        # We'll process comment tokens later when preparing job info
        self.comment = self.comment_template
        
        # Load ExtraInfo templates
        self.extra_info = extra_info if extra_info is not None else config.get('submission.extra_info_templates', [])
        
        # Store the job_name template for later processing
        self.job_name_template = job_name if job_name else config.get('submission.job_name_template', "{batch} / {write} / {file}")
        
        # Store job dependencies
        self.job_dependencies = job_dependencies
        
        # Store job completion options
        self.on_job_complete = on_job_complete if on_job_complete is not None else config.get('submission.on_job_complete')
        self.submit_suspended = submit_suspended if isinstance(submit_suspended, bool) else config.get('submission.submit_suspended', False)
        
        # Store resource limitation options
        self.limit_groups = limit_groups if limit_groups is not None else config.get('submission.limit_groups')
        self.task_timeout = task_timeout if task_timeout is not None else config.get('submission.task_timeout')
        self.enable_auto_timeout = enable_auto_timeout if isinstance(enable_auto_timeout, bool) else config.get('submission.enable_auto_timeout', False)
        self.limit_worker_tasks = limit_worker_tasks if isinstance(limit_worker_tasks, bool) else config.get('submission.limit_worker_tasks', False)
        
        # Script hook parameters
        self.pre_job_script = pre_job_script if pre_job_script is not None else config.get('submission.pre_job_script')
        self.post_job_script = post_job_script if post_job_script is not None else config.get('submission.post_job_script')
        self.pre_task_script = pre_task_script if pre_task_script is not None else config.get('submission.pre_task_script')
        self.post_task_script = post_task_script if post_task_script is not None else config.get('submission.post_task_script')
        
        # Nuke-specific options
        self.use_nuke_x = use_nuke_x if isinstance(use_nuke_x, bool) else config.get('submission.use_nuke_x', False)
        self.batch_mode = batch_mode if isinstance(batch_mode, bool) else config.get('submission.batch_mode', True)
        self.threads = threads if threads is not None else config.get('submission.threads')
        self.use_gpu = use_gpu if isinstance(use_gpu, bool) else config.get('submission.use_gpu', False)
        self.gpu_override = gpu_override if gpu_override is not None else config.get('submission.gpu_override')
        self.ram_use = ram_use if ram_use is not None else config.get('submission.ram_use')
        self.enforce_render_order = enforce_render_order if isinstance(enforce_render_order, bool) else config.get('submission.enforce_render_order', True)
        self.stack_size = stack_size if stack_size is not None else config.get('submission.stack_size')
        self.continue_on_error = continue_on_error if isinstance(continue_on_error, bool) else config.get('submission.continue_on_error', False)
        self.reload_plugins = reload_plugins if isinstance(reload_plugins, bool) else config.get('submission.reload_plugins', False)
        self.performance_profiler = performance_profiler if isinstance(performance_profiler, bool) else config.get('submission.performance_profiler', False)
        self.performance_profiler_path = performance_profiler_path if performance_profiler_path is not None else config.get('submission.performance_profiler_path')
        self.render_mode = render_mode if render_mode else config.get('submission.render_mode', 'full')
        self.render_order_dependencies = render_order_dependencies if isinstance(render_order_dependencies, bool) else config.get('submission.render_order_dependencies', False)
        self.job_dependencies = job_dependencies
        self.write_nodes_as_tasks = write_nodes_as_tasks if isinstance(write_nodes_as_tasks, bool) else config.get('submission.write_nodes_as_tasks', False)
        self.write_nodes_as_separate_jobs = write_nodes_as_separate_jobs if isinstance(write_nodes_as_separate_jobs, bool) else config.get('submission.write_nodes_as_separate_jobs', False)
        self.submit_writes_alphabetically = submit_writes_alphabetically if isinstance(submit_writes_alphabetically, bool) else config.get('submission.submit_writes_alphabetically', False)
        self.submit_writes_in_render_order = submit_writes_in_render_order if isinstance(submit_writes_in_render_order, bool) else config.get('submission.submit_writes_in_render_order', False)
        self.use_node_frame_list = use_node_frame_list if isinstance(use_node_frame_list, bool) else config.get('submission.use_node_frame_list', False)
        self.use_parser_instead_of_nuke = use_parser_instead_of_nuke
        
        # Store views parameter
        self.views = views if views is not None else config.get('submission.views', None)
        
        # Script copying options
        self.copy_script = copy_script if copy_script is not None else config.get('submission.copy_script', False)
        self.submit_copied_script = submit_copied_script if submit_copied_script is not None else config.get('submission.submit_copied_script', False)
        self.submit_script_as_auxiliary_file = submit_script_as_auxiliary_file if submit_script_as_auxiliary_file is not None else config.get('submission.submit_script_as_auxiliary_file', False)
        self.copied_script_paths = []
        
        # Store copy script path and name options
        self.copy_script_path = copy_script_path
        
        # Store ScriptJob parameters
        self.script_job_script_path = script_job_script_path
        
        # Initialize machine list parameters
        self.machine_allow_list, self.machine_deny_list = self._initialize_machine_lists(machine_list, machine_list_is_a_deny_list, machine_allow_list, machine_deny_list)
        
        # Store machine limit
        self.machine_limit = machine_limit if machine_limit is not None else config.get('submission.machine_limit')
        
        # Store Nuke version
        self.nuke_version = nuke_version
        
        # Store GSV settings
        self.graph_scope_variables = graph_scope_variables
        self.gsv_combinations = []
        
        # Store environment variables settings
        self.use_current_environment = use_current_environment if isinstance(use_current_environment, bool) else config.get('submission.use_current_environment', False)
        
        # Process environment variables with helper functions
        self.environment = self._process_env_dict(environment, 'submission.environment')
        self.environment_keys = self._process_env_list(environment_keys, 'submission.environment_keys')
        self.omit_environment_keys = self._process_env_list(omit_environment_keys, 'submission.omit_environment_keys')

        # Set parse_output_paths_to_deadline to True if script_is_open is True
        # unless explicitly set by the user
        self.parse_output_paths_to_deadline = parse_output_paths_to_deadline
        if script_is_open and parse_output_paths_to_deadline is False:
            self.parse_output_paths_to_deadline = True

        if self.submission_is_build_job:
            # Exit here if we are submitting as a script job because after this early exit
            # we may call on the nuke module and slow down the submission process
            # the intent of submission_is_build_job is to offload the rendering to deadline
            # and not have nk2dl call on the nuke module to handle parts of the submission
            return
        
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
        if frames:
            self.fr = FrameRange(frames)
            # If frame range contains tokens, try to substitute them
            if self.fr.has_tokens:
                # First ensure we can parse the script
                nuke = self._ensure_script_can_be_parsed()
                
                try:
                    # Only substitute tokens if it's not "i" or "input"
                    if not re.search(r'\b(i|input)\b', frames):
                        self._get_frame_range_from_nuke()
                    else:
                        # For input token, we need to specify the write node
                        if self.write_nodes and len(self.write_nodes) == 1:
                            self._get_frame_range_from_nuke(self.write_nodes[0])
                        else:
                            logger.debug(f"Input token found in frame_range object and multiple write nodes specified. We will resolve the input token later."
                                         f"writenodes: {self.write_nodes} frames: \"{frames}\"")

                except Exception as e:
                    logger.warning(f"Failed to substitute frame range tokens: {e}")
            
            # Validate frame range syntax
            if not self.fr.is_valid_syntax():
                raise SubmissionError(f"Invalid frame range syntax: {frames}")
        else:
            # Get frame range from Nuke script
            self._get_frame_range_from_nuke()
        
        # For job_name we'll do the replacement later when we have access to more information
        
        # If we have GSVs, parse them
        if self.graph_scope_variables:
            self._parse_graph_scope_variables()


    def _initialize_machine_lists(self, machine_list, machine_list_is_a_deny_list, machine_allow_list, machine_deny_list):
        """Initialize machine allow and deny lists based on provided parameters.
        
        Args:
            machine_list: Generic list of machines
            machine_list_is_a_deny_list: Whether the machine_list should be treated as a deny list
            machine_allow_list: Explicit allow list of machines
            machine_deny_list: Explicit deny list of machines
            
        Returns:
            tuple: (machine_allow_list, machine_deny_list)
            
        Raises:
            SubmissionError: If more than one machine list parameter is provided
        """
        # Check that only one of the three machine list parameters is provided
        provided_lists = [
            (machine_list is not None, "machine_list"),
            (machine_allow_list is not None, "machine_allow_list"),
            (machine_deny_list is not None, "machine_deny_list")
        ]
        provided = [name for is_provided, name in provided_lists if is_provided]

        if len(provided) > 1:
            raise SubmissionError(f"Only one of these parameters can be specified: {', '.join(provided)}")

        # Handle machine list logic from parameters
        if machine_list is not None:
            # If machine_list_is_a_deny_list is True, use it as deny list
            if machine_list_is_a_deny_list:
                return None, machine_list
            # Otherwise, use it as allow list
            else:
                return machine_list, None
        elif machine_allow_list is not None:
            return machine_allow_list, None
        elif machine_deny_list is not None:
            return None, machine_deny_list
        
        # If no machine lists were provided through parameters, check config
        config_allow_list = config.get('submission.machine_allow_list')
        config_deny_list = config.get('submission.machine_deny_list')
        
        # Check that both aren't specified in the config
        if config_allow_list and config_deny_list:
            raise SubmissionError("Cannot have both machine_allow_list and machine_deny_list specified in the configuration")
            
        if config_allow_list:
            return config_allow_list, None
        elif config_deny_list:
            return None, config_deny_list
        else:
            # No machine lists specified in parameters or config
            return None, None

    def _ensure_script_can_be_parsed(self):
        """Ensure the script is open in Nuke or available for parsing.
        
        This method will either:
        1. Use the actual Nuke Python module if use_parser_instead_of_nuke is False (default)
        2. Use our custom parser module if use_parser_instead_of_nuke is True
        
        Loading the nuke module is a time-consuming operation, so we only do it if necessary.

        Returns:
            Either the nuke module or our parser module interface
        """
        if not self.nuke_module:
            if self.use_parser_instead_of_nuke:
                # Use our custom parser module
                nuke = nuke_utils.parser_module()
                
                # If the script path is different from what's currently parsed, we need to open it
                if not self.script_is_open:
                    # Open the script
                    nuke.scriptOpen(str(self.script_path.absolute()))
                    # Mark as same as current session now
                    self.script_is_open = True
                    # Track that we opened a script
                    self.script_will_close = True
                self.nuke_module = nuke
                return nuke
            else:
                # Use the actual Nuke module
                nuke = nuke_utils.nuke_module()
                
                # If the script path is different from what's currently open in Nuke, we need to open it
                if not self.script_is_open:
                    # Open the script
                    nuke.scriptOpen(str(self.script_path.absolute()))
                    # Mark as same as current session now
                    self.script_is_open = True
                    # Track that we opened a script
                    self.script_will_close = True
                self.nuke_module = nuke
                return nuke
        else:
            return self.nuke_module

    def _all_write_nodes(self, filter_types=None):
        """Get all write nodes of specified types.
        
        Args:
            filter_types: Optional list of write node types to include.
                         Defaults to ['Write', 'DeepWrite'] if None.
                         
        Returns:
            List of write nodes matching the specified types
        """
        # Set default filter types if none provided
        if filter_types is None:
            filter_types = ['Write', 'DeepWrite']
        
        # Ensure the script is open
        nuke = self._ensure_script_can_be_parsed()
        
        # Get all nodes of the specified types
        all_write_nodes = []
        for node_type in filter_types:
            all_write_nodes.extend(nuke.allNodes(node_type))
            
        return all_write_nodes

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
            nuke = self._ensure_script_can_be_parsed()
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

    def _replace_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None, allowed_token_group_names=None) -> str:
        """Generic token replacement function for any field.
        
        Args:
            template: Template string with tokens
            write_node: Optional write node name for write-node specific tokens
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            allowed_token_group_names: Optional list of token group names to allow (all allowed if None)
            
        Returns:
            String with tokens replaced
        """
        
        # Apply GSV values if provided
        if gsv_combination:
            # Ensure the script is open
            nuke = self._ensure_script_can_be_parsed()

            # Check Nuke version before attempting to use GSV
            nuke_version_str = nuke_utils.nuke_version(self.nuke_version) if self.nuke_version else nuke_utils.nuke_version()
            try:
                major, minor = map(int, nuke_version_str.split('.')[:2])
                supports_gsv = (major > 15) or (major == 15 and minor >= 2)
            except ValueError:
                supports_gsv = False
            
            if supports_gsv:
                # Ensure the script is open
                nuke = self._ensure_script_can_be_parsed()

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
        
        # Define token groups with their names
        script_directory_tokens = ["{nkdir}", "{scriptdir}", "{nukescriptdir}"]
        script_stem_tokens = ["{nkstem}", "{scriptstem}", "{nukescriptstem}"]
        script_name_tokens = ["{nk}", "{script}", "{scriptname}","{nukescript}"]
        batch_name_tokens = ["{batch}", "{batchname}"]
        write_node_tokens = ["{write}", "{writenode}", "{writename}"]
        output_directory_tokens = ["{outdir}", "{outputdir}"]
        output_stem_tokens = ["{filestem}", "{filenamestem}", "{outstem}", "{outputstem}"]
        output_tokens = ["{file}", "{filename}", "{out}", "{output}"]
        render_order_tokens = ["{ro}", "{renderorder}"]
        frame_range_tokens = ["{x}", "{f}", "{fr}", "{range}", "{framerange}"]
        gsv_tokens = ["{g}", "{gsv}", "{gsvs}", "{GSVs}", "{graphscopevars}", "{graphscopevariables}"]
        temp_directory_tokens = ["{tmp}", "{temp}","{tmpdir}", "{tempdir}"]
        uuid_tokens = ["{uuid}"]
        build_directory_tokens = ["{builddir}", "{buildjobdir}"]
        build_name_tokens = ["{buildjob}", "{buildname}"]
        build_stem_tokens = ["{buildstem}", "{buildjobstem}"]
        date_tokens = ["{YYYY}", "{YY}", "{MM}", "{DD}", "{hh}", "{mm}", "{ss}"]

        # Create a mapping of token group names to token groups
        token_group_map = {
            'script_directory_tokens': script_directory_tokens,
            'script_stem_tokens': script_stem_tokens,
            'script_name_tokens': script_name_tokens,
            'batch_name_tokens': batch_name_tokens,
            'write_node_tokens': write_node_tokens,
            'output_directory_tokens': output_directory_tokens,
            'output_stem_tokens': output_stem_tokens,
            'output_tokens': output_tokens,
            'render_order_tokens': render_order_tokens,
            'frame_range_tokens': frame_range_tokens,
            'gsv_tokens': gsv_tokens,
            'temp_directory_tokens': temp_directory_tokens,
            'uuid_tokens': uuid_tokens,
            'build_directory_tokens': build_directory_tokens,
            'build_name_tokens': build_name_tokens,
            'build_stem_tokens': build_stem_tokens,
            'date_tokens': date_tokens
        }

        # Filter token groups if allowed_token_group_names is provided
        if allowed_token_group_names is not None:
            token_groups = [token_group_map[name] for name in allowed_token_group_names if name in token_group_map]
        else:
            # Include all token groups
            token_groups = list(token_group_map.values())
        
        # Replace tokens with their values
        for token_group in token_groups:
            for token in token_group:
                # Skip token replacement if it's not in the template
                if token not in result:
                    continue
                
                # Initialize value to empty string as a fallback
                value = ""
                
                # Get the value for each token type
                if token in script_directory_tokens:
                    value = str(self.script_path.parent)
                elif token in script_stem_tokens:
                    value = self.script_stem
                elif token in script_name_tokens:
                    value = self.script_filename
                elif token in output_stem_tokens:
                    # File stem tokens require a write node to get output path
                    if write_node:
                        # Ensure the script is open
                        nuke = self._ensure_script_can_be_parsed()

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
                    value = self.frames
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
                elif token in temp_directory_tokens:
                    # Return a temporary directory path without creating it
                    value = tempfile.gettempdir()
                elif token in uuid_tokens:
                    # Generate a UUID for temporary file identification
                    value = str(uuid.uuid4())
                elif token in build_directory_tokens:
                    # Extract directory from build job script path
                    if self.build_job_script_path:
                        value = str(Path(self.build_job_script_path).parent)
                    else:
                        value = ""
                elif token in build_name_tokens:
                    # Extract filename from build job script path
                    if self.build_job_script_path:
                        value = Path(self.build_job_script_path).name
                    else:
                        value = ""
                elif token in build_stem_tokens:
                    # Extract stem from build job script path
                    if self.build_job_script_path:
                        value = Path(self.build_job_script_path).stem
                    else:
                        value = ""                    
                elif token in date_tokens:
                    # Replace date tokens with their values
                    now = datetime.datetime.now()
                    if token == '{YYYY}':
                        value = now.strftime('%Y')
                    elif token == '{YY}':
                        value = now.strftime('%y')
                    elif token == '{MM}':
                        value = now.strftime('%m')
                    elif token == '{DD}':
                        value = now.strftime('%d')
                    elif token == '{hh}':
                        value = now.strftime('%H')
                    elif token == '{mm}':
                        value = now.strftime('%M')
                    elif token == '{ss}':
                        value = now.strftime('%S')
  
                elif write_node and token in write_node_tokens + output_tokens + render_order_tokens:
                    # Ensure the script is open
                    nuke = self._ensure_script_can_be_parsed()

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
        
        # Handle environment variable tokens with a cleaner regex approach
        # First handle PowerShell style: {$env:VAR}, {$Env:VAR}, {$ENV:VAR}
        ps_env_pattern = re.compile(r'\{\$(env|Env|ENV):([^}]+)\}')
        for match in ps_env_pattern.finditer(result):
            full_token = match.group(0)
            env_var = match.group(2)
            env_value = os.environ.get(env_var, "")
            result = result.replace(full_token, env_value)
        
        # Then handle Unix style: {$VAR}
        unix_env_pattern = re.compile(r'\{\$([^:}]+)\}')
        for match in unix_env_pattern.finditer(result):
            full_token = match.group(0)
            env_var = match.group(1)
            env_value = os.environ.get(env_var, "")
            result = result.replace(full_token, env_value)
        
        return result

    def _replace_batch_name_tokens(self, template: str) -> str:
        """Replace tokens in batch name template.
        
        Supported tokens (ONLY these are allowed):
        - script_stem_tokens: {nkstem}, {scriptstem}, {nukescriptstem}
        - script_name_tokens: {nk}, {script}, {scriptname}, {nukescript}
        
        Args:
            template: template with tokens

        Returns:
            Batch name with tokens replaced
            
        Raises:
            ValueError: If a restricted token is used in batch_name
        """
        # Batch name can ONLY use script name and script stem tokens
        allowed_token_groups = ['script_stem_tokens', 'script_name_tokens']
        return self._replace_tokens(template, allowed_token_group_names=allowed_token_groups)

    def _replace_job_name_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in job name template.
                
        Args:
            template: template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            Job name with tokens replaced
        """
        # All token groups except build tokens are allowed for job name
        allowed_token_groups = [
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'batch_name_tokens', 'write_node_tokens', 'output_directory_tokens',
            'output_stem_tokens', 'output_tokens', 'render_order_tokens',
            'frame_range_tokens', 'gsv_tokens', 'temp_directory_tokens',
            'uuid_tokens', 'date_tokens'
        ]
        return self._replace_tokens(template, write_node, gsv_combination, allowed_token_groups)

    def _replace_comment_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in comment template.
        
        Args:
            template: template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            Comment with tokens replaced
        """

        allowed_token_groups = [
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'batch_name_tokens', 'write_node_tokens', 'output_directory_tokens',
            'output_stem_tokens', 'output_tokens', 'render_order_tokens',
            'frame_range_tokens', 'gsv_tokens', 'temp_directory_tokens',
            'uuid_tokens', 'date_tokens'
        ]
        return self._replace_tokens(template, write_node, gsv_combination, allowed_token_groups)

    def _replace_extrainfo_tokens(self, template: str, write_node: Optional[str] = None, gsv_combination=None) -> str:
        """Replace tokens in extrainfo template.
        
        Args:
            template: template with tokens
            write_node: Specific write node to use for token replacement
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply

        Returns:
            ExtraInfo with tokens replaced
        """

        allowed_token_groups = [
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'batch_name_tokens', 'write_node_tokens', 'output_directory_tokens',
            'output_stem_tokens', 'output_tokens', 'render_order_tokens',
            'frame_range_tokens', 'gsv_tokens', 'temp_directory_tokens',
            'uuid_tokens', 'date_tokens'
        ]
        return self._replace_tokens(template, write_node, gsv_combination, allowed_token_groups)
    
    def _replace_build_job_script_tokens(self, template: str) -> str:
        """Replace tokens in build job script template.

        Args:
            template: template with tokens

        Returns:
            Build job script with tokens replaced
        """

        allowed_token_groups = [
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'batch_name_tokens', 'write_node_tokens', 'output_directory_tokens',
            'output_stem_tokens', 'output_tokens', 'render_order_tokens',
            'frame_range_tokens', 'gsv_tokens', 'temp_directory_tokens',
            'uuid_tokens', 'date_tokens'
        ]
        return self._replace_tokens(template, allowed_token_group_names=allowed_token_groups)
    
    def _replace_build_job_name_tokens(self, template: str) -> str:
        """Replace tokens in build job name template.
        
        Returns:
            Build job name with tokens replaced
        """
        allowed_token_groups = [
            'build_directory_tokens', 'build_name_tokens', 'build_stem_tokens',
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'batch_name_tokens', 'write_node_tokens', 'output_directory_tokens'
        ]
        return self._replace_tokens(template, allowed_token_group_names=allowed_token_groups)
        
    def _replace_copy_script_tokens(self, template: str) -> str:
        """Replace tokens in copy script path template.
        
        Args:
            template: File path template with tokens
            
        Returns:
            Copy script path with tokens replaced
        """
        allowed_token_groups = [
            'script_directory_tokens', 'script_stem_tokens', 'script_name_tokens',
            'output_directory_tokens', 'output_stem_tokens', 'output_tokens',
            'date_tokens', 'temp_directory_tokens', 'uuid_tokens'
        ]
        return self._replace_tokens(template, allowed_token_group_names=allowed_token_groups)
    
    def _get_frame_range_from_nuke(self, write_node_name: Optional[str] = None) -> None:
        """Get frame range from Nuke script using Nuke API.
        
        Args:
            write_node_name: Optional name of a write node for 'input' token
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_parsed()
        
        try:
            # Use token substitution with the write node if specified
            if self.fr.has_tokens:
                self.fr.substitute_tokens_from_nuke(write_node_name)
                self.frames = str(self.fr)
            else:
                # Get frame range from root
                root = nuke.root()
                first_frame = int(root['first_frame'].value())
                last_frame = int(root['last_frame'].value())
                
                self.frames = f"{first_frame}-{last_frame}"
                self.fr = FrameRange(self.frames)
            
            logger.debug(f"Got frame range from Nuke API: {self.frames}")
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
        nuke = self._ensure_script_can_be_parsed()
        
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
        nuke = self._ensure_script_can_be_parsed()
        node = nuke.toNode(write_node)
        
        if node and node.Class() == "Write" and 'file_type' in node.knobs():
            file_type = node['file_type'].value()
            movie_formats = ['mov', 'mxf']
            return file_type.lower() in movie_formats
            
        return False

    def _prepare_job_info(self, gsv_combination=None) -> Dict[str, Any]:
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
            "Frames": self.frames,
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
        if self.user_name:
            job_info["UserName"] = self.user_name
        if self.comment:
            # Process comment tokens if it contains any
            if any(token in self.comment for token in ["{", "}"]):
                if self.write_nodes and len(self.write_nodes) == 1:
                    job_info["Comment"] = self._replace_comment_tokens(self.comment, self.write_nodes[0], gsv_combination)
                else:
                    job_info["Comment"] = self._replace_comment_tokens(self.comment, None, gsv_combination)
            else:
                job_info["Comment"] = self.comment
                
        # Add OutputFilename entries to job info only if parse_output_paths_to_deadline is True
        if self.parse_output_paths_to_deadline:
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
        
        # Log a warning if submit_script_as_auxiliary_file is False
        if not self.submit_script_as_auxiliary_file:
            logger.warning("submit_script_as_auxiliary_file is False. Deadline will still copy the Nuke script to the worker as an auxiliary file if path mapping is enabled in the Nuke plugin under the Deadline repository plugin settings.")
        
        # Store the path for the auxiliary file if needed
        if self.submit_script_as_auxiliary_file:
            # Determine which script path to use
            script_file_path = str(self.script_path.absolute())
            if self.submit_copied_script and self.copied_script_paths:
                script_file_path = self.copied_script_paths[0]
                
            # Store the auxiliary file path for later use
            self.auxiliary_script_path = script_file_path
        
        # Add machine list to job info if specified
        if self.machine_allow_list:
            job_info["Allowlist"] = ",".join(self.machine_allow_list)
        elif self.machine_deny_list:
            job_info["Denylist"] = ",".join(self.machine_deny_list)
        
        # Add machine limit if specified
        if self.machine_limit is not None:
            job_info["MachineLimit"] = str(self.machine_limit)
        
        # Add job completion options
        if self.on_job_complete:
            job_info["OnJobComplete"] = self.on_job_complete
        
        # Add initial status if job should be submitted suspended
        if self.submit_suspended:
            job_info["InitialStatus"] = "Suspended"
            
        # Add limit groups if specified
        if self.limit_groups:
            job_info["LimitGroups"] = self.limit_groups
            
        # Add task timeout if specified
        if self.task_timeout is not None:
            job_info["TaskTimeoutSeconds"] = str(self.task_timeout)
            
        # Add auto task timeout if enabled
        if self.enable_auto_timeout:
            job_info["EnableAutoTimeout"] = "true"
            
        # Add limit concurrent tasks if enabled
        if self.limit_worker_tasks:
            job_info["LimitConcurrentTasks"] = "true"
        
        # Add script hooks if specified
        if self.pre_job_script:
            # Replace tokens in the script path if needed
            job_info["PreJobScript"] = self._replace_tokens(self.pre_job_script)
            
        if self.post_job_script:
            job_info["PostJobScript"] = self._replace_tokens(self.post_job_script)
            
        if self.pre_task_script:
            job_info["PreTaskScript"] = self._replace_tokens(self.pre_task_script)
            
        if self.post_task_script:
            job_info["PostTaskScript"] = self._replace_tokens(self.post_task_script)
        
        # Add environment variables to job info
        self._add_environment_variables_to_job_info(job_info)
        
        return job_info
    
    def _process_env_dict(self, env_dict, config_key):
        """Process environment dictionary with special config token.
        
        Args:
            env_dict: Dictionary of environment variables or None
            config_key: The config key to get default values from
            
        Returns:
            Processed environment dictionary
        """
        # If no dictionary provided, return config values
        if env_dict is None or not isinstance(env_dict, dict):
            return config.get(config_key, {})
            
        # Check for special config token
        if "{config}" in env_dict:
            mode = env_dict.pop("{config}")
            
            # If extend mode, combine config with provided values
            if mode and mode.lower() == "extend":
                result = config.get(config_key, {}).copy()
                result.update(env_dict)
                return result
                
        # Default is to use provided dictionary as-is
        return env_dict
        
    def _process_env_list(self, env_list, config_key):
        """Process environment list with special config token.
        
        Args:
            env_list: List of environment variables or None
            config_key: The config key to get default values from
            
        Returns:
            Processed environment list
        """
        # If no list provided, return config values
        if env_list is None:
            return config.get(config_key, [])
            
        # Check for special format and token
        if (isinstance(env_list, list) and env_list and 
            isinstance(env_list[0], str) and 
            env_list[0].startswith("{config:")):
            
            # Extract mode from token
            token = env_list[0]
            mode = token.split(":", 1)[1].rstrip("}")
            
            # If extend mode, combine config with provided values
            if mode.lower() == "extend":
                result = config.get(config_key, []) + env_list[1:]  # Skip the token
                return result
            else:
                # Remove the token but keep the rest
                return env_list[1:]
                
        # Default is to use provided list as-is
        return env_list
        
    def _add_environment_variables_to_job_info(self, job_info: Dict[str, Any]) -> None:
        """Add environment variables to job info according to specified parameters.
        
        Args:
            job_info: The job info dictionary to update
        """
        env_vars = {}
        
        # If use_current_environment is True, start with all current environment variables
        if self.use_current_environment:
            import os
            env_vars.update(os.environ)
            
        # If environment_keys is provided, only include those specific keys
        elif self.environment_keys:
            import os
            for key in self.environment_keys:
                if key in os.environ:
                    env_vars[key] = os.environ[key]
        
        # Add/override with specific environment variables
        if self.environment:
            env_vars.update(self.environment)
        
        # Omit specific environment variables if requested
        for key in self.omit_environment_keys:
            if key in env_vars:
                del env_vars[key]
        
        # Add environment variables to job info in Deadline format
        for i, (key, value) in enumerate(env_vars.items()):
            job_info[f"EnvironmentKeyValue{i}"] = f"{key}={value}"

    def _add_output_filenames_to_job_info(self, job_info: Dict[str, Any], gsv_combination=None) -> None:
        """Add OutputFilename# entries to job info.
        
        This allows the Deadline Monitor to display the "View Output Image" context menu option.
        
        Args:
            job_info: The job info dictionary to update
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
        """
        nuke = self._ensure_script_can_be_parsed()
        
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
            for node in self._all_write_nodes():
                if not node['disable'].value():
                    write_nodes.append(node)
            
            # Add outputs for all enabled write nodes
            for i, node in enumerate(write_nodes):
                output_path = self._get_node_pretty_path(node, gsv_combination)
                if output_path:
                    job_info[f"OutputFilename{i}"] = output_path
        
        # If using dependencies, don't add OutputFilename entries as they'll be set per job
        # They are added in the submit method when handling each write node
        
    def _prepare_plugin_info(self, gsv_combination=None) -> Dict[str, Any]:
        """Prepare plugin information for Deadline submission.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV
            
        Returns:
            Dictionary containing plugin information
        """
        # Determine which script path to use
        script_file_path = str(self.script_path.absolute())
        if self.submit_copied_script and self.copied_script_paths:
            script_file_path = self.copied_script_paths[0]
            logger.debug(f"Using copied script path: {script_file_path}")
        
        plugin_info = {
            "Version": nuke_utils.nuke_version(self.nuke_version),
            "UseNukeX": "1" if self.use_nuke_x else "0",
            "BatchMode": "1" if self.batch_mode else "0",
            "EnforceRenderOrder": "1" if self.enforce_render_order else "0",
            "ContinueOnError": "1" if self.continue_on_error else "0",
            "RenderMode": self.render_mode.capitalize()
        }
        
        # Handle SceneFile differently based on whether script is an auxiliary file
        if not self.submit_script_as_auxiliary_file:
            # If not submitting as auxiliary file, add script path to SceneFile
            plugin_info["SceneFile"] = script_file_path
        # No else clause needed - if script is an auxiliary file, it will be added to job_info as AuxFile0
        
        # Handle ScriptJob parameters
        if self.script_job_script_path:
            plugin_info["ScriptJob"] = "True"
            plugin_info["ScriptFilename"] = self.script_job_script_path
        
        # Add BatchModeIsMovie flag if needed - single write node that outputs a movie format
        # Note: When this is set, we need to update ChunkSize in job_info, but that's done in submit()
        if (self.write_nodes and len(self.write_nodes) == 1 and 
            not self.write_nodes_as_tasks and 
            self._is_movie_format(self.write_nodes[0])):
            plugin_info["BatchModeIsMovie"] = "True"
        
        # Add views if specified
        if self.views:
            plugin_info["Views"] = ",".join(self.views)
        
        # Add optional plugin settings
        if self.threads is not None:
            plugin_info["Threads"] = str(self.threads)
        if self.use_gpu:
            plugin_info["UseGpu"] = "1"
        if self.gpu_override:
            plugin_info["GpuOverride"] = self.gpu_override
        if self.ram_use is not None:
            plugin_info["RamUse"] = str(self.ram_use)
        if self.stack_size is not None:
            plugin_info["StackSize"] = str(self.stack_size)
        if self.reload_plugins:
            plugin_info["ReloadPlugins"] = "1"
        if self.performance_profiler:
            plugin_info["PerformanceProfiler"] = "1"
            if self.performance_profiler_path:
                plugin_info["PerformanceProfilerDir"] = self.performance_profiler_path
        
        # Handle write nodes differently based on submission mode
        if self.write_nodes_as_tasks and self.write_nodes:
            # For write_nodes_as_tasks: Add individual write nodes with frame ranges
            # Format: WriteNode0=Write1, WriteNode0StartFrame=X, WriteNode0EndFrame=Y, etc.
            # Note: Using WriteNodesAsSeparateJobs=True despite tasks not being separate jobs
            # This is legacy debt from the Thinkbox Deadline plugin naming
            plugin_info["WriteNodesAsSeparateJobs"] = "True"
            
            # If we have an explicit frame range with no tokens, and use_node_frame_list is False,
            # we can skip checking node frame ranges and use the explicit range for all nodes
            explicit_frame_range = (self.frames and 
                                  not self.fr.has_tokens and 
                                  not self.use_node_frame_list and 
                                  re.match(r'^\d+\-\d+$', self.frames))
            
            if explicit_frame_range:
                # Parse explicit frame range
                start_frame, end_frame = map(int, self.frames.split('-'))
                # Use the same frame range for all write nodes
                write_node_info = [(node_name, start_frame, end_frame) for node_name in self.write_nodes]
            else:
                # Get write node frame ranges
                write_node_info = self._get_write_node_frame_ranges(gsv_combination)
            
            # Add write node info to plugin info
            for i, (node_name, start_frame, end_frame) in enumerate(write_node_info):
                plugin_info[f"WriteNode{i}"] = node_name
                plugin_info[f"WriteNode{i}StartFrame"] = str(start_frame)
                plugin_info[f"WriteNode{i}EndFrame"] = str(end_frame)
                
            # Do not add UseNodeFrameList=1 as it's not a valid plugin info entry
        elif self.write_nodes and not self.render_order_dependencies:
            # For regular submission with specific write nodes
            # Format: WriteNode=Write1,Write2,Write3
            # Use a comma-separated list for all write nodes
            plugin_info["WriteNode"] = ",".join(self.write_nodes)
        
        if self.output_file_path:
            plugin_info["OutputFilePath"] = self.output_file_path
        
        # Add GSV information to plugin info if provided
        if gsv_combination:
            # Set GraphScopeVariablesEnabled to 1
            plugin_info["GraphScopeVariablesEnabled"] = "1"
            
            # Create a single comma-separated string for all GSV key-value pairs
            gsv_string = ",".join([f"{key}:{value}" for key, value in gsv_combination])
            plugin_info["GraphScopeVariables"] = gsv_string
        
        return plugin_info
    
    def _get_write_node_frame_ranges(self, gsv_combination=None) -> List[Tuple[str, int, int]]:
        """Get frame ranges for each write node using Nuke API.
        
        Behavior:
        1. If use_node_frame_list is true and the node has use_limit enabled, use the node's first/last knobs
        2. If no frames was specified (empty string), implicitly use "input" (node input frame range)
        3. If an explicit frames was provided, use that according to the match rules
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            List of tuples (node_name, start_frame, end_frame)
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_parsed()
        
        # Debug logging
        logger.debug(f"_get_write_node_frame_ranges called with frames: '{self.frames}'")
        logger.debug(f"use_node_frame_list: {self.use_node_frame_list}")
        
        write_node_info = []
        
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
        
        logger.debug(f"Processing frame ranges for {len(all_write_nodes)} write nodes: {all_write_nodes}")
        
        # Get the default frame range from Nuke root or explicit frame range
        root = nuke.root()
        root_first_frame = int(root['first_frame'].value())
        root_last_frame = int(root['last_frame'].value())
        
        logger.debug(f"Root frame range: {root_first_frame}-{root_last_frame}")
        
        # Parse explicit frame range if provided
        default_start = root_first_frame
        default_end = root_last_frame
        
        # Check if a proper frame range was provided
        has_explicit_frame_range = False
        is_input_frame_range = False
        
        if self.frames:
            # Check if it's an "input" frame range
            if re.search(r'\b(i|input)\b', self.frames):
                is_input_frame_range = True
                logger.debug("Using input frame range mode")
            # Check if it's a numeric frame range like "1001-2000"
            elif re.match(r'^\d+\-\d+$', self.frames):
                try:
                    parts = self.frames.split('-')
                    default_start = int(parts[0])
                    default_end = int(parts[1])
                    has_explicit_frame_range = True
                    logger.debug(f"Using explicit numeric frame range: {default_start}-{default_end}")
                except (ValueError, IndexError):
                    logger.warning(f"Invalid numeric frame range: {self.frames}, using root frame range")
            # Check if it's a token frame range like "f-l", "first-last", etc.
            elif (re.match(r'^[fm]\-[lm]$', self.frames) or 
                  re.match(r'^first\-last$', self.frames) or 
                  re.match(r'^first\-middle$', self.frames) or 
                  re.match(r'^middle\-last$', self.frames)):
                has_explicit_frame_range = True
                logger.debug(f"Using token-based frame range: {self.frames}")
        else:
            # If no frame range was specified, implicitly use "input"
            is_input_frame_range = True
            logger.debug("No frame range specified, implicitly using input frame range mode")
        
        try:
            # For each write node, determine its frame range
            for node_name in all_write_nodes:
                node = nuke.toNode(node_name)
                if node and node.Class() == "Write":
                    frame_range_source = "unknown"
                    # Case 1: If use_node_frame_list is true and the node has use_limit enabled,
                    # use the node's first/last knobs
                    if self.use_node_frame_list and 'use_limit' in node.knobs() and node['use_limit'].value():
                        if 'first' in node.knobs() and 'last' in node.knobs():
                            node_start = int(node['first'].value())
                            node_end = int(node['last'].value())
                            frame_range_source = "node use_limit"
                            write_node_info.append((node_name, node_start, node_end))
                            logger.debug(f"Write node {node_name}: Using frame range from node's use_limit: {node_start}-{node_end}")
                            continue
                    
                    # Case 2: If we're using input frame range (explicit or implicit),
                    # try to use the node's input frame range
                    elif is_input_frame_range:
                        try:
                            # Get frame range from input
                            node_start = node.firstFrame()
                            node_end = node.lastFrame()
                            frame_range_source = "node input"
                            write_node_info.append((node_name, node_start, node_end))
                            logger.debug(f"Write node {node_name}: Using frame range from node's input: {node_start}-{node_end}")
                            continue
                        except Exception as e:
                            logger.warning(f"Failed to get input frame range for node {node_name}: {e}")
                            # Fall back to root frame range
                            write_node_info.append((node_name, root_first_frame, root_last_frame))
                            logger.debug(f"Write node {node_name}: Falling back to root frame range: {root_first_frame}-{root_last_frame}")
                            continue
                    
                    # Case 3: If we have an explicit frame range from the user, use that
                    elif has_explicit_frame_range:
                        frame_range_source = "explicit user range"
                        write_node_info.append((node_name, default_start, default_end))
                        logger.debug(f"Write node {node_name}: Using explicit frame range: {default_start}-{default_end}")
                        continue
                    
                    # Case 4: Fall back to root frame range
                    frame_range_source = "root fallback"
                    write_node_info.append((node_name, root_first_frame, root_last_frame))
                    logger.debug(f"Write node {node_name}: Using root frame range: {root_first_frame}-{root_last_frame}")
            
            # Summary debug log
            frame_range_summary = ", ".join([f"{name}: {start}-{end}" for name, start, end in write_node_info])
            logger.debug(f"Final write node frame ranges: {frame_range_summary}")
            
            return write_node_info
        except Exception as e:
            logger.error(f"Failed to get write node frame ranges: {e}")
            raise SubmissionError(f"Failed to get write node frame ranges: {e}")
    
    def _get_write_nodes_by_render_order(self, gsv_combination=None) -> Dict[int, List[str]]:
        """Get write nodes grouped by render order using Nuke API.
        
        Args:
            gsv_combination: Optional tuple of (key, value) pairs for GSV to apply
            
        Returns:
            Dictionary mapping render orders to lists of write node names
        """
        # Ensure the script is open
        nuke = self._ensure_script_can_be_parsed()
        
        # Debug logging
        logger.debug(f"_get_write_nodes_by_render_order called with write_nodes: {self.write_nodes}")
        
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
            all_write_nodes = self._all_write_nodes()
            logger.debug(f"Found {len(all_write_nodes)} Write nodes in nukescript: {nuke.root().name()}")
            
            for node in all_write_nodes:
                node_name = node.name()
                logger.debug(f"Processing write node: {node_name}")
                
                # Get render order, default to 0
                render_order = 0
                if 'render_order' in node.knobs():
                    render_order = int(node['render_order'].value())
                
                # Store node information for sorting
                write_nodes_info.append((node_name, render_order))
            
            # If we're filtering to specific write nodes, only keep those
            if self.write_nodes:
                logger.debug(f"Filtering to specific write nodes: {self.write_nodes}")
                write_nodes_set = set(self.write_nodes)
                original_count = len(write_nodes_info)
                
                filtered_nodes = [
                    (node_name, render_order) for node_name, render_order in write_nodes_info
                    if node_name in write_nodes_set
                ]
                
                logger.debug(f"After filtering: {len(filtered_nodes)} nodes match from {original_count} total")
                
                if len(filtered_nodes) == 0:
                    # If no nodes matched, log each requested node and whether it exists
                    for requested_node in self.write_nodes:
                        exists = requested_node in [node[0] for node in write_nodes_info]
                        logger.debug(f"Requested node '{requested_node}' exists in script: {exists}")
                
                write_nodes_info = filtered_nodes
            
            # Handle sorting based on options
            if self.submit_writes_in_render_order and self.submit_writes_alphabetically:
                # Sort by render order first, then alphabetically within render order groups
                write_nodes_info.sort(key=lambda x: (x[1], x[0]))
            elif self.submit_writes_in_render_order:
                # Sort by render order only
                write_nodes_info.sort(key=lambda x: x[1])
            elif self.submit_writes_alphabetically:
                # Sort alphabetically by node name
                write_nodes_info.sort(key=lambda x: x[0])
            # Otherwise, keep the original order (or filtered order if write_nodes was specified)
            
            # Group by render order for later processing
            for node_name, render_order in write_nodes_info:
                if render_order not in write_nodes_by_order:
                    write_nodes_by_order[render_order] = []
                write_nodes_by_order[render_order].append(node_name)
            
            logger.debug(f"Final write_nodes_by_order: {write_nodes_by_order}")
            return write_nodes_by_order
        except Exception as e:
            logger.error(f"Failed to get write nodes by render order: {e}")
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
        if self.submit_writes_in_render_order:
            # Go through render orders in ascending order
            for render_order in sorted(write_nodes_by_order.keys()):
                nodes_in_order = write_nodes_by_order[render_order]
                
                # If also sorting alphabetically, sort this group
                if self.submit_writes_alphabetically:
                    nodes_in_order.sort()
                
                sorted_nodes.extend(nodes_in_order)
        else:
            # Collect all nodes
            all_nodes = []
            for render_order in sorted(write_nodes_by_order.keys()):
                all_nodes.extend(write_nodes_by_order[render_order])
            
            # If sorting alphabetically, sort the collected nodes
            if self.submit_writes_alphabetically:
                all_nodes.sort()
            
            sorted_nodes = all_nodes
            
        return sorted_nodes

    def _copy_script(self) -> List[str]:
        """Copy the Nuke script to the specified location(s) based on config.
        
        The copy_script_path parameter contains full file paths (directory + filename) with tokens.
        Multiple copies can be specified using:
        - copy_script_path = "/path/to/destination/{nkstem}.nk" (single copy)
        - copy_script_path = ["/path1/{nkstem}.nk", "/path2/{nkstem}.nk"] (multiple copies)  
        - copy_script_path = {0: "/path1/{nkstem}.nk", 1: "/path2/{nkstem}.nk"} (indexed)
        
        Available tokens:
        - Script directory: {nkdir}, {scriptdir}, {nukescriptdir}
        - Script stem: {nkstem}, {scriptstem}, {nukescriptstem} 
        - Script name: {nk}, {script}, {scriptname}, {nukescript}
        - Output directory: {outdir}, {outputdir}
        - Output stem: {filestem}, {filenamestem}, {outstem}, {outputstem}
        - Date: {YYYY}, {YY}, {MM}, {DD}, {hh}, {mm}, {ss}
        - Temp: {tmp}, {temp}, {tmpdir}, {tempdir}
        - UUID: {uuid}
        
        Returns:
            List of paths where the script was copied to
        """
        import shutil
        
        if not self.copy_script:
            logger.debug("Script copying is disabled")
            return []
            
        # Ensure script is saved
        nuke = self._ensure_script_can_be_parsed()
        
        # Get the project directory from Nuke root node
        root = nuke.root()
        project_dir = None
        try:
            project_dir = root['project_directory'].evaluate()
            logger.debug(f"Evaluated project directory: {project_dir}")
        except:
            logger.warning("Failed to evaluate project directory from Nuke root")

        copied_paths = []
        
        # Process copy_script_path parameter
        path_templates = []
        
        if self.copy_script_path is not None:
            # Handle different input formats
            if isinstance(self.copy_script_path, str):
                path_templates = [self.copy_script_path]
            elif isinstance(self.copy_script_path, list):
                path_templates = self.copy_script_path
            elif isinstance(self.copy_script_path, dict):
                # Sort by keys and extract values
                path_templates = [self.copy_script_path[key] for key in sorted(self.copy_script_path.keys())]
        else:
            # Fall back to config
            # First check for single configuration
            single_config_path = config.get('submission.script_copy_path', None)
            if single_config_path is not None:
                path_templates = [single_config_path]
            else:
                # Look for indexed configurations (copy0_path, copy1_path, ...)
                index = 0
                while True:
                    indexed_path = config.get(f'submission.script_copy{index}_path', None)
                    if indexed_path is None:
                        break
                    path_templates.append(indexed_path)
                    index += 1
                
                # If still no configurations found, use default
                if not path_templates:
                    logger.debug("No script copy configuration found, using default")
                    path_templates = ["{outdir}/.farm/{nkstem}.nk"]
        
        # Process each path template
        for path_template in path_templates:
            try:
                # Replace tokens in the full path
                resolved_path = self._replace_copy_script_tokens(path_template)
                
                # Ensure we have a valid path
                if not resolved_path:
                    logger.warning(f"Empty path after token replacement: {path_template}")
                    continue
                
                # Convert to Path object and resolve
                target_path = Path(resolved_path).resolve()
                
                # Create directory if it doesn't exist
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the script
                logger.info(f"Copying script from {self.script_path} to {target_path}")
                shutil.copy2(self.script_path, target_path)
                
                # If we have a project directory, update it in the copied script
                if project_dir is not None:
                    self._update_project_directory_in_script(target_path, project_dir)
                
                # Add to copied paths
                copied_paths.append(str(target_path))
                
            except Exception as e:
                logger.error(f"Failed to copy script using template '{path_template}': {e}")
        
        # Store the copied paths
        self.copied_script_paths = copied_paths
        logger.debug(f"Script copied to: {copied_paths}")
        
        return copied_paths
        
    def _update_project_directory_in_script(self, script_path: Union[str, Path], project_dir: str) -> None:
        """Update the project_directory knob in the copied script.
        
        This ensures that the copied script has the evaluated project directory value
        rather than a Python expression.
        
        Args:
            script_path: Path to the copied script file
            project_dir: Evaluated project directory path
        """
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Look for project_directory line and replace it
            # Pattern matches:
            # project_directory "\[python \{nuke.script_directory()\}]"
            pattern = r'(project_directory\s+)(\".*?\")'
            replacement = f'\\1"{project_dir}"'
            
            # Apply replacement
            modified_content = re.sub(pattern, replacement, content)
            
            # Write back to file
            with open(script_path, 'w') as f:
                f.write(modified_content)
                
            logger.debug(f"Updated project_directory in {script_path} to {project_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to update project_directory in copied script: {e}")
        
    def _submit_job(self, job_info, plugin_info, render_order=0, write_node=None, gsv_combination=None, auxiliary_files=None):
        """
        Submit a job to Deadline, track results, and log details.
        
        Args:
            job_info: The job info dictionary for submission
            plugin_info: The plugin info dictionary for submission
            render_order: The render order value (default: 0)
            write_node: Optional write node name
            gsv_combination: Optional GSV combination used for this submission
            auxiliary_files: Optional list of auxiliary files to include with the job
            
        Returns:
            dict: Job tracking information
            
        Raises:
            SubmissionError: If submission fails
        """
        try:
            # Submit the job with auxiliary files if provided
            deadline_response = self.deadline.submit_job(job_info, plugin_info, auxiliary_files)
            job_id = deadline_response["job_id"]
            
            # Track job ID by render order
            if render_order not in self.jobs_by_render_order:
                self.jobs_by_render_order[render_order] = []
            self.jobs_by_render_order[render_order].append(job_id)
            
            # Create job tracking info
            job_data = {
                "job_id": job_id,
                "render_order": render_order,
                "plugin_info": plugin_info,
                "job_info": job_info,
                "deadline_return": deadline_response
            }
            
            # Add to jobs list
            self.jobs.append(job_data)
            
            # Determine appropriate log message
            if self.write_nodes_as_tasks and len(self.write_nodes) > 1:
                if gsv_combination:
                    log_msg = f"GSV job submitted with write nodes as tasks. Job ID: {job_id}"
                else:
                    log_msg = f"Job submitted with write nodes as tasks. Job ID: {job_id}"
            elif write_node:
                log_msg = f"Successfully submitted job for {write_node}. Job ID: {job_id}"
            else:
                log_msg = f"Job submitted successfully. Job ID: {job_id}"
            
            # Log submission info
            logger.info(log_msg)
            logger.debug(f"Render order: {render_order}")
            logger.debug(f"Plugin info: {json.dumps(plugin_info, indent=2)}")
            logger.debug(f"Job info: {json.dumps(job_info, indent=2)}")
            logger.debug("Deadline return:")
            logger.debug(f"  job_id: {deadline_response.get('job_id', '')}")
            logger.debug(f"  connection_type: {deadline_response.get('connection_type', '')}")
            logger.debug("  raw_response:")
            
            # Log raw response formatting
            raw_response = deadline_response.get('raw_response', '')
            if raw_response:
                if isinstance(raw_response, str):
                    for line in raw_response.splitlines():
                        logger.debug(f"    {line}")
                elif isinstance(raw_response, dict):
                    logger.debug(f"    {json.dumps(raw_response, indent=2)}")
                else:
                    logger.debug(f"    Expected string or dict, got {type(raw_response)}")
                    logger.debug(f"    {raw_response}")
            
            return job_data
            
        except Exception as e:
            logger.error(f"Failed to submit job{f' for {write_node}' if write_node else ''}: {e}")
            raise SubmissionError(f"Failed to submit job: {e}")
            
    def submit(self) -> List[Dict[str, Any]]:
        """Submit the Nuke script to Deadline.
        
        Returns:
            List of dictionaries, each containing:
                - job_id (str): The Deadline job ID
                - render_order (int): The render order (0 if not fetched)
                - plugin_info (dict): The plugin info used for submission
                - job_info (dict): The job info used for submission
                - deadline_return (Any): The raw return from the Deadline submission
            
        Raises:
            SubmissionError: If submission fails
        """
        try:
            # Initialize tracking structures
            self.jobs = []
            self.jobs_by_render_order = {}
            
            # Get Deadline connection
            self.deadline = get_connection()
            logger.info(f"Connected to Deadline: {self.deadline}")
            
            # If write_nodes_as_separate_jobs is True but no write nodes are provided,
            # automatically get all enabled write nodes from the script
            if (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and not self.write_nodes:
                # Ensure the script is open
                nuke = self._ensure_script_can_be_parsed()
                
                # Get all enabled Write nodes
                enabled_write_nodes = []
                for node in self._all_write_nodes():
                    if not node['disable'].value():
                        enabled_write_nodes.append(node.name())
                
                if enabled_write_nodes:
                    self.write_nodes = enabled_write_nodes
                    logger.info(f"Automatically using {len(enabled_write_nodes)} enabled Write nodes: {', '.join(enabled_write_nodes)}")
                else:
                    logger.warning("No enabled Write nodes found in the script. Switching to normal submission.")
                    self.write_nodes_as_separate_jobs = False
                    self.render_order_dependencies = False
            
            logger.info(f"Write nodes to submit: {self.write_nodes}")
            logger.info(f"render_order_dependencies: {self.render_order_dependencies}")
            logger.info(f"write_nodes_as_separate_jobs: {self.write_nodes_as_separate_jobs}")
            
            # Copy script if requested
            if self.copy_script:
                self._copy_script()
            
            # If using GSVs, submit multiple jobs for each combination
            if self.graph_scope_variables and self.gsv_combinations:
                for gsv_combination in self.gsv_combinations:
                    # Prepare job and plugin info with GSV information
                    job_info = self._prepare_job_info(gsv_combination)
                    plugin_info = self._prepare_plugin_info(gsv_combination)
                    
                    # Prepare auxiliary files if needed
                    auxiliary_files = None
                    if hasattr(self, 'auxiliary_script_path'):
                        auxiliary_files = [self.auxiliary_script_path]
                    
                    # If using write nodes as tasks with GSVs
                    if self.write_nodes_as_tasks and self.write_nodes and len(self.write_nodes) > 1:
                        # Submit as a single job with all write nodes as tasks
                        self._submit_job(job_info, plugin_info, 0, None, gsv_combination, auxiliary_files)
                    # If using separate jobs or dependencies with GSVs
                    elif (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and self.write_nodes and len(self.write_nodes) > 1:
                        # Get write node frame ranges if use_nodes_frame_list is enabled
                        write_node_frames = {}
                        if self.use_node_frame_list or re.search(r'\b(i|input)\b', self.frames):
                            write_node_info = self._get_write_node_frame_ranges(gsv_combination)
                            for node_name, start_frame, end_frame in write_node_info:
                                write_node_frames[node_name] = (start_frame, end_frame)
                        
                        # Get sorted write nodes
                        sorted_write_nodes = self._get_sorted_write_nodes(gsv_combination)
                        
                        # Count existing dependencies from the user-specified ones
                        dependency_count = 0
                        if self.job_dependencies:
                            dependency_count = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
                        
                        # Get render orders for all write nodes
                        nuke = self._ensure_script_can_be_parsed()
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
                        for write_node in sorted_write_nodes:
                            # Get render order for this node
                            render_order = write_node_render_orders[write_node]
                            
                            # Clone job info for this write node and GSV combination
                            node_job_info = job_info.copy()
                            node_plugin_info = plugin_info.copy()
                            
                            # Apply any write node-specific overrides from the WriteNode config
                            job_overrides = self.write_nodes_config.get_job_info_overrides(write_node)
                            plugin_overrides = self.write_nodes_config.get_plugin_info_overrides(write_node)
                            
                            logger.debug(f"Job info overrides for {write_node}: {job_overrides}")
                            logger.debug(f"Plugin info overrides for {write_node}: {plugin_overrides}")
                            
                            # Apply job info overrides
                            for key, value in job_overrides.items():
                                node_job_info[key] = value
                                logger.debug(f"Applied job override: {key}={value}")
                            
                            # Apply plugin info overrides
                            for key, value in plugin_overrides.items():
                                node_plugin_info[key] = value
                                logger.debug(f"Applied plugin override: {key}={value}")
                            
                            # Extract and apply metadata settings if enabled
                            if self.render_settings_from_metadata:
                                metadata_job_overrides, metadata_plugin_overrides = self._extract_settings_from_metadata(write_node)
                                
                                logger.debug(f"Metadata job overrides for {write_node}: {metadata_job_overrides}")
                                logger.debug(f"Metadata plugin overrides for {write_node}: {metadata_plugin_overrides}")
                                
                                # Apply metadata job overrides
                                for key, value in metadata_job_overrides.items():
                                    # Only apply if not already overridden by write_nodes config
                                    if key not in job_overrides:
                                        node_job_info[key] = value
                                        logger.debug(f"Applied metadata job override: {key}={value}")
                                
                                # Apply metadata plugin overrides
                                for key, value in metadata_plugin_overrides.items():
                                    # Only apply if not already overridden by write_nodes config
                                    if key not in plugin_overrides:
                                        node_plugin_info[key] = value
                                        logger.debug(f"Applied metadata plugin override: {key}={value}")
                            
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
                            # For write_nodes_as_separate_jobs: Format is WriteNode=Write1 (single write node per job)
                            node_plugin_info["WriteNode"] = write_node
                            
                            # Override frame range if use_nodes_frame_list is enabled and frame range is available
                            if (self.use_node_frame_list or re.search(r'\b(i|input)\b', self.frames)) and write_node in write_node_frames:
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
                                    if previous_order in self.jobs_by_render_order:
                                        for i, dep_id in enumerate(self.jobs_by_render_order[previous_order]):
                                            node_job_info[f"JobDependency{i + dependency_count}"] = dep_id
                            
                            # Add environment variables to this job's info
                            self._add_environment_variables_to_job_info(node_job_info)
                            
                            # Submit the job
                            self._submit_job(node_job_info, node_plugin_info, render_order, write_node, gsv_combination)
                    
                    else:
                        # Regular submission without separate jobs/tasks
                        self._submit_job(job_info, plugin_info, 0, None, gsv_combination)
                
                logger.info(f"Submitted jobs with GSV combinations. Jobs by render order: {self.jobs_by_render_order}")
                
            # Standard submission without GSVs
            else:
                # Prepare job and plugin information
                job_info = self._prepare_job_info()
                plugin_info = self._prepare_plugin_info()
                
                logger.debug(f"Job info:\n{json.dumps(job_info, indent=4)}")
                logger.debug(f"Plugin info:\n{json.dumps(plugin_info, indent=4)}")
                
                # If using write nodes as tasks
                if self.write_nodes_as_tasks and self.write_nodes and len(self.write_nodes) > 1:
                    # Handle submission with write nodes as tasks
                    # Submit as a single job
                    try:
                        self._submit_job(job_info, plugin_info, 0, None, None)
                    except Exception as e:
                        logger.error(f"Failed to submit job with write nodes as tasks: {e}")
                        # Re-raise the exception to propagate it to the caller
                        raise SubmissionError(f"Failed to submit job: {e}")
                
                # If using separate jobs or dependencies
                elif (self.write_nodes_as_separate_jobs or self.render_order_dependencies) and self.write_nodes and len(self.write_nodes) > 1:
                    logger.info(f"Processing {len(self.write_nodes)} write nodes for separate submission")
                    
                    # Get write node frame ranges if use_nodes_frame_list is enabled
                    write_node_frames = {}
                    if self.use_node_frame_list or re.search(r'\b(i|input)\b', self.frames):
                        write_node_info = self._get_write_node_frame_ranges()
                        logger.info(f"Write node frame ranges: {write_node_info}")
                        for node_name, start_frame, end_frame in write_node_info:
                            write_node_frames[node_name] = (start_frame, end_frame)
                    
                    # Get sorted write nodes
                    sorted_write_nodes = self._get_sorted_write_nodes()
                    logger.info(f"Sorted write nodes: {sorted_write_nodes}")
                    
                    # Count existing dependencies from the user-specified ones
                    dependency_count = 0
                    if self.job_dependencies:
                        dependency_count = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
                    
                    # Get render orders for all write nodes
                    nuke = self._ensure_script_can_be_parsed()
                    write_node_render_orders = {}
                    for write_node in sorted_write_nodes:
                        node_obj = nuke.toNode(write_node)
                        render_order = 0
                        if node_obj and 'render_order' in node_obj.knobs():
                            render_order = int(node_obj['render_order'].value())
                        write_node_render_orders[write_node] = render_order
                    
                    logger.info(f"Write node render orders: {write_node_render_orders}")
                    
                    # Find all unique render orders and sort them
                    unique_render_orders = sorted(set(write_node_render_orders.values()))
                    logger.info(f"Unique render orders: {unique_render_orders}")
                    
                    # Submit each node based on sorting options
                    for write_node in sorted_write_nodes:
                        logger.info(f"Processing write node: {write_node}")
                        
                        # Get render order for this node
                        render_order = write_node_render_orders[write_node]
                        
                        # Clone job info for this write node
                        node_job_info = job_info.copy()
                        node_plugin_info = plugin_info.copy()
                        
                        # Apply any write node-specific overrides from the WriteNode config
                        job_overrides = self.write_nodes_config.get_job_info_overrides(write_node)
                        plugin_overrides = self.write_nodes_config.get_plugin_info_overrides(write_node)
                        
                        logger.debug(f"Job info overrides for {write_node}: {job_overrides}")
                        logger.debug(f"Plugin info overrides for {write_node}: {plugin_overrides}")
                        
                        # Apply job info overrides
                        for key, value in job_overrides.items():
                            node_job_info[key] = value
                            logger.debug(f"Applied job override: {key}={value}")
                        
                        # Apply plugin info overrides
                        for key, value in plugin_overrides.items():
                            node_plugin_info[key] = value
                            logger.debug(f"Applied plugin override: {key}={value}")
                        
                        # Extract and apply metadata settings if enabled
                        if self.render_settings_from_metadata:
                            metadata_job_overrides, metadata_plugin_overrides = self._extract_settings_from_metadata(write_node)
                            
                            logger.debug(f"Metadata job overrides for {write_node}: {metadata_job_overrides}")
                            logger.debug(f"Metadata plugin overrides for {write_node}: {metadata_plugin_overrides}")
                            
                            # Apply metadata job overrides
                            for key, value in metadata_job_overrides.items():
                                # Only apply if not already overridden by write_nodes config
                                if key not in job_overrides:
                                    node_job_info[key] = value
                                    logger.debug(f"Applied metadata job override: {key}={value}")
                            
                            # Apply metadata plugin overrides
                            for key, value in metadata_plugin_overrides.items():
                                # Only apply if not already overridden by write_nodes config
                                if key not in plugin_overrides:
                                    node_plugin_info[key] = value
                                    logger.debug(f"Applied metadata plugin override: {key}={value}")
                        
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
                        # For write_nodes_as_separate_jobs: Format is WriteNode=Write1 (single write node per job)
                        node_plugin_info["WriteNode"] = write_node
                        
                        # Override frame range if use_nodes_frame_list is enabled and frame range is available
                        if (self.use_node_frame_list or re.search(r'\b(i|input)\b', self.frames)) and write_node in write_node_frames:
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
                                if previous_order in self.jobs_by_render_order:
                                    for i, dep_id in enumerate(self.jobs_by_render_order[previous_order]):
                                        node_job_info[f"JobDependency{i + dependency_count}"] = dep_id
                        
                        # Add environment variables to this job's info
                        self._add_environment_variables_to_job_info(node_job_info)
                        
                        logger.info(f"Submitting job for write node {write_node}")
                        logger.debug(f"Job info for {write_node}: {node_job_info}")
                        logger.debug(f"Plugin info for {write_node}: {node_plugin_info}")
                        
                        # Prepare auxiliary files if needed
                        auxiliary_files = None
                        if hasattr(self, 'auxiliary_script_path'):
                            auxiliary_files = [self.auxiliary_script_path]
                        
                        # Submit the job
                        try:
                            self._submit_job(node_job_info, node_plugin_info, render_order, write_node, None, auxiliary_files)
                        except Exception as e:
                            logger.error(f"Failed to submit job for write node {write_node}: {e}")
                    
                    logger.info(f"Jobs submitted as separate jobs. Jobs by render order: {self.jobs_by_render_order}")
                else:
                    # Regular submission without separate jobs/tasks
                    try:
                        # For single write node case, apply its overrides if any
                        if self.write_nodes and len(self.write_nodes) == 1:
                            write_node = self.write_nodes[0]
                            
                            # Get job and plugin info overrides
                            job_overrides = self.write_nodes_config.get_job_info_overrides(write_node)
                            plugin_overrides = self.write_nodes_config.get_plugin_info_overrides(write_node)
                            
                            # Apply overrides
                            for key, value in job_overrides.items():
                                job_info[key] = value
                            
                            for key, value in plugin_overrides.items():
                                plugin_info[key] = value
                        else:
                            write_node = None
                        
                        # Prepare auxiliary files if needed
                        auxiliary_files = None
                        if hasattr(self, 'auxiliary_script_path'):
                            auxiliary_files = [self.auxiliary_script_path]
                        
                        self._submit_job(job_info, plugin_info, 0, write_node, None, auxiliary_files)
                    except Exception as e:
                        logger.error(f"Failed to submit regular job: {e}")
                        # Re-raise the exception to propagate it to the caller
                        raise SubmissionError(f"Failed to submit job: {e}")
            
            # Close the script if we opened it
            if self.script_will_close:
                nuke = self._ensure_script_can_be_parsed()
                nuke.scriptClose()
                nuke.scriptClear()
                self.script_will_close = False
                logger.info(f"Script {self.script_path} closed after submission")
            
            return self.jobs
                    
        except Exception as e:
            # Close the script if we opened it, even if submission failed
            if self.script_will_close:
                try:
                    nuke = self._ensure_script_can_be_parsed()
                    nuke.scriptClose()
                    self.script_will_close = False
                except:
                    pass  # Don't let script closing error mask the original error
            
            raise SubmissionError(f"Failed to submit job: {e}")

    def submit_as_build_job(self) -> List[Dict[str, Any]]:
        """Create and submit a Python script job that calls submit_nuke_script.
        
        Creates a temporary Python script file that calls submit_nuke_script with
        all the current instance parameters, then submits it to Deadline as a 
        Nuke python job. This will create a single job regardless of how many
        write nodes are specified - the actual write node separation will happen
        when the script executes on the farm.
        
        Returns:
            List of dictionaries with job information, matching the format of regular submission.
            
        Raises:
            SubmissionError: If script job submission fails
        """
        # The build_job_as_auxiliary_file parameter controls whether the Python script is submitted
        # as an auxiliary file to Deadline:
        # - When True (default): The script is stored as an auxiliary file, allowing Deadline
        #   to recover the job if it fails, since the script will be re-copied to the worker.
        # - When False: The script path is only set in BuildJobsFilename. If the script gets 
        #   deleted (e.g., by the script itself), the job can't be restarted or requeued.
        
        logger.info(f"Creating script job for Nuke script: {self.script_path}")
        
        # Generate timestamp for default path generation
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        nukescript_stem = self.script_path.stem
        
        # Determine full script path with directory and name
        if self.build_job_script_path:
            # Replace tokens in path
            build_job_script_path = self._replace_build_job_script_tokens(self.build_job_script_path)
            
            # If the path doesn't contain a file extension, add .py
            if not os.path.splitext(build_job_script_path)[1]:
                build_job_script_path += ".py"
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(build_job_script_path)), exist_ok=True)
        else:
            # Default to script directory with timestamp
            script_dir = str(self.script_path.parent)
            build_job_script_name = f"{nukescript_stem}_build_job_{timestamp}.py"
            build_job_script_path = os.path.join(script_dir, build_job_script_name)
            self.build_job_script_path = build_job_script_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(build_job_script_path)), exist_ok=True)
        
        logger.debug(f"Creating build job script file at: {build_job_script_path}")
        
        # Process pre and post build job scripts, which can be either a string or a list of strings
        pre_build_script_info = None
        if self.pre_build_job_script:
            # Handle either string or list format
            if isinstance(self.pre_build_job_script, str):
                # Single script path, no arguments
                script_path_with_tokens = self.pre_build_job_script
                resolved_path = self._replace_build_job_script_tokens(script_path_with_tokens)
                pre_build_script_info = {'path': resolved_path, 'args': []}
                logger.debug(f"Pre-build job script: {resolved_path}")
            elif isinstance(self.pre_build_job_script, list) and len(self.pre_build_job_script) > 0:
                # List format: [script_path, arg1, arg2, ...]
                script_path_with_tokens = self.pre_build_job_script[0]
                resolved_path = self._replace_build_job_script_tokens(script_path_with_tokens)
                args = self.pre_build_job_script[1:]
                pre_build_script_info = {'path': resolved_path, 'args': args}
                logger.debug(f"Pre-build job script: {resolved_path} with arguments: {args}")
            else:
                logger.warning(f"Invalid pre_build_job_script format: {self.pre_build_job_script}")
        
        post_build_script_info = None
        if self.post_build_job_script:
            # Handle either string or list format
            if isinstance(self.post_build_job_script, str):
                # Single script path, no arguments
                script_path_with_tokens = self.post_build_job_script
                resolved_path = self._replace_build_job_script_tokens(script_path_with_tokens)
                post_build_script_info = {'path': resolved_path, 'args': []}
                logger.debug(f"Post-build job script: {resolved_path}")
            elif isinstance(self.post_build_job_script, list) and len(self.post_build_job_script) > 0:
                # List format: [script_path, arg1, arg2, ...]
                script_path_with_tokens = self.post_build_job_script[0]
                resolved_path = self._replace_build_job_script_tokens(script_path_with_tokens)
                args = self.post_build_job_script[1:]
                post_build_script_info = {'path': resolved_path, 'args': args}
                logger.debug(f"Post-build job script: {resolved_path} with arguments: {args}")
            else:
                logger.warning(f"Invalid post_build_job_script format: {self.post_build_job_script}")
        
        # Use a regular file context to create the script
        try:
            with open(build_job_script_path, 'w') as script_file_obj:
                # Add proper encoding header for Python 3 compatibility
                script_file_obj.write("#!/usr/bin/env python\n")
                script_file_obj.write("# -*- coding: utf-8 -*-\n\n")
                
                # Set environment variable to signal we're in a build job
                script_file_obj.write("# Set environment variable to signal we're in a build job to other nk2dl modules\n")
                script_file_obj.write("import os\n")
                script_file_obj.write("os.environ['NK2DL_IN_BUILD_JOB'] = 'true'\n\n")
                script_file_obj.write("# Debug the environment variables\n")
                script_file_obj.write("import sys\n")
                script_file_obj.write("import time\n")
                script_file_obj.write("import logging\n")
                

                # Write the import statements
                script_file_obj.write("from nk2dl import submit_nuke_script\n")
                
                # Add logging setup
                script_file_obj.write("\n# Set up logging\n")
                script_file_obj.write("logger = logging.getLogger('nk2dl.submission.submit_as_build_job')\n")
                script_file_obj.write("logger.setLevel(logging.INFO)\n")
                script_file_obj.write("\n# Prevent propagation to root logger to avoid double logging\n")
                script_file_obj.write("logger.propagate = False\n")
                script_file_obj.write("handler = logging.StreamHandler(sys.stdout)\n")
                script_file_obj.write("\n# Use a simpler formatter without timestamp when running inside another logger like Deadline\n")
                script_file_obj.write("formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')\n")
                script_file_obj.write("handler.setFormatter(formatter)\n")
                script_file_obj.write("logger.addHandler(handler)\n")
                
                # Add verification of build job environment variable
                script_file_obj.write("\n# Verify the build job environment variable is set correctly\n")
                script_file_obj.write("build_job_env = os.environ.get('NK2DL_IN_BUILD_JOB', 'not set') # required for pre/post build scripts\n")
                script_file_obj.write("build_job_aux_env = os.environ.get('NK2DL_BUILD_JOB_IS_AUXILIARY', 'not set') # optional\n")
                script_file_obj.write("logger.info(f\"NK2DL_IN_BUILD_JOB environment variable is '{build_job_env}'\")\n")
                script_file_obj.write("logger.info(f\"NK2DL_BUILD_JOB_IS_AUXILIARY environment variable is '{build_job_aux_env}'\")\n")
                
                # Log script location
                script_file_obj.write("\n# Log script location\n")
                script_file_obj.write("logger.info(f\"Build job script started: {os.path.abspath(__file__)}\")\n\n")

                # Add function to run scripts with proper error handling
                if pre_build_script_info or post_build_script_info:
                    script_file_obj.write("def run_script(script_path, script_type, args=None, results=None):\n")
                    script_file_obj.write("    \"\"\"Run a Python script with proper error handling.\n")
                    script_file_obj.write("    \n")
                    script_file_obj.write("    Args:\n")
                    script_file_obj.write("        script_path: Path to the script to run\n")
                    script_file_obj.write("        script_type: Type of script ('pre-build' or 'post-build')\n")
                    script_file_obj.write("        args: Optional list of arguments to pass to the script\n")
                    script_file_obj.write("        results: Optional submission results to pass to the script\n")
                    script_file_obj.write("    \"\"\"\n")
                    script_file_obj.write("    # Check if we should run scripts from the same directory as build script\n")
                    script_file_obj.write("    build_job_aux_env = os.environ.get('NK2DL_BUILD_JOB_IS_AUXILIARY', '').lower() == 'true'\n")
                    script_file_obj.write("    original_script_path = script_path\n")
                    script_file_obj.write("    \n")
                    script_file_obj.write("    if build_job_aux_env:\n")
                    script_file_obj.write("        # Get directory of this build job script\n")
                    script_file_obj.write("        build_script_dir = os.path.dirname(os.path.abspath(__file__))\n")
                    script_file_obj.write("        # Get just the filename of the script\n")
                    script_file_obj.write("        script_filename = os.path.basename(script_path)\n")
                    script_file_obj.write("        # Create new path in the same directory as build script\n")
                    script_file_obj.write("        script_path = os.path.join(build_script_dir, script_filename)\n")
                    script_file_obj.write("        logger.info(f\"Using script from build job directory: {script_path}\")\n")
                    script_file_obj.write("    \n")
                    script_file_obj.write("    if not os.path.exists(script_path):\n")
                    script_file_obj.write("        if build_job_aux_env and original_script_path != script_path:\n")
                    script_file_obj.write("            logger.warning(f\"Script not found in build job directory: {script_path}\")\n")
                    script_file_obj.write("            logger.info(f\"Falling back to original script path: {original_script_path}\")\n")
                    script_file_obj.write("            script_path = original_script_path\n")
                    script_file_obj.write("            \n")
                    script_file_obj.write("            if not os.path.exists(script_path):\n")
                    script_file_obj.write("                logger.error(f\"Cannot run {script_type} script: File not found: {script_path}\")\n")
                    script_file_obj.write("                return False\n")
                    script_file_obj.write("        else:\n")
                    script_file_obj.write("            logger.error(f\"Cannot run {script_type} script: File not found: {script_path}\")\n")
                    script_file_obj.write("            return False\n")
                    script_file_obj.write("    \n")
                    script_file_obj.write("    try:\n")
                    script_file_obj.write("        if args:\n")
                    script_file_obj.write("            logger.info(f\"Running {script_type} script: {script_path} with args: {args}\")\n")
                    script_file_obj.write("        else:\n")
                    script_file_obj.write("            logger.info(f\"Running {script_type} script: {script_path}\")\n")
                    script_file_obj.write("        # Create a locals dict with common variables that might be useful\n")
                    script_file_obj.write("        script_locals = {\n")
                    script_file_obj.write("            'os': os,\n")
                    script_file_obj.write("            'sys': sys,\n")
                    script_file_obj.write("            'logger': logger,\n")
                    script_file_obj.write("            'logging': logging,\n")
                    script_file_obj.write("            'args': args or [],\n")
                    script_file_obj.write("        }\n")
                    script_file_obj.write("        # Add results if available (for post-build script)\n")
                    script_file_obj.write("        if results is not None:\n")
                    script_file_obj.write("            script_locals['results'] = results\n")
                    script_file_obj.write("            script_locals['job_ids'] = [job.get('job_id', 'unknown') for job in results]\n")
                    script_file_obj.write("        \n")
                    script_file_obj.write("        with open(script_path, 'r') as script_file:\n")
                    script_file_obj.write("            script_content = script_file.read()\n")
                    script_file_obj.write("        \n")
                    script_file_obj.write("        # Execute the script with the locals dictionary\n")
                    script_file_obj.write("        exec(script_content, script_locals)\n")
                    script_file_obj.write("        logger.info(f\"Completed {script_type} script: {script_path}\")\n")
                    script_file_obj.write("        return True\n")
                    script_file_obj.write("    except Exception as e:\n")
                    script_file_obj.write("        logger.error(f\"Error running {script_type} script {script_path}: {e}\", exc_info=True)\n")
                    script_file_obj.write("        return False\n\n")

                # Write a main function to ensure proper execution
                script_file_obj.write("def main():\n")
                
                # Declare results as global before fetching them
                script_file_obj.write("    # Declare global variable for results\n")
                script_file_obj.write("    global results\n\n")
                
                # Log start of submission process
                script_file_obj.write("    logger.info(\"Starting Nuke script submission\")\n")
                
                # Add a global variable to store the original and running script paths
                script_file_obj.write("    # Store original and running script paths as globals for potential self-deletion\n")
                script_file_obj.write("    ORIGINAL_SCRIPT_PATH = None\n")
                script_file_obj.write("    RUNNING_SCRIPT_PATH = None\n\n")
                script_file_obj.write("    try:\n")
                script_file_obj.write("        import os\n")
                script_file_obj.write("        RUNNING_SCRIPT_PATH = os.path.abspath(__file__)\n")
                script_file_obj.write("    except NameError:\n")
                script_file_obj.write("        logger.warning(\"Could not determine running script path\")\n\n")
                
                # Properly escape the path to avoid \n being interpreted as newline
                build_job_script_path_escaped = str(build_job_script_path).replace('\\', '\\\\')
                script_file_obj.write(f"    ORIGINAL_SCRIPT_PATH = \"{build_job_script_path_escaped}\"\n")
                script_file_obj.write(f"    logger.info(\"Submitting script: {build_job_script_path_escaped}\")\n")
                script_file_obj.write(f"    logger.info(f\"Running from: {{RUNNING_SCRIPT_PATH}}\")\n\n")
                
                # Add pre-build job script execution if provided
                pre_build_path_escaped = None
                if pre_build_script_info:
                    pre_build_path_escaped = pre_build_script_info['path'].replace('\\', '\\\\')
                    args_repr = repr(pre_build_script_info['args'])
                    script_file_obj.write(f"    # Run pre-build job script\n")
                    script_file_obj.write(f"    pre_script_success = run_script(\"{pre_build_path_escaped}\", \"pre-build\", args={args_repr})\n")
                    script_file_obj.write(f"    if not pre_script_success:\n")
                    script_file_obj.write(f"        logger.warning(\"Pre-build script failed, but continuing with submission\")\n\n")
                
                # Create the function call with all parameters
                script_path_str = str(self.script_path)
                script_path_str = script_path_str.replace("\\", "/")
                args_str = [f'    "{script_path_str}"']
                
                logger.debug("Generating script arguments for submit_nuke_script")
                
                # Map all instance attributes to kwargs for the script
                # Only add parameters that aren't using default values to keep the script clean
                args_str.append(f"    script_is_open=False")
                if self.use_parser_instead_of_nuke:
                    args_str.append(f"    use_parser_instead_of_nuke={self.use_parser_instead_of_nuke}")
                if self.submit_writes_alphabetically:
                    args_str.append(f"    submit_writes_alphabetically={self.submit_writes_alphabetically}")
                if self.submit_writes_in_render_order:
                    args_str.append(f"    submit_writes_in_render_order={self.submit_writes_in_render_order}")
                if self.submit_script_as_auxiliary_file is not None:
                    args_str.append(f"    submit_script_as_auxiliary_file={self.submit_script_as_auxiliary_file}")
                if self.render_settings_from_metadata:
                    args_str.append(f"    render_settings_from_metadata={self.render_settings_from_metadata}")
                if self.build_job_script_path:
                    logger.warning(f"build_job_script_path should have been popped from args before this point: {self.build_job_script_path}")
                    args_str.append(f'    build_job_script_path="{self.build_job_script_path}"')
                if self.pre_build_job_script:
                    args_str.append(f"    pre_build_job_script={repr(self.pre_build_job_script)}")
                if self.post_build_job_script:
                    args_str.append(f"    post_build_job_script={repr(self.post_build_job_script)}")
                if self.copy_script is not None:
                    args_str.append(f"    copy_script={self.copy_script}")
                if self.copy_script_path is not None:
                    args_str.append(f"    copy_script_path={repr(self.copy_script_path)}")
                if self.submit_copied_script is not None:
                    args_str.append(f"    submit_copied_script={self.submit_copied_script}")
                if self.machine_allow_list:
                    args_str.append(f"    machine_allow_list={repr(self.machine_allow_list)}")
                if self.machine_deny_list:
                    args_str.append(f"    machine_deny_list={repr(self.machine_deny_list)}")
                if self.machine_limit is not None:
                    args_str.append(f"    machine_limit={self.machine_limit}")
                if self.job_name_template != config.get('submission.job_name_template', "{batch} / {write} / {file}"):
                    args_str.append(f'    job_name="{self.job_name_template}"')
                if self.batch_name_template != config.get('submission.batch_name_template', "{script_stem}"):
                    args_str.append(f'    batch_name="{self.batch_name_template}"')
                if self.priority != config.get('submission.priority', 50):
                    args_str.append(f"    priority={self.priority}")
                if self.pool != config.get('submission.pool', 'nuke'):
                    args_str.append(f'    pool="{self.pool}"')
                if self.group != config.get('submission.group', 'none'):
                    args_str.append(f'    group="{self.group}"')
                if self.chunk_size != config.get('submission.chunk_size', 10):
                    args_str.append(f"    chunk_size={self.chunk_size}")
                if self.department is not None:
                    args_str.append(f'    department="{self.department}"')
                if self.user_name:
                    args_str.append(f'    user_name="{self.user_name}"')
                else:
                    import getpass
                    args_str.append(f'    user_name="{getpass.getuser()}"')
                if self.comment_template:
                    args_str.append(f'    comment="{self.comment_template}"')
                if self.concurrent_tasks != config.get('submission.concurrent_tasks', 1):
                    args_str.append(f"    concurrent_tasks={self.concurrent_tasks}")
                if self.extra_info:
                    args_str.append(f"    extra_info={repr(self.extra_info)}")
                if self.frames:
                    args_str.append(f'    frames="{self.frames}"')
                if self.job_dependencies:
                    args_str.append(f'    job_dependencies="{self.job_dependencies}"')
                if self.on_job_complete:
                    args_str.append(f'    on_job_complete="{self.on_job_complete}"')
                if self.submit_suspended:
                    args_str.append(f"    submit_suspended={self.submit_suspended}")
                if self.limit_groups:
                    args_str.append(f'    limit_groups="{self.limit_groups}"')
                if self.task_timeout is not None:
                    args_str.append(f"    task_timeout={self.task_timeout}")
                if self.enable_auto_timeout:
                    args_str.append(f"    enable_auto_timeout={self.enable_auto_timeout}")
                if self.limit_worker_tasks:
                    args_str.append(f"    limit_worker_tasks={self.limit_worker_tasks}")
                if self.pre_job_script:
                    args_str.append(f'    pre_job_script="{self.pre_job_script}"')
                if self.post_job_script:
                    args_str.append(f'    post_job_script="{self.post_job_script}"')
                if self.pre_task_script:
                    args_str.append(f'    pre_task_script="{self.pre_task_script}"')
                if self.post_task_script:
                    args_str.append(f'    post_task_script="{self.post_task_script}"')
                if self.output_file_path:
                    args_str.append(f'    output_file_path="{self.output_file_path}"')
                if self.use_nuke_x:
                    args_str.append(f"    use_nuke_x={self.use_nuke_x}")
                if not self.batch_mode:  # Default is True, so only include if False
                    args_str.append(f"    batch_mode={self.batch_mode}")
                if self.threads is not None:
                    args_str.append(f"    threads={self.threads}")
                if self.use_gpu:
                    args_str.append(f"    use_gpu={self.use_gpu}")
                if self.gpu_override:
                    args_str.append(f'    gpu_override="{self.gpu_override}"')
                if self.ram_use is not None:
                    args_str.append(f"    ram_use={self.ram_use}")
                if not self.enforce_render_order:  # Default is True, so only include if False
                    args_str.append(f"    enforce_render_order={self.enforce_render_order}")
                if self.stack_size is not None:
                    args_str.append(f"    stack_size={self.stack_size}")
                if self.continue_on_error:
                    args_str.append(f"    continue_on_error={self.continue_on_error}")
                if self.reload_plugins:
                    args_str.append(f"    reload_plugins={self.reload_plugins}")
                if self.performance_profiler:
                    args_str.append(f"    performance_profiler={self.performance_profiler}")
                if self.performance_profiler_path:
                    args_str.append(f'    performance_profiler_path="{self.performance_profiler_path}"')
                if self.write_nodes:
                    args_str.append(f"    write_nodes={repr(self.write_nodes)}")
                if self.render_mode != config.get('submission.render_mode', 'full'):
                    args_str.append(f'    render_mode="{self.render_mode}"')
                if self.write_nodes_as_tasks:
                    args_str.append(f"    write_nodes_as_tasks={self.write_nodes_as_tasks}")
                if self.write_nodes_as_separate_jobs:
                    args_str.append(f"    write_nodes_as_separate_jobs={self.write_nodes_as_separate_jobs}")
                if self.render_order_dependencies:
                    args_str.append(f"    render_order_dependencies={self.render_order_dependencies}")
                if self.use_node_frame_list:
                    args_str.append(f"    use_node_frame_list={self.use_node_frame_list}")
                if self.views:
                    args_str.append(f"    views={repr(self.views)}")
                if self.graph_scope_variables:
                    args_str.append(f"    graph_scope_variables={repr(self.graph_scope_variables)}")
                if self.use_current_environment:
                    args_str.append(f"    use_current_environment={self.use_current_environment}")
                if self.environment_keys:
                    args_str.append(f"    environment_keys={repr(self.environment_keys)}")
                if self.environment:
                    args_str.append(f"    environment={repr(self.environment)}")
                if self.omit_environment_keys:
                    args_str.append(f"    omit_environment_keys={repr(self.omit_environment_keys)}")
                
                # Write the function call with proper indentation
                script_file_obj.write(f"    results = submit_nuke_script(\n")
                script_file_obj.write(",\n".join(args_str))
                script_file_obj.write("\n    )\n\n")
                
                # Log submission results
                script_file_obj.write("    job_ids = [job.get('job_id', 'unknown') for job in results]\n")
                script_file_obj.write("    logger.info(f\"Successfully submitted {len(results)} jobs with IDs: {job_ids}\")\n\n")
                
                # Add post-build job script execution if provided
                post_build_path_escaped = None
                if post_build_script_info:
                    post_build_path_escaped = post_build_script_info['path'].replace('\\', '\\\\')
                    args_repr = repr(post_build_script_info['args'])
                    script_file_obj.write(f"    # Run post-build job script\n")
                    script_file_obj.write(f"    post_script_success = run_script(\"{post_build_path_escaped}\", \"post-build\", args={args_repr}, results=results)\n")
                    script_file_obj.write(f"    if not post_script_success:\n")
                    script_file_obj.write(f"        logger.warning(\"Post-build script failed\")\n\n")
                
                # Add cleanup logic if delete_build_job_script is True - delete file immediately after submission
                if self.delete_build_job_script:
                    script_file_obj.write("    # Delete the script file immediately after successful submission\n")
                    script_file_obj.write("    try:\n")
                    script_file_obj.write("        logger.info(f\"Deleting script file: {ORIGINAL_SCRIPT_PATH}\")\n")
                    script_file_obj.write("        # Rename the file first to avoid permission issues\n")
                    script_file_obj.write("        tmp_file = ORIGINAL_SCRIPT_PATH + '.tmp'\n")
                    script_file_obj.write("        os.rename(ORIGINAL_SCRIPT_PATH, tmp_file)\n")
                    script_file_obj.write("        os.remove(tmp_file)\n")
                    script_file_obj.write("        logger.info(\"Script file successfully deleted\")\n")
                    if not self.build_job_as_auxiliary_file:
                        script_file_obj.write("        logger.warning(\"WARNING: If this Deadline job fails after this point, it cannot resume because build_job_as_auxiliary_file=False\")\n")
                    script_file_obj.write("    except Exception as e:\n")
                    script_file_obj.write("        logger.warning(f\"Failed to delete script file: {e}\")\n")
                    if not self.build_job_as_auxiliary_file:
                        script_file_obj.write("        logger.warning(\"WARNING: If this Deadline job fails after this point, it may not be able to resume because build_job_as_auxiliary_file=False\")\n")

                script_file_obj.write("    # Enter loop printing READY FOR INPUT every 5 seconds\n")
                script_file_obj.write("    # Deadline will read this and exit the process\n")
                script_file_obj.write("    logger.info(\"Entering monitoring loop - will be terminated by Deadline\")\n")
                script_file_obj.write("    loop_count = 0\n")
                script_file_obj.write("    while True:\n")
                script_file_obj.write("        print(\"READY FOR INPUT\")\n")
                script_file_obj.write("        # Log every 12 cycles (approximately once per minute at 5 seconds per cycle)\n")
                script_file_obj.write("        loop_count += 1\n")
                script_file_obj.write("        if loop_count % 12 == 0:\n")
                script_file_obj.write("            logger.info(f\"Build job still running - {loop_count // 12} minute(s) elapsed\")\n")
                script_file_obj.write("        time.sleep(5)\n\n")

                script_file_obj.write("if __name__ == \"__main__\":\n")
                script_file_obj.write("    try:\n")
                script_file_obj.write("        logger.info(\"Build job script execution starting\")\n")
                script_file_obj.write("        main()\n")
                script_file_obj.write("    except Exception as e:\n")
                script_file_obj.write("        logger.error(f\"Error in build job script: {e}\", exc_info=True)\n")
                script_file_obj.write("        raise\n\n")

                logger.debug(f"Python script content generated with {len(args_str)} parameters")
            
            logger.info(f"Created script job Python file: {build_job_script_path}")
            
            # Get Deadline connection
            deadline = get_connection()
            
            # Prepare job and plugin info
            job_info = {
                'Plugin': 'Nuke',
                'Name': self._replace_build_job_name_tokens(self.build_job_name_template),
                'Frames': '1',
                'ChunkSize': '1'
            }
            
            # Add other job info parameters if provided
            if self.pool:
                job_info['Pool'] = self.pool
            if self.group:
                job_info['Group'] = self.group
            if self.priority:
                job_info['Priority'] = self.priority
            if self.department:
                job_info['Department'] = self.department
            if self.user_name:
                job_info['UserName'] = self.user_name
            if self.comment:
                job_info['Comment'] = self.comment
            if self.batch_name:
                job_info['BatchName'] = self.batch_name
            if self.concurrent_tasks:
                job_info['ConcurrentTasks'] = self.concurrent_tasks
            if self.limit_groups:
                job_info['LimitGroups'] = self.limit_groups
            if self.job_dependencies:
                job_info['JobDependencies'] = self.job_dependencies
            if self.on_job_complete:
                job_info['OnJobComplete'] = self.on_job_complete
            
            plugin_info = {
                'Version': nuke_utils.nuke_version(self.nuke_version),
                # Always specify the script path in plugin info even if it's also an auxiliary file
                'BuildJobsFilename': os.path.abspath(build_job_script_path),  # Make sure the path is absolute
                'SingleFramesOnly': 'True'
            }
            
            logger.debug(f"Submitting script job with job_info: {json.dumps(job_info, indent=2)}")
            logger.debug(f"Plugin info: {json.dumps(plugin_info, indent=2)}")
            
            # Determine auxiliary files based on settings
            auxiliary_files = []
            
            # Add the build job Python script as an auxiliary file if requested
            if self.build_job_as_auxiliary_file:
                if os.path.exists(os.path.abspath(build_job_script_path)):
                    auxiliary_files.append(os.path.abspath(build_job_script_path))
                    logger.debug(f"Added build job script as auxiliary file: {build_job_script_path}")
                else:
                    logger.warning(f"Build job script not found but was requested: {build_job_script_path}.")
                if pre_build_path_escaped:
                    if os.path.exists(os.path.abspath(pre_build_path_escaped)):
                        auxiliary_files.append(os.path.abspath(pre_build_path_escaped))
                        logger.debug(f"Added pre-build script as auxiliary file: {pre_build_path_escaped}")
                    else:
                        logger.warning(f"Pre-build script not found but was requested: {pre_build_path_escaped}")
                if post_build_path_escaped:
                    if os.path.exists(os.path.abspath(post_build_path_escaped)):
                        auxiliary_files.append(os.path.abspath(post_build_path_escaped))
                        logger.debug(f"Added post-build script as auxiliary file: {post_build_path_escaped}")
                    else:
                        logger.warning(f"Post-build script not found but was requested: {post_build_path_escaped}")
                logger.debug(f"Added build job script as auxiliary file: {build_job_script_path}")
            else:
                logger.debug(f"Script file is not added as auxiliary file. Using BuildJobsFilename only: {build_job_script_path}")
                logger.warning(f"When build_job_as_auxiliary_file=False, job recovery may be limited if the script file is deleted")
            
            # Also add the original Nuke script as an auxiliary file if requested
            if self.submit_script_as_auxiliary_file:
                script_file_path = str(self.script_path.absolute())
                if self.submit_copied_script and self.copied_script_paths:
                    script_file_path = os.path.abspath(self.copied_script_paths[0])
                
                # Add to the list of auxiliary files
                auxiliary_files.append(script_file_path)
                logger.debug(f"Added Nuke script as auxiliary file: {script_file_path}")
            
            # Store the auxiliary files for direct submission
            script_aux_files = auxiliary_files
            
            # Submit the job with auxiliary files
            response = deadline.submit_job(job_info, plugin_info, script_aux_files)
            job_id = response['job_id']
            
            logger.info(f"Successfully submitted script job with ID: {job_id}")
            logger.debug(f"Build job will handle write nodes: {self.write_nodes}")
            
            # Format the return value to match the expected format
            return [{
                'job_id': job_id,
                'render_order': 0,
                'plugin_info': plugin_info,
                'job_info': job_info,
                'deadline_return': response
            }]
            
        except Exception as e:
            logger.error(f"Failed to submit script job: {e}", exc_info=True)
            raise SubmissionError(f"Failed to submit script job: {e}")

    def _extract_settings_from_metadata(self, write_node_name):
        """Extract submission settings from write node metadata.
        
        Looks for metadata keys starting with 'input/nk2dl/' and converts them to
        submission settings. These settings can be in either Deadline job/plugin info format
        or nk2dl parameter format.
        
        Args:
            write_node_name: Name of the write node to extract metadata from
            
        Returns:
            Tuple of (job_info_overrides, plugin_info_overrides) dictionaries
        """
        if not self.render_settings_from_metadata:
            return {}, {}
            
        # Ensure the script is open
        nuke = self._ensure_script_can_be_parsed()
        
        # Get the write node
        node = nuke.toNode(write_node_name)
        if not node or node.Class() != "Write":
            logger.warning(f"Cannot extract metadata from {write_node_name}: Node not found or not a Write node")
            return {}, {}
            
        # Get metadata from the write node
        try:
            metadata = node.metadata()
            if not metadata:
                logger.debug(f"No metadata found for write node {write_node_name}")
                return {}, {}
                
            # Create temporary WriteNode to handle translation of parameters
            metadata_settings = {}
            
            # Extract nk2dl metadata keys
            for key, value in metadata.items():
                if key.startswith('input/nk2dl/'):
                    # Remove the 'input/nk2dl/' prefix
                    setting_key = key[len('input/nk2dl/'):]
                    metadata_settings[setting_key] = value
                    
            logger.debug(f"Extracted metadata settings from {write_node_name}: {metadata_settings}")
            
            # Create a WriteNode object to handle parameter translation
            temp_node = WriteNode({"write_node": write_node_name})
            
            # Add each metadata setting to the WriteNode
            for key, value in metadata_settings.items():
                temp_node._add_override(key, value)
                
            # Return job and plugin info overrides
            return temp_node.job_info_overrides, temp_node.plugin_info_overrides
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from write node {write_node_name}: {e}")
            return {}, {}


def submit_nuke_script(script_path: str, **kwargs) -> List[Dict[str, Any]]:
    """Submit a Nuke script to Deadline.
    
    Args:
        script_path: Path to the Nuke script file
        **kwargs: Additional submission parameters
        
          # nk2dl specific parameters
          - script_is_open: Whether this script path is already open in the current Nuke session
          - use_parser_instead_of_nuke: Whether to use a parser instead of Nuke for parsing script
          - submit_writes_alphabetically: Whether to sort write nodes alphabetically by name
          - submit_writes_in_render_order: Whether to sort write nodes by render order
          - submit_script_as_auxiliary_file: Whether to submit the script as an auxiliary file
          - render_settings_from_metadata: Whether to extract submission settings from write node metadata
                                         stored as 'input/nk2dl/parameter_name'
          - copy_script: Whether to make copies of the script before submission
          - copy_script_path: Optional file path template(s) for copying the script. Can be:
                            - String: Single file path template (e.g., "{outdir}/.farm/{nkstem}.nk")
                            - List: Multiple file path templates
                            - Dict: With integer keys for multiple file path templates
                            Supports tokens: {script}, {output}, {nkstem}, {YYYY}, {MM}, {DD}, etc.
          - submit_copied_script: Whether to use the copied script path in the submission
          - submission_is_build_job: Whether to submit as a Python script job that calls submit_nuke_script
          - build_job_script_path: Full path template for the build job script file.
                                 Supports tokens for both directory and filename parts:
                                 - Script directory tokens: {sdir}, {nkdir}, {scriptdir}, {nukescriptdir}
                                 - Script stem tokens: {ss}, {basename}, {stem}, {sstem}, {scriptstem}
                                 - Script name tokens: {s}, {script}, {scriptname}
                                 - Date tokens: {YYYY}, {YY}, {MM}, {DD}, {hh}, {mm}, {ss}
                                 Example: "{scriptdir}/build_jobs/{stem}_{YYYY}-{MM}-{DD}.py"
          - build_job_as_auxiliary_file: Whether to submit the build job script as an auxiliary file (default: True).
                                      When True, the job can be recovered if it fails since Deadline
                                      will re-copy the script to the worker. When False, the job cannot
                                      be restarted if the script file is deleted.
          - delete_build_job_script: Whether to automatically delete the build job script after execution (default: True)
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
          - user_name: User name (defaults to config value)
          - comment: Job comment (defaults to config value)
          - concurrent_tasks: Number of parallel tasks for the job (defaults to 1)
          - extra_info: List of extra info fields
          - frames: Frame range to render (defaults to Nuke script settings)
          - job_dependencies: Comma or space separated list of job IDs
          - on_job_complete: Optional job completion script
          - submit_suspended: Whether to submit the job suspended
          - limit_groups: Optional comma-separated list of group names to limit
          - task_timeout: Optional task timeout in seconds
          - enable_auto_timeout: Whether to enable auto timeout
          - limit_worker_tasks: Whether to limit concurrent tasks
          - pre_job_script: Path to a script to run before the job starts. Can include tokens like {script}.
          - post_job_script: Path to a script to run after the job completes. Can include tokens like {script}.
          - pre_task_script: Path to a script to run before each task starts. Can include tokens like {script}.
          - post_task_script: Path to a script to run after each task completes. Can include tokens like {script}.
          
          # Plugin Info parameters
          - output_file_path: Output directory for rendered files
          - parse_output_paths_to_deadline: Whether to parse output paths to add as OutputFilename entries in job info.
                                           Defaults to True if script_is_open is True
          - nuke_version: Version of Nuke to use for rendering. Can be:
                          - String: "15.1"
                          - Float: 15.1 (converts to "15.1")
                          - Int: 15 (converts to "15.0")
                          If None, uses config or current Nuke version
          - use_nuke_x: Whether to use NukeX for rendering
          - batch_mode: Whether to use batch mode
          - threads: Number of render threads
          - use_gpu: Whether to use GPU for rendering
          - gpu_override: Specific GPU to use
          - ram_use: Maximum RAM usage (MB)
          - enforce_render_order: Whether to enforce write node render order
          - stack_size: Minimum stack size (MB)
          - continue_on_error: Whether to continue rendering on error
          - reload_plugins: Whether to reload plugins between tasks
          - performance_profiler: Whether to use the performance profiler
          - performance_profiler_path: Directory for performance profile files
          - write_nodes: Write nodes to render. Can be provided in multiple formats:
                       - Single string: The name of a write node
                       - List of strings: Multiple write node names
                       - Dictionary: Write node name with overrides, must contain 'write_node' key
                       - List of dictionaries: Multiple write nodes with their individual overrides
                         
                         The dictionary format allows overriding job and plugin info parameters
                         on a per-write-node basis. You can use either direct Deadline parameter
                         names or nk2dl parameter names (which will be translated).
                         
                         Examples:
                         ```python
                         # Simple list of write nodes (original format)
                         write_nodes = ['Write1', 'Write2']
                         
                         # Single write node with overrides
                         write_nodes = {
                             'write_node': 'Write1',   # Required key
                             'priority': 90,           # Override job priority
                             'use_gpu': True           # Enable GPU rendering
                         }
                         
                         # Multiple write nodes with individual settings
                         write_nodes = [
                             {
                                 'write_node': 'Write1',
                                 'priority': 90,       # Higher priority
                                 'chunk_size': 5       # Smaller chunks
                             },
                             {
                                 'write_node': 'Write2',
                                 'priority': 50,       # Lower priority
                                 'ram_use': 16000,     # More RAM
                                 'threads': 16         # More threads
                             },
                             'Write3'  # Regular write node without overrides
                         ]
                         ```
          - render_mode: Render mode (full, proxy, both). When set to "both", two separate submissions are created - one with "full" and one with "proxy". Note: The "both" option is only available in the submit_nuke_script function, not directly in NukeSubmission.
          - write_nodes_as_tasks: Whether to submit write nodes as separate tasks
          - write_nodes_as_separate_jobs: Whether to submit write nodes as separate jobs
          - render_order_dependencies: Whether to set job dependencies based on render order
          - use_node_frame_list: Whether to use node-specific frame lists
          - views: List of view names to render. If None, all views will be rendered.
          
          # Environment Variables parameters
          - use_current_environment: Whether to use the current environment variables
          - environment_keys: List of environment variables to include.
                            Can use the special token "{config:extend}" as the first item
                            to include config values and then extend them with the rest of the list.
          - environment: Dictionary of environment variables to add to jobs.
                       Can use the special key "{config}" with value "extend"
                       to include config values and then extend/override them with the rest of the dictionary.
          - omit_environment_keys: List of environment variables to omit from jobs.
                                 Can use the special token "{config:extend}" as the first item
                                 to include config values and then extend them with the rest of the list.
          
          # Machine List parameters
          - machine_list: List of machine names to allow or deny based on machine_list_is_a_deny_list
          - machine_list_is_a_deny_list: Whether the machine_list is a deny list (default: False, treat as allow list)
          - machine_allow_list: Alternative to machine_list, explicitly specifies an allow list
          - machine_deny_list: List of machine names to deny (cannot be used with machine_allow_list/machine_list)
          - machine_limit: Maximum number of machines that can work on the job simultaneously
    
    Returns:
        List of dictionaries, each containing:
            - job_id (str): The Deadline job ID
            - render_order (int): The render order (0 if not fetched)
            - plugin_info (dict): The plugin info used for submission
            - job_info (dict): The job info used for submission
            - deadline_return (Any): The raw return from the Deadline submission
    """

    # Handle the "both" render_mode by submitting two separate jobs
    if kwargs.get('render_mode', "").lower() == 'both':
        logger.info("Render mode 'both' specified. Submitting two separate jobs for 'full' and 'proxy' modes.")
        
        # Make a copy of kwargs to avoid modifying the original
        full_kwargs = kwargs.copy()
        full_kwargs['render_mode'] = 'full'
        
        proxy_kwargs = kwargs.copy()
        proxy_kwargs['render_mode'] = 'proxy'
        
        # Submit jobs with full and proxy modes
        full_jobs = submit_nuke_script(script_path, **full_kwargs)
        proxy_jobs = submit_nuke_script(script_path, **proxy_kwargs)
        
        # Combine and return the results
        return full_jobs + proxy_jobs

    if kwargs.get('submission_is_build_job', False):
        # WARNING: setting default to True will result in infinite job submissions
        submission = NukeSubmission(script_path=script_path, **kwargs)
        return submission.submit_as_build_job()

    # Extract parameters needed for determining script path
    script_is_open = kwargs.get('script_is_open', False)
    use_parser_instead_of_nuke = kwargs.get('use_parser_instead_of_nuke', False)
    
    # Check if we need to parse the script
    from .subprocess import script_parsing_required
    
    requires_parsing = script_parsing_required(**kwargs)
    
    # Check if we're running inside the Nuke GUI
    running_in_nuke_gui = False
    in_build_job = os.environ.get('NK2DL_IN_BUILD_JOB', 'false').lower() == 'true'
    
    try:
        import psutil
        current_process = psutil.Process(os.getpid())
        parent_process_name = current_process.name()
        running_in_nuke_gui = "Nuke" in parent_process_name
        logger.debug(f"Parent process name: {parent_process_name}, running in Nuke GUI: {running_in_nuke_gui}, in_build_job: {in_build_job}")
    except Exception as e:
        logger.warning(f"Failed to check if running in Nuke GUI: {e}")

    # Only launch subprocess if script parsing is needed AND we're in the Nuke GUI AND script not open in current session
    # AND we're not in a build job
    launch_subprocess = False
    if requires_parsing and running_in_nuke_gui and not script_is_open and not in_build_job:
        launch_subprocess = True
        
    if not running_in_nuke_gui or launch_subprocess:
        # If parse_output_paths_to_deadline is not set, set it to True if not explicitly set to False
        # If we're not running in the Nuke GUI, we need launch nuke or nuke parser anyway to parse the script
        # So we might as well parse the output paths to deadline as well
        parse_output_paths_to_deadline = kwargs.get('parse_output_paths_to_deadline', True)
        kwargs['parse_output_paths_to_deadline']=parse_output_paths_to_deadline
        logger.debug(f"Running without Nuke GUI, setting parse_output_paths_to_deadline: {parse_output_paths_to_deadline}")

    if launch_subprocess:
        logger.info(f"Submitted script is different from currently open script. Script parsing required and running in Nuke GUI. Launching subprocess for {script_path}")
        from .subprocess import submit_script_via_subprocess
        return submit_script_via_subprocess(script_path, use_parser_instead_of_nuke, **kwargs)
    
    if not running_in_nuke_gui or in_build_job:
        logger.info(f"Not running in Nuke GUI{'.' if not running_in_nuke_gui else ' or running in build job mode.'} Proceeding with submission within the current process for {script_path}")
        # Set script_is_open to False to ensure the script is loaded if it needs to be parsed
        # By definition, if we're not running in the Nuke GUI, there is no open script in the current session
        # We wont deal with cases where nuke.scriptOpen() has been run in a python session, as this is an edge case
        kwargs['script_is_open']=False

    # Proceed with submission within the current process if submitted script is same as currently open script
    submission = NukeSubmission(script_path=script_path, **kwargs)
    return submission.submit() 
