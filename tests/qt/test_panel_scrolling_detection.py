#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for panel scrolling detection in ScrollableTabWidget.

This test verifies that the tab widget can detect when it's in a scrollable panel
and automatically enables tab content scrolling.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_panel_scrolling_detection.py
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
    for i in range(30):
        label = QtWidgets.QLabel(f"Test content line {i+1} - This is a long line to test horizontal scrolling as well")
        label.setStyleSheet("padding: 10px; border: 1px solid #555; margin: 2px;")
        layout.addWidget(label)
    
    # Add some controls
    for i in range(10):
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(f"Control {i+1}:"))
        row.addWidget(QtWidgets.QLineEdit(f"Value {i+1}"))
        row.addWidget(QtWidgets.QPushButton(f"Button {i+1}"))
        layout.addLayout(row)
    
    layout.addStretch()
    return widget

def main():
    """Test the ScrollableTabWidget with panel scrolling detection."""
    print("=== Testing Panel Scrolling Detection ===")
    
    try:
        # Import the ScrollableTabWidget
        from nk2dl.gui.panel.widgets.misc_widgets import ScrollableTabWidget
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Panel Scrolling Detection Test")
        window.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("Panel Scrolling Detection Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test demonstrates automatic scrolling detection in tab widgets. "
            "The tab widget should automatically detect when it's in a scrollable panel "
            "and enable internal scrolling for tab content."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 5px 10px; color: #666;")
        main_layout.addWidget(description)
        
        # Create control panel
        control_panel = QtWidgets.QHBoxLayout()
        
        # Force enable/disable buttons
        force_enable_btn = QtWidgets.QPushButton("Force Enable Scrolling")
        force_enable_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        control_panel.addWidget(force_enable_btn)
        
        force_disable_btn = QtWidgets.QPushButton("Force Disable Scrolling")
        force_disable_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        control_panel.addWidget(force_disable_btn)
        
        control_panel.addStretch()
        
        # Status label
        status_label = QtWidgets.QLabel("Status: Ready")
        status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(status_label)
        
        main_layout.addLayout(control_panel)
        
        # Create a scroll area to simulate Nuke's panel system
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        # Create content widget for scroll area
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        
        # Add some content above the tab widget to make it scrollable
        for i in range(5):
            label = QtWidgets.QLabel(f"Content above tab widget - Line {i+1}")
            label.setStyleSheet("padding: 20px; background-color: #2a2a2a; margin: 5px; border: 1px solid #555;")
            scroll_layout.addWidget(label)
        
        # Create the scrollable tab widget
        tab_widget = ScrollableTabWidget()
        scroll_layout.addWidget(tab_widget)
        
        # Add some content below the tab widget
        for i in range(5):
            label = QtWidgets.QLabel(f"Content below tab widget - Line {i+1}")
            label.setStyleSheet("padding: 20px; background-color: #2a2a2a; margin: 5px; border: 1px solid #555;")
            scroll_layout.addWidget(label)
        
        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Add test tabs
        tab_widget.addTab(create_test_content(), "Long Content Tab 1")
        tab_widget.addTab(create_test_content(), "Long Content Tab 2")
        tab_widget.addTab(create_test_content(), "Long Content Tab 3")
        
        # Add a simple tab for comparison
        simple_widget = QtWidgets.QWidget()
        simple_layout = QtWidgets.QVBoxLayout(simple_widget)
        simple_layout.addWidget(QtWidgets.QLabel("Simple content - no scrolling needed"))
        simple_layout.addWidget(QtWidgets.QPushButton("Test Button"))
        tab_widget.addTab(simple_widget, "Simple Tab")
        
        # Connect controls
        def update_status():
            is_scrolling = tab_widget.is_scrolling_enabled()
            current_height = tab_widget.height()
            threshold = tab_widget._scroll_threshold
            in_scrollable_panel = tab_widget._is_in_scrollable_panel()
            
            status_text = f"Scrolling: {'ENABLED' if is_scrolling else 'DISABLED'} | "
            status_text += f"Height: {current_height}px | "
            status_text += f"Threshold: {threshold}px | "
            status_text += f"In Scrollable Panel: {'YES' if in_scrollable_panel else 'NO'}"
            
            if is_scrolling:
                status_label.setText(status_text)
                status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                status_label.setText(status_text)
                status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        def on_force_enable():
            tab_widget.force_enable_scrolling()
            update_status()
        
        def on_force_disable():
            tab_widget.force_disable_scrolling()
            update_status()
        
        force_enable_btn.clicked.connect(on_force_enable)
        force_disable_btn.clicked.connect(on_force_disable)
        
        # Update status periodically
        timer = QtCore.QTimer()
        timer.timeout.connect(update_status)
        timer.start(1000)  # Update every second
        
        # Show the window
        window.show()
        print("✓ Panel scrolling detection test window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_window'] = window
        globals()['_test_tab_widget'] = tab_widget
        globals()['_test_scroll_area'] = scroll_area
        
        print("\n✓ Test ready! Try the following:")
        print("1. Resize the window to see if scrolling detection works")
        print("2. Use the Force Enable/Disable buttons to test manual control")
        print("3. Check the status label for current scrolling state")
        print("4. Switch between tabs to see scrolling behavior")
        print("5. The scroll area simulates Nuke's panel system")
        
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