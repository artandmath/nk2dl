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
                selected_write_nodes: Optional[List[str]] = None,
                render_mode: str = "full"):
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
            selected_write_nodes: List of write nodes to render
            render_mode: Render mode (full, proxy)
        """
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
        self.selected_write_nodes = selected_write_nodes
        self.render_mode = render_mode
        
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
    
    def prepare_plugin_info(self) -> Dict[str, Any]:
        """Prepare plugin information for Deadline submission.
        
        Returns:
            Dictionary containing plugin information
        """
        plugin_info = {
            "SceneFile": str(self.script_path.absolute()),
            "Version": "10.0",  # Default Nuke version - usually auto-detected by Deadline
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
        if self.selected_write_nodes:
            plugin_info["WriteNodes"] = ",".join(self.selected_write_nodes)
        if self.output_path:
            plugin_info["OutputFilePath"] = self.output_path
            
        return plugin_info
    
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
            
            # Submit job to Deadline
            logger.info(f"Submitting Nuke script: {self.script_path}")
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