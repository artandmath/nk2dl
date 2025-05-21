"""Module for handling Nuke script submission through subprocesses.

This module provides functionality for submitting Nuke scripts through external processes 
when direct parsing of the script in the current Nuke session is not possible.
"""

import os
import sys
import json
import tempfile
import subprocess as sp
from typing import Dict, List, Any, Optional
import re

from ..common.framerange import FrameRange
from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.nuke.subprocess')

def serialize_kwargs(kwargs: Dict[str, Any]) -> str:
    """Serialize kwargs to a JSON string that can be safely included in Python code."""
    return json.dumps(kwargs).replace("'", "\\'").replace('"', '\\"')

def submit_script_via_subprocess(script_path: str, 
                                use_parser_instead_of_nuke: bool = False, 
                                **kwargs) -> Dict[int, List[str]]:
    """
    Submit a Nuke script via subprocess to ensure proper script parsing.
    
    Args:
        script_path: Path to the Nuke script
        use_parser_instead_of_nuke: Whether to use Python parser instead of Nuke
        **kwargs: Additional arguments to pass to submit_nuke_script
        
    Returns:
        Dictionary mapping render orders to job IDs
    """
    # Create temp file
    temp_file = create_submission_script(script_path, kwargs)
    
    try:
        # Execute the subprocess
        result = execute_submission_script(temp_file, use_parser_instead_of_nuke)
        return result
    finally:
        # Clean up
        try:
            os.unlink(temp_file)
        except:
            pass

def create_submission_script(script_path: str, kwargs: Dict[str, Any]) -> str:
    """Create a temporary Python script for submission."""
    # Create unique temp file
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_path = temp_file.name
        
        # Write script content with a unique marker for JSON output
        script_content = f"""
import sys
import os
import json

try:
    from nk2dl.nuke.submission import submit_nuke_script
    
    # Parse arguments from JSON
    kwargs = json.loads('''{serialize_kwargs(kwargs)}''')
    
    # Add script_is_open=True
    kwargs['script_is_open'] = True
    
    # Submit the script
    result = submit_nuke_script('{script_path}', **kwargs)
    
    # Print the result as JSON with unique markers to separate it from log output
    print("NK2DL_JSON_BEGIN")
    print(json.dumps(result))
    print("NK2DL_JSON_END")
    
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
"""
        temp_file.write(script_content.encode('utf-8'))
        
    return temp_path

