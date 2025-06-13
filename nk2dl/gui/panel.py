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
        job_column = QtWidgets.QVBoxLayout()
        job_column.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        job_column.setSpacing(5)  # Consistent spacing
        self.job_settings_group.setLayout(job_column)
        
        # === MACHINE SETTINGS GROUP (Right) ===
        self.machine_settings_group = QtWidgets.QGroupBox("Machine Settings")
        machine_column = QtWidgets.QVBoxLayout()
        machine_column.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        machine_column.setSpacing(5)  # Consistent spacing
        self.machine_settings_group.setLayout(machine_column)
        
        # === JOB SETTINGS CONTENT ===
        # Create a more sophisticated layout similar to Machine Settings
        job_main_layout = QtWidgets.QVBoxLayout()
        job_main_layout.setSpacing(8)
        
        # First row: Pool + Secondary Pool
        pool_row = QtWidgets.QHBoxLayout()
        pool_row.setSpacing(10)
        
        pool_label = QtWidgets.QLabel("Pool")
        pool_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pool_label.setMinimumWidth(120)
        pool_row.addWidget(pool_label)
        
        self.pool_combo = QtWidgets.QComboBox()
        self.pool_combo.addItems(["comp", "render", "light", "fx"])
        self.pool_combo.setFixedWidth(100)
        pool_row.addWidget(self.pool_combo)
        
        # Vertical separator
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.VLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator1.setFixedWidth(1)
        pool_row.addWidget(separator1)
        
        secondary_pool_label = QtWidgets.QLabel("Secondary Pool")
        secondary_pool_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_row.addWidget(secondary_pool_label)
        
        self.secondary_pool_combo = QtWidgets.QComboBox()
        self.secondary_pool_combo.addItems(["", "comp", "render", "light", "fx"])
        self.secondary_pool_combo.setFixedWidth(100)
        pool_row.addWidget(self.secondary_pool_combo)
        pool_row.addStretch()
        
        job_main_layout.addLayout(pool_row)
        
        # Second row: Group
        group_row = QtWidgets.QHBoxLayout()
        group_row.setSpacing(10)
        
        group_label = QtWidgets.QLabel("Group")
        group_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        group_label.setMinimumWidth(120)
        group_row.addWidget(group_label)
        
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(["none", "comp_high", "comp_med", "render_high", "render_low"])
        self.group_combo.setFixedWidth(150)
        group_row.addWidget(self.group_combo)
        group_row.addStretch()
        
        job_main_layout.addLayout(group_row)
        
        # Third row: Priority
        priority_row = QtWidgets.QHBoxLayout()
        priority_row.setSpacing(10)
        
        priority_label = QtWidgets.QLabel("Priority")
        priority_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        priority_label.setMinimumWidth(120)
        priority_row.addWidget(priority_label)
        
        self.priority_spin = QtWidgets.QSpinBox()
        self.priority_spin.setMinimum(0)
        self.priority_spin.setMaximum(100)
        self.priority_spin.setValue(50)
        self.priority_spin.setFixedWidth(60)
        priority_row.addWidget(self.priority_spin)
        priority_row.addStretch()
        
        job_main_layout.addLayout(priority_row)
        
        # Fourth row: Task Timeout + checkbox
        timeout_row = QtWidgets.QHBoxLayout()
        timeout_row.setSpacing(10)
        
        timeout_label = QtWidgets.QLabel("Task Timeout")
        timeout_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        timeout_label.setMinimumWidth(120)
        timeout_row.addWidget(timeout_label)
        
        self.task_timeout_spin = QtWidgets.QSpinBox()
        self.task_timeout_spin.setMinimum(0)
        self.task_timeout_spin.setMaximum(999)
        self.task_timeout_spin.setValue(0)
        self.task_timeout_spin.setFixedWidth(60)
        timeout_row.addWidget(self.task_timeout_spin)
        
        # Vertical separator
        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.VLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator2.setFixedWidth(1)
        timeout_row.addWidget(separator2)
        
        self.enable_auto_timeout_check = QtWidgets.QCheckBox("Enable auto task timeout")
        timeout_row.addWidget(self.enable_auto_timeout_check)
        timeout_row.addStretch()
        
        job_main_layout.addLayout(timeout_row)
        
        # Fifth row: Frames dropdown + string input + Chunk Size
        frames_row = QtWidgets.QHBoxLayout()
        frames_row.setSpacing(10)
        
        frames_label = QtWidgets.QLabel("Frames")
        frames_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        frames_label.setMinimumWidth(120)
        frames_row.addWidget(frames_label)
        
        self.frames_combo = QtWidgets.QComboBox()
        self.frames_combo.addItems(["Global", "Custom", "Input"])
        self.frames_combo.setFixedWidth(80)
        frames_row.addWidget(self.frames_combo)
        
        self.frame_range_edit = QtWidgets.QLineEdit("1001-2315")
        self.frame_range_edit.setMinimumWidth(150)
        frames_row.addWidget(self.frame_range_edit)
        
        # Add Chunk Size to end of frames line
        chunk_label = QtWidgets.QLabel("Chunk Size")
        chunk_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        frames_row.addWidget(chunk_label)
        
        self.chunk_size_spin = QtWidgets.QSpinBox()
        self.chunk_size_spin.setValue(1)
        self.chunk_size_spin.setMinimum(1)
        self.chunk_size_spin.setFixedWidth(60)
        frames_row.addWidget(self.chunk_size_spin)
        frames_row.addStretch()
        
        job_main_layout.addLayout(frames_row)
        
        # Sixth row: Render Mode (removed separate chunk size row)
        render_mode_row = QtWidgets.QHBoxLayout()
        render_mode_row.setSpacing(10)
        
        render_mode_label = QtWidgets.QLabel("Render Mode")
        render_mode_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        render_mode_label.setMinimumWidth(120)
        render_mode_row.addWidget(render_mode_label)
        
        self.render_mode_combo = QtWidgets.QComboBox()
        self.render_mode_combo.addItems(["Normal", "Draft", "Fast", "Preview"])
        self.render_mode_combo.setFixedWidth(100)
        render_mode_row.addWidget(self.render_mode_combo)
        render_mode_row.addStretch()
        
        job_main_layout.addLayout(render_mode_row)
        
        # Seventh row: Views + checkbox
        views_row = QtWidgets.QHBoxLayout()
        views_row.setSpacing(10)
        
        views_label = QtWidgets.QLabel("Views")
        views_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        views_label.setMinimumWidth(120)
        views_row.addWidget(views_label)
        
        self.views_combo = QtWidgets.QComboBox()
        self.views_combo.addItems(["All", "Main", "Left", "Right", "Custom"])
        self.views_combo.setFixedWidth(100)
        views_row.addWidget(self.views_combo)
        
        # Vertical separator
        separator4 = QtWidgets.QFrame()
        separator4.setFrameShape(QtWidgets.QFrame.VLine)
        separator4.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator4.setFixedWidth(1)
        views_row.addWidget(separator4)
        
        self.views_separate_jobs_check = QtWidgets.QCheckBox("Views as separate jobs")
        views_row.addWidget(self.views_separate_jobs_check)
        views_row.addStretch()
        
        job_main_layout.addLayout(views_row)
        
        # Eighth row: Use Nuke X + Use Batch Mode checkboxes
        checkboxes_row = QtWidgets.QHBoxLayout()
        checkboxes_row.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label = QtWidgets.QLabel("")
        empty_label.setMinimumWidth(120)
        checkboxes_row.addWidget(empty_label)
        
        self.render_nukex_check = QtWidgets.QCheckBox("Use Nuke X")
        checkboxes_row.addWidget(self.render_nukex_check)
        
        self.use_batch_mode_check = QtWidgets.QCheckBox("Use batch mode")
        checkboxes_row.addWidget(self.use_batch_mode_check)
        checkboxes_row.addStretch()
        
        job_main_layout.addLayout(checkboxes_row)
        
        job_column.addLayout(job_main_layout)
        job_column.addStretch()
        
        # === MACHINE SETTINGS CONTENT ===
        # Create a more sophisticated layout with fixed widget sizes
        machine_main_layout = QtWidgets.QVBoxLayout()
        machine_main_layout.setSpacing(8)
        
        # First row: Threads
        threads_row = QtWidgets.QHBoxLayout()
        threads_row.setSpacing(10)
        
        threads_label = QtWidgets.QLabel("Threads")
        threads_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        threads_label.setMinimumWidth(120)  # Fixed label width
        threads_row.addWidget(threads_label)
        
        self.threads_spin = QtWidgets.QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(64)
        self.threads_spin.setValue(4)
        self.threads_spin.setFixedWidth(60)  # Fixed widget width
        threads_row.addWidget(self.threads_spin)
        threads_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(threads_row)
        
        # Second row: Min RAM + Max RAM
        ram_row = QtWidgets.QHBoxLayout()
        ram_row.setSpacing(10)
        
        min_ram_label = QtWidgets.QLabel("Min RAM (GB)")
        min_ram_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        min_ram_label.setMinimumWidth(120)  # Same fixed label width
        ram_row.addWidget(min_ram_label)
        
        self.min_ram_spin = QtWidgets.QSpinBox()
        self.min_ram_spin.setMinimum(1)
        self.min_ram_spin.setMaximum(64)
        self.min_ram_spin.setValue(0)
        self.min_ram_spin.setFixedWidth(60)  # Fixed widget width
        ram_row.addWidget(self.min_ram_spin)
        
        # Vertical separator
        separator5 = QtWidgets.QFrame()
        separator5.setFrameShape(QtWidgets.QFrame.VLine)
        separator5.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator5.setFixedWidth(1)
        ram_row.addWidget(separator5)
        
        self.max_ram_spin = QtWidgets.QSpinBox()
        self.max_ram_spin.setMinimum(1)
        self.max_ram_spin.setMaximum(512)
        self.max_ram_spin.setValue(0)
        self.max_ram_spin.setFixedWidth(60)  # Fixed widget width
        ram_row.addWidget(self.max_ram_spin)
        
        max_ram_label = QtWidgets.QLabel("Max RAM (GB)")
        max_ram_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        ram_row.addWidget(max_ram_label)
        ram_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(ram_row)
        
        # Third row: GPU Device + GPU Override + Use GPU
        gpu_row = QtWidgets.QHBoxLayout()
        gpu_row.setSpacing(10)
        
        gpu_device_label = QtWidgets.QLabel("GPU Device")
        gpu_device_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        gpu_device_label.setMinimumWidth(120)  # Fixed label width
        gpu_row.addWidget(gpu_device_label)
        
        self.gpu_override_spin = QtWidgets.QSpinBox()
        self.gpu_override_spin.setMinimum(0)
        self.gpu_override_spin.setMaximum(16)
        self.gpu_override_spin.setValue(0)
        self.gpu_override_spin.setFixedWidth(60)  # Fixed widget width
        gpu_row.addWidget(self.gpu_override_spin)
        
        # Vertical separator
        separator6 = QtWidgets.QFrame()
        separator6.setFrameShape(QtWidgets.QFrame.VLine)
        separator6.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator6.setFixedWidth(1)
        gpu_row.addWidget(separator6)
        
        self.use_gpu_check = QtWidgets.QCheckBox("Use GPU")
        gpu_row.addWidget(self.use_gpu_check)
        gpu_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(gpu_row)
        
        # Fourth row: Concurrent Tasks + checkbox
        concurrent_row = QtWidgets.QHBoxLayout()
        concurrent_row.setSpacing(10)
        
        concurrent_label = QtWidgets.QLabel("Concurrent Tasks")
        concurrent_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        concurrent_label.setMinimumWidth(120)  # Same fixed label width
        concurrent_row.addWidget(concurrent_label)
        
        self.concurrent_tasks_spin = QtWidgets.QSpinBox()
        self.concurrent_tasks_spin.setMinimum(1)
        self.concurrent_tasks_spin.setMaximum(64)
        self.concurrent_tasks_spin.setValue(2)
        self.concurrent_tasks_spin.setFixedWidth(60)  # Fixed widget width
        concurrent_row.addWidget(self.concurrent_tasks_spin)
        
        # Vertical separator
        separator7 = QtWidgets.QFrame()
        separator7.setFrameShape(QtWidgets.QFrame.VLine)
        separator7.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator7.setFixedWidth(1)
        concurrent_row.addWidget(separator7)
        
        self.limit_tasks_check = QtWidgets.QCheckBox("Limit tasks to worker's task limit")
        concurrent_row.addWidget(self.limit_tasks_check)
        concurrent_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(concurrent_row)
        
        # Fifth row: Machine Limit + checkbox
        limit_row = QtWidgets.QHBoxLayout()
        limit_row.setSpacing(10)
        
        machine_limit_label = QtWidgets.QLabel("Machine Limit")
        machine_limit_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_limit_label.setMinimumWidth(120)  # Same fixed label width
        limit_row.addWidget(machine_limit_label)
        
        self.machine_limit_spin = QtWidgets.QSpinBox()
        self.machine_limit_spin.setMinimum(0)
        self.machine_limit_spin.setMaximum(999)
        self.machine_limit_spin.setValue(0)
        self.machine_limit_spin.setFixedWidth(60)  # Fixed widget width
        limit_row.addWidget(self.machine_limit_spin)
        
        # Vertical separator
        separator8 = QtWidgets.QFrame()
        separator8.setFrameShape(QtWidgets.QFrame.VLine)
        separator8.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator8.setFixedWidth(1)
        limit_row.addWidget(separator8)
        
        self.machine_deny_list_check = QtWidgets.QCheckBox("Machine list is a deny list")
        limit_row.addWidget(self.machine_deny_list_check)
        limit_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(limit_row)
        
        # Sixth row: Machine List + Browse button
        machine_list_row = QtWidgets.QHBoxLayout()
        machine_list_row.setSpacing(10)
        
        machine_list_label = QtWidgets.QLabel("Machine List")
        machine_list_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_list_label.setMinimumWidth(120)  # Same fixed label width
        machine_list_row.addWidget(machine_list_label)
        
        self.machine_list_edit = QtWidgets.QLineEdit()
        self.machine_list_edit.setMinimumWidth(300)  # Fixed minimum width
        machine_list_row.addWidget(self.machine_list_edit)
        
        self.machine_list_browse_btn = QtWidgets.QPushButton("Browse")
        self.machine_list_browse_btn.setFixedWidth(80)  # Fixed button width
        machine_list_row.addWidget(self.machine_list_browse_btn)
        
        machine_main_layout.addLayout(machine_list_row)
        
        # Seventh row: Limits + Browse button
        limits_row = QtWidgets.QHBoxLayout()
        limits_row.setSpacing(10)
        
        limits_label = QtWidgets.QLabel("Limits")
        limits_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        limits_label.setMinimumWidth(120)  # Same fixed label width
        limits_row.addWidget(limits_label)
        
        self.limits_edit = QtWidgets.QLineEdit()
        self.limits_edit.setMinimumWidth(300)  # Fixed minimum width
        limits_row.addWidget(self.limits_edit)
        
        self.limits_browse_btn = QtWidgets.QPushButton("Browse")
        self.limits_browse_btn.setFixedWidth(80)  # Fixed button width
        limits_row.addWidget(self.limits_browse_btn)
        
        machine_main_layout.addLayout(limits_row)
        
        machine_column.addLayout(machine_main_layout)
        machine_column.addStretch()
        
        # Add both group boxes to the horizontal layout with equal stretch
        self.content_layout.addWidget(self.job_settings_group, 1)  # Stretch factor 1
        self.content_layout.addWidget(self.machine_settings_group, 1)  # Stretch factor 1
        
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
            ("3999", "Write4", "Some_path1_v002.%04d.exr", "3", "1350-1650", "comp", "workstations", "50"),
            ("3100", "Write30", "Some_path3_v002.%04d.exr", "3", "1350-1650", "comp", "workstations", "40"),
            ("3050", "Write27", "Some_path5_v002.%04d.exr", "5", "1570-1620", "comp", "workstations", "30"),
            ("3000", "Write9", "Some_path6_v002.%04d.exr", "8", "1350-1650", "render", "workstations", "60"),
            ("2999", "Write3", "Some_path9_v002.%04d.exr", "1", "1100-1400", "render", "workstations", "20"),
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