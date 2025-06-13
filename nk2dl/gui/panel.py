"""Advanced dockable panel for nk2dl in Nuke using version-appropriate PySide."""

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

from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel')


class Nk2dlPanel(QtWidgets.QWidget):
    """Advanced nk2dl panel using version-appropriate PySide for Nuke.
    
    This creates a comprehensive interface with proper layout control,
    settings section, tabbed interface, and professional table widget.
    Uses PySide6 for Nuke 16+ and PySide2 for earlier versions.
    """
    
    def __init__(self, parent=None):
        """Initialize the nk2dl panel."""
        if not NUKE_AVAILABLE:
            logger.error("Nuke not available, cannot create panel")
            return
            
        QtWidgets.QWidget.__init__(self, parent)
        
        # Set up the main layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(5)
        self.layout().setContentsMargins(5, 5, 5, 5)
        
        # Create the UI components
        self._create_settings_section()
        self._create_tabbed_interface()
        self._create_bottom_controls()
        
        # Set stretch factors to make render order table expand
        self.layout().setStretchFactor(self.settings_container, 0)  # Settings don't stretch
        self.layout().setStretchFactor(self.tab_widget, 1)         # Table area stretches
        
        # Set size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        logger.info(f"nk2dl panel initialized using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
    
    def _create_settings_section(self):
        """Create separate Job Settings and Machine Settings sections with responsive layout."""
        # Main container with horizontal layout for responsive behavior
        self.settings_container = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QHBoxLayout()  # Start horizontal
        self.content_layout.setSpacing(15)  # Add spacing between groups
        self.content_layout.setContentsMargins(0, 0, 0, 15)  # Add bottom margin for spacing below settings
        self.settings_container.setLayout(self.content_layout)
        
        # === JOB SETTINGS GROUP (Left) ===
        self.job_settings_group = QtWidgets.QGroupBox("Job Settings")
        self.job_settings_group.setMinimumWidth(300)
        job_column = QtWidgets.QVBoxLayout()
        job_column.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        job_column.setSpacing(5)  # Consistent spacing
        self.job_settings_group.setLayout(job_column)
        
        # === MACHINE SETTINGS GROUP (Right) ===
        self.machine_settings_group = QtWidgets.QGroupBox("Machine Settings")
        self.machine_settings_group.setMinimumWidth(300)
        machine_column = QtWidgets.QVBoxLayout()
        machine_column.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        machine_column.setSpacing(5)  # Consistent spacing
        self.machine_settings_group.setLayout(machine_column)
        
        # === JOB SETTINGS CONTENT ===
        # Frames and basic settings (removed Job Information section)
        basic_layout = QtWidgets.QGridLayout()
        
        basic_layout.addWidget(QtWidgets.QLabel("Frames:"), 0, 0)
        self.frame_range_edit = QtWidgets.QLineEdit("1001-2315")
        basic_layout.addWidget(self.frame_range_edit, 0, 1)
        
        basic_layout.addWidget(QtWidgets.QLabel("Chunk Size:"), 1, 0)
        self.chunk_size_spin = QtWidgets.QSpinBox()
        self.chunk_size_spin.setValue(1)
        self.chunk_size_spin.setMinimum(1)
        basic_layout.addWidget(self.chunk_size_spin, 1, 1)
        
        basic_layout.addWidget(QtWidgets.QLabel("Threads:"), 2, 0)
        self.threads_spin = QtWidgets.QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(64)
        self.threads_spin.setValue(4)
        basic_layout.addWidget(self.threads_spin, 2, 1)
        
        job_column.addLayout(basic_layout)
        
        # Divider
        divider1 = QtWidgets.QFrame()
        divider1.setFrameShape(QtWidgets.QFrame.HLine)
        divider1.setFrameShadow(QtWidgets.QFrame.Sunken)
        job_column.addWidget(divider1)
        
        # Checkboxes (moved up to replace removed job info section)
        self.render_nukex_check = QtWidgets.QCheckBox("Render with NukeX")
        job_column.addWidget(self.render_nukex_check)
        
        self.use_batch_mode_check = QtWidgets.QCheckBox("Use Batch Mode")
        job_column.addWidget(self.use_batch_mode_check)
        
        # Add stretch to job column
        job_column.addStretch()
        
        # === MACHINE SETTINGS CONTENT ===
        # GPU and Hardware settings
        gpu_layout = QtWidgets.QGridLayout()
        
        gpu_layout.addWidget(QtWidgets.QLabel("GPU Override:"), 0, 0)
        self.gpu_override_spin = QtWidgets.QSpinBox()
        self.gpu_override_spin.setMinimum(-1)
        self.gpu_override_spin.setMaximum(16)
        self.gpu_override_spin.setValue(-1)
        gpu_layout.addWidget(self.gpu_override_spin, 0, 1)
        
        self.use_gpu_check = QtWidgets.QCheckBox("Use GPU")
        gpu_layout.addWidget(self.use_gpu_check, 1, 0, 1, 2)  # Span both columns
        
        gpu_layout.addWidget(QtWidgets.QLabel("Render Mode:"), 2, 0)
        self.render_mode_combo = QtWidgets.QComboBox()
        self.render_mode_combo.addItems(["Normal", "Draft", "Fast", "Preview"])
        gpu_layout.addWidget(self.render_mode_combo, 2, 1)
        
        machine_column.addLayout(gpu_layout)
        
        # Divider
        divider2 = QtWidgets.QFrame()
        divider2.setFrameShape(QtWidgets.QFrame.HLine)
        divider2.setFrameShadow(QtWidgets.QFrame.Sunken)
        machine_column.addWidget(divider2)
        
        # RAM settings
        ram_layout = QtWidgets.QGridLayout()
        
        ram_layout.addWidget(QtWidgets.QLabel("Max RAM (GB):"), 0, 0)
        self.max_ram_spin = QtWidgets.QSpinBox()
        self.max_ram_spin.setMinimum(1)
        self.max_ram_spin.setMaximum(512)
        self.max_ram_spin.setValue(16)
        ram_layout.addWidget(self.max_ram_spin, 0, 1)
        
        ram_layout.addWidget(QtWidgets.QLabel("Min RAM (GB):"), 1, 0)
        self.min_ram_spin = QtWidgets.QSpinBox()
        self.min_ram_spin.setMinimum(1)
        self.min_ram_spin.setMaximum(64)
        self.min_ram_spin.setValue(4)
        ram_layout.addWidget(self.min_ram_spin, 1, 1)
        
        machine_column.addLayout(ram_layout)
        machine_column.addStretch()
        
        # Add both group boxes to the horizontal layout
        self.content_layout.addWidget(self.job_settings_group)
        self.content_layout.addWidget(self.machine_settings_group)
        
        # Add the settings container to main panel layout
        self.layout().addWidget(self.settings_container)
        
        # Override the resize event for the main panel to handle responsive behavior
        original_resize = self.resizeEvent
        def responsive_resize_event(event):
            self._handle_responsive_resize(event)
            if original_resize:
                original_resize(event)
        self.resizeEvent = responsive_resize_event
    
    def _handle_responsive_resize(self, event):
        """Handle panel resize to make settings responsive."""
        if hasattr(self, 'content_layout'):
            panel_width = event.size().width()
            
            # Calculate if we have enough space for horizontal layout
            # Account for margins and spacing
            available_width = panel_width - 60  # Account for margins and group box padding
            
            if available_width < 700:  # Stack vertically when narrow
                if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                    self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                    self.content_layout.setSpacing(20)  # More spacing when stacked vertically
            else:  # Side by side when wide enough
                if self.content_layout.direction() == QtWidgets.QBoxLayout.TopToBottom:
                    self.content_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)
                    self.content_layout.setSpacing(15)  # Less spacing when side by side
    
    def _create_tabbed_interface(self):
        """Create the tabbed interface for Render Order, Console, and Extra Settings."""
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Render Order tab
        self._create_render_order_tab()
        
        # Console tab
        self._create_console_tab()
        
        # Extra Settings tab
        self._create_extra_settings_tab()
        
        # Add tab widget to main layout
        self.layout().addWidget(self.tab_widget)
    
    def _create_render_order_tab(self):
        """Create the Render Order tab with table and controls."""
        render_order_widget = QtWidgets.QWidget()
        render_order_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        render_order_layout = QtWidgets.QVBoxLayout()
        render_order_widget.setLayout(render_order_layout)
        
        # Control buttons with filter
        button_layout = QtWidgets.QHBoxLayout()
        
        self.update_btn = QtWidgets.QPushButton("Update")
        self.update_btn.clicked.connect(lambda: print("Update clicked"))
        button_layout.addWidget(self.update_btn)
        
        self.all_btn = QtWidgets.QPushButton("All")
        self.all_btn.clicked.connect(lambda: print("All clicked"))
        button_layout.addWidget(self.all_btn)
        
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(lambda: print("Clear clicked"))
        button_layout.addWidget(self.clear_btn)
        
        self.selection_btn = QtWidgets.QPushButton("Selection")
        self.selection_btn.clicked.connect(lambda: print("Selection clicked"))
        button_layout.addWidget(self.selection_btn)
        
        self.inside_groups_check = QtWidgets.QCheckBox("Inside groups")
        self.inside_groups_check.stateChanged.connect(lambda state: print(f"Inside groups: {state == 2}"))
        button_layout.addWidget(self.inside_groups_check)
        
        # Add spacer to push filter to the right
        button_layout.addStretch()
        
        # Filter input on same row
        button_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("filter...")
        self.filter_edit.setMaximumWidth(150)  # Limit width so it doesn't take too much space
        button_layout.addWidget(self.filter_edit)
        
        render_order_layout.addLayout(button_layout)
        
        # Render Order Table
        self.render_table = QtWidgets.QTableWidget()
        self.render_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        headers = ["RenderOrder", "Node Name", "Filename", "Chunk Size", "Frames", "Pool", "Group", "Priority"]
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(headers)
        
        # Sample data - updated to include new columns
        sample_data = [
            ("3999", "Write4", "PartCloth_comp2k_v01.%04d.exr", "3", "1350-1650", "comp", "workstations", "50"),
            ("3100", "Write30", "PartMP08Out_comp2k_v02.%04d.exr", "3", "1350-1650", "comp", "workstations", "40"),
            ("3050", "Write27", "PartPreBank_comp2k_v01.%04d.exr", "5", "1570-1620", "comp", "workstations", "30"),
            ("3000", "Write9", "PartGlassTexture_comp2k_v01.%04d.exr", "8", "1350-1650", "render", "workstations", "60"),
            ("2999", "Write3", "PartBKOC_comp2k_v01.%04d.exr", "1", "1100-1400", "render", "workstations", "20"),
        ]
        
        self.render_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                self.render_table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))
        
        # Table properties
        self.render_table.setAlternatingRowColors(True)
        self.render_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.render_table.setSortingEnabled(True)
        self.render_table.resizeColumnsToContents()
        
        render_order_layout.addWidget(self.render_table)
        
        # Set stretch factor to make table expand
        render_order_layout.setStretchFactor(self.render_table, 1)
        
        # Add render order tab
        self.tab_widget.addTab(render_order_widget, "Render Order")
    
    def _create_console_tab(self):
        """Create the Console tab for output."""
        console_widget = QtWidgets.QWidget()
        console_layout = QtWidgets.QVBoxLayout()
        console_widget.setLayout(console_layout)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #2b2b2b; color: #ffffff; font-family: 'Courier New';")
        self.console_output.setText("Ready for submission...\nLatest submission: 2023-10-28 11:10:46")
        
        console_layout.addWidget(self.console_output)
        
        # Add console tab
        self.tab_widget.addTab(console_widget, "Console")
    
    def _create_extra_settings_tab(self):
        """Create the Extra Settings tab with Job Name, Comment, and Department."""
        extra_settings_widget = QtWidgets.QWidget()
        extra_settings_layout = QtWidgets.QVBoxLayout()
        extra_settings_layout.setContentsMargins(15, 15, 15, 15)  # Add padding
        extra_settings_layout.setSpacing(10)  # Add spacing between elements
        extra_settings_widget.setLayout(extra_settings_layout)
        
        # Job Information section
        job_info_group = QtWidgets.QGroupBox("Job Information")
        job_info_layout = QtWidgets.QGridLayout()
        job_info_layout.setSpacing(8)
        job_info_group.setLayout(job_info_layout)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Job Name:"), 0, 0)
        self.job_name_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.job_name_edit, 0, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Comment:"), 1, 0)
        self.comment_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.comment_edit, 1, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Department:"), 2, 0)
        self.department_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.department_edit, 2, 1)
        
        extra_settings_layout.addWidget(job_info_group)
        
        # Add stretch to push content to top
        extra_settings_layout.addStretch()
        
        # Add extra settings tab
        self.tab_widget.addTab(extra_settings_widget, "Extra Settings")
    
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
    
    def _on_render_clicked(self):
        """Handle render button click - show development message."""
        if NUKE_AVAILABLE:
            nuke.message('Nuke to Deadline panel is in development and not ready for production use.\n\nUse the "Submit Selected Writes to Deadline" option from the Render menu.')
        else:
            print("Nuke to Deadline panel is in development, Use the 'Submit Selected Writes to Deadline' options from the Render menu")


def create_dockable_panel():
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


def create_panel():
    """Create and return a new instance of the nk2dl panel.
    
    This function is used by the panel registration system.
    
    Returns:
        Nk2dlPanel: A new panel instance, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, cannot create panel")
        return None
        
    return Nk2dlPanel()
