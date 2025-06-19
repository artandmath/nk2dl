# -*- coding: utf-8 -*-
"""Extra settings view for the nk2dl panel.

This module contains the ExtraSettingsView class for managing additional job
information like job name, comment, and department.
"""

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from ..widgets import ColoredGroupBox
from ..constants import Settings, Sizes, GSVDefaults
from ..config import apply_panel_config


class ExtraSettingsView(QtWidgets.QWidget):
    """View for extra settings like job name, comment, and department.
    
    This view handles the UI for additional job information that doesn't
    fit into the main job settings category.
    """
    
    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings_model = settings_model
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_settings_from_model()
    
    def _create_ui(self):
        """Create the extra settings UI components."""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Job Information section
        job_info_group = QtWidgets.QGroupBox("Job Information")
        job_info_layout = QtWidgets.QGridLayout()
        job_info_layout.setSpacing(8)
        job_info_group.setLayout(job_info_layout)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Job Name:"), 0, 0)
        self.job_name_edit = QtWidgets.QLineEdit()
        self.job_name_edit.setToolTip("The name of your job. This is optional, and if left blank, it will default to 'Untitled'.")
        job_info_layout.addWidget(self.job_name_edit, 0, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Comment:"), 1, 0)
        self.comment_edit = QtWidgets.QLineEdit()
        self.comment_edit.setToolTip("A simple description of your job. This is optional and can be left blank.")
        job_info_layout.addWidget(self.comment_edit, 1, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Department:"), 2, 0)
        self.department_edit = QtWidgets.QLineEdit()
        self.department_edit.setToolTip("The department you belong to. This is optional and can be left blank.")
        job_info_layout.addWidget(self.department_edit, 2, 1)
        
        layout.addWidget(job_info_group)
        
        # Add stretch to push content to top
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect UI signals to model updates."""
        self.job_name_edit.textChanged.connect(lambda t: self.settings_model.set_extra_setting('job_name', t))
        self.comment_edit.textChanged.connect(lambda t: self.settings_model.set_extra_setting('comment', t))
        self.department_edit.textChanged.connect(lambda t: self.settings_model.set_extra_setting('department', t))
        
        # Model change signals
        self.settings_model.extraSettingsChanged.connect(self._on_extra_settings_changed)
    
    def _load_settings_from_model(self):
        """Load current settings from the model into the UI."""
        # Block signals to prevent feedback loops
        self._block_signals(True)
        
        try:
            # Load extra settings
            extra_settings = self.settings_model.get_all_extra_settings()
            self.job_name_edit.setText(extra_settings.get('job_name', ''))
            self.comment_edit.setText(extra_settings.get('comment', ''))
            self.department_edit.setText(extra_settings.get('department', ''))
        finally:
            # Re-enable signals
            self._block_signals(False)
    
    def _block_signals(self, block):
        """Block or unblock signals for all UI controls."""
        self.job_name_edit.blockSignals(block)
        self.comment_edit.blockSignals(block)
        self.department_edit.blockSignals(block)
    
    def _on_extra_settings_changed(self):
        """Handle extra settings changes from the model."""
        # Reload settings from model (in case they were changed externally)
        self._load_settings_from_model()
    
    def get_settings_model(self):
        """Get the settings model.
        
        Returns:
            SettingsModel: The settings model instance
        """
        return self.settings_model 
    
    def _apply_configuration(self):
        """Apply panel configuration to extra settings controls."""
        # Add debug logging - move outside try block for error handling
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.extra_settings_view')
        
        try:
            logger.debug("Starting _apply_configuration for ExtraSettingsView")
            
            # Set object names for extra settings controls - MUST match control names passed to apply_panel_config
            self.job_name_edit.setObjectName("job_name")
            self.comment_edit.setObjectName("comment")
            self.department_edit.setObjectName("department")
            
            # Apply configuration to extra settings controls
            apply_panel_config(self.job_name_edit, "job_name")
            apply_panel_config(self.comment_edit, "comment")
            apply_panel_config(self.department_edit, "department")
            
        except Exception as e:
            logger.error(f"Error applying configuration to ExtraSettingsView: {e}") 