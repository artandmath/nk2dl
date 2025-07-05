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


class Storage:
    """Storage-related constants for node settings persistence."""
    
    # Storage knob names on root node
    TAB_KNOB_NAME = "nk2dl"
    SETTINGS_KNOB_NAME = "nk2dl_settings"
    
    # Display names for storage knobs
    SETTINGS_KNOB_DISPLAY_NAME = "Nk2dl Settings"


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
    
    # Header dimensions
    HEADER_TEXT_PADDING = 6  # Horizontal padding for header text (3px each side)
    HEADER_DEFAULT_SECTION_SIZE = 80  # Default column width to reduce initial flashing (will be overridden by calculations)
    
    # Checkbox column dimensions
    CHECKBOX_COLUMN_PADDING = 5  # 5 pixels padding each side of checkbox
    
    # Row dimensions
    TABLE_ROW_HEIGHT = 24  # Static height for all table rows
    
    # Responsive behavior
    RESPONSIVE_BREAKPOINT = 1250  # Width below which settings stack vertically
    
    # Progress bar dimensions
    PROGRESS_BAR_WIDTH = 200  # Fixed width for progress bar in bottom controls


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


class Timing:
    """Timing constants for UI operations."""
    
    # Progress bar timing (in milliseconds)
    PROGRESS_SUCCESS_DELAY = 500   # Delay before resetting progress bar after successful operation (reduced from 3000ms)
    PROGRESS_CANCEL_DELAY = 500    # Delay before resetting progress bar after cancelled operation (reduced from 2000ms)
    
    # UI update timing
    UI_REFRESH_DELAY = 0           # Immediate UI updates via event queue
    PANEL_INITIALIZATION_DELAY = 50    # Delay for panel data loading initialization
    FROZEN_TABLE_GEOMETRY_DELAY = 100   # Delay for frozen table geometry updates
    FROZEN_TABLE_GEOMETRY_DELAY_LOADING = 200  # Delay for frozen table geometry updates during data loading
    COLUMN_WIDTH_RESTORE_DELAY = 100    # Delay before restoring column widths after data refresh


