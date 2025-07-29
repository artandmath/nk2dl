#!/usr/bin/env python3
"""
Minimal Nuke test to validate PySide environment
No nk2dl imports to avoid conflicts
"""

import sys
import os

def test_nuke_environment():
    """Test basic Nuke environment"""
    
    print("============================================================")
    print("MINIMAL NUKE TEST: ENVIRONMENT")
    print("============================================================")
    
    try:
        import nuke
        
        print(f"Nuke version: {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")
        
        # Test basic nuke functionality
        root = nuke.root()
        print(f"Nuke root: {root}")
        
        print("✓ Nuke environment works")
        return True
        
    except Exception as e:
        print(f"✗ Nuke environment failed: {e}")
        return False

def test_pyside_environment():
    """Test PySide environment"""
    
    print("\n============================================================")
    print("MINIMAL NUKE TEST: PYSIDE")
    print("============================================================")
    
    try:
        import nuke
        
        # Test PySide imports based on Nuke version
        if nuke.NUKE_VERSION_MAJOR >= 16:
            from PySide6 import QtWidgets, QtCore, QtGui
            print("✓ PySide6 imported successfully")
            pyside_version = "PySide6"
        else:
            from PySide2 import QtWidgets, QtCore, QtGui
            print("✓ PySide2 imported successfully")
            pyside_version = "PySide2"
        
        # Test basic Qt functionality
        app = QtWidgets.QApplication.instance()
        if app is None:
            print("✗ Qt Application not available")
            return False
        else:
            print(f"✓ Qt Application available: {app}")
            print(f"✓ {pyside_version} environment ready")
        
        # Test widget creation
        widget = QtWidgets.QWidget()
        widget.setWindowTitle("Test Widget")
        print(f"✓ Test widget created: {widget}")
        
        return True
        
    except Exception as e:
        print(f"✗ PySide environment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_python_path():
    """Test Python path to understand import issues"""
    
    print("\n============================================================")
    print("MINIMAL NUKE TEST: PYTHON PATH")
    print("============================================================")
    
    print("Python path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # Check if nk2dl is in path
    nk2dl_in_path = any('nk2dl' in path for path in sys.path)
    print(f"\nnk2dl in path: {nk2dl_in_path}")
    
    # Check for potential conflicts
    print("\nChecking for 'nuke' module conflicts:")
    for path in sys.path:
        if 'nk2dl' in path:
            nuke_path = os.path.join(path, 'nk2dl', 'nuke')
            if os.path.exists(nuke_path):
                print(f"  Found nk2dl.nuke at: {nuke_path}")
    
    return True

def main():
    """Run minimal tests"""
    
    print("Starting minimal Nuke tests...")
    
    # Keep track of results
    test_results = []
    
    # Run tests
    test_results.append(test_nuke_environment())
    test_results.append(test_pyside_environment())
    test_results.append(test_python_path())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n============================================================")
    print(f"MINIMAL NUKE TEST SUMMARY")
    print(f"============================================================")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ MINIMAL NUKE TESTS PASSED")
        print("🎉 Nuke and PySide environment validated!")
    else:
        print("❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main() 