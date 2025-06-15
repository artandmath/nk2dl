# -*- coding: utf-8 -*-
"""Constants for the nk2dl panel components.

This module contains all constants used by the panel widgets, views, models, and delegates.
Moved from nk2dl/gui/constants.py to be part of the panel module.
"""


class Settings:
    """Settings-related constants."""
    
    # Frame options for the frames dropdown
    FRAMES_OPTIONS = ["Global", "Input", "Custom"]
    
    # Pool options for machine settings
    # Placeholder for actual pool options, which will be populated from Deadline
    POOL_OPTIONS = ["comp", "lighting", "fx", "render", "general"]
    
    # Group options for machine settings
    # Placeholder for actual group options, which will be populated from Deadline
    GROUP_OPTIONS = ["none", "high_priority", "overnight", "weekend"]


class Sizes:
    """Size and dimension constants for UI components."""
    
    # Settings panel dimensions
    SETTINGS_LABEL_WIDTH = 110
    SETTINGS_SPACING = 20
    SETTINGS_MARGIN = 15
    SETTINGS_BOTTOM_MARGIN = 20
    
    # Group box minimum widths
    JOB_SETTINGS_MIN_WIDTH = 650  # Minimum width for job settings box
    MACHINE_SETTINGS_MIN_WIDTH = 650  # Minimum width for machine settings box
    
    # Control dimensions
    SPINBOX_WIDTH = 60
    COMBO_WIDTH = 100
    BUTTON_WIDTH = 80
    LINE_EDIT_MIN_WIDTH = 120
    FILTER_EDIT_WIDTH = 150
    
    # Responsive behavior
    RESPONSIVE_BREAKPOINT = 1250  # Width below which settings stack vertically


class Colors:
    """Color constants for UI styling."""
    
    # Group box colors
    JOB_SETTINGS_COLOR = "#4A90E2"      # Blue
    MACHINE_SETTINGS_COLOR = "#8E44AD"   # Purple
    
    # Settings panel background colors (for group box titles)
    JOB_SETTINGS_BACKGROUND = "#2A2633"      # Dark grey with blue tint
    MACHINE_SETTINGS_BACKGROUND = "#332633"  # Dark grey with purple tint
    
    # Text colors
    INHERITED_TEXT_COLOR = "#888888"     # Grey for inherited values
    EXPLICIT_TEXT_COLOR = "#FFFFFF"      # White for explicit values
    
    # Console colors
    CONSOLE_BACKGROUND = "#2b2b2b"       # Dark background
    CONSOLE_TEXT = "#ffffff"             # White text
    CONSOLE_INFO = "#ffffff"             # White for info
    CONSOLE_WARNING = "#ffaa00"          # Orange for warnings
    CONSOLE_ERROR = "#ff4444"            # Red for errors
    CONSOLE_SUCCESS = "#44ff44"          # Green for success
    
    # Pinned row styling (using same colors as settings panels)
    PINNED_JOB_BACKGROUND = JOB_SETTINGS_BACKGROUND      # Same as job settings title
    PINNED_JOB_BORDER = JOB_SETTINGS_COLOR               # Same as job settings border
    PINNED_MACHINE_BACKGROUND = MACHINE_SETTINGS_BACKGROUND  # Same as machine settings title
    PINNED_MACHINE_BORDER = MACHINE_SETTINGS_COLOR       # Same as machine settings border


