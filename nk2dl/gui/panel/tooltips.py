"""
Panel tooltip definitions and generation logic.

This module contains default tooltips for panel controls and the logic
for generating enhanced tooltips with configuration information.
"""

import os
from pathlib import Path
from typing import Optional, Any

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from nk2dl.common.logging import setup_logging
from nk2dl.common.config import config

logger = setup_logging(__name__)

# Default tooltips for panel controls
DEFAULT_TOOLTIPS = {
    # Essential controls
    'render_btn': 'Submit the selected nodes to Deadline for rendering',
    'tab_widget': 'Switch between different panel sections',
    'progress_bar': 'Shows rendering progress and status',
    
    # Job settings controls
    'priority': 'Set the job priority (0-100, higher numbers = higher priority)',
    'chunk_size': 'Number of frames to render per task',
    'frames': 'Frame range source (Global, Custom, or Node)',
    'frame_range': 'Custom frame range (e.g., 1-100, 1-50,75-100)',
    'use_node_frame_list': 'Use frame list from selected nodes instead of range',
    'task_timeout': 'Maximum time (minutes) before a task times out (0 = no timeout)',
    'enable_auto_timeout': 'Automatically set timeout based on frame complexity',
    'render_mode': 'Rendering mode (Full, Bbox, or other)',
    'render_nukex': 'Use NukeX instead of Nuke for rendering',
    'use_batch_mode': 'Run Nuke in batch mode (no GUI)',
    'reload_plugin': 'Reload plugins before rendering',
    'separate_tasks': 'Create separate tasks for each frame',
    'separate_jobs': 'Create separate jobs for each selected node',
    'views_separate_jobs': 'Create separate jobs for each view',
    
    # Machine settings controls
    'pool': 'Primary machine pool for rendering',
    'secondary_pool': 'Secondary machine pool as fallback',
    'group': 'Machine group for job assignment',
    'threads': 'Number of CPU threads to use per task',
    'min_ram': 'Minimum RAM required (GB)',
    'max_ram': 'Maximum RAM allowed (GB)',
    'gpu_override': 'Number of GPUs to use (overrides auto-detection)',
    'use_gpu': 'Enable GPU acceleration for rendering',
    'concurrent_tasks': 'Maximum concurrent tasks per machine',
    'limit_tasks': 'Enable task limiting per machine',
    'machine_limit': 'Maximum number of machines to use',
    'machine_deny_list': 'Use machine deny list',
    'machine_list': 'List of machines to exclude from rendering',
    'limits': 'Additional Deadline limits (comma-separated)',
    
    # Table controls
    'update': 'Refresh the node list and update rendering information',
    'all': 'Select all nodes in the table',
    'clear': 'Clear all selections in the table',
    'selection': 'Select only the currently selected nodes in Nuke',
    'inside_groups': 'Include nodes inside groups in the scan',
    'column_dropdown': 'Show/hide table columns',
    'filter': 'Filter nodes by name or type',
    
    # Extra settings controls
    'job_name': 'Custom job name (leave empty for auto-generated)',
    'comment': 'Job comment or description',
    'department': 'Department name for job organization',
}


def get_default_tooltip(control_name: str) -> str:
    """Get the default tooltip for a control."""
    return DEFAULT_TOOLTIPS.get(control_name, f"Configuration control: {control_name}")


