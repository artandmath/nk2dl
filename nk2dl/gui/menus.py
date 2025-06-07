"""Menu creation and management for nk2dl in Nuke."""

from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.menus')

try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False


def create_nk2dl_menu():
    """Create the main nk2dl menu in Nuke.
    
    Returns:
        nuke.Menu or None: The created menu object, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, skipping menu creation")
        return None
    
    # Get the main menu bar
    menubar = nuke.menu('Nuke')
    
    # Create or get the nk2dl menu
    render_menu = menubar.addMenu('Render')
    
    # Create a separator
    render_menu.addSeparator()
    
    # Add submission command
    render_menu.addCommand(
        'Submit Nuke to Deadline',
        'from nk2dl.gui.commands import submit_current_script; submit_current_script()',
        "shift+F7",
        tooltip='Submit the current Nuke script to Deadline',
    )

    # Add submission with options
    render_menu.addCommand(
        'Submit Selected Writes to Deadline',
        'from nk2dl.gui.commands import submit_selected_writes_to_deadline; submit_selected_writes_to_deadline()',
        "alt+shift+F7",
        tooltip='Open submission dialog with advanced options',
    )


        
    logger.info("nk2dl menus created successfully")
    return render_menu 