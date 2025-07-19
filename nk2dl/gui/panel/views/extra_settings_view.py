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
        left_layout.setSpacing(8)
        self.left_column_widget.setLayout(left_layout)
        
        # Job section
        job_info_group = QtWidgets.QGroupBox("Job")
        job_info_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        job_info_layout = QtWidgets.QGridLayout()
        job_info_layout.setSpacing(8)
        job_info_layout.setContentsMargins(8, 8, 8, 8)  # Reduced top margin
        job_info_group.setLayout(job_info_layout)
        
        job_name_label = QtWidgets.QLabel("Job Name")
        job_name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        job_name_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(job_name_label, 0, 0)
        self.job_name_edit = HighlightableLineEdit()
        self.job_name_edit.setToolTip("The name of your job. This is optional, and if left blank, it will default to 'Untitled'.")
        job_info_layout.addWidget(self.job_name_edit, 0, 1, 1, 2)
        
        comment_label = QtWidgets.QLabel("Comment")
        comment_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        comment_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(comment_label, 1, 0)
        self.comment_edit = HighlightableLineEdit()
        self.comment_edit.setToolTip("A simple description of your job. This is optional and can be left blank.")
        job_info_layout.addWidget(self.comment_edit, 1, 1, 1, 2)
        
        department_label = QtWidgets.QLabel("Department")
        department_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        department_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(department_label, 2, 0)
        self.department_edit = HighlightableLineEdit()
        self.department_edit.setToolTip("The department you belong to. This is optional and can be left blank.")
        job_info_layout.addWidget(self.department_edit, 2, 1, 1, 2)
        
        # Extra Info (moved from Job Info section)
        extra_info_label = QtWidgets.QLabel("Extra Info")
        extra_info_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        extra_info_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(extra_info_label, 3, 0)
        self.extra_info_edit = HighlightableLineEdit()
        self.extra_info_edit.setToolTip("Additional information for the job (comma-separated).")
        job_info_layout.addWidget(self.extra_info_edit, 3, 1, 1, 2)
        
        # Job Dependencies
        job_deps_label = QtWidgets.QLabel("Job Dependencies")
        job_deps_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        job_deps_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(job_deps_label, 4, 0)
        self.job_dependencies_edit = HighlightableLineEdit()
        self.job_dependencies_edit.setToolTip("Comma or space separated list of job IDs that this job depends on.")
        job_info_layout.addWidget(self.job_dependencies_edit, 4, 1)
        
        # Add browse button for job dependencies
        self.job_deps_browse_btn = QtWidgets.QPushButton("Browse")
        self.job_deps_browse_btn.setFixedWidth(Sizes.BUTTON_WIDTH)
        self.job_deps_browse_btn.setToolTip("Browse for job dependencies")
        job_info_layout.addWidget(self.job_deps_browse_btn, 4, 2)
        
        # Plugin checkboxes (moved from Plugin section) - all on one row
        plugin_label = QtWidgets.QLabel("")
        plugin_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_info_layout.addWidget(plugin_label, 5, 0)
        
        # Create horizontal layout for the three checkboxes
        plugin_checkboxes_row = QtWidgets.QHBoxLayout()
        plugin_checkboxes_row.setSpacing(20)  # Space between checkboxes
        
        self.use_batch_mode_check = HighlightableCheckBox("Use Batch Mode")
        self.use_batch_mode_check.setToolTip("This uses the Nuke plugin's Batch Mode. It keeps the Nuke script loaded in memory between frames, which reduces the overhead of rendering the job.")
        plugin_checkboxes_row.addWidget(self.use_batch_mode_check)
        
        self.reload_plugin_check = HighlightableCheckBox("Reload Plugin Between Tasks")
        self.reload_plugin_check.setToolTip("If checked, Nuke will force all memory to be released before starting the next task, but this can increase the overhead time between tasks.")
        plugin_checkboxes_row.addWidget(self.reload_plugin_check)
        
        self.render_settings_from_metadata_check = HighlightableCheckBox("Render Settings from Metadata")
        self.render_settings_from_metadata_check.setToolTip("Whether to extract submission settings from write node metadata.")
        plugin_checkboxes_row.addWidget(self.render_settings_from_metadata_check)
        
        plugin_checkboxes_row.addStretch()  # Push checkboxes to the left
        job_info_layout.addLayout(plugin_checkboxes_row, 5, 1)
        
        left_layout.addWidget(job_info_group)
        
        # Nukescript section
        script_submission_group = QtWidgets.QGroupBox("Nukescript")
        script_submission_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        script_submission_layout = QtWidgets.QVBoxLayout()
        script_submission_layout.setSpacing(8)
        script_submission_layout.setContentsMargins(8, 8, 8, 8)
        script_submission_group.setLayout(script_submission_layout)
        
        # Submit script as auxiliary file
        submit_auxiliary_row = QtWidgets.QHBoxLayout()
        submit_auxiliary_row.setSpacing(10)
        empty_label4 = QtWidgets.QLabel("")
        empty_label4.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        submit_auxiliary_row.addWidget(empty_label4)
        self.submit_script_as_auxiliary_check = HighlightableCheckBox("Submit Script as Auxiliary")
        self.submit_script_as_auxiliary_check.setToolTip("Whether to submit the script as an auxiliary file.")
        submit_auxiliary_row.addWidget(self.submit_script_as_auxiliary_check)
        submit_auxiliary_row.addStretch()
        script_submission_layout.addLayout(submit_auxiliary_row)
        
        # Copy script and Submit copied script in same row
        copy_script_row = QtWidgets.QHBoxLayout()
        copy_script_row.setSpacing(10)
        empty_label5 = QtWidgets.QLabel("")
        empty_label5.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        copy_script_row.addWidget(empty_label5)
        self.copy_script_check = HighlightableCheckBox("Copy Script")
        self.copy_script_check.setToolTip("Whether to copy the script before submission.")
        copy_script_row.addWidget(self.copy_script_check)
        
        # Add some spacing between the two checkboxes
        copy_script_row.addSpacing(20)
        
        self.submit_copied_script_check = HighlightableCheckBox("Submit Copied Script")
        self.submit_copied_script_check.setToolTip("Whether to submit the copied script instead of the original.")
        copy_script_row.addWidget(self.submit_copied_script_check)
        copy_script_row.addStretch()
        script_submission_layout.addLayout(copy_script_row)
        
        # Copy script path
        copy_script_path_row = QtWidgets.QHBoxLayout()
        copy_script_path_row.setSpacing(10)
        copy_script_path_label = QtWidgets.QLabel("Copy Script Path")
        copy_script_path_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        copy_script_path_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        copy_script_path_row.addWidget(copy_script_path_label)
        self.copy_script_path_edit = HighlightableLineEdit()
        self.copy_script_path_edit.setToolTip("Path where to copy the script.")
        copy_script_path_row.addWidget(self.copy_script_path_edit, 1)  # Add stretch factor
        script_submission_layout.addLayout(copy_script_path_row)
        
        left_layout.addWidget(script_submission_group)
        
        # Python Script Job section (moved from right column)
        python_script_job_group = QtWidgets.QGroupBox("Python Script Job")
        python_script_job_layout = QtWidgets.QVBoxLayout()
        python_script_job_layout.setSpacing(8)
        python_script_job_group.setLayout(python_script_job_layout)
        
        # Script job script path
        python_script_job_path_row = QtWidgets.QHBoxLayout()
        python_script_job_path_row.setSpacing(10)
        python_script_job_path_label = QtWidgets.QLabel("Script Job Path")
        python_script_job_path_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        python_script_job_path_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        python_script_job_path_row.addWidget(python_script_job_path_label)
        self.script_job_script_path_edit = HighlightableLineEdit()
        self.script_job_script_path_edit.setToolTip("Path to the script for script jobs.")
        python_script_job_path_row.addWidget(self.script_job_script_path_edit, 1)  # Add stretch factor
        python_script_job_layout.addLayout(python_script_job_path_row)
        
        left_layout.addWidget(python_script_job_group)
        
        # Add stretch to push content to top
        left_layout.addStretch()
    
    def _create_right_column(self):
        """Create the right column with Build Job, Job Info, and Environment Variables sections."""
        self.right_column_widget = QtWidgets.QWidget()
        # Use a smaller minimum width to prevent horizontal scrollbar
        self.right_column_widget.setMinimumWidth(Sizes.MACHINE_SETTINGS_MIN_WIDTH - 50)
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        self.right_column_widget.setLayout(right_layout)
        
        # Build Job section
        build_job_group = QtWidgets.QGroupBox("Build Job")
        build_job_layout = QtWidgets.QVBoxLayout()
        build_job_layout.setSpacing(8)
        build_job_group.setLayout(build_job_layout)
        
        # Submission is build job, Build job as auxiliary, and Delete build script in same row
        submission_build_row = QtWidgets.QHBoxLayout()
        submission_build_row.setSpacing(10)
        empty_label7 = QtWidgets.QLabel("")
        empty_label7.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        submission_build_row.addWidget(empty_label7)
        self.submission_is_build_job_check = HighlightableCheckBox("Submission is Build Job")
        self.submission_is_build_job_check.setToolTip("Whether this submission is a build job.")
        submission_build_row.addWidget(self.submission_is_build_job_check)
        
        # Add some spacing between the checkboxes
        submission_build_row.addSpacing(20)
        
        self.build_job_as_auxiliary_check = HighlightableCheckBox("Build Job as Auxiliary")
        self.build_job_as_auxiliary_check.setToolTip("Whether to submit the build job as an auxiliary file.")
        submission_build_row.addWidget(self.build_job_as_auxiliary_check)
        
        # Add some spacing between the checkboxes
        submission_build_row.addSpacing(20)
        
        self.delete_build_job_script_check = HighlightableCheckBox("Delete Build Script")
        self.delete_build_job_script_check.setToolTip("Whether to delete the build job script after completion.")
        submission_build_row.addWidget(self.delete_build_job_script_check)
        submission_build_row.addStretch()
        build_job_layout.addLayout(submission_build_row)
        
        # Build job name
        build_job_name_row = QtWidgets.QHBoxLayout()
        build_job_name_row.setSpacing(10)
        build_job_name_label = QtWidgets.QLabel("Build Job Name")
        build_job_name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        build_job_name_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        build_job_name_row.addWidget(build_job_name_label)
        self.build_job_name_edit = HighlightableLineEdit()
        self.build_job_name_edit.setToolTip("Name for the build job.")
        build_job_name_row.addWidget(self.build_job_name_edit, 1)  # Add stretch factor
        build_job_layout.addLayout(build_job_name_row)
        
        # Pre-build job script
        pre_build_script_row = QtWidgets.QHBoxLayout()
        pre_build_script_row.setSpacing(10)
        pre_build_script_label = QtWidgets.QLabel("Pre-build Script")
        pre_build_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pre_build_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        pre_build_script_row.addWidget(pre_build_script_label)
        self.pre_build_job_script_edit = HighlightableLineEdit()
        self.pre_build_job_script_edit.setToolTip("Script to run before the build job.")
        pre_build_script_row.addWidget(self.pre_build_job_script_edit, 1)  # Add stretch factor
        build_job_layout.addLayout(pre_build_script_row)
        
        # Post-build job script
        post_build_script_row = QtWidgets.QHBoxLayout()
        post_build_script_row.setSpacing(10)
        post_build_script_label = QtWidgets.QLabel("Post-build Script")
        post_build_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        post_build_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        post_build_script_row.addWidget(post_build_script_label)
        self.post_build_job_script_edit = HighlightableLineEdit()
        self.post_build_job_script_edit.setToolTip("Script to run after the build job.")
        post_build_script_row.addWidget(self.post_build_job_script_edit, 1)  # Add stretch factor
        build_job_layout.addLayout(post_build_script_row)
        


        
        right_layout.addWidget(build_job_group)
        
        # Deadline Scripts section
        job_info_advanced_group = QtWidgets.QGroupBox("Deadline Scripts")
        job_info_advanced_layout = QtWidgets.QVBoxLayout()
        job_info_advanced_layout.setSpacing(8)
        job_info_advanced_group.setLayout(job_info_advanced_layout)
        
        # On job complete
        on_job_complete_row = QtWidgets.QHBoxLayout()
        on_job_complete_row.setSpacing(10)
        on_job_complete_label = QtWidgets.QLabel("On Job Complete")
        on_job_complete_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        on_job_complete_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        on_job_complete_row.addWidget(on_job_complete_label)
        self.on_job_complete_edit = HighlightableLineEdit()
        self.on_job_complete_edit.setToolTip("Script to run when the job completes.")
        on_job_complete_row.addWidget(self.on_job_complete_edit, 1)  # Add stretch factor
        job_info_advanced_layout.addLayout(on_job_complete_row)
        
        # Pre job script
        pre_job_script_row = QtWidgets.QHBoxLayout()
        pre_job_script_row.setSpacing(10)
        pre_job_script_label = QtWidgets.QLabel("Pre Job Script")
        pre_job_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pre_job_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        pre_job_script_row.addWidget(pre_job_script_label)
        self.pre_job_script_edit = HighlightableLineEdit()
        self.pre_job_script_edit.setToolTip("Script to run before the job starts.")
        pre_job_script_row.addWidget(self.pre_job_script_edit, 1)  # Add stretch factor
        job_info_advanced_layout.addLayout(pre_job_script_row)
        
        # Post job script
        post_job_script_row = QtWidgets.QHBoxLayout()
        post_job_script_row.setSpacing(10)
        post_job_script_label = QtWidgets.QLabel("Post Job Script")
        post_job_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        post_job_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        post_job_script_row.addWidget(post_job_script_label)
        self.post_job_script_edit = HighlightableLineEdit()
        self.post_job_script_edit.setToolTip("Script to run after the job completes.")
        post_job_script_row.addWidget(self.post_job_script_edit, 1)  # Add stretch factor
        job_info_advanced_layout.addLayout(post_job_script_row)
        
        # Pre task script
        pre_task_script_row = QtWidgets.QHBoxLayout()
        pre_task_script_row.setSpacing(10)
        pre_task_script_label = QtWidgets.QLabel("Pre Task Script")
        pre_task_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pre_task_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        pre_task_script_row.addWidget(pre_task_script_label)
        self.pre_task_script_edit = HighlightableLineEdit()
        self.pre_task_script_edit.setToolTip("Script to run before each task starts.")
        pre_task_script_row.addWidget(self.pre_task_script_edit, 1)  # Add stretch factor
        job_info_advanced_layout.addLayout(pre_task_script_row)
        
        # Post task script
        post_task_script_row = QtWidgets.QHBoxLayout()
        post_task_script_row.setSpacing(10)
        post_task_script_label = QtWidgets.QLabel("Post Task Script")
        post_task_script_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        post_task_script_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        post_task_script_row.addWidget(post_task_script_label)
        self.post_task_script_edit = HighlightableLineEdit()
        self.post_task_script_edit.setToolTip("Script to run after each task completes.")
        post_task_script_row.addWidget(self.post_task_script_edit, 1)  # Add stretch factor
        job_info_advanced_layout.addLayout(post_task_script_row)
        
        right_layout.addWidget(job_info_advanced_group)
        
        # Environment Variables section
        env_group = QtWidgets.QGroupBox("Environment Variables")
        env_layout = QtWidgets.QVBoxLayout()
        env_layout.setSpacing(8)
        env_group.setLayout(env_layout)
        
        # Use current environment
        use_current_env_row = QtWidgets.QHBoxLayout()
        use_current_env_row.setSpacing(10)
        empty_label10 = QtWidgets.QLabel("")
        empty_label10.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        use_current_env_row.addWidget(empty_label10)
        self.use_current_environment_check = HighlightableCheckBox("Use Current Environment")
        self.use_current_environment_check.setToolTip("Whether to use the current environment variables.")
        use_current_env_row.addWidget(self.use_current_environment_check)
        use_current_env_row.addStretch()
        env_layout.addLayout(use_current_env_row)
        
        # Environment keys
        env_keys_row = QtWidgets.QHBoxLayout()
        env_keys_row.setSpacing(10)
        env_keys_label = QtWidgets.QLabel("Keys")
        env_keys_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        env_keys_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        env_keys_row.addWidget(env_keys_label)
        self.environment_keys_edit = HighlightableLineEdit()
        self.environment_keys_edit.setToolTip("Environment variables to include (comma-separated).")
        env_keys_row.addWidget(self.environment_keys_edit, 1)  # Add stretch factor
        env_layout.addLayout(env_keys_row)
        
        # Environment
        environment_row = QtWidgets.QHBoxLayout()
        environment_row.setSpacing(10)
        environment_label = QtWidgets.QLabel("Environment")
        environment_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        environment_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        environment_row.addWidget(environment_label)
        self.environment_edit = HighlightableLineEdit()
        self.environment_edit.setToolTip("Environment variables as key=value pairs (comma-separated).")
        environment_row.addWidget(self.environment_edit, 1)  # Add stretch factor
        env_layout.addLayout(environment_row)
        
        # Omit environment keys
        omit_env_keys_row = QtWidgets.QHBoxLayout()
        omit_env_keys_row.setSpacing(10)
        omit_env_keys_label = QtWidgets.QLabel("Omit Keys")
        omit_env_keys_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        omit_env_keys_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        omit_env_keys_row.addWidget(omit_env_keys_label)
        self.omit_environment_keys_edit = HighlightableLineEdit()
        self.omit_environment_keys_edit.setToolTip("Environment variables to exclude (comma-separated).")
        omit_env_keys_row.addWidget(self.omit_environment_keys_edit, 1)  # Add stretch factor
        env_layout.addLayout(omit_env_keys_row)
        
        right_layout.addWidget(env_group)
        
        # Add stretch to push content to top
        right_layout.addStretch()
    
    def _setup_responsive_behavior(self):
        """Set up responsive behavior controlled by main panel."""
        # No individual resize handling - will be controlled by main panel
        pass
    
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
        else:
            # Set to one column
            if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                self.content_layout.setSpacing(20)  # More spacing when stacked vertically
    
    def _connect_signals(self):
        """Connect UI signals to model updates."""
        # Job Information signals
        self.job_name_edit.textChanged.connect(lambda t: self._on_user_changed_setting('job_name', t))
        self.comment_edit.textChanged.connect(lambda t: self._on_user_changed_setting('comment', t))
        self.department_edit.textChanged.connect(lambda t: self._on_user_changed_setting('department', t))
        self.extra_info_edit.textChanged.connect(lambda t: self._on_user_changed_setting('extra_info', t))
        self.job_dependencies_edit.textChanged.connect(lambda t: self._on_user_changed_setting('job_dependencies', t))
        self.job_deps_browse_btn.clicked.connect(self._on_job_deps_browse_clicked)
        
        # Plugin Settings signals
        self.use_batch_mode_check.toggled.connect(lambda c: self._on_user_changed_setting('batch_mode', c))
        self.reload_plugin_check.toggled.connect(lambda c: self._on_user_changed_setting('reload_plugins', c))
        self.render_settings_from_metadata_check.toggled.connect(lambda c: self._on_user_changed_setting('render_settings_from_metadata', c))
        
        # Script Submission signals
        self.submit_script_as_auxiliary_check.toggled.connect(lambda c: self._on_user_changed_setting('submit_script_as_auxiliary_file', c))
        self.copy_script_check.toggled.connect(lambda c: self._on_user_changed_setting('copy_script', c))
        self.copy_script_path_edit.textChanged.connect(lambda t: self._on_user_changed_setting('copy_script_path', t))
        self.submit_copied_script_check.toggled.connect(lambda c: self._on_user_changed_setting('submit_copied_script', c))
        
        # Build Job signals
        self.submission_is_build_job_check.toggled.connect(lambda c: self._on_user_changed_setting('submission_is_build_job', c))
        self.build_job_name_edit.textChanged.connect(lambda t: self._on_user_changed_setting('build_job_name', t))
        self.pre_build_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('pre_build_job_script', t))
        self.post_build_job_script_edit.textChanged.connect(lambda t: self._on_user_changed_setting('post_build_job_script', t))
        self.build_job_as_auxiliary_check.toggled.connect(lambda c: self._on_user_changed_setting('build_job_as_auxiliary_file', c))
        self.delete_build_job_script_check.toggled.connect(lambda c: self._on_user_changed_setting('delete_build_job_script', c))
        
        # Script Job signals
        self.script_job_script_path_edit.textChanged.connect(lambda t: self._on_user_changed_setting('script_job_script_path', t))
        
        # Job Info signals
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
    
    def _on_job_deps_browse_clicked(self):
        """Handle job dependencies browse button click."""
        # TODO: Implement job dependencies browsing functionality
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.extra_settings_view')
        logger.info("Job dependencies browse functionality not yet implemented")
    
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
            self.extra_info_edit.setText(str(extra_settings.get('extra_info', '{}')))
            self.job_dependencies_edit.setText(extra_settings.get('job_dependencies', ''))
            
            # Plugin Settings
            self.use_batch_mode_check.setChecked(extra_settings.get('batch_mode', False))
            self.reload_plugin_check.setChecked(extra_settings.get('reload_plugins', False))
            self.render_settings_from_metadata_check.setChecked(extra_settings.get('render_settings_from_metadata', False))
            
            # Script Submission
            self.submit_script_as_auxiliary_check.setChecked(extra_settings.get('submit_script_as_auxiliary_file', False))
            self.copy_script_check.setChecked(extra_settings.get('copy_script', False))
            self.copy_script_path_edit.setText(str(extra_settings.get('copy_script_path', '')))
            self.submit_copied_script_check.setChecked(extra_settings.get('submit_copied_script', False))
            
            # Build Job
            self.submission_is_build_job_check.setChecked(extra_settings.get('submission_is_build_job', False))
            self.build_job_name_edit.setText(str(extra_settings.get('build_job_name', '')))
            self.pre_build_job_script_edit.setText(str(extra_settings.get('pre_build_job_script', '')))
            self.post_build_job_script_edit.setText(str(extra_settings.get('post_build_job_script', '')))
            self.build_job_as_auxiliary_check.setChecked(extra_settings.get('build_job_as_auxiliary_file', False))
            self.delete_build_job_script_check.setChecked(extra_settings.get('delete_build_job_script', False))
            
            # Script Job
            self.script_job_script_path_edit.setText(str(extra_settings.get('script_job_script_path', '')))
            
            # Job Info
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
    

    
    def _block_signals(self, block):
        """Block or unblock signals for all UI controls."""
        # Job Information controls
        self.job_name_edit.blockSignals(block)
        self.comment_edit.blockSignals(block)
        self.department_edit.blockSignals(block)
        self.job_dependencies_edit.blockSignals(block)
        
        # Plugin Settings controls
        self.use_batch_mode_check.blockSignals(block)
        self.reload_plugin_check.blockSignals(block)
        self.render_settings_from_metadata_check.blockSignals(block)
        
        # Script Submission controls
        self.submit_script_as_auxiliary_check.blockSignals(block)
        self.copy_script_check.blockSignals(block)
        self.copy_script_path_edit.blockSignals(block)
        self.submit_copied_script_check.blockSignals(block)
        
        # Build Job controls
        self.submission_is_build_job_check.blockSignals(block)
        self.build_job_name_edit.blockSignals(block)
        self.pre_build_job_script_edit.blockSignals(block)
        self.post_build_job_script_edit.blockSignals(block)
        self.build_job_as_auxiliary_check.blockSignals(block)
        self.delete_build_job_script_check.blockSignals(block)
        
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
            self.job_dependencies_edit.setObjectName("job_dependencies")
            
            # Script Submission
            self.submit_script_as_auxiliary_check.setObjectName("submit_script_as_auxiliary_file")
            self.copy_script_check.setObjectName("copy_script")
            self.copy_script_path_edit.setObjectName("copy_script_path")
            self.submit_copied_script_check.setObjectName("submit_copied_script")
            
            # Build Job
            self.submission_is_build_job_check.setObjectName("submission_is_build_job")
            self.build_job_name_edit.setObjectName("build_job_name")
            self.pre_build_job_script_edit.setObjectName("pre_build_job_script")
            self.post_build_job_script_edit.setObjectName("post_build_job_script")
            self.build_job_as_auxiliary_check.setObjectName("build_job_as_auxiliary_file")
            self.delete_build_job_script_check.setObjectName("delete_build_job_script")
            
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
            apply_panel_config(self.job_dependencies_edit, "job_dependencies")
            
            # Script Submission
            apply_panel_config(self.submit_script_as_auxiliary_check, "submit_script_as_auxiliary_file")
            apply_panel_config(self.copy_script_check, "copy_script")
            apply_panel_config(self.copy_script_path_edit, "copy_script_path")
            apply_panel_config(self.submit_copied_script_check, "submit_copied_script")
            
            # Build Job
            apply_panel_config(self.submission_is_build_job_check, "submission_is_build_job")
            apply_panel_config(self.build_job_name_edit, "build_job_name")
            apply_panel_config(self.pre_build_job_script_edit, "pre_build_job_script")
            apply_panel_config(self.post_build_job_script_edit, "post_build_job_script")
            apply_panel_config(self.build_job_as_auxiliary_check, "build_job_as_auxiliary_file")
            apply_panel_config(self.delete_build_job_script_check, "delete_build_job_script")
            
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
        self.register_widget_for_visual_indication(self.job_dependencies_edit, 'job_dependencies')
        
        # Plugin Settings widgets
        self.register_widget_for_visual_indication(self.use_batch_mode_check, 'batch_mode')
        self.register_widget_for_visual_indication(self.reload_plugin_check, 'reload_plugins')
        self.register_widget_for_visual_indication(self.render_settings_from_metadata_check, 'render_settings_from_metadata')
        
        # Script Submission widgets
        self.register_widget_for_visual_indication(self.submit_script_as_auxiliary_check, 'submit_script_as_auxiliary_file')
        self.register_widget_for_visual_indication(self.copy_script_check, 'copy_script')
        self.register_widget_for_visual_indication(self.copy_script_path_edit, 'copy_script_path')
        self.register_widget_for_visual_indication(self.submit_copied_script_check, 'submit_copied_script')
        
        # Build Job widgets
        self.register_widget_for_visual_indication(self.submission_is_build_job_check, 'submission_is_build_job')
        self.register_widget_for_visual_indication(self.build_job_name_edit, 'build_job_name')
        self.register_widget_for_visual_indication(self.pre_build_job_script_edit, 'pre_build_job_script')
        self.register_widget_for_visual_indication(self.post_build_job_script_edit, 'post_build_job_script')
        self.register_widget_for_visual_indication(self.build_job_as_auxiliary_check, 'build_job_as_auxiliary_file')
        self.register_widget_for_visual_indication(self.delete_build_job_script_check, 'delete_build_job_script')
        
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
        self.register_widget_for_change_tracking(self.job_dependencies_edit, 'job_dependencies')
        
        # Plugin Settings widgets
        self.register_widget_for_change_tracking(self.use_batch_mode_check, 'batch_mode')
        self.register_widget_for_change_tracking(self.reload_plugin_check, 'reload_plugins')
        self.register_widget_for_change_tracking(self.render_settings_from_metadata_check, 'render_settings_from_metadata')
        
        # Script Submission widgets
        self.register_widget_for_change_tracking(self.submit_script_as_auxiliary_check, 'submit_script_as_auxiliary_file')
        self.register_widget_for_change_tracking(self.copy_script_check, 'copy_script')
        self.register_widget_for_change_tracking(self.copy_script_path_edit, 'copy_script_path')
        self.register_widget_for_change_tracking(self.submit_copied_script_check, 'submit_copied_script')
        
        # Build Job widgets
        self.register_widget_for_change_tracking(self.submission_is_build_job_check, 'submission_is_build_job')
        self.register_widget_for_change_tracking(self.build_job_name_edit, 'build_job_name')
        self.register_widget_for_change_tracking(self.pre_build_job_script_edit, 'pre_build_job_script')
        self.register_widget_for_change_tracking(self.post_build_job_script_edit, 'post_build_job_script')
        self.register_widget_for_change_tracking(self.build_job_as_auxiliary_check, 'build_job_as_auxiliary_file')
        self.register_widget_for_change_tracking(self.delete_build_job_script_check, 'delete_build_job_script')
        
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