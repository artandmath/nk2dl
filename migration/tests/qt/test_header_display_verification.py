#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple test to verify table headers show display names correctly."""

import sys
import os
import time

# Direct path setup
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

# Direct import to avoid relative import issues
from nk2dl.gui.panel.constants import TableColumns

class HeaderDisplayTest(QtWidgets.QMainWindow):
    """Test window to verify header display names."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Header Display Test - {PYSIDE_VERSION}")
        self.setGeometry(100, 100, 1200, 400)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "Header Display Test:\n"
            "This test verifies that table headers show display names (e.g., 'Chunk Size') instead of internal names (e.g., 'ChunkSize')\n"
            "Check the table headers below - they should show user-friendly names with spaces."
        )
        instructions.setStyleSheet("QLabel { padding: 15px; background-color: #333; color: white; font-size: 12px; }")
        layout.addWidget(instructions)
        
        # Create table
        self.table = QtWidgets.QTableWidget()
        layout.addWidget(self.table)
        
        # Set up headers
        headers = TableColumns.HEADERS[:10]  # First 10 columns for testing
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        
        print(f"Internal headers: {headers}")
        print(f"Display headers: {display_headers}")
        
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(display_headers)
        
        # Add some sample data
        self.table.setRowCount(2)
        for row in range(2):
            for col in range(len(headers)):
                item = QtWidgets.QTableWidgetItem(f"R{row}C{col}")
                self.table.setItem(row, col, item)
        
        # Create verification report
        report_text = self._create_verification_report(headers, display_headers)
        report_label = QtWidgets.QLabel(report_text)
        report_label.setStyleSheet("QLabel { padding: 10px; background-color: #222; color: #aaa; font-family: monospace; font-size: 10px; }")
        layout.addWidget(report_label)
        
        # Resize columns to content
        self.table.resizeColumnsToContents()
        
        print("Header Display Test created")
        print("Check if headers show display names with spaces")
    
    def _create_verification_report(self, internal_headers, display_headers):
        """Create a report showing the header mapping."""
        report_lines = ["Header Verification Report:", "=" * 50]
        
        for i, (internal, display) in enumerate(zip(internal_headers, display_headers)):
            status = "✓ DISPLAY NAME" if internal != display else "→ SAME AS INTERNAL"
            report_lines.append(f"{i:2d}. '{internal}' → '{display}' {status}")
        
        return "\n".join(report_lines)

def main():
    """Main function to run the header display test."""
    window = HeaderDisplayTest()
    window.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_window'] = window
    
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.1)
            if not window.isVisible():
                break
    except KeyboardInterrupt:
        pass
    
    return window

if __name__ == "__main__":
    main() 