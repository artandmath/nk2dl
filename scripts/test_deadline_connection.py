#!/usr/bin/env python3
"""Test script to verify connectivity to a Deadline server.

This script performs connectivity tests against a Deadline server using both
command-line and web service methods. It verifies basic operations like:
- Establishing connection
- Retrieving render groups
- Getting repository path (command-line only)
- Submitting a test job

Usage:
    python test_deadline_connection.py

Environment Variables:
    PYTHONPATH: Python path including nk2dl package
    DEADLINE_PATH: Path to Deadline installation directory
    NK2DL_DEADLINE_HOST: Hostname for Deadline Web Service (default: localhost)
    NK2DL_DEADLINE_PORT: Port for Deadline Web Service (default: 8081)
    NK2DL_DEADLINE_SSL: Enable SSL connection (default: False)
    NK2DL_DEADLINE_SSL_CERT: Path to SSL certificate file (required if SSL enabled)
    NK2DL_DEADLINE_USE__WEB__SERVICE: Use web service instead of command line (default: False)

Requirements:
    - Deadline Client must be installed and configured on the system
    - For command-line tests: deadlinecommand must be in system PATH
    - For web service tests: Deadline Web Service must be running and accessible
    - For SSL connections: Valid SSL certificate file

Exit Codes:
    0: All tests passed
    1: One or more tests failed

Examples:
    # Run with default settings
    python test_deadline_connection.py

    # Linux/Unix Examples:
    # ------------------
    # Run with custom web service settings
    export PYTHONPATH=/path/to/nk2dl
    export DEADLINE_PATH=/path/to/deadline/bin
    export NK2DL_DEADLINE_USE__WEB__SERVICE=True
    export NK2DL_DEADLINE_HOST=deadline-server 
    export NK2DL_DEADLINE_PORT=8081
    export NK2DL_DEADLINE_SSL=False
    python test_deadline_connection.py

    # Run with SSL enabled
    export PYTHONPATH=/path/to/nk2dl
    export DEADLINE_PATH=/path/to/deadline/bin
    export NK2DL_DEADLINE_USE__WEB__SERVICE=True
    export NK2DL_DEADLINE_HOST=deadline-server
    export NK2DL_DEADLINE_PORT=4434
    export NK2DL_DEADLINE_SSL=True
    export NK2DL_DEADLINE_SSL_CERT=/path/to/certificate.pxf
    python test_deadline_connection.py

    # Windows PowerShell Examples:
    # -------------------------
    # Run with custom web service settings
    $env:PYTHONPATH = "C:\\path\\to\\nk2dl"
    $env:DEADLINE_PATH = "C:\\Program Files\\Thinkbox\\Deadline10\\bin"
    $env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
    $env:NK2DL_DEADLINE_HOST = "deadline-server"
    $env:NK2DL_DEADLINE_PORT = "8081"
    $env:NK2DL_DEADLINE_SSL = "False"
    python test_deadline_connection.py

    # Run with SSL enabled
    $env:PYTHONPATH = "C:\\path\\to\\nk2dl"
    $env:DEADLINE_PATH = "C:\\Program Files\\Thinkbox\\Deadline10\\bin"
    $env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
    $env:NK2DL_DEADLINE_HOST = "deadline-server"
    $env:NK2DL_DEADLINE_PORT = "4434"
    $env:NK2DL_DEADLINE_SSL = "True"
    $env:NK2DL_DEADLINE_SSL_CERT = "C:\\path\\to\\certificate.pxf"
    python test_deadline_connection.py
"""

import os
import sys
from nk2dl.deadline.connection import DeadlineConnection
from nk2dl.common.config import config
from nk2dl.common.errors import DeadlineError

def setup_deadline_environment():
    """Set up the Deadline environment including Python paths."""
    # Get Deadline installation path
    deadline_path = os.environ.get('DEADLINE_PATH')
    if not deadline_path:
        raise DeadlineError(
            "DEADLINE_PATH environment variable not set. Please set it to your Deadline installation directory."
        )
    
    # Add Deadline Python API paths
    api_paths = [
        os.path.join(deadline_path, "bin"),  # Main Deadline Python modules
        os.path.join(deadline_path, "bin", "Modules"),  # Additional modules
    ]
    
    # Add paths to Python path
    for path in api_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)

