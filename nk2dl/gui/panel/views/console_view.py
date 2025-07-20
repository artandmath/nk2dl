# -*- coding: utf-8 -*-
"""Console view for the nk2dl panel.

This module contains the ConsoleView class for displaying console output,
logs, and submission status information.
"""

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from ..constants import Colors, Fonts


class ConsoleView(QtWidgets.QWidget):
    """View for console output and logging.
    
    This view handles the UI for displaying console output, logs,
    and submission status information.
    """
    
    # Qt signals for thread-safe logging
    log_info_signal = QtCore.Signal(str)
    log_warning_signal = QtCore.Signal(str)
    log_error_signal = QtCore.Signal(str)
    log_success_signal = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create the main layout and UI components
        self._create_ui()
        
        # Connect signals to slots for thread-safe updates
        self.log_info_signal.connect(self._log_info_slot)
        self.log_warning_signal.connect(self._log_warning_slot)
        self.log_error_signal.connect(self._log_error_slot)
        self.log_success_signal.connect(self._log_success_slot)
    
    def _create_ui(self):
        """Create the console UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        
        # Use base font size directly without scaling
        font_size = Fonts.CONSOLE_FONT_SIZE
        
        self.console_output.setStyleSheet(
            f"background-color: {Colors.CONSOLE_BACKGROUND}; "
            f"color: {Colors.CONSOLE_TEXT}; "
            f"font-family: {Fonts.CONSOLE_FONT_FAMILY}; "
            f"font-size: {font_size}pt;"
        )
        
        # Set initial content
        self._set_initial_content()
        
        layout.addWidget(self.console_output)
    

    
    def _set_initial_content(self):
        """Set initial console content."""
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        initial_text = f"""Ready for submission...
Latest submission: {current_time}

NK2DL Panel Status:
- Models: Initialized ✓
- Views: Loaded ✓
- Delegates: Active ✓
- Widgets: Ready ✓

Waiting for user input..."""
        
        self.console_output.setText(initial_text)
    
    def append_message(self, message, message_type="info"):
        """Append a message to the console.
        
        Args:
            message (str): Message to append
            message_type (str): Type of message ("info", "warning", "error", "success")
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message type - using constants
        color_map = {
            "info": Colors.CONSOLE_INFO,
            "warning": Colors.CONSOLE_WARNING,
            "error": Colors.CONSOLE_ERROR,
            "success": Colors.CONSOLE_SUCCESS
        }
        
        color = color_map.get(message_type, Colors.CONSOLE_INFO)
        
        # Format the message with timestamp and color
        formatted_message = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        
        # Append to console
        self.console_output.append(formatted_message)
        
        # Auto-scroll to bottom and process events to ensure immediate display
        self._auto_scroll_to_bottom()
        
        # Force immediate widget update for real-time display
        QtWidgets.QApplication.processEvents()
    
    def _auto_scroll_to_bottom(self):
        """Ensure console auto-scrolls to show the latest messages."""
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_console(self):
        """Clear the console output."""
        self.console_output.clear()
        self._set_initial_content()
    
    def log_info(self, message):
        """Log an info message.
        
        Args:
            message (str): Info message
        """
        self.append_message(message, "info")
    
    def log_warning(self, message):
        """Log a warning message.
        
        Args:
            message (str): Warning message
        """
        self.append_message(message, "warning")
    
    def log_error(self, message):
        """Log an error message.
        
        Args:
            message (str): Error message
        """
        self.append_message(message, "error")
    
    def log_success(self, message):
        """Log a success message.
        
        Args:
            message (str): Success message
        """
        self.append_message(message, "success")
    
    def get_console_text(self):
        """Get the current console text.
        
        Returns:
            str: Current console content
        """
        return self.console_output.toPlainText()
    
    def set_console_text(self, text):
        """Set the console text.
        
        Args:
            text (str): Text to set
        """
        self.console_output.setPlainText(text)
    
    # Thread-safe slot methods for Qt signals
    def _log_info_slot(self, message):
        """Thread-safe slot for info messages."""
        self.log_info(message)
    
    def _log_warning_slot(self, message):
        """Thread-safe slot for warning messages."""
        self.log_warning(message)
    
    def _log_error_slot(self, message):
        """Thread-safe slot for error messages."""
        self.log_error(message)
    
    def _log_success_slot(self, message):
        """Thread-safe slot for success messages."""
        self.log_success(message) 