class TableColumns:
    """Table column definitions and properties."""
    
    # Standard table headers (reordered to put Priority before ChunkSize)
    HEADERS = [
        "Order", "Node", "Filename", "Priority", "ChunkSize", "Frames", 
        "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", 
        "NukeX", "BatchMode", "ReloadPlugin", "Pool", "SecondaryPool", 
        "Group", "Threads", "MinRam", "MaxRam", "UseGPU", "GPUId", 
        "ConcurrentTasks", "WorkerTaskLimit", "MachineList", "Limits"
    ]
    
    # Display names for headers (more readable versions)
    HEADER_DISPLAY_NAMES = {
        "Order": "Order",
        "Node": "Node", 
        "Filename": "Filename",
        "Priority": "Priority",
        "ChunkSize": "Chunk Size",
        "Frames": "Frames",
        "NodesFrames": "Nodes Frames",
        "TaskTimeout": "Task Timeout",
        "AutoTimeout": "Auto Timeout",
        "RenderMode": "Render Mode",
        "NukeX": "Nuke X",
        "BatchMode": "Batch Mode",
        "ReloadPlugin": "Reload Plugin",
        "Pool": "Pool",
        "SecondaryPool": "Secondary Pool",
        "Group": "Group",
        "Threads": "Threads",
        "MinRam": "Min RAM",
        "MaxRam": "Max RAM",
        "UseGPU": "Use GPU",
        "GPUId": "GPU ID",
        "ConcurrentTasks": "Concurrent Tasks",
        "WorkerTaskLimit": "Worker Task Limit",
        "MachineList": "Machine List",
        "Limits": "Limits"
    }
    
    # Column groups for visibility dropdown
    COLUMN_GROUPS = {
        "Fixed": ["Order", "Node", "Filename"],  # Always visible, cannot be hidden
        "Job Settings": [
            "Priority", "ChunkSize", "Frames", "NodesFrames", 
            "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", 
            "BatchMode", "ReloadPlugin"
        ],
        "Machine Settings": [
            "Pool", "SecondaryPool", "Group", "Threads", 
            "MinRam", "MaxRam", "UseGPU", "GPUId", 
            "ConcurrentTasks", "WorkerTaskLimit", "MachineList", "Limits"
        ]
    }
    
    # Dropdown columns (columns that have dropdown editors) - updated indices for reordered headers
    DROPDOWN_COLUMNS = {
        6: ["Yes", "No"],                    # NodesFrames
        8: ["Yes", "No"],                    # AutoTimeout  
        9: ["Full", "Proxy", "Both", "Script"],  # RenderMode
        10: ["Yes", "No"],                   # NukeX
        11: ["Yes", "No"],                   # BatchMode
        12: ["Yes", "No"],                   # ReloadPlugin
        13: Settings.POOL_OPTIONS,           # Pool
        14: Settings.POOL_OPTIONS,           # SecondaryPool
        15: Settings.GROUP_OPTIONS,          # Group
        19: ["Yes", "No"],                   # UseGPU
        22: ["Yes", "No"]                    # WorkerTaskLimit
    }
    
    # Column widths (optional, for initial sizing) - updated indices for reordered headers
    COLUMN_WIDTHS = {
        0: 60,   # Order
        1: 100,  # Node
        2: 200,  # Filename
        3: 70,   # Priority (moved to position 3)
        4: 80,   # ChunkSize (moved to position 4)
        5: 120,  # Frames
        6: 90,   # NodesFrames
        7: 90,   # TaskTimeout
        8: 90,   # AutoTimeout
        9: 90,   # RenderMode
        10: 70,  # NukeX
        11: 90,  # BatchMode
        12: 100, # ReloadPlugin
        13: 80,  # Pool
        14: 100, # SecondaryPool
        15: 80,  # Group
        16: 70,  # Threads
        17: 70,  # MinRam
        18: 70,  # MaxRam
        19: 70,  # UseGPU
        20: 70,  # GPUId
        21: 100, # ConcurrentTasks
        22: 110, # WorkerTaskLimit
        23: 120, # MachineList
        24: 80   # Limits
    }
    
    # Machine settings columns (for styling pinned rows) - updated indices
    MACHINE_SETTINGS_COLUMNS = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]


