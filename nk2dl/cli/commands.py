"""Command implementations for nk2dl CLI.

This module provides the implementations for the nk2dl CLI commands.
"""

import argparse
import sys
from typing import Dict, Any, List, Optional

from ..common.config import config
from ..common.errors import NK2DLError
from ..common.logging import logger
from ..nuke.submission import submit_nuke_script


def handle_submit(args: argparse.Namespace) -> int:
    """Handle the submit command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info(f"Submitting Nuke script: {args.script_path}")
        
        # Convert CLI args to submission kwargs
        kwargs = _args_to_kwargs(args)
        
        # Submit the Nuke script
        job_id = submit_nuke_script(args.script_path, **kwargs)
        
        print(f"Job submitted successfully. Job ID: {job_id}")
        return 0
        
    except NK2DLError as e:
        logger.error(f"Submission error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception("Unexpected error during submission")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def handle_config_list(args: argparse.Namespace) -> int:
    """Handle the config list command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Access the config object directly
        if hasattr(config, "_config"):
            # Flatten the config for display
            flat_config = _flatten_config(config._config)
            
            # Print configuration values
            print("Current configuration:")
            print("----------------------")
            
            for key in sorted(flat_config.keys()):
                print(f"{key} = {flat_config[key]}")
                
            return 0
        else:
            print("Error: Unable to access configuration", file=sys.stderr)
            return 1
            
    except Exception as e:
        logger.exception("Unexpected error during config listing")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def handle_config(args: argparse.Namespace) -> int:
    """Handle the config command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if args.config_command == "list":
        return handle_config_list(args)
    else:
        print(f"Error: Unknown config command: {args.config_command}", file=sys.stderr)
        return 1


def _args_to_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    """Convert command line arguments to keyword arguments for submission.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dictionary of keyword arguments
    """
    # Create a dictionary to hold the kwargs
    kwargs = {}
    
    # Job identification
    if hasattr(args, "BatchName") and args.BatchName is not None:
        kwargs["batch_name"] = args.BatchName
    if hasattr(args, "JobName") and args.JobName is not None:
        kwargs["job_name"] = args.JobName
    if hasattr(args, "Comment") and args.Comment is not None:
        kwargs["comment"] = args.Comment
    if hasattr(args, "Department") and args.Department is not None:
        kwargs["department"] = args.Department
        
    # Priority and pool options
    if hasattr(args, "Pool") and args.Pool is not None:
        kwargs["pool"] = args.Pool
    if hasattr(args, "Group") and args.Group is not None:
        kwargs["group"] = args.Group
    if hasattr(args, "Priority") and args.Priority is not None:
        kwargs["priority"] = args.Priority
    if hasattr(args, "ConcurrentTasks") and args.ConcurrentTasks is not None:
        kwargs["concurrent_tasks"] = args.ConcurrentTasks
    if hasattr(args, "LimitWorkerTasks") and args.LimitWorkerTasks:
        kwargs["limit_worker_tasks"] = True
    if hasattr(args, "MachineLimit") and args.MachineLimit is not None:
        kwargs["machine_limit"] = args.MachineLimit
    if hasattr(args, "MachineList") and args.MachineList is not None:
        kwargs["machine_list"] = args.MachineList
    if hasattr(args, "Limits") and args.Limits is not None:
        kwargs["limits"] = args.Limits
        
    # Dependencies options
    if hasattr(args, "Dependencies") and args.Dependencies is not None:
        kwargs["job_dependencies"] = args.Dependencies
    if hasattr(args, "SubmitJobsAsSuspended") and args.SubmitJobsAsSuspended:
        kwargs["submit_suspended"] = True
    if hasattr(args, "SubmitNukeScript") and args.SubmitNukeScript:
        kwargs["submit_script"] = True
        
    # Write node options
    if hasattr(args, "WriteNodes") and args.WriteNodes is not None:
        kwargs["write_nodes"] = args.WriteNodes.split(",")
    if hasattr(args, "WritesAsSeparateJobs") and args.WritesAsSeparateJobs:
        kwargs["write_nodes_as_separate_jobs"] = True
    if hasattr(args, "WritesAsSeparateTasks") and args.WritesAsSeparateTasks:
        kwargs["write_nodes_as_tasks"] = True
    if hasattr(args, "NodeFrameRange") and args.NodeFrameRange:
        kwargs["use_nodes_frame_list"] = True
    if hasattr(args, "RenderOrderDependencies") and args.RenderOrderDependencies:
        kwargs["render_order_dependencies"] = True
        
    # Frame range options
    if hasattr(args, "Frames") and args.Frames is not None:
        kwargs["frame_range"] = args.Frames
    if hasattr(args, "FramesPerTask") and args.FramesPerTask is not None:
        kwargs["chunk_size"] = args.FramesPerTask
        
    # Nuke options
    if hasattr(args, "UseNukeX") and args.UseNukeX:
        kwargs["use_nuke_x"] = True
    if hasattr(args, "BatchMode") and args.BatchMode:
        kwargs["use_batch_mode"] = True
    if hasattr(args, "RenderThreads") and args.RenderThreads is not None:
        kwargs["render_threads"] = args.RenderThreads
    if hasattr(args, "UseGPU") and args.UseGPU:
        kwargs["use_gpu"] = True
    if hasattr(args, "RAM") and args.RAM is not None:
        # Convert GB to MB
        kwargs["max_ram_usage"] = args.RAM * 1024
    if hasattr(args, "ContinueOnError") and args.ContinueOnError:
        kwargs["continue_on_error"] = True
    if hasattr(args, "ReloadBetweenTasks") and args.ReloadBetweenTasks:
        kwargs["reload_plugins"] = True
    if hasattr(args, "PerformanceProfiler") and args.PerformanceProfiler:
        kwargs["use_profiler"] = True
    if hasattr(args, "XMLDirectory") and args.XMLDirectory is not None:
        kwargs["profile_dir"] = args.XMLDirectory
    if hasattr(args, "Proxy") and args.Proxy:
        kwargs["use_proxy"] = True
    if hasattr(args, "Views") and args.Views is not None:
        kwargs["views"] = args.Views.split(",")
        
    # Graph scope variables
    if hasattr(args, "GraphScopeVariables") and args.GraphScopeVariables is not None:
        kwargs["graph_scope_variables"] = args.GraphScopeVariables
        
    # Job completion options
    if hasattr(args, "OnJobComplete") and args.OnJobComplete is not None:
        kwargs["on_job_complete"] = args.OnJobComplete
        
    # Remove None values to use defaults from config
    return {k: v for k, v in kwargs.items() if v is not None}


def _flatten_config(config_dict: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """Flatten a nested configuration dictionary.
    
    Args:
        config_dict: Nested configuration dictionary
        parent_key: Parent key for nested values
        
    Returns:
        Flattened configuration dictionary
    """
    items = []
    for key, value in config_dict.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(_flatten_config(value, new_key).items())
        else:
            items.append((new_key, value))
            
    return dict(items)


def main() -> int:
    """Main entry point for the nk2dl CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from .parser import parse_args
    
    # Parse command line arguments
    args = parse_args()
    
    # Execute the appropriate command
    if args.command == "submit":
        return handle_submit(args)
    elif args.command == "config":
        return handle_config(args)
    else:
        print(f"Error: Unknown command: {args.command}", file=sys.stderr)
        return 1 