class TableColumns:
    """Table column definitions and properties."""
    
    # Standard table headers (Render column added as first column)
    HEADERS = [
        "Render", "Order", "Node", "Filename", "Priority", "ChunkSize", "Frames", 
        "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", 
        "NukeX", "BatchMode", "ReloadPlugin", "Pool", "SecondaryPool", 
        "Group", "Threads", "MinRam", "MaxRam", "UseGPU", "GPUId", 
        "ConcurrentTasks", "WorkerTaskLimit", "MachineList", "Limits"
    ]
    
    # Display names for headers (more readable versions)
    HEADER_DISPLAY_NAMES = {
        "Render": "",  # Empty string = no header text shown for checkbox column
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
        "Fixed": ["Render", "Order", "Node", "Filename"],  # Always visible, cannot be hidden
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
    
    # Column width calculation settings (replaces hard-coded COLUMN_WIDTHS)
    COLUMN_WIDTH_SETTINGS = {
        # Minimum widths for each column type
        "min_widths": {
            "Render": 30,  # Checkbox + padding (20px checkbox + 10px padding)
            "Order": 50,
            "Node": 80, 
            "Filename": 150,
            "Priority": 60,
            "ChunkSize": 70,
            "Frames": 100,
            "NodesFrames": 80,
            "TaskTimeout": 80,
            "AutoTimeout": 80,
            "RenderMode": 80,
            "NukeX": 60,
            "BatchMode": 80,
            "ReloadPlugin": 90,
            "Pool": 70,
            "SecondaryPool": 90,
            "Group": 70,
            "Threads": 60,
            "MinRam": 60,
            "MaxRam": 60,
            "UseGPU": 60,
            "GPUId": 60,
            "ConcurrentTasks": 90,
            "WorkerTaskLimit": 100,
            "MachineList": 100,
            "Limits": 70
        },
        # Maximum widths for each column type
        "max_widths": {
            "Render": 30,  # Same as min (non-resizable)
            "Order": 80,
            "Node": 150,
            "Filename": 300,
            "Priority": 80,
            "ChunkSize": 110,  # Increased for "Chunk Size" text + padding
            "Frames": 150,
            "NodesFrames": 120,  # Increased for "Nodes Frames" text + padding
            "TaskTimeout": 120,  # Increased for "Task Timeout" text + padding
            "AutoTimeout": 120,  # Increased for "Auto Timeout" text + padding
            "RenderMode": 120,
            "NukeX": 80,
            "BatchMode": 120,  # Increased for "Batch Mode" text + padding
            "ReloadPlugin": 130,  # Increased for "Reload Plugin" text + padding
            "Pool": 100,
            "SecondaryPool": 130,  # Increased for "Secondary Pool" text + padding
            "Group": 120,  # Increased for better spacing
            "Threads": 80,
            "MinRam": 80,
            "MaxRam": 80,
            "UseGPU": 80,
            "GPUId": 80,
            "ConcurrentTasks": 140,  # Increased for "Concurrent Tasks" text + padding
            "WorkerTaskLimit": 140,  # Increased for "Worker Task Limit" text + padding
            "MachineList": 200,
            "Limits": 120
        }
    }
    
    @classmethod
    def calculate_column_width(cls, header_name, font_metrics, sample_values=None):
        """Calculate optimal column width based on header text and sample content.
        
        Args:
            header_name (str): Internal header name (e.g., "ConcurrentTasks")
            font_metrics (QFontMetrics): Font metrics for content text
            sample_values (list, optional): Sample values to consider for width
            
        Returns:
            int: Calculated optimal width in pixels
        """
        # Get display name for header
        display_name = cls.HEADER_DISPLAY_NAMES.get(header_name, header_name)
        
        # Debug output for width calculation
        from ...common.logging import qt_logger
        qt_logger.debug(f"Calculating width for '{header_name}' -> display: '{display_name}'")
        
        # FIXED: Calculate header text width using BOLD font to ensure it never truncates when selected
        # Create bold font metrics for header width calculation
        # Note: We need to create a new font since QFontMetrics doesn't expose its font
        try:
            # Try to get font from QApplication (most reliable)
            from PySide2.QtWidgets import QApplication
            app_font = QApplication.font()
        except:
            try:
                from PySide6.QtWidgets import QApplication
                app_font = QApplication.font()
            except:
                # Fallback to default font
                from PySide2.QtGui import QFont
                app_font = QFont()
        
        bold_font = app_font
        bold_font.setBold(True)
        bold_font_metrics = font_metrics.__class__(bold_font)
        
        # Calculate header text width using bold font
        try:
            header_width = bold_font_metrics.horizontalAdvance(display_name)
        except AttributeError:
            # Fallback for older Qt versions
            header_width = bold_font_metrics.width(display_name)
        
        # Debug header width calculation  
        qt_logger.debug(f"Header '{display_name}' base width (bold): {header_width}px")
        
        # Add header text padding (double it since padding is applied on both sides)
        header_width += Sizes.HEADER_TEXT_PADDING * 2
        
        # Calculate content width if sample values provided (using normal font for content)
        content_width = 0
        if sample_values:
            for value in sample_values:
                try:
                    value_width = font_metrics.horizontalAdvance(str(value))
                except AttributeError:
                    value_width = font_metrics.width(str(value))
                content_width = max(content_width, value_width)
            
            # Add some padding for content
            content_width += 16  # 8px each side for content padding
        
        # Use the larger of header or content width
        calculated_width = max(header_width, content_width)
        
        # Apply min/max constraints
        min_width = cls.COLUMN_WIDTH_SETTINGS["min_widths"].get(header_name, 60)
        max_width = cls.COLUMN_WIDTH_SETTINGS["max_widths"].get(header_name, 200)
        
        final_width = max(min_width, min(calculated_width, max_width))
        
        # Debug final width calculation
        qt_logger.debug(f"Final width for '{display_name}': {final_width}px (calculated: {calculated_width}px, header_bold: {header_width-Sizes.HEADER_TEXT_PADDING*2}px, content: {content_width}px, min: {min_width}px, max: {max_width}px)")
        
        return final_width


class GSVDefaults:
    """Default values and constants for GSV functionality."""
    
    # Default GSV text values
    DEFAULT_PRIMARY_GSVS = "Sequence, Shotcode"
    DEFAULT_SECONDARY_GSVS = "Resolution, Format"
    
    # GSV Column Sizing Constants
    SECONDARY_COLUMN_PADDING = 16  # Total padding for secondary columns (8px each side)
    SECONDARY_COLUMN_MIN_WIDTH = 20  # Minimum width for secondary columns
    SECONDARY_COLUMN_MAX_WIDTH = 120  # Maximum width for secondary columns
    PRIMARY_COLUMN_MIN_WIDTH = 120  # Minimum width for primary column
    PRIMARY_COLUMN_MAX_WIDTH = 250  # Maximum width for primary column
    PRIMARY_COLUMN_PADDING = 80  # Padding for primary column (checkbox + tree decoration + margins)
    PRIMARY_COLUMN_INDENTATION = 20  # Indentation per level in primary column
    
    # Header view minimum section sizes
    GSV_HEADER_MIN_SECTION_SIZE = 20  # Minimum section size for GSV tree header
    
    # Sample GSV data for demonstration
    SAMPLE_PRIMARY_DATA = {
        "Sequence": ["seq010", "seq020", "seq030"],
        "Shotcode": ["sh010", "sh020", "sh030", "sh040"]
    }
    
    SAMPLE_SECONDARY_DATA = {
        "Resolution": ["wh", "hh", "qh"],
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
        "use_node_frame_list": False,
        "task_timeout": 0,
        "enable_auto_timeout": False,
        "render_mode": "Full",
        "use_nuke_x": False,
        "batch_mode": False,
        "reload_plugins": False,
        "separate_tasks": False,
        "separate_jobs": False,
        "views_separate_jobs": False,
        # Machine settings defaults for node table
        "pool": "comp",
        "secondary_pool": "",
        "group": "none",
        "threads": 4,
        "stack_size": 0,
        "ram_use": 0,
        "use_gpu": False,
        "gpu_override": 0,
        "concurrent_tasks": 2,
        "limit_worker_tasks": False,
        "machine_list": "",
        "limit_groups": ""
    }
    
    # Machine settings defaults
    MACHINE_DEFAULTS = {
        "pool": "comp",
        "secondary_pool": "",
        "group": "none",
        "threads": 4,
        "stack_size": 0,
        "ram_use": 0,
        "gpu_override": 0,
        "use_gpu": False,
        "concurrent_tasks": 2,
        "limit_worker_tasks": False,
        "machine_limit": 0,
        "machine_deny_list": False,
        "machine_list": "",
        "limit_groups": ""
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
        "NodesFrames": "use_node_frame_list",
        "TaskTimeout": "task_timeout",
        "AutoTimeout": "enable_auto_timeout",
        "RenderMode": "render_mode",
        "NukeX": "use_nuke_x",
        "BatchMode": "batch_mode",
        "ReloadPlugin": "reload_plugins"
    }
    
    # Machine Settings Relationships  
    # Maps table column headers to machine settings field names
    MACHINE_SETTINGS_MAPPING = {
        "Pool": "pool",
        "SecondaryPool": "secondary_pool",
        "Group": "group",
        "Threads": "threads",
        "MinRam": "stack_size",
        "MaxRam": "ram_use",
        "UseGPU": "use_gpu",
        "GPUId": "gpu_override",
        "ConcurrentTasks": "concurrent_tasks",
        "WorkerTaskLimit": "limit_worker_tasks",
        "MachineList": "machine_list",
        "Limits": "limit_groups"
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

    # Machine settings columns (for styling pinned rows) - updated indices (+1 due to Render column)
    MACHINE_SETTINGS_COLUMNS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25] 