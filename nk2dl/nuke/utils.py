"""Utility functions for working with Nuke.

This module provides utility functions for working with Nuke, including
functions to get the Nuke module, get node file paths, and get Nuke version.
"""

import re
from typing import Any, Optional, Union

from ..common.config import config
from ..common.errors import SubmissionError
from ..common.logging import logger

# Global variable to store nuke module when imported
_nuke_module = None

def nuke_module():
    """Get the nuke module, importing it if necessary.
    
    Returns:
        The nuke module.
        
    Raises:
        SubmissionError: If nuke module is not available.
    """
    global _nuke_module
    if _nuke_module is None:
        try:
            import nuke
            _nuke_module = nuke
        except (ImportError, ModuleNotFoundError):
            raise SubmissionError("The Nuke Python API is required but not available. "
                                 "This module must be run from within Nuke or nuke should be available in the system path.")
    return _nuke_module

def node_pretty_path(node) -> str:
    """Get a node's file path while preserving frame number placeholders.
    
    When Nuke evaluates a file path with node['file'].evaluate(), it replaces
    frame number placeholders (e.g., '####', '%04d') with the actual frame number.
    This function evaluates the path but restores those placeholders.
    
    Args:
        node: A Nuke node with a 'file' knob
        
    Returns:
        The evaluated file path with frame number placeholders preserved
    """
    nuke = nuke_module()
    
    if not 'file' in node.knobs():
        return ""
        
    try:
        # Get the original unexpanded file path expression
        original_path = node['file'].value()
        logger.debug(f"{node.name()} Original path: {original_path}")

        # Evaluate the path (which will substitute the current frame number)
        evaluated_path = node['file'].evaluate()
        logger.debug(f"{node.name()} Nuke evaluated path: {evaluated_path}")

        # Check if the original path had frame number placeholders
        has_hash_placeholder = re.search(r'#+', original_path) is not None
        has_printf_placeholder = re.search(r'%\d*d', original_path) is not None
        
        if has_hash_placeholder or has_printf_placeholder:
            # Get the frame number format from the original path
            if has_hash_placeholder:
                # Extract the hash sequence (e.g., '####')
                hash_match = re.search(r'(#+)', original_path)
                if hash_match:
                    placeholder = hash_match.group(1)
                    
                    # Create a regex pattern to find the frame number in the evaluated path
                    # Use only the suffix for more reliable matching
                    parts = original_path.split(placeholder)
                    if len(parts) >= 2:
                        suffix = re.escape(parts[1]) if len(parts) > 1 else ''
                        # Only match against the suffix
                        pattern = f"(\\d+){suffix}"
                        
                        # Find and replace the frame number with the original placeholder
                        frame_match = re.search(pattern, evaluated_path)
                        if frame_match:
                            frame_num = frame_match.group(1)
                            evaluated_path = evaluated_path.replace(frame_num, placeholder, 1)
            
            elif has_printf_placeholder:
                # Extract the printf format (e.g., '%04d')
                printf_match = re.search(r'(%\d*d)', original_path)
                if printf_match:
                    placeholder = printf_match.group(1)
                    
                    # Create a regex pattern to find the frame number in the evaluated path
                    # Use only the suffix for more reliable matching
                    parts = original_path.split(placeholder)
                    if len(parts) >= 2:
                        suffix = re.escape(parts[1]) if len(parts) > 1 else ''
                        # Only match against the suffix
                        pattern = f"(\\d+){suffix}"
                        
                        # Find and replace the frame number with the original placeholder
                        frame_match = re.search(pattern, evaluated_path)
                        if frame_match:
                            frame_num = frame_match.group(1)
                            evaluated_path = evaluated_path.replace(frame_num, placeholder, 1)

        # Check if the path contains GSV variables like %{shotcode}
        gsv_pattern = r'%\{([^}]+)\}'
        gsv_matches = re.finditer(gsv_pattern, evaluated_path)
        
        # If unevaluated GSV variables are found, evaluate them
        if re.search(gsv_pattern, evaluated_path):
            try:
                # Get the root node to access GSV knob
                root_node = nuke_module().root()
                if 'gsv' in root_node.knobs():
                    gsv_knob = root_node['gsv']
                    
                    # For each GSV variable found, replace with its value
                    for match in re.finditer(gsv_pattern, evaluated_path):
                        logger.debug(f"Found unevaluated GSV variable: {match.group(1)}")

                        var_name = match.group(1)
                        var_value = gsv_knob.getGsvValue(var_name)
                        
                        if var_value:
                            # Replace the GSV placeholder with its value
                            gsv_placeholder = match.group(0)  # %{var_name}
                            evaluated_path = evaluated_path.replace(gsv_placeholder, var_value)
            except Exception as e:
                logger.warning(f"Error evaluating GSV variables: {e}")

        # If no placeholders or replacement failed, return the evaluated path
        logger.debug(f"{node.name()} Pretty path: {evaluated_path}")
        return evaluated_path
        
    except Exception as e:
        logger.warning(f"Error evaluating node file path: {e}")
        return ""

def nuke_version(nuke_version: Optional[Union[str, int, float]] = None) -> str:
    """Get the Nuke version to use for rendering.
    
    Uses the following priority:
    1. The nuke_version parameter provided 
    2. The nuke_version value from config
    3. The current Nuke version
    
    Args:
        nuke_version: Optional Nuke version to use. Can be string, int, or float.
    
    Returns:
        Version string in format "MAJOR.MINOR" (e.g. "13.0")
    """
    # If nuke_version was provided
    if nuke_version is not None:
        # Handle different input types
        if isinstance(nuke_version, int):
            # Integer: add ".0" (e.g., 15 -> "15.0")
            return f"{nuke_version}.0"
        elif isinstance(nuke_version, float):
            # Float: convert to string (e.g., 15.1 -> "15.1")
            return str(nuke_version)
        else:
            # String or anything else: convert to string
            return str(nuke_version)
    
    # Check if nuke_version is in config
    config_version = config.get('submission.nuke_version')
    if config_version is not None:
        # Handle different config value types
        if isinstance(config_version, int):
            return f"{config_version}.0"
        elif isinstance(config_version, float):
            return str(config_version)
        else:
            return str(config_version)
    
    # Fall back to current Nuke version
    nuke = nuke_module()
    major = nuke.NUKE_VERSION_MAJOR
    minor = nuke.NUKE_VERSION_MINOR
    return f"{major}.{minor}" 