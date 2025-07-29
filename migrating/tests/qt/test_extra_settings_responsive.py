#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for responsive Extra Settings view.

This test verifies that the Extra Settings view switches between two columns and one column
based on the available width, just like the Job and Machine settings.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_extra_settings_responsive.py
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
    """Test the responsive Extra Settings view."""
    print("=== Testing Responsive Extra Settings View ===")
    
    try:
        # Import the ExtraSettingsView and SettingsModel
        from nk2dl.gui.panel.views.extra_settings_view import ExtraSettingsView
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Responsive Extra Settings Test")
        window.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("Responsive Extra Settings Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test demonstrates responsive layout in the Extra Settings view. "
            "Resize the window horizontally to see the layout switch between two columns and one column. "
            "The breakpoint is set to 1250px width (same as Job/Machine settings). "
            "Note: Group box containers have been removed - only spacing remains between columns."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 5px 10px; color: #666;")
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
        
        # Update width and layout info periodically
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
        
        # Update info periodically
        timer = QtCore.QTimer()
        timer.timeout.connect(update_info)
        timer.start(500)  # Update every 500ms
        
        # Show the window
        window.show()
        print("✓ Responsive Extra Settings test window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_window'] = window
        globals()['_test_extra_settings'] = extra_settings_view
        
        print("\n✓ Test ready! Try the following:")
        print("1. Resize the window horizontally to see responsive behavior")
        print("2. Watch the layout info label change between 'Two Columns' and 'One Column'")
        print("3. The breakpoint is at 1250px width (same as Job/Machine settings)")
        print("4. Group box containers removed - only spacing between columns")
        print("5. All Extra Settings sections are now organized in two columns when wide")
        
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