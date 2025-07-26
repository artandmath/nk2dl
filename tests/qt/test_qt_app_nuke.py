#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Standalone Qt application to test the nk2dl panel in Nuke."""

import sys
import os

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

# Import Nuke's PySide
try:
    import nuke
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
except ImportError:
    print("Error: This script must be run within Nuke")
    sys.exit(1)

# Import only the core components we need, avoiding widgets that have relative imports
from gui.panel.models import TableDataModel, SettingsModel
from gui.panel.constants import TableColumns


class SimpleTableWidget(QtWidgets.QTableWidget):
    """Simple table widget without the complex dependencies."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSortingEnabled(False)
        self.setWordWrap(False)
        
        # Set header properties
        horizontal_header = self.horizontalHeader()
        horizontal_header.setStretchLastSection(True)
        horizontal_header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        
        vertical_header = self.verticalHeader()
        vertical_header.setVisible(True)
        vertical_header.setDefaultSectionSize(25)


class SimpleNodeSettingsView(QtWidgets.QWidget):
    """Simplified node settings view for testing inheritance."""
    
    def __init__(self, table_model, settings_model=None, parent=None):
        super().__init__(parent)
        self.table_model = table_model
        self.settings_model = settings_model
        
        # Connect settings model to table model for inheritance
        if self.settings_model:
            self.table_model.set_settings_model(self.settings_model)
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_data_from_model()
    
    def _create_ui(self):
        """Create the node settings UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Create the table
        self.render_table = SimpleTableWidget()
        layout.addWidget(self.render_table)
        
        # Set up table headers
        headers = self.table_model.get_headers()
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(headers)
        
        # Connect table signals
        self.render_table.itemChanged.connect(self._on_table_item_changed)
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.table_model.dataChanged.connect(self._on_model_data_changed)
        
        # Connect settings model change signals to refresh table
        if self.settings_model:
            self.settings_model.jobSettingsChanged.connect(self._on_settings_changed)
            self.settings_model.machineSettingsChanged.connect(self._on_settings_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the table widget."""
        # Block signals during loading to prevent unwanted updates
        self.render_table.blockSignals(True)
        
        try:
            # Get data from model
            data = self.table_model.get_data()
            headers = self.table_model.get_headers()
            
            # Set table size
            self.render_table.setRowCount(len(data))
            
            # Populate table with raw values, but display effective values
            for row, row_data in enumerate(data):
                for col, header in enumerate(headers):
                    # Get raw cell value (may be None for inheritance)
                    raw_value = self.table_model.get_cell_value(row, col)
                    
                    # Create item with raw value for data storage
                    if raw_value is None:
                        # For None values, store empty string but mark as inherited
                        item = QtWidgets.QTableWidgetItem("")
                        item.setData(QtCore.Qt.UserRole, None)  # Store None in user data
                    else:
                        # For explicit values, store the actual value
                        item = QtWidgets.QTableWidgetItem(str(raw_value))
                        item.setData(QtCore.Qt.UserRole, raw_value)
                    
                    # Set display text to effective value (for inheritance display)
                    effective_value = self.table_model.get_effective_cell_value(row, col)
                    item.setText(str(effective_value))
                    
                    # Apply styling based on whether cell is overridden
                    self._apply_cell_styling(item, row, col)
                    
                    self.render_table.setItem(row, col, item)
            
            # Resize columns to content
            self.render_table.resizeColumnsToContents()
            
        finally:
            # Re-enable signals after loading is complete
            self.render_table.blockSignals(False)
    
    def _apply_cell_styling(self, item, row, col):
        """Apply styling to table cell items based on override status."""
        # Check if cell is overridden (has explicit value different from inherited)
        is_overridden = self.table_model.is_cell_overridden(row, col)
        
        if is_overridden:
            # Use highlight color background for override values (same as other highlightable widgets)
            from nk2dl.gui.panel.constants import Colors
            # White text for explicit values
            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            # Light blue background for highlighting (same as other widgets)
            item.setBackground(QtGui.QBrush(QtGui.QColor(Colors.WIDGET_HIGHLIGHT_COLOR)))
        else:
            # Default colors for inherited values
            # Default text color for inherited values
            item.setForeground(QtGui.QBrush())
            # Default background for inherited values
            item.setBackground(QtGui.QBrush())
    
    def _on_table_item_changed(self, item):
        """Handle table item changes and update the model."""
        if not item:
            return
        
        # Block signals to prevent recursive calls
        self.render_table.blockSignals(True)
        
        try:
            row = item.row()
            col = item.column()
            text_value = item.text()
            
            # Determine the value to store in the model
            if text_value.strip() == "":
                # Empty string means user wants to inherit from settings
                model_value = None
            else:
                # Non-empty string is an explicit value
                model_value = text_value
            
            # Update the model with the appropriate value (suppress signal to prevent full reload)
            self.table_model.set_cell_value(row, col, model_value, emit_signal=False)
            
            # Update the item's user data to reflect the stored value
            item.setData(QtCore.Qt.UserRole, model_value)
            
            # Update display text to show effective value (may be inherited)
            effective_value = self.table_model.get_effective_cell_value(row, col)
            item.setText(str(effective_value))
            
            # Refresh styling for this cell only
            self._apply_cell_styling(item, row, col)
            
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
    
    def _on_model_data_changed(self):
        """Handle model data changes."""
        # Refresh the table display
        self._load_data_from_model()
    
    def _on_settings_changed(self):
        """Handle settings model changes - refresh table to show updated inherited values."""
        # Update only inherited cells instead of reloading entire table
        self._update_inherited_cells()
    
    def _update_inherited_cells(self):
        """Update only cells that inherit from settings."""
        # Block signals to prevent recursive updates
        self.render_table.blockSignals(True)
        
        try:
            for row in range(self.render_table.rowCount()):
                for col in range(self.render_table.columnCount()):
                    # Check if this cell is inherited (not overridden)
                    if not self.table_model.is_cell_overridden(row, col):
                        item = self.render_table.item(row, col)
                        if item:
                            # Update display text with new inherited value
                            effective_value = self.table_model.get_effective_cell_value(row, col)
                            item.setText(str(effective_value))
                            
                            # Refresh styling
                            self._apply_cell_styling(item, row, col)
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)


class StandaloneNk2dlPanel(QtWidgets.QWidget):
    """Standalone version of the nk2dl panel for testing in Nuke."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"NK2DL Panel Test - {PYSIDE_VERSION} - Nuke {nuke.NUKE_VERSION_STRING}")
        self.setMinimumSize(1200, 800)
        
        # Create models
        self.settings_model = SettingsModel()
        self.table_model = TableDataModel()
        self.table_model.set_settings_model(self.settings_model)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Add title
        title = QtWidgets.QLabel("NK2DL Panel - Inheritance Test (Nuke)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add settings info
        settings_info = QtWidgets.QLabel(
            f"Settings: Priority={self.settings_model.get_job_setting('priority')}, "
            f"Chunk={self.settings_model.get_job_setting('chunk_size')}, "
            f"Pool={self.settings_model.get_machine_setting('pool')}, "
            f"UseGPU={self.settings_model.get_machine_setting('use_gpu')}"
        )
        settings_info.setStyleSheet("color: #888888; margin: 5px;")
        layout.addWidget(settings_info)
        
        # Create the node settings view (table)
        self.node_settings_view = SimpleNodeSettingsView(self.table_model, self.settings_model)
        layout.addWidget(self.node_settings_view)
        
        # Load test data
        self._load_test_data()
        
        # Add instructions
        instructions = QtWidgets.QLabel(
            "Instructions:\n"
            "• Bold text = Explicit values (overrides)\n"
            "• Normal text = Inherited from settings\n"
            "• Edit cells to test inheritance behavior\n"
            "• Empty cells should inherit from settings"
        )
        instructions.setStyleSheet("color: #666666; margin: 10px; font-size: 11px;")
        layout.addWidget(instructions)
    
    def _load_test_data(self):
        """Load test data to demonstrate inheritance."""
        test_data = [
            {
                # Row 1: Mix of explicit and inherited values
                "Order": "3999", 
                "Node": "Write4", 
                "Filename": "Some_path1_v002.%04d.exr", 
                "ChunkSize": None,  # Should inherit (normal text)
                "Frames": None,  # Should inherit 1001-2315 from job settings (normal text)
                "Priority": "75",  # Explicit override (bold)
                "NodesFrames": None,  # Should inherit (normal text)
                "TaskTimeout": None,  # Should inherit (normal text)
                "AutoTimeout": None,  # Should inherit (normal text)
                "RenderMode": "Full",  # Explicit (bold)
                "NukeX": None,  # Should inherit (normal text)
                "BatchMode": None,  # Should inherit (normal text)
                "ReloadPlugin": None,  # Should inherit (normal text)
                "Pool": "lighting",  # Explicit override (bold)
                "SecondaryPool": None,  # Should inherit (normal text)
                "Group": None,  # Should inherit (normal text)
                "Threads": None,  # Should inherit (normal text)
                "MinRam": None,  # Should inherit (normal text)
                "MaxRam": None,  # Should inherit (normal text)
                "UseGPU": "Yes",  # Explicit override (bold)
                "GPUId": None,  # Should inherit (normal text)
                "ConcurrentTasks": None,  # Should inherit (normal text)
                "WorkerTaskLimit": None,  # Should inherit (normal text)
                "MachineList": None,  # Should inherit (normal text)
                "Limits": None  # Should inherit (normal text)
            },
            {
                # Row 2: All explicit values (all should be bold)
                "Order": "3100", 
                "Node": "Write30", 
                "Filename": "Some_path3_v002.%04d.exr", 
                "ChunkSize": "3", 
                "Frames": "1500-2000",  # Custom frame range override (bold)
                "Priority": "40", 
                "NodesFrames": "No", 
                "TaskTimeout": "10", 
                "AutoTimeout": "No", 
                "RenderMode": "Proxy", 
                "NukeX": "No", 
                "BatchMode": "No", 
                "ReloadPlugin": "No",
                "Pool": "fx", 
                "SecondaryPool": "render", 
                "Group": "high_priority",
                "Threads": "4", 
                "MinRam": "16", 
                "MaxRam": "64", 
                "UseGPU": "No",
                "GPUId": "0", 
                "ConcurrentTasks": "2", 
                "WorkerTaskLimit": "No",
                "MachineList": "workstation01", 
                "Limits": "nuke_license:2"
            },
            {
                # Row 3: All inherited values (all should be normal text)
                "Order": "3050", 
                "Node": "Write27", 
                "Filename": "Some_path5_v002.%04d.exr", 
                "ChunkSize": None,
                "Frames": None,  # Should inherit 1001-2315 from job settings (normal text)
                "Priority": None,
                "NodesFrames": None,
                "TaskTimeout": None,
                "AutoTimeout": None,
                "RenderMode": None,
                "NukeX": None,
                "BatchMode": None,
                "ReloadPlugin": None,
                "Pool": None,
                "SecondaryPool": None,
                "Group": None,
                "Threads": None,
                "MinRam": None,
                "MaxRam": None,
                "UseGPU": None,
                "GPUId": None,
                "ConcurrentTasks": None,
                "WorkerTaskLimit": None,
                "MachineList": None,
                "Limits": None
            }
        ]
        
        self.table_model.set_data(test_data)
        
        print("Test data loaded:")
        print("Row 1: Mix of explicit (bold) and inherited (normal) values - Frames should inherit 1001-2315")
        print("Row 2: All explicit values (all should be bold) - Frames shows custom 1500-2000")
        print("Row 3: All inherited values (all should be normal text) - Frames should inherit 1001-2315")


def main():
    """Run the standalone Qt application in Nuke."""
    # Create and show the panel
    panel = StandaloneNk2dlPanel()
    panel.show()
    
    print(f"NK2DL Panel Test started using {PYSIDE_VERSION} in Nuke {nuke.NUKE_VERSION_STRING}")
    print("Check the table for inheritance behavior:")
    print("- Bold text should indicate explicit values")
    print("- Normal text should indicate inherited values")
    print("\nWindow should remain open. Close it manually when done testing.")
    
    # Store global reference to prevent garbage collection
    globals()['_test_panel'] = panel
    
    return panel  # Return the panel so it doesn't get garbage collected


if __name__ == "__main__":
    panel = main()
    
    # Keep the script alive in Nuke's terminal mode
    try:
        # This will keep the script running until interrupted
        import time
        print("Press Ctrl+C in terminal to exit, or close the window manually.")
        while True:
            # Process Qt events to keep the window responsive
            QtWidgets.QApplication.processEvents()
            time.sleep(0.1)  # Shorter sleep for better responsiveness
            
            # Check if window is still open
            if not panel.isVisible():
                print("Window closed, exiting...")
                break
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        # Keep panel reference alive even if there's an error
        pass 