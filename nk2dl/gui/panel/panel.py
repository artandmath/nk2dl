# -*- coding: utf-8 -*-
"""Main panel coordinator for the nk2dl panel.

This module contains the main Nk2dlPanel class that coordinates all the extracted
components (models, views, widgets, delegates) into a cohesive interface.
"""

try:
    import nuke
    import nukescripts
    from nukescripts import panels
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

from ...common.logging import setup_logging

# Import all the extracted components
from .models import TableDataModel, GSVHierarchyModel, SettingsModel
from .views import SettingsView, NodeSettingsView, GSVView, ExtraSettingsView, ConsoleView
from .constants import Sizes, DefaultValues, GSVDefaults

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel.panel')


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
        
        # Load sample data for demonstration
        self._load_sample_data()
        
        # Set size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        logger.info(f"nk2dl panel initialized using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
    
    def _create_models(self):
        """Create all data models."""
        self.table_model = TableDataModel(self)
        self.gsv_model = GSVHierarchyModel(self)
        self.settings_model = SettingsModel(self)
        
        logger.info("Models created: TableDataModel, GSVHierarchyModel, SettingsModel")
    
    def _setup_layout(self):
        """Set up the main panel layout."""
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(5)
        self.layout().setContentsMargins(5, 5, 5, 5)
    
    def _create_views(self):
        """Create all view components."""
        # Settings view (top section)
        self.settings_view = SettingsView(self.settings_model, self)
        
        # Node settings view (table tab)
        self.node_settings_view = NodeSettingsView(self.table_model, self)
        
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
        """Create the bottom controls with version text, progress bar and render button."""
        bottom_layout = QtWidgets.QHBoxLayout()
        
        # Version label on the left
        version_label = QtWidgets.QLabel("NK2DL Submitter v0.1-alpha")
        version_label.setStyleSheet("color: #888888; font-size: 10px;")
        bottom_layout.addWidget(version_label)
        
        # Add stretch to push progress bar and render button to the right
        bottom_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        bottom_layout.addWidget(self.progress_bar)
        
        # Render button
        self.render_btn = QtWidgets.QPushButton("Render")
        self.render_btn.setStyleSheet("QPushButton { background-color: #4a90e2; color: white; font-weight: bold; }")
        self.render_btn.clicked.connect(self._on_render_clicked)
        bottom_layout.addWidget(self.render_btn)
        
        self.layout().addLayout(bottom_layout)
    
    def _connect_signals(self):
        """Connect signals between models and views."""
        # Connect table model changes to console logging
        self.table_model.dataChanged.connect(self._on_table_data_changed)
        
        # Connect GSV model changes to console logging
        if self.gsv_view:
            self.gsv_model.hierarchyChanged.connect(self._on_gsv_hierarchy_changed)
            self.gsv_model.selectionChanged.connect(self._on_gsv_selection_changed)
        
        # Connect settings model changes to console logging
        self.settings_model.jobSettingsChanged.connect(self._on_job_settings_changed)
        self.settings_model.machineSettingsChanged.connect(self._on_machine_settings_changed)
        self.settings_model.extraSettingsChanged.connect(self._on_extra_settings_changed)
        
        logger.info("Signals connected between models and views")
    
    def _load_sample_data(self):
        """Load sample data for demonstration."""
        from .constants import GSVDefaults
        
        # Load sample table data - all rows now have explicit values
        sample_table_data = [
            {
                "Order": "3999", "Node": "Write4", "Filename": "Some_path1_v002.%04d.exr", 
                "Chunk": "5", "Frames": "1350-1650", "Priority": "50", "NodesFrames": "Yes", 
                "TaskTimeout": "0", "AutoTimeout": "Yes", "RenderMode": "Full", "NukeX": "Yes", 
                "BatchMode": "Yes", "Reloadplugin": "Yes",
                # Machine settings columns with explicit values
                "Pool": GSVDefaults.SAMPLE_MACHINE_DATA["pool"],
                "SecondaryPool": GSVDefaults.SAMPLE_MACHINE_DATA["secondary_pool"],
                "Group": GSVDefaults.SAMPLE_MACHINE_DATA["group"],
                "Threads": str(GSVDefaults.SAMPLE_MACHINE_DATA["threads"]),
                "MinRam": str(GSVDefaults.SAMPLE_MACHINE_DATA["min_ram"]),
                "MaxRam": str(GSVDefaults.SAMPLE_MACHINE_DATA["max_ram"]),
                "UseGPU": "Yes" if GSVDefaults.SAMPLE_MACHINE_DATA["use_gpu"] else "No",
                "GPUId": str(GSVDefaults.SAMPLE_MACHINE_DATA["gpu_id"]),
                "ConcurrentTasks": str(GSVDefaults.SAMPLE_MACHINE_DATA["concurrent_tasks"]),
                "WorkerTaskLimit": "Yes" if GSVDefaults.SAMPLE_MACHINE_DATA["worker_task_limit"] else "No",
                "MachineList": GSVDefaults.SAMPLE_MACHINE_DATA["machine_list"],
                "Limits": GSVDefaults.SAMPLE_MACHINE_DATA["limits"]
            },
            {
                "Order": "3100", "Node": "Write30", "Filename": "Some_path3_v002.%04d.exr", 
                "Chunk": "3", "Frames": "1001-2315", "Priority": "40", "NodesFrames": "No", 
                "TaskTimeout": "10", "AutoTimeout": "No", "RenderMode": "Proxy", "NukeX": "No", 
                "BatchMode": "No", "Reloadplugin": "No",
                # Machine settings columns with explicit values
                "Pool": "lighting",
                "SecondaryPool": "render",
                "Group": "high_priority",
                "Threads": "4",
                "MinRam": "16",
                "MaxRam": "64",
                "UseGPU": "No",
                "GPUId": "0",
                "ConcurrentTasks": "2",
                "WorkerTaskLimit": "No",
                "MachineList": "",
                "Limits": ""
            },
            {
                "Order": "3050", "Node": "Write27", "Filename": "Some_path5_v002.%04d.exr", 
                "Chunk": "1", "Frames": "1570-1620", "Priority": "30", "NodesFrames": "Yes", 
                "TaskTimeout": "0", "AutoTimeout": "Yes", "RenderMode": "Full", "NukeX": "Yes", 
                "BatchMode": "Yes", "Reloadplugin": "Yes",
                # Machine settings columns with explicit values
                "Pool": "comp",
                "SecondaryPool": "",
                "Group": "none",
                "Threads": "8",
                "MinRam": "8",
                "MaxRam": "32",
                "UseGPU": "Yes",
                "GPUId": "1",
                "ConcurrentTasks": "4",
                "WorkerTaskLimit": "Yes",
                "MachineList": "render01,render02",
                "Limits": "nuke_license:2"
            },
            {
                "Order": "3000", "Node": "Write9", "Filename": "Some_path6_v002.%04d.exr", 
                "Chunk": "8", "Frames": "1350-1650", "Priority": "60", "NodesFrames": "No", 
                "TaskTimeout": "5", "AutoTimeout": "No", "RenderMode": "Both", "NukeX": "No", 
                "BatchMode": "No", "Reloadplugin": "No",
                # Machine settings columns with explicit values
                "Pool": "fx",
                "SecondaryPool": "general",
                "Group": "weekend",
                "Threads": "16",
                "MinRam": "32",
                "MaxRam": "128",
                "UseGPU": "Yes",
                "GPUId": "2",
                "ConcurrentTasks": "1",
                "WorkerTaskLimit": "No",
                "MachineList": "workstation03",
                "Limits": "arnold_license:1"
            },
            {
                "Order": "2999", "Node": "Write3", "Filename": "Some_path9_v002.%04d.exr", 
                "Chunk": "2", "Frames": "1001-2315", "Priority": "20", "NodesFrames": "Yes", 
                "TaskTimeout": "0", "AutoTimeout": "Yes", "RenderMode": "Script", "NukeX": "Yes", 
                "BatchMode": "Yes", "Reloadplugin": "Yes",
                # Machine settings columns with explicit values
                "Pool": "render",
                "SecondaryPool": "comp",
                "Group": "overnight",
                "Threads": "6",
                "MinRam": "12",
                "MaxRam": "48",
                "UseGPU": "No",
                "GPUId": "0",
                "ConcurrentTasks": "3",
                "WorkerTaskLimit": "Yes",
                "MachineList": "",
                "Limits": ""
            }
        ]
        
        self.table_model.set_data(sample_table_data)
        
        # Log sample data loading
        self.console_view.log_info("Sample table data loaded")
        self.console_view.log_info(f"Loaded {len(sample_table_data)} rows with explicit values")
        
        logger.info("Sample data loaded into models")
    
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