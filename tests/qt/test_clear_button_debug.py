#!/usr/bin/env python
"""
Enhanced Clear Button Debug Test

Automatically tests clear button operations with comprehensive debug logging
to identify the source of intermediate redraws and header truncation issues.

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
        from PySide6.QtTest import QTest
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        from PySide2.QtTest import QTest
except ImportError:
    print("This test must be run in Nuke environment")
    sys.exit(1)

# Import nk2dl modules
from nk2dl.gui.panel import Nk2dlPanel

def _wait(ms=100):
    """Custom wait function since QTest.qWait doesn't exist in older PySide versions."""
    end_time = time.time() + (ms / 1000.0)
    while time.time() < end_time:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)

class ClearButtonDebugTest:
    def __init__(self):
        self.panel = None
        self.node_settings_view = None
        self.column_width_changes = []
        
    def setUp(self):
        """Set up the test environment with full panel."""
        print("🔧 Setting up enhanced clear button debug test...")
        
        # Create main panel
        self.panel = Nk2dlPanel()
        self.panel.show()
        
        # Find the node settings view
        self.node_settings_view = None
        for child in self.panel.findChildren(QtWidgets.QWidget):
            if hasattr(child, 'render_table') and hasattr(child, '_on_clear_clicked'):
                self.node_settings_view = child
                break
                
        if not self.node_settings_view:
            raise RuntimeError("Could not find NodeSettingsView in panel")
            
        print(f"✅ Found NodeSettingsView: {self.node_settings_view}")
        
        # Wait for panel to fully initialize
        _wait(500)
        
    def load_sample_data(self):
        """Load sample data into the table."""
        print("📊 Loading sample data...")
        
        sample_data = [
            {
                'Render': True, 'Order': '1000', 'Node': 'Write_Beauty_v01', 
                'Filename': '//server/project/shots/shot_010/comp/beauty/shot_010_beauty_v001.%04d.exr',
                'Priority': '75', 'ChunkSize': '1', 'Frames': '1001-2315'
            },
            {
                'Render': True, 'Order': '2000', 'Node': 'Write_Z', 
                'Filename': '//server/project/shots/shot_010/comp/depth/shot_010_zdepth_v001.%04d.exr',
                'Priority': '50', 'ChunkSize': '5', 'Frames': '1001-2315'
            },
            {
                'Render': False, 'Order': '3000', 'Node': 'Write_Cryptomatte', 
                'Filename': '//server/project/shots/shot_010/comp/crypto/shot_010_crypto_v001.%04d.exr',
                'Priority': '25', 'ChunkSize': '10', 'Frames': '1001-2315'
            }
        ]
        
        # Load data through the table model
        if hasattr(self.node_settings_view, 'table_model'):
            self.node_settings_view.table_model.set_data(sample_data)
            
        _wait(200)
        print("✅ Sample data loaded")
        
    def capture_header_state(self, label):
        """Capture current header state for comparison."""
        if not self.node_settings_view or not self.node_settings_view.render_table:
            return
            
        header = self.node_settings_view.render_table.horizontalHeader()
        
        print(f"📋 HEADER STATE ({label}):")
        for col in range(min(6, header.count())):  # Check first 6 columns
            try:
                section_size = header.sectionSize(col)
                header_text = self.node_settings_view.render_table.horizontalHeaderItem(col)
                header_text = header_text.text() if header_text else "None"
                print(f"   Column {col}: '{header_text}' - {section_size}px")
            except Exception as e:
                print(f"   Column {col}: Error reading - {e}")
                
    def test_clear_button_enhanced_debug(self):
        """Test clear button with enhanced debugging."""
        print(f"\n{'='*60}")
        print("🔍 ENHANCED CLEAR BUTTON DEBUG TEST")
        print(f"{'='*60}")
        
        # Load sample data first
        self.load_sample_data()
        
        # Capture initial header state
        self.capture_header_state("BEFORE_CLEAR")
        
        # Find clear button
        clear_button = None
        for button in self.panel.findChildren(QtWidgets.QPushButton):
            if "clear" in button.text().lower():
                clear_button = button
                break
                
        if not clear_button:
            print("❌ Clear button not found!")
            return
            
        print(f"✅ Found clear button: {clear_button.text()}")
        
        # Click clear button and capture all debug output
        print("\n🔴 CLICKING CLEAR BUTTON...")
        
        start_time = time.time()
        QTest.mouseClick(clear_button, QtCore.Qt.LeftButton)
        
        # Process events and wait for operations to complete
        _wait(500)
        
        elapsed = (time.time() - start_time) * 1000
        print(f"🔴 Clear button operation completed in {elapsed:.1f}ms")
        
        # Capture final header state
        self.capture_header_state("AFTER_CLEAR")
        
        # Test column artifact by checking frozen table synchronization
        self.check_column_artifacts()
        
    def check_column_artifacts(self):
        """Check for column artifacts between frozen and unfrozen columns."""
        print(f"\n{'='*60}")
        print("🔍 CHECKING COLUMN ARTIFACTS")
        print(f"{'='*60}")
        
        if not hasattr(self.node_settings_view.render_table, 'frozen_table'):
            print("❌ No frozen table found")
            return
            
        frozen_table = self.node_settings_view.render_table.frozen_table
        main_table = self.node_settings_view.render_table
        
        print("📊 Comparing frozen vs main table column widths:")
        
        # Check frozen columns (typically first 4: Render, Order, Node, Filename)
        frozen_count = getattr(self.node_settings_view.render_table, 'frozen_column_count', 4)
        
        for col in range(min(frozen_count, 6)):
            try:
                frozen_width = frozen_table.columnWidth(col)
                main_width = main_table.columnWidth(col)
                
                if frozen_width != main_width:
                    print(f"   ⚠️ Column {col}: Frozen={frozen_width}px ≠ Main={main_width}px")
                else:
                    print(f"   ✅ Column {col}: Frozen={frozen_width}px = Main={main_width}px")
                    
            except Exception as e:
                print(f"   ❌ Column {col}: Error comparing - {e}")
                
    def run_test(self):
        """Run the complete test suite."""
        try:
            self.setUp()
            self.test_clear_button_enhanced_debug()
            
            print(f"\n{'='*60}")
            print("🎯 TEST COMPLETED")
            print(f"{'='*60}")
            print("Review the debug output above to identify:")
            print("- Number of setColumnWidth calls during clear operation")
            print("- Timing of column width changes")
            print("- Header state changes")
            print("- Column synchronization issues")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main test entry point."""
    print("🚀 Starting Enhanced Clear Button Debug Test")
    
    # Keep test widget alive
    test = ClearButtonDebugTest()
    globals()['_test_instance'] = test
    
    test.run_test()
    
    # Keep GUI alive for inspection
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if test.panel and not test.panel.isVisible():
                break
    except KeyboardInterrupt:
        pass
    
    return test

if __name__ == "__main__":
    main() 