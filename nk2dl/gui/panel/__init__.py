# -*- coding: utf-8 -*-
"""Panel module for nk2dl GUI components.

This module contains all the components for the nk2dl panel interface,
organized following MVC/MVP patterns for better maintainability.

Modules:
    constants: Color themes, sizes, and configuration constants
    widgets: Custom Qt widgets (ColoredGroupBox, PinnedRowTableWidget, etc.)
    delegates: Custom item delegates for table rendering and editing
    models: Data models for table data, GSV hierarchy, and settings
    views: UI view components for different panel sections
    panel: Main panel class and registration functions

Usage:
    # Check if panel is available (requires Nuke + PySide)
    from nk2dl.gui.panel import get_panel_availability
    available, error = get_panel_availability()
    
    if available:
        from nk2dl.gui.panel import Nk2dlPanel, register_panel
        register_panel()  # Explicitly register the panel
    
    # Constants are always available
    from nk2dl.gui.panel.constants import Settings, Colors, Sizes
"""

__version__ = "0.1.0"
__author__ = "Daniel Harkness"

# Import main panel class for convenience
# This will only succeed in a Nuke environment with PySide
try:
    from .panel import Nk2dlPanel, register_panel
    __all__ = ['Nk2dlPanel', 'register_panel', 'get_panel_availability']
    _PANEL_AVAILABLE = True
except ImportError as e:
    # Handle case where dependencies (Nuke, PySide) are not available
    __all__ = ['get_panel_availability']
    _PANEL_AVAILABLE = False
    _IMPORT_ERROR = str(e)

def get_panel_availability():
    """Check if the panel classes are available.
    
    Returns:
        tuple: (available: bool, error_message: str or None)
        
    Example:
        >>> available, error = get_panel_availability()
        >>> if available:
        ...     from nk2dl.gui.panel import register_panel
        ...     register_panel()
    """
    if _PANEL_AVAILABLE:
        return True, None
    else:
        return False, _IMPORT_ERROR 