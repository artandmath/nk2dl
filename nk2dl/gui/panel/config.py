"""
Panel configuration system for nk2dl.

This module provides the core functionality for applying panel configurations,
including hiding/disabling controls, setting default values, and managing
widget state through configuration files and environment variables.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Set

from PySide2 import QtWidgets, QtCore

from nk2dl.common.logging import setup_logging
from nk2dl.common import config
from .tooltips import set_enhanced_tooltip

logger = setup_logging(__name__)

# Configuration constants
ESSENTIAL_CONTROLS = {
    'render_btn',      # Main render button - always visible
    'tab_widget',      # Tab widget - always visible
    'progress_bar',    # Progress bar - always visible
}

CONTROL_GROUPS = {
    'job_settings': {
        'priority', 'chunk_size', 'frames', 'frame_range', 'use_node_frame_list',
        'task_timeout', 'enable_auto_timeout', 'render_mode', 'render_nukex',
        'use_batch_mode', 'reload_plugin', 'separate_tasks', 'separate_jobs',
        'views_separate_jobs'
    },
    'machine_settings': {
        'pool', 'secondary_pool', 'group', 'threads', 'min_ram', 'max_ram',
        'gpu_override', 'use_gpu', 'concurrent_tasks', 'limit_tasks',
        'machine_limit', 'machine_deny_list', 'machine_list', 'limits'
    },
    'table_controls': {
        'update', 'all', 'clear', 'selection', 'inside_groups', 'column_dropdown', 'filter'
    },
    'extra_settings': {
        'job_name', 'comment', 'department'
    }
}

# Widget default value storage
_widget_defaults: Dict[str, Any] = {}

def apply_panel_config(widget: QtWidgets.QWidget, control_name: Optional[str] = None) -> None:
    """Apply panel configuration to a widget.
    
    This is the main entry point for applying panel configuration. It handles:
    - Storing widget default values before configuration
    - Applying hidden state
    - Applying disabled state with visual styling
    - Setting default values
    - Adding enhanced tooltips with configuration source information
    - Adding context menu for reset functionality
    
    Args:
        widget: The Qt widget to configure
        control_name: The name of the control (used for configuration lookup)
    """
    logger.debug(f"apply_panel_config called with widget={widget}, control_name={control_name}")
    
    if not widget or not control_name:
        logger.debug(f"Skipping configuration - widget: {widget}, control_name: {control_name}")
        return
    
    logger.debug(f"Applying panel configuration to {control_name} (widget: {widget.__class__.__name__})")
    
    # Skip essential controls for safety (but still add tooltips)
    if control_name in ESSENTIAL_CONTROLS:
        logger.debug(f"Skipping configuration for essential control: {control_name}")
        # Still add enhanced tooltip and context menu for essential controls
        try:
            set_enhanced_tooltip(widget, control_name)
            logger.debug(f"Enhanced tooltip set for essential control: {control_name}")
        except Exception as e:
            logger.error(f"Error setting tooltip for essential control {control_name}: {e}")
        return
    
    try:
        # Store widget default value before any configuration
        _store_widget_default(widget, control_name)
        
        # Get panel configuration for this control
        config_key = f"panel.{control_name}"
        control_config = config.get(config_key, {})
        
        # Apply configuration if it exists
        if control_config:
            logger.debug(f"Applying configuration to {control_name}: {control_config}")
            
            # Apply hidden state
            if 'hidden' in control_config:
                hidden = bool(control_config['hidden'])
                widget.setVisible(not hidden)
                logger.debug(f"Set {control_name} hidden state: {hidden}")
            
            # Apply disabled state with styling
            if 'disabled' in control_config:
                disabled = bool(control_config['disabled'])
                widget.setEnabled(not disabled)
                if disabled:
                    _apply_disabled_styling(widget)
                logger.debug(f"Set {control_name} disabled state: {disabled}")
            
            # Apply default value
            if 'default_value' in control_config:
                default_value = control_config['default_value']
                _set_widget_value(widget, default_value)
                logger.debug(f"Set {control_name} default value: {default_value}")
        else:
            logger.debug(f"No configuration found for control: {control_name}")
        
        # Always set enhanced tooltip and context menu (regardless of whether config exists)
        try:
            logger.debug(f"Attempting to set enhanced tooltip for {control_name}")
            set_enhanced_tooltip(widget, control_name)
            logger.debug(f"Enhanced tooltip set for {control_name}")
        except Exception as e:
            logger.error(f"Error setting enhanced tooltip for {control_name}: {e}")
            import traceback
            logger.debug(f"Tooltip error traceback: {traceback.format_exc()}")
            
        try:
            logger.debug(f"Attempting to add context menu for {control_name}")
            _add_context_menu(widget, control_name)
            logger.debug(f"Context menu added for {control_name}")
        except Exception as e:
            logger.error(f"Error adding context menu for {control_name}: {e}")
            import traceback
            logger.debug(f"Context menu error traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logger.error(f"Error applying configuration to {control_name}: {e}")
        # Still try to add basic tooltip even if configuration fails
        try:
            set_enhanced_tooltip(widget, control_name)
        except:
            pass


def _store_widget_default(widget: QtWidgets.QWidget, control_name: str) -> None:
    """Store the widget's default value before configuration is applied."""
    if control_name in _widget_defaults:
        return  # Already stored
    
    try:
        default_value = _get_current_widget_value(widget)
        _widget_defaults[control_name] = {
            'value': default_value,
            'visible': widget.isVisible(),
            'enabled': widget.isEnabled(),
            'style': widget.styleSheet()
        }
        logger.debug(f"Stored default for {control_name}: {_widget_defaults[control_name]}")
        
    except Exception as e:
        logger.error(f"Error storing default for {control_name}: {e}")


