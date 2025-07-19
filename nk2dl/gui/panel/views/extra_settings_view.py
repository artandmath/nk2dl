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

from ..widgets import ColoredGroupBox, HighlightableLineEdit, HighlightableComboBox, HighlightableCheckBox
from ..constants import Settings, Sizes, GSVDefaults
from ..config import apply_panel_config
from ..storage_visual_indication import StorageVisualIndicationMixin
from ..widget_change_tracker import WidgetChangeTrackingMixin


class ExtraSettingsView(StorageVisualIndicationMixin, WidgetChangeTrackingMixin, QtWidgets.QWidget):
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
        
        # Register widgets for visual indication
        self._register_widgets_for_visual_indication()
        
        # Register widgets for change tracking
        self._register_widgets_for_change_tracking()
        
        # Set up responsive behavior (will be controlled by main panel)
        self._setup_responsive_behavior()
    
    def _create_ui(self):
        """Create the extra settings UI components."""
        # Main container with horizontal layout for responsive behavior
        self.content_layout = QtWidgets.QHBoxLayout()  # Start horizontal
        self.content_layout.setSpacing(Sizes.SETTINGS_SPACING)
        self.content_layout.setContentsMargins(Sizes.SETTINGS_MARGIN, 15, Sizes.SETTINGS_MARGIN, Sizes.SETTINGS_BOTTOM_MARGIN)
        self.setLayout(self.content_layout)
        
        # Create left and right column widgets (no group boxes)
        self._create_left_column()
        self._create_right_column()
        
        # Add columns to layout with flexible size policies
        self.left_column_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.right_column_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.content_layout.addWidget(self.left_column_widget, 1)  # Stretch factor 1
        self.content_layout.addWidget(self.right_column_widget, 1)  # Stretch factor 1
    
    def _create_left_column(self):
        """Create the left column with Job Information and Script Submission sections."""
        self.left_column_widget = QtWidgets.QWidget()
        # Use a smaller minimum width to prevent horizontal scrollbar
        self.left_column_widget.setMinimumWidth(Sizes.JOB_SETTINGS_MIN_WIDTH - 50)
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        self.left_column_widget.setLayout(left_layout)
        
        # Job Information section
        job_info_group = QtWidgets.QGroupBox("Job Information")
        job_info_layout = QtWidgets.QGridLayout()
        job_info_layout.setSpacing(8)
        job_info_group.setLayout(job_info_layout)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Job Name:"), 0, 0)
        self.job_name_edit = HighlightableLineEdit()
        self.job_name_edit.setToolTip("The name of your job. This is optional, and if left blank, it will default to 'Untitled'.")
        job_info_layout.addWidget(self.job_name_edit, 0, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Comment:"), 1, 0)
        self.comment_edit = HighlightableLineEdit()
        self.comment_edit.setToolTip("A simple description of your job. This is optional and can be left blank.")
        job_info_layout.addWidget(self.comment_edit, 1, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Department:"), 2, 0)
        self.department_edit = HighlightableLineEdit()
        self.department_edit.setToolTip("The department you belong to. This is optional and can be left blank.")
        job_info_layout.addWidget(self.department_edit, 2, 1)
        
        left_layout.addWidget(job_info_group)
        
        # Script Submission section
        script_submission_group = QtWidgets.QGroupBox("Script Submission")
        script_submission_layout = QtWidgets.QGridLayout()
        script_submission_layout.setSpacing(8)
        script_submission_group.setLayout(script_submission_layout)
        
        # Submit script as auxiliary file
        script_submission_layout.addWidget(QtWidgets.QLabel("Submit Script as Auxiliary:"), 0, 0)
        self.submit_script_as_auxiliary_combo = HighlightableComboBox()
        self.submit_script_as_auxiliary_combo.addItems(["Default", "Yes", "No"])
        self.submit_script_as_auxiliary_combo.setToolTip("Whether to submit the script as an auxiliary file.")
        script_submission_layout.addWidget(self.submit_script_as_auxiliary_combo, 0, 1)
        
        # Copy script
        script_submission_layout.addWidget(QtWidgets.QLabel("Copy Script:"), 1, 0)
        self.copy_script_combo = HighlightableComboBox()
        self.copy_script_combo.addItems(["Default", "Yes", "No"])
        self.copy_script_combo.setToolTip("Whether to copy the script before submission.")
        script_submission_layout.addWidget(self.copy_script_combo, 1, 1)
        
        # Copy script path
        script_submission_layout.addWidget(QtWidgets.QLabel("Copy Script Path:"), 2, 0)
        self.copy_script_path_edit = HighlightableLineEdit()
        self.copy_script_path_edit.setToolTip("Path where to copy the script.")
        script_submission_layout.addWidget(self.copy_script_path_edit, 2, 1)
        
        # Submit copied script
        script_submission_layout.addWidget(QtWidgets.QLabel("Submit Copied Script:"), 3, 0)
        self.submit_copied_script_combo = HighlightableComboBox()
        self.submit_copied_script_combo.addItems(["Default", "Yes", "No"])
        self.submit_copied_script_combo.setToolTip("Whether to submit the copied script instead of the original.")
        script_submission_layout.addWidget(self.submit_copied_script_combo, 3, 1)
        
        left_layout.addWidget(script_submission_group)
    
    def _create_right_column(self):
        """Create the right column with Build Job, Script Job, Job Info, and Environment Variables sections."""
        self.right_column_widget = QtWidgets.QWidget()
        # Use a smaller minimum width to prevent horizontal scrollbar
        self.right_column_widget.setMinimumWidth(Sizes.MACHINE_SETTINGS_MIN_WIDTH - 50)
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        self.right_column_widget.setLayout(right_layout)
        
        # Build Job section
        build_job_group = QtWidgets.QGroupBox("Build Job")
        build_job_layout = QtWidgets.QGridLayout()
        build_job_layout.setSpacing(8)
        build_job_group.setLayout(build_job_layout)
        
        # Submission is build job
        build_job_layout.addWidget(QtWidgets.QLabel("Submission is Build Job:"), 0, 0)
        self.submission_is_build_job_check = HighlightableCheckBox("")
        self.submission_is_build_job_check.setToolTip("Whether this submission is a build job.")
        build_job_layout.addWidget(self.submission_is_build_job_check, 0, 1)
        
        # Build job name
        build_job_layout.addWidget(QtWidgets.QLabel("Build Job Name:"), 1, 0)
        self.build_job_name_edit = HighlightableLineEdit()
        self.build_job_name_edit.setToolTip("Name for the build job.")
        build_job_layout.addWidget(self.build_job_name_edit, 1, 1)
        
        # Pre-build job script
        build_job_layout.addWidget(QtWidgets.QLabel("Pre-build Script:"), 2, 0)
        self.pre_build_job_script_edit = HighlightableLineEdit()
        self.pre_build_job_script_edit.setToolTip("Script to run before the build job.")
        build_job_layout.addWidget(self.pre_build_job_script_edit, 2, 1)
        
        # Post-build job script
        build_job_layout.addWidget(QtWidgets.QLabel("Post-build Script:"), 3, 0)
        self.post_build_job_script_edit = HighlightableLineEdit()
        self.post_build_job_script_edit.setToolTip("Script to run after the build job.")
        build_job_layout.addWidget(self.post_build_job_script_edit, 3, 1)
        
        # Build job as auxiliary file
        build_job_layout.addWidget(QtWidgets.QLabel("Build Job as Auxiliary:"), 4, 0)
        self.build_job_as_auxiliary_combo = HighlightableComboBox()
        self.build_job_as_auxiliary_combo.addItems(["Default", "Yes", "No"])
        self.build_job_as_auxiliary_combo.setToolTip("Whether to submit the build job as an auxiliary file.")
        build_job_layout.addWidget(self.build_job_as_auxiliary_combo, 4, 1)
        
        # Delete build job script
        build_job_layout.addWidget(QtWidgets.QLabel("Delete Build Script:"), 5, 0)
        self.delete_build_job_script_combo = HighlightableComboBox()
        self.delete_build_job_script_combo.addItems(["Default", "Yes", "No"])
        self.delete_build_job_script_combo.setToolTip("Whether to delete the build job script after completion.")
        build_job_layout.addWidget(self.delete_build_job_script_combo, 5, 1)
        
        right_layout.addWidget(build_job_group)
        
        # Script Job section
        script_job_group = QtWidgets.QGroupBox("Script Job")
        script_job_layout = QtWidgets.QGridLayout()
        script_job_layout.setSpacing(8)
        script_job_group.setLayout(script_job_layout)
        
        # Script job script path
        script_job_layout.addWidget(QtWidgets.QLabel("Script Job Path:"), 0, 0)
        self.script_job_script_path_edit = HighlightableLineEdit()
        self.script_job_script_path_edit.setToolTip("Path to the script for script jobs.")
        script_job_layout.addWidget(self.script_job_script_path_edit, 0, 1)
        
        right_layout.addWidget(script_job_group)
        
        # Job Info section
        job_info_advanced_group = QtWidgets.QGroupBox("Job Info")
        job_info_advanced_layout = QtWidgets.QGridLayout()
        job_info_advanced_layout.setSpacing(8)
        job_info_advanced_group.setLayout(job_info_advanced_layout)
        
        # Extra info
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("Extra Info:"), 0, 0)
        self.extra_info_edit = HighlightableLineEdit()
        self.extra_info_edit.setToolTip("Additional information for the job (comma-separated).")
        job_info_advanced_layout.addWidget(self.extra_info_edit, 0, 1)
        
        # On job complete
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("On Job Complete:"), 1, 0)
        self.on_job_complete_edit = HighlightableLineEdit()
        self.on_job_complete_edit.setToolTip("Script to run when the job completes.")
        job_info_advanced_layout.addWidget(self.on_job_complete_edit, 1, 1)
        
        # Pre job script
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("Pre Job Script:"), 2, 0)
        self.pre_job_script_edit = HighlightableLineEdit()
        self.pre_job_script_edit.setToolTip("Script to run before the job starts.")
        job_info_advanced_layout.addWidget(self.pre_job_script_edit, 2, 1)
        
        # Post job script
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("Post Job Script:"), 3, 0)
        self.post_job_script_edit = HighlightableLineEdit()
        self.post_job_script_edit.setToolTip("Script to run after the job completes.")
        job_info_advanced_layout.addWidget(self.post_job_script_edit, 3, 1)
        
        # Pre task script
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("Pre Task Script:"), 4, 0)
        self.pre_task_script_edit = HighlightableLineEdit()
        self.pre_task_script_edit.setToolTip("Script to run before each task starts.")
        job_info_advanced_layout.addWidget(self.pre_task_script_edit, 4, 1)
        
        # Post task script
        job_info_advanced_layout.addWidget(QtWidgets.QLabel("Post Task Script:"), 5, 0)
        self.post_task_script_edit = HighlightableLineEdit()
        self.post_task_script_edit.setToolTip("Script to run after each task completes.")
        job_info_advanced_layout.addWidget(self.post_task_script_edit, 5, 1)
        
        right_layout.addWidget(job_info_advanced_group)
        
        # Environment Variables section
        env_group = QtWidgets.QGroupBox("Environment Variables")
        env_layout = QtWidgets.QGridLayout()
        env_layout.setSpacing(8)
        env_group.setLayout(env_layout)
        
        # Use current environment
        env_layout.addWidget(QtWidgets.QLabel("Use Current Environment:"), 0, 0)
        self.use_current_environment_check = HighlightableCheckBox("")
        self.use_current_environment_check.setToolTip("Whether to use the current environment variables.")
        env_layout.addWidget(self.use_current_environment_check, 0, 1)
        
        # Environment keys
        env_layout.addWidget(QtWidgets.QLabel("Environment Keys:"), 1, 0)
        self.environment_keys_edit = HighlightableLineEdit()
        self.environment_keys_edit.setToolTip("Environment variables to include (comma-separated).")
        env_layout.addWidget(self.environment_keys_edit, 1, 1)
        
        # Environment
        env_layout.addWidget(QtWidgets.QLabel("Environment:"), 2, 0)
        self.environment_edit = HighlightableLineEdit()
        self.environment_edit.setToolTip("Environment variables as key=value pairs (comma-separated).")
        env_layout.addWidget(self.environment_edit, 2, 1)
        
        # Omit environment keys
        env_layout.addWidget(QtWidgets.QLabel("Omit Environment Keys:"), 3, 0)
        self.omit_environment_keys_edit = HighlightableLineEdit()
        self.omit_environment_keys_edit.setToolTip("Environment variables to exclude (comma-separated).")
        env_layout.addWidget(self.omit_environment_keys_edit, 3, 1)
        
        right_layout.addWidget(env_group)
        
        # Add stretch to push content to top
        right_layout.addStretch()
    
    def _setup_responsive_behavior(self):
        """Set up responsive behavior controlled by main panel."""
        # Override resize event to detect when we're about to overflow
        original_resize = self.resizeEvent
        def responsive_resize_event(event):
            self._check_for_overflow(event)
            if original_resize:
                original_resize(event)
        self.resizeEvent = responsive_resize_event
    
    def _check_for_overflow(self, event):
        """Check if the view is about to overflow and trigger layout change."""
        # Only check if we're currently in two-column mode
        if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
            panel_width = event.size().width()
            # Calculate if we have enough space for two columns
            # Use a more conservative breakpoint to prevent scrollbar
            available_width = panel_width - 60  # Account for margins and padding
            
            # If we're getting close to the breakpoint, force single column
            if available_width < Sizes.RESPONSIVE_BREAKPOINT + 40:  # 40px buffer
                self.set_layout_mode(False)
    
    def set_layout_mode(self, is_two_columns: bool):
        """Set the layout mode based on main panel's responsive state.
        
        Args:
            is_two_columns (bool): True for two columns, False for one column
        """
        if is_two_columns:
            # Set to two columns
            if self.content_layout.direction() == QtWidgets.QBoxLayout.TopToBottom:
                self.content_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)
                self.content_layout.setSpacing(Sizes.SETTINGS_SPACING)
                # Set minimum widths for two-column layout
                self.left_column_widget.setMinimumWidth(Sizes.JOB_SETTINGS_MIN_WIDTH - 50)
                self.right_column_widget.setMinimumWidth(Sizes.MACHINE_SETTINGS_MIN_WIDTH - 50)
        else:
            # Set to one column
            if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                self.content_layout.setSpacing(20)  # More spacing when stacked vertically
                # Remove minimum widths for single-column layout to prevent scrollbar
                self.left_column_widget.setMinimumWidth(0)
                self.right_column_widget.setMinimumWidth(0)
    
    def _connect_signals(self):
        """Connect UI signals to model updates."""
        # Job Information signals
        self.job_name_edit.textChanged.connect(lambda t: self._on_user_changed_setting('job_name', t))
        self.comment_edit.textChanged.connect(lambda t: self._on_user_changed_setting('comment', t))
        self.department_edit.textChanged.connect(lambda t: self._on_user_changed_setting('department', t))
        
        # Script Submission signals
        self.submit_script_as_auxiliary_combo.currentTextChanged.connect(lambda t: self._on_user_changed_setting('submit_script_as_auxiliary_file', t))
        self.copy_script_combo.currentTextChanged.connect(lambda t: self._on_user_changed_setting('copy_script', t))
        self.copy_script_path_edit.textChanged.connect(lambda t: self._on_user_changed_setting('copy_script_path', t))
        self.submit_copied_script_combo.currentTextChanged.connect(lambda t: self._on_user_changed_setting('submit_copied_script', t))
        
        # Build Job signals
        self.submission_is_build_job_check.toggled.connect(lambda c: self._on_user_changed_setting('submission_is_build_job', c))
        self.build_job_name_edit.textChanged.connect(lambda t: self._on_user_changed_setting('build_job_name', t))
        self.pre_build_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('pre_build_job_script', t))
        self.post_build_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('post_build_job_script', t))
        self.build_job_as_auxiliary_combo.currentTextChanged.connect(lambda t: self._on_user_changed_setting('build_job_as_auxiliary_file', t))
        self.delete_build_job_script_combo.currentTextChanged.connect(lambda t: self._on_user_changed_setting('delete_build_job_script', t))
        
        # Script Job signals
        self.script_job_script_path_edit.textChanged.connect(lambda t: self._on_user_changed_setting('script_job_script_path', t))
        
        # Job Info signals
        self.extra_info_edit.textChanged.connect(lambda t: self._on_user_changed_setting('extra_info', t))
        self.on_job_complete_edit.textChanged.connect(lambda t: self._on_user_changed_setting('on_job_complete', t))
        self.pre_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('pre_job_script', t))
        self.post_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('post_job_script', t))
        self.pre_task_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('pre_task_script', t))
        self.post_task_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('post_task_script', t))
        
        # Environment Variables signals
        self.use_current_environment_check.toggled.connect(lambda c: self._on_user_changed_setting('use_current_environment', c))
        self.environment_keys_edit.textChanged.connect(lambda t: self._on_user_changed_setting('environment_keys', t))
        self.environment_edit.textChanged.connect(lambda t: self._on_user_changed_setting('environment', t))
        self.omit_environment_keys_edit.textChanged.connect(lambda t: self._on_user_changed_setting('omit_environment_keys', t))
        
        # Model change signals
        self.settings_model.extraSettingsChanged.connect(self._on_extra_settings_changed)
    
    def _on_user_changed_setting(self, param_name, value):
        """Handle user changes to extra settings with tracking.
        
        Args:
            param_name: The parameter name
            value: The new value
        """
        # Update the model with the new value
        self.settings_model.set_extra_setting(param_name, value)
        
        # Mark as user-changed for tracking
        self.settings_model.mark_as_user_changed(param_name)
        
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.extra_settings_view')
        logger.debug(f"User changed extra setting: {param_name} = {value}")
    
    def _update_model_setting(self, param_name: str, value, setting_type: str) -> None:
        """Update the settings model with a new value.
        
        This method is called by the WidgetChangeTrackingMixin.
        
        Args:
            param_name: The parameter name
            value: The new value
            setting_type: 'job', 'machine', or 'extra' (always 'extra' for this view)
        """
        self.settings_model.set_extra_setting(param_name, value)
    

    
    def _load_settings_from_model(self):
        """Load current settings from the model into the UI."""
        # Block signals to prevent feedback loops
        self._block_signals(True)
        
        # Disable change tracking during programmatic updates
        self.settings_model.disable_user_change_tracking()
        
        try:
            # Load extra settings
            extra_settings = self.settings_model.get_all_extra_settings()
            
            # Job Information
            self.job_name_edit.setText(extra_settings.get('job_name', ''))
            self.comment_edit.setText(extra_settings.get('comment', ''))
            self.department_edit.setText(extra_settings.get('department', ''))
            
            # Script Submission
            self._set_combo_text(self.submit_script_as_auxiliary_combo, extra_settings.get('submit_script_as_auxiliary_file', 'Default'))
            self._set_combo_text(self.copy_script_combo, extra_settings.get('copy_script', 'Default'))
            self.copy_script_path_edit.setText(str(extra_settings.get('copy_script_path', '')))
            self._set_combo_text(self.submit_copied_script_combo, extra_settings.get('submit_copied_script', 'Default'))
            
            # Build Job
            self.submission_is_build_job_check.setChecked(extra_settings.get('submission_is_build_job', False))
            self.build_job_name_edit.setText(str(extra_settings.get('build_job_name', '')))
            self.pre_build_job_script_edit.setText(str(extra_settings.get('pre_build_job_script', '')))
            self.post_build_job_script_edit.setText(str(extra_settings.get('post_build_job_script', '')))
            self._set_combo_text(self.build_job_as_auxiliary_combo, extra_settings.get('build_job_as_auxiliary_file', 'Default'))
            self._set_combo_text(self.delete_build_job_script_combo, extra_settings.get('delete_build_job_script', 'Default'))
            
            # Script Job
            self.script_job_script_path_edit.setText(str(extra_settings.get('script_job_script_path', '')))
            
            # Job Info
            self.extra_info_edit.setText(str(extra_settings.get('extra_info', '')))
            self.on_job_complete_edit.setText(str(extra_settings.get('on_job_complete', '')))
            self.pre_job_script_edit.setText(str(extra_settings.get('pre_job_script', '')))
            self.post_job_script_edit.setText(str(extra_settings.get('post_job_script', '')))
            self.pre_task_script_edit.setText(str(extra_settings.get('pre_task_script', '')))
            self.post_task_script_edit.setText(str(extra_settings.get('post_task_script', '')))
            
            # Environment Variables
            self.use_current_environment_check.setChecked(extra_settings.get('use_current_environment', False))
            self.environment_keys_edit.setText(str(extra_settings.get('environment_keys', '')))
            self.environment_edit.setText(str(extra_settings.get('environment', '')))
            self.omit_environment_keys_edit.setText(str(extra_settings.get('omit_environment_keys', '')))
        finally:
            # Re-enable signals
            self._block_signals(False)
            
                    # Re-enable change tracking
        self.settings_model.enable_user_change_tracking()
    
    def _set_combo_text(self, combo, text):
        """Set combo box text safely, handling missing items."""
        index = combo.findText(str(text))
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            # If text not found, add it temporarily and set it
            combo.addItem(str(text))
            combo.setCurrentText(str(text))
    
    def _block_signals(self, block):
        """Block or unblock signals for all UI controls."""
        # Job Information controls
        self.job_name_edit.blockSignals(block)
        self.comment_edit.blockSignals(block)
        self.department_edit.blockSignals(block)
        
        # Script Submission controls
        self.submit_script_as_auxiliary_combo.blockSignals(block)
        self.copy_script_combo.blockSignals(block)
        self.copy_script_path_edit.blockSignals(block)
        self.submit_copied_script_combo.blockSignals(block)
        
        # Build Job controls
        self.submission_is_build_job_check.blockSignals(block)
        self.build_job_name_edit.blockSignals(block)
        self.pre_build_job_script_edit.blockSignals(block)
        self.post_build_job_script_edit.blockSignals(block)
        self.build_job_as_auxiliary_combo.blockSignals(block)
        self.delete_build_job_script_combo.blockSignals(block)
        
        # Script Job controls
        self.script_job_script_path_edit.blockSignals(block)
        
        # Job Info controls
        self.extra_info_edit.blockSignals(block)
        self.on_job_complete_edit.blockSignals(block)
        self.pre_job_script_edit.blockSignals(block)
        self.post_job_script_edit.blockSignals(block)
        self.pre_task_script_edit.blockSignals(block)
        self.post_task_script_edit.blockSignals(block)
        
        # Environment Variables controls
        self.use_current_environment_check.blockSignals(block)
        self.environment_keys_edit.blockSignals(block)
        self.environment_edit.blockSignals(block)
        self.omit_environment_keys_edit.blockSignals(block)
    
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
            # Job Information
            self.job_name_edit.setObjectName("job_name")
            self.comment_edit.setObjectName("comment")
            self.department_edit.setObjectName("department")
            
            # Script Submission
            self.submit_script_as_auxiliary_combo.setObjectName("submit_script_as_auxiliary_file")
            self.copy_script_combo.setObjectName("copy_script")
            self.copy_script_path_edit.setObjectName("copy_script_path")
            self.submit_copied_script_combo.setObjectName("submit_copied_script")
            
            # Build Job
            self.submission_is_build_job_check.setObjectName("submission_is_build_job")
            self.build_job_name_edit.setObjectName("build_job_name")
            self.pre_build_job_script_edit.setObjectName("pre_build_job_script")
            self.post_build_job_script_edit.setObjectName("post_build_job_script")
            self.build_job_as_auxiliary_combo.setObjectName("build_job_as_auxiliary_file")
            self.delete_build_job_script_combo.setObjectName("delete_build_job_script")
            
            # Script Job
            self.script_job_script_path_edit.setObjectName("script_job_script_path")
            
            # Job Info
            self.extra_info_edit.setObjectName("extra_info")
            self.on_job_complete_edit.setObjectName("on_job_complete")
            self.pre_job_script_edit.setObjectName("pre_job_script")
            self.post_job_script_edit.setObjectName("post_job_script")
            self.pre_task_script_edit.setObjectName("pre_task_script")
            self.post_task_script_edit.setObjectName("post_task_script")
            
            # Environment Variables
            self.use_current_environment_check.setObjectName("use_current_environment")
            self.environment_keys_edit.setObjectName("environment_keys")
            self.environment_edit.setObjectName("environment")
            self.omit_environment_keys_edit.setObjectName("omit_environment_keys")
            
            # Apply configuration to extra settings controls
            # Job Information
            apply_panel_config(self.job_name_edit, "job_name")
            apply_panel_config(self.comment_edit, "comment")
            apply_panel_config(self.department_edit, "department")
            
            # Script Submission
            apply_panel_config(self.submit_script_as_auxiliary_combo, "submit_script_as_auxiliary_file")
            apply_panel_config(self.copy_script_combo, "copy_script")
            apply_panel_config(self.copy_script_path_edit, "copy_script_path")
            apply_panel_config(self.submit_copied_script_combo, "submit_copied_script")
            
            # Build Job
            apply_panel_config(self.submission_is_build_job_check, "submission_is_build_job")
            apply_panel_config(self.build_job_name_edit, "build_job_name")
            apply_panel_config(self.pre_build_job_script_edit, "pre_build_job_script")
            apply_panel_config(self.post_build_job_script_edit, "post_build_job_script")
            apply_panel_config(self.build_job_as_auxiliary_combo, "build_job_as_auxiliary_file")
            apply_panel_config(self.delete_build_job_script_combo, "delete_build_job_script")
            
            # Script Job
            apply_panel_config(self.script_job_script_path_edit, "script_job_script_path")
            
            # Job Info
            apply_panel_config(self.extra_info_edit, "extra_info")
            apply_panel_config(self.on_job_complete_edit, "on_job_complete")
            apply_panel_config(self.pre_job_script_edit, "pre_job_script")
            apply_panel_config(self.post_job_script_edit, "post_job_script")
            apply_panel_config(self.pre_task_script_edit, "pre_task_script")
            apply_panel_config(self.post_task_script_edit, "post_task_script")
            
            # Environment Variables
            apply_panel_config(self.use_current_environment_check, "use_current_environment")
            apply_panel_config(self.environment_keys_edit, "environment_keys")
            apply_panel_config(self.environment_edit, "environment")
            apply_panel_config(self.omit_environment_keys_edit, "omit_environment_keys")
            
        except Exception as e:
            logger.error(f"Error applying configuration to ExtraSettingsView: {e}")
    
    def _register_widgets_for_visual_indication(self):
        """Register all widgets for visual indication based on storage state."""
        # Job Information widgets
        self.register_widget_for_visual_indication(self.job_name_edit, 'job_name')
        self.register_widget_for_visual_indication(self.comment_edit, 'comment')
        self.register_widget_for_visual_indication(self.department_edit, 'department')
        
        # Script Submission widgets
        self.register_widget_for_visual_indication(self.submit_script_as_auxiliary_combo, 'submit_script_as_auxiliary_file')
        self.register_widget_for_visual_indication(self.copy_script_combo, 'copy_script')
        self.register_widget_for_visual_indication(self.copy_script_path_edit, 'copy_script_path')
        self.register_widget_for_visual_indication(self.submit_copied_script_combo, 'submit_copied_script')
        
        # Build Job widgets
        self.register_widget_for_visual_indication(self.submission_is_build_job_check, 'submission_is_build_job')
        self.register_widget_for_visual_indication(self.build_job_name_edit, 'build_job_name')
        self.register_widget_for_visual_indication(self.pre_build_job_script_edit, 'pre_build_job_script')
        self.register_widget_for_visual_indication(self.post_build_job_script_edit, 'post_build_job_script')
        self.register_widget_for_visual_indication(self.build_job_as_auxiliary_combo, 'build_job_as_auxiliary_file')
        self.register_widget_for_visual_indication(self.delete_build_job_script_combo, 'delete_build_job_script')
        
        # Script Job widgets
        self.register_widget_for_visual_indication(self.script_job_script_path_edit, 'script_job_script_path')
        
        # Job Info widgets
        self.register_widget_for_visual_indication(self.extra_info_edit, 'extra_info')
        self.register_widget_for_visual_indication(self.on_job_complete_edit, 'on_job_complete')
        self.register_widget_for_visual_indication(self.pre_job_script_edit, 'pre_job_script')
        self.register_widget_for_visual_indication(self.post_job_script_edit, 'post_job_script')
        self.register_widget_for_visual_indication(self.pre_task_script_edit, 'pre_task_script')
        self.register_widget_for_visual_indication(self.post_task_script_edit, 'post_task_script')
        
        # Environment Variables widgets
        self.register_widget_for_visual_indication(self.use_current_environment_check, 'use_current_environment')
        self.register_widget_for_visual_indication(self.environment_keys_edit, 'environment_keys')
        self.register_widget_for_visual_indication(self.environment_edit, 'environment')
        self.register_widget_for_visual_indication(self.omit_environment_keys_edit, 'omit_environment_keys')
        
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.extra_settings_view')
        logger.debug("Registered all widgets for visual indication in ExtraSettingsView")
    
    def _register_widgets_for_change_tracking(self):
        """Register all widgets for change tracking to detect user vs programmatic changes."""
        # Job Information widgets
        self.register_widget_for_change_tracking(self.job_name_edit, 'job_name')
        self.register_widget_for_change_tracking(self.comment_edit, 'comment')
        self.register_widget_for_change_tracking(self.department_edit, 'department')
        
        # Script Submission widgets
        self.register_widget_for_change_tracking(self.submit_script_as_auxiliary_combo, 'submit_script_as_auxiliary_file')
        self.register_widget_for_change_tracking(self.copy_script_combo, 'copy_script')
        self.register_widget_for_change_tracking(self.copy_script_path_edit, 'copy_script_path')
        self.register_widget_for_change_tracking(self.submit_copied_script_combo, 'submit_copied_script')
        
        # Build Job widgets
        self.register_widget_for_change_tracking(self.submission_is_build_job_check, 'submission_is_build_job')
        self.register_widget_for_change_tracking(self.build_job_name_edit, 'build_job_name')
        self.register_widget_for_change_tracking(self.pre_build_job_script_edit, 'pre_build_job_script')
        self.register_widget_for_change_tracking(self.post_build_job_script_edit, 'post_build_job_script')
        self.register_widget_for_change_tracking(self.build_job_as_auxiliary_combo, 'build_job_as_auxiliary_file')
        self.register_widget_for_change_tracking(self.delete_build_job_script_combo, 'delete_build_job_script')
        
        # Script Job widgets
        self.register_widget_for_change_tracking(self.script_job_script_path_edit, 'script_job_script_path')
        
        # Job Info widgets
        self.register_widget_for_change_tracking(self.extra_info_edit, 'extra_info')
        self.register_widget_for_change_tracking(self.on_job_complete_edit, 'on_job_complete')
        self.register_widget_for_change_tracking(self.pre_job_script_edit, 'pre_job_script')
        self.register_widget_for_change_tracking(self.post_job_script_edit, 'post_job_script')
        self.register_widget_for_change_tracking(self.pre_task_script_edit, 'pre_task_script')
        self.register_widget_for_change_tracking(self.post_task_script_edit, 'post_task_script')
        
        # Environment Variables widgets
        self.register_widget_for_change_tracking(self.use_current_environment_check, 'use_current_environment')
        self.register_widget_for_change_tracking(self.environment_keys_edit, 'environment_keys')
        self.register_widget_for_change_tracking(self.environment_edit, 'environment')
        self.register_widget_for_change_tracking(self.omit_environment_keys_edit, 'omit_environment_keys')
        
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.extra_settings_view')
        logger.debug("Registered all widgets for change tracking in ExtraSettingsView") 