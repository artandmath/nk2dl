#!/usr/bin/env python
"""
Frozen Table Alignment Test

Tests that frozen table geometry stays properly aligned with the main table
after clear and update operations, ensuring row numbers and columns don't 
get misaligned or clipped.

Usage: Run in Nuke environment
"""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
try:
    import nuke
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    # Fallback for non-Nuke environments
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
    except ImportError:
        from PySide2 import QtWidgets, QtCore, QtGui

def _wait(ms=100):
    """Wait for Qt events to process."""
    start_time = time.time()
    while (time.time() - start_time) * 1000 < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)

def check_frozen_table_alignment():
    """Check if frozen table is properly aligned with main table."""
    
    try:
        print("🚀 Starting Frozen Table Alignment Test")
        print("🔧 Setting up panel...")
        
        # Create the full panel
        from nk2dl.gui.panel import Nk2dlPanel
        panel = Nk2dlPanel()
        panel.show()
        
        _wait(1000)  # Wait for initialization
        
        # Find the NodeSettingsView
        node_settings_view = None
        for child in panel.findChildren(QtWidgets.QWidget):
            if hasattr(child, 'render_table') and hasattr(child.render_table, 'frozen_table'):
                node_settings_view = child
                break
        
        if not node_settings_view:
            print("❌ Could not find NodeSettingsView")
            return
            
        print(f"✅ Found NodeSettingsView: {node_settings_view}")
        
        # Check initial state
        main_table = node_settings_view.render_table
        frozen_table = main_table.frozen_table
        
        print("\n============================================================")
        print("🔍 INITIAL GEOMETRY CHECK")
        print("============================================================")
        
        def print_geometry_info():
            main_geom = main_table.geometry()
            frozen_geom = frozen_table.geometry()
            vertical_header_width = main_table.verticalHeader().width()
            
            print(f"📊 Main table geometry: x={main_geom.x()}, y={main_geom.y()}, w={main_geom.width()}, h={main_geom.height()}")
            print(f"📊 Frozen table geometry: x={frozen_geom.x()}, y={frozen_geom.y()}, w={frozen_geom.width()}, h={frozen_geom.height()}")
            print(f"📊 Vertical header width: {vertical_header_width}px")
            print(f"📊 Frozen table X offset should be: {vertical_header_width + main_table.frameWidth()}px")
            
            # Check if frozen table X position accounts for vertical header
            expected_x = vertical_header_width + main_table.frameWidth()
            actual_x = frozen_geom.x()
            alignment_ok = abs(actual_x - expected_x) <= 2  # Allow 2px tolerance
            
            if alignment_ok:
                print(f"✅ Frozen table X alignment: GOOD ({actual_x}px ≈ {expected_x}px)")
            else:
                print(f"❌ Frozen table X alignment: BAD ({actual_x}px ≠ {expected_x}px)")
                
            return alignment_ok
        
        initial_alignment = print_geometry_info()
        
        # Load sample data
        print("\n📊 Loading sample data...")
        sample_data = [
            {"Render": True, "Order": 1, "Node": "Write1", "Filename": "output.%04d.exr", "Priority": 50},
            {"Render": True, "Order": 2, "Node": "Write2", "Filename": "comp.%04d.exr", "Priority": 75},
            {"Render": False, "Order": 3, "Node": "Write3", "Filename": "preview.%04d.jpg", "Priority": 25}
        ]
        
        node_settings_view.table_model.set_data(sample_data)
        _wait(1000)
        
        print("\n============================================================")
        print("🔍 AFTER DATA LOADING - GEOMETRY CHECK")
        print("============================================================")
        
        after_load_alignment = print_geometry_info()
        
        # Test clear button
        print("\n🔴 TESTING CLEAR BUTTON...")
        clear_button = None
        for button in panel.findChildren(QtWidgets.QPushButton):
            if "Clear" in button.text():
                clear_button = button
                break
        
        if clear_button:
            clear_button.click()
            _wait(500)
            
            print("\n============================================================")
            print("🔍 AFTER CLEAR OPERATION - GEOMETRY CHECK")
            print("============================================================")
            
            after_clear_alignment = print_geometry_info()
        else:
            print("❌ Could not find Clear button")
            after_clear_alignment = False
        
        # Test update button (if there are nodes)
        print("\n🔵 TESTING UPDATE BUTTON...")
        update_button = None
        for button in panel.findChildren(QtWidgets.QPushButton):
            if "Update" in button.text():
                update_button = button
                break
        
        if update_button:
            update_button.click()
            _wait(1000)  # Update takes longer
            
            print("\n============================================================")
            print("🔍 AFTER UPDATE OPERATION - GEOMETRY CHECK")
            print("============================================================")
            
            after_update_alignment = print_geometry_info()
        else:
            print("❌ Could not find Update button")
            after_update_alignment = False
        
        print("\n============================================================")
        print("🎯 FINAL RESULTS")
        print("============================================================")
        
        results = {
            "Initial": initial_alignment,
            "After Load": after_load_alignment,
            "After Clear": after_clear_alignment,
            "After Update": after_update_alignment
        }
        
        all_good = True
        for test_name, result in results.items():
            if result is False:
                all_good = False
                
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}: Frozen table alignment")
        
        if all_good:
            print("\n🎉 ALL TESTS PASSED - Frozen table alignment is working correctly!")
        else:
            print("\n⚠️ SOME TESTS FAILED - Frozen table alignment issues detected")
            
        print("\nTest completed - check alignment visually in the GUI")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_frozen_table_alignment() 