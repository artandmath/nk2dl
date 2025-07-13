# -*- coding: utf-8 -*-
"""Widget change tracking system for the nk2dl panel.

This module provides functionality to track which widgets have been explicitly
changed by users versus programmatically changed, enabling proper storage
behavior and visual indication.
"""

from typing import Dict, Any, Optional, Set
from ...common.logging import setup_logging

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
    PYSIDE_VERSION = "Unknown"
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

logger = setup_logging('nk2dl.gui.panel.widget_change_tracker')


class WidgetChangeTracker:
    """Tracks which widgets have been explicitly changed by users.
    
    This class maintains the distinction between user-initiated changes and
    programmatic changes to widgets, which is crucial for proper storage
    behavior and visual indication.
    """
    
    def __init__(self):
        """Initialize the widget change tracker."""
        # Maps parameter name to boolean indicating if user changed it
        self._user_changed_settings: Dict[str, bool] = {}
        
        # Maps widget object to parameter name for reverse lookup
        self._widget_to_param: Dict[Any, str] = {}
        
        # Flag to temporarily disable tracking (for programmatic changes)
        self._tracking_disabled = False
        
        logger.debug("WidgetChangeTracker initialized")
    
    def register_widget(self, widget, param_name: str) -> None:
        """Register a widget for change tracking.
        
        Args:
            widget: The widget to track
            param_name: The parameter name this widget controls
        """
        self._widget_to_param[widget] = param_name
        # Initialize as not user-changed
        if param_name not in self._user_changed_settings:
            self._user_changed_settings[param_name] = False
        
        logger.debug(f"Registered widget for parameter {param_name}")
    
    def unregister_widget(self, widget) -> None:
        """Unregister a widget from change tracking.
        
        Args:
            widget: The widget to unregister
        """
        if widget in self._widget_to_param:
            param_name = self._widget_to_param[widget]
            del self._widget_to_param[widget]
            logger.debug(f"Unregistered widget for parameter {param_name}")
    
    def mark_as_user_changed(self, param_name: str) -> None:
        """Mark a parameter as user-changed.
        
        Args:
            param_name: The parameter name to mark as user-changed
        """
        if not self._tracking_disabled:
            self._user_changed_settings[param_name] = True
            logger.debug(f"Marked parameter {param_name} as user-changed")
    
    def mark_widget_as_user_changed(self, widget) -> None:
        """Mark a widget's parameter as user-changed.
        
        Args:
            widget: The widget whose parameter should be marked as user-changed
        """
        if not self._tracking_disabled and widget in self._widget_to_param:
            param_name = self._widget_to_param[widget]
            self.mark_as_user_changed(param_name)
    
    def mark_as_reset_to_default(self, param_name: str) -> None:
        """Mark a parameter as reset to default (no longer user-changed).
        
        This completely removes the parameter from user-changed tracking.
        
        Args:
            param_name: The parameter name to mark as reset
        """
        # Remove the parameter completely from user-changed tracking
        if param_name in self._user_changed_settings:
            del self._user_changed_settings[param_name]
        logger.debug(f"Removed parameter {param_name} from user-changed tracking (reset to default)")
    
    def mark_widget_as_reset_to_default(self, widget) -> None:
        """Mark a widget's parameter as reset to default.
        
        Args:
            widget: The widget whose parameter should be marked as reset
        """
        if widget in self._widget_to_param:
            param_name = self._widget_to_param[widget]
            self.mark_as_reset_to_default(param_name)
    
    def is_user_changed(self, param_name: str) -> bool:
        """Check if a parameter has been changed by the user.
        
        Args:
            param_name: The parameter name to check
            
        Returns:
            True if the parameter has been changed by the user
        """
        return self._user_changed_settings.get(param_name, False)
    
    def is_widget_user_changed(self, widget) -> bool:
        """Check if a widget's parameter has been changed by the user.
        
        Args:
            widget: The widget to check
            
        Returns:
            True if the widget's parameter has been changed by the user
        """
        if widget in self._widget_to_param:
            param_name = self._widget_to_param[widget]
            return self.is_user_changed(param_name)
        return False
    
    def get_user_changed_settings(self) -> Dict[str, bool]:
        """Get all parameters that have been changed by the user.
        
        Returns:
            Dictionary mapping parameter names to True if user-changed
        """
        return {param: True for param, changed in self._user_changed_settings.items() if changed}
    
    def get_user_changed_param_names(self) -> Set[str]:
        """Get set of parameter names that have been changed by the user.
        
        Returns:
            Set of parameter names that are user-changed
        """
        return {param for param, changed in self._user_changed_settings.items() if changed}
    
    def disable_tracking(self) -> None:
        """Temporarily disable change tracking.
        
        This is useful when making programmatic changes that shouldn't
        be tracked as user changes.
        """
        self._tracking_disabled = True
        logger.debug("Change tracking disabled")
    
    def enable_tracking(self) -> None:
        """Re-enable change tracking."""
        self._tracking_disabled = False
        logger.debug("Change tracking enabled")
    
    def is_tracking_disabled(self) -> bool:
        """Check if tracking is currently disabled.
        
        Returns:
            True if tracking is disabled
        """
        return self._tracking_disabled
    
    def clear_all_user_changes(self) -> None:
        """Clear all user change tracking.
        
        This resets all parameters to not user-changed state.
        """
        self._user_changed_settings.clear()
        logger.debug("Cleared all user change tracking")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked changes.
        
        Returns:
            Dictionary with tracking statistics
        """
        total_params = len(self._user_changed_settings)
        user_changed_count = sum(1 for changed in self._user_changed_settings.values() if changed)
        
        return {
            'total_tracked_params': total_params,
            'user_changed_count': user_changed_count,
            'tracking_disabled': self._tracking_disabled,
            'registered_widgets': len(self._widget_to_param)
        }
    
    def get_change_tracking_stats(self) -> Dict[str, Any]:
        """Get statistics about user change tracking.
        
        Returns:
            Dictionary with tracking statistics  
        """
        total_params = len(self._widget_to_param)
        user_changed_count = sum(1 for changed in self._user_changed_settings.values() if changed)
        
        return {
            'total_tracked_widgets': total_params,
            'user_changed_count': user_changed_count,
            'tracking_disabled': self._tracking_disabled
        }
    
    def get_config_default_value(self, param_name: str) -> Any:
        """Get the config default value for a parameter.
        
        Args:
            param_name: The parameter name
            
        Returns:
            The config default value for the parameter
        """
        try:
            from nk2dl.common.config import config
            
            # Map parameter names to config keys
            param_to_config_key = {
                'priority': 'submission.priority',
                'chunk_size': 'submission.chunk_size',
                'use_node_frame_list': 'submission.use_node_frame_list',
                'enable_auto_timeout': 'submission.enable_auto_timeout',
                'render_mode': 'submission.render_mode',
                'use_nuke_x': 'submission.use_nuke_x',
                'batch_mode': 'submission.batch_mode',
                'reload_plugins': 'submission.reload_plugins',
                'separate_tasks': 'submission.write_nodes_as_tasks',
                'separate_jobs': 'submission.write_nodes_as_separate_jobs',
                'render_order_dependencies': 'submission.render_order_dependencies',
                'pool': 'submission.pool',
                'group': 'submission.group',
                'threads': 'submission.threads',
                'stack_size': 'submission.stack_size',
                'ram_use': 'submission.ram_use',
                'use_gpu': 'submission.use_gpu',
                'gpu_override': 'submission.gpu_override',
                'concurrent_tasks': 'submission.concurrent_tasks',
                'limit_worker_tasks': 'submission.limit_worker_tasks',
                'limit_groups': 'submission.limit_groups',
                'job_name': 'submission.job_name_template',
                'comment': 'submission.comment_template',
                'department': 'submission.department'
            }
            
            config_key = param_to_config_key.get(param_name)
            if config_key:
                return config.get(config_key)
            
            # Handle special cases
            if param_name == 'frames_mode':
                return 'Global'
            elif param_name == 'task_timeout':
                return 0
            elif param_name == 'views_separate_jobs':
                return False
            elif param_name == 'secondary_pool':
                return ''
            elif param_name == 'machine_limit':
                return 0
            elif param_name == 'machine_deny_list':
                return False
            elif param_name == 'machine_list':
                return ''
            elif param_name == 'frames':
                # Dynamic frame range based on Nuke script
                return self._get_nuke_root_frame_range()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting config default for {param_name}: {e}")
            return None
    
    def _get_nuke_root_frame_range(self) -> str:
        """Get frame range from Nuke root node.
        
        Returns:
            Frame range in format "first-last"
        """
        try:
            import nuke
            first_frame = int(nuke.root().firstFrame())
            last_frame = int(nuke.root().lastFrame())
            return f"{first_frame}-{last_frame}"
        except (ImportError, AttributeError, Exception):
            return "1001-1100"


class WidgetChangeTrackingMixin:
    """Mixin class to add widget change tracking to views.
    
    This mixin provides methods to register widgets for change tracking
    and handle context menu reset functionality.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin (call from derived class __init__)."""
        super().__init__(*args, **kwargs)
        self.widget_change_tracker = WidgetChangeTracker()
        
        logger.debug(f"WidgetChangeTrackingMixin initialized for {self.__class__.__name__}")
    
    def register_widget_for_change_tracking(self, widget, param_name: str) -> None:
        """Register a widget for change tracking.
        
        Args:
            widget: The widget to track
            param_name: The parameter name this widget controls
        """
        self.widget_change_tracker.register_widget(widget, param_name)
        
        # Install context menu for reset functionality
        self._install_context_menu(widget, param_name)
        
        logger.debug(f"Registered widget for change tracking: {param_name}")
    
    def _install_context_menu(self, widget, param_name: str) -> None:
        """Install context menu with reset functionality on a widget.
        
        Args:
            widget: The widget to add context menu to
            param_name: The parameter name for reset functionality
        """
        try:
            # Store parameter name on widget for context menu access
            widget._nk2dl_param_name = param_name
            
            # Set context menu policy
            widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            
            # Connect context menu signal
            widget.customContextMenuRequested.connect(
                lambda pos: self._show_context_menu(widget, pos)
            )
            
            logger.debug(f"Installed context menu for widget: {param_name}")
            
        except Exception as e:
            logger.error(f"Error installing context menu for {param_name}: {e}")
    
    def _show_context_menu(self, widget, position) -> None:
        """Show context menu with reset option.
        
        Args:
            widget: The widget to show context menu for
            position: The position where the menu was requested
        """
        try:
            param_name = getattr(widget, '_nk2dl_param_name', None)
            if not param_name:
                return
            
            # Check if parameter is user-changed
            is_user_changed = self.widget_change_tracker.is_user_changed(param_name)
            
            # Create context menu
            menu = QtWidgets.QMenu(widget)
            
            # Add reset action
            reset_action = menu.addAction("Reset to Default")
            reset_action.setEnabled(is_user_changed)
            
            if is_user_changed:
                # Show what the default value would be
                default_value = self.widget_change_tracker.get_config_default_value(param_name)
                if default_value is not None:
                    reset_action.setText(f"Reset to Default ({default_value})")
            
            # Show menu
            action = menu.exec(widget.mapToGlobal(position))
            
            if action == reset_action and is_user_changed:
                self._reset_widget_to_default(widget, param_name)
                
        except Exception as e:
            logger.error(f"Error showing context menu: {e}")
    
    def _reset_widget_to_default(self, widget, param_name: str) -> None:
        """Reset a widget to its config default value.
        
        Args:
            widget: The widget to reset
            param_name: The parameter name
        """
        try:
            # Get config default value
            default_value = self.widget_change_tracker.get_config_default_value(param_name)
            if default_value is None:
                logger.warning(f"No default value found for parameter: {param_name}")
                return
            
            # Mark as reset in tracker (removes from user-changed tracking)
            self.widget_change_tracker.mark_as_reset_to_default(param_name)
            
            # Update the widget value
            self._set_widget_value(widget, default_value)
            
            # Update the settings model (this will trigger save to storage)
            self._update_model_with_reset_value(param_name, default_value)
            
            # Refresh visual indication to remove highlighting with slight delay
            # to ensure storage save completes first
            if hasattr(self, 'refresh_widget_visual_indication'):
                QtCore.QTimer.singleShot(50, lambda: self.refresh_widget_visual_indication(widget))
            
            logger.info(f"Reset {param_name} to default value: {default_value}")
            
        except Exception as e:
            logger.error(f"Error resetting widget {param_name}: {e}")
    
    def _set_widget_value(self, widget, value) -> None:
        """Set widget value based on widget type.
        
        Args:
            widget: The widget to update
            value: The value to set
        """
        try:
            if hasattr(widget, 'setValue'):
                # SpinBox, DoubleSpinBox, etc.
                widget.setValue(value)
            elif hasattr(widget, 'setChecked'):
                # CheckBox, RadioButton
                widget.setChecked(bool(value))
            elif hasattr(widget, 'setCurrentText'):
                # ComboBox
                widget.setCurrentText(str(value))
            elif hasattr(widget, 'setText'):
                # LineEdit, TextEdit
                widget.setText(str(value))
            else:
                logger.warning(f"Unknown widget type for value setting: {type(widget)}")
                
        except Exception as e:
            logger.error(f"Error setting widget value: {e}")
    
    def _update_model_with_reset_value(self, param_name: str, value) -> None:
        """Update the settings model with the reset value.
        
        Args:
            param_name: The parameter name
            value: The reset value
        """
        try:
            # Remove from settings model user-changed tracking
            if hasattr(self, 'settings_model'):
                self.settings_model.mark_as_reset_to_default(param_name)
            
            # Don't update the model value - it already has the correct default
            # Just trigger a manual save to update the storage YAML
            self._trigger_manual_save_to_storage()
                
        except Exception as e:
            logger.error(f"Error updating model with reset value: {e}")
    
    def _trigger_manual_save_to_storage(self) -> None:
        """Manually trigger a save to storage to update YAML after reset.
        
        This bypasses the normal signal system to avoid re-marking parameters as user-changed.
        """
        try:
            # Try to access the panel's storage save method directly
            # Walk up the parent hierarchy to find the main panel
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, '_on_settings_changed_save_to_storage'):
                    parent._on_settings_changed_save_to_storage()
                    logger.debug("Triggered manual save to storage after reset")
                    return
                parent = parent.parent()
            
            logger.warning("Could not find panel to trigger manual save to storage")
            
        except Exception as e:
            logger.error(f"Error triggering manual save to storage: {e}")
    
    def _on_user_changed_setting(self, param_name: str, value, setting_type: str = None) -> None:
        """Handle user changes to settings with tracking.
        
        Args:
            param_name: The parameter name
            value: The new value
            setting_type: 'job', 'machine', or 'extra' (optional, will be inferred if not provided)
        """
        try:
            # Mark as user-changed in tracker
            self.widget_change_tracker.mark_as_user_changed(param_name)
            
            # Infer setting type if not provided
            if setting_type is None:
                setting_type = self._infer_setting_type(param_name)
            
            # Update the model - this should be implemented by concrete views
            if hasattr(self, '_update_model_setting'):
                self._update_model_setting(param_name, value, setting_type)
            
            logger.debug(f"User changed {setting_type} setting: {param_name} = {value}")
            
        except Exception as e:
            logger.error(f"Error handling user changed setting: {e}")
    
    def _infer_setting_type(self, param_name: str) -> str:
        """Infer the setting type based on parameter name.
        
        Args:
            param_name: The parameter name
            
        Returns:
            'job', 'machine', or 'extra'
        """
        job_settings = ['priority', 'chunk_size', 'frames_mode', 'frames', 'use_node_frame_list',
                       'task_timeout', 'enable_auto_timeout', 'render_mode', 'use_nuke_x',
                       'batch_mode', 'reload_plugins', 'separate_tasks', 'separate_jobs',
                       'render_order_dependencies', 'views_separate_jobs']
        
        machine_settings = ['pool', 'secondary_pool', 'group', 'threads', 'stack_size',
                           'ram_use', 'use_gpu', 'gpu_override', 'concurrent_tasks',
                           'limit_worker_tasks', 'machine_limit', 'machine_deny_list',
                           'machine_list', 'limit_groups']
        
        extra_settings = ['job_name', 'comment', 'department']
        
        if param_name in job_settings:
            return 'job'
        elif param_name in machine_settings:
            return 'machine'
        elif param_name in extra_settings:
            return 'extra'
        else:
            logger.warning(f"Unknown parameter type, defaulting to 'extra': {param_name}")
            return 'extra'
    
    def disable_change_tracking(self) -> None:
        """Disable change tracking temporarily."""
        self.widget_change_tracker.disable_tracking()
    
    def enable_change_tracking(self) -> None:
        """Enable change tracking."""
        self.widget_change_tracker.enable_tracking()
    
    def get_change_tracking_stats(self) -> Dict[str, Any]:
        """Get change tracking statistics.
        
        Returns:
            Dictionary with tracking statistics
        """
        return self.widget_change_tracker.get_change_tracking_stats() 