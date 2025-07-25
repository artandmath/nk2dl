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
        'priority', 'chunk_size', 'frames', 'custom_frames', 'frame_range', 'use_node_frame_list',
        'task_timeout', 'enable_auto_timeout', 'render_mode', 'render_nukex',
        'separate_tasks', 'separate_jobs',
        'render_order_dependencies', 'views_separate_jobs'
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
        'job_name', 'comment', 'department', 'job_dependencies', 'batch_mode', 'reload_plugins', 'render_settings_from_metadata'
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
        defaults_to_store = {
            'value': default_value,
            'visible': widget.isVisible(),
            'enabled': widget.isEnabled(),
            'style': widget.styleSheet()
        }
        
        _widget_defaults[control_name] = defaults_to_store
        
        # Add detailed logging to debug what's being stored
        logger.debug(f"Storing defaults for {control_name}:")
        logger.debug(f"  Widget type: {type(widget).__name__}")
        logger.debug(f"  Stored defaults: {defaults_to_store}")
        
    except Exception as e:
        logger.error(f"Error storing default for {control_name}: {e}")
        import traceback
        logger.debug(f"Store error traceback: {traceback.format_exc()}")


def _set_widget_value(widget: QtWidgets.QWidget, value: Any) -> None:
    """Set a widget's value based on its type."""
    try:
        logger.debug(f"Setting widget value: {type(widget).__name__} = {value}")
        
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(float(value))
        elif isinstance(widget, QtWidgets.QComboBox):
            # Try to find and set the text, otherwise set by index
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
                logger.debug(f"Set combo box to index {index} (text: {value})")
            else:
                try:
                    widget.setCurrentIndex(int(value))
                    logger.debug(f"Set combo box to index {int(value)}")
                except (ValueError, TypeError):
                    logger.warning(f"Could not set combo box value: {value}")
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
            logger.debug(f"Set checkbox to {bool(value)}")
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(str(value))
            logger.debug(f"Set line edit to '{str(value)}'")
        elif isinstance(widget, QtWidgets.QTextEdit):
            widget.setPlainText(str(value))
            logger.debug(f"Set text edit to '{str(value)}'")
        else:
            logger.warning(f"Unsupported widget type for value setting: {type(widget)}")
            
    except Exception as e:
        logger.error(f"Error setting widget value: {e}")
        import traceback
        logger.debug(f"Set widget value error traceback: {traceback.format_exc()}")


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
        # Disconnect any existing context menu connections to prevent conflicts
        try:
            widget.customContextMenuRequested.disconnect()
            logger.debug(f"Disconnected existing context menu signal for {control_name}")
        except (TypeError, RuntimeError) as e:
            # No connections exist, which is fine
            logger.debug(f"No existing context menu connections for {control_name}: {e}")
        
        # Set context menu policy
        widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        logger.debug(f"Set context menu policy for {control_name}")
        
        # Store control_name as a property on the widget to avoid lambda closure issues
        widget.setProperty("nk2dl_control_name", control_name)
        logger.debug(f"Set nk2dl_control_name property for {control_name}")
        
        # Connect signal using a proper slot method to avoid lambda issues
        widget.customContextMenuRequested.connect(
            lambda pos, w=widget: _show_context_menu_safe(w, pos)
        )
        logger.debug(f"Connected customContextMenuRequested signal for {control_name}")
        
        # Verify the connection was successful
        try:
            # Test emit to verify signal is connected (but don't show menu)
            # We'll use a flag to prevent actual menu display during test
            widget.setProperty("nk2dl_test_emit", True)
            widget.customContextMenuRequested.emit(QtCore.QPoint(0, 0))
            widget.setProperty("nk2dl_test_emit", False)
            logger.debug(f"Context menu signal verification successful for {control_name}")
        except Exception as e:
            logger.warning(f"Context menu signal verification failed for {control_name}: {e}")
        
        logger.debug(f"Context menu setup completed successfully for {control_name}")
        
    except Exception as e:
        logger.error(f"Error adding context menu to {control_name}: {e}")
        import traceback
        logger.debug(f"Context menu setup error traceback: {traceback.format_exc()}")


def _show_context_menu_safe(widget: QtWidgets.QWidget, position: QtCore.QPoint) -> None:
    """Safe wrapper for showing context menu that gets control_name from widget property."""
    try:
        # Check if this is a test emit (don't show menu during verification)
        if widget.property("nk2dl_test_emit"):
            logger.debug("Test emit detected, skipping menu display")
            return
        
        # Get control name from widget property
        control_name = widget.property("nk2dl_control_name")
        if not control_name:
            logger.warning("Widget missing nk2dl_control_name property for context menu")
            return
        
        logger.debug(f"Context menu requested for {control_name} at position {position}")
        _show_context_menu(widget, control_name, position)
        
    except Exception as e:
        logger.error(f"Error in safe context menu handler: {e}")
        import traceback
        logger.debug(f"Safe context menu error traceback: {traceback.format_exc()}")


