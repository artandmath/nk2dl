# -*- coding: utf-8 -*-
"""Widget change tracking system for the nk2dl panel.

This module provides functionality to track which widgets have been explicitly
changed by users versus programmatically changed, enabling proper storage
behavior and visual indication.
"""

from typing import Dict, Any, Optional, Set
from ...common.logging import setup_logging

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
        
        Args:
            param_name: The parameter name to mark as reset
        """
        self._user_changed_settings[param_name] = False
        logger.debug(f"Marked parameter {param_name} as reset to default")
    
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


class WidgetChangeTrackingMixin:
    """Mixin class to add widget change tracking support to views.
    
    This mixin provides methods to register widgets for change tracking
    and manages the connection to the change tracking system.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin (call from derived class __init__)."""
        super().__init__(*args, **kwargs)
        self.change_tracker = WidgetChangeTracker()
        
        logger.debug(f"WidgetChangeTrackingMixin initialized for {self.__class__.__name__}")
    
    def register_widget_for_change_tracking(self, widget, param_name: str) -> None:
        """Register a widget for change tracking.
        
        Args:
            widget: The widget to track
            param_name: The parameter name this widget controls
        """
        self.change_tracker.register_widget(widget, param_name)
        logger.debug(f"Registered widget for change tracking: {param_name}")
    
    def mark_widget_as_user_changed(self, widget) -> None:
        """Mark a widget as user-changed.
        
        Args:
            widget: The widget to mark as user-changed
        """
        self.change_tracker.mark_widget_as_user_changed(widget)
    
    def mark_widget_as_reset(self, widget) -> None:
        """Mark a widget as reset to default.
        
        Args:
            widget: The widget to mark as reset
        """
        self.change_tracker.mark_widget_as_reset_to_default(widget)
    
    def get_user_changed_settings(self) -> Dict[str, bool]:
        """Get all user-changed settings.
        
        Returns:
            Dictionary of user-changed settings
        """
        return self.change_tracker.get_user_changed_settings()
    
    def disable_change_tracking(self) -> None:
        """Temporarily disable change tracking."""
        self.change_tracker.disable_tracking()
    
    def enable_change_tracking(self) -> None:
        """Re-enable change tracking."""
        self.change_tracker.enable_tracking()
    
    def get_change_tracking_stats(self) -> Dict[str, Any]:
        """Get change tracking statistics.
        
        Returns:
            Dictionary with tracking statistics
        """
        return self.change_tracker.get_stats() 