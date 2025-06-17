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


class ConsoleView(QtWidgets.QWidget):
    """View for console output and logging.
    
    This view handles the UI for displaying console output, logs,
    and submission status information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create the main layout and UI components
        self._create_ui()
    
    def _create_ui(self):
        """Create the console UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet(
            "background-color: #2b2b2b; "
            "color: #ffffff; "
            "font-family: 'Courier New', monospace; "
            "font-size: 10pt;"
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
        
        # Color coding based on message type
        color_map = {
            "info": "#ffffff",      # White
            "warning": "#ffaa00",   # Orange
            "error": "#ff4444",     # Red
            "success": "#44ff44"    # Green
        }
        
        color = color_map.get(message_type, "#ffffff")
        
        # Format the message with timestamp and color
        formatted_message = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        
        # Append to console
        self.console_output.append(formatted_message)
        
        # Auto-scroll to bottom
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