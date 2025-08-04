"""
Centralized logging configuration for nk2dl.

This module provides logging setup and configuration management,
ensuring consistent formatting across all nk2dl modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os
import inspect
import datetime
import threading
import queue
import time

# Import config at module level but handle circular import gracefully
try:
    from . import config
except ImportError:
    config = None

# Module-level flag to track if we've already shown the initial config messages
_config_debug_shown = False
_nk2dl_env_debug_shown = False
_date_logged = False
_session_logged = False
_session_lock = threading.Lock()

# Module-level flag to temporarily disable caller information
_disable_caller_info = False

def _get_numeric_level(level):
    """Convert string level names to numeric values, handle both formats.
    
    Args:
        level: String level name (DEBUG, INFO, etc.) or numeric value
        
    Returns:
        int: Numeric logging level
    """
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    elif isinstance(level, int):
        return level
    else:
        return logging.INFO

class Nk2dlLogger(logging.Logger):
    """Custom logger that automatically adds caller information to DEBUG messages."""
    
    def debug(self, message, *args, **kwargs):
        """Override debug to automatically add caller information when level is at or below configured threshold."""
        # Get configured caller info level (default to INFO if not available)
        call_level = 'INFO'  # Default value - no caller info until explicitly configured to DEBUG
        try:
            if config and hasattr(config, 'config'):
                # Temporarily disable caller info to prevent recursion when accessing config
                global _disable_caller_info
                original_disable_state = _disable_caller_info
                _disable_caller_info = True
                try:
                    call_level = config.config.get('logging.call_level', 'INFO')
                finally:
                    _disable_caller_info = original_disable_state
        except:
            pass
        
        # Convert to numeric level
        call_level_numeric = _get_numeric_level(call_level)
        
        # Only add caller info if the DEBUG level is at/below the configured call_level threshold and not temporarily disabled
        if logging.DEBUG >= call_level_numeric and not _disable_caller_info:
            caller_info = self._get_caller_info()
            
            # Add caller info if we found it
            if caller_info:
                if args or kwargs:
                    # Format the message first if there are args
                    formatted_message = message % args if args else message
                    enhanced_message = f"{formatted_message}\n    called from {caller_info}"
                    # Call parent debug with enhanced message, no args to avoid double formatting
                    super().debug(enhanced_message, **kwargs)
                else:
                    enhanced_message = f"{message}\n    called from {caller_info}"
                    super().debug(enhanced_message, **kwargs)
            else:
                # Fallback to normal debug
                super().debug(message, *args, **kwargs)
        else:
            # Level > 9 or caller info disabled - just normal debug
            super().debug(message, *args, **kwargs)
    
    def _get_caller_info(self) -> Optional[str]:
        """Get caller information by walking the call stack."""
        try:
            # Walk up the call stack to find the actual caller
            frame = inspect.currentframe()
            while frame:
                frame = frame.f_back
                if not frame:
                    break
                
                filename = frame.f_code.co_filename
                # Skip internal logging methods
                if (filename.endswith('logging.py') or 
                    filename.endswith('__init__.py') or
                    frame.f_code.co_name in ['debug', '_get_caller_info', 'callHandlers', 'handle', 'emit']):
                    continue
                
                # Found the actual caller
                line_number = frame.f_lineno
                return f"{filename}:{line_number}"
                
        except Exception:
            pass
        
        return None

def disable_caller_info():
    """Temporarily disable caller information for debug messages."""
    global _disable_caller_info
    _disable_caller_info = True

def enable_caller_info():
    """Re-enable caller information for debug messages."""
    global _disable_caller_info
    _disable_caller_info = False

# Set the custom logger class globally for all new loggers
logging.setLoggerClass(Nk2dlLogger)

def get_nk2dl_logger(name: str) -> Nk2dlLogger:
    """Get a logger with the custom Nk2dlLogger class, ensuring it's properly configured."""
    # Ensure we're using the custom class
    original_class = logging.getLoggerClass()
    if original_class != Nk2dlLogger:
        logging.setLoggerClass(Nk2dlLogger)
    
    logger = logging.getLogger(name)
    
    # Restore original class if it was different
    if original_class != Nk2dlLogger:
        logging.setLoggerClass(original_class)
    
    return logger

