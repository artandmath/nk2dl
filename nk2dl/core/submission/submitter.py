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
        Call the Deadline command with the given arguments.
        
        Args:
            args: List of arguments to pass to the Deadline command
            
        Returns:
            Output from the Deadline command
            
        Raises:
            RuntimeError: If the Deadline command fails
        """
        try:
            cmd = [self.deadline_command] + args
            print(f"Running Deadline command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Command output: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # For dependency setting, we'll ignore errors as it's not critical
            if args[0] == "-SetJobDependencies":
                print(f"Warning: Failed to set job dependencies: {e.stderr}")
                return ""
            raise RuntimeError(f"Deadline command failed: {e.stderr}")
            
    def submit_job(self, 
                  nuke_script_path: str, 
                  write_nodes: Optional[List[Any]] = None,
                  write_node_names: Optional[List[str]] = None,
                  dependencies: Optional[Dict[str, List[str]]] = None,
                  progress_callback: Optional[Callable[[str, str], None]] = None,
                  **kwargs) -> Union[str, Dict[str, str]]:
        """
        Submit a Nuke script to Deadline.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            write_nodes: Optional list of write node objects to include in submission
            write_node_names: Optional list of write node names to include in submission
            dependencies: Optional dictionary of node name to list of dependency node names
            progress_callback: Optional callback function to report progress
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
        
        # Determine if we're submitting multiple jobs or a single job
        if write_nodes or write_node_names:
            return self._submit_multiple_jobs(
                nuke_script_path,
                write_nodes,
                write_node_names,
                dependencies,
                progress_callback,
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
                             **kwargs) -> Dict[str, str]:
        """
        Submit multiple jobs to Deadline, one for each write node.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            write_nodes: Optional list of write node objects to include in submission
            write_node_names: Optional list of write node names to include in submission
            dependencies: Optional dictionary of node name to list of dependency node names
            progress_callback: Optional callback function to report progress
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
        
        # Order nodes for submission based on dependencies
        # We need to submit nodes that others depend on first
        submission_order = []
        remaining_nodes = list(write_node_names)
        
        # Keep adding nodes that don't depend on any remaining nodes
        while remaining_nodes:
            # Find nodes with no dependencies or with already submitted dependencies
            ready_nodes = []
            for node in remaining_nodes:
                if node not in dependencies or not dependencies[node]:
                    # No dependencies at all
                    ready_nodes.append(node)
                elif all(dep not in remaining_nodes for dep in dependencies[node]):
                    # All dependencies already processed
                    ready_nodes.append(node)
            
            if not ready_nodes:
                # If we can't find any ready nodes but still have remaining nodes,
                # there might be circular dependencies; break the cycle
                ready_nodes = [remaining_nodes[0]]
                
            # Add ready nodes to submission order and remove from remaining
            for node in ready_nodes:
                submission_order.append(node)
                remaining_nodes.remove(node)
        
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