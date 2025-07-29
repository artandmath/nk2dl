#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Phase 2 completion in Nuke environment.

This test validates that UI parameter alignment is complete and working
in the actual Nuke/PySide environment.
"""

import sys
import os
import time

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

# Import the panel components
from gui.panel.models import SettingsModel, TableDataModel
from gui.panel.constants import HeaderSettingsMapping
from common.config import config


def test_config_parameter_completeness():
    """Test that all required parameters are in the config system."""
    print("Testing Config Parameter Completeness")
    print("=" * 45)
    
    required_params = [
        'priority', 'chunk_size', 'pool', 'use_gpu', 'use_nuke_x',
        'batch_mode', 'reload_plugins', 'enable_auto_timeout',
        'use_node_frame_list', 'gpu_override', 'limit_worker_tasks',
        'limit_groups', 'stack_size', 'ram_use'
    ]
    
    missing_params = []
    for param in required_params:
        try:
            value = config.get(f'submission.{param}')
            print(f"  {param}: {value} ✓")
        except Exception as e:
            print(f"  {param}: MISSING - {e} ❌")
            missing_params.append(param)
    
    if not missing_params:
        print("✓ All required config parameters present")
        return True
    else:
        print(f"❌ Missing parameters: {missing_params}")
        return False


def test_settings_model_config_integration():
    """Test that SettingsModel properly integrates with config system."""
    print("\nTesting SettingsModel Config Integration")
    print("=" * 45)
    
    settings_model = SettingsModel()
    
    # Test a few key parameters
    test_params = [
        ('job', 'priority'),
        ('job', 'chunk_size'),
        ('job', 'enable_auto_timeout'),
        ('machine', 'pool'),
        ('machine', 'use_gpu'),
        ('machine', 'gpu_override'),
        ('machine', 'limit_worker_tasks'),
        ('machine', 'limit_groups')
    ]
    
    integration_working = True
    for setting_type, param in test_params:
        try:
            if setting_type == 'job':
                model_value = settings_model.get_job_setting(param)
            else:
                model_value = settings_model.get_machine_setting(param)
            
            config_value = config.get(f'submission.{param}')
            
            if model_value == config_value:
                print(f"  {setting_type}.{param}: {model_value} ✓")
            else:
                print(f"  {setting_type}.{param}: model={model_value}, config={config_value} ❌")
                integration_working = False
        except Exception as e:
            print(f"  {setting_type}.{param}: ERROR - {e} ❌")
            integration_working = False
    
    if integration_working:
        print("✓ SettingsModel config integration working")
    else:
        print("❌ SettingsModel config integration has issues")
    
    return integration_working


def test_table_model_inheritance():
    """Test table model inheritance with settings model."""
    print("\nTesting Table Model Inheritance")
    print("=" * 45)
    
    settings_model = SettingsModel()
    table_model = TableDataModel(settings_model)
    
    # Test data with inheritance scenarios
    test_data = [
        {
            "Node": "Write1",
            "Priority": None,  # Should inherit
            "ChunkSize": "5",  # Explicit override
            "Pool": None,      # Should inherit
            "UseGPU": None,    # Should inherit
            "AutoTimeout": None, # Should inherit
            "GPUId": "1",      # Explicit override
            "WorkerTaskLimit": None, # Should inherit
            "Limits": "maya,nuke" # Explicit override
        }
    ]
    
    table_model.set_data(test_data)
    headers = table_model.get_headers()
    
    test_headers = ["Priority", "ChunkSize", "Pool", "UseGPU", "AutoTimeout", "GPUId", "WorkerTaskLimit", "Limits"]
    inheritance_working = True
    
    for header in test_headers:
        if header in headers:
            col_idx = headers.index(header)
            raw_value = table_model.get_cell_value(0, col_idx)
            effective_value = table_model.get_effective_cell_value(0, col_idx)
            is_overridden = table_model.is_cell_overridden(0, col_idx)
            
            if raw_value is None:
                # Should be inherited
                if not is_overridden and effective_value:
                    print(f"  {header}: Inherits '{effective_value}' ✓")
                else:
                    print(f"  {header}: Inheritance failed ❌")
                    inheritance_working = False
            else:
                # Should be explicit
                if is_overridden and str(effective_value) == str(raw_value):
                    print(f"  {header}: Explicit '{effective_value}' ✓")
                else:
                    print(f"  {header}: Override failed ❌")
                    inheritance_working = False
    
    if inheritance_working:
        print("✓ Table model inheritance working")
    else:
        print("❌ Table model inheritance has issues")
    
    return inheritance_working


def test_parameter_alignment():
    """Test complete parameter alignment from UI to submission."""
    print("\nTesting Complete Parameter Alignment")
    print("=" * 45)
    
    # Test that HeaderSettingsMapping uses correct parameter names
    expected_mappings = {
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
    
    alignment_correct = True
    for header, expected_param in expected_mappings.items():
        setting_type, actual_param = HeaderSettingsMapping.get_setting_type_and_key(header)
        if actual_param == expected_param:
            print(f"  {header} -> {actual_param} ✓")
        else:
            print(f"  {header} -> {actual_param}, expected {expected_param} ❌")
            alignment_correct = False
    
    if alignment_correct:
        print("✓ Parameter alignment is correct")
    else:
        print("❌ Parameter alignment has issues")
    
    return alignment_correct


def main():
    """Run all Phase 2 completion tests."""
    print(f"NK2DL Phase 2 Completion Test - {PYSIDE_VERSION} in Nuke {nuke.NUKE_VERSION_STRING}")
    print("=" * 70)
    
    tests = [
        test_config_parameter_completeness,
        test_settings_model_config_integration,
        test_table_model_inheritance,
        test_parameter_alignment
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
    
    print("=" * 70)
    print(f"Phase 2 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 Phase 2: UI Parameter Standardization COMPLETE!")
        print("\nNext steps:")
        print("- Proceed to Phase 3: Node Override Integration")
        print("- All UI parameter names now align with submission parameters")
        print("- Config system serves as single source of truth for defaults")
        print("- Zero translation needed between UI and submission")
    else:
        print("❌ Phase 2 has remaining issues that need to be addressed")
    
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    
    # Keep the test results visible in Nuke terminal
    print("\nTest completed. Results shown above.")
    print("You can now proceed with Phase 3 or debug any failing tests.") 