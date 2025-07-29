#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Test custom header styling with FrozenTableWidget in Nuke environment.

This test replicates the real scenario using FrozenTableWidget to test
the synchronization between frozen and unfrozen columns with custom headers.

Usage:
    Run in Nuke terminal mode:
    & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_frozen_headers_nuke.py
"""

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
from nk2dl.gui.panel.constants import Colors, TableColumns, HeaderSettingsMapping
from nk2dl.gui.panel.widgets import FrozenTableWidget, CustomHeaderView


class FrozenHeaderTestWindow(QtWidgets.QMainWindow):
    """Test window to demonstrate custom header styling with FrozenTableWidget."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Frozen Table Header Test - {PYSIDE_VERSION}")
        self.setGeometry(100, 100, 1400, 700)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "FrozenTableWidget Custom Header Test:\n"
            "• This test uses the ACTUAL FrozenTableWidget from the Nuke UI\n"
            "• First 3 columns (Order, Node, Filename) are frozen\n"
            "• Test column resizing to verify synchronization between frozen and unfrozen tables\n"
            "• Job Settings columns should have BLUE headers, Machine Settings should have PURPLE headers"
        )
        instructions.setStyleSheet("QLabel { padding: 15px; background-color: #333; color: white; font-size: 12px; }")
        layout.addWidget(instructions)
        
        # Create color legend
        legend_widget = self._create_color_legend()
        layout.addWidget(legend_widget)
        
        # Create FrozenTableWidget with custom headers
        self.table = FrozenTableWidget()
        layout.addWidget(self.table)
        
        # Set up table
        headers = TableColumns.HEADERS
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(display_headers)
        
        # Apply our custom header view to BOTH main and frozen tables
        main_custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(main_custom_header)
        
        # Also apply custom header to frozen table and reconnect synchronization
        if hasattr(self.table, 'frozen_table'):
            frozen_custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.table.frozen_table)
            self.table.frozen_table.setHorizontalHeader(frozen_custom_header)
            
            # CRITICAL: Reconnect synchronization signals after replacing headers
            # This is the fix for the column sync issue
            main_custom_header.sectionResized.connect(self.table._update_frozen_section_width)
            print("✅ Header synchronization signals reconnected")
        
        # Load test data
        self._load_test_data()
        
        # Create control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        test_resize_btn = QtWidgets.QPushButton("Test Column Resize Sync")
        test_resize_btn.clicked.connect(self._test_resize_sync)
        button_layout.addWidget(test_resize_btn)
        
        test_scroll_btn = QtWidgets.QPushButton("Test Horizontal Scroll")
        test_scroll_btn.clicked.connect(self._test_scroll)
        button_layout.addWidget(test_scroll_btn)
        
        refresh_btn = QtWidgets.QPushButton("Refresh Headers")
        refresh_btn.clicked.connect(self._refresh_headers)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # Add debug info button
        debug_btn = QtWidgets.QPushButton("Debug Info")
        debug_btn.clicked.connect(self._show_debug_info)
        button_layout.addWidget(debug_btn)
        
        layout.addLayout(button_layout)
        
        print(f"FrozenTableWidget header test window created using {PYSIDE_VERSION}")
        print("Testing synchronization between frozen and unfrozen table headers")
    
    def _create_color_legend(self):
        """Create a color legend showing the header color scheme."""
        legend_widget = QtWidgets.QWidget()
        legend_layout = QtWidgets.QHBoxLayout(legend_widget)
        legend_layout.setContentsMargins(15, 10, 15, 10)
        
        # Job settings legend
        job_frame = QtWidgets.QFrame()
        job_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.JOB_SETTINGS_BACKGROUND};
                border-bottom: 3px solid {Colors.JOB_SETTINGS_COLOR};
                padding: 8px;
                margin: 5px;
            }}
        """)
        job_layout = QtWidgets.QVBoxLayout(job_frame)
        job_label = QtWidgets.QLabel("Job Settings")
        job_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        job_columns = QtWidgets.QLabel("Priority, Chunk Size, Frames, etc.")
        job_columns.setStyleSheet("QLabel { color: #ccc; font-size: 10px; }")
        job_layout.addWidget(job_label)
        job_layout.addWidget(job_columns)
        legend_layout.addWidget(job_frame)
        
        # Machine settings legend  
        machine_frame = QtWidgets.QFrame()
        machine_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.MACHINE_SETTINGS_BACKGROUND};
                border-bottom: 3px solid {Colors.MACHINE_SETTINGS_COLOR};
                padding: 8px;
                margin: 5px;
            }}
        """)
        machine_layout = QtWidgets.QVBoxLayout(machine_frame)
        machine_label = QtWidgets.QLabel("Machine Settings")
        machine_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        machine_columns = QtWidgets.QLabel("Pool, Threads, RAM, etc.")
        machine_columns.setStyleSheet("QLabel { color: #ccc; font-size: 10px; }")
        machine_layout.addWidget(machine_label)
        machine_layout.addWidget(machine_columns)
        legend_layout.addWidget(machine_frame)
        
        # Fixed columns legend
        fixed_frame = QtWidgets.QFrame()
        fixed_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-bottom: 3px solid #555555;
                padding: 8px;
                margin: 5px;
            }
        """)
        fixed_layout = QtWidgets.QVBoxLayout(fixed_frame)
        fixed_label = QtWidgets.QLabel("Fixed Columns (Frozen)")
        fixed_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        fixed_columns = QtWidgets.QLabel("Order, Node, Filename")
        fixed_columns.setStyleSheet("QLabel { color: #ccc; font-size: 10px; }")
        fixed_layout.addWidget(fixed_label)
        fixed_layout.addWidget(fixed_columns)
        legend_layout.addWidget(fixed_frame)
        
        return legend_widget
    
    def _load_test_data(self):
        """Load test data to demonstrate frozen table with custom headers."""
        test_data = [
            {
                # Row 1: Mix of job and machine settings
                "Order": "1000", "Node": "Write1", "Filename": "/path/to/output1.%04d.exr",
                "Priority": "75", "ChunkSize": "1", "Frames": "1001-1500",  # Job settings
                "Pool": "lighting", "UseGPU": "Yes", "Threads": "8"  # Machine settings
            },
            {
                # Row 2: Different values
                "Order": "2000", "Node": "Write2", "Filename": "/path/to/output2.%04d.exr",
                "Priority": "50", "ChunkSize": "5", "Frames": "1001-2315",  # Job settings
                "Pool": "render", "UseGPU": "No", "Threads": "4"  # Machine settings
            },
            {
                # Row 3: More data to show styling differences
                "Order": "3000", "Node": "Write3", "Filename": "/path/to/output3.%04d.exr",
                "Priority": "90", "ChunkSize": "2", "Frames": "2001-2500",  # Job settings
                "Pool": "fx", "UseGPU": "No", "Threads": "16"  # Machine settings
            }
        ]
        
        # Populate the table
        self.table.setRowCount(len(test_data))
        headers = TableColumns.HEADERS
        
        for row, row_data in enumerate(test_data):
            for col, header in enumerate(headers):
                value = row_data.get(header, "")
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)
        
        # Resize columns to show headers better
        self.table.resizeColumnsToContents()
        
        # Set minimum column widths for better visibility
        for col in range(self.table.columnCount()):
            current_width = self.table.columnWidth(col)
            self.table.setColumnWidth(col, max(80, current_width))
    
    def _test_resize_sync(self):
        """Test column resize synchronization between frozen and unfrozen tables."""
        print("Testing column resize synchronization...")
        
        # Test resizing the first column (Order - should be frozen)
        original_width = self.table.columnWidth(0)
        new_width = original_width + 50
        
        print(f"Resizing column 0 (Order) from {original_width} to {new_width}")
        self.table.setColumnWidth(0, new_width)
        
        # Check if frozen table column was also resized
        if hasattr(self.table, 'frozen_table'):
            frozen_width = self.table.frozen_table.columnWidth(0)
            print(f"Frozen table column 0 width: {frozen_width}")
            
            if frozen_width == new_width:
                print("✅ Column resize synchronization WORKING")
            else:
                print("❌ Column resize synchronization BROKEN")
        else:
            print("❌ No frozen table found")
    
    def _test_scroll(self):
        """Test horizontal scrolling to see header styling."""
        scroll_bar = self.table.horizontalScrollBar()
        current_value = scroll_bar.value()
        
        # Animate scroll to show different column types
        target_value = min(scroll_bar.maximum(), current_value + 400)
        
        def scroll_step():
            current = scroll_bar.value()
            if current < target_value:
                scroll_bar.setValue(current + 15)
                QtCore.QTimer.singleShot(50, scroll_step)
        
        scroll_step()
    
    def _refresh_headers(self):
        """Refresh the header display."""
        self.table.horizontalHeader().update()
        if hasattr(self.table, 'frozen_table'):
            self.table.frozen_table.horizontalHeader().update()
        print("Headers refreshed")
    
    def _show_debug_info(self):
        """Show debug information about the table setup."""
        info_text = "FrozenTableWidget Debug Info:\n\n"
        
        # Check if frozen table exists
        if hasattr(self.table, 'frozen_table'):
            info_text += "✅ Frozen table exists\n"
            info_text += f"Frozen column count: {getattr(self.table, 'frozen_column_count', 'Unknown')}\n"
            
            # Check header types
            main_header_type = type(self.table.horizontalHeader()).__name__
            frozen_header_type = type(self.table.frozen_table.horizontalHeader()).__name__
            
            info_text += f"Main table header type: {main_header_type}\n"
            info_text += f"Frozen table header type: {frozen_header_type}\n"
            
            # Check if synchronization signal is connected
            main_header = self.table.horizontalHeader()
            if hasattr(main_header, 'sectionResized'):
                info_text += "✅ Main header has sectionResized signal\n"
            else:
                info_text += "❌ Main header missing sectionResized signal\n"
            
            # Check column widths for first few columns
            info_text += "\nColumn widths (first 5 columns):\n"
            for i in range(min(5, self.table.columnCount())):
                main_width = self.table.columnWidth(i)
                frozen_width = self.table.frozen_table.columnWidth(i)
                sync_status = "✅" if main_width == frozen_width else "❌"
                info_text += f"Column {i}: Main={main_width}, Frozen={frozen_width} {sync_status}\n"
        else:
            info_text += "❌ No frozen table found\n"
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Debug Information")
        msg.setText(info_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()


def main():
    """Main function to run the frozen table header test."""
    window = FrozenHeaderTestWindow()
    window.show()
    
    # Prevent garbage collection in tests - store global reference
    globals()['_test_window'] = window
    
    # Keep windows responsive in Nuke terminal mode
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