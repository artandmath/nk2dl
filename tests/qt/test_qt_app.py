#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Standalone Qt application to test the nk2dl panel."""

import sys
import os

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide6"
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
    except ImportError:
        print("Error: Neither PySide6 nor PySide2 is available")
        sys.exit(1)

# Import the panel components
from gui.panel.models import TableDataModel, SettingsModel, GSVHierarchyModel
from gui.panel.views import NodeSettingsView


class StandaloneNk2dlPanel(QtWidgets.QWidget):
    """Standalone version of the nk2dl panel for testing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"NK2DL Panel Test - {PYSIDE_VERSION}")
        self.setMinimumSize(1200, 800)
        
        # Create models
        self.settings_model = SettingsModel()
        self.table_model = TableDataModel()
        self.table_model.set_settings_model(self.settings_model)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Add title
        title = QtWidgets.QLabel("NK2DL Panel - Inheritance Test")
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
        self.node_settings_view = NodeSettingsView(self.table_model, self.settings_model)
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
                "Chunk": None,  # Should inherit (normal text)
                "Frames": "1350-1650",  # Explicit (bold)
                "Priority": "75",  # Explicit override (bold)
                "NodesFrames": None,  # Should inherit (normal text)
                "TaskTimeout": None,  # Should inherit (normal text)
                "AutoTimeout": None,  # Should inherit (normal text)
                "RenderMode": "Full",  # Explicit (bold)
                "NukeX": None,  # Should inherit (normal text)
                "BatchMode": None,  # Should inherit (normal text)
                "Reloadplugin": None,  # Should inherit (normal text)
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
                "Chunk": "3", 
                "Frames": "1001-2315", 
                "Priority": "40", 
                "NodesFrames": "No", 
                "TaskTimeout": "10", 
                "AutoTimeout": "No", 
                "RenderMode": "Proxy", 
                "NukeX": "No", 
                "BatchMode": "No", 
                "Reloadplugin": "No",
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
                "Chunk": None,
                "Frames": "1570-1620", 
                "Priority": None,
                "NodesFrames": None,
                "TaskTimeout": None,
                "AutoTimeout": None,
                "RenderMode": None,
                "NukeX": None,
                "BatchMode": None,
                "Reloadplugin": None,
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
        print("Row 1: Mix of explicit (bold) and inherited (normal) values")
        print("Row 2: All explicit values (all should be bold)")
        print("Row 3: All inherited values (all should be normal text)")


def main():
    """Run the standalone Qt application."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("NK2DL Panel Test")
    app.setApplicationVersion("1.0")
    
    # Create and show the panel
    panel = StandaloneNk2dlPanel()
    panel.show()
    
    print(f"NK2DL Panel Test started using {PYSIDE_VERSION}")
    print("Check the table for inheritance behavior:")
    print("- Bold text should indicate explicit values")
    print("- Normal text should indicate inherited values")
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 