"""
Nuke to Deadline Submitter - Core Library

A pure Python library for submitting nukescripts to Thinkbox Deadline.
"""

from datetime import date
from . import info
import os

if not os.environ.get('NK2DL_HIDE_COPYRIGHT', ''):
    print(f"\nNuke to Deadline (nk2dl) v{info.__version__}")
    print(f"Copyright (c) {date.today().year} {info.__author__}. All Rights Reserved.\n")

from .submission import submit_nuke_script as _submit_nuke_script

def submit_nuke_script(script_path, **kwargs):
    """Submit a Nuke script to Deadline render farm.
    
    This is the primary entry point for the nk2dl package. It handles parsing the script,
    configuring job parameters, and submitting to Deadline.
    
    Args:
        script_path (str): Path to the Nuke script file (.nk)
        **kwargs: Submission parameters
    
        # For full parameter list, see the NukeSubmission class documentation
    
    Returns:
        list: List of dictionaries containing job information:
            - job_id (str): The Deadline job ID
            - render_order (int): The render order value
            - plugin_info (dict): Plugin info used for submission
            - job_info (dict): Job info used for submission
            - deadline_return (dict): Raw return data from Deadline
    
    Examples:
        Basic usage:
        >>> from nk2dl import submit_nuke_script
        >>> submit_nuke_script("path/to/script.nk")
        
        With specific write nodes:
        >>> submit_nuke_script("path/to/script.nk", write_nodes=["Write1", "Write2"])
        
        With job parameters:
        >>> submit_nuke_script(
        ...     "path/to/script.nk",
        ...     priority=80,
        ...     pool="nuke",
        ...     chunk_size=10,
        ...     comment="Render {script} on farm"
        ... )
        
        Submit as a Python script job (ScriptJob in Deadline):
        >>> submit_nuke_script(
        ...     "path/to/script.nk",
        ...     submission_as_script_job=True
        ... )
    
    Raises:
        NK2DLError: For configuration or submission errors
    """
    return _submit_nuke_script(script_path, **kwargs)

__all__ = ["submit_nuke_script"]