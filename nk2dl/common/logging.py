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
        # Get configured caller info level (default to DEBUG if not available)
        call_level = 'DEBUG'  # Default value
        try:
            if config and hasattr(config, 'config'):
                call_level = config.config.get('logging.call_level', 'DEBUG')
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
        log_format = config.config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        level = config.config.get('logging.level', 'INFO')
        log_file = config.config.get('logging.file', None)
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
        log_format = config.config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        level = config.config.get('logging.level', 'INFO')
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
        
        # Sync Qt logger levels
        sync_qt_logger_levels()
        
        # Install Qt message handler to capture Qt internal messages
        if install_qt_message_handler():
            logger.debug("Qt message handler installed successfully")
        else:
            logger.debug("Qt message handler installation skipped (Qt not available)")
        
        # Log the level change
        logger.debug(f"Logging level set to {level} for all nk2dl loggers")
    
    # Update Qt debug level if specified
    if qt_level is not None and config:
        try:
            # Update config in memory
            if 'logging' not in config.config._config:
                config.config._config['logging'] = {}
            config.config._config['logging']['qt_level'] = qt_level
            
            # Sync Qt logger levels
            sync_qt_logger_levels()
            logger.debug(f"Qt level set to {qt_level}")
        except Exception as e:
            logger.warning(f"Failed to set Qt level: {e}")
    
    # Update caller info level if specified  
    if call_level is not None and config:
        try:
            # Update config in memory
            if 'logging' not in config.config._config:
                config.config._config['logging'] = {}
            config.config._config['logging']['call_level'] = call_level
            logger.debug(f"Call level set to {call_level}")
        except Exception as e:
            logger.warning(f"Failed to set call level: {e}")


# Create default logger with custom class
logging.setLoggerClass(Nk2dlLogger)
logger = setup_logging('nk2dl.common')

