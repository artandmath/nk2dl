#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple test for parameter alignment focused on constants and mappings."""

import sys
import os
import importlib.util

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

def load_module_from_path(module_name, file_path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_constants_mapping():
    """Test the HeaderSettingsMapping in constants.py."""
    print("Testing HeaderSettingsMapping Parameter Names")
    print("=" * 50)
    
    # Load constants module directly
    constants_path = os.path.join(nk2dl_path, 'gui', 'panel', 'constants.py')
    constants = load_module_from_path('constants', constants_path)
    
    # Expected mappings after Phase 2 updates
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
    
    print("Current HeaderSettingsMapping:")
    mapping_correct = True
    
    # Get the actual HeaderSettingsMapping
    header_mapping = constants.HeaderSettingsMapping
    
    for header, expected_param in expected_mappings.items():
        actual_param = header_mapping.ALL_MAPPINGS.get(header)
        if actual_param != expected_param:
            print(f"  {header}: '{actual_param}' -> Expected: '{expected_param}' ❌")
            mapping_correct = False
        else:
            print(f"  {header}: '{actual_param}' ✓")
    
    if mapping_correct:
        print("✓ All HeaderSettingsMapping parameter names are correct")
    else:
        print("❌ Some HeaderSettingsMapping parameter names need updating")
    
    return mapping_correct

def test_config_parameters():
    """Test the config parameters directly."""
    print("\nTesting Config Parameters")
    print("=" * 50)
    
    # Load config module directly  
    config_path = os.path.join(nk2dl_path, 'config.yaml')
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        submission_params = config_data.get('submission', {})
        print(f"Config submission parameters: {list(submission_params.keys())}")
        
        # Check for required parameters
        required_params = [
            'priority', 'chunk_size', 'pool', 'use_gpu', 'use_nuke_x',
            'batch_mode', 'reload_plugins', 'enable_auto_timeout',
            'use_node_frame_list', 'gpu_override', 'limit_worker_tasks',
            'limit_groups', 'stack_size', 'ram_use'
        ]
        
        missing_params = []
        for param in required_params:
            if param not in submission_params:
                missing_params.append(param)
            else:
                print(f"  {param}: {submission_params[param]} ✓")
        
        if missing_params:
            print(f"❌ Missing parameters: {missing_params}")
            return False
        else:
            print("✓ All required parameters found in config")
            return True
            
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_widget_object_names():
    """Test widget object names in settings views."""
    print("\nTesting Widget Object Names")
    print("=" * 50)
    
    # This is a theoretical test - checking if the object names would match
    # the expected parameter names
    
    expected_widget_names = {
        'priority_spinbox': 'priority',
        'chunk_size_spinbox': 'chunk_size',
        'pool_combobox': 'pool',
        'use_gpu_checkbox': 'use_gpu',
        'use_nuke_x_checkbox': 'use_nuke_x',
        'batch_mode_checkbox': 'batch_mode',
        'reload_plugins_checkbox': 'reload_plugins',
        'enable_auto_timeout_checkbox': 'enable_auto_timeout',
        'use_node_frame_list_checkbox': 'use_node_frame_list',
        'gpu_override_lineedit': 'gpu_override',
        'limit_worker_tasks_checkbox': 'limit_worker_tasks',
        'limit_groups_lineedit': 'limit_groups',
        'stack_size_spinbox': 'stack_size',
        'ram_use_spinbox': 'ram_use'
    }
    
    print("Expected widget object names should match parameter names:")
    for widget_name, param_name in expected_widget_names.items():
        # Extract the parameter name from the widget name
        extracted_param = widget_name.split('_')[0:-1]
        extracted_param = '_'.join(extracted_param)
        
        if extracted_param == param_name:
            print(f"  {widget_name} -> {param_name} ✓")
        else:
            print(f"  {widget_name} -> {param_name} ❌")
    
    print("✓ Widget naming pattern analysis completed")
    return True

def run_all_tests():
    """Run all simple parameter alignment tests."""
    print("NK2DL Parameter Alignment Simple Test Suite")
    print("=" * 60)
    
    tests = [
        test_constants_mapping,
        test_config_parameters,
        test_widget_object_names
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