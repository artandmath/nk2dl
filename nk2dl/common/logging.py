"""Logging system for nk2dl.

This module provides a centralized logging configuration that integrates
with the configuration system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import config

def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Set up and return a logger instance.
    
    Args:
        name: Logger name (defaults to root logger if None)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist (avoid duplicate handlers)
    if not logger.handlers:
        # Get logging config
        log_level = config.get('logging.level', 'INFO')
        log_format = config.get('logging.format', 
                              '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = config.get('logging.file')
        
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

# Create default logger
logger = setup_logging('nk2dl') 