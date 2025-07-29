#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for Extra Settings view spacing improvements.

This test verifies that the spacing between sections matches the outer margins (15px)
and that columns are equal height with evenly distributed content.
Run with: & 'C:/Program Files/Nuke15.1v1/Nuke15.1.exe' --tg tests/qt/test_extra_settings_spacing.py
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

def main():
    """Test the Extra Settings view spacing improvements."""
    print("=== Testing Extra Settings View Spacing Improvements ===")
    
    try:
        # Import the ExtraSettingsView and SettingsModel
        from nk2dl.gui.panel.views.extra_settings_view import ExtraSettingsView
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Extra Settings Spacing Test")
        window.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("Extra Settings Spacing Improvements Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test verifies the spacing improvements in the Extra Settings view:\n"
            "✓ 15px spacing between sections (matches outer margins)\n"
            "✓ Equal height columns with evenly distributed content\n"
            "✓ Proper spacing in both two-column and single-column modes\n"
            "✓ Sections align on top and bottom edges"
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 5px 10px; color: #666; font-family: monospace;")
        main_layout.addWidget(description)
        
        # Create control panel
        control_panel = QtWidgets.QHBoxLayout()
        
        # Width info label
        width_label = QtWidgets.QLabel("Window Width: 1400px")
        width_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(width_label)
        
        control_panel.addStretch()
        
        # Layout info label
        layout_label = QtWidgets.QLabel("Layout: Two Columns")
        layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        control_panel.addWidget(layout_label)
        
        # Spacing info label
        spacing_label = QtWidgets.QLabel("Section Spacing: 15px")
        spacing_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        control_panel.addWidget(spacing_label)
        
        main_layout.addLayout(control_panel)
        
        # Create the settings model
        settings_model = SettingsModel()
        
        # Create the extra settings view
        extra_settings_view = ExtraSettingsView(settings_model)
        main_layout.addWidget(extra_settings_view)
        
        # Add some test content below to make it scrollable
        test_content = QtWidgets.QWidget()
        test_layout = QtWidgets.QVBoxLayout(test_content)
        
        for i in range(3):
            label = QtWidgets.QLabel(f"Test content below Extra Settings - Line {i+1}")
            label.setStyleSheet("padding: 20px; background-color: #2a2a2a; margin: 5px; border: 1px solid #555;")
            test_layout.addWidget(label)
        
        main_layout.addWidget(test_content)
        
        # Update info periodically
        def update_info():
            width = window.width()
            width_label.setText(f"Window Width: {width}px")
            
            # Check layout direction
            content_layout = extra_settings_view.content_layout
            if content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                layout_label.setText("Layout: Two Columns")
                layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                layout_label.setText("Layout: One Column")
                layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # Show spacing info
            spacing_label.setText("Section Spacing: 15px (matches outer margins)")
        
        # Update info periodically
        timer = QtCore.QTimer()
        timer.timeout.connect(update_info)
        timer.start(500)  # Update every 500ms
        
        # Show the window
        window.show()
        print("✓ Extra Settings spacing test window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_window'] = window
        globals()['_test_extra_settings'] = extra_settings_view
        
        print("\n✓ Test ready! Verify the following:")
        print("1. Spacing between sections is 15px (matches outer margins)")
        print("2. Left and right columns are equal height")
        print("3. Content is evenly distributed within columns")
        print("4. Sections align on top and bottom edges")
        print("5. Spacing remains consistent when switching to single column mode")
        
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