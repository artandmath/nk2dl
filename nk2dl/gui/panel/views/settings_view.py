# -*- coding: utf-8 -*-
"""Settings view component for the nk2dl panel.

This module contains the SettingsView class which handles UI for job and machine settings
with responsive layout functionality.
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
from ..constants import Settings, Sizes
from ..config import apply_panel_config


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
        self.pool_combo.addItems(Settings.get_pool_options())
        self.pool_combo.setFixedWidth(Sizes.COMBO_WIDTH)
        self.pool_combo.setToolTip("The pool that your job will be submitted to.")
        pool_group_row.addWidget(self.pool_combo)
        
        secondary_pool_label = QtWidgets.QLabel("Secondary Pool")
        secondary_pool_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(secondary_pool_label)
        
        self.secondary_pool_combo = QtWidgets.QComboBox()
        self.secondary_pool_combo.addItems([""] + Settings.get_pool_options())
        self.secondary_pool_combo.setFixedWidth(Sizes.COMBO_WIDTH)
        self.secondary_pool_combo.setToolTip("The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.")
        pool_group_row.addWidget(self.secondary_pool_combo)
        
        group_label = QtWidgets.QLabel("Group")
        group_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(group_label)
        
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(Settings.get_group_options())
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
        self.use_node_frame_list_check.toggled.connect(lambda c: self.settings_model.set_job_setting('use_node_frame_list', c))
        self.task_timeout_spin.valueChanged.connect(lambda v: self.settings_model.set_job_setting('task_timeout', v))
        self.enable_auto_timeout_check.toggled.connect(lambda c: self.settings_model.set_job_setting('enable_auto_timeout', c))
        self.render_mode_combo.currentTextChanged.connect(lambda t: self.settings_model.set_job_setting('render_mode', t))
        self.render_nukex_check.toggled.connect(lambda c: self.settings_model.set_job_setting('use_nuke_x', c))
        self.use_batch_mode_check.toggled.connect(lambda c: self.settings_model.set_job_setting('batch_mode', c))
        self.reload_plugin_check.toggled.connect(lambda c: self.settings_model.set_job_setting('reload_plugins', c))
        self.separate_tasks_check.toggled.connect(lambda c: self.settings_model.set_job_setting('separate_tasks', c))
        self.separate_jobs_check.toggled.connect(lambda c: self.settings_model.set_job_setting('separate_jobs', c))
        self.views_separate_jobs_check.toggled.connect(lambda c: self.settings_model.set_job_setting('views_separate_jobs', c))
        
        # Machine Settings signals
        self.pool_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('pool', t))
        self.secondary_pool_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('secondary_pool', t))
        self.group_combo.currentTextChanged.connect(lambda t: self.settings_model.set_machine_setting('group', t))
        self.threads_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('threads', v))
        self.min_ram_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('stack_size', v))
        self.max_ram_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('ram_use', v))
        self.gpu_override_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('gpu_override', v))
        self.use_gpu_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('use_gpu', c))
        self.concurrent_tasks_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('concurrent_tasks', v))
        self.limit_tasks_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('limit_worker_tasks', c))
        self.machine_limit_spin.valueChanged.connect(lambda v: self.settings_model.set_machine_setting('machine_limit', v))
        self.machine_deny_list_check.toggled.connect(lambda c: self.settings_model.set_machine_setting('machine_deny_list', c))
        self.machine_list_edit.textChanged.connect(lambda t: self.settings_model.set_machine_setting('machine_list', t))
        self.limits_edit.textChanged.connect(lambda t: self.settings_model.set_machine_setting('limit_groups', t))
        
        # Model change signals
        self.settings_model.jobSettingsChanged.connect(self._on_job_settings_changed)
        self.settings_model.machineSettingsChanged.connect(self._on_machine_settings_changed)
    
    def _load_settings_from_model(self):
        """Load current settings from the model into the UI."""
        # Block signals to prevent feedback loops
        self._block_signals(True)
        
        try:
            # Load job settings (convert to int for spinboxes)
            job_settings = self.settings_model.get_all_job_settings()
            self.priority_spin.setValue(int(job_settings.get('priority', 50)))
            self.chunk_size_spin.setValue(int(job_settings.get('chunk_size', 1)))
            
            frames_mode = job_settings.get('frames_mode', 'Global')
            index = self.frames_combo.findText(frames_mode)
            if index >= 0:
                self.frames_combo.setCurrentIndex(index)
            
            self.frame_range_edit.setText(job_settings.get('frames', ''))
            self.use_node_frame_list_check.setChecked(job_settings.get('use_node_frame_list', False))
            self.task_timeout_spin.setValue(int(job_settings.get('task_timeout', 0)))
            self.enable_auto_timeout_check.setChecked(job_settings.get('enable_auto_timeout', False))
            
            render_mode = job_settings.get('render_mode', 'Full')
            index = self.render_mode_combo.findText(render_mode)
            if index >= 0:
                self.render_mode_combo.setCurrentIndex(index)
            
            self.render_nukex_check.setChecked(job_settings.get('use_nuke_x', False))
            self.use_batch_mode_check.setChecked(job_settings.get('batch_mode', False))
            self.reload_plugin_check.setChecked(job_settings.get('reload_plugins', False))
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
            
            # Convert to int for spinboxes (config values might be strings)
            self.threads_spin.setValue(int(machine_settings.get('threads', 4)))
            self.min_ram_spin.setValue(int(machine_settings.get('stack_size', 0)))
            self.max_ram_spin.setValue(int(machine_settings.get('ram_use', 0)))
            
            # Handle gpu_override which can be empty string
            gpu_override = machine_settings.get('gpu_override', 0)
            if gpu_override == '' or gpu_override is None:
                gpu_override = 0
            self.gpu_override_spin.setValue(int(gpu_override))
            
            self.use_gpu_check.setChecked(machine_settings.get('use_gpu', False))
            self.concurrent_tasks_spin.setValue(int(machine_settings.get('concurrent_tasks', 2)))
            self.limit_tasks_check.setChecked(machine_settings.get('limit_worker_tasks', False))
            self.machine_limit_spin.setValue(int(machine_settings.get('machine_limit', 0)))
            self.machine_deny_list_check.setChecked(machine_settings.get('machine_deny_list', False))
            self.machine_list_edit.setText(str(machine_settings.get('machine_list', '')))
            self.limits_edit.setText(str(machine_settings.get('limit_groups', '')))
            
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
    
    def _apply_configuration(self):
        """Apply panel configuration to job and machine settings controls."""
        # Add debug logging - move outside try block for error handling
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.settings_view')
        
        try:
            logger.debug("Starting _apply_configuration for SettingsView")
            
            # Set object names for all controls first - MUST match control names passed to apply_panel_config
            # Job settings controls
            self.priority_spin.setObjectName("priority")
            self.chunk_size_spin.setObjectName("chunk_size")
            self.frames_combo.setObjectName("frames")
            self.frame_range_edit.setObjectName("frame_range")
            self.use_node_frame_list_check.setObjectName("use_node_frame_list")
            self.task_timeout_spin.setObjectName("task_timeout")
            self.enable_auto_timeout_check.setObjectName("enable_auto_timeout")
            self.render_mode_combo.setObjectName("render_mode")
            self.render_nukex_check.setObjectName("render_nukex")
            self.use_batch_mode_check.setObjectName("use_batch_mode")
            self.reload_plugin_check.setObjectName("reload_plugin")
            self.separate_tasks_check.setObjectName("separate_tasks")
            self.separate_jobs_check.setObjectName("separate_jobs")
            self.views_separate_jobs_check.setObjectName("views_separate_jobs")
            
            # Machine settings controls
            self.pool_combo.setObjectName("pool")
            self.secondary_pool_combo.setObjectName("secondary_pool")
            self.group_combo.setObjectName("group")
            self.threads_spin.setObjectName("threads")
            self.min_ram_spin.setObjectName("min_ram")
            self.max_ram_spin.setObjectName("max_ram")
            self.gpu_override_spin.setObjectName("gpu_override")
            self.use_gpu_check.setObjectName("use_gpu")
            self.concurrent_tasks_spin.setObjectName("concurrent_tasks")
            self.limit_tasks_check.setObjectName("limit_tasks")
            self.machine_limit_spin.setObjectName("machine_limit")
            self.machine_deny_list_check.setObjectName("machine_deny_list")
            self.machine_list_edit.setObjectName("machine_list")
            self.limits_edit.setObjectName("limits")
            
            # Apply configuration to job settings controls
            apply_panel_config(self.priority_spin, "priority")
            apply_panel_config(self.chunk_size_spin, "chunk_size")
            apply_panel_config(self.frames_combo, "frames")
            apply_panel_config(self.frame_range_edit, "frame_range")
            apply_panel_config(self.use_node_frame_list_check, "use_node_frame_list")
            apply_panel_config(self.task_timeout_spin, "task_timeout")
            apply_panel_config(self.enable_auto_timeout_check, "enable_auto_timeout")
            apply_panel_config(self.render_mode_combo, "render_mode")
            apply_panel_config(self.render_nukex_check, "render_nukex")
            apply_panel_config(self.use_batch_mode_check, "use_batch_mode")
            apply_panel_config(self.reload_plugin_check, "reload_plugin")
            apply_panel_config(self.separate_tasks_check, "separate_tasks")
            apply_panel_config(self.separate_jobs_check, "separate_jobs")
            apply_panel_config(self.views_separate_jobs_check, "views_separate_jobs")
            
            # Apply configuration to machine settings controls
            apply_panel_config(self.pool_combo, "pool")
            apply_panel_config(self.secondary_pool_combo, "secondary_pool")
            apply_panel_config(self.group_combo, "group")
            apply_panel_config(self.threads_spin, "threads")
            apply_panel_config(self.min_ram_spin, "min_ram")
            apply_panel_config(self.max_ram_spin, "max_ram")
            apply_panel_config(self.gpu_override_spin, "gpu_override")
            apply_panel_config(self.use_gpu_check, "use_gpu")
            apply_panel_config(self.concurrent_tasks_spin, "concurrent_tasks")
            apply_panel_config(self.limit_tasks_check, "limit_tasks")
            apply_panel_config(self.machine_limit_spin, "machine_limit")
            apply_panel_config(self.machine_deny_list_check, "machine_deny_list")
            apply_panel_config(self.machine_list_edit, "machine_list")
            apply_panel_config(self.limits_edit, "limits")
            
        except Exception as e:
            logger.error(f"Error applying configuration to SettingsView: {e}")
    
    def refresh_pool_dropdowns(self):
        """Refresh pool dropdown contents with updated options from Deadline."""
        try:
            # Store current selections
            current_pool = self.pool_combo.currentText()
            current_secondary = self.secondary_pool_combo.currentText()
            
            # Get updated pool options
            pool_options = Settings.get_pool_options()
            
            # Update primary pool dropdown
            self.pool_combo.clear()
            self.pool_combo.addItems(pool_options)
            
            # Update secondary pool dropdown (includes empty option)
            self.secondary_pool_combo.clear()
            self.secondary_pool_combo.addItems([""] + pool_options)
            
            # Restore selections if they still exist
            if current_pool in pool_options:
                self.pool_combo.setCurrentText(current_pool)
            
            if current_secondary in ([""] + pool_options):
                self.secondary_pool_combo.setCurrentText(current_secondary)
            
            logger.info(f"Pool dropdowns refreshed with {len(pool_options)} options")
            
        except Exception as e:
            logger.error(f"Error refreshing pool dropdowns: {e}", exc_info=True)
    
    def refresh_group_dropdown(self):
        """Refresh group dropdown contents with updated options from Deadline."""
        try:
            # Store current selection
            current_group = self.group_combo.currentText()
            
            # Get updated group options
            group_options = Settings.get_group_options()
            
            # Update group dropdown
            self.group_combo.clear()
            self.group_combo.addItems(group_options)
            
            # Restore selection if it still exists
            if current_group in group_options:
                self.group_combo.setCurrentText(current_group)
            
            logger.info(f"Group dropdown refreshed with {len(group_options)} options")
            
        except Exception as e:
            logger.error(f"Error refreshing group dropdown: {e}", exc_info=True)
    
    def refresh_all_dropdowns(self):
        """Refresh all pool and group dropdowns with updated options."""
        self.refresh_pool_dropdowns()
        self.refresh_group_dropdown() 