class GSVDefaults:
    """Default values and constants for GSV functionality."""
    
    # Default GSV text values
    DEFAULT_PRIMARY_GSVS = "Sequence, Shotcode"
    DEFAULT_SECONDARY_GSVS = "Resolution, Format"
    
    # Sample GSV data for demonstration
    SAMPLE_PRIMARY_DATA = {
        "Sequence": ["seq010", "seq020", "seq030"],
        "Shotcode": ["sh010", "sh020", "sh030", "sh040"]
    }
    
    SAMPLE_SECONDARY_DATA = {
        "Resolution": ["1920x1080", "2048x1556", "4096x3112"],
        "Format": ["exr", "dpx", "jpg"]
    }
    
    # Sample machine settings data for testing pinned rows
    SAMPLE_MACHINE_DATA = {
        "pool": "comp",
        "secondary_pool": "lighting", 
        "group": "high_priority",
        "threads": 8,
        "min_ram": 8,
        "max_ram": 32,
        "use_gpu": True,
        "gpu_id": 1,
        "concurrent_tasks": 4,
        "worker_task_limit": True,
        "machine_list": "render01,render02,render03",
        "limits": "nuke_license:4"
    }


class ValidationRules:
    """Validation rules and constraints."""
    
    # Job settings validation
    MIN_PRIORITY = 0
    MAX_PRIORITY = 100
    MIN_CHUNK_SIZE = 1
    MAX_CHUNK_SIZE = 1000
    MIN_TASK_TIMEOUT = 0
    MAX_TASK_TIMEOUT = 999
    
    # Machine settings validation
    MIN_THREADS = 1
    MAX_THREADS = 64
    MIN_RAM = 0
    MAX_RAM_MIN = 64
    MAX_RAM_MAX = 512
    MIN_GPU_DEVICE = 0
    MAX_GPU_DEVICE = 16
    MIN_CONCURRENT_TASKS = 1
    MAX_CONCURRENT_TASKS = 64
    MIN_MACHINE_LIMIT = 0
    MAX_MACHINE_LIMIT = 999
    
    # Required fields
    REQUIRED_JOB_FIELDS = ["priority", "chunk_size"]
    REQUIRED_MACHINE_FIELDS = ["threads", "concurrent_tasks"]


class DefaultValues:
    """Default values for settings and controls."""
    
    # Job settings defaults
    JOB_DEFAULTS = {
        "priority": 50,
        "chunk_size": 1,
        "frames_mode": "Global",
        "frames": "1001-2315",
        "nodes_frames": False,
        "task_timeout": 0,
        "auto_timeout": False,
        "render_mode": "Full",
        "use_nukex": False,
        "use_batch_mode": False,
        "reload_plugin": False,
        "separate_tasks": False,
        "separate_jobs": False,
        "views_separate_jobs": False,
        # Machine settings defaults for node table
        "pool": "comp",
        "secondary_pool": "",
        "group": "none",
        "threads": 4,
        "min_ram": 0,
        "max_ram": 0,
        "use_gpu": False,
        "gpu_id": 0,
        "concurrent_tasks": 2,
        "worker_task_limit": False,
        "machine_list": "",
        "limits": ""
    }
    
    # Machine settings defaults
    MACHINE_DEFAULTS = {
        "pool": "comp",
        "secondary_pool": "",
        "group": "none",
        "threads": 4,
        "min_ram": 0,
        "max_ram": 0,
        "gpu_device": 0,
        "use_gpu": False,
        "concurrent_tasks": 2,
        "limit_tasks": False,
        "machine_limit": 0,
        "machine_deny_list": False,
        "machine_list": "",
        "limits": ""
    }
    
    # Extra settings defaults
    EXTRA_DEFAULTS = {
        "job_name": "",
        "comment": "",
        "department": ""
    }


