# -*- coding: utf-8 -*-
"""View components for the nk2dl panel.

This module contains all view classes used for rendering UI components in the nk2dl panel interface.
Views handle UI presentation and user interaction, connecting to models for data management.
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

from .widgets import ColoredGroupBox
from .constants import Settings, Sizes, GSVDefaults


class SettingsView(QtWidgets.QWidget):
    """View for job and machine settings with responsive layout.
    
    This view handles the UI for job settings and machine settings sections,
    including responsive behavior that switches between horizontal and vertical
    layouts based on available width.
    """
    
    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings_model = settings_model
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_settings_from_model()
        
        # Set up responsive resize handling
        self._setup_responsive_behavior()
    
    def _create_ui(self):
        """Create the settings UI components."""
        # Main container with horizontal layout for responsive behavior
        self.content_layout = QtWidgets.QHBoxLayout()  # Start horizontal
        self.content_layout.setSpacing(Sizes.SETTINGS_SPACING)
        self.content_layout.setContentsMargins(0, 0, 0, Sizes.SETTINGS_BOTTOM_MARGIN)
        self.setLayout(self.content_layout)
        
        # Create job and machine settings groups
        self._create_job_settings_group()
        self._create_machine_settings_group()
        
        # Add groups to layout
        self.content_layout.addWidget(self.job_settings_group, 1)  # Stretch factor 1
        self.content_layout.addWidget(self.machine_settings_group, 1)  # Stretch factor 1
    
    def _create_job_settings_group(self):
        """Create the Job Settings group box and controls."""
        self.job_settings_group = ColoredGroupBox("Job Settings", "#4A90E2")
        self.job_settings_group.setMinimumWidth(Sizes.JOB_SETTINGS_MIN_WIDTH)
        job_layout = QtWidgets.QVBoxLayout()
        job_layout.setContentsMargins(Sizes.SETTINGS_MARGIN, 25, Sizes.SETTINGS_MARGIN, Sizes.SETTINGS_MARGIN)
        job_layout.setSpacing(8)
        self.job_settings_group.setLayout(job_layout)
        
        # Create job settings content
        job_main_layout = QtWidgets.QVBoxLayout()
        job_main_layout.setSpacing(8)
        
        # Priority + Chunk Size row
        priority_chunk_row = QtWidgets.QHBoxLayout()
        priority_chunk_row.setSpacing(10)
        
        priority_label = QtWidgets.QLabel("Priority")
        priority_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        priority_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        priority_chunk_row.addWidget(priority_label)
        
        self.priority_spin = QtWidgets.QSpinBox()
        self.priority_spin.setMinimum(0)
        self.priority_spin.setMaximum(100)
        self.priority_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.priority_spin.setToolTip("A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority.")
        priority_chunk_row.addWidget(self.priority_spin)
        
        chunk_label = QtWidgets.QLabel("Chunk")
        chunk_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        priority_chunk_row.addWidget(chunk_label)
        
        self.chunk_size_spin = QtWidgets.QSpinBox()
        self.chunk_size_spin.setMinimum(1)
        self.chunk_size_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.chunk_size_spin.setToolTip("This is the number of frames that will be rendered at a time for each job task.")
        priority_chunk_row.addWidget(self.chunk_size_spin)
        priority_chunk_row.addStretch()
        
        job_main_layout.addLayout(priority_chunk_row)
        
        # Frames row
        frames_row = QtWidgets.QHBoxLayout()
        frames_row.setSpacing(10)
        
        frames_label = QtWidgets.QLabel("Frames")
        frames_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        frames_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        frames_row.addWidget(frames_label)
        
        self.frames_combo = QtWidgets.QComboBox()
        self.frames_combo.addItems(Settings.FRAMES_OPTIONS)
        self.frames_combo.setFixedWidth(80)
        self.frames_combo.setToolTip("Select the Global, Input, or Custom frame list mode.")
        frames_row.addWidget(self.frames_combo)
        
        self.frame_range_edit = QtWidgets.QLineEdit()
        self.frame_range_edit.setMinimumWidth(Sizes.LINE_EDIT_MIN_WIDTH)
        self.frame_range_edit.setToolTip("If Custom frame list mode is selected, this is the list of frames to render.")
        frames_row.addWidget(self.frame_range_edit)
        frames_row.addStretch()
        
        job_main_layout.addLayout(frames_row)
        
        # Use node's frame list checkbox
        node_frame_list_row = QtWidgets.QHBoxLayout()
        node_frame_list_row.setSpacing(10)
        
        empty_label1 = QtWidgets.QLabel("")
        empty_label1.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        node_frame_list_row.addWidget(empty_label1)
        
        self.use_node_frame_list_check = QtWidgets.QCheckBox("Use node's frame list")
        self.use_node_frame_list_check.setToolTip("If submitting each write node as a separate job, enable this to pull the frame range from the write node, instead of using the global frame range.")
        node_frame_list_row.addWidget(self.use_node_frame_list_check)
        node_frame_list_row.addStretch()
        
        job_main_layout.addLayout(node_frame_list_row)
        
        # Task Timeout row
        timeout_row = QtWidgets.QHBoxLayout()
        timeout_row.setSpacing(10)
        
        timeout_label = QtWidgets.QLabel("Task Timeout")
        timeout_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        timeout_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        timeout_row.addWidget(timeout_label)
        
        self.task_timeout_spin = QtWidgets.QSpinBox()
        self.task_timeout_spin.setMinimum(0)
        self.task_timeout_spin.setMaximum(999)
        self.task_timeout_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.task_timeout_spin.setToolTip("The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit.")
        timeout_row.addWidget(self.task_timeout_spin)
        
        minutes_label = QtWidgets.QLabel("minutes")
        minutes_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        timeout_row.addWidget(minutes_label)
        
        self.enable_auto_timeout_check = QtWidgets.QCheckBox("Enable auto task timeout")
        self.enable_auto_timeout_check.setToolTip("If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.")
        timeout_row.addWidget(self.enable_auto_timeout_check)
        timeout_row.addStretch()
        
        job_main_layout.addLayout(timeout_row)
        
        # Render Mode row
        render_mode_row = QtWidgets.QHBoxLayout()
        render_mode_row.setSpacing(10)
        
        render_mode_label = QtWidgets.QLabel("Render Mode")
        render_mode_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        render_mode_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        render_mode_row.addWidget(render_mode_label)
        
        self.render_mode_combo = QtWidgets.QComboBox()
        self.render_mode_combo.addItems(["Full", "Proxy", "Both", "Script"])
        self.render_mode_combo.setFixedWidth(Sizes.COMBO_WIDTH)
        self.render_mode_combo.setToolTip("The mode to render with.")
        render_mode_row.addWidget(self.render_mode_combo)
        render_mode_row.addStretch()
        
        job_main_layout.addLayout(render_mode_row)
        
        # Checkboxes row
        checkboxes_row = QtWidgets.QHBoxLayout()
        checkboxes_row.setSpacing(10)
        
        empty_label2 = QtWidgets.QLabel("")
        empty_label2.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        checkboxes_row.addWidget(empty_label2)
        
        self.render_nukex_check = QtWidgets.QCheckBox("Use Nuke X")
        self.render_nukex_check.setToolTip("If checked, NukeX will be used instead of just Nuke.")
        checkboxes_row.addWidget(self.render_nukex_check)
        
        self.use_batch_mode_check = QtWidgets.QCheckBox("Use batch mode")
        self.use_batch_mode_check.setToolTip("This uses the Nuke plugin's Batch Mode. It keeps the Nuke script loaded in memory between frames, which reduces the overhead of rendering the job.")
        checkboxes_row.addWidget(self.use_batch_mode_check)
        
        self.reload_plugin_check = QtWidgets.QCheckBox("Reload plugin between tasks")
        self.reload_plugin_check.setToolTip("If checked, Nuke will force all memory to be released before starting the next task, but this can increase the overhead time between tasks.")
        checkboxes_row.addWidget(self.reload_plugin_check)
        checkboxes_row.addStretch()
        
        job_main_layout.addLayout(checkboxes_row)
        
        # Divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setFrameShadow(QtWidgets.QFrame.Sunken)
        divider.setStyleSheet("color: #C0C0C0; margin: 5px 0px;")
        job_main_layout.addWidget(divider)
        
        # Job organization checkboxes
        job_org_row1 = QtWidgets.QHBoxLayout()
        job_org_row1.setSpacing(10)
        
        empty_label3 = QtWidgets.QLabel("")
        empty_label3.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_org_row1.addWidget(empty_label3)
        
        self.separate_tasks_check = QtWidgets.QCheckBox("Write node as separate tasks for the same job")
        self.separate_tasks_check.setToolTip("Enable to submit a job to Deadline where each task for the job represents a different write node, and all frames for that write node are rendered by its corresponding task.")
        job_org_row1.addWidget(self.separate_tasks_check)
        job_org_row1.addStretch()
        
        job_main_layout.addLayout(job_org_row1)
        
        job_org_row2 = QtWidgets.QHBoxLayout()
        job_org_row2.setSpacing(10)
        
        empty_label4 = QtWidgets.QLabel("")
        empty_label4.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_org_row2.addWidget(empty_label4)
        
        self.separate_jobs_check = QtWidgets.QCheckBox("Write nodes as separate jobs")
        self.separate_jobs_check.setToolTip("Enable to submit each write node to Deadline as a separate job.")
        job_org_row2.addWidget(self.separate_jobs_check)
        job_org_row2.addStretch()
        
        job_main_layout.addLayout(job_org_row2)
        
        job_org_row3 = QtWidgets.QHBoxLayout()
        job_org_row3.setSpacing(10)
        
        empty_label5 = QtWidgets.QLabel("")
        empty_label5.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        job_org_row3.addWidget(empty_label5)
        
        self.views_separate_jobs_check = QtWidgets.QCheckBox("Views as separate jobs")
        self.views_separate_jobs_check.setToolTip("Choose the view(s) you wish to render. This is optional.")
        job_org_row3.addWidget(self.views_separate_jobs_check)
        job_org_row3.addStretch()
        
        job_main_layout.addLayout(job_org_row3)
        
        job_layout.addLayout(job_main_layout)
        job_layout.addStretch()
    
    def _create_machine_settings_group(self):
        """Create the Machine Settings group box and controls."""
        self.machine_settings_group = ColoredGroupBox("Machine Settings", "#8E44AD")
        self.machine_settings_group.setMinimumWidth(Sizes.MACHINE_SETTINGS_MIN_WIDTH)
        machine_layout = QtWidgets.QVBoxLayout()
        machine_layout.setContentsMargins(Sizes.SETTINGS_MARGIN, 25, Sizes.SETTINGS_MARGIN, Sizes.SETTINGS_MARGIN)
        machine_layout.setSpacing(8)
        self.machine_settings_group.setLayout(machine_layout)
        
        # Create machine settings content
        machine_main_layout = QtWidgets.QVBoxLayout()
        machine_main_layout.setSpacing(8)
        
        # Pool + Secondary Pool + Group row
        pool_group_row = QtWidgets.QHBoxLayout()
        pool_group_row.setSpacing(10)
        
        pool_label = QtWidgets.QLabel("Pool")
        pool_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pool_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        pool_group_row.addWidget(pool_label)
        
        self.pool_combo = QtWidgets.QComboBox()
        self.pool_combo.addItems(Settings.POOL_OPTIONS)
        self.pool_combo.setFixedWidth(Sizes.COMBO_WIDTH)
        self.pool_combo.setToolTip("The pool that your job will be submitted to.")
        pool_group_row.addWidget(self.pool_combo)
        
        secondary_pool_label = QtWidgets.QLabel("Secondary Pool")
        secondary_pool_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(secondary_pool_label)
        
        self.secondary_pool_combo = QtWidgets.QComboBox()
        self.secondary_pool_combo.addItems([""] + Settings.POOL_OPTIONS)
        self.secondary_pool_combo.setFixedWidth(Sizes.COMBO_WIDTH)
        self.secondary_pool_combo.setToolTip("The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.")
        pool_group_row.addWidget(self.secondary_pool_combo)
        
        group_label = QtWidgets.QLabel("Group")
        group_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(group_label)
        
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(Settings.GROUP_OPTIONS)
        self.group_combo.setFixedWidth(120)
        self.group_combo.setToolTip("The group that your job will be submitted to.")
        pool_group_row.addWidget(self.group_combo)
        pool_group_row.addStretch()
        
        machine_main_layout.addLayout(pool_group_row)
        
        # Threads row
        threads_row = QtWidgets.QHBoxLayout()
        threads_row.setSpacing(10)
        
        threads_label = QtWidgets.QLabel("Threads")
        threads_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        threads_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        threads_row.addWidget(threads_label)
        
        self.threads_spin = QtWidgets.QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(64)
        self.threads_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.threads_spin.setToolTip("The number of threads to use for rendering. Set to 0 to have Nuke automatically determine the optimal thread count.")
        threads_row.addWidget(self.threads_spin)
        threads_row.addStretch()
        
        machine_main_layout.addLayout(threads_row)
        
        # RAM row
        ram_row = QtWidgets.QHBoxLayout()
        ram_row.setSpacing(10)
        
        min_ram_label = QtWidgets.QLabel("Min RAM (GB)")
        min_ram_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        min_ram_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        ram_row.addWidget(min_ram_label)
        
        self.min_ram_spin = QtWidgets.QSpinBox()
        self.min_ram_spin.setMinimum(0)
        self.min_ram_spin.setMaximum(64)
        self.min_ram_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.min_ram_spin.setToolTip("The minimum RAM usage (in GB) to be used for rendering. Set to 0 to not enforce a minimum amount of RAM.")
        ram_row.addWidget(self.min_ram_spin)
        
        self.max_ram_spin = QtWidgets.QSpinBox()
        self.max_ram_spin.setMinimum(0)
        self.max_ram_spin.setMaximum(512)
        self.max_ram_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.max_ram_spin.setToolTip("The maximum RAM usage (in GB) to be used for rendering. Set to 0 to not enforce a maximum amount of RAM.")
        ram_row.addWidget(self.max_ram_spin)
        
        max_ram_label = QtWidgets.QLabel("Max RAM (GB)")
        max_ram_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        ram_row.addWidget(max_ram_label)
        ram_row.addStretch()
        
        machine_main_layout.addLayout(ram_row)
        
        # GPU row
        gpu_row = QtWidgets.QHBoxLayout()
        gpu_row.setSpacing(10)
        
        gpu_device_label = QtWidgets.QLabel("GPU Device")
        gpu_device_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        gpu_device_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        gpu_row.addWidget(gpu_device_label)
        
        self.gpu_override_spin = QtWidgets.QSpinBox()
        self.gpu_override_spin.setMinimum(0)
        self.gpu_override_spin.setMaximum(16)
        self.gpu_override_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.gpu_override_spin.setToolTip("The GPU to use when rendering.")
        gpu_row.addWidget(self.gpu_override_spin)
        
        self.use_gpu_check = QtWidgets.QCheckBox("Use GPU")
        self.use_gpu_check.setToolTip("If Nuke should also use the GPU for rendering.")
        gpu_row.addWidget(self.use_gpu_check)
        gpu_row.addStretch()
        
        machine_main_layout.addLayout(gpu_row)
        
        # Concurrent Tasks row
        concurrent_row = QtWidgets.QHBoxLayout()
        concurrent_row.setSpacing(10)
        
        concurrent_label = QtWidgets.QLabel("Concurrent Tasks")
        concurrent_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        concurrent_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        concurrent_row.addWidget(concurrent_label)
        
        self.concurrent_tasks_spin = QtWidgets.QSpinBox()
        self.concurrent_tasks_spin.setMinimum(1)
        self.concurrent_tasks_spin.setMaximum(64)
        self.concurrent_tasks_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.concurrent_tasks_spin.setToolTip("The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs.")
        concurrent_row.addWidget(self.concurrent_tasks_spin)
        
        self.limit_tasks_check = QtWidgets.QCheckBox("Limit tasks to worker's task limit")
        self.limit_tasks_check.setToolTip("If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator.")
        concurrent_row.addWidget(self.limit_tasks_check)
        concurrent_row.addStretch()
        
        machine_main_layout.addLayout(concurrent_row)
        
        # Machine Limit row
        limit_row = QtWidgets.QHBoxLayout()
        limit_row.setSpacing(10)
        
        machine_limit_label = QtWidgets.QLabel("Machine Limit")
        machine_limit_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_limit_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        limit_row.addWidget(machine_limit_label)
        
        self.machine_limit_spin = QtWidgets.QSpinBox()
        self.machine_limit_spin.setMinimum(0)
        self.machine_limit_spin.setMaximum(999)
        self.machine_limit_spin.setFixedWidth(Sizes.SPINBOX_WIDTH)
        self.machine_limit_spin.setToolTip("Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.")
        limit_row.addWidget(self.machine_limit_spin)
        
        self.machine_deny_list_check = QtWidgets.QCheckBox("Machine list is a deny list")
        self.machine_deny_list_check.setToolTip("You can force the job to render on specific machines by using an allow list, or you can avoid specific machines by using a deny list.")
        limit_row.addWidget(self.machine_deny_list_check)
        limit_row.addStretch()
        
        machine_main_layout.addLayout(limit_row)
        
        # Machine List row
        machine_list_row = QtWidgets.QHBoxLayout()
        machine_list_row.setSpacing(10)
        
        machine_list_label = QtWidgets.QLabel("Machine List")
        machine_list_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_list_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        machine_list_row.addWidget(machine_list_label)
        
        self.machine_list_edit = QtWidgets.QLineEdit()
        self.machine_list_edit.setMinimumWidth(300)
        self.machine_list_edit.setToolTip("The list of machines on the deny list or allow list.")
        machine_list_row.addWidget(self.machine_list_edit)
        
        self.machine_list_browse_btn = QtWidgets.QPushButton("Browse")
        self.machine_list_browse_btn.setFixedWidth(Sizes.BUTTON_WIDTH)
        machine_list_row.addWidget(self.machine_list_browse_btn)
        
        machine_main_layout.addLayout(machine_list_row)
        
        # Limits row
        limits_row = QtWidgets.QHBoxLayout()
        limits_row.setSpacing(10)
        
        limits_label = QtWidgets.QLabel("Limits")
        limits_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        limits_label.setMinimumWidth(Sizes.SETTINGS_LABEL_WIDTH)
        limits_row.addWidget(limits_label)
        
        self.limits_edit = QtWidgets.QLineEdit()
        self.limits_edit.setMinimumWidth(300)
        self.limits_edit.setToolTip("The Limits that your job requires.")
        limits_row.addWidget(self.limits_edit)
        
        self.limits_browse_btn = QtWidgets.QPushButton("Browse")
        self.limits_browse_btn.setFixedWidth(Sizes.BUTTON_WIDTH)
        limits_row.addWidget(self.limits_browse_btn)
        
        machine_main_layout.addLayout(limits_row)
        
        machine_layout.addLayout(machine_main_layout)
        machine_layout.addStretch()
    
    def _connect_signals(self):
        """Connect UI signals to model updates."""
        # Job Settings signals
        self.priority_spin.valueChanged.connect(lambda v: self.settings_model.set_job_setting('priority', v))
        self.chunk_size_spin.valueChanged.connect(lambda v: self.settings_model.set_job_setting('chunk_size', v))
        self.frames_combo.currentTextChanged.connect(lambda t: self.settings_model.set_job_setting('frames_mode', t))
        self.frame_range_edit.textChanged.connect(lambda t: self.settings_model.set_job_setting('frames', t))
        self.use_node_frame_list_check.toggled.connect(lambda c: self.settings_model.set_job_setting('nodes_frames', c))
        self.task_timeout_spin.valueChanged.connect(lambda v: self.settings_model.set_job_setting('task_timeout', v))
        self.enable_auto_timeout_check.toggled.connect(lambda c: self.settings_model.set_job_setting('auto_timeout', c))
        self.render_mode_combo.currentTextChanged.connect(lambda t: self.settings_model.set_job_setting('render_mode', t))
        self.render_nukex_check.toggled.connect(lambda c: self.settings_model.set_job_setting('use_nukex', c))
        self.use_batch_mode_check.toggled.connect(lambda c: self.settings_model.set_job_setting('use_batch_mode', c))
        self.reload_plugin_check.toggled.connect(lambda c: self.settings_model.set_job_setting('reload_plugin', c))
        self.separate_tasks_check.toggled.connect(lambda c: self.settings_model.set_job_setting('separate_tasks', c))
        self.separate_jobs_check.toggled.connect(lambda c: self.settings_model.set_job_setting('separate_jobs', c))
        self.views_separate_jobs_check.toggled.connect(lambda c: self.settings_model.set_job_setting('views_separate_jobs', c))
        
        # Machine Settings signals
        self.pool_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('pool', t))
        self.secondary_pool_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('secondary_pool', t))
        self.group_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('group', t))
        self.threads_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('threads', v))
        self.min_ram_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('min_ram', v))
        self.max_ram_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('max_ram', v))
        self.gpu_override_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('gpu_device', v))
        self.use_gpu_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('use_gpu', c))
        self.concurrent_tasks_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('concurrent_tasks', v))
        self.limit_tasks_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('limit_tasks', c))
        self.machine_limit_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('machine_limit', v))
        self.machine_deny_list_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('machine_deny_list', c))
        self.machine_list_edit.textChanged.connect(lambda t: self.settings_model.set_machine_setting('machine_list', t))
        self.limits_edit.textChanged.connect(lambda t: self.settings_model.set_machine_setting('limits', t))
        
        # Model change signals
        self.settings_model.jobSettingsChanged.connect(self._on_job_settings_changed)
        self.settings_model.machineSettingsChanged.connect(self._on_machine_settings_changed)
    
    def _load_settings_from_model(self):
        """Load current settings from the model into the UI."""
        # Block signals to prevent feedback loops
        self._block_signals(True)
        
        try:
            # Load job settings
            job_settings = self.settings_model.get_all_job_settings()
            self.priority_spin.setValue(job_settings.get('priority', 50))
            self.chunk_size_spin.setValue(job_settings.get('chunk_size', 1))
            
            frames_mode = job_settings.get('frames_mode', 'Global')
            index = self.frames_combo.findText(frames_mode)
            if index >= 0:
                self.frames_combo.setCurrentIndex(index)
            
            self.frame_range_edit.setText(job_settings.get('frames', '1001-2315'))
            self.use_node_frame_list_check.setChecked(job_settings.get('nodes_frames', False))
            self.task_timeout_spin.setValue(job_settings.get('task_timeout', 0))
            self.enable_auto_timeout_check.setChecked(job_settings.get('auto_timeout', False))
            
            render_mode = job_settings.get('render_mode', 'Full')
            index = self.render_mode_combo.findText(render_mode)
            if index >= 0:
                self.render_mode_combo.setCurrentIndex(index)
            
            self.render_nukex_check.setChecked(job_settings.get('use_nukex', False))
            self.use_batch_mode_check.setChecked(job_settings.get('use_batch_mode', False))
            self.reload_plugin_check.setChecked(job_settings.get('reload_plugin', False))
            self.separate_tasks_check.setChecked(job_settings.get('separate_tasks', False))
            self.separate_jobs_check.setChecked(job_settings.get('separate_jobs', False))
            self.views_separate_jobs_check.setChecked(job_settings.get('views_separate_jobs', False))
            
            # Load machine settings
            machine_settings = self.settings_model.get_all_machine_settings()
            
            pool = machine_settings.get('pool', 'comp')
            index = self.pool_combo.findText(pool)
            if index >= 0:
                self.pool_combo.setCurrentIndex(index)
            
            secondary_pool = machine_settings.get('secondary_pool', '')
            index = self.secondary_pool_combo.findText(secondary_pool)
            if index >= 0:
                self.secondary_pool_combo.setCurrentIndex(index)
            
            group = machine_settings.get('group', 'none')
            index = self.group_combo.findText(group)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
            
            self.threads_spin.setValue(machine_settings.get('threads', 4))
            self.min_ram_spin.setValue(machine_settings.get('min_ram', 0))
            self.max_ram_spin.setValue(machine_settings.get('max_ram', 0))
            self.gpu_override_spin.setValue(machine_settings.get('gpu_device', 0))
            self.use_gpu_check.setChecked(machine_settings.get('use_gpu', False))
            self.concurrent_tasks_spin.setValue(machine_settings.get('concurrent_tasks', 2))
            self.limit_tasks_check.setChecked(machine_settings.get('limit_tasks', False))
            self.machine_limit_spin.setValue(machine_settings.get('machine_limit', 0))
            self.machine_deny_list_check.setChecked(machine_settings.get('machine_deny_list', False))
            self.machine_list_edit.setText(machine_settings.get('machine_list', ''))
            self.limits_edit.setText(machine_settings.get('limits', ''))
            
        finally:
            # Re-enable signals
            self._block_signals(False)
    
    def _block_signals(self, block):
        """Block or unblock signals for all UI controls."""
        # Job settings controls
        self.priority_spin.blockSignals(block)
        self.chunk_size_spin.blockSignals(block)
        self.frames_combo.blockSignals(block)
        self.frame_range_edit.blockSignals(block)
        self.use_node_frame_list_check.blockSignals(block)
        self.task_timeout_spin.blockSignals(block)
        self.enable_auto_timeout_check.blockSignals(block)
        self.render_mode_combo.blockSignals(block)
        self.render_nukex_check.blockSignals(block)
        self.use_batch_mode_check.blockSignals(block)
        self.reload_plugin_check.blockSignals(block)
        self.separate_tasks_check.blockSignals(block)
        self.separate_jobs_check.blockSignals(block)
        self.views_separate_jobs_check.blockSignals(block)
        
        # Machine settings controls
        self.pool_combo.blockSignals(block)
        self.secondary_pool_combo.blockSignals(block)
        self.group_combo.blockSignals(block)
        self.threads_spin.blockSignals(block)
        self.min_ram_spin.blockSignals(block)
        self.max_ram_spin.blockSignals(block)
        self.gpu_override_spin.blockSignals(block)
        self.use_gpu_check.blockSignals(block)
        self.concurrent_tasks_spin.blockSignals(block)
        self.limit_tasks_check.blockSignals(block)
        self.machine_limit_spin.blockSignals(block)
        self.machine_deny_list_check.blockSignals(block)
        self.machine_list_edit.blockSignals(block)
        self.limits_edit.blockSignals(block)
    
    def _setup_responsive_behavior(self):
        """Set up responsive resize handling."""
        # Override the resize event for responsive behavior
        original_resize = self.resizeEvent
        def responsive_resize_event(event):
            self._handle_responsive_resize(event)
            if original_resize:
                original_resize(event)
        self.resizeEvent = responsive_resize_event
    
    def _handle_responsive_resize(self, event):
        """Handle resize to make settings responsive."""
        panel_width = event.size().width()
        
        # Calculate if we have enough space for horizontal layout
        available_width = panel_width - 60  # Account for margins and group box padding
        
        if available_width < Sizes.RESPONSIVE_BREAKPOINT:  # Stack vertically when narrow
            if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                self.content_layout.setSpacing(20)  # More spacing when stacked vertically
        else:  # Side by side when wide enough
            if self.content_layout.direction() == QtWidgets.QBoxLayout.TopToBottom:
                self.content_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)
                self.content_layout.setSpacing(Sizes.SETTINGS_SPACING)  # Less spacing when side by side
    
    def _on_job_settings_changed(self):
        """Handle job settings changes from the model."""
        # Reload settings from model (in case they were changed externally)
        self._load_settings_from_model()
    
    def _on_machine_settings_changed(self):
        """Handle machine settings changes from the model."""
        # Reload settings from model (in case they were changed externally)
        self._load_settings_from_model()
    
    def get_settings_model(self):
        """Get the settings model.
        
        Returns:
            SettingsModel: The settings model instance
        """
        return self.settings_model


class NodeSettingsView(QtWidgets.QWidget):
    """View for the node settings table with controls.
    
    This view handles the UI for the node settings table (formerly render order),
    including the table widget, control buttons, filter functionality, and
    settings inheritance system.
    """
    
    def __init__(self, table_model, settings_model=None, parent=None):
        super().__init__(parent)
        self.table_model = table_model
        self.settings_model = settings_model
        
        # Connect settings model to table model for inheritance
        if self.settings_model:
            self.table_model.set_settings_model(self.settings_model)
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_data_from_model()
    
    def _create_ui(self):
        """Create the node settings UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Control buttons with filter
        self._create_control_buttons()
        layout.addLayout(self.button_layout)
        
        # Create the table
        self._create_table()
        layout.addWidget(self.render_table)
        
        # Set stretch factor to make table expand
        layout.setStretchFactor(self.render_table, 1)
    
    def _create_control_buttons(self):
        """Create the control buttons and filter."""
        self.button_layout = QtWidgets.QHBoxLayout()
        
        self.update_btn = QtWidgets.QPushButton("Update")
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.button_layout.addWidget(self.update_btn)
        
        self.all_btn = QtWidgets.QPushButton("All")
        self.all_btn.clicked.connect(self._on_all_clicked)
        self.button_layout.addWidget(self.all_btn)
        
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.button_layout.addWidget(self.clear_btn)
        
        self.selection_btn = QtWidgets.QPushButton("Selection")
        self.selection_btn.clicked.connect(self._on_selection_clicked)
        self.button_layout.addWidget(self.selection_btn)
        
        self.inside_groups_check = QtWidgets.QCheckBox("Inside groups")
        self.inside_groups_check.stateChanged.connect(self._on_inside_groups_changed)
        self.button_layout.addWidget(self.inside_groups_check)
        
        # Add spacer to push column dropdown and filter to the right
        self.button_layout.addStretch()
        
        # Column visibility dropdown
        from .widgets import ColumnVisibilityDropdown
        self.column_dropdown = ColumnVisibilityDropdown()
        self.column_dropdown.column_visibility_changed.connect(self._on_column_visibility_changed)
        self.button_layout.addWidget(self.column_dropdown)
        
        # Filter input on same row
        self.button_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("filter...")
        self.filter_edit.setMaximumWidth(Sizes.FILTER_EDIT_WIDTH)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        self.button_layout.addWidget(self.filter_edit)
    
    def _create_table(self):
        """Create the node settings table."""
        from .widgets import FrozenTableWidget
        from .delegates import SettingsAwareDelegate
        from .constants import TableColumns
        
        self.render_table = FrozenTableWidget()
        self.render_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Set up settings-aware delegate for inheritance and override styling
        self.settings_delegate = SettingsAwareDelegate(self.table_model)
        self.render_table.setItemDelegate(self.settings_delegate)
        
        # Set up table headers with display names
        headers = self.table_model.get_headers()
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(display_headers)
        
        # Connect table signals
        self.render_table.itemChanged.connect(self._on_table_item_changed)
        
        # Table properties are already set in FrozenTableWidget constructor
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.table_model.dataChanged.connect(self._on_model_data_changed)
        
        # Connect settings model change signals to refresh table
        if self.settings_model:
            self.settings_model.jobSettingsChanged.connect(self._on_settings_changed)
            self.settings_model.machineSettingsChanged.connect(self._on_settings_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the table widget."""
        # Block signals during loading to prevent unwanted updates
        self.render_table.blockSignals(True)
        
        try:
            # Get data from model
            data = self.table_model.get_data()
            headers = self.table_model.get_headers()
            
            # Set table size
            self.render_table.setRowCount(len(data))
            
            # Populate table with raw values, but display effective values
            for row, row_data in enumerate(data):
                for col, header in enumerate(headers):
                    # Get raw cell value (may be None for inheritance)
                    raw_value = self.table_model.get_cell_value(row, col)
                    
                    # Create item with raw value for data storage
                    if raw_value is None:
                        # For None values, store empty string but mark as inherited
                        item = QtWidgets.QTableWidgetItem("")
                        item.setData(QtCore.Qt.UserRole, None)  # Store None in user data
                    else:
                        # For explicit values, store the actual value
                        item = QtWidgets.QTableWidgetItem(str(raw_value))
                        item.setData(QtCore.Qt.UserRole, raw_value)
                    
                    # Set display text to effective value (for inheritance display)
                    effective_value = self.table_model.get_effective_cell_value(row, col)
                    item.setText(str(effective_value))
                    
                    # Apply styling based on whether cell is overridden
                    self._apply_cell_styling(item, row, col)
                    
                    self.render_table.setItem(row, col, item)
                    
                    # Sync to frozen table if this is a frozen column
                    self._sync_frozen_item(row, col, item)
            
            # Resize columns to content
            self.render_table.resizeColumnsToContents()
            
        finally:
            # Re-enable signals after loading is complete
            self.render_table.blockSignals(False)
    
    def _apply_cell_styling(self, item, row, col):
        """Apply styling to table cell items based on override status."""
        # Don't apply bold styling to frozen columns (Order, Node, Filename)
        # since they don't support inheritance and are always explicit
        if (hasattr(self.render_table, 'frozen_column_count') and 
            col < self.render_table.frozen_column_count):
            # Frozen columns use normal font and default text color
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            item.setForeground(QtGui.QBrush())
            return
        
        # Check if cell is overridden (has explicit value different from inherited)
        is_overridden = self.table_model.is_cell_overridden(row, col)
        
        if is_overridden:
            # Bold font for override values
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            # White text for explicit values
            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        else:
            # Normal font for inherited values
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            # Default text color for inherited values
            item.setForeground(QtGui.QBrush())
    
    def _sync_frozen_item(self, row, col, item):
        """Sync item to frozen table if it's in a frozen column."""
        # Check if this table has frozen columns and if column is frozen
        if (hasattr(self.render_table, 'frozen_table') and 
            hasattr(self.render_table, 'frozen_column_count') and
            col < self.render_table.frozen_column_count):
            
            # Create a copy of the item for the frozen table
            frozen_item = QtWidgets.QTableWidgetItem(item.text())
            frozen_item.setData(QtCore.Qt.UserRole, item.data(QtCore.Qt.UserRole))
            frozen_item.setFont(item.font())
            frozen_item.setForeground(item.foreground())
            frozen_item.setBackground(item.background())
            
            # Set the item in the frozen table
            self.render_table.frozen_table.setItem(row, col, frozen_item)
    
    def _on_table_item_changed(self, item):
        """Handle table item changes and update the model."""
        if not item:
            return
        
        # Block signals to prevent recursive calls
        self.render_table.blockSignals(True)
        
        try:
            row = item.row()
            col = item.column()
            text_value = item.text()
            
            # Determine the value to store in the model
            if text_value.strip() == "":
                # Empty string means user wants to inherit from settings
                model_value = None
            else:
                # Non-empty string is an explicit value
                model_value = text_value
            
            # Update the model with the appropriate value (suppress signal to prevent full reload)
            self.table_model.set_cell_value(row, col, model_value, emit_signal=False)
            
            # Update the item's user data to reflect the stored value
            item.setData(QtCore.Qt.UserRole, model_value)
            
            # Update display text to show effective value (may be inherited)
            effective_value = self.table_model.get_effective_cell_value(row, col)
            item.setText(str(effective_value))
            
            # Refresh styling for this cell only
            self._apply_cell_styling(item, row, col)
            
            # Sync to frozen table if this is a frozen column
            self._sync_frozen_item(row, col, item)
            
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
    
    def _on_model_data_changed(self):
        """Handle model data changes."""
        # Refresh the table display
        self._load_data_from_model()
    
    def _on_settings_changed(self):
        """Handle settings model changes - refresh table to show updated inherited values."""
        # Update only inherited cells instead of reloading entire table
        self._update_inherited_cells()
    
    def _update_inherited_cells(self):
        """Update only cells that inherit from settings."""
        # Block signals to prevent recursive updates
        self.render_table.blockSignals(True)
        
        try:
            for row in range(self.render_table.rowCount()):
                for col in range(self.render_table.columnCount()):
                    # Check if this cell is inherited (not overridden)
                    if not self.table_model.is_cell_overridden(row, col):
                        item = self.render_table.item(row, col)
                        if item:
                            # Update display text with new inherited value
                            effective_value = self.table_model.get_effective_cell_value(row, col)
                            item.setText(str(effective_value))
                            
                            # Refresh styling
                            self._apply_cell_styling(item, row, col)
                            
                            # Sync to frozen table if this is a frozen column
                            self._sync_frozen_item(row, col, item)
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
    
    def _on_filter_changed(self, text):
        """Handle filter text changes."""
        # TODO: Implement filtering logic
        # For now, just store the filter text
        self.current_filter = text.lower()
    
    def _on_inside_groups_changed(self, state):
        """Handle inside groups checkbox changes."""
        # TODO: Implement inside groups logic
        checked = state == QtCore.Qt.Checked
        print(f"Inside groups: {checked}")
    
    def _on_update_clicked(self):
        """Handle update button click."""
        if NUKE_AVAILABLE:
            nuke.message('Update functionality will be implemented in the final integration phase.')
        else:
            print("Update functionality will be implemented in the final integration phase.")
    
    def _on_all_clicked(self):
        """Handle all button click."""
        if NUKE_AVAILABLE:
            nuke.message('All functionality will be implemented in the final integration phase.')
        else:
            print("All functionality will be implemented in the final integration phase.")
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        # Clear all data
        self.table_model.set_data([])
    
    def _on_selection_clicked(self):
        """Handle selection button click."""
        if NUKE_AVAILABLE:
            nuke.message('Selection functionality will be implemented in the final integration phase.')
        else:
            print("Selection functionality will be implemented in the final integration phase.")
    
    def _on_column_visibility_changed(self):
        """Handle column visibility changes."""
        visible_columns = self.column_dropdown.get_visible_columns()
        
        # Update the table model
        self.table_model.set_visible_columns(visible_columns)
        
        # Hide/show columns in the table widget
        headers = self.table_model.get_headers()
        for i, header in enumerate(headers):
            column_visible = header in visible_columns
            self.render_table.setColumnHidden(i, not column_visible)
            
            # Also hide in frozen table if applicable
            if (hasattr(self.render_table, 'frozen_table') and 
                hasattr(self.render_table, 'frozen_column_count') and
                i < self.render_table.frozen_column_count):
                self.render_table.frozen_table.setColumnHidden(i, not column_visible)
    
    def get_table_model(self):
        """Get the table model.
        
        Returns:
            TableDataModel: The table model instance
        """
        return self.table_model
    
    def get_effective_values(self):
        """Get effective values from the table model.
        
        Returns:
            list: List of effective row values
        """
        return self.table_model.get_data()


class GSVView(QtWidgets.QWidget):
    """View for the GSV hierarchy tree with controls.
    
    This view handles the UI for the GSV tree, including primary/secondary GSV
    input fields, tree widget, and control buttons.
    """
    
    def __init__(self, gsv_model, parent=None):
        super().__init__(parent)
        self.gsv_model = gsv_model
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_data_from_model()
    
    def _create_ui(self):
        """Create the GSV UI components."""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # GSV input fields
        self._create_input_fields()
        layout.addLayout(self.input_layout)
        
        # Tree widget
        self._create_tree_widget()
        layout.addWidget(self.gsvs_tree)
        
        # Control buttons
        self._create_control_buttons()
        layout.addLayout(self.controls_layout)
    
    def _create_input_fields(self):
        """Create the GSV input fields."""
        self.input_layout = QtWidgets.QHBoxLayout()
        
        # Primary GSVs (tree hierarchy)
        self.input_layout.addWidget(QtWidgets.QLabel("Primary GSVs:"))
        self.primary_gsvs_field = QtWidgets.QLineEdit()
        self.primary_gsvs_field.setPlaceholderText("Sequence, Shotcode...")
        self.primary_gsvs_field.textChanged.connect(self._on_primary_gsv_text_changed)
        self.input_layout.addWidget(self.primary_gsvs_field)
        
        # Secondary GSVs (columns)
        self.input_layout.addWidget(QtWidgets.QLabel("Secondary GSVs:"))
        self.secondary_gsvs_field = QtWidgets.QLineEdit()
        self.secondary_gsvs_field.setPlaceholderText("Resolution, Format...")
        self.secondary_gsvs_field.textChanged.connect(self._on_secondary_gsv_text_changed)
        self.input_layout.addWidget(self.secondary_gsvs_field)
        
        # Refresh button
        refresh_hierarchy_btn = QtWidgets.QPushButton("Refresh Hierarchy")
        refresh_hierarchy_btn.clicked.connect(self._refresh_hierarchy)
        self.input_layout.addWidget(refresh_hierarchy_btn)
    
    def _create_tree_widget(self):
        """Create the GSV tree widget."""
        self.gsvs_tree = QtWidgets.QTreeWidget()
        self.gsvs_tree.setRootIsDecorated(True)
        self.gsvs_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.gsvs_tree.setAlternatingRowColors(True)
        self.gsvs_tree.itemChanged.connect(self._on_tree_item_changed)
        
        # Apply centered checkbox delegate
        from .delegates import CenteredCheckboxDelegate
        self.centered_delegate = CenteredCheckboxDelegate(self.gsvs_tree)
        self.gsvs_tree.setItemDelegate(self.centered_delegate)
        
        # Set up tree styling
        checkbox_style = """
            QTreeWidget::item {
                padding-top: 2px;
                padding-bottom: 2px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            QTreeWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QTreeWidget::item:selected:active {
                background-color: transparent;
            }
            QTreeWidget::item:selected:!active {
                background-color: transparent;
            }
        """
        self.gsvs_tree.setStyleSheet(checkbox_style)
    
    def _create_control_buttons(self):
        """Create the control buttons."""
        self.controls_layout = QtWidgets.QHBoxLayout()
        
        expand_all_btn = QtWidgets.QPushButton("Expand All")
        expand_all_btn.clicked.connect(self.gsvs_tree.expandAll)
        self.controls_layout.addWidget(expand_all_btn)
        
        collapse_all_btn = QtWidgets.QPushButton("Collapse All")
        collapse_all_btn.clicked.connect(self.gsvs_tree.collapseAll)
        self.controls_layout.addWidget(collapse_all_btn)
        
        self.controls_layout.addStretch()
        
        check_all_btn = QtWidgets.QPushButton("Check All")
        check_all_btn.clicked.connect(self._check_all_items)
        self.controls_layout.addWidget(check_all_btn)
        
        uncheck_all_btn = QtWidgets.QPushButton("Uncheck All")
        uncheck_all_btn.clicked.connect(self._uncheck_all_items)
        self.controls_layout.addWidget(uncheck_all_btn)
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.gsv_model.hierarchyChanged.connect(self._on_hierarchy_changed)
        self.gsv_model.selectionChanged.connect(self._on_selection_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the UI."""
        # Load text fields
        self.primary_gsvs_field.setText(self.gsv_model.get_primary_gsv_text())
        self.secondary_gsvs_field.setText(self.gsv_model.get_secondary_gsv_text())
        
        # Refresh the hierarchy
        self._refresh_hierarchy()
    
    def _refresh_hierarchy(self):
        """Refresh the GSV hierarchy tree."""
        # Store current header view to preserve it
        current_header = self.gsvs_tree.header() if hasattr(self.gsvs_tree, 'header') else None
        from .widgets import GroupedHeaderView
        is_grouped_header = isinstance(current_header, GroupedHeaderView)
        
        # Clear existing tree
        self.gsvs_tree.clear()
        
        # Get headers and groups from model
        headers = self.gsv_model.get_tree_headers()
        groups = self.gsv_model.get_tree_groups()
        
        if not headers:
            return
        
        # Set up tree headers
        self.gsvs_tree.setHeaderLabels(headers)
        self.gsvs_tree.setColumnCount(len(headers))
        
        # Apply grouped header view if we have secondary columns
        if len(headers) > 1:
            # Only create new header if we don't have one or it's not grouped
            if not is_grouped_header:
                grouped_header = GroupedHeaderView(QtCore.Qt.Horizontal, self.gsvs_tree)
                self.gsvs_tree.setHeader(grouped_header)
            else:
                grouped_header = current_header
            
            grouped_header.setGroups(groups)
        
        # Build the tree structure
        self._build_tree_from_model()
        
        # Expand first level by default
        self.gsvs_tree.expandToDepth(0)
        
        # Set up column properties
        self._setup_column_properties()
        
        # Force a repaint to ensure everything displays correctly
        self.gsvs_tree.update()
    
    def _build_tree_from_model(self):
        """Build the tree structure from the model data."""
        tree_items = self.gsv_model.build_tree_structure()
        self._add_tree_items(tree_items, None)
    
    def _add_tree_items(self, items, parent_widget_item):
        """Recursively add tree items to the widget.
        
        Args:
            items (list): List of item data dictionaries
            parent_widget_item (QTreeWidgetItem): Parent widget item (None for root)
        """
        for item_data in items:
            # Create tree item
            tree_item = QtWidgets.QTreeWidgetItem()
            tree_item.setText(0, item_data['text'])
            
            # Add checkbox to primary column (column 0)
            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            tree_item.setCheckState(0, QtCore.Qt.Unchecked)
            
            # Store metadata for primary column
            tree_item.setData(0, QtCore.Qt.UserRole, {
                'level': item_data['level'],
                'value': item_data['value'],
                'level_index': item_data['level_index'],
                'is_primary': True,
                'path': item_data['path']
            })
            
            # Add checkboxes for secondary GSVs
            headers = self.gsv_model.get_tree_headers()
            secondary_gsv_data = self.gsv_model.get_secondary_gsv_data()
            secondary_gsv_levels = self.gsv_model.get_secondary_gsv_levels()
            
            column_index = 1
            for secondary_gsv in secondary_gsv_levels:
                if secondary_gsv in secondary_gsv_data:
                    for value in secondary_gsv_data[secondary_gsv]:
                        if column_index < len(headers):
                            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                            tree_item.setCheckState(column_index, QtCore.Qt.Unchecked)
                            
                            # Store metadata for secondary columns
                            tree_item.setData(column_index, QtCore.Qt.UserRole, {
                                'secondary_gsv': secondary_gsv,
                                'secondary_value': value,
                                'is_primary': False,
                                'path': item_data['path']
                            })
                            column_index += 1
            
            # Add to parent or root
            if parent_widget_item:
                parent_widget_item.addChild(tree_item)
            else:
                self.gsvs_tree.addTopLevelItem(tree_item)
            
            # Recursively add children
            if item_data['children']:
                self._add_tree_items(item_data['children'], tree_item)
    
    def _setup_column_properties(self):
        """Set up column properties including width and alignment."""
        header = self.gsvs_tree.header()
        
        # Set a reasonable minimum section size for GSV columns
        # This is separate from the node settings table minimum
        header.setMinimumSectionSize(GSVDefaults.GSV_HEADER_MIN_SECTION_SIZE)
        
        # Set up each column
        for i in range(self.gsvs_tree.columnCount()):
            if i == 0:
                # Primary GSVs column
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Interactive)
                primary_width = self._calculate_primary_column_width()
                header.resizeSection(i, primary_width)
            else:
                # Secondary GSV columns
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
                secondary_width = self._calculate_secondary_column_width()
                header.resizeSection(i, secondary_width)
    
    def _calculate_primary_column_width(self):
        """Calculate the optimal width for the primary GSVs column."""
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        
        # Check the header text width
        header_text = "Primary GSVs"
        try:
            header_width = font_metrics.horizontalAdvance(header_text)
        except AttributeError:
            header_width = font_metrics.width(header_text)
        max_width = max(max_width, header_width)
        
        # Check all possible GSV values from the model data
        gsv_data = self.gsv_model.get_gsv_data()
        primary_levels = self.gsv_model.get_primary_gsv_levels()
        
        def check_data_width(data, level_index=0):
            nonlocal max_width
            if level_index >= len(primary_levels):
                return
            
            level_name = primary_levels[level_index]
            if level_name in data:
                level_data = data[level_name]
                if isinstance(level_data, dict):
                    for key in level_data.keys():
                        try:
                            text_width = font_metrics.horizontalAdvance(str(key))
                        except AttributeError:
                            text_width = font_metrics.width(str(key))
                        
                        # Add indentation using constant
                        indented_width = text_width + (level_index * GSVDefaults.PRIMARY_COLUMN_INDENTATION)
                        max_width = max(max_width, indented_width)
                        
                        # Recursively check children
                        check_data_width(level_data[key], level_index + 1)
        
        check_data_width(gsv_data)
        
        # Add padding using constant
        final_width = max_width + GSVDefaults.PRIMARY_COLUMN_PADDING
        
        # Ensure reasonable bounds using constants
        return max(GSVDefaults.PRIMARY_COLUMN_MIN_WIDTH, min(final_width, GSVDefaults.PRIMARY_COLUMN_MAX_WIDTH))
    
    def _calculate_secondary_column_width(self):
        """Calculate the optimal width for secondary GSV columns.
        
        This method finds the widest GSV value (not the grouped header names)
        across all secondary columns, adds minimal padding for the checkbox,
        and returns a uniform width that all secondary columns will use.
        """
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        longest_value = ""
        
        # Only check the actual GSV values (second row headers), not the grouped headers
        secondary_gsv_data = self.gsv_model.get_secondary_gsv_data()
        all_values = []
        for values in secondary_gsv_data.values():
            all_values.extend(values)
        
        # Find the longest GSV value (e.g., "Full", "Proxy", "EXR", "MOV", "DWAA")
        for value in all_values:
            value_str = str(value)
            try:
                value_width = font_metrics.horizontalAdvance(value_str)
            except AttributeError:
                value_width = font_metrics.width(value_str)
            
            if value_width > max_width:
                max_width = value_width
                longest_value = value_str
        
        # Calculate width based on content with padding from constants
        if max_width > 0:
            content_based_width = max_width + GSVDefaults.SECONDARY_COLUMN_PADDING
        else:
            # Fallback: use minimum width from constants
            content_based_width = GSVDefaults.SECONDARY_COLUMN_MIN_WIDTH
        
        # Ensure bounds using constants
        final_width = max(GSVDefaults.SECONDARY_COLUMN_MIN_WIDTH, min(content_based_width, GSVDefaults.SECONDARY_COLUMN_MAX_WIDTH))
        
        return final_width
    
    def _on_primary_gsv_text_changed(self, text):
        """Handle primary GSV text changes."""
        self.gsv_model.set_primary_gsv_text(text)
    
    def _on_secondary_gsv_text_changed(self, text):
        """Handle secondary GSV text changes."""
        self.gsv_model.set_secondary_gsv_text(text)
    
    def _on_hierarchy_changed(self):
        """Handle hierarchy changes from the model."""
        # Use a timer to avoid updating on every keystroke
        if hasattr(self, '_hierarchy_update_timer'):
            self._hierarchy_update_timer.stop()
        
        self._hierarchy_update_timer = QtCore.QTimer()
        self._hierarchy_update_timer.setSingleShot(True)
        self._hierarchy_update_timer.timeout.connect(self._refresh_hierarchy)
        self._hierarchy_update_timer.start(500)  # 500ms delay
    
    def _on_selection_changed(self):
        """Handle selection changes from the model."""
        # Update tree widget selection states
        self._update_tree_selection_from_model()
    
    def _on_tree_item_changed(self, item, column):
        """Handle tree item checkbox state changes."""
        if not item:
            return
        
        # Get item metadata
        item_data = item.data(column, QtCore.Qt.UserRole)
        if not item_data:
            return
        
        # Get the item path
        item_path = item_data.get('path', [])
        
        # Get the new check state
        check_state = item.checkState(column)
        checked = check_state == QtCore.Qt.Checked
        
        # Update the model
        self.gsv_model.set_item_selection(item_path, column, checked)
        
        # Handle parent/child updates
        self._update_parent_child_states(item, column, check_state)
    
    def _update_parent_child_states(self, item, column, check_state):
        """Update parent and child states based on item change."""
        # Block signals to prevent recursion
        self.gsvs_tree.blockSignals(True)
        
        try:
            # Update all children
            self._update_children_state(item, column, check_state)
            
            # Update parent state
            self._update_parent_state(item, column)
        finally:
            # Re-enable signals
            self.gsvs_tree.blockSignals(False)
    
    def _update_children_state(self, parent_item, column, check_state):
        """Update all children of an item."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(column, check_state)
            # Recursively update grandchildren
            self._update_children_state(child, column, check_state)
    
    def _update_parent_state(self, child_item, column):
        """Update parent state based on children."""
        parent = child_item.parent()
        if not parent:
            return
        
        # Count checked and unchecked children
        total_children = parent.childCount()
        checked_children = 0
        
        for i in range(total_children):
            child = parent.child(i)
            if child.checkState(column) == QtCore.Qt.Checked:
                checked_children += 1
        
        # Set parent state based on children
        if checked_children == 0:
            parent.setCheckState(column, QtCore.Qt.Unchecked)
        elif checked_children == total_children:
            parent.setCheckState(column, QtCore.Qt.Checked)
        else:
            parent.setCheckState(column, QtCore.Qt.PartiallyChecked)
        
        # Recursively update grandparent
        self._update_parent_state(parent, column)
    
    def _update_tree_selection_from_model(self):
        """Update tree widget selection states from the model."""
        # This would be implemented to sync model selection state to UI
        # For now, it's a placeholder
        pass
    
    def _check_all_items(self):
        """Check all items in all columns."""
        self.gsv_model.set_all_selections(True)
        self._set_all_tree_items_check_state(QtCore.Qt.Checked)
    
    def _uncheck_all_items(self):
        """Uncheck all items in all columns."""
        self.gsv_model.set_all_selections(False)
        self._set_all_tree_items_check_state(QtCore.Qt.Unchecked)
    
    def _set_all_tree_items_check_state(self, check_state):
        """Set check state for all items in all columns."""
        self.gsvs_tree.blockSignals(True)
        try:
            # Iterate through all top-level items
            for i in range(self.gsvs_tree.topLevelItemCount()):
                item = self.gsvs_tree.topLevelItem(i)
                self._set_item_and_children_check_state(item, check_state)
        finally:
            self.gsvs_tree.blockSignals(False)
    
    def _set_item_and_children_check_state(self, item, check_state):
        """Recursively set check state for an item and all its children."""
        # Set check state for all columns
        for column in range(self.gsvs_tree.columnCount()):
            item.setCheckState(column, check_state)
        
        # Recursively update children
        for i in range(item.childCount()):
            child = item.child(i)
            self._set_item_and_children_check_state(child, check_state)
    
    def get_gsv_model(self):
        """Get the GSV model.
        
        Returns:
            GSVHierarchyModel: The GSV model instance
        """
        return self.gsv_model
    
    def get_selected_gsvs(self):
        """Get the currently selected GSV values.
        
        Returns:
            dict: Dictionary with selected GSV data
        """
        return self.gsv_model.get_selected_gsvs()


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


class ConsoleView(QtWidgets.QWidget):
    """View for console output and logging.
    
    This view handles the UI for displaying console output, logs,
    and submission status information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create the main layout and UI components
        self._create_ui()
    
    def _create_ui(self):
        """Create the console UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet(
            "background-color: #2b2b2b; "
            "color: #ffffff; "
            "font-family: 'Courier New', monospace; "
            "font-size: 10pt;"
        )
        
        # Set initial content
        self._set_initial_content()
        
        layout.addWidget(self.console_output)
    
    def _set_initial_content(self):
        """Set initial console content."""
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        initial_text = f"""Ready for submission...
Latest submission: {current_time}

NK2DL Panel Status:
- Models: Initialized ✓
- Views: Loaded ✓
- Delegates: Active ✓
- Widgets: Ready ✓

Waiting for user input..."""
        
        self.console_output.setText(initial_text)
    
    def append_message(self, message, message_type="info"):
        """Append a message to the console.
        
        Args:
            message (str): Message to append
            message_type (str): Type of message ("info", "warning", "error", "success")
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message type
        color_map = {
            "info": "#ffffff",      # White
            "warning": "#ffaa00",   # Orange
            "error": "#ff4444",     # Red
            "success": "#44ff44"    # Green
        }
        
        color = color_map.get(message_type, "#ffffff")
        
        # Format the message with timestamp and color
        formatted_message = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        
        # Append to console
        self.console_output.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_console(self):
        """Clear the console output."""
        self.console_output.clear()
        self._set_initial_content()
    
    def log_info(self, message):
        """Log an info message.
        
        Args:
            message (str): Info message
        """
        self.append_message(message, "info")
    
    def log_warning(self, message):
        """Log a warning message.
        
        Args:
            message (str): Warning message
        """
        self.append_message(message, "warning")
    
    def log_error(self, message):
        """Log an error message.
        
        Args:
            message (str): Error message
        """
        self.append_message(message, "error")
    
    def log_success(self, message):
        """Log a success message.
        
        Args:
            message (str): Success message
        """
        self.append_message(message, "success")
    
    def get_console_text(self):
        """Get the current console text.
        
        Returns:
            str: Current console content
        """
        return self.console_output.toPlainText()
    
    def set_console_text(self, text):
        """Set the console text.
        
        Args:
            text (str): Text to set
        """
        self.console_output.setPlainText(text) 