#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test column width calculation and header resize modes in Nuke environment."""

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

# Import our widgets and constants
from nk2dl.gui.panel.widgets.table_widgets import FrozenTableWidget
from nk2dl.gui.panel.constants import TableColumns, Sizes

def debug_header_resize_modes():
    """Debug different header resize modes and their effects on column widths."""
    print("\n=== DEBUGGING HEADER RESIZE MODES ===")
    
    # Create a simple table widget
    table = FrozenTableWidget()
    table.setColumnCount(5)
    table.setRowCount(1)
    
    # Set headers
    headers = ["Order", "Node", "Filename", "Priority", "ChunkSize"]
    table.setHorizontalHeaderLabels(headers)
    
    # Add some sample data
    for col, header in enumerate(headers):
        item = QtWidgets.QTableWidgetItem(f"Sample_{header}")
        table.setItem(0, col, item)
    
    print(f"Created table with {table.columnCount()} columns")
    
    # Test different resize modes
    resize_modes = [
        ("Interactive", QtWidgets.QHeaderView.Interactive),
        ("Stretch", QtWidgets.QHeaderView.Stretch),
        ("ResizeToContents", QtWidgets.QHeaderView.ResizeToContents),
        ("Fixed", QtWidgets.QHeaderView.Fixed)
    ]
    
    for mode_name, mode_value in resize_modes:
        print(f"\n--- Testing {mode_name} mode ---")
        
        # Set the resize mode
        table.horizontalHeader().setSectionResizeMode(mode_value)
        
        # Try to set different column widths
        target_widths = [50, 110, 200, 60, 80]
        for col, width in enumerate(target_widths):
            table.setColumnWidth(col, width)
            print(f"Set column {col} ({headers[col]}) to {width}px")
        
        # Check actual widths
        print("Actual widths after setting:")
        actual_widths = []
        for col in range(table.columnCount()):
            actual_width = table.columnWidth(col)
            actual_widths.append(actual_width)
            print(f"  Column {col} ({headers[col]}): {actual_width}px")
        
        # Check if all widths are the same
        unique_widths = set(actual_widths)
        if len(unique_widths) == 1:
            print(f"  ❌ All columns have same width: {list(unique_widths)[0]}px")
        else:
            print(f"  ✅ Found {len(unique_widths)} different widths: {sorted(unique_widths)}")
    
    return table

def debug_column_width_calculation():
    """Debug the column width calculation method."""
    print("\n=== DEBUGGING COLUMN WIDTH CALCULATION ===")
    
    # Create font metrics
    font = QtGui.QFont()
    font_metrics = QtGui.QFontMetrics(font)
    
    print(f"Using font: {font.family()}, {font.pointSize()}pt")
    
    # Test calculation for different headers
    test_headers = ["Order", "Node", "Filename", "Priority", "ChunkSize"]
    
    for header in test_headers:
        # Test with sample values
        if header == "Order":
            sample_values = ["1", "1000", "2000"]
        elif header == "Node":
            sample_values = ["Write1", "Write123", "WriteNode_v001"]
        elif header == "Filename":
            sample_values = ["output.%04d.exr", "/long/path/to/output_file.%04d.exr"]
        elif header == "Priority":
            sample_values = ["50", "100"]
        elif header == "ChunkSize":
            sample_values = []
        else:
            sample_values = []
        
        calculated_width = TableColumns.calculate_column_width(header, font_metrics, sample_values)
        print(f"Header '{header}': calculated width = {calculated_width}px, samples = {sample_values[:3]}")

def debug_frozen_table_integration():
    """Debug the frozen table column width synchronization."""
    print("\n=== DEBUGGING FROZEN TABLE INTEGRATION ===")
    
    # Create frozen table widget
    table = FrozenTableWidget()
    table.setColumnCount(10)
    table.setRowCount(2)
    
    # Set headers
    headers = TableColumns.HEADERS[:10]
    table.setHorizontalHeaderLabels(headers)
    
    print(f"Created frozen table with {table.columnCount()} columns, {table.frozen_column_count} frozen")
    
    # Add some sample data
    for row in range(2):
        for col in range(10):
            item = QtWidgets.QTableWidgetItem(f"R{row}C{col}")
            table.setItem(row, col, item)
    
    # Show the table
    table.show()
    table.resize(800, 300)
    
    print("Table shown, calling calculate_optimal_column_widths...")
    
    # Call our column width calculation
    table.calculate_optimal_column_widths()
    
    return table

def main():
    """Main test function."""
    print("Starting column width debug test in Nuke environment...")
    print(f"Nuke version: {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
    print(f"Using PySide version: {QtCore.__version__}")
    
    # Run debug tests
    debug_column_width_calculation()
    debug_header_resize_modes()
    test_table = debug_frozen_table_integration()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_table'] = test_table
    
    print("\n=== Test completed. Table is visible for inspection ===")
    print("Press Ctrl+C to exit or close the table window")
    
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.01)
            if not test_table.isVisible():
                break
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    return test_table

if __name__ == "__main__":
    main() 