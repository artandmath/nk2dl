#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug test script for Extra Settings responsive behavior.

This test helps debug why the responsive layout isn't working properly.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_extra_settings_responsive_debug.py
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
    """Debug the responsive Extra Settings view."""
    print("=== Debugging Extra Settings Responsive Behavior ===")
    
    try:
        # Import the ExtraSettingsView and SettingsModel
        from nk2dl.gui.panel.views.extra_settings_view import ExtraSettingsView
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        from nk2dl.gui.panel.constants import Sizes
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Extra Settings Responsive Debug")
        window.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("Extra Settings Responsive Debug")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add debug info
        debug_info = QtWidgets.QLabel(
            f"RESPONSIVE_BREAKPOINT: {Sizes.RESPONSIVE_BREAKPOINT}px\n"
            "Available width = panel_width - 60\n"
            "Breakpoint triggers when available_width < 1250px\n"
            "NEW: Extra Settings now follows Job/Machine settings layout"
        )
        debug_info.setStyleSheet("margin: 5px 10px; color: #666; font-family: monospace;")
        main_layout.addWidget(debug_info)
        
        # Create control panel
        control_panel = QtWidgets.QHBoxLayout()
        
        # Width info label
        width_label = QtWidgets.QLabel("Panel Width: 1400px")
        width_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(width_label)
        
        # Available width label
        available_label = QtWidgets.QLabel("Available Width: 1340px")
        available_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        control_panel.addWidget(available_label)
        
        control_panel.addStretch()
        
        # Layout info label
        layout_label = QtWidgets.QLabel("Layout: Two Columns")
        layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        control_panel.addWidget(layout_label)
        
        # Breakpoint status
        breakpoint_label = QtWidgets.QLabel("Breakpoint: Above")
        breakpoint_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(breakpoint_label)
        
        main_layout.addLayout(control_panel)
        
        # Create the settings model
        settings_model = SettingsModel()
        
        # Create the extra settings view
        extra_settings_view = ExtraSettingsView(settings_model)
        main_layout.addWidget(extra_settings_view)
        
        # Add some test content below
        test_content = QtWidgets.QWidget()
        test_layout = QtWidgets.QVBoxLayout(test_content)
        
        for i in range(2):
            label = QtWidgets.QLabel(f"Test content below Extra Settings - Line {i+1}")
            label.setStyleSheet("padding: 20px; background-color: #2a2a2a; margin: 5px; border: 1px solid #555;")
            test_layout.addWidget(label)
        
        main_layout.addWidget(test_content)
        
        # Update debug info periodically
        def update_debug_info():
            panel_width = window.width()
            available_width = panel_width - 60
            
            width_label.setText(f"Panel Width: {panel_width}px")
            available_label.setText(f"Available Width: {available_width}px")
            
            # Check layout direction
            content_layout = extra_settings_view.content_layout
            if content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                layout_label.setText("Layout: Two Columns")
                layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                layout_label.setText("Layout: One Column")
                layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # Check breakpoint status
            if available_width < Sizes.RESPONSIVE_BREAKPOINT:
                breakpoint_label.setText("Breakpoint: Below")
                breakpoint_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                breakpoint_label.setText("Breakpoint: Above")
                breakpoint_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Update info periodically
        timer = QtCore.QTimer()
        timer.timeout.connect(update_debug_info)
        timer.start(100)  # Update every 100ms for more responsive debugging
        
        # Show the window
        window.show()
        print("✓ Debug window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_debug_window'] = window
        globals()['_debug_extra_settings'] = extra_settings_view
        
        print("\n✓ Debug ready! Try the following:")
        print("1. Resize the window horizontally")
        print("2. Watch the debug info update in real-time")
        print("3. The breakpoint should trigger at 1310px panel width (1250 + 60)")
        print("4. Check if the layout direction changes when crossing the breakpoint")
        print("5. NEW: Extra Settings should now follow Job/Machine settings layout changes")
        
        # Keep the window alive
        try:
            while True:
                QtWidgets.QApplication.processEvents()
                time.sleep(0.001)
                if not window.isVisible():
                    break
        except KeyboardInterrupt:
            print("\nDebug interrupted by user")
        
        return window
        
    except Exception as e:
        print(f"✗ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 