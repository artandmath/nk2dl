#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Qt test for Extra Settings View height balancing in Nuke environment."""

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
    
    # Create main window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Extra Settings Height Balancing Test")
    window.resize(1400, 800)
    
    # Create central widget
    central_widget = QtWidgets.QWidget()
    window.setCentralWidget(central_widget)
    
    # Create main layout
    main_layout = QtWidgets.QVBoxLayout(central_widget)
    
    # Create header with info
    header_label = QtWidgets.QLabel("=== Testing Extra Settings View Height Balancing ===")
    header_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
    main_layout.addWidget(header_label)
    
    # Create status display
    status_label = QtWidgets.QLabel("Initializing...")
    status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12px;")
    main_layout.addWidget(status_label)
    
    # Create height info display
    height_info_label = QtWidgets.QLabel("Column Heights: Measuring...")
    height_info_label.setStyleSheet("color: cyan; font-weight: bold; font-size: 11px;")
    main_layout.addWidget(height_info_label)
    
    # Create extra settings view
    extra_settings_view = ExtraSettingsView(settings_model)
    main_layout.addWidget(extra_settings_view)
    
    # Add test content below
    test_label = QtWidgets.QLabel("Test content below Extra Settings - Line 1")
    test_label.setStyleSheet("color: white; font-size: 10px;")
    main_layout.addWidget(test_label)
    
    test_label2 = QtWidgets.QLabel("Test content below Extra Settings - Line 2")
    test_label2.setStyleSheet("color: white; font-size: 10px;")
    main_layout.addWidget(test_label2)
    
    test_label3 = QtWidgets.QLabel("Test content below Extra Settings - Line 3")
    test_label3.setStyleSheet("color: white; font-size: 10px;")
    main_layout.addWidget(test_label3)
    
    # Function to update height measurements
    def update_height_measurements():
        try:
            # Get the content layout
            content_layout = extra_settings_view.content_layout
            
            # Check if we're in two-column mode
            is_two_columns = content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight
            
            # Update status
            if is_two_columns:
                status_label.setText("Layout: Two Columns | Height Balancing: Active")
                status_label.setStyleSheet("color: green; font-weight: bold; font-size: 12px;")
            else:
                status_label.setText("Layout: Single Column | Height Balancing: Inactive")
                status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12px;")
            
            # Measure column heights
            if is_two_columns and hasattr(extra_settings_view, 'left_groups') and hasattr(extra_settings_view, 'right_groups'):
                # Calculate content heights
                left_content_height = extra_settings_view._calculate_column_content_height(extra_settings_view.left_groups)
                right_content_height = extra_settings_view._calculate_column_content_height(extra_settings_view.right_groups)
                
                # Get actual column heights
                left_column_height = extra_settings_view.left_layout.parentWidget().height() if extra_settings_view.left_layout.parentWidget() else 0
                right_column_height = extra_settings_view.right_layout.parentWidget().height() if extra_settings_view.right_layout.parentWidget() else 0
                
                # Get max height
                max_height = max(left_column_height, right_column_height)
                
                height_info = f"Column Heights: L={left_content_height}px (col:{left_column_height}px), R={right_content_height}px (col:{right_column_height}px), Max={max_height}px"
                height_info_label.setText(height_info)
                height_info_label.setStyleSheet("color: cyan; font-weight: bold; font-size: 11px;")
            else:
                height_info_label.setText("Column Heights: Single column mode - no balancing needed")
                height_info_label.setStyleSheet("color: orange; font-weight: bold; font-size: 11px;")
                
        except Exception as e:
            height_info_label.setText(f"Error measuring heights: {str(e)}")
            height_info_label.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
    
    # Create timer for continuous measurement
    measurement_timer = QtCore.QTimer()
    measurement_timer.timeout.connect(update_height_measurements)
    measurement_timer.start(500)  # Update every 500ms
    
    # Initial measurement
    QtCore.QTimer.singleShot(100, update_height_measurements)
    
    # Show window
    window.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_widget'] = window
    globals()['_extra_settings_view'] = extra_settings_view
    
    print("✓ Extra Settings height balancing test window displayed")
    print("\n✓ Test ready! Verify the following:")
    print("1. In two-column mode: Columns should have equal heights")
    print("2. Height balancing info should show 'Active' in two-column mode")
    print("3. Column heights should be displayed and balanced")
    print("4. In single-column mode: Height balancing should be 'Inactive'")
    print("5. Groups should be evenly distributed in both modes")
    print("6. Resize the window to test responsive behavior")
    print("7. Height measurements update every 500ms - resize window to see changes")
    
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