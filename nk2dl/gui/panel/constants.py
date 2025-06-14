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
    # Placeholder for actual gr options, which will be populated from Deadline
    GROUP_OPTIONS = ["none", "high_priority", "overnight", "weekend"]


class Sizes:
    """Size and dimension constants for UI components."""
    
    # Settings panel dimensions
    SETTINGS_LABEL_WIDTH = 90
    SETTINGS_SPACING = 20
    SETTINGS_MARGIN = 15
    SETTINGS_BOTTOM_MARGIN = 20
    
    # Control dimensions
    SPINBOX_WIDTH = 60
    COMBO_WIDTH = 100
    BUTTON_WIDTH = 80
    LINE_EDIT_MIN_WIDTH = 120
    FILTER_EDIT_WIDTH = 150
    
    # Responsive behavior
    RESPONSIVE_BREAKPOINT = 800  # Width below which settings stack vertically


class Colors:
    """Color constants for UI styling."""
    
    # Group box colors
    JOB_SETTINGS_COLOR = "#4A90E2"      # Blue
    MACHINE_SETTINGS_COLOR = "#8E44AD"   # Purple
    
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


class TableColumns:
    """Table column definitions and properties."""
    
    # Standard table headers
    HEADERS = [
        "Order", "Node", "Filename", "Chunk", "Frames", "Priority", 
        "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", 
        "NukeX", "BatchMode", "Reloadplugin"
    ]
    
    # Dropdown columns (columns that have dropdown editors)
    DROPDOWN_COLUMNS = {
        6: ["Yes", "No"],                    # NodesFrames
        8: ["Yes", "No"],                    # AutoTimeout  
        9: ["Full", "Proxy", "Both", "Script"],  # RenderMode
        10: ["Yes", "No"],                   # NukeX
        11: ["Yes", "No"],                   # BatchMode
        12: ["Yes", "No"]                    # Reloadplugin
    }
    
    # Column widths (optional, for initial sizing)
    COLUMN_WIDTHS = {
        0: 60,   # Order
        1: 100,  # Node
        2: 200,  # Filename
        3: 60,   # Chunk
        4: 120,  # Frames
        5: 70,   # Priority
        6: 90,   # NodesFrames
        7: 90,   # TaskTimeout
        8: 90,   # AutoTimeout
        9: 90,   # RenderMode
        10: 70,  # NukeX
        11: 90,  # BatchMode
        12: 100  # Reloadplugin
    }


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
        "frame_range": "1001-2315",
        "use_node_frame_list": False,
        "task_timeout": 0,
        "enable_auto_timeout": False,
        "render_mode": "Full",
        "use_nukex": False,
        "use_batch_mode": False,
        "reload_plugin": False,
        "separate_tasks": False,
        "separate_jobs": False,
        "views_separate_jobs": False
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