"""Error handling for nk2dl.

This module defines custom exceptions and error handling utilities.
"""

class NK2DLError(Exception):
    """Base exception for all nk2dl errors."""
    pass

class ConfigError(NK2DLError):
    """Configuration related errors."""
    pass

class ValidationError(NK2DLError):
    """Validation related errors."""
    pass

class DeadlineError(NK2DLError):
    """Deadline connection/communication errors."""
    pass

class SubmissionError(NK2DLError):
    """Job submission related errors."""
    pass

class NukeError(NK2DLError):
    """Nuke script/execution related errors."""
    pass

class ParserError(NK2DLError):
    """Parser related errors when parsing Nuke scripts without using Nuke."""
    pass

def handle_error(error: Exception, logger=None) -> None:
    """Handle an error by logging it and optionally performing additional actions.
    
    Args:
        error: The exception to handle
        logger: Optional logger instance to use
    """
    from .logging import logger as default_logger
    log = logger or default_logger
    
    if isinstance(error, NK2DLError):
        # Handle known errors
        log.error(str(error))
    else:
        # Handle unexpected errors
        log.exception("An unexpected error occurred") 