def log_session_start():
    """Log the session start date if in DEBUG mode and not already logged."""
    global _session_logged
    
    with _session_lock:
        if _session_logged:
            return
        
        # Get the first nk2dl logger to check level
        try:
            test_logger = get_nk2dl_logger('nk2dl.common')
            if test_logger.isEnabledFor(logging.DEBUG):
                from datetime import datetime
                date_str = datetime.now().strftime('%Y-%m-%d')
                test_logger.debug(f"=== Logging session started on {date_str} ===")
                _session_logged = True
        except Exception:
            pass

def setup_logging(name: str) -> Nk2dlLogger:
    """
    Set up logging configuration for nk2dl modules.
    
    Args:
        name: The logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    # Log session start on first nk2dl logger creation
    log_session_start()
    
    # Get logger with custom class
    logger = get_nk2dl_logger(name)
    
    # Get configuration if available
    global config
    if config is None:
        try:
            from . import config as config_module
            config = config_module
        except ImportError:
            pass
    
    if config and hasattr(config, 'config'):
        # Get configured values
        # Temporarily disable caller info to prevent recursion when accessing config
        global _disable_caller_info
        original_disable_state = _disable_caller_info
        _disable_caller_info = True
        try:
            log_format = config.config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            level = config.config.get('logging.level', 'INFO')
            log_file = config.config.get('logging.file', None)
        finally:
            _disable_caller_info = original_disable_state
    else:
        # Fallback configuration
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        level = 'INFO'
        log_file = None
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
    
    # Set up handlers if not already configured
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not set up file logging to {log_file}: {e}")
        
        # Set level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Prevent duplicate messages
        logger.propagate = False
    
    return logger

def fix_existing_loggers() -> None:
    """Fix any existing nk2dl loggers to use consistent formatting."""
    # Set the custom logger class for future loggers
    logging.setLoggerClass(Nk2dlLogger)
    
    # Get configured format
    if config and hasattr(config, 'config'):
        # Temporarily disable caller info to prevent recursion when accessing config
        global _disable_caller_info
        original_disable_state = _disable_caller_info
        _disable_caller_info = True
        try:
            log_format = config.config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            level = config.config.get('logging.level', 'INFO')
        finally:
            _disable_caller_info = original_disable_state
    else:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        level = 'INFO'
    
    formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Fix formatting for existing nk2dl loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        if logger_name == 'nk2dl' or logger_name.startswith('nk2dl.'):
            existing_logger = logging.getLogger(logger_name)
            
            # Update level
            existing_logger.setLevel(numeric_level)
            
            # Update handler formatters
            for handler in existing_logger.handlers:
                handler.setFormatter(formatter)


def configure_logging(level: str = None, qt_level = None, call_level = None) -> None:
    """Configure logging level dynamically.
    
    Args:
        level: Logging level to set (INFO, DEBUG, NOTSET)
        qt_level: Level for Qt debug messages - string (DEBUG, INFO, etc.) or numeric (None to keep current)
        call_level: Level for caller information - string (DEBUG, INFO, etc.) or numeric (None to keep current)
    """
    global _disable_caller_info
    
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
        
        # Fix any existing loggers to use consistent formatting
        fix_existing_loggers()
        
        # Log the level change
        logger.debug(f"Logging level set to {level} for all nk2dl loggers")
    
    # Update caller info level if specified  
    if call_level is not None and config:
        try:
            # Temporarily disable caller info to prevent recursion when accessing config
            original_disable_state = _disable_caller_info
            _disable_caller_info = True
            try:
                # Update config in memory
                if 'logging' not in config.config._config:
                    config.config._config['logging'] = {}
                config.config._config['logging']['call_level'] = call_level
                logger.debug(f"Call level set to {call_level}")
            finally:
                _disable_caller_info = original_disable_state
        except Exception as e:
            logger.warning(f"Failed to set call level: {e}")


# Create default logger with custom class
logging.setLoggerClass(Nk2dlLogger)
logger = setup_logging('nk2dl.common') 