# Qt-specific debugging utilities
class QtDebugLogger:
    """Specialized logger for Qt debugging with asynchronous processing to prevent UI lag."""
    
    def __init__(self, logger_name: str = 'nk2dl.qt', async_logging: bool = True, adaptive: bool = True):
        # Use setup_logging to ensure proper formatting and handlers
        self.logger = setup_logging(logger_name)
        self._nuke_available = None
        self.async_logging = async_logging
        self.adaptive = adaptive
        
        # Adaptive logging state
        self.ui_operation_active = False
        self.message_count = 0
        self.last_reset_time = time.time()
        self.max_messages_per_second = 50  # Throttle to 50 messages/second during UI ops
        
        # Set Qt debug level from configuration (default to DEBUG if not available)
        qt_level = 'DEBUG'  # Default value  
        try:
            if config and hasattr(config, 'config'):
                qt_level = config.config.get('logging.qt_level', 'DEBUG')
        except:
            pass
        
        # Convert to numeric level and set
        qt_level_numeric = _get_numeric_level(qt_level)
        self.logger.setLevel(qt_level_numeric)
        
        # Store qt_level for use in logging methods
        self.qt_level_numeric = qt_level_numeric
        
        # Initialize async logging if enabled
        if self.async_logging:
            self._init_async_logging()
        
        # Debug: Confirm initialization
        try:
            import nuke
            nuke.tprint(f"[NK2DL QT INIT] QtDebugLogger created with level: {self.logger.getEffectiveLevel()}, async: {self.async_logging}, adaptive: {self.adaptive}")
        except:
            pass
    
    def _init_async_logging(self):
        """Initialize asynchronous logging system to prevent UI lag."""
        # Create thread-safe queue for log messages
        self.log_queue = queue.Queue(maxsize=1000)  # Limit queue size to prevent memory issues
        self.logging_thread = None
        self.shutdown_event = threading.Event()
        
        # Start background logging thread
        self._start_logging_thread()
    
    def _start_logging_thread(self):
        """Start the background thread that processes log messages."""
        if self.logging_thread is None or not self.logging_thread.is_alive():
            self.shutdown_event.clear()
            self.logging_thread = threading.Thread(
                target=self._process_log_queue,
                name="QtDebugLogger",
                daemon=True  # Dies when main thread dies
            )
            self.logging_thread.start()
    
    def _process_log_queue(self):
        """Background thread function that processes queued log messages."""
        while not self.shutdown_event.is_set():
            try:
                # Get message from queue with timeout
                try:
                    level, message = self.log_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Process the log message in background thread
                if level == logging.DEBUG:
                    self.logger.debug(message)
                elif level == logging.INFO:
                    self.logger.info(message)
                elif level == logging.WARNING:
                    self.logger.warning(message)
                elif level == logging.ERROR:
                    self.logger.error(message)
                
                # Mark task as done
                self.log_queue.task_done()
                
            except Exception as e:
                # Don't let logging errors crash the thread
                try:
                    self.logger.error(f"Error in async logging thread: {e}")
                except:
                    pass
    
    def _queue_message(self, level: int, message: str):
        """Queue a message for asynchronous processing.
        
        Args:
            level: Logging level (logging.DEBUG, etc.)
            message: Message to log
        """
        if not self.async_logging:
            # Fallback to synchronous logging
            return False
        
        try:
            # Try to add to queue without blocking
            self.log_queue.put_nowait((level, message))
            return True
        except queue.Full:
            # Queue is full, drop the message to prevent UI blocking
            # This is better than blocking the UI thread
            return False
    
    def shutdown(self):
        """Shutdown the async logging system gracefully."""
        if hasattr(self, 'shutdown_event'):
            self.shutdown_event.set()
        
        if hasattr(self, 'logging_thread') and self.logging_thread and self.logging_thread.is_alive():
            # Wait for thread to finish processing remaining messages
            try:
                self.logging_thread.join(timeout=1.0)  # Don't wait too long
            except:
                pass
    
    def _check_nuke(self):
        """Check if nuke is available (cached)."""
        if self._nuke_available is None:
            try:
                import nuke
                self._nuke_available = True
            except ImportError:
                self._nuke_available = False
        return self._nuke_available
    
    def debug(self, message: str):
        """Log Qt debug message with [QT] prefix asynchronously.
        
        Args:
            message: Debug message to log
        """
        # Only log Qt debug messages if the DEBUG level is at/below the configured qt_level threshold
        if logging.DEBUG >= self.qt_level_numeric and self.logger.isEnabledFor(logging.DEBUG) and self._should_log_message(logging.DEBUG):
            qt_message = f"[QT] {message}"
            
            # Try async logging first, fallback to sync if needed
            if not self._queue_message(logging.DEBUG, qt_message):
                # Fallback to synchronous logging if queue is full or async disabled
                self.logger.debug(qt_message)
    
    def info(self, message: str):
        """Log Qt info message with [QT] prefix asynchronously.
        
        Args:
            message: Info message to log
        """
        if self._should_log_message(logging.INFO):
            qt_message = f"[QT] {message}"
            
            if not self._queue_message(logging.INFO, qt_message):
                self.logger.info(qt_message)
    
    def warning(self, message: str):
        """Log Qt warning message with [QT] prefix asynchronously.
        
        Args:
            message: Warning message to log
        """
        if self._should_log_message(logging.WARNING):
            qt_message = f"[QT] {message}"
            
            if not self._queue_message(logging.WARNING, qt_message):
                self.logger.warning(qt_message)
    
    def error(self, message: str):
        """Log Qt error message with [QT] prefix asynchronously.
        
        Args:
            message: Error message to log
        """
        if self._should_log_message(logging.ERROR):
            qt_message = f"[QT] {message}"
            
            if not self._queue_message(logging.ERROR, qt_message):
                self.logger.error(qt_message)

    def set_ui_operation_mode(self, active: bool):
        """Enable/disable UI operation mode for adaptive logging.
        
        During UI operations (like column width calculations), logging can be
        throttled to prevent performance issues.
        
        Args:
            active: True when UI operation is active, False when complete
        """
        self.ui_operation_active = active
        if not active:
            # Reset message count when UI operation completes
            self.message_count = 0
            self.last_reset_time = time.time()
    
    def _should_log_message(self, level: int) -> bool:
        """Determine if a message should be logged based on adaptive settings.
        
        Args:
            level: Logging level
            
        Returns:
            bool: True if message should be logged
        """
        if not self.adaptive:
            return True
        
        # Always log warnings and errors
        if level >= logging.WARNING:
            return True
        
        # If not in UI operation mode, log everything
        if not self.ui_operation_active:
            return True
        
        # During UI operations, throttle debug/info messages
        current_time = time.time()
        
        # Reset counter every second
        if current_time - self.last_reset_time >= 1.0:
            self.message_count = 0
            self.last_reset_time = current_time
        
        # Check if we're over the rate limit
        if self.message_count >= self.max_messages_per_second:
            return False
        
        self.message_count += 1
        return True
    
    def _sync_logging_level(self):
        """Sync Qt logger level with current configuration."""
        qt_level = 'DEBUG'  # Default value
        try:
            if config and hasattr(config, 'config'):
                qt_level = config.config.get('logging.qt_level', 'DEBUG')
        except:
            pass
        
        # Convert to numeric level and set
        qt_level_numeric = _get_numeric_level(qt_level)
        self.logger.setLevel(qt_level_numeric)
        
        # Store qt_level for use in logging methods
        self.qt_level_numeric = qt_level_numeric

