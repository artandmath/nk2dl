# -*- coding: utf-8 -*-
"""Storage visual indication system for the nk2dl panel.

This module provides functionality to visually indicate which widgets have user-changed values
by applying highlight colors to widgets that have been explicitly modified by the user and
persisted to the storage system.
"""

from typing import Dict, Any, Optional, Set, List
from ...common.logging import setup_logging

logger = setup_logging('nk2dl.gui.panel.storage_visual_indication')


class StorageVisualIndicationManager:
    """Manager for applying visual indication to widgets based on user-changed storage state.
    
    This class tracks which widgets have user-changed stored values and applies/removes
    highlights accordingly. Only widgets with explicitly user-modified values will be highlighted.
    """
    
    def __init__(self, storage_instance=None):
        """Initialize the visual indication manager.
        
        Args:
            storage_instance: Optional NodeSettingsStorage instance
        """
        self.storage_instance = storage_instance
        self.tracked_widgets = {}  # Dict[widget_id, (widget, param_name)]
        self.widget_states = {}   # Dict[widget_id, is_stored]
        self.widget_counter = 0
        
        logger.debug("StorageVisualIndicationManager initialized")
    
    def set_storage_instance(self, storage_instance):
        """Set the storage instance for checking stored values.
        
        Args:
            storage_instance: NodeSettingsStorage instance
        """
        self.storage_instance = storage_instance
        logger.debug("Storage instance set for visual indication")
    
    def register_widget(self, widget, param_name):
        """Register a widget for visual indication tracking.
        
        Args:
            widget: The widget to track (must have set_highlighted method)
            param_name (str): The parameter name for storage lookup
            
        Returns:
            str: Widget ID for reference
        """
        widget_id = f"widget_{self.widget_counter}"
        self.widget_counter += 1
        
        self.tracked_widgets[widget_id] = (widget, param_name)
        self.widget_states[widget_id] = False
        
        logger.debug(f"Registered widget {widget_id} for parameter {param_name}")
        return widget_id
    
    def unregister_widget(self, widget_id):
        """Unregister a widget from tracking.
        
        Args:
            widget_id (str): The widget ID to remove
        """
        if widget_id in self.tracked_widgets:
            del self.tracked_widgets[widget_id]
            del self.widget_states[widget_id]
            logger.debug(f"Unregistered widget {widget_id}")
    
    def refresh_all_widgets(self):
        """Refresh the visual indication for all tracked widgets."""
        if not self.storage_instance:
            logger.debug("No storage instance available for refresh")
            return
        
        try:
            # Get only user-changed settings (this is what should be highlighted)
            user_changed_settings = self.storage_instance.load_user_changed_settings()
            
            updated_count = 0
            
            for widget_id, (widget, param_name) in self.tracked_widgets.items():
                if not widget or not hasattr(widget, 'set_highlighted'):
                    continue
                
                # Check if this parameter has a user-changed stored value
                is_stored = self._is_parameter_stored(param_name, user_changed_settings)
                
                # Determine if widget is editable
                editable = True
                if hasattr(widget, 'isEnabled'):
                    editable = widget.isEnabled()
                
                # Update widget highlight state
                if self.widget_states[widget_id] != is_stored:
                    if is_stored and editable:
                        widget.set_highlighted(True)
                    else:
                        widget.set_highlighted(False)
                    self.widget_states[widget_id] = is_stored
                    updated_count += 1
                    
                    logger.debug(f"Updated widget {widget_id} ({param_name}) highlight: {is_stored}")
            
            logger.debug(f"Refreshed {updated_count} widgets out of {len(self.tracked_widgets)} tracked")
            
        except Exception as e:
            logger.error(f"Error refreshing visual indication: {e}", exc_info=True)
    
    def refresh_widget(self, widget_id):
        """Refresh the visual indication for a specific widget.
        
        Args:
            widget_id (str): The widget ID to refresh
        """
        if widget_id not in self.tracked_widgets:
            logger.warning(f"Widget {widget_id} not found in tracked widgets")
            return
        
        if not self.storage_instance:
            logger.debug("No storage instance available for widget refresh")
            return
        
        try:
            widget, param_name = self.tracked_widgets[widget_id]
            
            if not widget or not hasattr(widget, 'set_highlighted'):
                logger.warning(f"Widget {widget_id} is invalid or doesn't support highlighting")
                return
            
            # Get only user-changed settings (this is what should be highlighted)
            user_changed_settings = self.storage_instance.load_user_changed_settings()
            
            # Check if this parameter has a user-changed stored value
            is_stored = self._is_parameter_stored(param_name, user_changed_settings)
            
            # Update widget highlight state
            if self.widget_states[widget_id] != is_stored:
                widget.set_highlighted(is_stored)
                self.widget_states[widget_id] = is_stored
                logger.debug(f"Updated widget {widget_id} ({param_name}) highlight: {is_stored}")
            
        except Exception as e:
            logger.error(f"Error refreshing widget {widget_id}: {e}", exc_info=True)
    
    def _is_parameter_stored(self, param_name, user_changed_settings):
        """Check if a parameter has a user-changed stored value.
        
        Args:
            param_name (str): The parameter name
            user_changed_settings (dict): The user-changed settings dictionary
            
        Returns:
            bool: True if the parameter has a user-changed stored value
        """
        if not user_changed_settings:
            return False
        
        # Check if parameter exists in user-changed settings
        return param_name in user_changed_settings and user_changed_settings[param_name] is not None
    
    def get_tracked_widget_count(self):
        """Get the number of tracked widgets.
        
        Returns:
            int: Number of tracked widgets
        """
        return len(self.tracked_widgets)
    
    def get_highlighted_widget_count(self):
        """Get the number of currently highlighted widgets.
        
        Returns:
            int: Number of highlighted widgets
        """
        return sum(1 for is_highlighted in self.widget_states.values() if is_highlighted)


