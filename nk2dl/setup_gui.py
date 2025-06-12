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
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

from .common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.setup_gui')

def create_render_menus():
    """Create the main nk2dl menus in Nuke.
    
    This function creates the main nk2dl menus in the render menu of Nuke.

    Returns:
        True or None: True if menus were created, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, skipping menu creation")
        return None
    
    # Get the main menu bar
    menubar = nuke.menu('Nuke')
    render_menu = menubar.addMenu('Render')
    render_menu.addSeparator()

    # The following is for the Thinkbox submitter.
    # Consider enabling this if transitioning to NK2DL from Thinkbox.
    '''
    # Add thinkbox submitter
    render_menu.addCommand(
        'Submit Nuke to Deadline (Thinkbox)',
        'import DeadlineNukeClient; DeadlineNukeClient.main()',
        "ctrl+shift+F7",
        tooltip='Submit the current Nuke script to Deadline',
    )
    '''

    # Add submission command
    render_menu.addCommand(
        'Submit Nuke to Deadline',
        'from nk2dl.gui.commands import submit_current_script; submit_current_script()',
        "shift+F7",
        tooltip='Submit the current Nuke script to Deadline',
    )

    # Add Selected Writes submission command
    render_menu.addCommand(
        'Submit Selected Writes to Deadline',
        'from nk2dl.gui.commands import submit_selected_writes_to_deadline; submit_selected_writes_to_deadline()',
        "alt+shift+F7",
        tooltip='Open submission dialog with advanced options',
    )
        
    logger.info("nk2dl menus created successfully")
    return True

def create_toolbar_commands():
    """Create nk2dl gizmo commands in the Nodes toolbar.
    
    This function adds nk2dl gizmo nodes to the Nodes toolbar using nuke.nodePaste().

    Returns:
        True or None: True if toolbar commands were created, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, skipping toolbar creation")
        return None
    
    # Get the path to the gizmos directory
    current_dir = Path(__file__).parent
    gizmos_dir = current_dir / "gui" / "grizmos"
    
    # Define gizmo files
    gizmos = {
        "Nk2dl_ModifyMetaData.nk": "Nk2dl_ModifyMetaData",
        "Nk2dl_ModifyMetaDataGui.nk": "Nk2dl_ModifyMetaDataGui"
    }
    
    # Get the Nodes toolbar
    toolbar = nuke.toolbar("Nodes")
    
    # Add commands for each gizmo
    for gizmo_file, display_name in gizmos.items():
        gizmo_path = gizmos_dir / gizmo_file
        
        if gizmo_path.exists():
            # Create the command string using nuke.nodePaste()
            command = f"nuke.nodePaste(r'{gizmo_path}')"
            
            # Add the command to the toolbar
            toolbar.addCommand(
                f"Nk2dl/{display_name}",
                command,
                tooltip=f'Add {display_name} gizmo to the node graph'
            )
            logger.debug(f"Added toolbar command for {display_name} at {gizmo_path}")
        else:
            logger.warning(f"Gizmo file not found: {gizmo_path}")
    
    logger.info("nk2dl toolbar commands created successfully")
    return True

create_render_menus()
create_toolbar_commands()