# Global Qt debug logger instance (created lazily)
_qt_logger_instance = None

def get_qt_logger(logger_name: str = None) -> QtDebugLogger:
    """Get a Qt-specific debug logger.
    
    Args:
        logger_name: Optional custom logger name (defaults to 'nk2dl.qt')
        
    Returns:
        QtDebugLogger instance
    """
    global _qt_logger_instance
    
    if logger_name:
        return QtDebugLogger(logger_name)
        
    # Create the global qt_logger lazily after main logging is configured
    if _qt_logger_instance is None:
        _qt_logger_instance = QtDebugLogger()
        
    return _qt_logger_instance

def sync_qt_logger_levels():
    """Synchronize all Qt logger levels with main configuration.
    
    This should be called whenever the main logging level changes.
    """
    try:
        # Get qt_level from configuration
        qt_level = 'DEBUG'  # Default value
        if config and hasattr(config, 'config'):
            qt_level = config.config.get('logging.qt_level', 'DEBUG')
        
        # Convert to numeric level
        qt_level_numeric = _get_numeric_level(qt_level)
        
        # Sync the global qt_logger if it exists
        global _qt_logger_instance
        if _qt_logger_instance is not None:
            _qt_logger_instance._sync_logging_level()
        
        # Also sync any custom Qt loggers that might exist
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            if logger_name.startswith('nk2dl.qt'):
                qt_logger_instance = logging.getLogger(logger_name)
                if hasattr(qt_logger_instance, '_sync_logging_level'):
                    qt_logger_instance._sync_logging_level()
                else:
                    # For regular loggers like nk2dl.qt.system, set level directly
                    qt_logger_instance.setLevel(qt_level_numeric)
                    
    except Exception:
        pass

# Expose the lazy qt_logger at module level for easy importing
def _get_qt_logger():
    """Get the global Qt logger instance."""
    return get_qt_logger()

# Create a property-like access for the qt_logger
class QtLoggerProxy:
    """Proxy object that provides access to the lazily-created qt_logger."""
    def __getattr__(self, name):
        qt_logger_instance = get_qt_logger()
        return getattr(qt_logger_instance, name)

