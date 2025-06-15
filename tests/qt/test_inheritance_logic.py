#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test inheritance logic without UI dependencies."""

import sys
import os

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

# Mock Qt classes for testing without PySide
class MockQObject:
    def __init__(self, parent=None):
        pass

class MockSignal:
    def emit(self):
        pass
    def connect(self, slot):
        pass
    def disconnect(self, slot=None):
        pass

# Mock QtCore
class MockQtCore:
    class QObject(MockQObject):
        pass
    
    # Signal should be a callable that returns a MockSignal instance
    Signal = lambda *args: MockSignal()

# Inject mock Qt into sys.modules before importing anything
import types
mock_pyside2 = types.ModuleType('PySide2')
mock_pyside2.QtCore = MockQtCore()
sys.modules['PySide2'] = mock_pyside2
sys.modules['PySide2.QtCore'] = mock_pyside2.QtCore

mock_pyside6 = types.ModuleType('PySide6')
mock_pyside6.QtCore = MockQtCore()
sys.modules['PySide6'] = mock_pyside6
sys.modules['PySide6.QtCore'] = mock_pyside6.QtCore

# Now import our models
from gui.panel.models import TableDataModel, SettingsModel
from gui.panel.constants import HeaderSettingsMapping


def test_inheritance_logic():
    """Test the inheritance logic."""
    print("Testing NK2DL Inheritance Logic")
    print("=" * 40)
    
    # Create models
    settings_model = SettingsModel()
    table_model = TableDataModel()
    table_model.set_settings_model(settings_model)
    
    # Print default settings
    print("\nDefault Settings:")
    print(f"  Priority: {settings_model.get_job_setting('priority')}")
    print(f"  Chunk Size: {settings_model.get_job_setting('chunk_size')}")
    print(f"  Pool: {settings_model.get_machine_setting('pool')}")
    print(f"  Use GPU: {settings_model.get_machine_setting('use_gpu')}")
    print(f"  Use Node Frame List: {settings_model.get_job_setting('use_node_frame_list')}")
    
    # Test data with mix of explicit and inherited values
    test_data = [
        {
            "Order": "3999",  # No mapping - should be explicit
            "Node": "Write4",  # No mapping - should be explicit
            "Filename": "test.exr",  # No mapping - should be explicit
            "Chunk": None,  # Maps to chunk_size - should inherit
            "Priority": "75",  # Maps to priority - explicit override
            "NodesFrames": None,  # Maps to use_node_frame_list - should inherit
            "Pool": "lighting",  # Maps to pool - explicit override
            "UseGPU": None,  # Maps to use_gpu - should inherit
        }
    ]
    
    table_model.set_data(test_data)
    
    # Test each column
    headers = table_model.get_headers()
    test_columns = ["Order", "Node", "Filename", "Priority", "ChunkSize", "NodesFrames", "Pool", "UseGPU"]
    
    print("\nInheritance Test Results:")
    print("-" * 60)
    print(f"{'Column':<15} {'Raw Value':<12} {'Effective':<12} {'Override':<10} {'Expected'}")
    print("-" * 60)
    
    for col_name in test_columns:
        if col_name in headers:
            col_idx = headers.index(col_name)
            raw_value = table_model.get_cell_value(0, col_idx)
            effective_value = table_model.get_effective_cell_value(0, col_idx)
            is_overridden = table_model.is_cell_overridden(0, col_idx)
            
            # Determine expected behavior
            setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(col_name)
            if setting_type and setting_key:
                if raw_value is None:
                    expected = "Inherit"
                else:
                    expected = "Override"
            else:
                expected = "Override" if raw_value is not None else "N/A"
            
            print(f"{col_name:<15} {str(raw_value):<12} {str(effective_value):<12} {str(is_overridden):<10} {expected}")
    
    print("\nMapping Test:")
    print("-" * 40)
    for col_name in test_columns:
        setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(col_name)
        if setting_type and setting_key:
            print(f"{col_name} -> {setting_type}.{setting_key}")
        else:
            print(f"{col_name} -> No mapping")
    
    print("\nExpected Results:")
    print("- Chunk: Should inherit chunk_size (1) and show normal text")
    print("- Priority: Should show explicit value (75) and show bold text")
    print("- NodesFrames: Should inherit use_node_frame_list (False->No) and show normal text")
    print("- Pool: Should show explicit value (lighting) and show bold text")
    print("- UseGPU: Should inherit use_gpu (False->No) and show normal text")
    print("- Order/Node/Filename: Should show explicit values and show bold text (no inheritance)")


if __name__ == "__main__":
    test_inheritance_logic() 