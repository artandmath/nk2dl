#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to demonstrate frozen column functionality.

This script shows how the first 3 columns (Order, Node, Filename) are frozen
and remain visible while other columns scroll horizontally.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from PySide6 import QtWidgets, QtCore
    PYSIDE_VERSION = "PySide6"
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
        PYSIDE_VERSION = "PySide2"
    except ImportError:
        print("Neither PySide6 nor PySide2 is available")
        sys.exit(1)

from nk2dl.gui.panel.models import TableDataModel, SettingsModel
from nk2dl.gui.panel.widgets import FrozenTableWidget
from nk2dl.gui.panel.delegates import SettingsAwareDelegate


class FrozenColumnTestWindow(QtWidgets.QMainWindow):
    """Test window to demonstrate frozen column functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Frozen Column Test - {PYSIDE_VERSION}")
        self.setGeometry(100, 100, 1200, 600)
        
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
            "Frozen Column Test:\n"
            "• The first 3 columns (Order, Node, Filename) are frozen and always visible\n"
            "• Use horizontal scroll to see how frozen columns stay in place\n"
            "• Frozen columns don't support inheritance (they're unique per node) and aren't bold\n"
            "• Other columns can inherit from settings (normal text) or have explicit values (bold text)\n"
            "• Frozen area has darker alternating row colors\n"
            "• Click individual cells to select them (not whole rows)\n"
            "• Selection is exclusive: selecting in one area clears selection in the other area"
        )
        instructions.setStyleSheet("QLabel { padding: 10px; background-color: #333; color: white; }")
        layout.addWidget(instructions)
        
        # Create frozen table
        self.table = FrozenTableWidget()
        layout.addWidget(self.table)
        
        # Set up delegate
        delegate = SettingsAwareDelegate(self.table_model)
        self.table.setItemDelegate(delegate)
        
        # Set up table
        headers = self.table_model.get_headers()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Load test data
        self._load_test_data()
        
        # Create control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        test_scroll_btn = QtWidgets.QPushButton("Test Horizontal Scroll")
        test_scroll_btn.clicked.connect(self._test_scroll)
        button_layout.addWidget(test_scroll_btn)
        
        reset_btn = QtWidgets.QPushButton("Reset View")
        reset_btn.clicked.connect(self._reset_view)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        print(f"Frozen column test window created using {PYSIDE_VERSION}")
        print("First 3 columns (Order, Node, Filename) are frozen")
    
    def _load_test_data(self):
        """Load test data to demonstrate frozen columns."""
        test_data = [
            {
                # Row 1: Order, Node, Filename are always explicit (no inheritance)
                "Order": "1000", "Node": "Write1", "Filename": "/path/to/output1.%04d.exr",
                "Priority": "75", "ChunkSize": None, "Frames": None,  # Some inherit, some explicit
                "Pool": "lighting", "UseGPU": "Yes", "Threads": None
            },
            {
                # Row 2: Frozen columns with different values
                "Order": "2000", "Node": "Write2", "Filename": "/path/to/output2.%04d.exr",
                "Priority": None, "ChunkSize": "5", "Frames": "1001-1500",  # Different inheritance pattern
                "Pool": None, "UseGPU": None, "Threads": "8"
            },
            {
                # Row 3: More test data
                "Order": "3000", "Node": "Write3", "Filename": "/path/to/output3.%04d.exr",
                "Priority": None, "ChunkSize": None, "Frames": None,  # All inherit non-frozen columns
                "Pool": "fx", "UseGPU": "No", "Threads": None
            },
            {
                # Row 4: Even more data to test scrolling
                "Order": "4000", "Node": "Write4", "Filename": "/path/to/output4.%04d.exr",
                "Priority": "90", "ChunkSize": "2", "Frames": "2001-2500",
                "Pool": "render", "UseGPU": "Yes", "Threads": "16"
            }
        ]
        
        self.table_model.set_data(test_data)
        self._populate_table()
        
        # Resize columns to show the effect better
        self.table.resizeColumnsToContents()
        
        # Set minimum column widths to force horizontal scrolling
        for col in range(3, self.table.columnCount()):
            self.table.setColumnWidth(col, max(120, self.table.columnWidth(col)))
    
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
                # Don't make frozen columns highlighted (they don't support inheritance)
                if col >= 3 and is_overridden:  # Only non-frozen columns can be highlighted
                    from nk2dl.gui.panel.constants import Colors
                    # Light blue background for highlighting (same as other widgets)
                    item.setBackground(QtGui.QBrush(QtGui.QColor(Colors.WIDGET_HIGHLIGHT_COLOR)))
                
                self.table.setItem(row, col, item)
    
    def _test_scroll(self):
        """Test horizontal scrolling to demonstrate frozen columns."""
        # Scroll to show that frozen columns stay in place
        scroll_bar = self.table.horizontalScrollBar()
        current_value = scroll_bar.value()
        
        # Animate scroll to the right
        target_value = min(scroll_bar.maximum(), current_value + 300)
        
        # Simple scroll animation
        def scroll_step():
            current = scroll_bar.value()
            if current < target_value:
                scroll_bar.setValue(current + 10)
                QtCore.QTimer.singleShot(50, scroll_step)
        
        scroll_step()
    
    def _reset_view(self):
        """Reset the view to show all columns."""
        self.table.horizontalScrollBar().setValue(0)
        self.table.resizeColumnsToContents()


def main():
    """Run the frozen column test."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Set a dark style for better visibility
    app.setStyle('Fusion')
    palette = app.palette()
    palette.setColor(palette.Window, QtCore.Qt.darkGray)
    palette.setColor(palette.WindowText, QtCore.Qt.white)
    app.setPalette(palette)
    
    window = FrozenColumnTestWindow()
    window.show()
    
    print("\nFrozen Column Test Instructions:")
    print("1. The first 3 columns (Order, Node, Filename) should be frozen")
    print("2. Click 'Test Horizontal Scroll' to see frozen columns in action")
    print("3. Try manually scrolling horizontally with the scroll bar")
    print("4. Frozen columns should always remain visible")
    print("5. Frozen columns should NOT be bold (they don't support inheritance)")
    print("6. Only non-frozen columns with explicit values should be bold")
    print("7. Frozen area should have darker alternating row colors")
    print("8. Click individual cells to select them (not whole rows)")
    print("9. Selection is exclusive: selecting in frozen area clears unfrozen selection and vice versa")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 