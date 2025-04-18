#!/usr/bin/env python
"""
Example script demonstrating submission of a Nuke script to Deadline.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import the package
sys.path.append(str(Path(__file__).parent.parent))

from nk2dl.nuke import submit_nuke_script
from nk2dl.common.errors import NK2DLError


def main():
    """Example Nuke script submission."""
    parser = argparse.ArgumentParser(description="Submit a Nuke script to Deadline")
    parser.add_argument("script_path", help="Path to Nuke script (.nk file)")
    parser.add_argument("--frame-range", help="Frame range to render (default: from script)")
    parser.add_argument("--output-path", help="Override output path")
    parser.add_argument("--job-name", help="Custom job name")
    parser.add_argument("--priority", type=int, help="Job priority (0-100)")
    parser.add_argument("--pool", help="Deadline pool")
    parser.add_argument("--group", help="Deadline group")
    parser.add_argument("--chunk-size", type=int, help="Chunk size")
    parser.add_argument("--use-nuke-x", action="store_true", help="Use NukeX for rendering")
    parser.add_argument("--render-threads", type=int, help="Render threads")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU for rendering")
    
    args = parser.parse_args()
    
    try:
        # Build keyword arguments from CLI arguments
        kwargs = {
            "frame_range": args.frame_range,
            "job_name": args.job_name,
            "priority": args.priority,
            "pool": args.pool,
            "group": args.group,
            "chunk_size": args.chunk_size,
            "use_nuke_x": args.use_nuke_x,
            "render_threads": args.render_threads,
            "use_gpu": args.use_gpu
        }
        
        if args.output_path:
            kwargs["output_path"] = args.output_path
            
        # Remove None values to use defaults from config
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # Submit the Nuke script
        job_id = submit_nuke_script(args.script_path, **kwargs)
        
        print(f"Nuke script submitted successfully. Job ID: {job_id}")
        return 0
    
    except NK2DLError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main()) 