"""Command line argument parser for nk2dl.

This module provides the argument parser for the nk2dl command line interface.
"""

import argparse
import sys
from typing import List, Optional

from ..common.config import config
from ..common.logging import configure_logging


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for nk2dl."""
    parser = argparse.ArgumentParser(
        prog="nk2dl",
        description="Nuke to Deadline Submitter - Submit Nuke scripts to Deadline render farm",
    )
    
    # Set up logging/verbosity arguments globally
    parser.add_argument(
        "-V", "--verbose", 
        action="store_const", 
        dest="logging", 
        const="DEBUG",
        help="Enable verbose output (DEBUG level logging)"
    )
    parser.add_argument(
        "-VV", 
        action="store_const", 
        dest="logging", 
        const="NOTSET",
        help="Enable very verbose output (NOTSET level logging)"
    )
    parser.add_argument(
        "--logging", "--verbosity",
        choices=["INFO", "DEBUG", "NOTSET"],
        help="Set logging level"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a Nuke script to Deadline")
    _setup_submit_parser(submit_parser)
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage nk2dl configuration")
    _setup_config_parser(config_parser)
    
    return parser


def _setup_submit_parser(parser: argparse.ArgumentParser) -> None:
    """Set up the submit command parser with all options."""
    # Required arguments
    parser.add_argument(
        "script_path",
        help="Path to the Nuke script to submit"
    )
    
    # Job identification options
    job_group = parser.add_argument_group("Job identification options")
    job_group.add_argument(
        "--BatchName", 
        metavar="NAME",
        help="Batch name for the job (default: Nuke script filename)"
    )
    job_group.add_argument(
        "--JobName", 
        metavar="NAME",
        help="Job name (default: <nukescript_filename>/<write_nodename>)"
    )
    job_group.add_argument(
        "--Comment", 
        metavar="TEXT",
        help="Comment for the job"
    )
    job_group.add_argument(
        "--Department", 
        metavar="NAME",
        help="Department for the job"
    )
    
    # Priority and pool options
    resource_group = parser.add_argument_group("Priority and pool options")
    resource_group.add_argument(
        "--Pool", 
        metavar="NAME",
        help="Worker pool to use"
    )
    resource_group.add_argument(
        "--Group", 
        metavar="NAME",
        help="Worker group to use"
    )
    resource_group.add_argument(
        "--Priority", 
        metavar="VALUE",
        type=int,
        help="Job priority (0-100, default: 50)"
    )
    resource_group.add_argument(
        "--TaskTimeout", 
        metavar="MINUTES",
        type=int,
        help="Task timeout in minutes (0 for no timeout)"
    )
    resource_group.add_argument(
        "--AutoTaskTimeout", 
        action="store_true",
        help="Enable automatic task timeout"
    )
    resource_group.add_argument(
        "--ConcurrentTasks", 
        metavar="COUNT",
        type=int,
        help="Maximum number of concurrent tasks per job (default: 1)"
    )
    resource_group.add_argument(
        "--LimitWorkerTasks", 
        action="store_true",
        help="Limit tasks to one per worker"
    )
    resource_group.add_argument(
        "--MachineLimit", 
        metavar="COUNT",
        type=int,
        help="Maximum number of machines to use (0 for no limit)"
    )
    resource_group.add_argument(
        "--MachineList", 
        metavar="LIST",
        help="List of machines to allow or deny (format: allow:machine1,machine2 or deny:machine1,machine2)"
    )
    resource_group.add_argument(
        "--Limits", 
        metavar="LIST",
        help="Resource limits to use (comma-separated)"
    )
    
    # Dependencies and submission options
    dependency_group = parser.add_argument_group("Dependencies and submission options")
    dependency_group.add_argument(
        "--Dependencies", 
        metavar="JOB_IDS",
        help="Job IDs this job depends on (comma-separated)"
    )
    dependency_group.add_argument(
        "--SubmitJobsAsSuspended", 
        action="store_true",
        help="Submit jobs as suspended"
    )
    dependency_group.add_argument(
        "--SubmitNukeScript", 
        action="store_true",
        help="Submit the Nuke script as an auxiliary file"
    )
    
    # Write node options
    write_group = parser.add_argument_group("Write node options")
    write_group.add_argument(
        "--WriteNodes", "--Writes", "--Nodes", "-w", "-n",
        metavar="NODES",
        dest="WriteNodes",
        help="Write nodes to render (comma-separated, default: all)"
    )
    write_group.add_argument(
        "--WritesAsSeparateJobs", 
        action="store_true",
        help="Submit each write node as a separate job"
    )
    write_group.add_argument(
        "--WritesAsSeparateTasks", 
        action="store_true",
        help="Submit write nodes as separate tasks for the same job"
    )
    write_group.add_argument(
        "--NodeFrameRange", 
        action="store_true",
        help="Use frame range from write nodes instead of global frame range"
    )
    write_group.add_argument(
        "--RenderOrderDependencies", 
        action="store_true",
        help="Set dependencies based on write node render order"
    )
    
    # Frame range options
    frame_group = parser.add_argument_group("Frame range options")
    frame_group.add_argument(
        "--Frames", "-f",
        metavar="RANGE",
        help="Frame range to render (Nuke syntax, special tokens: f,l,m,h,i)"
    )
    frame_group.add_argument(
        "--FramesPerTask", "--TaskSize", "--ChunkSize", "--Chunk",
        metavar="SIZE",
        dest="FramesPerTask",
        type=int,
        help="Number of frames per task (default: 1)"
    )
    
    # Nuke options
    nuke_group = parser.add_argument_group("Nuke options")
    nuke_group.add_argument(
        "--NukeX", "-nx", "--UseNukeX",
        action="store_true",
        dest="UseNukeX",
        help="Use NukeX for rendering"
    )
    nuke_group.add_argument(
        "--BatchMode", 
        action="store_true",
        help="Use batch mode"
    )
    nuke_group.add_argument(
        "--RenderThreads", 
        metavar="COUNT",
        type=int,
        help="Number of render threads to use"
    )
    nuke_group.add_argument(
        "--Gpu", "--UseGPU",
        action="store_true",
        dest="UseGPU",
        help="Use GPU for rendering"
    )
    nuke_group.add_argument(
        "--RAM", 
        metavar="GB",
        type=int,
        help="Maximum RAM usage in GB"
    )
    nuke_group.add_argument(
        "--ContinueOnError", 
        action="store_true",
        help="Continue rendering if an error occurs"
    )
    nuke_group.add_argument(
        "--ReloadBetweenTasks", "--ReloadBetweenChunks",
        action="store_true",
        dest="ReloadBetweenTasks",
        help="Reload plugins between tasks"
    )
    nuke_group.add_argument(
        "--PerformanceProfiler", 
        action="store_true",
        help="Use performance profiler"
    )
    nuke_group.add_argument(
        "--XMLDirectory", "--XMLDir",
        metavar="PATH",
        dest="XMLDirectory",
        help="Directory to save performance profile XML files"
    )
    nuke_group.add_argument(
        "--Proxy", 
        action="store_true",
        help="Render in proxy mode"
    )
    nuke_group.add_argument(
        "--Views", 
        metavar="VIEWS",
        help="Views to render (comma-separated, default: all)"
    )
    
    # Graph scope variables options
    gsv_group = parser.add_argument_group("Graph scope variables options")
    gsv_group.add_argument(
        "--Var", "--Variable", "--GSV",
        metavar="VARIABLES",
        dest="GraphScopeVariables",
        action="append",
        help="Graph scope variables (format: var:value1,value2,var2:value3,value4)"
    )
    
    # Job completion options
    completion_group = parser.add_argument_group("Job completion options")
    completion_group.add_argument(
        "--OnJobComplete", 
        choices=["Nothing", "Archive", "Delete"],
        help="Action to take when job completes"
    )


def _setup_config_parser(parser: argparse.ArgumentParser) -> None:
    """Set up the config command parser with all options."""
    # Add subcommands for config operations
    subparsers = parser.add_subparsers(dest="config_command", help="Config operation")
    
    # List config values
    list_parser = subparsers.add_parser("list", help="List configuration values")
    list_parser.add_argument(
        "--source", 
        action="store_true",
        help="Show configuration sources"
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args: Command line arguments to parse (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments namespace
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Configure logging based on arguments
    if parsed_args.logging:
        configure_logging(level=parsed_args.logging)
    
    # Ensure a command was provided
    if not parsed_args.command:
        parser.print_help()
        sys.exit(1)
        
    return parsed_args 