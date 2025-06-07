"""Auto-setup convenience module for nk2dl.

Import this module to automatically setup the nk2dl GUI in Nuke.

Usage:
    from nk2dl import auto_setup  # GUI is automatically setup
    # or
    import nk2dl.auto_setup  # GUI is automatically setup
"""

from .gui.menus import create_nk2dl_menu

# Automatically setup GUI when this module is imported
create_nk2dl_menu()

# Re-export for convenience
__all__ = ['create_nk2dl_menu'] 