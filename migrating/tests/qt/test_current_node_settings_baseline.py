#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Baseline test for current node_settings_view before checkbox column implementation.

This test verifies the current functionality works properly before making changes.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_current_node_settings_baseline.py
"""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
try:
    import nuke
    NUKE_AVAILABLE = True
    
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from nk2dl.gui.panel.models import TableDataModel, SettingsModel
from nk2dl.gui.panel.views import NodeSettingsView
from nk2dl.gui.panel.constants import TableColumns


class BaselineTestWindow(QtWidgets.QMainWindow):
    """Test window to verify current node_settings_view functionality."""
    
    def __init__(self):
        super().__init__()
        nuke_info = f" - Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}" if NUKE_AVAILABLE else ""
        self.setWindowTitle(f"Node Settings View Baseline Test - {PYSIDE_VERSION}{nuke_info}")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create models
        self.settings_model = SettingsModel()
        self.table_model = TableDataModel(self.settings_model)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "BASELINE TEST - Current Node Settings View\n\n"
            "This test verifies current functionality before adding the checkbox column:\n"
            "• 3 frozen columns: Order, Node, Filename\n"  
            "• Settings inheritance with bold text for overrides\n"
            "• Column resizing and sorting\n"
            "• Frozen table synchronization\n\n"
            "Expected behavior:\n"
            "• Frozen columns (Order, Node, Filename) stay visible during horizontal scroll\n"
            "• Bold text indicates overridden values vs inherited (normal text)\n"
            "• Column headers show job settings (blue) vs machine settings (purple)\n"
            "• All functionality should work smoothly"
        )
        instructions.setStyleSheet("""
            QLabel { 
                padding: 10px; 
                background-color: #333; 
                color: white; 
                border: 1px solid #555;
                font-size: 11px;
            }
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create node settings view
        self.node_settings_view = NodeSettingsView(self.table_model, self.settings_model)
        layout.addWidget(self.node_settings_view)
        
        # Load test data
        self._load_test_data()
        
        # Add status and control buttons
        self._create_controls(layout)
        
        print(f"Baseline test window created using {PYSIDE_VERSION}")
        print("Testing current node_settings_view before checkbox column implementation")
    
    def _load_test_data(self):
        """Load test data to verify current functionality."""
        test_data = [
            {
                # Row 1: Mix of explicit and inherited values
                "Render": True,
                "Order": "1000", 
                "Node": "Write1", 
                "Filename": "output1_%04d.exr",
                "Priority": "75",      # Explicit (should be bold)
                "ChunkSize": None,     # Inherit (should be normal text) 
                "Frames": "1001-1500", # Explicit (should be bold)
                "NodesFrames": None,   # Inherit (should be normal text)
                "Pool": "lighting",    # Explicit (should be bold)
                "UseGPU": "Yes",       # Explicit (should be bold)
                "Threads": None        # Inherit (should be normal text)
            },
            {
                # Row 2: Different mix
                "Render": False,
                "Order": "2000",
                "Node": "Write2", 
                "Filename": "output2_%04d.exr",
                "Priority": None,      # Inherit
                "ChunkSize": "5",      # Explicit
                "Frames": None,        # Inherit
                "NodesFrames": "Yes",  # Explicit
                "Pool": None,          # Inherit
                "UseGPU": None,        # Inherit
                "Threads": "8"         # Explicit
            },
            {
                # Row 3: More test data for scrolling
                "Render": True,
                "Order": "3000",
                "Node": "Write3",
                "Filename": "output3_%04d.exr", 
                "Priority": "90",      # Explicit
                "ChunkSize": "2",      # Explicit
                "Frames": "2001-2500", # Explicit
                "NodesFrames": None,   # Inherit
                "Pool": "fx",          # Explicit
                "UseGPU": "No",        # Explicit
                "Threads": "16"        # Explicit
            },
            {
                # Row 4: Test frozen column visibility during scroll
                "Render": False,
                "Order": "4000",
                "Node": "WriteVeryLongNodeName123",
                "Filename": "/very/long/path/to/output/file_with_long_name_%04d.exr",
                "Priority": None,      # Inherit
                "ChunkSize": None,     # Inherit
                "Frames": None,        # Inherit
                "NodesFrames": None,   # Inherit
                "Pool": "render",      # Explicit
                "UseGPU": "Yes",       # Explicit
                "Threads": None        # Inherit
            }
        ]
        
        # Set the data in the table model
        self.table_model.set_data(test_data)
        print(f"Loaded {len(test_data)} test rows")
        
        # Verify expected column count (should be 25 columns currently)
        headers = self.table_model.get_headers()
        print(f"Current column count: {len(headers)}")
        print(f"Headers: {headers[:10]}...")  # Show first 10
        print(f"Frozen columns expected: 4 (Render, Order, Node, Filename)")
        
    def _create_controls(self, layout):
        """Create control buttons and status."""
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        
        # Test buttons
        test_inheritance_btn = QtWidgets.QPushButton("Test Inheritance")
        test_inheritance_btn.clicked.connect(self._test_inheritance)
        controls_layout.addWidget(test_inheritance_btn)
        
        test_frozen_btn = QtWidgets.QPushButton("Test Frozen Columns")
        test_frozen_btn.clicked.connect(self._test_frozen_columns)
        controls_layout.addWidget(test_frozen_btn)
        
        test_sorting_btn = QtWidgets.QPushButton("Test Sorting")
        test_sorting_btn.clicked.connect(self._test_sorting)
        controls_layout.addWidget(test_sorting_btn)
        
        controls_layout.addStretch()
        
        # Status info
        status_label = QtWidgets.QLabel("Status: Ready for baseline testing")
        status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        controls_layout.addWidget(status_label)
        self.status_label = status_label
        
        layout.addWidget(controls_widget)
    
    def _test_inheritance(self):
        """Test inheritance functionality."""
        print("\n=== Testing Inheritance ===")
        self.status_label.setText("Status: Testing inheritance...")
        
        # Check if bold styling is working for overrides
        table = self.node_settings_view.render_table
        headers = self.table_model.get_headers()
        
        for row in range(min(3, table.rowCount())):
            for col in range(min(10, table.columnCount())):
                item = table.item(row, col)
                if item:
                    header = headers[col] if col < len(headers) else f"Col{col}"
                    is_bold = item.font().bold()
                    raw_value = self.table_model.get_cell_value(row, col)
                    print(f"  Row {row}, {header}: value='{raw_value}', bold={is_bold}")
        
        self.status_label.setText("Status: Inheritance test complete")
    
    def _test_frozen_columns(self):
        """Test frozen column functionality."""
        print("\n=== Testing Frozen Columns ===")
        self.status_label.setText("Status: Testing frozen columns...")
        
        table = self.node_settings_view.render_table
        if hasattr(table, 'frozen_table'):
            frozen_count = getattr(table, 'frozen_column_count', 0)
            print(f"  Frozen column count: {frozen_count}")
            print(f"  Expected: 4 (Render, Order, Node, Filename)")
            
            # Test frozen table sync
            main_width = table.columnWidth(0)
            frozen_width = table.frozen_table.columnWidth(0)
            print(f"  Order column width sync: main={main_width}, frozen={frozen_width}")
            
            if main_width == frozen_width:
                print("  ✓ Column width synchronization working")
            else:
                print("  ✗ Column width synchronization issue")
        else:
            print("  ✗ No frozen table found")
        
        self.status_label.setText("Status: Frozen columns test complete")
    
    def _test_sorting(self):
        """Test sorting functionality."""
        print("\n=== Testing Sorting ===")
        self.status_label.setText("Status: Testing sorting...")
        
        # Get current sort state
        sort_state = self.table_model.get_sort_state()
        print(f"  Current sort state: {sort_state}")
        
        # Test clicking header for sorting
        table = self.node_settings_view.render_table
        header = table.horizontalHeader()
        print(f"  Sort indicator shown: {header.sortIndicatorShown()}")
        if header.sortIndicatorShown():
            section = header.sortIndicatorSection()
            order = header.sortIndicatorOrder()
            print(f"  Sort indicator: section={section}, order={order}")
        
        self.status_label.setText("Status: Sorting test complete")


def main():
    """Main test function."""
    print("Starting baseline test for node_settings_view...")
    
    # Create test window
    window = BaselineTestWindow()
    window.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_baseline_test_window'] = window
    
    try:
        print("Window shown. Use Ctrl+C to exit.")
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if not window.isVisible():
                break
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    print("Baseline test completed")
    return window


if __name__ == "__main__":
    main() 