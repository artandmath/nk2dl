#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Qt test for console output capture in Nuke environment."""

import sys
import os
import time
import logging
import threading
from queue import Queue

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui

class ConsoleWidgetSignals(QtCore.QObject):
    """Qt signals for thread-safe console updates."""
    log_message = QtCore.Signal(str, str)  # message, level

class ConsoleWidget(QtWidgets.QWidget):
    """Test widget that captures and displays console output."""
    
    def __init__(self):
        super().__init__()
        self.signals = ConsoleWidgetSignals()
        self.signals.log_message.connect(self._on_log_message)
        self.setupUI()
        self.setupLogging()
        
    def setupUI(self):
        """Set up the UI."""
        self.setWindowTitle("Console Output Capture Test")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Title
        title = QtWidgets.QLabel("Console Output Capture Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #555;
            }
        """)
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)
        
        # Test buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.test_logging_btn = QtWidgets.QPushButton("Test Logging")
        self.test_logging_btn.clicked.connect(self.test_logging)
        button_layout.addWidget(self.test_logging_btn)
        
        self.test_threading_btn = QtWidgets.QPushButton("Test Threading")
        self.test_threading_btn.clicked.connect(self.test_threading)
        button_layout.addWidget(self.test_threading_btn)
        
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self.console_output.clear)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def setupLogging(self):
        """Set up logging to capture console output."""
        # Create custom handler
        self.log_handler = ConsoleLogHandler(self.signals)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Add to both root logger and nk2dl logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG)
        
        nk2dl_logger = logging.getLogger('nk2dl')
        nk2dl_logger.addHandler(self.log_handler)
        nk2dl_logger.setLevel(logging.DEBUG)
        
        # Add to test logger
        self.test_logger = logging.getLogger('test')
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        print("=== Console Logging Setup Complete ===")
        
    @QtCore.Slot(str, str)
    def _on_log_message(self, message, level):
        """Handle log messages from any thread."""
        color_map = {
            'debug': '#888888',
            'info': '#ffffff',
            'warning': '#ffaa00',
            'error': '#ff4444',
            'critical': '#ff0000'
        }
        
        color = color_map.get(level.lower(), '#ffffff')
        
        # Format message with color
        formatted_msg = f'<span style="color: {color};">{message}</span>'
        
        # Append to console
        self.console_output.append(formatted_msg)
        
        # Auto-scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Force update
        QtWidgets.QApplication.processEvents()
        
    def test_logging(self):
        """Test basic logging functionality."""
        print("=== Testing Basic Logging ===")
        
        self.test_logger.debug("This is a debug message")
        self.test_logger.info("This is an info message")
        self.test_logger.warning("This is a warning message")
        self.test_logger.error("This is an error message")
        self.test_logger.critical("This is a critical message")
        
        # Test with different loggers
        logging.info("Root logger info message")
        logging.warning("Root logger warning message")
        
        nk2dl_logger = logging.getLogger('nk2dl')
        nk2dl_logger.info("nk2dl logger info message")
        nk2dl_logger.error("nk2dl logger error message")
        
        print("=== Basic Logging Test Complete ===")
        
    def test_threading(self):
        """Test threaded logging."""
        print("=== Testing Threaded Logging ===")
        
        def worker_function():
            """Worker function that generates log messages."""
            worker_logger = logging.getLogger('worker')
            
            for i in range(5):
                worker_logger.info(f"Worker thread message {i+1}")
                time.sleep(0.5)
                
            worker_logger.info("Worker thread completed")
            
        # Start worker thread
        worker_thread = threading.Thread(target=worker_function)
        worker_thread.daemon = True
        worker_thread.start()
        
        print("=== Threaded Logging Test Started ===")

class ConsoleLogHandler(logging.Handler):
    """Custom logging handler that emits Qt signals."""
    
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        
    def emit(self, record):
        """Emit log records as Qt signals."""
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            self.signals.log_message.emit(msg, level)
        except Exception as e:
            print(f"Error in ConsoleLogHandler: {e}")

def main():
    """Main test function."""
    print("Starting Console Capture Test...")
    
    # Create and show widget
    widget = ConsoleWidget()
    widget.show()
    
    # Prevent garbage collection
    globals()['_test_widget'] = widget
    
    print("Widget created and shown")
    
    try:
        # Keep alive for Nuke terminal mode
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if not widget.isVisible():
                break
    except KeyboardInterrupt:
        print("Test interrupted by user")
    
    print("Test completed")
    return widget

if __name__ == "__main__":
    main() 