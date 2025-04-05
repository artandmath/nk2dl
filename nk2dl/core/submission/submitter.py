"""
DeadlineSubmitter class for handling the main submission logic.
"""
import os
import tempfile
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from .job_info import JobInfo
from .plugin_info import NukePluginInfo


class DeadlineSubmitter:
    """
    Main class for submitting Nuke jobs to Deadline.
    """
    def __init__(self) -> None:
        self.job_info = JobInfo()
        self.plugin_info = NukePluginInfo()
        
        # Get Deadline command from environment
        self.deadline_command = self._get_deadline_command()
        
    def _get_deadline_command(self) -> str:
        """
        Get the path to the Deadline command executable.
        
        Returns:
            Path to the Deadline command executable
        
        Raises:
            RuntimeError: If DEADLINE_PATH is not set or Deadline command not found
        """
        deadline_path = os.getenv("DEADLINE_PATH")
        if not deadline_path:
            raise RuntimeError("DEADLINE_PATH environment variable is not set")
            
        if os.name == "nt":  # Windows
            cmd_path = os.path.join(deadline_path, "deadlinecommand.exe")
        else:  # Unix/Linux
            cmd_path = os.path.join(deadline_path, "deadlinecommand")
            
        if not os.path.exists(cmd_path):
            raise RuntimeError(f"Deadline command not found at: {cmd_path}")
            
        return cmd_path
        
    def _call_deadline_command(self, args: List[str]) -> str:
        """
        Execute the Deadline command with the given arguments.
        
        Args:
            args: List of arguments to pass to the Deadline command
            
        Returns:
            Output of the Deadline command
            
        Raises:
            RuntimeError: If the Deadline command fails
        """
        # Build the command line
        cmd = [self.deadline_command] + args
        
        # Print the command being run
        print(f"Running Deadline command: {' '.join(cmd)}")
        
        # Run the command
        try:
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            print(f"Command output: {result}")
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Deadline command failed with exit code {e.returncode}: {e.output}"
            print(error_msg)
            raise RuntimeError(error_msg)
            
    def _extract_metadata_overrides(self, write_nodes: List[Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract Deadline job submission overrides from write node metadata.
        
        Looks for metadata keys with the following prefixes:
        - 'input/deadline/jobInfo/' - For JobInfo settings
        - 'input/deadline/pluginInfo/' - For PluginInfo settings
        
        Args:
            write_nodes: List of write nodes to extract metadata from
            
        Returns:
            Dictionary mapping node names to dictionaries of override settings
        """
        metadata_overrides = {}
        
        for node in write_nodes:
            node_name = node.fullName()
            metadata_overrides[node_name] = {}
            
            # Skip nodes without metadata
            if not hasattr(node, 'metadata') or not callable(node.metadata):
                continue
                
            # Get all metadata keys for this node
            try:
                metadata = node.metadata()
                if not metadata:
                    continue
            except:
                # If there's an error getting metadata, skip this node
                print(f"Warning: Could not get metadata for {node_name}")
                continue
                
            # Extract job info overrides
            job_info_prefix = 'input/deadline/jobInfo/'
            plugin_info_prefix = 'input/deadline/pluginInfo/'
            
            for key in metadata:
                # Process JobInfo overrides
                if key.startswith(job_info_prefix):
                    param_name = key[len(job_info_prefix):]
                    metadata_overrides[node_name][f'job_info.{param_name}'] = metadata[key]
                
                # Process PluginInfo overrides
                elif key.startswith(plugin_info_prefix):
                    param_name = key[len(plugin_info_prefix):]
                    metadata_overrides[node_name][f'plugin_info.{param_name}'] = metadata[key]
        
        return metadata_overrides
        
    def _camel_to_snake_case(self, camel_str: str) -> str:
        """
        Convert a camelCase string to snake_case.
        
        Args:
            camel_str: A string in camelCase format
            
        Returns:
            The string converted to snake_case
        """
        # Handle the case where the first character is uppercase (ex: ChunkSize -> chunk_size)
        if camel_str and camel_str[0].isupper():
            camel_str = camel_str[0].lower() + camel_str[1:]
            
        # Insert underscores before uppercase characters and convert them to lowercase
        result = ""
        for char in camel_str:
            if char.isupper():
                result += '_' + char.lower()
            else:
                result += char
                
        return result
            
    def submit_job(self, 
                  nuke_script_path: str, 
                  write_nodes: Optional[List[Any]] = None,
                  write_node_names: Optional[List[str]] = None,
                  dependencies: Optional[Dict[str, List[str]]] = None,
                  progress_callback: Optional[Callable[[str, str], None]] = None,
                  metadata_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
                  **kwargs) -> Union[str, Dict[str, str]]:
        """
        Submit a Nuke script to Deadline.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            write_nodes: Optional list of write node objects to include in submission
            write_node_names: Optional list of write node names to include in submission
            dependencies: Optional dictionary of node name to list of dependency node names
            progress_callback: Optional callback function to report progress
            metadata_overrides: Optional dictionary of node name to override settings
                                or True to extract metadata from write nodes
            **kwargs: Additional job and plugin settings to override defaults
            
        Returns:
            Job ID returned by Deadline if single job, or dictionary mapping
            write node names to job IDs if multiple jobs
            
        Raises:
            ValueError: If required settings are missing or invalid
            RuntimeError: If the submission fails
        """
        # Validate inputs
        if not os.path.exists(nuke_script_path):
            raise ValueError(f"Nuke script not found: {nuke_script_path}")
            
        # Update job name if not specified
        if "name" not in kwargs:
            kwargs["name"] = os.path.basename(nuke_script_path)

        # Handle metadata extraction if requested
        if metadata_overrides is True and write_nodes:
            metadata_overrides = self._extract_metadata_overrides(write_nodes)
            if metadata_overrides:
                print("\nMetadata Overrides:")
                for node_name, overrides in metadata_overrides.items():
                    if overrides:
                        print(f"{node_name}:")
                        for key, value in overrides.items():
                            print(f"  {key} = {value}")
        
        # Determine if we're submitting multiple jobs or a single job
        if write_nodes or write_node_names:
            return self._submit_multiple_jobs(
                nuke_script_path,
                write_nodes,
                write_node_names,
                dependencies,
                progress_callback,
                metadata_overrides,
                **kwargs
            )
        else:
            # Submit a single job with the entire script
            return self._submit_single_job(nuke_script_path, **kwargs)
            
    def _submit_single_job(self, nuke_script_path: str, **kwargs) -> str:
        """
        Submit a single job to Deadline.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            **kwargs: Additional job and plugin settings to override defaults
            
        Returns:
            Job ID returned by Deadline
        """
        # Update settings
        job_settings = {k: v for k, v in kwargs.items() if hasattr(self.job_info, k)}
        plugin_settings = {k: v for k, v in kwargs.items() if hasattr(self.plugin_info, k)}
        
        self.job_info.update(job_settings)
        self.plugin_info.update(plugin_settings)
        
        # Set scene file in plugin info
        self.plugin_info.scene_file = nuke_script_path
        
        # Create temp directory for job files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate job files
            job_file = os.path.join(temp_dir, "job_info.job")
            plugin_file = os.path.join(temp_dir, "plugin_info.job")
            
            self.job_info.to_file(job_file)
            self.plugin_info.to_file(plugin_file)
            
            # Submit to Deadline
            args = [job_file, plugin_file]
            if not self.job_info.submit_suspended:
                args.append(nuke_script_path)
                
            result = self._call_deadline_command(args)
            
            # Parse job ID from result
            for line in result.splitlines():
                if line.startswith("JobID="):
                    return line[6:].strip()
                    
            raise RuntimeError("Failed to get job ID from submission result")
    
    def _submit_multiple_jobs(self, 
                             nuke_script_path: str,
                             write_nodes: Optional[List[Any]] = None,
                             write_node_names: Optional[List[str]] = None,
                             dependencies: Optional[Dict[str, List[str]]] = None,
                             progress_callback: Optional[Callable[[str, str], None]] = None,
                             metadata_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
                             **kwargs) -> Dict[str, str]:
        """
        Submit multiple jobs to Deadline, one for each write node.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            write_nodes: Optional list of write node objects to include in submission
            write_node_names: Optional list of write node names to include in submission
            dependencies: Optional dictionary of node name to list of dependency node names
            progress_callback: Optional callback function to report progress
            metadata_overrides: Optional dictionary of node name to override settings
            **kwargs: Additional job and plugin settings to override defaults
            
        Returns:
            Dictionary mapping write node names to job IDs
        """
        # Get write node names from objects if provided
        if write_nodes and not write_node_names:
            write_node_names = [node.fullName() for node in write_nodes]
            
        if not write_node_names:
            raise ValueError("No write nodes specified for submission")
            
        # Base settings for all jobs
        job_settings = {k: v for k, v in kwargs.items() if hasattr(self.job_info, k)}
        plugin_settings = {k: v for k, v in kwargs.items() if hasattr(self.plugin_info, k)}
        
        # Create a base job_info and plugin_info
        base_job_info = JobInfo()
        base_job_info.update(job_settings)
        
        base_plugin_info = NukePluginInfo()
        base_plugin_info.update(plugin_settings)
        base_plugin_info.scene_file = nuke_script_path
        
        # Store job IDs for each write node
        node_to_job_id = {}
        
        # Determine submission order based on dependencies
        submission_order = []
        processed_nodes = set()
        
        def process_node(name, stack=None):
            if stack is None:
                stack = []
            
            # Detect cycles
            if name in stack:
                cycle = " -> ".join(stack[stack.index(name):] + [name])
                raise ValueError(f"Cyclic dependency detected: {cycle}")
                
            # Skip if already processed
            if name in processed_nodes:
                return
                
            # Process dependencies first
            stack.append(name)
            if dependencies and name in dependencies:
                for dep in dependencies[name]:
                    if dep not in processed_nodes:
                        process_node(dep, stack)
                        
            # Add to submission order and mark as processed
            submission_order.append(name)
            processed_nodes.add(name)
            stack.pop()
        
        # Process each node in dependency order
        for node_name in write_node_names:
            if node_name not in processed_nodes:
                process_node(node_name)
        
        # Create temp directory for job files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Submit each write node as a separate job in the correct order
            for node_name in submission_order:
                print(f"\nSubmitting job for write node: {node_name}")
                
                # Create a copy of the base job info for this node
                node_job_info = JobInfo()
                for key, value in vars(base_job_info).items():
                    setattr(node_job_info, key, value)
                
                # Set job name to include write node name
                node_job_info.name = f"{node_job_info.name} - {node_name}"
                
                # Set dependencies in job info if this node has dependencies
                if dependencies and node_name in dependencies and dependencies[node_name]:
                    # Get dependency job IDs for nodes that have already been submitted
                    dependency_job_ids = []
                    for dep_node in dependencies[node_name]:
                        if dep_node in node_to_job_id:
                            dependency_job_ids.append(node_to_job_id[dep_node])
                    
                    # Add dependencies to job info
                    if dependency_job_ids:
                        node_job_info.dependencies = ",".join(dependency_job_ids)
                        print(f"Setting dependencies for {node_name}: {node_job_info.dependencies}")
                
                # Set node-specific settings in plugin info
                node_plugin_info = NukePluginInfo()
                for key, value in vars(base_plugin_info).items():
                    setattr(node_plugin_info, key, value)
                
                # Apply metadata overrides if available
                if metadata_overrides and node_name in metadata_overrides:
                    overrides = metadata_overrides[node_name]
                    for key, value in overrides.items():
                        if key.startswith('job_info.'):
                            # Extract the job info parameter name (in original case)
                            param_name = key[len('job_info.'):]
                            
                            # Find matching attribute in job_info (case-insensitive)
                            prop_name = self._find_matching_property(node_job_info, param_name)
                            
                            if prop_name:
                                # Convert value to the appropriate type
                                prop_value = getattr(node_job_info, prop_name)
                                if isinstance(prop_value, bool):
                                    if isinstance(value, str):
                                        value = value.lower() in ('true', 'yes', '1')
                                    else:
                                        value = bool(value)
                                elif isinstance(prop_value, int):
                                    value = int(value)
                                # Set the property value
                                setattr(node_job_info, prop_name, value)
                                print(f"Applied metadata override for {node_name}: {param_name} = {value}")
                            else:
                                print(f"Warning: No matching property found for {param_name} in JobInfo")
                                
                        elif key.startswith('plugin_info.'):
                            # Extract the plugin info parameter name (in original case)
                            param_name = key[len('plugin_info.'):]
                            
                            # Find matching attribute in plugin_info (case-insensitive)
                            prop_name = self._find_matching_property(node_plugin_info, param_name)
                            
                            if prop_name:
                                # Convert value to the appropriate type
                                prop_value = getattr(node_plugin_info, prop_name)
                                if isinstance(prop_value, bool):
                                    if isinstance(value, str):
                                        value = value.lower() in ('true', 'yes', '1')
                                    else:
                                        value = bool(value)
                                elif isinstance(prop_value, int):
                                    value = int(value)
                                # Set the property value
                                setattr(node_plugin_info, prop_name, value)
                                print(f"Applied metadata override for {node_name}: {param_name} = {value}")
                            else:
                                print(f"Warning: No matching property found for {param_name} in PluginInfo")
                
                # Generate job files
                job_file = os.path.join(temp_dir, f"{node_name}_job_info.job")
                plugin_file = os.path.join(temp_dir, f"{node_name}_plugin_info.job")
                
                node_job_info.to_file(job_file)
                node_plugin_info.to_file(plugin_file)
                
                # Add environment to plugin file manually
                with open(plugin_file, "a") as f:
                    f.write(f"EnvironmentKeyValue0=NUKE_WRITE_NODE={node_name}\n")
                
                # Submit to Deadline
                args = [job_file, plugin_file]
                if not node_job_info.submit_suspended:
                    args.append(nuke_script_path)
                    
                result = self._call_deadline_command(args)
                
                # Parse job ID from result
                job_id = None
                for line in result.splitlines():
                    if line.startswith("JobID="):
                        job_id = line[6:].strip()
                        break
                
                if job_id:
                    node_to_job_id[node_name] = job_id
                    print(f"Successfully submitted job {job_id} for {node_name}")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(node_name, job_id)
                else:
                    raise RuntimeError(f"Failed to get job ID for write node: {node_name}")
                
                # Small delay between submissions to ensure Deadline has processed the previous job
                time.sleep(1)
            
        return node_to_job_id 

    def _find_matching_property(self, obj: Any, param_name: str) -> Optional[str]:
        """
        Find a matching property name in an object, handling different naming conventions.
        
        This method tries different case conversions to find a match:
        1. Direct match (as is)
        2. Convert param_name from CamelCase to snake_case
        3. Case-insensitive match
        
        Args:
            obj: The object to search for properties
            param_name: The parameter name to find
            
        Returns:
            The matching property name if found, else None
        """
        # Try direct match first
        if hasattr(obj, param_name):
            return param_name
            
        # Try converting CamelCase to snake_case
        snake_case = self._camel_to_snake_case(param_name)
        if hasattr(obj, snake_case):
            return snake_case
            
        # Try case-insensitive match
        param_lower = param_name.lower()
        for prop in dir(obj):
            # Only consider non-private attributes
            if not prop.startswith('_') and prop.lower() == param_lower:
                return prop
                
        # No match found
        return None 