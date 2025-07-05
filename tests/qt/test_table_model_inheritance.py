#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test table model inheritance logic with current parameter names."""

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
    
    # Qt enums
    class Qt:
        AscendingOrder = 0
        DescendingOrder = 1

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

# Now import our modules
from gui.panel.models.table_model import TableDataModel
from gui.panel.models.settings_model import SettingsModel
from gui.panel.constants import HeaderSettingsMapping


def test_table_model_inheritance():
    """Test that table model inheritance works with current parameter names."""
    print("Testing Table Model Inheritance Logic")
    print("=" * 50)
    
    # Create models
    settings_model = SettingsModel()
    table_model = TableDataModel(settings_model)
    
    # Get some example parameter mappings to test
    test_headers = ["Priority", "ChunkSize", "Pool", "UseGPU", "NukeX", "BatchMode", 
                   "ReloadPlugin", "AutoTimeout", "NodesFrames", "GPUId", 
                   "WorkerTaskLimit", "Limits", "MinRam", "MaxRam"]
    
    print("Testing HeaderSettingsMapping integration:")
    for header in test_headers:
        setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(header)
        if setting_type and setting_key:
            # Get setting value from model
            if setting_type == "job":
                setting_value = settings_model.get_job_setting(setting_key)
            elif setting_type == "machine":
                setting_value = settings_model.get_machine_setting(setting_key)
            else:
                setting_value = None
            
            print(f"  {header} -> {setting_type}.{setting_key} = {setting_value}")
        else:
            print(f"  {header} -> No mapping")
    
    # Test inheritance behavior
    print(f"\nTesting inheritance behavior:")
    
    # Create test data with some None values (should inherit)
    test_data = [
        {
            "Node": "Write1",
            "Priority": None,  # Should inherit
            "ChunkSize": "5",  # Explicit override
            "Pool": None,      # Should inherit
            "UseGPU": None,    # Should inherit
            "NukeX": None,     # Should inherit
            "BatchMode": None, # Should inherit
            "AutoTimeout": None, # Should inherit
            "NodesFrames": None, # Should inherit
            "GPUId": "1",      # Explicit override
            "WorkerTaskLimit": None, # Should inherit
            "Limits": "maya,nuke",   # Explicit override
            "MinRam": None,    # Should inherit
            "MaxRam": None     # Should inherit
        }
    ]
    
    table_model.set_data(test_data)
    
    # Get headers
    headers = table_model.get_headers()
    
    # Test inheritance for each column
    inheritance_working = True
    for header in test_headers:
        if header in headers:
            col_idx = headers.index(header)
            
            # Test effective cell value (includes inheritance)
            raw_value = table_model.get_cell_value(0, col_idx)
            effective_value = table_model.get_effective_cell_value(0, col_idx)
            is_overridden = table_model.is_cell_overridden(0, col_idx)
            
            # Get expected inherited value
            setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(header)
            if setting_type and setting_key:
                if setting_type == "job":
                    expected_setting = settings_model.get_job_setting(setting_key)
                elif setting_type == "machine":
                    expected_setting = settings_model.get_machine_setting(setting_key)
                else:
                    expected_setting = None
                
                # Convert to display format
                if header in HeaderSettingsMapping.BOOLEAN_COLUMNS:
                    expected_display = "Yes" if expected_setting else "No"
                elif header in HeaderSettingsMapping.NUMERIC_COLUMNS:
                    expected_display = str(expected_setting) if expected_setting is not None else ""
                else:
                    expected_display = str(expected_setting) if expected_setting else ""
                
                if raw_value is None:
                    # Should inherit
                    if str(effective_value) == str(expected_display) and not is_overridden:
                        print(f"  {header}: Inherits '{effective_value}' ✓")
                    else:
                        print(f"  {header}: Inheritance failed - got '{effective_value}', expected '{expected_display}', override={is_overridden} ❌")
                        inheritance_working = False
                else:
                    # Should be explicit
                    if str(effective_value) == str(raw_value) and is_overridden:
                        print(f"  {header}: Explicit '{effective_value}' ✓")
                    else:
                        print(f"  {header}: Override failed - got '{effective_value}', raw '{raw_value}', override={is_overridden} ❌")
                        inheritance_working = False
            else:
                print(f"  {header}: No inheritance mapping ⚪")
    
    if inheritance_working:
        print("\n✓ Table model inheritance is working correctly")
    else:
        print("\n❌ Table model inheritance has issues")
    
    return inheritance_working


def test_parameter_alignment_integration():
    """Test full parameter alignment integration."""
    print("\n" + "=" * 50)
    print("Testing Full Parameter Alignment Integration")
    print("=" * 50)
    
    # Create models
    settings_model = SettingsModel()
    table_model = TableDataModel(settings_model)
    
    # Test that parameter names flow correctly through the system
    test_params = {
        "Priority": "priority",
        "ChunkSize": "chunk_size", 
        "Pool": "pool",
        "UseGPU": "use_gpu",
        "NukeX": "use_nuke_x",
        "BatchMode": "batch_mode",
        "ReloadPlugin": "reload_plugins",
        "AutoTimeout": "enable_auto_timeout",
        "NodesFrames": "use_node_frame_list",
        "GPUId": "gpu_override",
        "WorkerTaskLimit": "limit_worker_tasks",
        "Limits": "limit_groups",
        "MinRam": "stack_size",
        "MaxRam": "ram_use"
    }
    
    print("Parameter flow test:")
    flow_working = True
    for header, expected_param in test_params.items():
        setting_type, actual_param = HeaderSettingsMapping.get_setting_type_and_key(header)
        if actual_param == expected_param:
            print(f"  {header} -> {actual_param} ✓")
        else:
            print(f"  {header} -> {actual_param}, expected {expected_param} ❌")
            flow_working = False
    
    if flow_working:
        print("✓ Parameter alignment integration is working correctly")
    else:
        print("❌ Parameter alignment integration has issues")
    
    return flow_working


def run_all_tests():
    """Run all table model inheritance tests."""
    print("Table Model Inheritance Test Suite")
    print("=" * 60)
    
    tests = [
        test_table_model_inheritance,
        test_parameter_alignment_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 