def test_command_line():
    """Test command-line connectivity."""
    print("\nTesting command-line connectivity...")
    
    # Set config via environment variables
    os.environ['NK2DL_DEADLINE_USE__WEB__SERVICE'] = 'False'
    os.environ['NK2DL_DEADLINE_SSL'] = 'False'  # Ensure SSL is off for command line
    
    # Force reload config to pick up the environment variable changes
    config.load_config()
    
    try:
        conn = DeadlineConnection()
        conn.ensure_connected()
        print("✓ Successfully connected via command-line")
        
        # Test getting repository path
        try:
            repo_path = conn.get_repository_path()
            print(f"✓ Repository path: {repo_path}")
        except NotImplementedError:
            # Skip repository path test when using web service
            print("ℹ Skipping repository path test (not supported in web service mode)")
        
        # Test getting groups
        groups = conn.get_groups()
        print(f"✓ Retrieved {len(groups)} groups: {', '.join(groups)}")
        
        # Test submitting a test job
        job_info = {
            'BatchName': 'Test Batch',
            'Name': 'Command-line Connectivity Test Job',
            'Comment': 'Testing Deadline command-line connectivity',
            'Department': '',
            'Pool': 'none',
            'SecondaryPool': '',
            'Group': 'none',
            'Priority': '50',
            'TaskTimeoutMinutes': '0',
            'EnableAutoTimeout': 'False',
            'ConcurrentTasks': '1',
            'LimitConcurrentTasksToNumberOfCpus': 'True',
            'Frames': '1',
            'ChunkSize': '1',
            'Plugin': 'Python'
        }
        
        plugin_info = {
            'Version': '3.7',
            'ScriptFile': '',
            'Arguments': '',
            'SingleFramesOnly': 'False',
            'ScriptFilename': '',  # Extra field required by some Deadline versions
            'StartupDirectory': ''  # Extra field required by some Deadline versions
        }
        
        job_id = conn.submit_job(job_info, plugin_info)
        print(f"✓ Successfully submitted test job with ID: {job_id}")
        
    except DeadlineError as e:
        print(f"✗ Command-line test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error in command-line test: {e}")
        return False
    
    return True

def test_web_service():
    """Test web service connectivity."""
    print("\nTesting web service connectivity...")
    
    # Set config via environment variables
    os.environ['NK2DL_DEADLINE_USE__WEB__SERVICE'] = 'True'
    
    # Force reload config to pick up the environment variable changes
    config.load_config()
    
    try:
        conn = DeadlineConnection()
        conn.ensure_connected()
        print("✓ Successfully connected via web service")
        
        # Test getting groups
        groups = conn.get_groups()
        print(f"✓ Retrieved {len(groups)} groups: {', '.join(groups)}")
        
        # Test submitting a test job
        job_info = {
            'BatchName': 'Test Batch',
            'Name': 'Web Service Connectivity Test Job',
            'Comment': 'Testing Deadline web service connectivity',
            'Department': '',
            'Pool': 'none',
            'SecondaryPool': '',
            'Group': 'none',
            'Priority': '50',
            'TaskTimeoutMinutes': '0',
            'EnableAutoTimeout': 'False',
            'ConcurrentTasks': '1',
            'LimitConcurrentTasksToNumberOfCpus': 'True',
            'Frames': '1',
            'ChunkSize': '1',
            'Plugin': 'Python'
        }
        
        plugin_info = {
            'Version': '3.7',
            'ScriptFile': '',
            'Arguments': '',
            'SingleFramesOnly': 'False',
            'ScriptFilename': '',  # Extra field required by some Deadline versions
            'StartupDirectory': ''  # Extra field required by some Deadline versions
        }
        
        job_id = conn.submit_job(job_info, plugin_info)
        print(f"✓ Successfully submitted test job with ID: {job_id}")
        
    except DeadlineError as e:
        print(f"✗ Web service test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error in web service test: {e}")
        return False
    
    return True

def main():
    """Main function to run connectivity tests."""
    print("Deadline Connectivity Test")
    print("=========================")
    
    # Set up Deadline environment
    try:
        setup_deadline_environment()
    except DeadlineError as e:
        print(f"✗ Failed to set up Deadline environment: {e}")
        sys.exit(1)
    
    # Run tests
    cmd_success = test_command_line()
    web_success = test_web_service()
    
    # Print summary
    print("\nTest Summary")
    print("-----------")
    print(f"Command-line: {'✓ PASS' if cmd_success else '✗ FAIL'}")
    print(f"Web Service:  {'✓ PASS' if web_success else '✗ FAIL'}")
    
    # Exit with appropriate status
    sys.exit(0 if cmd_success and web_success else 1)

if __name__ == '__main__':
    main()