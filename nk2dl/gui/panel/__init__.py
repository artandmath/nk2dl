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
        from .constants import Sizes, GSVDefaults, Timing, Fonts, Settings
        from .config import apply_panel_config
        from .repositories import NodeSettingsStorage
        from .controllers import PanelProgressManager, DeadlineResourceWorker, NodeDataWorker, SubmissionWorker, ThreadLogHandler

        import logging
        import sys
        import os
        from pathlib import Path
        import threading
        from queue import Queue
        from typing import Optional, Dict, Any

        class ConsoleLogHandler(logging.Handler):
            """Custom logging handler that redirects log messages to the console widget using Qt signals."""
            
            def __init__(self, console_view):
                super().__init__()
                self.console_view = console_view
                
            def emit(self, record):
                """Emit a log record to the console widget."""
                try:
                    msg = self.format(record)
                    
                    # Use Qt signals to safely update from any thread
                    if record.levelno >= logging.ERROR:
                        self.console_view.log_error_signal.emit(msg)
                    elif record.levelno >= logging.WARNING:
                        self.console_view.log_warning_signal.emit(msg)
                    else:
                        self.console_view.log_info_signal.emit(msg)
                        
                except Exception:
                    self.handleError(record)




                    


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
                
                # Flag to prevent recursive saving during loading
                self._loading_from_storage = False
                
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
                
                # Set up storage visual indications
                self._setup_storage_visual_indications()
                
                logger.info(f"nk2dl panel initialized using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
            
            def _create_models(self):
                """Create all data models and repositories."""
                # Create models
                self.settings_model = SettingsModel(self)
                self.table_model = TableDataModel(self.settings_model, self)
                self.gsv_model = GSVHierarchyModel(self)
                
                # Create repositories
                self.node_data_worker = NodeDataWorker(self)
                self.settings_storage = NodeSettingsStorage()
                
                # Connect repositories to table model
                self.table_model.set_node_data_provider(self.node_data_worker)
                self.table_model.set_settings_storage(self.settings_storage)
                
                logger.info("Models and repositories created: TableDataModel, GSVHierarchyModel, SettingsModel, NodeDataWorker, NodeSettingsStorage")
            
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
                
                # Clear main tab widget tooltip to prevent it from showing over content areas
                self.tab_widget.setToolTip("")
                
                # Add tabs
                tab_index = 0
                
                # Node Settings tab
                self.tab_widget.addTab(self.node_settings_view, "Node Settings")
                self.tab_widget.setTabToolTip(tab_index, "Configure render settings for individual write nodes and manage the render queue")
                tab_index += 1
                
                # GSVs tab (only for Nuke 15.1+)
                if self.gsv_view:
                    self.tab_widget.addTab(self.gsv_view, "GSVs")
                    self.tab_widget.setTabToolTip(tab_index, "Manage Global State Variables for advanced shot and sequence organization")
                    tab_index += 1
                
                # Extra Settings tab
                self.tab_widget.addTab(self.extra_settings_view, "Extra Settings")
                self.tab_widget.setTabToolTip(tab_index, "Configure job information including job name, comment, and department")
                tab_index += 1
                
                # Console tab (moved to last)
                self.tab_widget.addTab(self.console_view, "Console")
                self.tab_widget.setTabToolTip(tab_index, "View submission logs and monitor Deadline job progress")
                
                # Add to main layout
                self.layout().addWidget(self.settings_view)
                self.layout().addWidget(self.tab_widget)
                
                # Set stretch factors
                self.layout().setStretchFactor(self.settings_view, 0)  # Settings don't stretch
                self.layout().setStretchFactor(self.tab_widget, 1)     # Table area stretches
            
            def _create_bottom_controls(self):
                """Create the bottom controls with info label, progress bar and render button."""
                bottom_layout = QtWidgets.QHBoxLayout()
                
                # Info label for status messages (larger font)
                self.info_label = QtWidgets.QLabel("Ready")
                self.info_label.setStyleSheet("color: #cccccc; font-size: 12px;")
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
                
                # Connect settings changes to visual indication refresh
                self.settings_model.jobSettingsChanged.connect(self._on_settings_changed_for_visual_indication)
                self.settings_model.machineSettingsChanged.connect(self._on_settings_changed_for_visual_indication)
                self.settings_model.extraSettingsChanged.connect(self._on_settings_changed_for_visual_indication)
                
                # Connect settings changes to storage saves
                self.settings_model.jobSettingsChanged.connect(self._on_settings_changed_save_to_storage)
                self.settings_model.machineSettingsChanged.connect(self._on_settings_changed_save_to_storage)
                self.settings_model.extraSettingsChanged.connect(self._on_settings_changed_save_to_storage)
                
                logger.info("Signals connected between models, views, and progress manager")
            
            def _load_initial_data(self):
                """Load initial node data from Nuke script."""
                # Load settings from storage first
                self._load_settings_from_storage()
                
                # Auto-refresh on panel initialization using event-based approach
                # This ensures the panel is fully initialized before data loading
                self._schedule_initial_data_load()
                
                # Also start loading Deadline resources in background
                self._schedule_deadline_resource_loading()
                
                logger.info("Scheduled initial node data refresh and Deadline resource loading via events")
            
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
            
            def _schedule_deadline_resource_loading(self):
                """Schedule Deadline resource loading via event queue."""
                # Use timer to start resource loading after panel is ready
                QtCore.QTimer.singleShot(Timing.PANEL_INITIALIZATION_DELAY + 50, self._start_deadline_resource_loading)
                logger.debug("Deadline resource loading scheduled")
            
            def _start_deadline_resource_loading(self):
                """Start background loading of Deadline resources."""
                try:
                    # Skip if already loading
                    if hasattr(self, '_deadline_resource_worker') and self._deadline_resource_worker:
                        logger.debug("Deadline resource loading already in progress")
                        return
                    
                    # Start progress indication
                    self.progress_manager.start_operation("Fetching Deadline Pools and Groups", indeterminate=True)
                    
                    # Populate initial values first
                    self._populate_initial_pool_group_values()
                    
                    # Create and configure worker
                    self._deadline_resource_worker = DeadlineResourceWorker(
                        fetch_pools=True, 
                        fetch_groups=True
                    )
                    
                    # Connect signals
                    self._deadline_resource_worker.signals.pools_loaded.connect(
                        self._on_pools_loaded, QtCore.Qt.QueuedConnection)
                    self._deadline_resource_worker.signals.groups_loaded.connect(
                        self._on_groups_loaded, QtCore.Qt.QueuedConnection)
                    self._deadline_resource_worker.signals.error_occurred.connect(
                        self._on_deadline_resource_error, QtCore.Qt.QueuedConnection)
                    self._deadline_resource_worker.signals.progress_update.connect(
                        self._on_deadline_resource_progress, QtCore.Qt.QueuedConnection)
                    self._deadline_resource_worker.signals.finished.connect(
                        self._on_deadline_resource_finished, QtCore.Qt.QueuedConnection)
                    
                    # Start worker in thread pool
                    QtCore.QThreadPool.globalInstance().start(self._deadline_resource_worker)
                    logger.info("Started Deadline resource loading in background")
                    
                except Exception as e:
                    logger.error(f"Error starting Deadline resource loading: {e}", exc_info=True)
                    # Finish progress on error
                    self.progress_manager.finish_operation(success=False, final_message="Failed to start Deadline resource loading")
                    # Use fallback values on error
                    self._use_fallback_resources()
            
            def _populate_initial_pool_group_values(self):
                """Populate initial pool/group values before Deadline fetch."""
                try:
                    # 1. Try storage first - load all settings once to avoid multiple calls
                    all_settings = self.settings_storage.load_all_settings()
                    global_settings = all_settings.get('global_settings', {})
                    
                    stored_pool = global_settings.get('pool')
                    stored_group = global_settings.get('group')
                    
                    # Check if we have any stored preferences
                    if stored_pool or stored_group:
                        # Use stored values if available, otherwise use 'none'
                        pool_value = stored_pool if stored_pool and stored_pool != 'none' else 'none'
                        group_value = stored_group if stored_group and stored_group != 'none' else 'none'
                        
                        logger.info(f"Using stored preferences - pool: {pool_value}, group: {group_value}")
                        self._set_initial_selections(pool_value, group_value, global_settings)
                        return
                    
                    # 2. Try config defaults
                    from ...common.config import config
                    config_pool = config.get('submission.pool', 'nuke')
                    config_group = config.get('submission.group', 'none')
                    
                    logger.info(f"Using config defaults - pool: {config_pool}, group: {config_group}")
                    self._set_initial_selections(config_pool, config_group, None)
                    
                except Exception as e:
                    logger.error(f"Error populating initial pool/group values: {e}", exc_info=True)
                    # Use fallback values
                    self._set_initial_selections('none', 'none', None)
            
            def _set_initial_selections(self, pool: str, group: str, global_settings: Optional[Dict[str, Any]] = None):
                """Set initial dropdown selections."""
                try:
                    # Block signals and disable change tracking during initial selection
                    if hasattr(self, 'settings_view') and self.settings_view:
                        self.settings_view.pool_combo.blockSignals(True)
                        self.settings_view.secondary_pool_combo.blockSignals(True)
                        self.settings_view.group_combo.blockSignals(True)
                        
                    if hasattr(self, 'settings_model') and self.settings_model:
                        self.settings_model.disable_user_change_tracking()
                    
                    try:
                        # Update settings model if available
                        if hasattr(self, 'settings_model') and self.settings_model:
                            if pool and pool != 'none':
                                self.settings_model.set_machine_setting('pool', pool)
                            if group and group != 'none':
                                self.settings_model.set_machine_setting('group', group)
                        
                        # Update UI if available
                        if hasattr(self, 'settings_view') and self.settings_view:
                            # Handle pool selection
                            if pool and pool != 'none':
                                pool_index = self.settings_view.pool_combo.findText(pool)
                                if pool_index < 0:
                                    # Pool value not found in dropdown, temporarily add it
                                    logger.info(f"Adding stored pool '{pool}' to dropdown temporarily")
                                    self.settings_view.pool_combo.addItem(pool)
                                    pool_index = self.settings_view.pool_combo.findText(pool)
                                
                                if pool_index >= 0:
                                    self.settings_view.pool_combo.setCurrentIndex(pool_index)
                                    logger.info(f"Set pool dropdown to stored value: {pool}")
                            
                            # Handle group selection  
                            if group and group != 'none':
                                group_index = self.settings_view.group_combo.findText(group)
                                if group_index < 0:
                                    # Group value not found in dropdown, temporarily add it
                                    logger.info(f"Adding stored group '{group}' to dropdown temporarily")
                                    self.settings_view.group_combo.addItem(group)
                                    group_index = self.settings_view.group_combo.findText(group)
                                
                                if group_index >= 0:
                                    self.settings_view.group_combo.setCurrentIndex(group_index)
                                    logger.info(f"Set group dropdown to stored value: {group}")
                            
                            # For secondary pool, we need to handle the stored value if it exists
                            # Get secondary pool from provided global_settings if available
                            try:
                                stored_secondary_pool = None
                                if global_settings:
                                    stored_secondary_pool = global_settings.get('secondary_pool')
                                
                                if stored_secondary_pool and stored_secondary_pool != '':
                                    secondary_pool_index = self.settings_view.secondary_pool_combo.findText(stored_secondary_pool)
                                    if secondary_pool_index < 0:
                                        # Secondary pool value not found, temporarily add it
                                        logger.info(f"Adding stored secondary pool '{stored_secondary_pool}' to dropdown temporarily")
                                        self.settings_view.secondary_pool_combo.addItem(stored_secondary_pool)
                                        secondary_pool_index = self.settings_view.secondary_pool_combo.findText(stored_secondary_pool)
                                    
                                    if secondary_pool_index >= 0:
                                        self.settings_view.secondary_pool_combo.setCurrentIndex(secondary_pool_index)
                                        logger.info(f"Set secondary pool dropdown to stored value: {stored_secondary_pool}")
                                        
                                        # Also update the settings model
                                        if hasattr(self, 'settings_model') and self.settings_model:
                                            self.settings_model.set_machine_setting('secondary_pool', stored_secondary_pool)
                            except Exception as e:
                                logger.debug(f"No stored secondary pool found or error loading: {e}")
                    
                    finally:
                        # Re-enable signals and change tracking
                        if hasattr(self, 'settings_view') and self.settings_view:
                            self.settings_view.pool_combo.blockSignals(False)
                            self.settings_view.secondary_pool_combo.blockSignals(False)
                            self.settings_view.group_combo.blockSignals(False)
                            
                        if hasattr(self, 'settings_model') and self.settings_model:
                            self.settings_model.enable_user_change_tracking()
                    
                except Exception as e:
                    logger.error(f"Error setting initial selections: {e}", exc_info=True)
            
            def _on_pools_loaded(self, pools):
                """Handle pools loaded from Deadline."""
                try:
                    logger.info(f"Pools loaded from Deadline: {pools}")
                    
                    # Update constants
                    Settings.set_pool_options(pools)
                    
                    # Update UI if ready
                    if self._is_ui_ready_for_updates():
                        self._refresh_pool_dropdowns()
                    
                except Exception as e:
                    logger.error(f"Error handling pools loaded: {e}", exc_info=True)
            
            def _on_groups_loaded(self, groups):
                """Handle groups loaded from Deadline."""
                try:
                    logger.info(f"Groups loaded from Deadline: {groups}")
                    
                    # Update constants
                    Settings.set_group_options(groups)
                    
                    # Update UI if ready
                    if self._is_ui_ready_for_updates():
                        self._refresh_group_dropdowns()
                    
                except Exception as e:
                    logger.error(f"Error handling groups loaded: {e}", exc_info=True)
            
            def _on_deadline_resource_error(self, error_msg):
                """Handle Deadline resource loading errors."""
                logger.warning(f"Deadline resource loading failed: {error_msg}")
                # Finish progress indication with error
                if hasattr(self, 'progress_manager'):
                    self.progress_manager.finish_operation(success=False, final_message=f"Deadline connection failed: {error_msg}")
                # Use fallback values
                self._use_fallback_resources()
            
            def _on_deadline_resource_progress(self, message):
                """Handle Deadline resource loading progress."""
                logger.debug(f"Deadline resource progress: {message}")
                # Update progress bar status message without changing progress value
                # to maintain indeterminate mode (crawling zebra pattern)
                if hasattr(self, 'progress_manager') and self.progress_manager.is_busy():
                    self.progress_manager.update_status_message(message)
            
            def _on_deadline_resource_finished(self):
                """Handle Deadline resource loading completion."""
                logger.info("Deadline resource loading finished")
                # Finish progress indication with auto-reset to "Ready"
                if hasattr(self, 'progress_manager'):
                    self.progress_manager.finish_operation(success=True, final_message="Deadline resources loaded", auto_reset_delay=500)
                # Clean up worker reference
                if hasattr(self, '_deadline_resource_worker'):
                    self._deadline_resource_worker = None
            
            def _use_fallback_resources(self):
                """Use fallback pool and group options when Deadline is unavailable."""
                try:
                    logger.warning("Using fallback pool and group options")
                    
                    # Use fallback values
                    Settings.use_fallback_pools()
                    Settings.use_fallback_groups()
                    
                    # Update UI if ready
                    if self._is_ui_ready_for_updates():
                        self._refresh_pool_dropdowns()
                        self._refresh_group_dropdowns()
                    
                except Exception as e:
                    logger.error(f"Error using fallback resources: {e}", exc_info=True)
            
            def _is_ui_ready_for_updates(self):
                """Check if UI is ready for updates."""
                return (hasattr(self, 'settings_view') and 
                        self.settings_view is not None and
                        hasattr(self.settings_view, 'pool_combo') and
                        hasattr(self.settings_view, 'group_combo'))
            
            def _refresh_pool_dropdowns(self):
                """Refresh pool dropdown contents."""
                try:
                    if hasattr(self, 'settings_view') and self.settings_view:
                        self.settings_view.refresh_pool_dropdowns()
                except Exception as e:
                    logger.error(f"Error refreshing pool dropdowns: {e}", exc_info=True)
            
            def _refresh_group_dropdowns(self):
                """Refresh group dropdown contents."""
                try:
                    if hasattr(self, 'settings_view') and self.settings_view:
                        self.settings_view.refresh_group_dropdown()
                except Exception as e:
                    logger.error(f"Error refreshing group dropdowns: {e}", exc_info=True)
            
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
            
            def _on_settings_changed_save_to_storage(self):
                """Handle settings changes by saving only user-changed settings to storage."""
                # Skip saving if we're currently loading from storage
                if self._loading_from_storage:
                    logger.debug("Skipping save to storage (currently loading)")
                    return
                    
                try:
                    # Get only user-changed settings from the model
                    user_changed_settings = self.settings_model.get_user_changed_settings()
                    
                    # Save only user-changed settings to storage (creates minimal YAML)
                    success = self.settings_storage.save_user_changed_settings(user_changed_settings)
                    
                    if success:
                        logger.debug(f"Saved {len(user_changed_settings)} user-changed settings to storage")
                    else:
                        logger.warning("Failed to save user-changed settings to storage")
                        
                except Exception as e:
                    logger.error(f"Error saving user-changed settings to storage: {e}", exc_info=True)
            
            def _load_settings_from_storage(self):
                """Load user-changed settings from storage and populate the settings model."""
                try:
                    # Set flag to prevent recursive saving during loading
                    self._loading_from_storage = True
                    
                    # Create minimal storage structure if needed
                    self.settings_storage.create_minimal_storage_if_needed()
                    
                    # Load only user-changed settings from storage
                    user_changed_settings = self.settings_storage.load_user_changed_settings()
                    
                    if user_changed_settings:
                        # Apply user-changed settings on top of config defaults
                        # The settings model will already have defaults, so we just override specific values
                        self.settings_model.set_user_changed_settings(user_changed_settings)
                        logger.info(f"Loaded {len(user_changed_settings)} user-changed settings from storage")
                    else:
                        logger.debug("No user-changed settings found in storage, using config defaults")
                    
                    # Refresh views after loading settings
                    self._refresh_views_after_storage_load()
                
                except Exception as e:
                    logger.error(f"Error loading user-changed settings from storage: {e}", exc_info=True)
                finally:
                    # Always clear the flag
                    self._loading_from_storage = False
            
            def _refresh_views_after_storage_load(self):
                """Refresh views after loading settings from storage."""
                try:
                    # Refresh settings view to show loaded values
                    if hasattr(self.settings_view, '_load_settings_from_model'):
                        self.settings_view._load_settings_from_model()
                        logger.debug("Refreshed SettingsView after storage load")
                    
                    # Refresh extra settings view to show loaded values
                    if hasattr(self.extra_settings_view, '_load_settings_from_model'):
                        self.extra_settings_view._load_settings_from_model()
                        logger.debug("Refreshed ExtraSettingsView after storage load")
                    
                    # Refresh visual indications to highlight user-changed settings
                    self._refresh_all_visual_indications()
                    
                    logger.debug("Views refreshed after storage load")
                    
                except Exception as e:
                    logger.error(f"Error refreshing views after storage load: {e}", exc_info=True)
            
            def _setup_storage_visual_indications(self):
                """Set up storage visual indication for views that support it."""
                try:
                    # Connect storage instance to views that have visual indication support
                    if hasattr(self.settings_view, 'set_storage_instance'):
                        self.settings_view.set_storage_instance(self.settings_storage)
                        logger.debug("Connected storage instance to SettingsView")
                    
                    if hasattr(self.extra_settings_view, 'set_storage_instance'):
                        self.extra_settings_view.set_storage_instance(self.settings_storage)
                        logger.debug("Connected storage instance to ExtraSettingsView")
                    
                    # Initial refresh of visual indications
                    self._refresh_all_visual_indications()
                    
                    logger.info("Storage visual indications set up successfully")
                    
                except Exception as e:
                    logger.error(f"Error setting up storage visual indications: {e}", exc_info=True)
            
            def _on_settings_changed_for_visual_indication(self):
                """Handle settings changes to refresh visual indications."""
                # Use a short delay to batch rapid changes
                if not hasattr(self, '_visual_indication_timer'):
                    self._visual_indication_timer = QtCore.QTimer()
                    self._visual_indication_timer.setSingleShot(True)
                    self._visual_indication_timer.timeout.connect(self._refresh_all_visual_indications)
                
                # Reset timer (batches rapid changes)
                self._visual_indication_timer.start(100)  # 100ms delay
            
            def _refresh_all_visual_indications(self):
                """Refresh visual indications in all views."""
                try:
                    if hasattr(self.settings_view, 'refresh_visual_indications'):
                        self.settings_view.refresh_visual_indications()
                    
                    if hasattr(self.extra_settings_view, 'refresh_visual_indications'):
                        self.extra_settings_view.refresh_visual_indications()
                    
                    logger.debug("Refreshed visual indications in all views")
                    
                except Exception as e:
                    logger.error(f"Error refreshing visual indications: {e}", exc_info=True)
            
            def _on_render_clicked(self):
                """Handle render button click - submit selected write nodes to Deadline."""
                # Check if already submitting
                if hasattr(self, '_submission_in_progress') and self._submission_in_progress:
                    self.console_view.log_warning("Submission already in progress, please wait...")
                    return
                
                try:
                    # 1. Switch to console tab and set up logging
                    console_tab_index = self.tab_widget.indexOf(self.console_view)
                    self.tab_widget.setCurrentIndex(console_tab_index)
                    
                    # Set up console logging handler
                    self._setup_console_logging()
                    
                    self.console_view.log_info("=== Starting Deadline Submission ===")
                    
                    # 2. Validate script is saved
                    script_path = nuke.root().name()
                    if not script_path or script_path == "Root":
                        self.console_view.log_error("Script not saved - please save your script before submitting")
                        nuke.message("Please save your script before submitting to Deadline.")
                        return
                    
                    self.console_view.log_info(f"Script path: {script_path}")
                    
                    # 3. Get selected write nodes
                    selected_nodes = []
                    for row in range(self.table_model.get_row_count()):
                        node_name = self.table_model.get_node_name(row)
                        if node_name and self.table_model.is_node_selected_for_render(row):
                            selected_nodes.append(node_name)
                    
                    if not selected_nodes:
                        self.console_view.log_error("No write nodes selected for rendering")
                        nuke.message("No write nodes selected for rendering.\n\nPlease select at least one write node in the table.")
                        return
                    
                    self.console_view.log_info(f"Selected write nodes: {', '.join(selected_nodes)}")
                    
                    # 4. Start progress and disable render button
                    self.progress_manager.start_operation("Submitting to Deadline", indeterminate=True)
                    self.render_btn.setEnabled(False)
                    self._submission_in_progress = True
                    
                    # 5. Get current UI state from all panels
                    self.console_view.log_info("Capturing current UI state...")
                    current_ui_state = self._capture_current_ui_state()
                    
                    # 6. Create and start submission worker thread
                    self._start_submission_worker(script_path, selected_nodes, current_ui_state)
                    
                except Exception as e:
                    self.console_view.log_error(f"Failed to start submission: {str(e)}")
                    self._cleanup_submission()
                    nuke.message(f"Failed to start submission: {str(e)}")
                    logger.error(f"Render button submission setup failed: {e}", exc_info=True)
            
            def _setup_console_logging(self):
                """Set up console logging handler."""
                if not hasattr(self, '_console_handler'):
                    self._console_handler = ConsoleLogHandler(self.console_view)
                    self._console_handler.setLevel(logging.DEBUG)
                    
                    # Add handler to nk2dl logger and root logger to capture all output
                    nk2dl_logger = logging.getLogger('nk2dl')
                    nk2dl_logger.addHandler(self._console_handler)
                    root_logger = logging.getLogger()
                    root_logger.addHandler(self._console_handler)
            
            def _cleanup_console_logging(self):
                """Clean up console logging handler."""
                if hasattr(self, '_console_handler'):
                    try:
                        nk2dl_logger = logging.getLogger('nk2dl')
                        nk2dl_logger.removeHandler(self._console_handler)
                        root_logger = logging.getLogger()
                        root_logger.removeHandler(self._console_handler)
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up console handler: {cleanup_error}")
                    finally:
                        delattr(self, '_console_handler')
            
            def _start_submission_worker(self, script_path, selected_nodes, current_ui_state):
                """Start the submission worker using QThreadPool."""
                # Create worker
                self._submission_worker = SubmissionWorker(
                    script_path, selected_nodes, current_ui_state, self.settings_storage
                )
                
                # Connect signals to handlers - use QueuedConnection for thread safety
                self._submission_worker.signals.progress_update.connect(
                    self._on_submission_progress, QtCore.Qt.QueuedConnection)
                self._submission_worker.signals.log_message.connect(
                    self._on_log_message, QtCore.Qt.QueuedConnection)  # Stable queued updates
                self._submission_worker.signals.error_occurred.connect(
                    self._on_submission_error, QtCore.Qt.QueuedConnection)
                self._submission_worker.signals.finished.connect(
                    self._on_submission_finished, QtCore.Qt.QueuedConnection)
                
                # Set up timer to process events during submission - conservative frequency
                self._submission_timer = QtCore.QTimer()
                self._submission_timer.timeout.connect(self._process_submission_events)
                self._submission_timer.start(Timing.CONSOLE_CAPTURE_TIMER_INTERVAL)  # Process events every 100ms for stability
                
                # Get global thread pool and start worker
                thread_pool = QtCore.QThreadPool.globalInstance()
                thread_pool.start(self._submission_worker)
                
                self.console_view.log_info(f"Started submission using {thread_pool.maxThreadCount()} available threads")
                
            def _process_submission_events(self):
                """Process Qt events during submission to ensure GUI updates."""
                # Process all pending Qt events to update GUI
                QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                
                # Also process deferred delete events
                QtWidgets.QApplication.sendPostedEvents()
                
                # Check if submission is still running
                if not hasattr(self, '_submission_worker') or not hasattr(self, '_submission_timer'):
                    return
            
            def _on_submission_progress(self, message):
                """Handle submission progress updates."""
                self.console_view.log_info(message)
            
            def _on_log_message(self, message, level):
                """Handle log messages from worker thread."""
                if level == 'error':
                    self.console_view.log_error(message)
                elif level == 'warning':
                    self.console_view.log_warning(message)
                else:
                    self.console_view.log_info(message)
                
                # Ensure the latest message is visible
                scrollbar = self.console_view.console_output.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            def _on_submission_error(self, error_msg):
                """Handle submission errors."""
                self.console_view.log_error(error_msg)
            
            def _on_submission_finished(self, success, message, result):
                """Handle submission completion."""
                try:
                    if success:
                        self.console_view.log_success("Submission completed successfully!")
                        
                        # Extract job information
                        job_count = len(self._submission_worker.selected_nodes)
                        node_list = ", ".join(self._submission_worker.selected_nodes)
                        
                        # Handle both dict and list return types from submission
                        if isinstance(result, dict):
                            job_id = result.get('job_id', 'unknown')
                        elif isinstance(result, list) and result:
                            job_id = result[0] if result else 'unknown'
                        else:
                            job_id = 'unknown'
                        
                        self.console_view.log_success(f"Job ID: {job_id}")
                        
                        # Show success message
                        success_msg = f"Successfully submitted {job_count} jobs to Deadline:\n\n"
                        success_msg += f"Write Nodes: {node_list}\n"
                        success_msg += f"Job ID: {job_id}"
                        
                        # TODO: Make success dialog configurable via panel settings
                        # nuke.message(success_msg)  # Suppressed for console-only workflow
                        self.progress_manager.finish_operation(success=True, final_message="Submission completed successfully")
                    else:
                        self.console_view.log_error(f"Submission failed: {message}")
                        # TODO: Make failure dialog configurable via panel settings  
                        # nuke.message(f"Submission failed:\n\n{message}")  # Suppressed for console-only workflow
                        self.progress_manager.finish_operation(success=False, final_message="Submission failed")
                        
                finally:
                    self._cleanup_submission()
            
            def _cleanup_submission(self):
                """Clean up after submission."""
                try:
                    # Stop the submission timer
                    if hasattr(self, '_submission_timer') and self._submission_timer.isActive():
                        self._submission_timer.stop()
                        delattr(self, '_submission_timer')
                    
                    # Re-enable render button
                    self.render_btn.setEnabled(True)
                    self._submission_in_progress = False
                    
                    # Clean up logging
                    self._cleanup_console_logging()
                    
                    # Log completion
                    self.console_view.log_info("=== Submission Process Complete ===")
                    
                except Exception as cleanup_error:
                    logger.error(f"Error during submission cleanup: {cleanup_error}")
            
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
                    
                    # NOTE: views_as_separate_jobs is not yet implemented in NukeSubmission
                    # Commenting out for now to avoid submission errors
                    # if hasattr(self.settings_view, 'views_separate_jobs_check'):
                    #     ui_state['views_as_separate_jobs'] = self.settings_view.views_separate_jobs_check.isChecked()
                    
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
                    
                    # Filter out unsupported parameters to avoid submission errors
                    ui_state = self._filter_supported_parameters(ui_state)
                    
                    logger.debug(f"Captured UI state: {ui_state}")
                    return ui_state
                    
                except Exception as e:
                    logger.error(f"Error capturing UI state: {e}", exc_info=True)
                    return {}
            
            def _filter_supported_parameters(self, ui_state):
                """Filter UI state to only include parameters supported by NukeSubmission.
                
                This prevents submission errors when UI is ahead of backend implementation.
                
                Args:
                    ui_state: Dictionary of UI state parameters
                    
                Returns:
                    Dict[str, Any]: Filtered UI state with only supported parameters
                """
                # Define parameters that are currently supported by NukeSubmission
                # Based on NukeSubmission.__init__ method signature
                supported_params = {
                    # nk2dl specific parameters
                    'script_is_open', 'use_parser_instead_of_nuke', 'submit_writes_alphabetically',
                    'submit_writes_in_render_order', 'submit_script_as_auxiliary_file', 
                    'render_settings_from_metadata',
                    
                    # Build job parameters
                    'submission_is_build_job', 'build_job_name', 'build_job_script_path',
                    'pre_build_job_script', 'post_build_job_script', 'build_job_as_auxiliary_file',
                    'delete_build_job_script',
                    
                    # Script copying parameters
                    'copy_script', 'copy_script_path', 'submit_copied_script',
                    
                    # ScriptJob parameters
                    'script_job_script_path',
                    
                    # Machine list parameters
                    'machine_list', 'machine_list_is_a_deny_list', 'machine_allow_list',
                    'machine_deny_list', 'machine_limit',
                    
                    # Job Info parameters
                    'job_name', 'batch_name', 'priority', 'pool', 'group', 'chunk_size',
                    'department', 'user_name', 'comment', 'concurrent_tasks', 'extra_info',
                    'frames', 'job_dependencies', 'on_job_complete', 'submit_suspended',
                    'limit_groups', 'task_timeout', 'enable_auto_timeout', 'limit_worker_tasks',
                    'pre_job_script', 'post_job_script', 'pre_task_script', 'post_task_script',
                    
                    # Plugin Info parameters
                    'output_file_path', 'parse_output_paths_to_deadline', 'nuke_version',
                    'use_nuke_x', 'batch_mode', 'threads', 'use_gpu', 'gpu_override',
                    'ram_use', 'enforce_render_order', 'stack_size', 'continue_on_error',
                    'reload_plugins', 'performance_profiler', 'performance_profiler_path',
                    'write_nodes', 'render_mode', 'write_nodes_as_tasks', 'write_nodes_as_separate_jobs',
                    'render_order_dependencies', 'use_node_frame_list', 'views',
                    
                    # Dual render mode parameters
                    'proxy_args',
                    
                    # Graph Scope Variables parameters
                    'graph_scope_variables',
                    
                    # Environment Variables parameters
                    'use_current_environment', 'environment_keys', 'environment', 'omit_environment_keys'
                }
                
                # Filter UI state to only include supported parameters
                filtered_state = {}
                unsupported_params = []
                
                for key, value in ui_state.items():
                    if key in supported_params:
                        filtered_state[key] = value
                    else:
                        unsupported_params.append(key)
                
                if unsupported_params:
                    logger.debug(f"Filtered out unsupported parameters: {unsupported_params}")
                
                return filtered_state
            
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