# Module-level qt_logger proxy
qt_logger = QtLoggerProxy()

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6.QtCore import qInstallMessageHandler, QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg, QtInfoMsg
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2.QtCore import qInstallMessageHandler, QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg, QtInfoMsg
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6.QtCore import qInstallMessageHandler, QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg, QtInfoMsg
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2.QtCore import qInstallMessageHandler, QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg, QtInfoMsg
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            # Qt not available, define dummy functions
            qInstallMessageHandler = None
            QtDebugMsg = QtWarningMsg = QtCriticalMsg = QtFatalMsg = QtInfoMsg = None 

def qt_message_handler(mode, context, message):
    """Qt message handler that redirects Qt internal messages to Python logging.
    
    This captures ALL Qt messages (debug, warnings, errors, etc.) and routes them
    through our logging system with appropriate levels and formatting.
    
    Args:
        mode: Qt message type (QtDebugMsg, QtWarningMsg, etc.)
        context: Qt message context (file, line, function)
        message: The actual message string
    """
    # Get or create a Qt system logger
    qt_system_logger = get_nk2dl_logger('nk2dl.qt.system')
    
    # Set Qt system logger level based on qt_level configuration
    try:
        qt_level = 'DEBUG'  # Default value
        if config and hasattr(config, 'config'):
            qt_level = config.config.get('logging.qt_level', 'DEBUG')
        
        # Convert to numeric level and set
        qt_level_numeric = _get_numeric_level(qt_level)
        qt_system_logger.setLevel(qt_level_numeric)
    except:
        pass
    
    # Format the message with context if available
    if context and hasattr(context, 'file') and context.file:
        # Extract just the filename from the full path
        filename = context.file.split('/')[-1].split('\\')[-1] if context.file else 'unknown'
        formatted_message = f"[QT-SYS] {message} ({filename}:{context.line})"
    else:
        formatted_message = f"[QT-SYS] {message}"
    
    # Map Qt message types to Python logging levels
    if mode == QtDebugMsg:
        qt_system_logger.debug(formatted_message)
    elif mode == QtInfoMsg:
        qt_system_logger.info(formatted_message)
    elif mode == QtWarningMsg:
        qt_system_logger.warning(formatted_message)
    elif mode == QtCriticalMsg:
        qt_system_logger.error(formatted_message)
    elif mode == QtFatalMsg:
        qt_system_logger.critical(formatted_message)
    else:
        # Unknown message type, log as info
        qt_system_logger.info(f"[QT-SYS-UNKNOWN] {message}")


def install_qt_message_handler():
    """Install the Qt message handler to redirect Qt messages to Python logging.
    
    This should be called once during application initialization to capture
    all Qt internal messages and route them through our logging system.
    
    Returns:
        bool: True if handler was installed successfully, False otherwise
    """
    if qInstallMessageHandler is None:
        # Qt not available
        return False
    
    try:
        # Install our custom message handler
        qInstallMessageHandler(qt_message_handler)
        
        # Log successful installation
        qt_system_logger = get_nk2dl_logger('nk2dl.qt.system')
        qt_system_logger.info("Qt message handler installed - Qt internal messages will be logged")
        
        return True
        
    except Exception as e:
        # Fallback logging if Qt logger isn't available yet
        try:
            import nuke
            nuke.tprint(f"[NK2DL] Failed to install Qt message handler: {e}")
        except:
            print(f"[NK2DL] Failed to install Qt message handler: {e}")
        
        return False


def uninstall_qt_message_handler():
    """Uninstall the Qt message handler and restore default Qt logging.
    
    This restores Qt's default message handling behavior.
    """
    if qInstallMessageHandler is None:
        return False
    
    try:
        # Restore default Qt message handler
        qInstallMessageHandler(None)
        
        # Log successful uninstallation  
        qt_system_logger = get_nk2dl_logger('nk2dl.qt.system')
        qt_system_logger.info("Qt message handler uninstalled - restored default Qt logging")
        
        return True
        
    except Exception as e:
        try:
            import nuke
            nuke.tprint(f"[NK2DL] Failed to uninstall Qt message handler: {e}")
        except:
            print(f"[NK2DL] Failed to uninstall Qt message handler: {e}")
        
        return False 