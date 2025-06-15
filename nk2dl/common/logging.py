"""Logging system for nk2dl.

This module provides a centralized logging configuration that integrates
with the configuration system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os
import inspect

from .config import config

# Module-level flag to track if we've already shown the initial config messages
_config_debug_shown = False
_nk2dl_env_debug_shown = False

def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Set up and return a logger instance.
    
    Args:
        name: Logger name (defaults to root logger if None)
        
    Returns:
        Configured logger instance
    """
    global _config_debug_shown, _nk2dl_env_debug_shown
    
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist (avoid duplicate handlers)
    if not logger.handlers:
        # Suppress config debug messages after first logger setup
        config_logger = logging.getLogger('nk2dl.common.config') if _config_debug_shown else None
        original_level = None
        if _config_debug_shown and config_logger:
            original_level = config_logger.level
            config_logger.setLevel(logging.INFO)
        
        # Get logging config
        log_level = config.get('logging.level', 'INFO')
        
        # Check if running in a build job via environment variable
        in_build_job = os.environ.get('NK2DL_IN_BUILD_JOB', 'false').lower() == 'true'
        
        # Create a basic formatter for initial debug message
        basic_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        
        # Create a temporary handler to log build job status
        temp_handler = logging.StreamHandler(sys.stdout)
        temp_handler.setFormatter(basic_formatter)
        logger.addHandler(temp_handler)
        numeric_level = getattr(logging, log_level.upper())
        logger.setLevel(numeric_level)
        
        # Log build job environment status for debugging - but add caller info after first time
        if name and name.startswith('nk2dl'):
            env_msg = f"NK2DL_IN_BUILD_JOB environment variable: '{os.environ.get('NK2DL_IN_BUILD_JOB', 'not set')}', in_build_job={in_build_job}"
            if not _nk2dl_env_debug_shown:
                logger.debug(env_msg)
                _nk2dl_env_debug_shown = True
            else:
                # Add caller information for subsequent calls
                caller_frame = inspect.currentframe().f_back
                caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
                logger.debug(f"{env_msg} (called from {caller_info})")
        
        # Remove the temporary handler after logging
        logger.removeHandler(temp_handler)
        
        # Use simplified format without timestamps when running in a build job
        if in_build_job:
            log_format = '%(name)s - %(levelname)s - %(message)s'
        else:
            # Regular format with timestamps
            log_format = config.get('logging.format', 
                                  '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Get log file
        log_file = config.get('logging.file')
        
        # Restore original config logger level if we suppressed it
        if original_level is not None and config_logger:
            config_logger.setLevel(original_level)
        
        # Mark that we've shown the config debug messages for the first time
        if not _config_debug_shown:
            _config_debug_shown = True
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Always add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if configured
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Set log level
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent propagation to root logger to avoid duplicate messages
        if name:
            logger.propagate = False
    
    return logger


def configure_logging(level: str = None) -> None:
    """Configure logging level dynamically.
    
    Args:
        level: Logging level to set (INFO, DEBUG, NOTSET)
    """
    if level:
        # Get the numeric level for easier comparison
        numeric_level = getattr(logging, level.upper())
        
        # Update root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Update all nk2dl loggers - both the base logger and all descendant loggers
        base_logger = logging.getLogger('nk2dl')
        base_logger.setLevel(numeric_level)
        
        # Find and update all nk2dl descendant loggers that may already exist
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            if logger_name == 'nk2dl' or logger_name.startswith('nk2dl.'):
                logging.getLogger(logger_name).setLevel(numeric_level)
        
        # Log the level change
        logger.debug(f"Logging level set to {level} for all nk2dl loggers")


# Create default logger
logger = setup_logging('nk2dl.common') 