def set_enhanced_tooltip(widget: QtWidgets.QWidget, control_name: str) -> None:
    """Set enhanced tooltip with configuration information."""
    try:
        # Get default tooltip
        default_tooltip = get_default_tooltip(control_name)
        
        # Get current value and source information
        config_key = f"panel.{control_name}"
        current_value = _get_current_widget_value(widget)
        
        # Build enhanced tooltip lines using HTML formatting
        tooltip_lines = []
        
        # Start with bold control name (config file format)
        tooltip_lines.append(f"<b>{control_name}</b>")
        
        # Add default tooltip
        tooltip_lines.append("<br>")
        tooltip_lines.append(default_tooltip)
        
        # Add configuration information (skip default value for buttons)
        tooltip_lines.append("<br><br>")
        
        # Only show default value for non-button widgets
        if not isinstance(widget, QtWidgets.QPushButton):
            tooltip_lines.append(f"Default Value: {current_value}<br>")
        
        # Try to get configuration source (don't fail if this doesn't work)
        try:
            config_source = _identify_config_source(config_key)
            if config_source:
                tooltip_lines.append(f"<br>Configuration Source: {config_source}")
        except Exception as e:
            logger.debug(f"Could not identify config source for {control_name}: {e}")
        
        # Add group information
        from .config import _get_control_group
        group_name = _get_control_group(control_name)
        if group_name:
            tooltip_lines.append(f"<br>Group: {group_name.replace('_', ' ').title()}")
        
        # Add reset instructions
        tooltip_lines.append("<br><br>Right-click for reset options")
        
        # Set the enhanced tooltip
        tooltip_text = "".join(tooltip_lines)
        widget.setToolTip(tooltip_text)
        
        logger.debug(f"Enhanced tooltip set for {control_name}")
        
    except Exception as e:
        logger.error(f"Error setting enhanced tooltip for {control_name}: {e}")
        # Try to set a basic tooltip as fallback
        try:
            fallback_tooltip = f"<b>{control_name}</b><br><br>Right-click for reset options"
            widget.setToolTip(fallback_tooltip)
        except:
            pass  # Don't fail completely if we can't set any tooltip


def _get_current_widget_value(widget: QtWidgets.QWidget) -> Any:
    """Get the current value of a widget."""
    try:
        if isinstance(widget, QtWidgets.QSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QComboBox):
            return widget.currentText()
        elif isinstance(widget, QtWidgets.QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QtWidgets.QLineEdit):
            return widget.text()
        elif isinstance(widget, QtWidgets.QTextEdit):
            return widget.toPlainText()
        else:
            return str(widget)
            
    except Exception as e:
        logger.error(f"Error getting widget value: {e}")
        return None


def _identify_config_source(config_key: str) -> Optional[str]:
    """Identify the source of a configuration value."""
    try:
        # Check if value exists in configuration
        value = config.get(config_key)
        if value is None:
            return "No configuration (using defaults)"
        
        # Check environment variable
        env_var = _config_key_to_env_var(config_key)
        if env_var in os.environ:
            return f"Environment variable: {env_var}"
        
        # Check user config file
        try:
            user_config_path = config.USER_CONFIG_PATH
            if user_config_path.exists() and _key_exists_in_yaml(user_config_path, config_key):
                return f"User config: {user_config_path}"
        except Exception as e:
            logger.debug(f"Could not check user config for {config_key}: {e}")
        
        # Check project config file
        try:
            project_config_path = getattr(config, '_project_config_path', None)
            if project_config_path and project_config_path.exists() and _key_exists_in_yaml(project_config_path, config_key):
                return f"Project config: {project_config_path}"
        except Exception as e:
            logger.debug(f"Could not check project config for {config_key}: {e}")
        
        # If we have a value but couldn't find its source, it's likely from default config
        return "Default configuration"
        
    except Exception as e:
        logger.debug(f"Error identifying config source for {config_key}: {e}")
        return None


def _config_key_to_env_var(config_key: str) -> str:
    """Convert a config key to environment variable name."""
    # Split into parts and convert underscores to double underscores
    parts = config_key.replace('_', '__').split('.')
    # Join with underscores and add prefix
    return 'NK2DL_' + '_'.join(part.upper() for part in parts)


def _key_exists_in_yaml(file_path: Path, config_key: str) -> bool:
    """Check if a configuration key exists in a YAML file."""
    try:
        import yaml
        
        with file_path.open('r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False
        
        # Navigate through nested keys
        current = data
        for part in config_key.split('.'):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        return True
        
    except Exception as e:
        logger.debug(f"Error checking key {config_key} in {file_path}: {e}")
        return False 