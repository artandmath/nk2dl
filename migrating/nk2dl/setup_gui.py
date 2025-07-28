"""Setup GUI convenience module for nk2dl.

Import this module to automatically setup the nk2dl GUI in Nuke.

Usage:
    from nk2dl import setup_gui  # GUI is automatically setup
    # or
    import nk2dl.setup_gui  # GUI is automatically setup
"""

import os
from pathlib import Path

try:
    import nuke
    from nukescripts import panels
    NUKE_AVAILABLE = True
    
    # Detect Nuke version for appropriate PySide import
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        PYSIDE_VERSION = "PySide6"
    else:
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"

from .common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.setup_gui')

def setup_gui():
    """Create and register the dockable nk2dl panel and menus.
    
    Returns:
        True or None: True, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, skipping panel creation")
        return None
    
    try:
        from .gui.panel import register_panel
        register_panel()
    except Exception as e:
        logger.error(f"Failed to register nk2dl panel: {str(e)}")

    try:
        from .gui.menus import create_render_menus, create_toolbar_commands
        create_render_menus()
        create_toolbar_commands()
    except Exception as e:
        logger.error(f"Failed to create menus and toolbar: {str(e)}")
        
    return True

# Initialize all GUI components
logger.info("Initializing nk2dl GUI components")
setup_gui()
