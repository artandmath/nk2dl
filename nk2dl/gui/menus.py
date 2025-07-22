"""Menu and command implementations for nk2dl."""

import logging
import os
from pathlib import Path

try:
    import nuke
    import nukescripts
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

from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.menus')


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
        'nukescripts.panels.restorePanel("com.danielharkness.nk2dl.panel")',
        "shift+F7",
        tooltip='Open submission dialog with advanced options',
    )

    # Add Selected Writes submission command
    render_menu.addCommand(
        'Submit Selected Writes to Deadline',
        'from nk2dl.gui.menus import submit_selected_writes_to_deadline; submit_selected_writes_to_deadline()',
        "alt+shift+F7",
        tooltip='Submit selected Write/DeepWrite nodes to Deadline',
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
    gizmos_dir = current_dir / "grizmos"
    
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


def submit_selected_writes_to_deadline():
    """Submit selected Write/DeepWrite nodes to Deadline."""
    if not NUKE_AVAILABLE:
        print("Error: Nuke not available")
        return
    
    logger.debug("submit_selected_writes_to_deadline called")
    
    try:
        nuke.scriptSave()
        logger.debug("saved script")
    except Exception as e:
        logger.warning(f"Could not save script: {e}")

    # Get selected nodes
    selected_nodes = nuke.selectedNodes()
    selected_groups = nuke.selectedNodes('Group')
    for group in selected_groups:
        selected_nodes.extend(nuke.allNodes(group=group, recurseGroups=True))
    
    selected_writes = []
    for node in selected_nodes:
        if node.Class() == 'Write' or node.Class() == 'DeepWrite':
            selected_writes.append(node)

    if not selected_writes:
        nuke.message("No nodes selected. Please select at least one Write or DeepWrite node.")
        return False
    
    write_node_names = []
    for node in selected_writes:
        write_node_names.append(node.fullName())

    try:
        from ..nuke import submit_nuke_script
        
        results = submit_nuke_script(
            nuke.root().name(),
            script_is_open=True,
            frames="input",
            render_order_dependencies=True,
            write_nodes_as_separate_jobs=True,   
            write_nodes=write_node_names,
            render_settings_from_metadata=True
        )

        # Extract job IDs from result
        job_ids = []
        for result in results:
            if result and 'job_id' in result:
                if isinstance(result['job_id'], list):
                    job_ids.extend(result['job_id'])
                else:
                    job_ids.append(result['job_id'])
        
        # Create message showing write nodes and job IDs
        message_parts = [f"Submitted {len(job_ids)} jobs to Deadline."]
        message_parts.append(f"\nWrite Nodes: {', '.join(write_node_names)}")
        
        if job_ids:
            message_parts.append(f"\nJob IDs: {', '.join(job_ids)}")
        
        nuke.message('\n'.join(message_parts))
        return True
        
    except Exception as e:
        error_msg = f"Submission failed: {str(e)}"
        logger.error(error_msg)
        nuke.message(error_msg)
        return False 