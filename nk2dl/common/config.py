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

# Get module-level logger
logger = logging.getLogger(__name__)

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
    4. User configuration file (~/.nk2dl/config.yaml)
    """
    
    # Default paths for configuration files
    USER_CONFIG_PATH = Path.home() / '.nk2dl' / 'config.yaml'
    
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
            'timeout': 5,
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
        logger.debug("Loading default configuration")
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Load project config first
        logger.debug(f"Attempting to load project config from {self._project_config_path}")
        project_config = self._load_yaml_file(self._project_config_path)
        if project_config:
            logger.debug(f"Project config found and loaded: {self._project_config_path}")
            logger.debug(f"Project config contents: {project_config}")
            self._update_config(project_config)
        else:
            logger.debug(f"No project config found at {self._project_config_path}")
        
        # Load environment variables second
        logger.debug("Loading configuration from environment variables")
        self._load_env_vars()
            
        # Load user config last (now has highest priority)
        logger.debug(f"Attempting to load user config from {self._user_config_path}")
        user_config = self._load_yaml_file(self._user_config_path)
        if user_config:
            logger.debug(f"User config found and loaded: {self._user_config_path}")
            logger.debug(f"User config contents: {user_config}")
            self._update_config(user_config)
        else:
            logger.debug(f"No user config found at {self._user_config_path}")
            
        # Log final config
        logger.debug(f"Final configuration: {self._config}")
    
    def _load_yaml_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a YAML configuration file."""
        if not path.exists():
            logger.debug(f"Config file does not exist: {path}")
            return None
            
        try:
            with path.open('r') as f:
                config_data = yaml.safe_load(f)
                logger.debug(f"Loaded YAML from {path}")
                return config_data
        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            raise ConfigError(f"Failed to load config file {path}: {e}")
    
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables.
        
        Environment variables should be in the format NK2DL_SECTION_KEY
        where SECTION is the top-level config section and KEY is the setting key.
        For keys containing underscores, use double underscores in the env var.
        
        Examples:
            NK2DL_DEADLINE_HOST -> deadline.host
            NK2DL_DEADLINE_USE__WEB__SERVICE -> deadline.use_web_service
        """
        env_vars_found = 0
        for key, value in os.environ.items():
            if key.startswith('NK2DL_') and key not in self.SPECIAL_ENV_VARS:
                # Remove prefix and split into section and key
                _, section, *key_parts = key.split('_')
                # Join remaining parts and replace double underscores with single
                key = '_'.join(key_parts).lower().replace('__', '_')
                logger.debug(f"Setting config from env var: {section.lower()}.{key} = {value}")
                self._set_config_value([section.lower(), key], value)
                env_vars_found += 1
                
        logger.debug(f"Found {env_vars_found} NK2DL_ environment variables")
    
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

# Global configuration instance
logger.debug("Creating global config instance")
config = Config() 