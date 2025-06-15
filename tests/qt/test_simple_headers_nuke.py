#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Simple test for custom header styling in Nuke environment.

This is a standalone test that demonstrates the custom header view without
complex imports. It embeds the header view code directly.

Usage:
    Run in Nuke terminal mode:
    & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_simple_headers_nuke.py
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
    PYSIDE_VERSION = "PySide6"
else:
    from PySide2 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide2"

# Import constants directly (these don't have relative import issues)
from gui.panel.constants import Colors, TableColumns, HeaderSettingsMapping


class SimpleCustomHeaderView(QtWidgets.QHeaderView):
    """Simplified custom header view for testing with proper synchronization."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
        # Set default header properties to match standard behavior
        self.setSectionsClickable(True)
        self.setSectionsMovable(False)
        self.setStretchLastSection(False)
        
        # Enable section resize mode to maintain standard behavior
        self.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        
        # Cache colors for performance
        self._job_background = QtGui.QColor(Colors.JOB_SETTINGS_BACKGROUND)
        self._job_border = QtGui.QColor(Colors.JOB_SETTINGS_COLOR)
        self._machine_background = QtGui.QColor(Colors.MACHINE_SETTINGS_BACKGROUND)
        self._machine_border = QtGui.QColor(Colors.MACHINE_SETTINGS_COLOR)
        self._default_background = QtGui.QColor("#2a2a2a")  # Dark gray for fixed columns
        self._default_border = QtGui.QColor("#555555")      # Medium gray border
        
        print("SimpleCustomHeaderView created with job/machine color schemes")
    
    def sectionResized(self, logicalIndex, oldSize, newSize):
        """Override to ensure resize events are properly forwarded."""
        # Call parent implementation first to ensure signals are emitted
        super().sectionResized(logicalIndex, oldSize, newSize)
        
        # Force a repaint to ensure styling is updated after resize
        self.update()
    
    def resizeEvent(self, event):
        """Override resize event to maintain proper header behavior."""
        super().resizeEvent(event)
        # Ensure the header repaints after resize
        self.update()
    
    def mousePressEvent(self, event):
        """Override to maintain standard header interaction behavior."""
        # Call parent to handle standard header interactions (sorting, resizing, etc.)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Override to maintain standard header resize cursor behavior."""
        # Call parent to handle resize cursors and interactions
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Override to maintain standard header interaction behavior."""
        # Call parent to handle standard header interactions
        super().mouseReleaseEvent(event)
    
    def paintSection(self, painter, rect, logicalIndex):
        """Paint header section with custom styling based on column type."""
        if not self.model():
            super().paintSection(painter, rect, logicalIndex)
            return
            
        painter.save()
        
        # Get column header name to determine styling
        header_name = self._get_header_name(logicalIndex)
        if not header_name:
            super().paintSection(painter, rect, logicalIndex)
            painter.restore()
            return
        
        # Determine column type and colors
        setting_type, _ = HeaderSettingsMapping.get_setting_type_and_key(header_name)
        
        if setting_type == "job":
            bg_color = self._job_background
            border_color = self._job_border
        elif setting_type == "machine":
            bg_color = self._machine_background
            border_color = self._machine_border
        else:
            # Fixed columns (Order, Node, Filename) or unmapped columns
            bg_color = self._default_background
            border_color = self._default_border
        
        # Fill background with dark color
        painter.fillRect(rect, bg_color)
        
        # Draw the column text
        display_name = self._get_display_name(header_name)
        self._draw_header_text(painter, rect, display_name)
        
        # Draw borders (sides and top with subtle border, bottom with bright color)
        self._draw_header_borders(painter, rect, border_color)
        
        painter.restore()
    
    def _get_header_name(self, logical_index):
        """Get the header name for a logical index."""
        header_data = self.model().headerData(logical_index, self.orientation(), QtCore.Qt.DisplayRole)
        if not header_data:
            return None
            
        # Convert display name back to header name using reverse lookup
        display_to_header = {v: k for k, v in TableColumns.HEADER_DISPLAY_NAMES.items()}
        return display_to_header.get(str(header_data), str(header_data))
    
    def _get_display_name(self, header_name):
        """Get the display name for a header."""
        return TableColumns.HEADER_DISPLAY_NAMES.get(header_name, header_name)
    
    def _draw_header_text(self, painter, rect, text):
        """Draw the header text centered in the rectangle."""
        # Set text color to white for good contrast on dark backgrounds
        painter.setPen(QtGui.QColor(255, 255, 255))
        
        # Set font (slightly bold for headers)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # Draw text centered
        painter.drawText(rect, QtCore.Qt.AlignCenter, str(text))
    
    def _draw_header_borders(self, painter, rect, border_color):
        """Draw header borders with bright bottom edge only."""
        # Use system default header border color for sides and top
        default_border_color = self.palette().color(QtGui.QPalette.Mid)
        painter.setPen(QtGui.QPen(default_border_color, 1))
        
        # Left border (system default)
        painter.drawLine(rect.topLeft(), rect.bottomLeft())
        
        # Right border (system default)
        painter.drawLine(rect.topRight(), rect.bottomRight())
        
        # Top border (system default)
        painter.drawLine(rect.topLeft(), rect.topRight())
        
        # Bright bottom border ONLY (full opacity, slightly thicker)
        painter.setPen(QtGui.QPen(border_color, 2))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())


class SimpleHeaderTestWindow(QtWidgets.QMainWindow):
    """Simple test window to demonstrate custom header styling."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Simple Header Test - {PYSIDE_VERSION}")
        self.setGeometry(100, 100, 1400, 500)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "Custom Header Styling Test (Simplified):\n"
            "• Job Settings columns (Priority, Chunk Size, Frames, etc.) have BLUE headers\n"
            "• Machine Settings columns (Pool, Threads, RAM, etc.) have PURPLE headers\n"
            "• Fixed columns (Order, Node, Filename) have default dark gray headers\n"
            "• This is a simplified standalone test that doesn't rely on complex models"
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
        headers = TableColumns.HEADERS
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(display_headers)
        
        # Apply our custom header view
        custom_header = SimpleCustomHeaderView(QtCore.Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(custom_header)
        
        # Add some sample data
        self._load_sample_data()
        
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
        
        print(f"Simple header test window created using {PYSIDE_VERSION}")
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
    
    def _load_sample_data(self):
        """Load simple sample data."""
        self.table.setRowCount(3)
        
        # Simple sample data
        sample_data = [
            ["1000", "Write1", "/path/to/output1.exr", "75", "1", "1001-1500", "No", "0", "No", "Full", "No", "No", "No", "lighting", "", "none", "4", "0", "0", "Yes", "0", "2", "No", "", ""],
            ["2000", "Write2", "/path/to/output2.exr", "50", "5", "1001-2315", "No", "5", "No", "Proxy", "No", "No", "No", "render", "fx", "high", "8", "16", "64", "No", "1", "1", "Yes", "workstation01", "arnold:1"],
            ["3000", "Write3", "/path/to/output3.exr", "90", "2", "2001-2500", "Yes", "10", "Yes", "Both", "Yes", "Yes", "Yes", "fx", "general", "weekend", "16", "32", "128", "No", "2", "4", "No", "render01,render02", "nuke:2"]
        ]
        
        for row, row_data in enumerate(sample_data):
            for col, value in enumerate(row_data):
                if col < self.table.columnCount():
                    item = QtWidgets.QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
        
        # Resize columns to show headers better
        self.table.resizeColumnsToContents()
        
        # Set minimum column widths for better visibility
        for col in range(self.table.columnCount()):
            current_width = self.table.columnWidth(col)
            self.table.setColumnWidth(col, max(80, current_width))
    
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
    """Main function to run the simple header test."""
    window = SimpleHeaderTestWindow()
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