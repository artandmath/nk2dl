#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal test to debug frozen table synchronization issues."""

import sys
import os
import time

# Path setup for Nuke testing - be very direct as suggested in @pyside rule
nk2dl_path = "C:/Users/Daniel/Documents/repo/nk2dl"
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide6"
else:
    from PySide2 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide2"

# Direct imports to avoid relative import issues
from nk2dl.gui.panel.widgets import FrozenTableWidget, CustomHeaderView
from nk2dl.gui.panel.constants import TableColumns

def test_synchronization_debug():
    """Test frozen table synchronization with debug output."""
    print(f"=== Frozen Table Synchronization Debug Test - {PYSIDE_VERSION} ===")
    
    # Create a simple window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Sync Debug Test")
    window.setGeometry(100, 100, 1000, 600)
    
    # Create central widget
    central_widget = QtWidgets.QWidget()
    window.setCentralWidget(central_widget)
    layout = QtWidgets.QVBoxLayout(central_widget)
    
    # Add debug info label
    info_label = QtWidgets.QLabel("Testing frozen table synchronization...")
    layout.addWidget(info_label)
    
    # Create frozen table with the same setup as nk2dl panel
    table = FrozenTableWidget()
    layout.addWidget(table)
    
    # Set up headers exactly like in the panel
    headers = TableColumns.HEADERS
    display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(display_headers)
    
    print(f"Table columns: {len(headers)}")
    print(f"Frozen columns: {table.frozen_column_count}")
    print(f"Headers: {headers[:5]}...")  # First 5 headers
    
    # Apply custom headers like in the panel
    custom_header = CustomHeaderView(QtCore.Qt.Horizontal, table)
    table.setHorizontalHeader(custom_header)
    
    if hasattr(table, 'frozen_table'):
        frozen_custom_header = CustomHeaderView(QtCore.Qt.Horizontal, table.frozen_table)
        table.frozen_table.setHorizontalHeader(frozen_custom_header)
        
        print("🔄 Reconnecting frozen signals...")
        table.reconnect_frozen_signals()
        print("✅ Frozen signals reconnected")
        
        # Debug: Check column widths before and after
        print("\n=== Column Width Debug ===")
        for col in range(min(5, table.columnCount())):
            main_width = table.columnWidth(col)
            frozen_width = table.frozen_table.columnWidth(col)
            sync_status = "✅" if main_width == frozen_width else "❌"
            print(f"Column {col} ({headers[col]}): Main={main_width}, Frozen={frozen_width} {sync_status}")
    
    # Add some test data (minimal)
    test_data = [
        ["1", "Write1", "output1.%04d.exr", "50", "1", "1001-1100"],
        ["2", "Write2", "output2.%04d.exr", "75", "5", "1001-1200"],
        ["3", "Write3", "output3.%04d.exr", "25", "2", "1001-1300"],
    ]
    
    table.setRowCount(len(test_data))
    for row, row_data in enumerate(test_data):
        for col, value in enumerate(row_data):
            if col < len(headers):  # Safety check
                item = QtWidgets.QTableWidgetItem(str(value))
                table.setItem(row, col, item)
    
    # Resize columns to content
    table.resizeColumnsToContents()
    
    # Debug: Check column widths after resize
    print("\n=== Column Width After Resize ===")
    if hasattr(table, 'frozen_table'):
        for col in range(min(5, table.columnCount())):
            main_width = table.columnWidth(col)
            frozen_width = table.frozen_table.columnWidth(col)
            sync_status = "✅" if main_width == frozen_width else "❌"
            print(f"Column {col} ({headers[col]}): Main={main_width}, Frozen={frozen_width} {sync_status}")
    
    # Add test buttons
    button_layout = QtWidgets.QHBoxLayout()
    
    test_resize_btn = QtWidgets.QPushButton("Test Resize Sync")
    def test_resize():
        print("\n=== Testing Manual Resize ===")
        original_width = table.columnWidth(0)
        new_width = original_width + 50
        print(f"Resizing column 0 from {original_width} to {new_width}")
        table.setColumnWidth(0, new_width)
        
        if hasattr(table, 'frozen_table'):
            frozen_width = table.frozen_table.columnWidth(0)
            sync_status = "✅" if frozen_width == new_width else "❌"
            print(f"Frozen table column 0 width: {frozen_width} {sync_status}")
    
    test_resize_btn.clicked.connect(test_resize)
    button_layout.addWidget(test_resize_btn)
    
    debug_btn = QtWidgets.QPushButton("Debug Geometry")
    def debug_geometry():
        print("\n=== Geometry Debug ===")
        frozen_width = table._get_frozen_table_width()
        print(f"Frozen table width: {frozen_width}")
        
        if hasattr(table, 'frozen_table'):
            geometry = table.frozen_table.geometry()
            print(f"Frozen table geometry: x={geometry.x()}, y={geometry.y()}, w={geometry.width()}, h={geometry.height()}")
            
            main_geometry = table.geometry()
            print(f"Main table geometry: x={main_geometry.x()}, y={main_geometry.y()}, w={main_geometry.width()}, h={main_geometry.height()}")
    
    debug_btn.clicked.connect(debug_geometry)
    button_layout.addWidget(debug_btn)
    
    layout.addLayout(button_layout)
    
    # Show window
    window.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_debug_window'] = window
    globals()['_debug_table'] = table
    
    print("\n=== Test Window Created ===")
    print("Use the test buttons to debug synchronization issues")
    print("Check if frozen columns (first 3) stay aligned with main table")
    
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
    test_synchronization_debug() 