def _set_widget_value(widget: QtWidgets.QWidget, value: Any) -> None:
    """Set a widget's value based on its type."""
    try:
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(float(value))
        elif isinstance(widget, QtWidgets.QComboBox):
            # Try to find and set the text, otherwise set by index
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
            else:
                try:
                    widget.setCurrentIndex(int(value))
                except (ValueError, TypeError):
                    logger.warning(f"Could not set combo box value: {value}")
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QtWidgets.QTextEdit):
            widget.setPlainText(str(value))
        else:
            logger.warning(f"Unsupported widget type for value setting: {type(widget)}")
            
    except Exception as e:
        logger.error(f"Error setting widget value: {e}")


def _apply_disabled_styling(widget: QtWidgets.QWidget) -> None:
    """Apply visual styling to indicate a disabled widget."""
    try:
        # Get current style and add disabled appearance
        current_style = widget.styleSheet()
        disabled_style = """
            color: #888888;
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
        """
        
        # Combine styles
        new_style = current_style + disabled_style
        widget.setStyleSheet(new_style)
        
    except Exception as e:
        logger.error(f"Error applying disabled styling: {e}")


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


def _add_context_menu(widget: QtWidgets.QWidget, control_name: str) -> None:
    """Add context menu to widget for reset functionality."""
    try:
        widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos: _show_context_menu(widget, control_name, pos)
        )
        
    except Exception as e:
        logger.error(f"Error adding context menu to {control_name}: {e}")


def _show_context_menu(widget: QtWidgets.QWidget, control_name: str, position: QtCore.QPoint) -> None:
    """Show context menu with reset options."""
    try:
        menu = QtWidgets.QMenu(widget)
        
        # Add reset actions
        reset_control_action = menu.addAction(f"Reset {_get_control_display_name(control_name)} to Default")
        reset_control_action.triggered.connect(lambda: _reset_control_to_default(control_name))
        
        # Add group reset if control belongs to a group
        group_name = _get_control_group(control_name)
        if group_name:
            reset_group_action = menu.addAction(f"Reset {group_name.replace('_', ' ').title()} to Defaults")
            reset_group_action.triggered.connect(lambda: _reset_group_to_default(group_name))
        
        menu.addSeparator()
        
        # Add panel-wide reset
        reset_all_action = menu.addAction("Reset All Panel Controls to Defaults")
        reset_all_action.triggered.connect(_reset_all_to_default)
        
        # Show menu
        global_pos = widget.mapToGlobal(position)
        menu.exec_(global_pos)
        
    except Exception as e:
        logger.error(f"Error showing context menu for {control_name}: {e}")


def _reset_control_to_default(control_name: str) -> None:
    """Reset a single control to its default value."""
    try:
        if control_name not in _widget_defaults:
            logger.warning(f"No default stored for control: {control_name}")
            return
        
        # Find the widget and reset it
        widget = _find_widget_by_name(control_name)
        if not widget:
            logger.warning(f"Could not find widget for control: {control_name}")
            return
        
        defaults = _widget_defaults[control_name]
        
        # Restore original state
        widget.setVisible(defaults['visible'])
        widget.setEnabled(defaults['enabled'])
        widget.setStyleSheet(defaults['style'])
        _set_widget_value(widget, defaults['value'])
        
        logger.info(f"Reset control {control_name} to default")
        
    except Exception as e:
        logger.error(f"Error resetting control {control_name}: {e}")


def _reset_group_to_default(group_name: str) -> None:
    """Reset all controls in a group to their defaults."""
    try:
        if group_name not in CONTROL_GROUPS:
            logger.warning(f"Unknown control group: {group_name}")
            return
        
        for control_name in CONTROL_GROUPS[group_name]:
            _reset_control_to_default(control_name)
        
        logger.info(f"Reset group {group_name} to defaults")
        
    except Exception as e:
        logger.error(f"Error resetting group {group_name}: {e}")


def _reset_all_to_default() -> None:
    """Reset all panel controls to their defaults."""
    try:
        for control_name in _widget_defaults.keys():
            if control_name not in ESSENTIAL_CONTROLS:
                _reset_control_to_default(control_name)
        
        logger.info("Reset all panel controls to defaults")
        
    except Exception as e:
        logger.error(f"Error resetting all controls: {e}")


def _get_control_group(control_name: str) -> Optional[str]:
    """Get the group name for a control."""
    for group_name, controls in CONTROL_GROUPS.items():
        if control_name in controls:
            return group_name
    return None


def _get_control_display_name(control_name: str) -> str:
    """Get a human-readable display name for a control."""
    # Convert snake_case to Title Case
    return control_name.replace('_', ' ').title()


def _find_widget_by_name(control_name: str) -> Optional[QtWidgets.QWidget]:
    """Find a widget by its control name."""
    try:
        panel = _get_panel_instance()
        if not panel:
            return None
        
        # Search for widget by objectName
        widget = panel.findChild(QtWidgets.QWidget, control_name)
        return widget
        
    except Exception as e:
        logger.error(f"Error finding widget {control_name}: {e}")
        return None


def _get_panel_instance():
    """Get the current panel instance for widget discovery."""
    try:
        # Try to find the panel instance in Qt's application
        # This is a simple approach that looks for any Nk2dlPanel widget
        app = QtWidgets.QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if widget.__class__.__name__ == 'Nk2dlPanel':
                    logger.debug(f"Found panel instance: {widget}")
                    return widget
        
        logger.debug("No panel instance found in Qt application")
        return None
        
    except Exception as e:
        logger.error(f"Error getting panel instance: {e}")
        return None
