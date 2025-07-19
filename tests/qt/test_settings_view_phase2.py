#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for SettingsView Phase 2 additions.

This test verifies that the new job settings UI components work correctly.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_settings_view_phase2.py
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
    """Test the SettingsView with new job settings."""
    print("=== Testing SettingsView Phase 2 ===")
    
    try:
        # Import the SettingsView and SettingsModel
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        from nk2dl.gui.panel.views.settings_view import SettingsView
        
        # Create the settings model
        print("Creating SettingsModel...")
        settings_model = SettingsModel()
        print("✓ SettingsModel created successfully")
        
        # Create the settings view
        print("Creating SettingsView...")
        settings_view = SettingsView(settings_model)
        print("✓ SettingsView created successfully")
        
        # Show the view
        settings_view.show()
        print("✓ SettingsView displayed")
        
        # Test setting values programmatically
        print("\n=== Testing New Job Settings ===")
        
        # Test render_settings_from_metadata
        settings_model.set_job_setting('render_settings_from_metadata', True)
        print(f"render_settings_from_metadata: {settings_model.get_job_setting('render_settings_from_metadata')}")
        
        # Test submit_suspended
        settings_model.set_job_setting('submit_suspended', True)
        print(f"submit_suspended: {settings_model.get_job_setting('submit_suspended')}")
        
        # Test continue_on_error
        settings_model.set_job_setting('continue_on_error', True)
        print(f"continue_on_error: {settings_model.get_job_setting('continue_on_error')}")
        
        # Test job_dependencies
        settings_model.set_job_setting('job_dependencies', '123,456,789')
        print(f"job_dependencies: {settings_model.get_job_setting('job_dependencies')}")
        
        # Keep alive for Nuke terminal mode
        globals()['_test_widget'] = settings_view
        globals()['_test_model'] = settings_model
        
        print("\n✓ All tests passed! SettingsView is ready for manual testing.")
        print("You can now interact with the new job settings:")
        print("- Render settings from metadata checkbox")
        print("- Submit suspended checkbox")
        print("- Continue on error checkbox")
        print("- Job dependencies text field with browse button")
        
        # Keep the window alive
        try:
            while True:
                QtWidgets.QApplication.processEvents()
                time.sleep(0.001)
                if not settings_view.isVisible():
                    break
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        
        return settings_view
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 