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

Usage:
    # Check if panel is available (requires Nuke + PySide)
    available, error = get_panel_availability()
    
    if available:
        panel = Nk2dlPanel()  # Create panel instance
        register_panel()      # Register the panel
    
    # Constants are available from submodules
    # from .constants import Settings, Colors, Sizes
"""

__version__ = "0.1.0"
__author__ = "Daniel Harkness"

# Get the logger before any Nuke or Qt imports
from ...common.logging import setup_logging
logger = setup_logging('nk2dl.gui.panel')

try:
    import nuke
    import nukescripts.panels as panels
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

# Only import panel components if Qt is available
if NUKE_AVAILABLE or 'QtWidgets' in locals():
    try:
        # Import all the extracted components from their directories
        from .models import TableDataModel, GSVHierarchyModel, SettingsModel
        from .views import SettingsView, NodeSettingsView, GSVView, ExtraSettingsView, ConsoleView
        from .constants import Sizes, GSVDefaults, Timing
        from .config import apply_panel_config
        from .repositories import NodeDataProvider, NodeSettingsStorage
        from .controllers import PanelProgressManager


        class Nk2dlPanel(QtWidgets.QWidget):
            """Advanced nk2dl panel using extracted MVC components.
            
            This creates a comprehensive interface by coordinating models, views, widgets,
            and delegates. Uses PySide6 for Nuke 16+ and PySide2 for earlier versions.
            """
            
            def __init__(self, parent=None):
                """Initialize the nk2dl panel."""
                if not NUKE_AVAILABLE:
                    logger.error("Nuke not available, cannot create panel")
                    return
                    
                QtWidgets.QWidget.__init__(self, parent)
                
                # Initialize models first
                self._create_models()
                
                # Set up the main layout
                self._setup_layout()
                
                # Create views and connect them to models
                self._create_views()
                
                # Create the tabbed interface
                self._create_tabbed_interface()
                
                # Create bottom controls
                self._create_bottom_controls()
                
                # Connect signals between components
                self._connect_signals()
                
                # Load initial node data
                self._load_initial_data()
                
                # Set size policy
                self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                
                # Apply panel configuration
                logger.debug("Applying panel configuration")
                self._apply_panel_configuration()
                
                logger.info(f"nk2dl panel initialized using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
            
            def _create_models(self):
                """Create all data models and repositories."""
                # Create models
                self.settings_model = SettingsModel(self)
                self.table_model = TableDataModel(self.settings_model, self)
                self.gsv_model = GSVHierarchyModel(self)
                
                # Create repositories
                self.node_data_provider = NodeDataProvider(self)
                self.settings_storage = NodeSettingsStorage()
                
                # Connect repositories to table model
                self.table_model.set_node_data_provider(self.node_data_provider)
                self.table_model.set_settings_storage(self.settings_storage)
                
                logger.info("Models and repositories created: TableDataModel, GSVHierarchyModel, SettingsModel, NodeDataProvider, NodeSettingsStorage")
            
            def _setup_layout(self):
                """Set up the main panel layout."""
                self.setLayout(QtWidgets.QVBoxLayout())
                self.layout().setSpacing(5)
                self.layout().setContentsMargins(5, 5, 5, 5)
            
            def _create_views(self):
                """Create all view components."""
                # Settings view (top section)
                self.settings_view = SettingsView(self.settings_model, self)
                
                # Node settings view (table tab) - now with settings model for inheritance
                self.node_settings_view = NodeSettingsView(self.table_model, self.settings_model, self)
                
                # GSV view (GSV tab) - only for Nuke 15.1+
                if NUKE_AVAILABLE and self._is_nuke_15_1_or_later():
                    self.gsv_view = GSVView(self.gsv_model, self)
                else:
                    self.gsv_view = None
                
                # Extra settings view (extra settings tab)
                self.extra_settings_view = ExtraSettingsView(self.settings_model, self)
                
                # Console view (console tab)
                self.console_view = ConsoleView(self)
                
                logger.info("Views created: SettingsView, NodeSettingsView, GSVView, ExtraSettingsView, ConsoleView")
            
            def _create_tabbed_interface(self):
                """Create the tabbed interface with all views."""
                # Create tab widget
                self.tab_widget = QtWidgets.QTabWidget()
                self.tab_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                
                # Add tabs
                self.tab_widget.addTab(self.node_settings_view, "Node Settings")
                
                # GSVs tab (only for Nuke 15.1+)
                if self.gsv_view:
                    self.tab_widget.addTab(self.gsv_view, "GSVs")
                
                # Extra Settings tab
                self.tab_widget.addTab(self.extra_settings_view, "Extra Settings")
                
                # Console tab (moved to last)
                self.tab_widget.addTab(self.console_view, "Console")
                
                # Add to main layout
                self.layout().addWidget(self.settings_view)
                self.layout().addWidget(self.tab_widget)
                
                # Set stretch factors
                self.layout().setStretchFactor(self.settings_view, 0)  # Settings don't stretch
                self.layout().setStretchFactor(self.tab_widget, 1)     # Table area stretches
            
            def _create_bottom_controls(self):
                """Create the bottom controls with version text, info label, progress bar and render button."""
                bottom_layout = QtWidgets.QHBoxLayout()
                
                # Version label on the left
                version_label = QtWidgets.QLabel("NK2DL Submitter v0.1-alpha")
                version_label.setStyleSheet("color: #888888; font-size: 10px;")
                bottom_layout.addWidget(version_label)
                
                # Info label for status messages
                self.info_label = QtWidgets.QLabel("Ready")
                self.info_label.setStyleSheet("color: #cccccc; font-size: 10px;")
                bottom_layout.addWidget(self.info_label)
                
                # Add stretch to push controls to the right
                bottom_layout.addStretch()
                
                # Progress bar (always visible)
                self.progress_bar = QtWidgets.QProgressBar()
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(0)
                self.progress_bar.setFixedWidth(Sizes.PROGRESS_BAR_WIDTH)
                bottom_layout.addWidget(self.progress_bar)
                
                # Render button
                self.render_btn = QtWidgets.QPushButton("Render")
                self.render_btn.setStyleSheet("QPushButton { background-color: #4a90e2; color: white; font-weight: bold; padding: 4px 8px; }")
                self.render_btn.clicked.connect(self._on_render_clicked)
                bottom_layout.addWidget(self.render_btn)
                
                self.layout().addLayout(bottom_layout)
                
                # Initialize progress manager
                self.progress_manager = PanelProgressManager(self.progress_bar, self.info_label)
            
            def _connect_signals(self):
                """Connect signals between models and views."""
                # Connect table model changes to console logging
                self.table_model.dataChanged.connect(self._on_table_data_changed)
                
                # Connect table model loading signals to progress manager
                self.table_model.loadingStarted.connect(self._on_loading_started)
                self.table_model.loadingFinished.connect(self._on_loading_finished)
                self.table_model.loadingProgress.connect(self._on_loading_progress)
                
                # Connect debug information from table model
                self.table_model.debugInfo.connect(self._on_debug_info)
                
                # Connect GSV model changes to console logging
                if self.gsv_view:
                    self.gsv_model.hierarchyChanged.connect(self._on_gsv_hierarchy_changed)
                    self.gsv_model.selectionChanged.connect(self._on_gsv_selection_changed)
                
                # Connect settings model changes to console logging
                self.settings_model.jobSettingsChanged.connect(self._on_job_settings_changed)
                self.settings_model.machineSettingsChanged.connect(self._on_machine_settings_changed)
                self.settings_model.extraSettingsChanged.connect(self._on_extra_settings_changed)
                
                logger.info("Signals connected between models, views, and progress manager")
            
            def _load_initial_data(self):
                """Load initial node data from Nuke script."""
                # Auto-refresh on panel initialization using event-based approach
                # This ensures the panel is fully initialized before data loading
                self._schedule_initial_data_load()
                
                logger.info("Scheduled initial node data refresh via events")
            
            def _schedule_initial_data_load(self):
                """Schedule initial data loading via event queue."""
                # Use event queue to ensure panel is fully constructed before data loading
                # Nuke 15.0 and earlier
                # Schedule with delay to ensure Nuke's script initialization is complete
                QtCore.QTimer.singleShot(Timing.PANEL_INITIALIZATION_DELAY, self._on_panel_ready_for_data)
                logger.debug("Initial data load scheduled via event system")
            
            def _on_panel_ready_for_data(self):
                """Handle panel ready for initial data loading."""
                try:
                    # Check if all components are properly initialized
                    if (hasattr(self, 'table_model') and self.table_model and
                        hasattr(self, 'node_settings_view') and self.node_settings_view and
                        hasattr(self, 'console_view') and self.console_view):
                        
                        logger.debug("Panel components ready, starting initial data refresh")
                        self._refresh_node_data()
                    else:
                        # Reschedule if components aren't ready yet
                        logger.debug("Panel components not ready, rescheduling data load")
                        QtCore.QTimer.singleShot(Timing.PANEL_INITIALIZATION_DELAY, self._on_panel_ready_for_data)
                        
                except Exception as e:
                    logger.error(f"Error in panel ready for data: {e}", exc_info=True)
            
            def _is_nuke_15_1_or_later(self):
                """Check if Nuke version is 15.1 or later."""
                try:
                    major = nuke.NUKE_VERSION_MAJOR
                    minor = nuke.NUKE_VERSION_MINOR
                    return (major > 15) or (major == 15 and minor >= 1)
                except:
                    return False
            
            # Signal handlers for model changes
            def _on_table_data_changed(self):
                """Handle table data changes."""
                self.console_view.log_info("Table data updated")
            
            def _on_gsv_hierarchy_changed(self):
                """Handle GSV hierarchy changes."""
                self.console_view.log_info("GSV hierarchy updated")
            
            def _on_gsv_selection_changed(self):
                """Handle GSV selection changes."""
                if self.gsv_view:
                    selected_gsvs = self.gsv_view.get_selected_gsvs()
                    count = len(selected_gsvs)
                    self.console_view.log_info(f"GSV selection changed - {count} items selected")
            
            def _on_job_settings_changed(self):
                """Handle job settings changes."""
                self.console_view.log_info("Job settings updated")
            
            def _on_machine_settings_changed(self):
                """Handle machine settings changes."""
                self.console_view.log_info("Machine settings updated")
            
            def _on_extra_settings_changed(self):
                """Handle extra settings changes."""
                self.console_view.log_info("Extra settings updated")
            
            def _on_render_clicked(self):
                """Handle render button click - submit selected write nodes to Deadline."""
                try:
                    # 1. Validate script is saved
                    script_path = nuke.root().name()
                    if not script_path or script_path == "Root":
                        nuke.message("Please save your script before submitting to Deadline.")
                        return
                    
                    # 2. Get selected write nodes
                    selected_nodes = []
                    for row in range(self.table_model.get_row_count()):
                        node_name = self.table_model.get_node_name(row)
                        if node_name and self.table_model.is_node_selected_for_render(row):
                            selected_nodes.append(node_name)
                    
                    if not selected_nodes:
                        nuke.message("No write nodes selected for rendering.\n\nPlease select at least one write node in the table.")
                        return
                    
                    # 3. Start progress
                    self.progress_manager.start_operation("Submitting to Deadline")
                    
                    # 4. Get current UI state from all panels
                    current_ui_state = self._capture_current_ui_state()
                    
                    # 5. Build submission arguments via storage with current UI state
                    submission_args = self.settings_storage.build_submission_args(
                        script_path=script_path,
                        write_nodes=selected_nodes,
                        **current_ui_state  # Pass current UI state as overrides
                    )
                    
                    # 5. Submit to Deadline
                    from ...nuke.submission import submit_nuke_script
                    result = submit_nuke_script(**submission_args)
                    
                    # 6. Show success message
                    job_count = len(selected_nodes)
                    node_list = ", ".join(selected_nodes)
                    
                    # Handle both dict and list return types from submission
                    if isinstance(result, dict):
                        job_id = result.get('job_id', 'unknown')
                    elif isinstance(result, list) and result:
                        job_id = result[0] if result else 'unknown'
                    else:
                        job_id = 'unknown'
                    
                    success_msg = f"Successfully submitted {job_count} jobs to Deadline:\n\n"
                    success_msg += f"Write Nodes: {node_list}\n"
                    success_msg += f"Job ID: {job_id}"
                    
                    nuke.message(success_msg)
                    self.progress_manager.finish_operation(success=True, final_message="Submission completed successfully")
                    
                except Exception as e:
                    error_msg = f"Submission failed:\n\n{str(e)}"
                    nuke.message(error_msg)
                    self.progress_manager.finish_operation(success=False, final_message="Submission failed")
                    logger.error(f"Render button submission failed: {e}", exc_info=True)
            
            def _capture_current_ui_state(self):
                """Capture current state of all UI controls for submission.
                
                Returns:
                    Dict[str, Any]: Current UI state with parameter names matching submission args
                """
                ui_state = {}
                
                try:
                    # Get critical checkboxes that affect submission behavior from SettingsView
                    if hasattr(self.settings_view, 'separate_jobs_check'):
                        ui_state['write_nodes_as_separate_jobs'] = self.settings_view.separate_jobs_check.isChecked()
                    
                    if hasattr(self.settings_view, 'separate_tasks_check'):
                        ui_state['write_nodes_as_tasks'] = self.settings_view.separate_tasks_check.isChecked()
                    
                    if hasattr(self.settings_view, 'views_separate_jobs_check'):
                        ui_state['views_as_separate_jobs'] = self.settings_view.views_separate_jobs_check.isChecked()
                    
                    # Get other important settings from SettingsView
                    if hasattr(self.settings_view, 'priority_spin'):
                        ui_state['priority'] = self.settings_view.priority_spin.value()
                    
                    if hasattr(self.settings_view, 'chunk_size_spin'):
                        ui_state['chunk_size'] = self.settings_view.chunk_size_spin.value()
                    
                    if hasattr(self.settings_view, 'frames_edit'):
                        ui_state['frames'] = self.settings_view.frames_edit.text()
                    
                    if hasattr(self.settings_view, 'pool_combo'):
                        ui_state['pool'] = self.settings_view.pool_combo.currentText()
                    
                    if hasattr(self.settings_view, 'group_combo'):
                        ui_state['group'] = self.settings_view.group_combo.currentText()
                    
                    if hasattr(self.settings_view, 'threads_spin'):
                        ui_state['threads'] = self.settings_view.threads_spin.value()
                    
                    if hasattr(self.settings_view, 'use_gpu_check'):
                        ui_state['use_gpu'] = self.settings_view.use_gpu_check.isChecked()
                    
                    if hasattr(self.settings_view, 'concurrent_tasks_spin'):
                        ui_state['concurrent_tasks'] = self.settings_view.concurrent_tasks_spin.value()
                    
                    # Get machine settings
                    if hasattr(self.settings_view, 'limit_tasks_check'):
                        ui_state['limit_worker_tasks'] = self.settings_view.limit_tasks_check.isChecked()
                    
                    if hasattr(self.settings_view, 'machine_limit_spin'):
                        ui_state['machine_limit'] = self.settings_view.machine_limit_spin.value()
                    
                    logger.debug(f"Captured UI state: {ui_state}")
                    return ui_state
                    
                except Exception as e:
                    logger.error(f"Error capturing UI state: {e}", exc_info=True)
                    return {}
            
            # Progress and data loading handlers
            def _refresh_node_data(self):
                """Refresh node data from the current Nuke script."""
                if self.progress_manager.is_busy():
                    logger.warning("Cannot refresh node data while another operation is in progress")
                    return
                
                self.console_view.log_info("Refreshing node data from script...")
                self.table_model.refresh_from_nodes_async()
            
            def _on_loading_started(self):
                """Handle start of data loading operation."""
                self.progress_manager.start_operation("Loading node data")
                # Disable update button during loading
                if hasattr(self.node_settings_view, 'update_btn'):
                    self.node_settings_view.update_btn.setEnabled(False)
                self.console_view.log_info("Started loading node data from script")
            
            def _on_loading_finished(self):
                """Handle completion of data loading operation."""
                self.progress_manager.finish_operation(success=True, final_message="Node data loaded successfully")
                # Re-enable update button
                if hasattr(self.node_settings_view, 'update_btn'):
                    self.node_settings_view.update_btn.setEnabled(True)
                
                # Log completion with node count
                node_count = self.table_model.get_row_count()
                self.console_view.log_info(f"Node data loading completed - {node_count} nodes loaded")
            
            def _on_loading_progress(self, progress_percent, status_message):
                """Handle progress updates during data loading."""
                self.progress_manager.update_progress(progress_percent, status_message)
            
            def _on_debug_info(self, debug_message):
                """Handle debug information from background threads.
                
                Args:
                    debug_message: Debug message from the background thread
                """
                # Display debug info in console view using log_info
                self.console_view.log_info(f"DEBUG: {debug_message}")
            
            # Public API methods for external access
            def get_table_model(self):
                """Get the table data model.
                
                Returns:
                    TableDataModel: The table model instance
                """
                return self.table_model
            
            def get_gsv_model(self):
                """Get the GSV hierarchy model.
                
                Returns:
                    GSVHierarchyModel: The GSV model instance
                """
                return self.gsv_model
            
            def get_settings_model(self):
                """Get the settings model.
                
                Returns:
                    SettingsModel: The settings model instance
                """
                return self.settings_model
            
            def get_console_view(self):
                """Get the console view.
                
                Returns:
                    ConsoleView: The console view instance
                """
                return self.console_view
            
            def get_effective_table_values(self):
                """Get effective values from the table.
                
                Returns:
                    list: List of effective row values
                """
                return self.node_settings_view.get_effective_values()
            
            def get_selected_gsvs(self):
                """Get selected GSV values.
                
                Returns:
                    dict: Selected GSV data
                """
                if self.gsv_view:
                    return self.gsv_view.get_selected_gsvs()
                return {}
            
            def get_all_settings(self):
                """Get all settings from the settings model.
                
                Returns:
                    dict: All settings organized by category
                """
                return self.settings_model.export_settings()

            def _apply_panel_configuration(self):
                """Apply panel configuration to all controls."""
                from .config import apply_panel_config
                
                # Add debug logging
                logger.debug("Starting _apply_panel_configuration")
                
                # Set object names for main panel controls first - MUST match control names passed to apply_panel_config
                self.render_btn.setObjectName("render_btn")
                self.tab_widget.setObjectName("tab_widget")
                self.progress_bar.setObjectName("progress_bar")
                
                # Apply to main panel controls
                apply_panel_config(self.render_btn, "render_btn")
                apply_panel_config(self.tab_widget, "tab_widget") 
                apply_panel_config(self.progress_bar, "progress_bar")
                
                # Apply to view controls
                logger.debug("Applying configuration to SettingsView")
                if hasattr(self.settings_view, '_apply_configuration'):
                    self.settings_view._apply_configuration()
                
                logger.debug("Applying configuration to NodeSettingsView")
                if hasattr(self.node_settings_view, '_apply_configuration'):
                    self.node_settings_view._apply_configuration()
                
                logger.debug("Applying configuration to ExtraSettingsView")
                if hasattr(self.extra_settings_view, '_apply_configuration'):
                    self.extra_settings_view._apply_configuration()
                    
                logger.debug("Finished _apply_panel_configuration")


        def register_panel():
            """Create and register the dockable nk2dl panel.
            
            This function registers the nk2dl panel as a dockable PySide widget in Nuke.
            Uses PySide6 for Nuke 16+ and PySide2 for earlier versions.
            Users can access it from the Pane menu.

            Returns:
                True or None: True if panel was registered, or None if Nuke is not available.
            """
            if not NUKE_AVAILABLE:
                logger.warning("Nuke not available, skipping panel creation")
                return None
            
            try:
                # Following the KnobScripter pattern - register in same module as widget class
                # Make the class available in nuke namespace
                nuke.Nk2dlPanel = Nk2dlPanel
                
                # Register the PySide widget as a dockable panel
                nuke.nk2dlPane = panels.registerWidgetAsPanel(
                    'nuke.Nk2dlPanel',                  # Class reference in nuke namespace
                    'Nuke to Deadline',                 # Display name in Pane menu
                    'com.danielharkness.nk2dl.panel'    # Unique ID for layout saving
                )
                
                logger.info(f"nk2dl dockable panel registered successfully using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register nk2dl panel: {str(e)}")
                return None

        # Panel classes are available
        __all__ = ['Nk2dlPanel', 'register_panel', 'get_panel_availability']
        _PANEL_AVAILABLE = True
        _IMPORT_ERROR = None

    except ImportError as e:
        # Handle case where panel components are not available
        __all__ = ['get_panel_availability']
        _PANEL_AVAILABLE = False
        _IMPORT_ERROR = str(e)
        
        # Create placeholder classes for documentation/error handling
        Nk2dlPanel = None
        register_panel = None

else:
    # Qt not available at all
    __all__ = ['get_panel_availability']
    _PANEL_AVAILABLE = False
    _IMPORT_ERROR = "Qt (PySide6/PySide2) not available"
    
    Nk2dlPanel = None
    register_panel = None


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