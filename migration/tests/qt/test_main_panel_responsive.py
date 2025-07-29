#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for main panel responsive behavior.

This test verifies that the Extra Settings view follows the Job/Machine settings
responsive layout changes through the main panel's signal system.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_main_panel_responsive.py
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
    """Test the main panel responsive behavior."""
    print("=== Testing Main Panel Responsive Behavior ===")
    
    try:
        # Import the main panel
        from nk2dl.gui.panel import Nk2dlPanel
        from nk2dl.gui.panel.constants import Sizes
        
        # Create main window
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Main Panel Responsive Test")
        window.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        window.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add title
        title = QtWidgets.QLabel("Main Panel Responsive Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test demonstrates the new responsive behavior where Extra Settings "
            "follows Job/Machine settings layout changes through the main panel's signal system. "
            "Resize the window horizontally to see both sections change layout simultaneously."
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
        
        # Available width label
        available_label = QtWidgets.QLabel("Available Width: 1340px")
        available_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        control_panel.addWidget(available_label)
        
        control_panel.addStretch()
        
        # Settings layout info label
        settings_layout_label = QtWidgets.QLabel("Job/Machine: Two Columns")
        settings_layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(settings_layout_label)
        
        # Extra settings layout info label
        extra_layout_label = QtWidgets.QLabel("Extra Settings: Two Columns")
        extra_layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(extra_layout_label)
        
        # Breakpoint status
        breakpoint_label = QtWidgets.QLabel("Breakpoint: Above")
        breakpoint_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        control_panel.addWidget(breakpoint_label)
        
        main_layout.addLayout(control_panel)
        
        # Create the main panel
        panel = Nk2dlPanel()
        main_layout.addWidget(panel)
        
        # Update debug info periodically
        def update_debug_info():
            panel_width = window.width()
            available_width = panel_width - 60
            
            width_label.setText(f"Window Width: {panel_width}px")
            available_label.setText(f"Available Width: {available_width}px")
            
            # Check Job/Machine settings layout direction
            settings_content_layout = panel.settings_view.content_layout
            if settings_content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                settings_layout_label.setText("Job/Machine: Two Columns")
                settings_layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                settings_layout_label.setText("Job/Machine: One Column")
                settings_layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # Check Extra Settings layout direction
            extra_content_layout = panel.extra_settings_view.content_layout
            if extra_content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                extra_layout_label.setText("Extra Settings: Two Columns")
                extra_layout_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                extra_layout_label.setText("Extra Settings: One Column")
                extra_layout_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
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
        timer.start(100)  # Update every 100ms for responsive debugging
        
        # Show the window
        window.show()
        print("✓ Main panel test window displayed")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_window'] = window
        globals()['_test_panel'] = panel
        
        print("\n✓ Test ready! Try the following:")
        print("1. Resize the window horizontally")
        print("2. Watch both Job/Machine and Extra Settings layout info update")
        print("3. Both sections should change layout simultaneously")
        print("4. The breakpoint should trigger at 1310px panel width (1250 + 60)")
        print("5. Switch to 'Extra Settings' tab to see the responsive behavior")
        
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