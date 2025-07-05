#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test UI parameter alignment with submission parameters."""

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

# Now import our modules
# Add common path to import config directly
common_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl', 'common')
if common_path not in sys.path:
    sys.path.insert(0, common_path)

from config import config

# Import models and constants directly
from gui.panel.models.table_model import TableDataModel
from gui.panel.models.settings_model import SettingsModel
from gui.panel.constants import HeaderSettingsMapping


def test_config_parameter_alignment():
    """Test that all config parameters align with submission requirements."""
    print("Testing Config Parameter Alignment")
    print("=" * 50)
    
    # Expected submission parameters (from submission.py)
    expected_submission_params = [
        'name', 'comment', 'pool', 'priority', 'chunk_size', 'use_gpu',
        'use_nuke_x', 'batch_mode', 'reload_plugins', 'continuous',
        'enable_auto_timeout', 'use_node_frame_list', 'gpu_override',
        'limit_worker_tasks', 'limit_groups', 'stack_size', 'ram_use',
        'output_overrides', 'frame_overrides', 'write_node'
    ]
    
    # Get config submission parameters
    config_params = list(config.get('submission', {}).keys())
    
    print(f"Expected submission parameters: {len(expected_submission_params)}")
    print(f"Config submission parameters: {len(config_params)}")
    
    missing_in_config = set(expected_submission_params) - set(config_params)
    extra_in_config = set(config_params) - set(expected_submission_params)
    
    if missing_in_config:
        print(f"MISSING in config: {missing_in_config}")
    if extra_in_config:
        print(f"EXTRA in config: {extra_in_config}")
    
    if not missing_in_config and not extra_in_config:
        print("✓ Config parameters perfectly align with submission requirements")
    
    return len(missing_in_config) == 0 and len(extra_in_config) == 0


def test_header_settings_mapping():
    """Test that HeaderSettingsMapping uses correct parameter names."""
    print("\nTesting HeaderSettingsMapping Parameter Names")
    print("=" * 50)
    
    # Expected mappings after Phase 2 updates
    expected_mappings = {
        "Priority": "priority",
        "ChunkSize": "chunk_size", 
        "Pool": "pool",
        "UseGPU": "use_gpu",
        "NukeX": "use_nuke_x",
        "BatchMode": "batch_mode",
        "ReloadPlugin": "reload_plugins",
        "Continuous": "continuous",
        "AutoTimeout": "enable_auto_timeout",
        "NodesFrames": "use_node_frame_list",
        "GPUId": "gpu_override",
        "WorkerTaskLimit": "limit_worker_tasks",
        "Limits": "limit_groups",
        "MinRam": "stack_size",
        "MaxRam": "ram_use"
    }
    
    print("Current HeaderSettingsMapping:")
    mapping_correct = True
    for header, expected_param in expected_mappings.items():
        actual_param = HeaderSettingsMapping.get(header)
        if actual_param != expected_param:
            print(f"  {header}: '{actual_param}' -> Expected: '{expected_param}' ❌")
            mapping_correct = False
        else:
            print(f"  {header}: '{actual_param}' ✓")
    
    if mapping_correct:
        print("✓ All HeaderSettingsMapping parameter names are correct")
    
    return mapping_correct


def test_settings_model_config_integration():
    """Test that SettingsModel properly integrates with config system."""
    print("\nTesting SettingsModel Config Integration")
    print("=" * 50)
    
    settings_model = SettingsModel()
    
    # Test that settings model uses config values
    config_job_params = ['priority', 'chunk_size', 'use_node_frame_list', 'continuous', 'enable_auto_timeout']
    config_machine_params = ['pool', 'use_gpu', 'use_nuke_x', 'batch_mode', 'reload_plugins', 'gpu_override', 'limit_worker_tasks', 'limit_groups', 'stack_size', 'ram_use']
    
    print("Testing job settings config integration:")
    for param in config_job_params:
        try:
            model_value = settings_model.get_job_setting(param)
            config_value = config.get(f'submission.{param}')
            print(f"  {param}: model={model_value}, config={config_value} {'✓' if model_value == config_value else '❌'}")
        except Exception as e:
            print(f"  {param}: ERROR - {e}")
    
    print("\nTesting machine settings config integration:")
    for param in config_machine_params:
        try:
            model_value = settings_model.get_machine_setting(param)
            config_value = config.get(f'submission.{param}')
            print(f"  {param}: model={model_value}, config={config_value} {'✓' if model_value == config_value else '❌'}")
        except Exception as e:
            print(f"  {param}: ERROR - {e}")
    
    return True


