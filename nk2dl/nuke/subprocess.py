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

from ..common.framerange import FrameRange
from ..common.logging import logger

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
    
    # Add script_path_same_as_current_nuke_session=True
    kwargs['script_path_same_as_current_nuke_session'] = True
    
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
    
    logger.info(f"Using PYTHONPATH: {env.get('PYTHONPATH')}")
    
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

def script_parsing_required(**kwargs):
    """Determine if we need to parse the Nuke script based on submission parameters.
    
    Args:
        **kwargs: Keyword arguments from submission function
        
    Returns:
        bool: True if script parsing is required, False otherwise
    """
    
    # Extract relevant parameters
    write_nodes = kwargs.get('write_nodes', None)

    # Extract string fields that might contain tokens
    job_name = kwargs.get('job_name', '')
    batch_name = kwargs.get('batch_name', '')
    comment = kwargs.get('comment', '')
    extra_info = kwargs.get('extra_info', '')
    
    # Define token groups that require script parsing
    file_stem_tokens    = ["{fs}", "{fns}", "{os}", "{fstem}", "{ostem}", "{filestem}", "{file_stem}", 
                           "{filenamestem}", "{filename_stem}", "{outputstem}", "{output_stem}"]
    output_tokens       = ["{o}", "{fn}", "{file}", "{filename}", "{file_name}", "{output}"]
    render_order_tokens = ["{r}", "{ro}", "{renderorder}", "{render_order}"]
    gsv_tokens          = ["{g}", "{gsv}", "{gsvs}", "{GSVs}", "{graphscopevars}", "{graphscopevariables}", 
                           "{graph_scope_vars}", "{graph_scope_variables}"]
    
    # Write node tokens require parsing only if write_nodes not specified
    write_node_tokens = ["{w}", "{wn}", "{write}", "{writenode}", "{write_node}", "{write_name}"]
    
    # Combine all token groups that require parsing
    parsing_required_tokens = file_stem_tokens + output_tokens + render_order_tokens + gsv_tokens
    
    # If write_nodes is not specified, add write_node_tokens to parsing_required_tokens
    if not write_nodes:
        parsing_required_tokens.extend(write_node_tokens)
    
    # Check if any of the string fields contain tokens requiring parsing
    fields_to_check = [job_name, batch_name, comment, extra_info]
    for field in fields_to_check:
        if any(token in field for token in parsing_required_tokens):
            return True

    # Extract rem relevant parameters
    frame_range = kwargs.get('frame_range', '')
    submit_alphabetically = kwargs.get('submit_alphabetically', False)
    submit_in_render_order = kwargs.get('submit_in_render_order', False)
    write_nodes_as_tasks = kwargs.get('write_nodes_as_tasks', False)
    write_nodes_as_separate_jobs = kwargs.get('write_nodes_as_separate_jobs', False)
    render_order_dependencies = kwargs.get('render_order_dependencies', False)
    use_nodes_frame_list = kwargs.get('use_nodes_frame_list', False)
    graph_scope_variables = kwargs.get('graph_scope_variables', None)
    parse_output_paths_to_deadline = kwargs.get('parse_output_paths_to_deadline', False)

    # Check if frame range has tokens using FrameRange's has_tokens property
    fr = FrameRange(frame_range)
    
    # Check other conditions requiring script parsing
    return (fr.has_tokens or
            (submit_alphabetically and not write_nodes) or
            submit_in_render_order or
            (not write_nodes and (write_nodes_as_tasks or write_nodes_as_separate_jobs)) or
            render_order_dependencies or
            use_nodes_frame_list or
            graph_scope_variables is not None or
            parse_output_paths_to_deadline) 