def execute_submission_script(script_path: str, use_parser_instead_of_nuke: bool) -> Dict[int, List[str]]:
    """Execute the submission script in a subprocess."""
    if use_parser_instead_of_nuke:
        # Use regular Python
        executable = sys.executable
    else:
        # Use Nuke's Python
        try:
            import nuke
            nuke_dir = os.path.dirname(os.path.realpath(nuke.EXE_PATH))
            executable = os.path.join(nuke_dir, "python.exe")
        except ImportError:
            raise RuntimeError("Cannot use Nuke Python: nuke module not available")
    
    # Configure environment to ensure nk2dl module is available
    env = os.environ.copy()
    
    # Add the current module's parent directory to PYTHONPATH
    module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{module_dir}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = module_dir
    
    # Ensure the subprocess knows it's not a build job
    env["NK2DL_IN_BUILD_JOB"] = "false"
    
    logger.info(f"Using PYTHONPATH: {env.get('PYTHONPATH')}")
    logger.debug(f"Environment: NK2DL_IN_BUILD_JOB={env.get('NK2DL_IN_BUILD_JOB', 'not set')}")
    
    # Run subprocess with stdout and stderr set to PIPE but not capture_output
    # This allows us to read and display output in real-time
    logger.info(f"Launching subprocess using {executable} to parse Nuke script")
    
    # Use Popen instead of run to have more control over the process
    process = sp.Popen(
        [executable, script_path],
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        text=True,
        env=env,
        bufsize=1  # Line buffered
    )
    
    # Variables to store the complete stdout and stderr
    all_stdout = []
    all_stderr = []
    
    # Read and display output in real-time
    while True:
        # Read from stdout
        stdout_line = process.stdout.readline()
        if stdout_line:
            print(stdout_line, end='')  # Print to console in real-time
            all_stdout.append(stdout_line)
        
        # Read from stderr
        stderr_line = process.stderr.readline()
        if stderr_line:
            print(stderr_line, end='', file=sys.stderr)  # Print to stderr in real-time
            all_stderr.append(stderr_line)
        
        # Check if process has finished
        if process.poll() is not None:
            # Read any remaining output
            for line in process.stdout:
                print(line, end='')
                all_stdout.append(line)
            for line in process.stderr:
                print(line, end='', file=sys.stderr)
                all_stderr.append(line)
            break
    
    # Combine all captured output
    stdout = ''.join(all_stdout)
    stderr = ''.join(all_stderr)
    
    # Check if the process failed
    if process.returncode != 0:
        logger.error(f"Subprocess failed with exit code {process.returncode}")
        logger.error(f"STDERR: {stderr}")
        logger.error(f"STDOUT: {stdout}")
        raise RuntimeError(f"Subprocess failed: {stderr}")
    
    # Extract JSON output between markers
    try:
        # Find the JSON output between markers
        start_marker = "NK2DL_JSON_BEGIN"
        end_marker = "NK2DL_JSON_END"
        
        start_idx = stdout.find(start_marker)
        end_idx = stdout.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            logger.error(f"Could not find JSON markers in output - STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            raise RuntimeError(f"No JSON output markers found in subprocess output")
        
        # Extract the JSON string between markers
        json_str = stdout[start_idx + len(start_marker):end_idx].strip()
        
        # Parse JSON
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to parse subprocess output - STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        logger.error(f"Exception: {str(e)}")
        raise RuntimeError(f"Failed to parse subprocess output: {e}")

def script_parsing_required(**kwargs) -> bool:
    """Determine whether we need to parse the script based on kwargs.
    
    Args:
        **kwargs: Submission keyword arguments
        
    Returns:
        bool: True if script parsing is required, False otherwise
    """
    # Criteria that would require parsing the Nuke script
    # 1. If write_nodes_as_tasks is enabled, we need to parse the script to get write nodes
    # 2. If write_nodes is provided but we need to get frame ranges for each node with use_node_frame_list
    # 3. If frames contains tokens like 'f-l' or 'i', we need to parse the script to get the actual frame range
    # 4. If all the following are true, we need to parse the script:
    #    a. parse_output_paths_to_deadline is True
    #    b. At least one write node is specified or the default is all write nodes
    # 5. If we need to sort write nodes by render order or alphabetically
    
    # Check if required parameters are provided
    write_nodes_as_separate_jobs = kwargs.get('write_nodes_as_separate_jobs', False)
    write_nodes_as_tasks = kwargs.get('write_nodes_as_tasks', False)
    render_order_dependencies = kwargs.get('render_order_dependencies', False)
    submit_writes_alphabetically = kwargs.get('submit_writes_alphabetically', False)
    submit_writes_in_render_order = kwargs.get('submit_writes_in_render_order', False)
    use_node_frame_list = kwargs.get('use_node_frame_list', False)
    frames = kwargs.get('frames', '')
    parse_output_paths_to_deadline = kwargs.get('parse_output_paths_to_deadline', False)
    write_nodes = kwargs.get('write_nodes')
    
    # Check for token patterns in frames
    token_pattern = r"(?i)\b(f-l|first-last|f-m|f,m,l|i|input)\b"
    has_tokens = bool(re.search(token_pattern, frames)) if frames else False

    # Check criteria
    requires_parsing = (
        frames and (
            'i' in frames.lower() or 
            'input' in frames.lower()
        ) or
        use_node_frame_list or  # Need to parse to get frame ranges
        write_nodes_as_tasks or  # Need to parse to set up tasks
        write_nodes_as_separate_jobs or  # Need to parse to list write nodes
        render_order_dependencies or  # Need to parse to get render order
        submit_writes_alphabetically or  # Need to parse to list write nodes
        submit_writes_in_render_order or  # Need to parse to get render order of write nodes
        (parse_output_paths_to_deadline and (write_nodes or write_nodes is None))  # Need to parse to get output paths
    )
    
    return requires_parsing 