"""
DeadlineSubmitter class for handling the main submission logic.
"""
import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple, Union

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
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Deadline command failed: {e.stderr}")
            
    def submit_job(self, nuke_script_path: str, **kwargs) -> str:
        """
        Submit a Nuke script to Deadline.
        
        Args:
            nuke_script_path: Path to the Nuke script to submit
            **kwargs: Additional job and plugin settings to override defaults
            
        Returns:
            Job ID returned by Deadline
            
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