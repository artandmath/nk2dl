#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Test render checkbox column functionality.

This test verifies the new render checkbox column works properly.
Run with: & 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_render_checkbox_column.py
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
    NUKE_AVAILABLE = True
    
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
    
    print(f"✓ {PYSIDE_VERSION} available")
    
except ImportError as e:
    print(f"✗ PySide not available: {e}")
    NUKE_AVAILABLE = False


def test_render_checkbox_column():
    """Test the render checkbox column functionality."""
    if not NUKE_AVAILABLE:
        print("✗ Nuke not available - skipping test")
        return False
    
    try:
        # Import nk2dl components
        from gui.panel.views.node_settings_view import NodeSettingsView
        from gui.panel.models.table_model import TableModel
        from gui.panel.constants import TableColumns
        
        print("✓ nk2dl imports successful")
        
        # Create test nodes
        nuke.scriptClear()
        
        write1 = nuke.createNode("Write")
        write1.setName("Write1")
        write1['file'].setValue("/tmp/test1.exr")
        
        write2 = nuke.createNode("Write") 
        write2.setName("Write2")
        write2['file'].setValue("/tmp/test2.exr")
        
        print("✓ Test nodes created")
        
        # Create table model and load data
        model = TableModel()
        model.load_from_nuke_selection([write1, write2])
        
        # Check headers include Render column
        headers = model.get_headers()
        print(f"Headers: {headers}")
        
        if "Render" not in headers:
            print("✗ Render column not found in headers")
            return False
        
        if headers[0] != "Render":
            print(f"✗ Render column is not first column. Found: {headers[0]}")
            return False
            
        print("✓ Render column is first column")
        
        # Check data includes boolean render values
        data = model.get_data()
        for i, row_data in enumerate(data):
            render_value = row_data.get("Render", None)
            if not isinstance(render_value, bool):
                print(f"✗ Row {i} render value is not boolean: {render_value} (type: {type(render_value)})")
                return False
                
        print("✓ Render column data is boolean")
        
        # Create Qt application if needed
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        
        # Create view and test UI
        view = NodeSettingsView(model)
        view.setWindowTitle("Render Checkbox Column Test")
        view.resize(800, 400)
        view.show()
        
        print("✓ View created and shown")
        
        # Test table structure
        table = view.render_table
        
        # Check frozen column count
        if not hasattr(table, 'frozen_column_count'):
            print("✗ Table missing frozen_column_count attribute")
            return False
            
        if table.frozen_column_count != 4:
            print(f"✗ Expected 4 frozen columns, got {table.frozen_column_count}")
            return False
            
        print("✓ Frozen column count is 4")
        
        # Check column width for render column
        render_column_width = table.columnWidth(0)
        if render_column_width != 30:
            print(f"✗ Expected render column width 30px, got {render_column_width}px")
            return False
            
        print("✓ Render column width is 30px")
        
        # Test checkbox functionality
        if table.rowCount() > 0:
            # Get first item (render column, first row)
            item = table.item(0, 0)
            if item is None:
                print("✗ No item in render column")
                return False
                
            # Check if item is checkable
            if not (item.flags() & QtCore.Qt.ItemIsUserCheckable):
                print("✗ Render column item is not checkable")
                return False
                
            print("✓ Render column item is checkable")
            
            # Test checkbox state
            initial_state = item.checkState()
            print(f"✓ Initial checkbox state: {initial_state}")
            
            # Toggle checkbox
            new_state = QtCore.Qt.Unchecked if initial_state == QtCore.Qt.Checked else QtCore.Qt.Checked
            item.setCheckState(new_state)
            
            # Verify state changed
            if item.checkState() != new_state:
                print("✗ Checkbox state did not change")
                return False
                
            print("✓ Checkbox state toggles correctly")
            
        # Test frozen table synchronization
        if hasattr(table, 'frozen_table') and table.frozen_table.rowCount() > 0:
            frozen_item = table.frozen_table.item(0, 0)
            if frozen_item is None:
                print("✗ No item in frozen render column")
                return False
                
            if not (frozen_item.flags() & QtCore.Qt.ItemIsUserCheckable):
                print("✗ Frozen render column item is not checkable")
                return False
                
            print("✓ Frozen table render column is checkable")
        
        # Keep window open for manual inspection
        print("✓ All tests passed! Keeping window open for 10 seconds...")
        
        # Process events and keep window visible
        start_time = time.time()
        while time.time() - start_time < 10:
            app.processEvents()
            time.sleep(0.1)
        
        view.close()
        print("✓ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("="*60)
    print("RENDER CHECKBOX COLUMN TEST")
    print("="*60)
    
    if test_render_checkbox_column():
        print("\n✓ ALL TESTS PASSED")
        nuke.message("Render checkbox column test PASSED")
    else:
        print("\n✗ TESTS FAILED")
        nuke.message("Render checkbox column test FAILED")


if __name__ == "__main__":
    main() 