#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug the styling logic."""

import sys
import os

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

# Mock Qt classes for testing without PySide
import types

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

class MockQtCore:
    class QObject(MockQObject):
        pass
    Signal = lambda *args: MockSignal()

# Inject mock Qt into sys.modules
mock_pyside2 = types.ModuleType('PySide2')
mock_pyside2.QtCore = MockQtCore()
sys.modules['PySide2'] = mock_pyside2
sys.modules['PySide2.QtCore'] = mock_pyside2.QtCore

mock_pyside6 = types.ModuleType('PySide6')
mock_pyside6.QtCore = MockQtCore()
sys.modules['PySide6'] = mock_pyside6
sys.modules['PySide6.QtCore'] = mock_pyside6.QtCore

# Import models
from gui.panel.models import TableDataModel, SettingsModel


def debug_styling_logic():
    """Debug the styling logic by simulating what the view does."""
    print("Debugging Styling Logic")
    print("=" * 30)
    
    # Create models
    settings_model = SettingsModel()
    table_model = TableDataModel()
    table_model.set_settings_model(settings_model)
    
    # Test data - same as the working inheritance test
    test_data = [
        {
            "Order": "3999",  # Explicit - should be bold
            "Node": "Write4",  # Explicit - should be bold
            "Priority": "75",  # Explicit - should be bold  
            "ChunkSize": None,  # Inherited - should be normal (updated from "Chunk")
            "NodesFrames": None,  # Inherited - should be normal
            "Pool": "lighting",  # Explicit - should be bold
            "UseGPU": None,  # Inherited - should be normal
        }
    ]
    
    table_model.set_data(test_data)
    
    # Simulate what the view does in _load_data_from_model
    print("\nSimulating View Logic:")
    print("-" * 50)
    
    headers = table_model.get_headers()
    test_columns = ["Order", "Node", "Priority", "ChunkSize", "NodesFrames", "Pool", "UseGPU"]
    
    print("\nStyling Debug Results:")
    print("-" * 80)
    print(f"{'Column':<12} | {'Raw Value':<8} | {'Display':<8} | {'Override':<5} | {'Style'}")
    print("-" * 80)
    
    for col_name in test_columns:
        if col_name in headers:
            col = headers.index(col_name)
            row = 0
            
            # Get raw cell value (may be None for inheritance)
            raw_value = table_model.get_cell_value(row, col)
            
            # Get effective value for display
            effective_value = table_model.get_effective_cell_value(row, col)
            
            # Check if overridden (this determines styling)
            is_overridden = table_model.is_cell_overridden(row, col)
            
            # Determine expected styling
            expected_style = "BOLD" if is_overridden else "NORMAL"
            
            print(f"{col_name:<12} | Raw: {str(raw_value):<8} | Display: {str(effective_value):<8} | Override: {str(is_overridden):<5} | Style: {expected_style}")
    
    print("\nExpected Results:")
    print("- Order, Node, Priority, Pool: Should be BOLD (explicit values)")
    print("- ChunkSize, NodesFrames, UseGPU: Should be NORMAL (inherited values)")
    
    # Test the specific case that might be causing issues
    print("\nDetailed Analysis:")
    print("-" * 30)
    
    for col_name in ["ChunkSize", "Priority"]:
        if col_name in headers:
            col = headers.index(col_name)
            row = 0
            
            raw_value = table_model.get_cell_value(row, col)
            effective_value = table_model.get_effective_cell_value(row, col)
            is_overridden = table_model.is_cell_overridden(row, col)
            
            print(f"\n{col_name} Analysis:")
            print(f"  Raw value: {repr(raw_value)}")
            print(f"  Effective value: {repr(effective_value)}")
            print(f"  Is overridden: {is_overridden}")
            print(f"  Expected style: {'BOLD' if is_overridden else 'NORMAL'}")
            
            # Check the data structure
            header = headers[col]
            row_data = table_model._data[row]
            print(f"  Key in row data: {header in row_data}")
            if header in row_data:
                print(f"  Value in row data: {repr(row_data[header])}")
            else:
                print(f"  Key missing from row data")


if __name__ == "__main__":
    debug_styling_logic() 