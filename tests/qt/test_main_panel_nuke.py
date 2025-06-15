#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the main nk2dl panel in Nuke environment."""

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

# Import the main panel
from gui.panel.panel import Nk2dlPanel


def main():
    """Run the main nk2dl panel in Nuke."""
    # Create and show the panel
    panel = Nk2dlPanel()
    panel.show()
    
    print(f"NK2DL Main Panel Test started using {PYSIDE_VERSION} in Nuke {nuke.NUKE_VERSION_STRING}")
    print("Check the Node Settings tab for inheritance behavior:")
    print("- Bold text should indicate explicit values")
    print("- Normal text should indicate inherited values")
    print("- Frames column should now inherit from job settings (1001-2315) when set to None")
    print("- Some sample rows have None for Frames (should show 1001-2315 in normal text)")
    print("- Other rows have explicit frame ranges (should show in bold text)")
    print("\nWindow should remain open. Close it manually when done testing.")
    
    # Store global reference to prevent garbage collection
    globals()['_test_panel'] = panel
    
    return panel


if __name__ == "__main__":
    panel = main()
    
    # Keep the script alive in Nuke's terminal mode
    try:
        import time
        print("Press Ctrl+C in terminal to exit, or close the window manually.")
        while True:
            # Process Qt events to keep the window responsive
            QtWidgets.QApplication.processEvents()
            time.sleep(0.1)
            
            # Check if window is still open
            if not panel.isVisible():
                print("Window closed, exiting...")
                break
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        pass 