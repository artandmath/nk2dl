"""Command implementations for nk2dl menu items."""

import logging

try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

# Set up logger
logger = logging.getLogger(__name__)


def submit_current_script():
    """Submit the current Nuke script to Deadline with default settings."""
    if not NUKE_AVAILABLE:
        print("Error: Nuke not available")
        return
    
    # Placeholder function - GUI not yet implemented
    nuke.message("NK2DL Submit Script GUI functionality not yet implemented.\n\nPlease use 'Submit Selected Writes to Deadline' instead.")


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
    selected_nodes = nuke.selectedNodes('Write') + nuke.selectedNodes('DeepWrite')
    
    if not selected_nodes:
        nuke.message("No nodes selected. Please select at least one Write or DeepWrite node.")
        return False
    
    write_node_names = []
    for node in selected_nodes:
        write_node_names.append(node.name())

    try:
        from ..nuke import submit_nuke_script
        
        results = submit_nuke_script(
            nuke.root().name(),
            script_is_open=True,
            frames="input",
            render_order_dependencies=True,
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