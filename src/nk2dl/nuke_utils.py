"""Utility functions for working with Nuke.

This module provides utility functions for working with Nuke, including
functions to get the Nuke module, get node file paths, and get Nuke version.
"""

import re
import os
from typing import Any, Optional, Union

from .config import config
from .errors import SubmissionError
from .logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.nuke.utils')

# Global variable to store nuke module when imported
_nuke_module = None
_parser_module = None


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
            logger.info("Importing Nuke module. This may take a while...")
            import nuke
            _nuke_module = nuke
        except (ImportError, ModuleNotFoundError):
            raise SubmissionError("The Nuke Python API is required but not available. "
                                 "This module must be run from within Nuke or nuke should be available in the system path.")
    return _nuke_module


def parser_module():
    """Get the parser module, creating it if necessary.
    
    This module is intended to provide a lightweight alternative to the real Nuke module
    for parsing Nuke scripts without loading Nuke itself.
    
    Returns:
        A parser instance that mimics the nuke module interface.
        
    Raises:
        SubmissionError: If the parser module is not available or functionality is incomplete.
    """
    global _parser_module
    if _parser_module is None:
        try:
            logger.info("Creating parser module...")
            from . import parser
            _parser_module = parser.create_parser()
        except (ImportError, ModuleNotFoundError):
            raise SubmissionError("The nukescript parser is required but is not available or implemented.")
    return _parser_module


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

        # Define frame placeholder patterns and their temporary replacements
        frame_placeholders = []
        
        # Find hash placeholders (####, ###, etc.)
        hash_matches = list(re.finditer(r'#+', original_path))
        for i, match in enumerate(hash_matches):
            placeholder = match.group(0)
            token = f"__FRAME_HASH_{len(placeholder)}_{i}__"
            frame_placeholders.append((placeholder, token))
        
        # Find printf placeholders (%04d, %d, etc.)
        printf_matches = list(re.finditer(r'%\d*d', original_path))
        for i, match in enumerate(printf_matches):
            placeholder = match.group(0)
            token = f"__FRAME_PRINTF_{placeholder.replace('%', '').replace('d', '')}_{i}__"
            frame_placeholders.append((placeholder, token))

        if frame_placeholders:
            # Step 1: Replace frame placeholders with temporary tokens
            modified_path = original_path
            for placeholder, token in frame_placeholders:
                modified_path = modified_path.replace(placeholder, token)
            
            logger.debug(f"{node.name()} Modified path with tokens: {modified_path}")
            
            # Step 2: Temporarily set the node's file path to the tokenized version
            original_knob_value = node['file'].value()
            node['file'].setValue(modified_path)
            
            # Step 3: Evaluate the path (this will resolve metadata but leave our tokens intact)
            evaluated_path = node['file'].evaluate()
            logger.debug(f"{node.name()} Evaluated path with tokens: {evaluated_path}")
            
            # Step 4: Restore the original file path
            node['file'].setValue(original_knob_value)
            
            # Step 5: Replace tokens back with original placeholders
            for placeholder, token in frame_placeholders:
                evaluated_path = evaluated_path.replace(token, placeholder)
            
            logger.debug(f"{node.name()} Final path with restored placeholders: {evaluated_path}")
        
        else:
            # No frame placeholders found, just evaluate normally
            evaluated_path = node['file'].evaluate()
            
        # Check if the path contains GSV variables like %{shotcode}
        gsv_pattern = r'%\{([^}]+)\}'
        if re.search(gsv_pattern, evaluated_path):
            try:
                # Get the root node to access GSV knob
                root_node = nuke_module().root()
                if 'gsv' in root_node.knobs():
                    gsv_knob = root_node['gsv']
                    
                    # For each GSV variable found, replace with its value
                    for match in re.finditer(gsv_pattern, evaluated_path):
                        var_name = match.group(1)
                        var_value = gsv_knob.getGsvValue(var_name)

                        logger.debug(f"Found unevaluated GSV variable: {var_name} = {var_value}")       

                        if var_value:
                            # Replace the GSV placeholder with its value
                            gsv_placeholder = match.group(0)  # %{var_name}
                            evaluated_path = evaluated_path.replace(gsv_placeholder, var_value)
            except Exception as e:
                logger.warning(f"Error evaluating GSV variables: {e}")

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