def _show_context_menu(widget: QtWidgets.QWidget, control_name: str, position: QtCore.QPoint) -> None:
    """Show context menu with reset options."""
    try:
        logger.debug(f"Showing context menu for {control_name} at position {position}")
        
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
        logger.debug(f"Executing context menu at global position {global_pos}")
        menu.exec_(global_pos)
        
    except Exception as e:
        logger.error(f"Error showing context menu for {control_name}: {e}")
        import traceback
        logger.debug(f"Context menu error traceback: {traceback.format_exc()}")


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
        
        # Add detailed logging to debug the reset process
        logger.debug(f"Resetting {control_name}:")
        logger.debug(f"  Current state - visible: {widget.isVisible()}, enabled: {widget.isEnabled()}")
        logger.debug(f"  Stored defaults: {defaults}")
        
        # Restore original state - but keep widget visible since user is interacting with it
        # widget.setVisible(defaults['visible'])  # Don't reset visibility for individual controls
        widget.setEnabled(defaults['enabled'])
        widget.setStyleSheet(defaults['style'])
        _set_widget_value(widget, defaults['value'])
        
        # INTEGRATION: Remove from user-changed tracking and update storage
        _remove_from_user_changed_tracking(control_name)
        
        # Log final state
        logger.debug(f"  After reset - visible: {widget.isVisible()}, enabled: {widget.isEnabled()}")
        
        logger.info(f"Reset control {control_name} to default")
        
    except Exception as e:
        logger.error(f"Error resetting control {control_name}: {e}")
        import traceback
        logger.debug(f"Reset error traceback: {traceback.format_exc()}")


def _remove_from_user_changed_tracking(control_name: str) -> None:
    """Remove a control from user-changed tracking and update storage.
    
    Args:
        control_name: The control name to remove from tracking
    """
    try:
        # Find the panel instance to access the settings model
        panel = _get_panel_instance()
        if not panel:
            logger.warning("Could not find panel instance for user-changed tracking")
            return
        
        # Map control name to parameter name (they're usually the same but let's be explicit)
        param_name = _get_parameter_name_from_control_name(control_name)
        
        # Remove from settings model user-changed tracking
        if hasattr(panel, 'settings_model') and panel.settings_model:
            panel.settings_model.mark_as_reset_to_default(param_name)
            logger.debug(f"Removed {param_name} from settings model user-changed tracking")
        
        # Trigger save to storage to update YAML
        if hasattr(panel, '_on_settings_changed_save_to_storage'):
            panel._on_settings_changed_save_to_storage()
            logger.debug(f"Triggered storage save after resetting {control_name}")
        
        # Refresh visual indications after a short delay to ensure storage save completes
        def refresh_visual_indications():
            try:
                if hasattr(panel, '_refresh_all_visual_indications'):
                    panel._refresh_all_visual_indications()
                    logger.debug(f"Refreshed visual indications after resetting {control_name}")
            except Exception as e:
                logger.error(f"Error refreshing visual indications: {e}")
        
        # Use QTimer to delay the refresh
        QtCore.QTimer.singleShot(100, refresh_visual_indications)
        
    except Exception as e:
        logger.error(f"Error removing {control_name} from user-changed tracking: {e}")


