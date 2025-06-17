# -*- coding: utf-8 -*-
"""Settings model for managing job, machine, and extra settings data.

This module contains the SettingsModel class that handles all settings data management,
including default values, validation, persistence, and change notifications.
"""

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtCore
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtCore
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtCore
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtCore
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")


class SettingsModel(QtCore.QObject):
    """Model for managing job and machine settings data.
    
    This model handles the logic for job settings and machine settings, including:
    - Default values and validation
    - Settings persistence and retrieval
    - Change notifications
    - Settings validation
    """
    
    # Signals
    jobSettingsChanged = QtCore.Signal()
    machineSettingsChanged = QtCore.Signal()
    extraSettingsChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._job_settings = {}
        self._machine_settings = {}
        self._extra_settings = {}
        
        # Initialize with default values
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize settings with default values."""
        from ..constants import Settings, DefaultValues
        
        # Job Settings defaults
        self._job_settings = DefaultValues.JOB_DEFAULTS.copy()
        
        # Machine Settings defaults  
        self._machine_settings = DefaultValues.MACHINE_DEFAULTS.copy()
        
        # Extra Settings defaults
        self._extra_settings = DefaultValues.EXTRA_DEFAULTS.copy()
    
    # Job Settings methods
    def get_job_setting(self, key, default=None):
        """Get a job setting value.
        
        Args:
            key (str): Setting key
            default: Default value if key not found
            
        Returns:
            Value of the setting
        """
        return self._job_settings.get(key, default)
    
    def set_job_setting(self, key, value):
        """Set a job setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        old_value = self._job_settings.get(key)
        if old_value != value:
            self._job_settings[key] = value
            self.jobSettingsChanged.emit()
    
    def get_all_job_settings(self):
        """Get all job settings.
        
        Returns:
            dict: Copy of all job settings
        """
        return self._job_settings.copy()
    
    def set_all_job_settings(self, settings):
        """Set all job settings.
        
        Args:
            settings (dict): Job settings dictionary
        """
        if settings != self._job_settings:
            self._job_settings = settings.copy()
            self.jobSettingsChanged.emit()
    
    # Machine Settings methods
    def get_machine_setting(self, key, default=None):
        """Get a machine setting value.
        
        Args:
            key (str): Setting key
            default: Default value if key not found
            
        Returns:
            Value of the setting
        """
        return self._machine_settings.get(key, default)
    
    def set_machine_setting(self, key, value):
        """Set a machine setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        old_value = self._machine_settings.get(key)
        if old_value != value:
            self._machine_settings[key] = value
            self.machineSettingsChanged.emit()
    
    def get_all_machine_settings(self):
        """Get all machine settings.
        
        Returns:
            dict: Copy of all machine settings
        """
        return self._machine_settings.copy()
    
    def set_all_machine_settings(self, settings):
        """Set all machine settings.
        
        Args:
            settings (dict): Machine settings dictionary
        """
        if settings != self._machine_settings:
            self._machine_settings = settings.copy()
            self.machineSettingsChanged.emit()
    
    # Extra Settings methods
    def get_extra_setting(self, key, default=None):
        """Get an extra setting value.
        
        Args:
            key (str): Setting key
            default: Default value if key not found
            
        Returns:
            Value of the setting
        """
        return self._extra_settings.get(key, default)
    
    def set_extra_setting(self, key, value):
        """Set an extra setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        old_value = self._extra_settings.get(key)
        if old_value != value:
            self._extra_settings[key] = value
            self.extraSettingsChanged.emit()
    
    def get_all_extra_settings(self):
        """Get all extra settings.
        
        Returns:
            dict: Copy of all extra settings
        """
        return self._extra_settings.copy()
    
    def set_all_extra_settings(self, settings):
        """Set all extra settings.
        
        Args:
            settings (dict): Extra settings dictionary
        """
        if settings != self._extra_settings:
            self._extra_settings = settings.copy()
            self.extraSettingsChanged.emit()
    
    # Validation methods
    def validate_job_settings(self):
        """Validate all job settings.
        
        Returns:
            tuple: (is_valid, error_messages_list)
        """
        errors = []
        
        # Validate priority
        priority = self._job_settings.get('priority', 0)
        if not isinstance(priority, int) or priority < 0 or priority > 100:
            errors.append("Priority must be between 0 and 100")
        
        # Validate chunk size
        chunk_size = self._job_settings.get('chunk_size', 1)
        if not isinstance(chunk_size, int) or chunk_size < 1:
            errors.append("Chunk size must be 1 or greater")
        
        # Validate task timeout
        task_timeout = self._job_settings.get('task_timeout', 0)
        if not isinstance(task_timeout, int) or task_timeout < 0 or task_timeout > 999:
            errors.append("Task timeout must be between 0 and 999")
        
        # Validate frame range format
        frames = self._job_settings.get('frames', '')
        if frames and not self._is_valid_frame_range(frames):
            errors.append("Invalid frame range format")
        
        return len(errors) == 0, errors
    
    def validate_machine_settings(self):
        """Validate all machine settings.
        
        Returns:
            tuple: (is_valid, error_messages_list)
        """
        errors = []
        
        # Validate threads
        threads = self._machine_settings.get('threads', 1)
        if not isinstance(threads, int) or threads < 1 or threads > 64:
            errors.append("Threads must be between 1 and 64")
        
        # Validate RAM settings
        min_ram = self._machine_settings.get('min_ram', 0)
        max_ram = self._machine_settings.get('max_ram', 0)
        
        if not isinstance(min_ram, int) or min_ram < 0 or min_ram > 64:
            errors.append("Min RAM must be between 0 and 64 GB")
        
        if not isinstance(max_ram, int) or max_ram < 0 or max_ram > 512:
            errors.append("Max RAM must be between 0 and 512 GB")
        
        if min_ram > 0 and max_ram > 0 and min_ram > max_ram:
            errors.append("Min RAM cannot be greater than Max RAM")
        
        # Validate GPU device
        gpu_device = self._machine_settings.get('gpu_device', 0)
        if not isinstance(gpu_device, int) or gpu_device < 0 or gpu_device > 16:
            errors.append("GPU device must be between 0 and 16")
        
        # Validate concurrent tasks
        concurrent_tasks = self._machine_settings.get('concurrent_tasks', 1)
        if not isinstance(concurrent_tasks, int) or concurrent_tasks < 1 or concurrent_tasks > 64:
            errors.append("Concurrent tasks must be between 1 and 64")
        
        # Validate machine limit
        machine_limit = self._machine_settings.get('machine_limit', 0)
        if not isinstance(machine_limit, int) or machine_limit < 0 or machine_limit > 999:
            errors.append("Machine limit must be between 0 and 999")
        
        return len(errors) == 0, errors
    
    def _is_valid_frame_range(self, frame_range):
        """Basic validation for frame range format.
        
        Args:
            frame_range (str): Frame range string
            
        Returns:
            bool: True if format appears valid
        """
        if not frame_range.strip():
            return True  # Empty is valid
        
        # Basic pattern check for formats like "1001-2315", "1001", "1001,1005,1010-1020"
        import re
        pattern = r'^[\d\-,\s]+$'
        return bool(re.match(pattern, frame_range.strip()))
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self._initialize_defaults()
        self.jobSettingsChanged.emit()
        self.machineSettingsChanged.emit()
        self.extraSettingsChanged.emit()
    
    def export_settings(self):
        """Export all settings to a dictionary.
        
        Returns:
            dict: All settings organized by category
        """
        return {
            'job_settings': self._job_settings.copy(),
            'machine_settings': self._machine_settings.copy(),
            'extra_settings': self._extra_settings.copy()
        }
    
    def import_settings(self, settings_dict):
        """Import settings from a dictionary.
        
        Args:
            settings_dict (dict): Settings organized by category
        """
        changed = False
        
        if 'job_settings' in settings_dict:
            if settings_dict['job_settings'] != self._job_settings:
                self._job_settings = settings_dict['job_settings'].copy()
                self.jobSettingsChanged.emit()
                changed = True
        
        if 'machine_settings' in settings_dict:
            if settings_dict['machine_settings'] != self._machine_settings:
                self._machine_settings = settings_dict['machine_settings'].copy()
                self.machineSettingsChanged.emit()
                changed = True
        
        if 'extra_settings' in settings_dict:
            if settings_dict['extra_settings'] != self._extra_settings:
                self._extra_settings = settings_dict['extra_settings'].copy()
                self.extraSettingsChanged.emit()
                changed = True
        
        return changed 