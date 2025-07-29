#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pre-build job script test example.

This script demonstrates how to create a pre-build job script for nk2dl.
It will have access to the arguments passed via the 'args' list.

Usage:
    Set as pre_build_job_script in NukeSubmission, e.g.:
    
    submission = NukeSubmission(
        script_path="my_script.nk",
        pre_build_job_script=["path/to/pre_build_test.py", "arg1", "arg2", "any_value"]
    )
"""

import os
import time
import tempfile
from pprint import pprint

# Logger is made available by the build job script
print("\n==== PRE-BUILD JOB SCRIPT EXECUTION ====")
logger.info("Starting pre-build job script")

# Print the arguments passed to the script
logger.info(f"Arguments passed to pre-build script: {args}")
if args:
    for i, arg in enumerate(args):
        logger.info(f"  Argument {i}: {arg}")
else:
    logger.info("No arguments were passed")

# Print some environment information
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# You could perform setup tasks here, for example:
# - Creating directories
# - Setting up environments
# - Initializing databases
# - Running validation checks

# Example of creating a temporary directory 
timestamp = time.strftime("%Y%m%d_%H%M%S")
test_dir_name = f"nk2dl_test_{timestamp}"
try:
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix=test_dir_name)
    logger.info(f"Created temporary test directory: {temp_dir}")
        
    # Create a test file
    test_file_path = os.path.join(temp_dir, "pre_build_test.txt")
    with open(test_file_path, "w") as f:
        f.write(f"Pre-build script executed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Arguments: {', '.join(args) if args else 'None'}\n")
    logger.info(f"Created test file: {test_file_path}")
    
except Exception as e:
    logger.error(f"Error creating test directory/file: {e}")

# Simulating some processing time
logger.info("Simulating processing...")
time.sleep(1)  # Sleep for 1 second

# Return success
logger.info("Pre-build job script completed successfully")
print("==== PRE-BUILD JOB SCRIPT COMPLETED ====\n")

# The script will automatically return True unless an exception is raised 