class StyleSheets:
    """CSS style sheets for UI components."""
    
    # Console styling
    CONSOLE_STYLE = """
        QTextEdit {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            border: 1px solid #555555;
        }
    """
    
    # Render button styling
    RENDER_BUTTON_STYLE = """
        QPushButton {
            background-color: #4a90e2;
            color: white;
            font-weight: bold;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #357abd;
        }
        QPushButton:pressed {
            background-color: #2968a3;
        }
    """
    
    # Version label styling
    VERSION_LABEL_STYLE = """
        QLabel {
            color: #888888;
            font-size: 10px;
        }
    """
    
    # Tree widget checkbox styling
    TREE_CHECKBOX_STYLE = """
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


class HeaderSettingsMapping:
    """Mapping between table column headers and job/machine settings.
    
    This class defines the relationships between table columns and settings panel
    fields, enabling inheritance where empty table cells inherit values from
    the corresponding settings, and explicit cell values override the settings.
    """
    
    # Job Settings Relationships
    # Maps table column headers to job settings field names
    JOB_SETTINGS_MAPPING = {
        "Priority": "priority",
        "ChunkSize": "chunk_size", 
        "Frames": "frames",  # Map Frames column to frames job setting
        "NodesFrames": "nodes_frames",
        "TaskTimeout": "task_timeout",
        "AutoTimeout": "auto_timeout",
        "RenderMode": "render_mode",
        "NukeX": "use_nukex",
        "BatchMode": "use_batch_mode",
        "ReloadPlugin": "reload_plugin"
    }
    
    # Machine Settings Relationships  
    # Maps table column headers to machine settings field names
    MACHINE_SETTINGS_MAPPING = {
        "Pool": "pool",
        "SecondaryPool": "secondary_pool",
        "Group": "group",
        "Threads": "threads",
        "MinRam": "min_ram",
        "MaxRam": "max_ram",
        "UseGPU": "use_gpu",
        "GPUId": "gpu_id",
        "ConcurrentTasks": "concurrent_tasks",
        "WorkerTaskLimit": "worker_task_limit",
        "MachineList": "machine_list",
        "Limits": "limits"
    }
    
    # Combined mapping for easy lookup
    ALL_MAPPINGS = {**JOB_SETTINGS_MAPPING, **MACHINE_SETTINGS_MAPPING}
    
    # Dropdown inheritance labels
    JOB_SETTINGS_INHERITANCE_LABEL = "Use job settings"
    MACHINE_SETTINGS_INHERITANCE_LABEL = "Use machine settings"
    DROPDOWN_SEPARATOR = "-----"
    
    # Boolean columns that should display as Yes/No
    BOOLEAN_COLUMNS = [
        "NodesFrames", "AutoTimeout", "NukeX", "BatchMode", 
        "ReloadPlugin", "UseGPU", "WorkerTaskLimit"
    ]
    
    # Numeric columns that should display as strings
    NUMERIC_COLUMNS = [
        "Priority", "ChunkSize", "TaskTimeout", "Threads", 
        "MinRam", "MaxRam", "GPUId", "ConcurrentTasks"
    ]
    
    # String columns that display directly
    STRING_COLUMNS = [
        "Frames", "Pool", "SecondaryPool", "Group", "RenderMode", 
        "MachineList", "Limits"
    ]
    
    @classmethod
    def get_setting_type_and_key(cls, column_header):
        """Get the setting type and key for a column header.
        
        Args:
            column_header (str): The table column header name
            
        Returns:
            tuple: (setting_type, setting_key) where setting_type is 
                   "job", "machine", or None, and setting_key is the 
                   corresponding field name in the settings model
        """
        if column_header in cls.JOB_SETTINGS_MAPPING:
            return "job", cls.JOB_SETTINGS_MAPPING[column_header]
        elif column_header in cls.MACHINE_SETTINGS_MAPPING:
            return "machine", cls.MACHINE_SETTINGS_MAPPING[column_header]
        else:
            return None, None
    
    @classmethod
    def is_mapped_column(cls, column_header):
        """Check if a column header has a settings mapping.
        
        Args:
            column_header (str): The table column header name
            
        Returns:
            bool: True if the column has a settings mapping
        """
        return column_header in cls.ALL_MAPPINGS
    
    @classmethod
    def get_inheritance_label(cls, column_header):
        """Get the inheritance label for a column header.
        
        Args:
            column_header (str): The table column header name
            
        Returns:
            str: The inheritance label to show in dropdown menus
        """
        setting_type, _ = cls.get_setting_type_and_key(column_header)
        if setting_type == "job":
            return cls.JOB_SETTINGS_INHERITANCE_LABEL
        elif setting_type == "machine":
            return cls.MACHINE_SETTINGS_INHERITANCE_LABEL
        else:
            return None 