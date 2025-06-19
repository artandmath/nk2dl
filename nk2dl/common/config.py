"""Configuration system for nk2dl.

This module handles loading, validating and accessing configuration settings
from YAML files and environment variables.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import importlib.resources
import inspect

# Get module-level logger with fallback format
# Use basic logger initially to avoid circular import, will be upgraded later
try:
    from .logging import get_nk2dl_logger
    logger = get_nk2dl_logger(__name__)
except ImportError:
    # Fallback to standard logger during bootstrap
    import logging
    logger = logging.getLogger(__name__)

# Configure a fallback formatter in case setup_logging isn't called
if not logger.handlers:
    # Create a basic handler with the time-only format (matching the new standard)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

# Flag to track if we need to reinitialize the logger with proper setup
_logger_needs_setup = True

# Track if debug config info has been shown (only show once)
_debug_config_shown = False

class ConfigError(Exception):
    """Base exception for configuration related errors."""
    pass

class Config:
    """Configuration manager for nk2dl.
    
    Handles loading and accessing configuration from YAML files and environment variables.
    Configuration is loaded in the following order (later sources override earlier ones):
    1. Default configuration
    2. Project configuration file (from NK2DL_CONFIG or config.yaml in nk2dl module root)
    3. Environment variables (NK2DL_*)
    4. User configuration file (~/.nuke/nk2dl/config.yaml)
    """
    
    # Default paths for configuration files - using .nuke directory
    USER_CONFIG_PATH = Path.home() / '.nuke' / 'nk2dl' / 'config.yaml'
    
    # Get the module directory path for finding the config
    try:
        import nk2dl
        MODULE_DIR = Path(importlib.resources.files(nk2dl))
        GLOBAL_CONFIG_PATH = MODULE_DIR / 'config.yaml'
    except (ImportError, TypeError):
        # Fall back to relative path if module lookup fails
        MODULE_DIR = Path(__file__).parent.parent
        GLOBAL_CONFIG_PATH = MODULE_DIR / 'config.yaml'
    
    # PROJECT_CONFIG_PATH is fetched from the env var NK2DL_CONFIG if it exists,
    # otherwise defaults to GLOBAL_CONFIG_PATH
    PROJECT_CONFIG_PATH = GLOBAL_CONFIG_PATH
    
    # Special environment variables that should not be processed as config settings
    SPECIAL_ENV_VARS = {'NK2DL_CONFIG'}
    
    DEFAULT_CONFIG = {
        'deadline': {
            # Web service configuration
            'use_web_service': False,  # Whether to use web service or command-line
            'host': 'localhost',
            'port': 8081,
            'ssl': False,
            'ssl_cert': None,  # Path to SSL certificate
            'timeout': 1, #seconds
            'commandline_on_fail': True,  # Whether to use command-line if web service fails
            
            # Command-line configuration
            'command_path': None,  # Will be auto-detected from DEADLINE_PATH
            'repository_path': None,  # Will be auto-detected using deadlinecommand
        },
        'logging': {
            'level': 'INFO',
            'file': None,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'submission': {
            'priority': 50,
            'pool': 'nuke',
            'group': 'none',
            'chunk_size': 10,
            'concurrent_tasks': 1,
            'threads': 0,
            'ram_use': 0,
            'stack_size': 0,
            'batch_name_template': '{nukescript}',
            'job_name_template': '{batch} / {write} / {file}',
            'build_job_name_template': '{buildjob} >> {nukescript}',
            'comment_template': '',
            'render_mode': 'full',
            'write_nodes_as_tasks': False,
            'write_nodes_as_separate_jobs': False,
            'render_order_dependencies': False,
            'enforce_render_order': True,
            'use_node_frame_list': False,
            'use_nuke_x': False,
            'batch_mode': True,
            'use_gpu': False,
            'performance_profiler': False,
            'performance_profiler_path': '',
            'continue_on_error': False,
            'reload_plugins': False,
            'use_proxy': False,
            'submit_writes_alphabetically': False,
            'submit_writes_in_render_order': False,
            'copy_script': False,
            'submit_copied_script': False,
            'submit_script_as_auxiliary_file': False,
            'use_current_environment': False,
            'environment_keys': [],
            'environment': {},
            'omit_environment_keys': [],
            'script_copy_path': '{outdir}/.farm/{nkstem}.nk',
            
            # Build job settings
            'build_job_script_path': None,
            'build_job_as_auxiliary_file': True,
            'delete_build_job_script': True,
            
            # Machine list options
            'machine_allow_list': None,
            'machine_deny_list': None,
            'machine_limit': None,
            
            # Script hook options
            'pre_job_script': None,
            'post_job_script': None,
            'pre_task_script': None,
            'post_task_script': None,
            
            # Environment variables
            'department': '',
            
            # Write node types
            'custom_write_classes': [],  # Additional custom write node types (Write and DeepWrite are always included)
        },
        'panel': {
            # Panel configuration for UI control visibility, disabled state, and default values
            # This section allows studio administrators to customize the panel behavior
        }
    }
    
    def __init__(self, project_config: Optional[str] = None, user_config: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            project_config: Optional path to project configuration file
            user_config: Optional path to user configuration file
        """
        logger.debug("Initializing configuration")
        self._config: Dict[str, Any] = {}
        self._project_config_path = self._get_project_config_path(project_config)
        logger.debug(f"Project config path: {self._project_config_path}")
        
        # Set up user config path
        self._user_config_path = Path(user_config) if user_config else self.USER_CONFIG_PATH
        logger.debug(f"User config path: {self._user_config_path}")
        self.load_config()
    
    def _get_project_config_path(self, project_config: Optional[str] = None) -> Path:
        """Get the project configuration file path.
        
        The path is determined in the following order:
        1. Explicitly provided project_config parameter
        2. NK2DL_CONFIG environment variable
        3. Default project config path (config.yaml in the nk2dl module directory)
        
        Args:
            project_config: Optional explicit path to project config
            
        Returns:
            Path to project configuration file
        """
        if project_config:
            logger.debug(f"Using explicitly provided project config: {project_config}")
            return Path(project_config)
        
        # Check environment variable
        env_config = os.environ.get('NK2DL_CONFIG')
        if env_config:
            logger.debug(f"Using project config from NK2DL_CONFIG: {env_config}")
            return Path(env_config)
        
        logger.debug(f"Using default project config path: {self.PROJECT_CONFIG_PATH}")
        return self.PROJECT_CONFIG_PATH
    
    def load_config(self) -> None:
        """Load configuration from all sources."""
        # Start with default config
        logger.debug("=== Loading nk2dl Configuration ===")
        logger.debug("Starting with default configuration")
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Load project config first
        logger.debug(f"1. Checking project config: {self._project_config_path}")
        project_config = self._load_yaml_file(self._project_config_path)
        if project_config:
            logger.debug(f"✓ Project config loaded from: {self._project_config_path}")
            logger.debug(f"Project config sections: {list(project_config.keys())}")
            logger.debug(f"Project config contents: {project_config}")
            self._update_config(project_config)
        else:
            logger.debug(f"✗ No project config found at: {self._project_config_path}")
        
        # Load environment variables second
        logger.debug("2. Loading environment variables (NK2DL_*)")
        env_count = self._load_env_vars()
        if env_count > 0:
            logger.debug(f"✓ Loaded {env_count} environment variables")
        else:
            logger.debug("✗ No NK2DL_* environment variables found")
            
        # Load user config last (now has highest priority)
        logger.debug(f"3. Checking user config: {self._user_config_path}")
        user_config = self._load_yaml_file(self._user_config_path)
        if user_config:
            logger.debug(f"✓ User config loaded from: {self._user_config_path}")
            logger.debug(f"User config sections: {list(user_config.keys())}")
            logger.debug(f"User config contents: {user_config}")
            self._update_config(user_config)
            user_config_loaded = True
            user_config_path_used = self._user_config_path
        else:
            logger.debug(f"✗ No user config found at: {self._user_config_path}")
            logger.debug(f"To create a user config, place config.yaml at: {self.USER_CONFIG_PATH}")
            user_config_loaded = False
            user_config_path_used = None
            
        # Log final config summary - moved to DEBUG level
        logger.debug("=== Configuration Summary ===")
        logger.debug(f"Sources loaded:")
        logger.debug(f"  - Default config: ✓")
        logger.debug(f"  - Project config: {'✓' if project_config else '✗'} {self._project_config_path if project_config else ''}")
        logger.debug(f"  - Environment vars: {'✓' if env_count > 0 else '✗'} ({env_count} vars)")
        logger.debug(f"  - User config: {'✓' if user_config_loaded else '✗'} {user_config_path_used if user_config_loaded else ''}")
        
        # Log key configuration sections
        logger.debug("Configuration sections available:")
        for section in sorted(self._config.keys()):
            if isinstance(self._config[section], dict):
                logger.debug(f"  - {section}: {len(self._config[section])} settings")
            else:
                logger.debug(f"  - {section}: {type(self._config[section]).__name__}")
        
        logger.debug(f"Complete final configuration: {self._config}")
        logger.debug("=== Configuration Loading Complete ===")
        
        # Now that config is loaded, set up the logger properly
        # Set flag for external debug trigger - check FINAL config level after all merging
        final_config_log_level = self.get('logging.level', 'INFO')
        self._should_show_debug = (isinstance(final_config_log_level, str) and final_config_log_level.upper() == 'DEBUG')
        
        # Now that config is loaded, set up the logger properly
        self._setup_config_logger()
        
        # Fix any existing loggers to use consistent formatting
        try:
            from .logging import fix_existing_loggers
            fix_existing_loggers()
        except ImportError:
            pass  # fix_existing_loggers may not be available during early import
        
        logger.debug(f"Configuration loaded. Level: {final_config_log_level}, Debug flag set: {self._should_show_debug}")
        
        # Trigger debug output automatically if DEBUG level is enabled
        if self._should_show_debug:
            # Use a simple approach - trigger after config is fully loaded and logger should be ready
            import threading
            def delayed_trigger():
                import time
                time.sleep(0.1)  # Brief delay to ensure logger is ready
                self.trigger_debug_if_enabled()
            
            thread = threading.Thread(target=delayed_trigger, daemon=True)
            thread.start()
    
    def _load_yaml_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a YAML configuration file."""
        logger.debug(f"Checking config file: {path}")
        logger.debug(f"  Path exists: {path.exists()}")
        logger.debug(f"  Path is file: {path.is_file() if path.exists() else 'N/A'}")
        logger.debug(f"  Path readable: {os.access(path, os.R_OK) if path.exists() else 'N/A'}")
        
        if not path.exists():
            logger.debug(f"Config file does not exist: {path}")
            return None
            
        try:
            with path.open('r') as f:
                config_data = yaml.safe_load(f)
                if config_data is None:
                    logger.debug(f"YAML file is empty: {path}")
                    return {}
                elif not isinstance(config_data, dict):
                    logger.warning(f"YAML file does not contain a dictionary: {path}")
                    return {}
                else:
                    logger.debug(f"Successfully loaded YAML from {path}")
                    logger.debug(f"  File size: {path.stat().st_size} bytes")
                    logger.debug(f"  Sections found: {list(config_data.keys())}")
                    return config_data
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {path}: {e}")
            raise ConfigError(f"YAML parsing error in {path}: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied reading config file {path}: {e}")
            raise ConfigError(f"Permission denied reading config file {path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            raise ConfigError(f"Failed to load config file {path}: {e}")
    
    def _load_env_vars(self) -> int:
        """Load configuration from environment variables.
        
        Environment variables should be in the format NK2DL_SECTION_KEY
        where SECTION is the top-level config section and KEY is the setting key.
        For keys containing underscores, use double underscores in the env var.
        
        Examples:
            NK2DL_DEADLINE_HOST -> deadline.host
            NK2DL_DEADLINE_USE__WEB__SERVICE -> deadline.use_web_service
            
        Returns:
            Number of environment variables processed
        """
        env_vars_found = 0
        env_vars_processed = []
        
        for key, value in os.environ.items():
            if key.startswith('NK2DL_') and key not in self.SPECIAL_ENV_VARS:
                # Remove prefix and split into section and key
                _, section, *key_parts = key.split('_')
                # Join remaining parts and replace double underscores with single
                config_key = '_'.join(key_parts).lower().replace('__', '_')
                config_path = f"{section.lower()}.{config_key}"
                logger.debug(f"Setting config from env var {key}: {config_path} = {value}")
                self._set_config_value([section.lower(), config_key], value)
                env_vars_found += 1
                env_vars_processed.append(f"{key} -> {config_path}")
                
        if env_vars_processed:
            logger.debug("Environment variables processed:")
            for env_var in env_vars_processed:
                logger.debug(f"  {env_var}")
        else:
            logger.debug("No NK2DL_* environment variables found")
            
        return env_vars_found
    
    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """Recursively update configuration dictionary."""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self._config:
                logger.debug(f"Updating nested config section: {key}")
                self._config[key].update(value)
            else:
                logger.debug(f"Setting config key: {key} = {value}")
                self._config[key] = value
    
    def _set_config_value(self, path: list, value: str) -> None:
        """Set a configuration value at the specified path."""
        current = self._config
        for part in path[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Convert string value to appropriate type
        original_value = value
        if value.lower() in ('true', 'yes', '1', 'on'):
            value = True
        elif value.lower() in ('false', 'no', '0', 'off'):
            value = False
        else:
            # Try to convert numeric values
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except (ValueError, TypeError):
                pass
        
        if original_value != value:
            logger.debug(f"Converted config value from '{original_value}' to {value} ({type(value).__name__})")
            
        current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Dot-separated configuration key (e.g. 'deadline.host')
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        current = self._config
        for part in key.split('.'):
            if not isinstance(current, dict) or part not in current:
                logger.debug(f"Config key not found: {key}, using default: {default}")
                return default
            current = current[part]
        
        logger.debug(f"Config get: {key} = {current}")
        return current

    def _setup_config_logger(self) -> None:
        """Set up the config logger properly after configuration is loaded."""
        global logger, _logger_needs_setup
        
        if not _logger_needs_setup:
            return
            
        try:
            # Import setup_logging after config is loaded to avoid circular import
            from .logging import setup_logging
            logger = setup_logging('nk2dl.common.config')
            _logger_needs_setup = False
            logger.debug("Config logger properly initialized with setup_logging")
        except ImportError:
            # Fallback to basic logger if setup_logging not available
            logger.debug("Using basic logger - setup_logging not available")
            _logger_needs_setup = False
    
    def trigger_debug_if_enabled(self) -> None:
        """Trigger debug output if DEBUG level is configured and hasn't been shown yet."""
        if hasattr(self, '_should_show_debug') and self._should_show_debug:
            logger.debug("DEBUG level detected - triggering configuration debug output")
            self.debug_config_info()
        else:
            logger.debug("DEBUG level not detected or not configured - skipping debug output")
    
    def debug_config_info(self) -> None:
        """Log detailed configuration debugging information to help troubleshoot config issues."""
        global _debug_config_shown
        
        if _debug_config_shown:
            logger.debug("Configuration debug info already shown (use debug_config(force=True) to show again)")
            return
            
        _debug_config_shown = True
        
        # Temporarily disable caller information for clean debug output
        try:
            from .logging import disable_caller_info, enable_caller_info
            disable_caller_info()
        except ImportError:
            pass
        
        # Save current logger level and temporarily set to 1 to ensure all debug messages appear
        original_level = logger.getEffectiveLevel()
        logger.setLevel(1)
        
        try:
            # Output each line as a separate debug message with individual timestamps
            logger.debug("=" * 60)
            logger.debug("NK2DL Configuration Debug Information")
            logger.debug("=" * 60)
            
            logger.debug("1. Configuration File Paths:")
            logger.debug(f"   Project config: {self._project_config_path}")
            logger.debug(f"   User config: {'✓' if self._user_config_path.exists() else '✗'} {self._user_config_path}")
            
            logger.debug("2. Environment Variables:")
            env_vars = [key for key in os.environ.keys() if key.startswith('NK2DL_')]
            if env_vars:
                logger.debug(f"   Found {len(env_vars)} NK2DL_* environment variables:")
                for var in sorted(env_vars):
                    logger.debug(f"     {var} = {os.environ[var]}")
            else:
                logger.debug("   No NK2DL_* environment variables found")
            
            logger.debug("3. Current Configuration Sections:")
            for section in sorted(self._config.keys()):
                if isinstance(self._config[section], dict):
                    logger.debug(f"   {section}: {len(self._config[section])} settings")
                    # Show ALL settings for each section
                    for key in sorted(self._config[section].keys()):
                        value = self._config[section][key]
                        # Format the value nicely
                        if isinstance(value, str) and len(value) > 80:
                            value = value[:77] + "..."
                        elif isinstance(value, list):
                            if len(value) == 0:
                                value = "[]"
                            elif len(value) <= 3:
                                value = str(value)
                            else:
                                value = f"[{len(value)} items: {value[0]}, ...]"
                        elif isinstance(value, dict):
                            if len(value) == 0:
                                value = "{}"
                            else:
                                value = f"{{{len(value)} items}}"
                        logger.debug(f"     {key}: {value}")
                else:
                    logger.debug(f"   {section}: {self._config[section]}")
            
            logger.debug("4. To create a user config file:")
            logger.debug(f"   1. Create directory: {self.USER_CONFIG_PATH.parent}")
            logger.debug(f"   2. Create file: {self.USER_CONFIG_PATH}")
            logger.debug("   3. Add YAML content like:")
            logger.debug("      deadline:")
            logger.debug("        host: your-deadline-server")
            logger.debug("      submission:")
            logger.debug("        priority: 75")
            logger.debug("        pool: your-pool")
            
            logger.debug("=" * 60)
        
        finally:
            # Restore original logger level
            logger.setLevel(original_level)
            
            # Re-enable caller information
            try:
                enable_caller_info()
            except ImportError:
                pass

# Global configuration instance
logger.debug("Creating global config instance")
config = Config()

# Convenience function for debugging
def debug_config(force: bool = False) -> None:
    """Convenience function to log configuration debugging information.
    
    Outputs detailed configuration information using the logger at DEBUG level.
    
    Args:
        force: If True, show debug info even if already shown once
    
    Usage:
        from nk2dl.common.config import debug_config
        debug_config()  # Show once
        debug_config(force=True)  # Force show again
    """
    global _debug_config_shown
    
    if force:
        _debug_config_shown = False
        
    config.debug_config_info() 