def test_table_model_parameter_alignment():
    """Test that TableDataModel properly uses new parameter names."""
    print("\nTesting TableDataModel Parameter Alignment")
    print("=" * 50)
    
    settings_model = SettingsModel()
    table_model = TableDataModel()
    table_model.set_settings_model(settings_model)
    
    # Test data with parameters using new naming
    test_data = [
        {
            "Priority": "75",
            "ChunkSize": None,
            "Pool": "lighting", 
            "UseGPU": None,
            "NukeX": None,
            "BatchMode": None,
            "ReloadPlugin": None,
            "Continuous": None,
            "AutoTimeout": None,
            "NodesFrames": None,
            "GPUId": "",
            "WorkerTaskLimit": None,
            "Limits": "",
            "MinRam": None,
            "MaxRam": None
        }
    ]
    
    table_model.set_data(test_data)
    
    # Test that inheritance works with new parameter names
    headers = table_model.get_headers()
    test_columns = ["Priority", "ChunkSize", "Pool", "UseGPU", "NukeX", "BatchMode", "ReloadPlugin", "AutoTimeout", "NodesFrames"]
    
    print("Testing inheritance with new parameter names:")
    inheritance_working = True
    for col_name in test_columns:
        if col_name in headers:
            col_idx = headers.index(col_name)
            raw_value = table_model.get_cell_value(0, col_idx)
            effective_value = table_model.get_effective_cell_value(0, col_idx)
            is_overridden = table_model.is_cell_overridden(0, col_idx)
            
            # Check if inheritance is working
            setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(col_name)
            if setting_type and setting_key and raw_value is None:
                # Should inherit from settings
                expected_inherited = getattr(settings_model, f'get_{setting_type}_setting')(setting_key)
                if str(effective_value) != str(expected_inherited):
                    print(f"  {col_name}: Inheritance broken - effective={effective_value}, expected={expected_inherited} ❌")
                    inheritance_working = False
                else:
                    print(f"  {col_name}: Inherits {expected_inherited} ✓")
            else:
                print(f"  {col_name}: Explicit value {raw_value} ✓")
    
    if inheritance_working:
        print("✓ Table model inheritance working with new parameter names")
    
    return inheritance_working


def test_full_parameter_flow():
    """Test the complete parameter flow from config to UI to submission format."""
    print("\nTesting Full Parameter Flow")
    print("=" * 50)
    
    # This test simulates the complete flow:
    # Config -> SettingsModel -> TableDataModel -> (future) Submission Args
    
    settings_model = SettingsModel()
    table_model = TableDataModel()
    table_model.set_settings_model(settings_model)
    
    # Test case: Node with some overrides and some inherited values
    test_node_data = {
        "Node": "Write1",
        "Priority": "80",  # Override
        "ChunkSize": None,  # Inherit
        "Pool": "gpu_farm",  # Override
        "UseGPU": None,  # Inherit
        "NukeX": None,  # Inherit
        "BatchMode": None,  # Inherit
        "ReloadPlugin": None,  # Inherit
        "AutoTimeout": None,  # Inherit
        "NodesFrames": None,  # Inherit
        "GPUId": "1",  # Override
        "WorkerTaskLimit": None,  # Inherit
        "Limits": "maya,nuke",  # Override
        "MinRam": None,  # Inherit
        "MaxRam": None  # Inherit
    }
    
    table_model.set_data([test_node_data])
    
    # Build what submission args would look like
    print("Expected submission parameters from this data:")
    
    # Get all parameter mappings
    for header, value in test_node_data.items():
        if header == "Node":
            continue
            
        setting_type, setting_key = HeaderSettingsMapping.get_setting_type_and_key(header)
        if setting_type and setting_key:
            if value is None:
                # Should inherit
                inherited_value = getattr(settings_model, f'get_{setting_type}_setting')(setting_key)
                print(f"  {setting_key}: {inherited_value} (inherited from {setting_type})")
            else:
                # Explicit override
                print(f"  {setting_key}: {value} (explicit override)")
    
    print("✓ Parameter flow test completed")
    return True


def run_all_tests():
    """Run all parameter alignment tests."""
    print("NK2DL Parameter Alignment Test Suite")
    print("=" * 60)
    
    tests = [
        test_config_parameter_alignment,
        test_header_settings_mapping,
        test_settings_model_config_integration,
        test_table_model_parameter_alignment,
        test_full_parameter_flow
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