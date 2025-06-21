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
    from nk2dl.gui.panel import get_panel_availability
    available, error = get_panel_availability()
    
    if available:
        from nk2dl.gui.panel import Nk2dlPanel, register_panel
        register_panel()  # Explicitly register the panel
    
    # Constants are always available
    from nk2dl.gui.panel.constants import Settings, Colors, Sizes
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
        from .constants import Sizes, DefaultValues, GSVDefaults
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
                """Create the bottom controls with version text, info label, progress bar, update button and render button."""
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
                
                # Progress bar (initially hidden)
                self.progress_bar = QtWidgets.QProgressBar()
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(False)  # Hidden by default
                bottom_layout.addWidget(self.progress_bar)
                
                # Update button
                self.update_btn = QtWidgets.QPushButton("Update Nodes")
                self.update_btn.setStyleSheet("QPushButton { background-color: #5cb85c; color: white; font-weight: bold; padding: 4px 8px; }")
                self.update_btn.clicked.connect(self._refresh_node_data)
                bottom_layout.addWidget(self.update_btn)
                
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
                # Auto-refresh on panel initialization using QTimer to avoid blocking
                QtCore.QTimer.singleShot(100, self._refresh_node_data)
                
                logger.info("Scheduled initial node data refresh")
            
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
                """Handle render button click - show development message."""
                nuke.message("Nuke to Deadline panel is still under development.\n\nUse the \"Submit Write Nodes to Deadline\" feature from the render menu.")
            
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
                self.update_btn.setEnabled(False)  # Disable update button during loading
                self.console_view.log_info("Started loading node data from script")
            
            def _on_loading_finished(self):
                """Handle completion of data loading operation."""
                self.progress_manager.finish_operation(success=True, final_message="Node data loaded successfully")
                self.update_btn.setEnabled(True)  # Re-enable update button
                
                # Log completion with node count
                node_count = self.table_model.get_row_count()
                self.console_view.log_info(f"Node data loading completed - {node_count} nodes loaded")
            
            def _on_loading_progress(self, progress_percent, status_message):
                """Handle progress updates during data loading."""
                self.progress_manager.update_progress(progress_percent, status_message)
            
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