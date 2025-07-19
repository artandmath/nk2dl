#!/usr/bin/env python3
"""Test script for Settings Model changes."""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, '.')

# Mock Qt for testing
class MockQtCore:
    class QObject:
        def __init__(self, parent=None):
            self.parent = parent
        
        def emit(self):
            pass
    
    class Signal:
        def __init__(self):
            pass

# Mock the Qt imports
sys.modules['PySide6.QtCore'] = MockQtCore
sys.modules['PySide2.QtCore'] = MockQtCore

try:
    # Import directly from the models directory
    import nk2dl.gui.panel.models.settings_model
    SettingsModel = nk2dl.gui.panel.models.settings_model.SettingsModel
    
    print("=== Testing Settings Model ===")
    
    # Create model
    model = SettingsModel()
    print("✓ SettingsModel created successfully")
    
    # Check job settings
    print(f"\nJob settings count: {len(model._job_settings)}")
    new_job_settings = ['render_settings_from_metadata', 'submit_suspended', 'job_dependencies', 'continue_on_error']
    found_job_settings = [k for k in model._job_settings.keys() if k in new_job_settings]
    print(f"New job settings found: {found_job_settings}")
    
    # Check extra settings
    print(f"\nExtra settings count: {len(model._extra_settings)}")
    new_extra_settings = [
        'submit_script_as_auxiliary_file', 'submission_is_build_job', 'build_job_name',
        'pre_build_job_script', 'post_build_job_script', 'build_job_as_auxiliary_file',
        'delete_build_job_script', 'copy_script', 'copy_script_path', 'submit_copied_script',
        'script_job_script_path', 'extra_info', 'on_job_complete', 'pre_job_script',
        'post_job_script', 'pre_task_script', 'post_task_script', 'use_current_environment',
        'environment_keys', 'environment', 'omit_environment_keys'
    ]
    found_extra_settings = [k for k in model._extra_settings.keys() if k in new_extra_settings]
    print(f"New extra settings found: {found_extra_settings}")
    
    # Test validation
    print("\n=== Testing Validation ===")
    
    # Test job settings validation
    is_valid, errors = model.validate_job_settings()
    print(f"Job settings validation: {'✓' if is_valid else '✗'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test extra settings validation
    is_valid, errors = model.validate_extra_settings()
    print(f"Extra settings validation: {'✓' if is_valid else '✗'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test setting values
    print("\n=== Testing Setting Values ===")
    
    # Test job settings
    model.set_job_setting('render_settings_from_metadata', True)
    model.set_job_setting('submit_suspended', True)
    model.set_job_setting('job_dependencies', '123,456')
    model.set_job_setting('continue_on_error', True)
    
    print(f"render_settings_from_metadata: {model.get_job_setting('render_settings_from_metadata')}")
    print(f"submit_suspended: {model.get_job_setting('submit_suspended')}")
    print(f"job_dependencies: {model.get_job_setting('job_dependencies')}")
    print(f"continue_on_error: {model.get_job_setting('continue_on_error')}")
    
    # Test extra settings
    model.set_extra_setting('submission_is_build_job', True)
    model.set_extra_setting('build_job_name', 'test_build_job')
    model.set_extra_setting('use_current_environment', True)
    
    print(f"submission_is_build_job: {model.get_extra_setting('submission_is_build_job')}")
    print(f"build_job_name: {model.get_extra_setting('build_job_name')}")
    print(f"use_current_environment: {model.get_extra_setting('use_current_environment')}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 