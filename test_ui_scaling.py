#!/usr/bin/env python3
"""Test script to verify UI scaling functionality."""

import sys
import os

# Add the nk2dl package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nk2dl'))

try:
    from PySide6 import QtWidgets, QtCore
    PYSIDE_VERSION = "PySide6"
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
        PYSIDE_VERSION = "PySide2"
    except ImportError:
        print("Error: Neither PySide6 nor PySide2 is available")
        sys.exit(1)

from nk2dl.gui.panel.views.console_view import ConsoleView
from nk2dl.gui.panel.constants import Fonts


def test_ui_scaling():
    """Test the UI scaling functionality."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Create a test window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("UI Scaling Test")
    window.resize(800, 600)
    
    # Create console view
    console_view = ConsoleView()
    window.setCentralWidget(console_view)
    
    # Test font size (no scaling applied)
    font_size = Fonts.CONSOLE_FONT_SIZE
    print(f"Font size: {font_size}pt (no scaling applied)")
    
    # Add some test messages
    console_view.log_info("Testing UI scaling functionality")
    console_view.log_warning("This is a warning message")
    console_view.log_error("This is an error message")
    console_view.log_success("This is a success message")
    
    # Show the window
    window.show()
    
    print(f"\nWindow displayed with {PYSIDE_VERSION}")
    print("Check if the console text is properly sized for your display")
    print("Press Ctrl+C to exit")
    
    # Run the application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    test_ui_scaling() 