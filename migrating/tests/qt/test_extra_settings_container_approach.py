#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Qt test for Extra Settings View container approach in Nuke environment."""

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
    # Import after path setup
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    from nk2dl.gui.panel.views.extra_settings_view import ExtraSettingsView
    
    # Create application
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    
    # Create settings model
    settings_model = SettingsModel()
    
    # Create Extra Settings View
    extra_settings_view = ExtraSettingsView(settings_model)
    
    # Create main window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Extra Settings Container Approach Test")
    window.setGeometry(100, 100, 1200, 800)
    
    # Create central widget with layout
    central_widget = QtWidgets.QWidget()
    window.setCentralWidget(central_widget)
    layout = QtWidgets.QVBoxLayout(central_widget)
    
    # Add debug header
    debug_header = QtWidgets.QLabel("=== Testing Extra Settings View Container Approach ===")
    debug_header.setStyleSheet("background-color: #2d5a2d; color: white; padding: 10px; font-weight: bold;")
    layout.addWidget(debug_header)
    
    # Add status label
    status_label = QtWidgets.QLabel("Layout: Two Columns | Container Approach: Active")
    status_label.setStyleSheet("background-color: #4a4a4a; color: white; padding: 5px;")
    layout.addWidget(status_label)
    
    # Add the Extra Settings View
    layout.addWidget(extra_settings_view)
    
    # Add test content below
    test_content = QtWidgets.QTextEdit()
    test_content.setMaximumHeight(100)
    test_content.setPlainText("Test content below Extra Settings - Line 1\nTest content below Extra Settings - Line 2\nTest content below Extra Settings - Line 3")
    layout.addWidget(test_content)
    
    # Show window
    window.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_window'] = window
    globals()['_extra_settings_view'] = extra_settings_view
    
    print("✓ Extra Settings container approach test window displayed")
    print()
    print("✓ Test ready! Verify the following:")
    print("1. In two-column mode: Columns should have equal heights")
    print("2. Container approach should constrain height to tallest column")
    print("3. Shorter column should distribute groups evenly")
    print("4. No dynamic stretching between groups")
    print("5. Bottom edges should align naturally")
    print("6. Resize the window to test responsive behavior")
    
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if not window.isVisible():
                break
    except KeyboardInterrupt:
        pass
    
    return window

if __name__ == "__main__":
    main() 