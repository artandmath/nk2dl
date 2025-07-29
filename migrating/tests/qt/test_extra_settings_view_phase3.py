#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for ExtraSettingsView Phase 3 additions.

This test verifies that the new extra settings UI components work correctly.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_extra_settings_view_phase3.py
"""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui

def main():
    """Test the ExtraSettingsView with new extra settings."""
    print("=== Testing ExtraSettingsView Phase 3 ===")
    
    try:
        # Import the ExtraSettingsView and SettingsModel
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        from nk2dl.gui.panel.views.extra_settings_view import ExtraSettingsView
        
        # Create the settings model
        print("Creating SettingsModel...")
        settings_model = SettingsModel()
        print("✓ SettingsModel created successfully")
        
        # Create the extra settings view
        print("Creating ExtraSettingsView...")
        extra_settings_view = ExtraSettingsView(settings_model)
        print("✓ ExtraSettingsView created successfully")
        
        # Show the view
        extra_settings_view.show()
        print("✓ ExtraSettingsView displayed")
        
        # Test setting values programmatically
        print("\n=== Testing New Extra Settings ===")
        
        # Test script submission settings
        settings_model.set_extra_setting('submit_script_as_auxiliary_file', 'Yes')
        settings_model.set_extra_setting('copy_script', 'No')
        settings_model.set_extra_setting('copy_script_path', '/path/to/copy')
        settings_model.set_extra_setting('submit_copied_script', 'Yes')
        
        # Test build job settings
        settings_model.set_extra_setting('submission_is_build_job', True)
        settings_model.set_extra_setting('build_job_name', 'TestBuildJob')
        settings_model.set_extra_setting('pre_build_job_script', 'pre_build.py')
        settings_model.set_extra_setting('post_build_job_script', 'post_build.py')
        settings_model.set_extra_setting('build_job_as_auxiliary_file', 'No')
        settings_model.set_extra_setting('delete_build_job_script', 'Yes')
        
        # Test script job settings
        settings_model.set_extra_setting('script_job_script_path', '/path/to/script.py')
        
        # Test job info settings
        settings_model.set_extra_setting('extra_info', 'info1,info2,info3')
        settings_model.set_extra_setting('on_job_complete', 'complete.py')
        settings_model.set_extra_setting('pre_job_script', 'pre_job.py')
        settings_model.set_extra_setting('post_job_script', 'post_job.py')
        settings_model.set_extra_setting('pre_task_script', 'pre_task.py')
        settings_model.set_extra_setting('post_task_script', 'post_task.py')
        
        # Test environment variables settings
        settings_model.set_extra_setting('use_current_environment', True)
        settings_model.set_extra_setting('environment_keys', 'PATH,HOME,USER')
        settings_model.set_extra_setting('environment', 'KEY1=value1,KEY2=value2')
        settings_model.set_extra_setting('omit_environment_keys', 'TEMP,TMP')
        
        print("✓ All extra settings set successfully")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_widget'] = extra_settings_view
        globals()['_test_model'] = settings_model
        
        print("\n✓ All tests passed! ExtraSettingsView is ready for manual testing.")
        print("You can now interact with the new extra settings sections:")
        print("- Script Submission (submit_script_as_auxiliary_file, copy_script, etc.)")
        print("- Build Job (submission_is_build_job, build_job_name, etc.)")
        print("- Script Job (script_job_script_path)")
        print("- Job Info (extra_info, on_job_complete, etc.)")
        print("- Environment Variables (use_current_environment, environment_keys, etc.)")
        
        # Keep the window alive
        try:
            while True:
                QtWidgets.QApplication.processEvents()
                time.sleep(0.001)
                if not extra_settings_view.isVisible():
                    break
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        
        return extra_settings_view
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 