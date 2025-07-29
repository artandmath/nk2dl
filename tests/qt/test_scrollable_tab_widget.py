#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for ScrollableTabWidget functionality.

This test verifies that the tab widget automatically enables scrolling when height is limited.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_scrollable_tab_widget.py
"""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui

def create_test_content():
    """Create test content for tabs."""
    # Create a widget with lots of content to test scrolling
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(widget)
    
    # Add many labels to make content tall
    for i in range(20):
        label = QtWidgets.QLabel(f"Test content line {i+1} - This is a long line to test horizontal scrolling as well")
        label.setStyleSheet("padding: 10px; border: 1px solid #555; margin: 2px;")
        layout.addWidget(label)
    
    # Add some controls
    for i in range(5):
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(f"Control {i+1}:"))
        row.addWidget(QtWidgets.QLineEdit(f"Value {i+1}"))
        row.addWidget(QtWidgets.QPushButton(f"Button {i+1}"))
        layout.addLayout(row)
    
    layout.addStretch()
    return widget

def main():
    """Test the ScrollableTabWidget with various content."""
    print("=== Testing ScrollableTabWidget ===")
    
    try:
        # Import the ScrollableTabWidget
        from nk2dl.gui.panel.widgets.misc_widgets import ScrollableTabWidget
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("ScrollableTabWidget Test")
        window.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("ScrollableTabWidget Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test demonstrates automatic scrolling in tab widgets. "
            "Resize the window vertically to see scrolling enable/disable automatically. "
            "The threshold is set to 400px height."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 5px 10px; color: #666;")
        main_layout.addWidget(description)
        
        # Create control panel
        control_panel = QtWidgets.QHBoxLayout()
        
        # Height threshold control
        control_panel.addWidget(QtWidgets.QLabel("Scroll Threshold:"))
        threshold_spin = QtWidgets.QSpinBox()
        threshold_spin.setRange(200, 800)
        threshold_spin.setValue(400)
        threshold_spin.setSuffix(" px")
        control_panel.addWidget(threshold_spin)
        
        # Min height control
        control_panel.addWidget(QtWidgets.QLabel("Min Height:"))
        min_height_spin = QtWidgets.QSpinBox()
        min_height_spin.setRange(200, 600)
        min_height_spin.setValue(350)
        min_height_spin.setSuffix(" px")
        control_panel.addWidget(min_height_spin)
        
        control_panel.addStretch()
        
        # Status label
        status_label = QtWidgets.QLabel("Status: Ready")
        status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(status_label)
        
        main_layout.addLayout(control_panel)
        
        # Create the scrollable tab widget
        tab_widget = ScrollableTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Add test tabs
        tab_widget.addTab(create_test_content(), "Long Content Tab")
        tab_widget.addTab(create_test_content(), "Another Long Tab")
        tab_widget.addTab(create_test_content(), "Third Long Tab")
        
        # Add a simple tab for comparison
        simple_widget = QtWidgets.QWidget()
        simple_layout = QtWidgets.QVBoxLayout(simple_widget)
        simple_layout.addWidget(QtWidgets.QLabel("Simple content - no scrolling needed"))
        simple_layout.addWidget(QtWidgets.QPushButton("Test Button"))
        tab_widget.addTab(simple_widget, "Simple Tab")
        
        # Connect controls
        def update_threshold():
            tab_widget.set_scroll_threshold(threshold_spin.value())
            update_status()
        
        def update_min_height():
            tab_widget.set_content_min_height(min_height_spin.value())
            update_status()
        
        def update_status():
            is_scrolling = tab_widget.is_scrolling_enabled()
            current_height = tab_widget.height()
            threshold = tab_widget._scroll_threshold
            
            if is_scrolling:
                status_label.setText(f"Status: Scrolling ENABLED (Height: {current_height}px < {threshold}px)")
                status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                status_label.setText(f"Status: Scrolling DISABLED (Height: {current_height}px >= {threshold}px)")
                status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        threshold_spin.valueChanged.connect(update_threshold)
        min_height_spin.valueChanged.connect(update_min_height)
        
        # Update status periodically
        timer = QtCore.QTimer()
        timer.timeout.connect(update_status)
        timer.start(500)  # Update every 500ms
        
        # Show the window
        window.show()
        print("✓ ScrollableTabWidget test window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_window'] = window
        globals()['_test_tab_widget'] = tab_widget
        
        print("\n✓ Test ready! Try the following:")
        print("1. Resize the window vertically to see scrolling enable/disable")
        print("2. Adjust the scroll threshold and min height controls")
        print("3. Switch between tabs to see scrolling behavior")
        print("4. Check the status label for current scrolling state")
        
        # Keep the window alive
        try:
            while True:
                QtWidgets.QApplication.processEvents()
                time.sleep(0.001)
                if not window.isVisible():
                    break
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        
        return window
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 