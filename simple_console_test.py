#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple console capture test for Nuke."""

import sys
import os
import time
import logging

# Direct path to nk2dl for testing
nk2dl_path = "C:/Users/Daniel/Documents/repo/nk2dl/"
sys.path.insert(0, nk2dl_path)

# Nuke-compatible imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui

class SimpleConsoleTest(QtWidgets.QWidget):
    """Simple test widget for console capture."""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setupLogging()
        
    def setupUI(self):
        """Set up basic UI."""
        self.setWindowTitle("Simple Console Test")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Console area
        self.console = QtWidgets.QTextEdit()
        self.console.setStyleSheet("background-color: black; color: white; font-family: monospace;")
        layout.addWidget(self.console)
        
        # Test button
        self.test_btn = QtWidgets.QPushButton("Test Logging")
        self.test_btn.clicked.connect(self.run_test)
        layout.addWidget(self.test_btn)
        
        self.setLayout(layout)
        
    def setupLogging(self):
        """Set up logging capture."""
        # Create handler that writes to console widget
        self.handler = ConsoleHandler(self.console)
        
        # Add to loggers
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.DEBUG)
        
        logging.getLogger('nk2dl').addHandler(self.handler)
        logging.getLogger('nk2dl').setLevel(logging.DEBUG)
        
        # Initial message
        self.console.append("=== Logging setup complete ===")
        
    def run_test(self):
        """Run logging test."""
        self.console.append("=== Starting test ===")
        
        # Test print statements
        print("This is a print statement")
        
        # Test logging
        logging.info("This is a logging.info message")
        logging.warning("This is a logging.warning message")
        logging.error("This is a logging.error message")
        
        # Test nk2dl logger
        nk2dl_logger = logging.getLogger('nk2dl')
        nk2dl_logger.info("This is nk2dl logger info")
        nk2dl_logger.error("This is nk2dl logger error")
        
        self.console.append("=== Test complete ===")

class ConsoleHandler(logging.Handler):
    """Simple logging handler that writes to QTextEdit."""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        """Emit log record to text widget."""
        try:
            msg = self.format(record)
            self.text_widget.append(f"[{record.levelname}] {msg}")
        except:
            pass

def main():
    """Main function."""
    print("Starting simple console test...")
    
    # Create widget
    widget = SimpleConsoleTest()
    widget.show()
    
    # Prevent garbage collection
    globals()['_test_widget'] = widget
    
    print("Widget should be visible now")
    
    # Keep alive
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.01)
            if not widget.isVisible():
                break
    except KeyboardInterrupt:
        print("Interrupted")
    
    return widget

if __name__ == "__main__":
    main() 