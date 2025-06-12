"""Basic dockable panel for nk2dl in Nuke."""

try:
    import nuke
    import nukescripts
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel')


class Nk2dlPanel(nukescripts.PythonPanel):
    """Basic nk2dl panel for Nuke.
    
    This is a dockable panel that provides a basic interface for nk2dl functionality.
    """
    
    def __init__(self):
        """Initialize the nk2dl panel."""
        if not NUKE_AVAILABLE:
            logger.error("Nuke not available, cannot create panel")
            return
            
        nukescripts.PythonPanel.__init__(self, 'Nuke to Deadline', 'danielharkness.com.nk2dl.panel')
        
        # Add some basic knobs for demonstration
        self._create_knobs()
        
        logger.info("nk2dl panel initialized")
    
    def _create_knobs(self):
        """Create the basic knobs for the panel."""
        # Add a text knob for information
        info_knob = nuke.Text_Knob('info', 'Info', 'nk2dl - Nuke to Deadline submission panel')
        self.addKnob(info_knob)
        
        # Add a separator
        sep_knob = nuke.Text_Knob('sep1', '', '')
        sep_knob.setFlag(nuke.STARTLINE)
        self.addKnob(sep_knob)
        
        # Add a simple button for future functionality
        submit_button = nuke.PyScript_Knob('submit_btn', 'Submit Current Script')
        submit_button.setCommand('from nk2dl.gui.commands import submit_current_script; submit_current_script()')
        self.addKnob(submit_button)
        
        # Add another button for selected writes
        selected_writes_button = nuke.PyScript_Knob('selected_writes_btn', 'Submit Selected Writes')
        selected_writes_button.setCommand('from nk2dl.gui.commands import submit_selected_writes_to_deadline; submit_selected_writes_to_deadline()')
        self.addKnob(selected_writes_button)


def create_panel():
    """Create and return a new instance of the nk2dl panel.
    
    This function is used by the panel registration system.
    
    Returns:
        The panel's addToPane() method result.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, cannot create panel")
        return None
        
    global nk2dl_panel
    nk2dl_panel = Nk2dlPanel()
    return nk2dl_panel.addToPane() 