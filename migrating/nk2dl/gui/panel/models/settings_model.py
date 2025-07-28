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

from ....common.logging import setup_logging

logger = setup_logging('nk2dl.gui.panel.models.settings_model')


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
        
        # Initialize user change tracking
        self._user_changed_settings = {}
        self._programmatic_change_flag = False
        
        # Initialize with default values
        self._initialize_defaults()
        
        logger.debug("SettingsModel initialized with change tracking")
    
    def _initialize_defaults(self):
        """Initialize settings with default values from config system."""
        from nk2dl.common.config import config
        
        # Job Settings defaults from config system
        self._job_settings = {
            'priority': config.get('submission.priority', 50),
            'chunk_size': config.get('submission.chunk_size', 10),
            'frames_mode': 'Global',  # UI-specific setting
            'frames': self._get_initial_frame_range(),  # Dynamic based on mode
            'custom_frames': None,  # Store custom frame range separately
            'use_node_frame_list': config.get('submission.use_node_frame_list', False),
            'task_timeout': 0,        # UI-specific setting
            'enable_auto_timeout': config.get('submission.enable_auto_timeout', False),
            'render_mode': config.get('submission.render_mode', 'full'),
            'use_nuke_x': config.get('submission.use_nuke_x', False),
            'separate_tasks': config.get('submission.write_nodes_as_tasks', False),
            'separate_jobs': config.get('submission.write_nodes_as_separate_jobs', False),
            'render_order_dependencies': config.get('submission.render_order_dependencies', False),
            'views_separate_jobs': False,  # UI-specific setting
            # New job settings from nuke.submission
            'submit_suspended': config.get('submission.submit_suspended', False),
            'continue_on_error': config.get('submission.continue_on_error', False),
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
            # Build job parameters
            'submit_script_as_auxiliary_file': config.get('submission.submit_script_as_auxiliary_file', None),
            'submission_is_build_job': config.get('submission.submission_is_build_job', False),
            'build_job_name': config.get('submission.build_job_name', None),
            'pre_build_job_script': config.get('submission.pre_build_job_script', None),
            'post_build_job_script': config.get('submission.post_build_job_script', None),
            'build_job_as_auxiliary_file': config.get('submission.build_job_as_auxiliary_file', None),
            'delete_build_job_script': config.get('submission.delete_build_job_script', None),
            # Script copying parameters
            'copy_script': config.get('submission.copy_script', None),
            'copy_script_path': config.get('submission.copy_script_path', None),
            'submit_copied_script': config.get('submission.submit_copied_script', None),
            # ScriptJob parameters
            'script_job_script_path': config.get('submission.script_job_script_path', None),
            # Job info parameters
            'extra_info': config.get('submission.extra_info', None),
            'on_job_complete': config.get('submission.on_job_complete', None),
            'pre_job_script': config.get('submission.pre_job_script', None),
            'post_job_script': config.get('submission.post_job_script', None),
            'pre_task_script': config.get('submission.pre_task_script', None),
            'post_task_script': config.get('submission.post_task_script', None),
            # Environment variables parameters
            'use_current_environment': config.get('submission.use_current_environment', False),
            'environment_keys': config.get('submission.environment_keys', None),
            'environment': config.get('submission.environment', None),
            'omit_environment_keys': config.get('submission.omit_environment_keys', None),
            # Plugin settings (moved from job settings)
            'batch_mode': config.get('submission.batch_mode', True),
            'reload_plugins': config.get('submission.reload_plugins', False),
            'render_settings_from_metadata': config.get('submission.render_settings_from_metadata', False),
            # Job dependencies (moved from job settings)
            'job_dependencies': config.get('submission.job_dependencies', None),
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
    
    def set_job_setting(self, key, value, user_changed=True):
        """Set a job setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
            user_changed (bool): Whether this change was made by user (default: True)
        """
        old_value = self._job_settings.get(key)
        if old_value != value:
            self._job_settings[key] = value
            
            # Track user changes if not programmatic
            if user_changed and not self._programmatic_change_flag:
                self._user_changed_settings[key] = True
                logger.debug(f"Marked job setting {key} as user-changed")
            
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
    
    def set_machine_setting(self, key, value, user_changed=True):
        """Set a machine setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
            user_changed (bool): Whether this change was made by user (default: True)
        """
        old_value = self._machine_settings.get(key)
        if old_value != value:
            self._machine_settings[key] = value
            
            # Track user changes if not programmatic
            if user_changed and not self._programmatic_change_flag:
                self._user_changed_settings[key] = True
                logger.debug(f"Marked machine setting {key} as user-changed")
            
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
    
    def set_extra_setting(self, key, value, user_changed=True):
        """Set an extra setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
            user_changed (bool): Whether this change was made by user (default: True)
        """
        old_value = self._extra_settings.get(key)
        if old_value != value:
            self._extra_settings[key] = value
            
            # Track user changes if not programmatic
            if user_changed and not self._programmatic_change_flag:
                self._user_changed_settings[key] = True
                logger.debug(f"Marked extra setting {key} as user-changed")
            
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
    
    # Frame range handling methods
    def _get_initial_frame_range(self):
        """Get the initial frame range based on the default frames mode.
        
        Returns:
            str: Frame range string
        """
        return self._get_frame_range_for_mode('Global')
    
    def _get_frame_range_for_mode(self, mode):
        """Get frame range string for a specific mode.
        
        Args:
            mode (str): Frame mode ('Global', 'Input', 'First Middle Last', 'Hero Frames', 'Custom')
            
        Returns:
            str: Frame range string
        """
        if mode == 'Global':
            return self._get_nuke_root_frame_range()
        elif mode == 'Input':
            return 'input'
        elif mode == 'First Middle Last':
            return 'f,m,l'
        elif mode == 'Hero Frames':
            return 'hero'
        elif mode == 'Custom':
            # Return the stored custom value or global frame range if no custom value
            custom_frames = self._job_settings.get('custom_frames')
            return custom_frames if custom_frames is not None else self._get_nuke_root_frame_range()
        else:
            return self._get_nuke_root_frame_range()
    
    def _get_nuke_root_frame_range(self):
        """Get frame range from Nuke root node.
        
        Returns:
            str: Frame range in format "first-last"
        """
        try:
            # Try to import nuke and get frame range
            import nuke
            first_frame = int(nuke.root().firstFrame())
            last_frame = int(nuke.root().lastFrame())
            return f"{first_frame}-{last_frame}"
        except (ImportError, AttributeError, Exception):
            # Fallback if nuke is not available or there's an error
            return "1001-1100"
    
    def update_frame_range_for_mode(self, mode):
        """Update the frame range based on the selected mode.
        
        Args:
            mode (str): Frame mode selected
        """
        new_frame_range = self._get_frame_range_for_mode(mode)
        # Only update the frames setting, don't overwrite custom_frames
        self.set_job_setting('frames', new_frame_range, user_changed=False)
    
    def set_custom_frame_range(self, frame_range):
        """Set a custom frame range value.
        
        This method should only be called when the user edits the frame range
        while the dropdown is set to 'Custom'.
        
        Args:
            frame_range (str): Custom frame range string
        """
        # Store the custom value separately
        self._job_settings['custom_frames'] = frame_range
        # Also update the current frames value
        self.set_job_setting('frames', frame_range)
    
    def get_custom_frame_range(self):
        """Get the stored custom frame range value.
        
        Returns:
            str: Custom frame range string or None if not set
        """
        return self._job_settings.get('custom_frames')
    
    def is_frame_range_editable(self, mode):
        """Check if frame range should be editable for given mode.
        
        Args:
            mode (str): Frame mode
            
        Returns:
            bool: True if editable
        """
        return mode == 'Custom'

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
        
        # Validate new job settings
        
        # Validate boolean settings
        boolean_job_settings = [
            'render_settings_from_metadata',
            'submit_suspended', 
            'continue_on_error'
        ]
        for setting in boolean_job_settings:
            value = self._job_settings.get(setting, False)
            if not isinstance(value, bool):
                errors.append(f"{setting} must be a boolean value")
        
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
    
    def validate_extra_settings(self):
        """Validate all extra settings.
        
        Returns:
            tuple: (is_valid, error_messages_list)
        """
        errors = []
        
        # Validate boolean settings
        boolean_extra_settings = [
            'submit_script_as_auxiliary_file',
            'submission_is_build_job',
            'build_job_as_auxiliary_file',
            'delete_build_job_script',
            'copy_script',
            'submit_copied_script',
            'use_current_environment'
        ]
        for setting in boolean_extra_settings:
            value = self._extra_settings.get(setting, None)
            if value is not None and not isinstance(value, bool):
                errors.append(f"{setting} must be a boolean value")
        
        # Validate string settings
        string_extra_settings = [
            'build_job_name',
            'script_job_script_path',
            'on_job_complete'
        ]
        for setting in string_extra_settings:
            value = self._extra_settings.get(setting, None)
            if value is not None and not isinstance(value, str):
                errors.append(f"{setting} must be a string value")
        
        # Validate list settings
        list_extra_settings = [
            'extra_info',
            'environment_keys',
            'omit_environment_keys'
        ]
        for setting in list_extra_settings:
            value = self._extra_settings.get(setting, None)
            if value is not None and not isinstance(value, list):
                errors.append(f"{setting} must be a list value")
        
        # Validate dict settings
        dict_extra_settings = ['environment']
        for setting in dict_extra_settings:
            value = self._extra_settings.get(setting, None)
            if value is not None and not isinstance(value, dict):
                errors.append(f"{setting} must be a dictionary value")
        
        # Validate job dependencies format
        job_dependencies = self._extra_settings.get('job_dependencies', None)
        if job_dependencies and not self._is_valid_job_dependencies(job_dependencies):
            errors.append("Job dependencies must be comma or space separated job IDs")
        
        # Validate script path settings
        script_path_settings = [
            'pre_build_job_script',
            'post_build_job_script',
            'copy_script_path',
            'pre_job_script',
            'post_job_script',
            'pre_task_script',
            'post_task_script'
        ]
        for setting in script_path_settings:
            value = self._extra_settings.get(setting, None)
            if value is not None:
                if isinstance(value, str) and not self._is_valid_script_path(value):
                    errors.append(f"{setting} must be a valid script path")
                elif isinstance(value, list) and not all(self._is_valid_script_path(v) for v in value if isinstance(v, str)):
                    errors.append(f"{setting} must contain valid script paths")
        
        return len(errors) == 0, errors
    
    def _is_valid_job_dependencies(self, job_dependencies):
        """Validate job dependencies format.
        
        Args:
            job_dependencies (str): Job dependencies string
            
        Returns:
            bool: True if format appears valid
        """
        if not job_dependencies.strip():
            return True  # Empty is valid
        
        # Basic pattern check for comma or space separated job IDs
        import re
        pattern = r'^[\d\s,]+$'
        return bool(re.match(pattern, job_dependencies.strip()))
    
    def _is_valid_script_path(self, script_path):
        """Validate script path format.
        
        Args:
            script_path (str): Script path string
            
        Returns:
            bool: True if format appears valid
        """
        if not script_path.strip():
            return True  # Empty is valid
        
        # Basic validation - should not contain invalid characters
        import re
        invalid_chars = r'[<>:"|?*]'
        return not re.search(invalid_chars, script_path)
    
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
    
    # User change tracking methods
    def mark_as_user_changed(self, param_name: str) -> None:
        """Mark a parameter as user-changed.
        
        Args:
            param_name: The parameter name to mark as user-changed
        """
        self._user_changed_settings[param_name] = True
        logger.debug(f"Marked parameter {param_name} as user-changed")
    
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
    
    def is_user_changed(self, param_name: str) -> bool:
        """Check if a parameter has been changed by the user.
        
        Args:
            param_name: The parameter name to check
            
        Returns:
            True if the parameter has been changed by the user
        """
        return self._user_changed_settings.get(param_name, False)
    
    def get_user_changed_settings(self) -> dict:
        """Get only the settings that have been changed by the user.
        
        Returns:
            Dictionary containing only user-changed settings with their values
        """
        user_changed = {}
        
        # Get user-changed job settings
        for key, value in self._job_settings.items():
            if self.is_user_changed(key):
                user_changed[key] = value
        
        # Get user-changed machine settings
        for key, value in self._machine_settings.items():
            if self.is_user_changed(key):
                user_changed[key] = value
        
        # Get user-changed extra settings
        for key, value in self._extra_settings.items():
            if self.is_user_changed(key):
                user_changed[key] = value
        
        return user_changed
    
    def get_user_changed_param_names(self) -> set:
        """Get set of parameter names that have been changed by the user.
        
        Returns:
            Set of parameter names that are user-changed
        """
        return {param for param, changed in self._user_changed_settings.items() if changed}
    
    def disable_user_change_tracking(self) -> None:
        """Temporarily disable user change tracking.
        
        This is useful when making programmatic changes that shouldn't
        be tracked as user changes.
        """
        self._programmatic_change_flag = True
        logger.debug("User change tracking disabled")
    
    def enable_user_change_tracking(self) -> None:
        """Re-enable user change tracking."""
        self._programmatic_change_flag = False
        logger.debug("User change tracking enabled")
    
    def is_user_change_tracking_disabled(self) -> bool:
        """Check if user change tracking is currently disabled.
        
        Returns:
            True if tracking is disabled
        """
        return self._programmatic_change_flag
    
    def clear_all_user_changes(self) -> None:
        """Clear all user change tracking.
        
        This resets all parameters to not user-changed state.
        """
        self._user_changed_settings.clear()
        logger.debug("Cleared all user change tracking")
    
    def set_user_changed_settings(self, user_changed_settings: dict) -> None:
        """Set settings that have been marked as user-changed.
        
        This method is used when loading settings from storage to restore
        which parameters were user-changed.
        
        Args:
            user_changed_settings: Dictionary of parameter names and values that are user-changed
        """
        # Disable tracking during this operation
        self.disable_user_change_tracking()
        
        try:
            # Set the values in the appropriate settings dictionaries
            for param_name, value in user_changed_settings.items():
                # Determine which settings category this parameter belongs to
                if param_name in self._job_settings:
                    self.set_job_setting(param_name, value, user_changed=False)
                elif param_name in self._machine_settings:
                    self.set_machine_setting(param_name, value, user_changed=False)
                elif param_name in self._extra_settings:
                    self.set_extra_setting(param_name, value, user_changed=False)
                
                # Mark as user-changed
                self._user_changed_settings[param_name] = True
                
        finally:
            # Re-enable tracking
            self.enable_user_change_tracking()
        
        logger.debug(f"Set {len(user_changed_settings)} user-changed settings")
    
    def get_change_tracking_stats(self) -> dict:
        """Get statistics about user change tracking.
        
        Returns:
            Dictionary with tracking statistics
        """
        total_params = len(self._job_settings) + len(self._machine_settings) + len(self._extra_settings)
        user_changed_count = sum(1 for changed in self._user_changed_settings.values() if changed)
        
        return {
            'total_params': total_params,
            'user_changed_count': user_changed_count,
            'tracking_disabled': self._programmatic_change_flag
        } 