def _get_parameter_name_from_control_name(control_name: str) -> str:
    """Map control name to parameter name for user-changed tracking.
    
    Args:
        control_name: The control name used in the config system
        
    Returns:
        The parameter name used in the settings model
    """
    # Mapping from control names to parameter names
    control_to_param = {
        'priority': 'priority',
        'chunk_size': 'chunk_size',
        'frames': 'frames_mode',  # Special case - frames control maps to frames_mode param
        'frame_range': 'frames',  # Special case - frame_range control maps to frames param
        'use_node_frame_list': 'use_node_frame_list',
        'task_timeout': 'task_timeout',
        'enable_auto_timeout': 'enable_auto_timeout',
        'render_mode': 'render_mode',
        'render_nukex': 'use_nuke_x',
        'use_batch_mode': 'batch_mode',
        'reload_plugin': 'reload_plugins',
        'separate_tasks': 'separate_tasks',
        'separate_jobs': 'separate_jobs',
        'render_order_dependencies': 'render_order_dependencies',
        'views_separate_jobs': 'views_separate_jobs',
        'pool': 'pool',
        'secondary_pool': 'secondary_pool',
        'group': 'group',
        'threads': 'threads',
        'min_ram': 'stack_size',
        'max_ram': 'ram_use',
        'gpu_override': 'gpu_override',
        'use_gpu': 'use_gpu',
        'concurrent_tasks': 'concurrent_tasks',
        'limit_tasks': 'limit_worker_tasks',
        'machine_limit': 'machine_limit',
        'machine_deny_list': 'machine_deny_list',
        'machine_list': 'machine_list',
        'limits': 'limit_groups',
        'job_name': 'job_name',
        'comment': 'comment',
        'department': 'department'
    }
    
    # Return mapped parameter name or fall back to control name if no mapping exists
    return control_to_param.get(control_name, control_name)


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
            logger.warning("No panel instance found for widget discovery")
            return None
        
        # First try to find by exact objectName match
        widget = panel.findChild(QtWidgets.QWidget, control_name)
        if widget:
            logger.debug(f"Found widget {control_name} by objectName")
            return widget
        
        # If not found by objectName, try to find by property (fallback)
        for child in panel.findChildren(QtWidgets.QWidget):
            if child.property("nk2dl_control_name") == control_name:
                logger.debug(f"Found widget {control_name} by property")
                return child
        
        logger.warning(f"Widget not found for control: {control_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error finding widget {control_name}: {e}")
        return None


def _get_panel_instance():
    """Get the current panel instance for widget discovery."""
    try:
        # Try to find the panel instance in Qt's application
        # This is a simple approach that looks for any Nk2dlPanel widget
        app = QtWidgets.QApplication.instance()
        if not app:
            logger.warning("No Qt application instance found")
            return None
            
        # Look for Nk2dlPanel widgets
        panels = []
        for widget in app.allWidgets():
            if widget.__class__.__name__ == 'Nk2dlPanel':
                panels.append(widget)
        
        if not panels:
            logger.debug("No Nk2dlPanel instances found in Qt application")
            return None
        elif len(panels) == 1:
            logger.debug(f"Found single panel instance: {panels[0]}")
            return panels[0]
        else:
            # Multiple panels - try to find the active/visible one
            for panel in panels:
                if panel.isVisible():
                    logger.debug(f"Found visible panel instance: {panel}")
                    return panel
            # If none are visible, return the first one
            logger.debug(f"Multiple panels found, returning first: {panels[0]}")
            return panels[0]
        
    except Exception as e:
        logger.error(f"Error getting panel instance: {e}")
        return None

# Debug utility functions
def debug_context_menu_status(control_name: str) -> None:
    """Debug utility to check context menu status for a control."""
    try:
        widget = _find_widget_by_name(control_name)
        if not widget:
            logger.info(f"DEBUG: Widget not found for {control_name}")
            return
        
        logger.info(f"DEBUG: Context menu status for {control_name}:")
        logger.info(f"  - Widget type: {type(widget).__name__}")
        logger.info(f"  - Widget visible: {widget.isVisible()}")
        logger.info(f"  - Widget enabled: {widget.isEnabled()}")
        logger.info(f"  - Object name: {widget.objectName()}")
        logger.info(f"  - Context menu policy: {widget.contextMenuPolicy()}")
        logger.info(f"  - nk2dl_control_name property: {widget.property('nk2dl_control_name')}")
        
        # Check if customContextMenuRequested signal has connections
        signal = widget.customContextMenuRequested
        try:
            # This is a bit hacky, but we can check if the signal has connections
            signal.emit(widget.rect().center())  # Emit to test, but don't show menu
        except:
            logger.info(f"  - customContextMenuRequested signal appears disconnected")
        else:
            logger.info(f"  - customContextMenuRequested signal appears connected")
            
    except Exception as e:
        logger.error(f"Error in debug_context_menu_status for {control_name}: {e}")


def test_context_menu_manually(control_name: str) -> None:
    """Manually trigger context menu for testing purposes."""
    try:
        widget = _find_widget_by_name(control_name)
        if not widget:
            logger.error(f"Widget not found for control: {control_name}")
            return
        
        logger.info(f"Manually triggering context menu for {control_name}")
        
        # Get the center of the widget for the menu position
        center_pos = widget.rect().center()
        logger.info(f"Widget center position: {center_pos}")
        
        # Manually trigger the context menu
        widget.customContextMenuRequested.emit(center_pos)
        logger.info(f"Context menu signal emitted for {control_name}")
        
    except Exception as e:
        logger.error(f"Error manually testing context menu for {control_name}: {e}")
        import traceback
        logger.debug(f"Manual test error traceback: {traceback.format_exc()}")
