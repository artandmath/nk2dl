#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Test custom header styling for node settings table in Nuke environment.

This test demonstrates the custom header view that styles columns based on whether
they belong to job settings (blue) or machine settings (purple).

Usage:
    Run in Nuke terminal mode:
    & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_custom_headers_nuke.py
"""

import sys
import os
import time
import logging

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide6"
else:
    from PySide2 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide2"

# Simple logging setup to avoid import issues
def setup_logging(name):
    """Simple logging setup for testing."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Monkey patch the logging function to avoid import error
import nk2dl.common
nk2dl.common.logging = type('MockLogging', (), {'setup_logging': setup_logging})()

# Import nk2dl components
from gui.panel.models import TableDataModel, SettingsModel
from gui.panel.widgets import CustomHeaderView
from gui.panel.delegates import SettingsAwareDelegate
from gui.panel.constants import Colors, TableColumns, HeaderSettingsMapping


class CustomHeaderTestWindow(QtWidgets.QMainWindow):
    """Test window to demonstrate custom header styling."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Custom Header Test - {PYSIDE_VERSION}")
        self.setGeometry(100, 100, 1400, 700)
        
        # Create models
        self.settings_model = SettingsModel()
        self.table_model = TableDataModel(self.settings_model)
        self.table_model.set_settings_model(self.settings_model)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "Custom Header Styling Test:\n"
            "• Job Settings columns (Priority, Chunk Size, Frames, etc.) have BLUE headers\n"
            "• Machine Settings columns (Pool, Threads, RAM, etc.) have PURPLE headers\n"
            "• Fixed columns (Order, Node, Filename) have default dark gray headers\n"
            "• Headers use dark background with bright colored bottom borders\n"
            "• All headers have bold white text for good contrast"
        )
        instructions.setStyleSheet("QLabel { padding: 15px; background-color: #333; color: white; font-size: 12px; }")
        layout.addWidget(instructions)
        
        # Create color legend
        legend_widget = self._create_color_legend()
        layout.addWidget(legend_widget)
        
        # Create table with custom headers
        self.table = QtWidgets.QTableWidget()
        layout.addWidget(self.table)
        
        # Set up table
        headers = self.table_model.get_headers()
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(display_headers)
        
        # Apply our custom header view
        custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(custom_header)
        
        # Set up delegate
        delegate = SettingsAwareDelegate(self.table_model)
        self.table.setItemDelegate(delegate)
        
        # Load test data
        self._load_test_data()
        
        # Create control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        test_scroll_btn = QtWidgets.QPushButton("Test Horizontal Scroll")
        test_scroll_btn.clicked.connect(self._test_scroll)
        button_layout.addWidget(test_scroll_btn)
        
        refresh_btn = QtWidgets.QPushButton("Refresh Headers")
        refresh_btn.clicked.connect(self._refresh_headers)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # Add color info button
        info_btn = QtWidgets.QPushButton("Show Color Info")
        info_btn.clicked.connect(self._show_color_info)
        button_layout.addWidget(info_btn)
        
        layout.addLayout(button_layout)
        
        print(f"Custom header test window created using {PYSIDE_VERSION}")
        print("Headers styled based on job/machine settings classification")
    
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
        job_columns = QtWidgets.QLabel("Priority, Chunk Size, Frames, Nodes Frames,\nTask Timeout, Auto Timeout, Render Mode,\nNuke X, Batch Mode, Reload Plugin")
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
        machine_columns = QtWidgets.QLabel("Pool, Secondary Pool, Group, Threads,\nMin RAM, Max RAM, Use GPU, GPU ID,\nConcurrent Tasks, Worker Task Limit,\nMachine List, Limits")
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
        fixed_label = QtWidgets.QLabel("Fixed Columns")
        fixed_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        fixed_columns = QtWidgets.QLabel("Order, Node, Filename")
        fixed_columns.setStyleSheet("QLabel { color: #ccc; font-size: 10px; }")
        fixed_layout.addWidget(fixed_label)
        fixed_layout.addWidget(fixed_columns)
        legend_layout.addWidget(fixed_frame)
        
        return legend_widget
    
    def _load_test_data(self):
        """Load test data to demonstrate custom headers."""
        test_data = [
            {
                # Row 1: Mix of job and machine settings
                "Order": "1000", "Node": "Write1", "Filename": "/path/to/output1.%04d.exr",
                "Priority": "75", "ChunkSize": None, "Frames": "1001-1500",  # Job settings
                "Pool": "lighting", "UseGPU": "Yes", "Threads": "8"  # Machine settings
            },
            {
                # Row 2: Different values
                "Order": "2000", "Node": "Write2", "Filename": "/path/to/output2.%04d.exr",
                "Priority": None, "ChunkSize": "5", "Frames": None,  # Job settings
                "Pool": "render", "UseGPU": None, "Threads": None  # Machine settings
            },
            {
                # Row 3: More data to show styling differences
                "Order": "3000", "Node": "Write3", "Filename": "/path/to/output3.%04d.exr",
                "Priority": "90", "ChunkSize": "2", "Frames": "2001-2500",  # Job settings
                "Pool": "fx", "UseGPU": "No", "Threads": "16"  # Machine settings
            }
        ]
        
        self.table_model.set_data(test_data)
        self._populate_table()
        
        # Resize columns to show headers better
        self.table.resizeColumnsToContents()
        
        # Set minimum column widths for better visibility
        for col in range(self.table.columnCount()):
            current_width = self.table.columnWidth(col)
            self.table.setColumnWidth(col, max(80, current_width))
    
    def _populate_table(self):
        """Populate the table with data from the model."""
        data = self.table_model.get_data()
        headers = self.table_model.get_headers()
        
        self.table.setRowCount(len(data))
        
        for row, row_data in enumerate(data):
            for col, header in enumerate(headers):
                raw_value = self.table_model.get_cell_value(row, col)
                effective_value = self.table_model.get_effective_cell_value(row, col)
                
                if raw_value is None:
                    item = QtWidgets.QTableWidgetItem("")
                    item.setData(QtCore.Qt.UserRole, None)
                else:
                    item = QtWidgets.QTableWidgetItem(str(raw_value))
                    item.setData(QtCore.Qt.UserRole, raw_value)
                
                item.setText(str(effective_value))
                
                # Apply styling based on override status
                is_overridden = self.table_model.is_cell_overridden(row, col)
                if is_overridden:
                    from nk2dl.gui.panel.constants import Colors
                    item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                    # Light blue background for highlighting (same as other widgets)
                    item.setBackground(QtGui.QBrush(QtGui.QColor(Colors.WIDGET_HIGHLIGHT_COLOR)))
                
                self.table.setItem(row, col, item)
    
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
        print("Headers refreshed")
    
    def _show_color_info(self):
        """Show color information dialog."""
        info_text = (
            "Custom Header Color Scheme:\n\n"
            f"Job Settings Color: {Colors.JOB_SETTINGS_COLOR} (Blue)\n"
            f"Job Settings Background: {Colors.JOB_SETTINGS_BACKGROUND}\n\n"
            f"Machine Settings Color: {Colors.MACHINE_SETTINGS_COLOR} (Purple)\n"
            f"Machine Settings Background: {Colors.MACHINE_SETTINGS_BACKGROUND}\n\n"
            "Column Classification:\n"
        )
        
        # Add job settings columns
        job_cols = list(HeaderSettingsMapping.JOB_SETTINGS_MAPPING.keys())
        info_text += f"Job Settings: {', '.join(job_cols)}\n\n"
        
        # Add machine settings columns
        machine_cols = list(HeaderSettingsMapping.MACHINE_SETTINGS_MAPPING.keys())
        info_text += f"Machine Settings: {', '.join(machine_cols)}\n\n"
        
        # Add fixed columns
        info_text += "Fixed Columns: Order, Node, Filename"
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Header Color Information")
        msg.setText(info_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()


def main():
    """Main function to run the custom header test."""
    window = CustomHeaderTestWindow()
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