class StorageVisualIndicationMixin:
    """Mixin class to add storage visual indication support to views.
    
    This mixin provides methods to register widgets for visual indication
    and manages the connection to the storage system.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin (call from derived class __init__)."""
        super().__init__(*args, **kwargs)
        self.visual_indication_manager = StorageVisualIndicationManager()
        self.widget_ids = {}  # Maps widget to widget_id
        
        logger.debug(f"StorageVisualIndicationMixin initialized for {self.__class__.__name__}")
    
    def register_widget_for_visual_indication(self, widget, param_name):
        """Register a widget for visual indication.
        
        Args:
            widget: The widget to track
            param_name (str): The parameter name for storage lookup
        """
        if not hasattr(widget, 'set_highlighted'):
            logger.warning(f"Widget {widget} doesn't support highlighting")
            return
        
        widget_id = self.visual_indication_manager.register_widget(widget, param_name)
        self.widget_ids[widget] = widget_id
        
        logger.debug(f"Registered widget for visual indication: {param_name}")
    
    def set_storage_instance(self, storage_instance):
        """Set the storage instance for the visual indication manager.
        
        Args:
            storage_instance: NodeSettingsStorage instance
        """
        self.visual_indication_manager.set_storage_instance(storage_instance)
        logger.debug("Storage instance set for visual indication")
    
    def refresh_visual_indications(self):
        """Refresh all visual indications."""
        self.visual_indication_manager.refresh_all_widgets()
        logger.debug("Refreshed all visual indications")
    
    def refresh_widget_visual_indication(self, widget):
        """Refresh visual indication for a specific widget.
        
        Args:
            widget: The widget to refresh
        """
        if widget in self.widget_ids:
            widget_id = self.widget_ids[widget]
            self.visual_indication_manager.refresh_widget(widget_id)
    
    def get_visual_indication_stats(self):
        """Get statistics about visual indication.
        
        Returns:
            dict: Dictionary with tracking statistics
        """
        return {
            'tracked_widgets': self.visual_indication_manager.get_tracked_widget_count(),
            'highlighted_widgets': self.visual_indication_manager.get_highlighted_widget_count()
        } 