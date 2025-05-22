#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post-build job script test example.

This script demonstrates how to create a post-build job script for nk2dl.
It will have access to:
- Arguments passed via the 'args' list
- Submission results in the 'results' variable
- Job IDs in the 'job_ids' variable

Usage:
    Set as post_build_job_script in NukeSubmission, e.g.:
    
    submission = NukeSubmission(
        script_path="my_script.nk",
        post_build_job_script=["path/to/post_build_test.py", "arg1", "arg2", "any_value"]
    )
"""

import os
import time
import json
import tempfile
from pprint import pformat

# Logger is made available by the build job script
print("\n==== POST-BUILD JOB SCRIPT EXECUTION ====")
logger.info("Starting post-build job script")

# Print the arguments passed to the script
logger.info(f"Arguments passed to post-build script: {args}")
if args:
    for i, arg in enumerate(args):
        logger.info(f"  Argument {i}: {arg}")
else:
    logger.info("No arguments were passed")

# Print some environment information
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Print submission results
logger.info(f"Number of jobs submitted: {len(results)}")
logger.info(f"Job IDs: {job_ids}")

# Create a temp directory and save the job information
try:
    results_dir = tempfile.mkdtemp(prefix="nk2dl_results_")
    logger.info(f"Created temporary results directory: {results_dir}")
    
    # Save detailed job information to a JSON file
    results_file = os.path.join(results_dir, "submission_results.json")
    
    # Format the results for JSON serialization (remove non-serializable objects)
    json_results = []
    for job in results:
        json_job = {
            "job_id": job.get("job_id", "unknown"),
            "render_order": job.get("render_order", 0),
        }
        
        # Include job_info and plugin_info if available
        if "job_info" in job:
            json_job["job_info"] = job["job_info"]
        if "plugin_info" in job:
            json_job["plugin_info"] = job["plugin_info"]
            
        json_results.append(json_job)
    
    with open(results_file, "w") as f:
        json.dump(json_results, f, indent=2)
    logger.info(f"Saved submission results to: {results_file}")
    
    # Create a summary text file
    summary_file = os.path.join(results_dir, "submission_summary.txt")
    with open(summary_file, "w") as f:
        f.write(f"Submission completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Arguments: {', '.join(args) if args else 'None'}\n")
        f.write(f"Number of jobs: {len(results)}\n")
        f.write(f"Job IDs: {', '.join(job_ids)}\n\n")
        
        # Include detailed information for each job
        for i, job in enumerate(results):
            f.write(f"Job {i+1}:\n")
            f.write(f"  ID: {job.get('job_id', 'unknown')}\n")
            f.write(f"  Render Order: {job.get('render_order', 0)}\n")
            
            if "job_info" in job:
                f.write("  Job Info:\n")
                job_info = job["job_info"]
                f.write(f"    Name: {job_info.get('Name', 'unknown')}\n")
                f.write(f"    Frames: {job_info.get('Frames', 'unknown')}\n")
                f.write(f"    Priority: {job_info.get('Priority', 'unknown')}\n")
                
            if "plugin_info" in job:
                f.write("  Plugin Info:\n")
                plugin_info = job["plugin_info"]
                f.write(f"    Version: {plugin_info.get('Version', 'unknown')}\n")
                write_node = plugin_info.get('WriteNode', '')
                if write_node:
                    f.write(f"    Write Node: {write_node}\n")
            
            f.write("\n")
    
    logger.info(f"Saved submission summary to: {summary_file}")
    
    # You could perform additional post-submission tasks:
    # - Trigger notifications (email, Slack, etc.)
    # - Update job tracking systems
    # - Trigger dependent processes
    # - Generate a submission report
    
except Exception as e:
    logger.error(f"Error processing submission results: {e}")
    logger.error(f"Results data structure: {pformat(results)}")

# Example of how you might use the submission results
logger.info("Examples of how you could use the submission results:")
logger.info(f"1. Create a submission report")
logger.info(f"2. Connect to asset managment database")
logger.info(f"3. Connect to notification system")

# Return success
logger.info("Post-build job script completed successfully")
print("==== POST-BUILD JOB SCRIPT COMPLETED ====\n")

# The script will automatically return True unless an exception is raised 