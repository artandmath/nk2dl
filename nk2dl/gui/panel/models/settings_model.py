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
        """Initialize settings with default values from config system."""
        from nk2dl.common.config import config
        
        # Job Settings defaults from config system
        self._job_settings = {
            'priority': config.get('submission.priority', 50),
            'chunk_size': config.get('submission.chunk_size', 10),
            'frames_mode': 'Global',  # UI-specific setting
            'frames': '1001-2315',    # UI-specific setting
            'use_node_frame_list': config.get('submission.use_node_frame_list', False),
            'task_timeout': 0,        # UI-specific setting
            'enable_auto_timeout': config.get('submission.enable_auto_timeout', False),
            'render_mode': config.get('submission.render_mode', 'full'),
            'use_nuke_x': config.get('submission.use_nuke_x', False),
            'batch_mode': config.get('submission.batch_mode', True),
            'reload_plugins': config.get('submission.reload_plugins', False),
            'separate_tasks': config.get('submission.write_nodes_as_tasks', False),
            'separate_jobs': config.get('submission.write_nodes_as_separate_jobs', False),
            'views_separate_jobs': False,  # UI-specific setting
        }
        
        # Machine Settings defaults from config system
        self._machine_settings = {
            'pool': config.get('submission.pool', 'nuke'),
            'secondary_pool': '',     # UI-specific setting
            'group': config.get('submission.group', 'none'),
            'threads': config.get('submission.threads', 0),
            'stack_size': config.get('submission.stack_size', 0),
            'ram_use': config.get('submission.ram_use', 0),
            'use_gpu': config.get('submission.use_gpu', False),
            'gpu_override': config.get('submission.gpu_override', ''),
            'concurrent_tasks': config.get('submission.concurrent_tasks', 1),
            'limit_worker_tasks': config.get('submission.limit_worker_tasks', False),
            'machine_limit': 0,       # UI-specific setting
            'machine_deny_list': False,  # UI-specific setting
            'machine_list': '',       # UI-specific setting
            'limit_groups': config.get('submission.limit_groups', ''),
        }
        
        # Extra Settings defaults from config system
        self._extra_settings = {
            'job_name': config.get('submission.job_name_template', '{batch} / {write} / {file}'),
            'comment': config.get('submission.comment_template', ''),
            'department': config.get('submission.department', ''),
        }
    
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
        stack_size = self._machine_settings.get('stack_size', 0)
        ram_use = self._machine_settings.get('ram_use', 0)
        
        if not isinstance(stack_size, int) or stack_size < 0 or stack_size > 64:
            errors.append("Stack size must be between 0 and 64 GB")
        
        if not isinstance(ram_use, int) or ram_use < 0 or ram_use > 512:
            errors.append("RAM use must be between 0 and 512 GB")
        
        if stack_size > 0 and ram_use > 0 and stack_size > ram_use:
            errors.append("Stack size cannot be greater than RAM use")
        
        # Validate GPU override
        gpu_override = self._machine_settings.get('gpu_override', '')
        if gpu_override:
            try:
                gpu_id = int(gpu_override) if isinstance(gpu_override, str) else gpu_override
                if gpu_id < 0 or gpu_id > 16:
                    errors.append("GPU override must be between 0 and 16")
            except (ValueError, TypeError):
                errors.append("GPU override must be a valid GPU ID")
        
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