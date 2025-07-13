"""
Node settings storage repository for persisting node overrides.

This module handles the storage and retrieval of node-specific overrides
from the root node's custom knobs using YAML storage with sync capabilities.
"""

import yaml
import time
from typing import Dict, Any, List, Optional, Set, Tuple

from ....common.logging import setup_logging
from ....common.config import config
from ....nuke.utils import nuke_module
from ..constants import Storage

logger = setup_logging('nk2dl.gui.panel.repositories.storage')


class NodeSettingsStorage:
    """Repository for storing and retrieving node settings overrides.
    
    This class manages the persistence of node-specific settings overrides
    by storing them as YAML data in custom knobs on the root node. It provides
    functionality for saving, loading, and synchronizing settings with the
    current nodes in the script.
    """
    
    # Storage format version for data migration
    STORAGE_VERSION = "0.1"
    
    def __init__(self, settings_model=None):
        """Initialize the settings storage.
        
        Args:
            settings_model: Optional reference to SettingsModel for global settings access
        """
        self._last_sync_timestamp = 0
        self.settings_model = settings_model
        self.node_overrides = {}  # Cache for node overrides
        logger.debug("NodeSettingsStorage initialized")
    
    def refresh_cache(self) -> None:
        """Refresh the internal cache with current stored node overrides."""
        self.node_overrides = self.load_node_overrides()
        logger.debug(f"Refreshed cache with {len(self.node_overrides)} node overrides")
    
    def _write_to_knob(self) -> None:
        """Write current node_overrides cache to storage knob."""
        self.save_node_overrides(self.node_overrides)
    
    def _read_from_knob(self) -> Dict[str, Dict[str, Any]]:
        """Read node overrides from storage knob and update cache."""
        self.node_overrides = self.load_node_overrides()
        return self.node_overrides
    
    def save_node_overrides(self, node_overrides: Dict[str, Dict[str, Any]]) -> bool:
        """Save node override settings to the root node.
        
        Args:
            node_overrides: Dictionary mapping node names to their override settings
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure storage knobs exist
            if not self._ensure_storage_knobs():
                logger.error("Failed to create storage knobs")
                return False
            
            # Prepare data for storage
            storage_data = {
                'version': self.STORAGE_VERSION,
                'timestamp': time.time(),
                'node_overrides': node_overrides
            }
            
            # Serialize to YAML with proper list indentation
            # Use a custom Dumper to ensure lists are properly indented
            class CustomDumper(yaml.SafeDumper):
                def increase_indent(self, flow=False, indentless=False):
                    return super(CustomDumper, self).increase_indent(flow, False)
            
            yaml_data = yaml.dump(storage_data, Dumper=CustomDumper, default_flow_style=False, 
                                sort_keys=True, indent=2, width=float('inf'),
                                allow_unicode=True)
            
            # Save to root node knob
            nuke = nuke_module()
            root_node = nuke.root()
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            settings_knob.setValue(yaml_data)
            
            logger.info(f"Saved settings for {len(node_overrides)} nodes to root node")
            return True
            
        except Exception as e:
            logger.error(f"Error saving node overrides: {e}", exc_info=True)
            return False
    
    def load_node_overrides(self) -> Dict[str, Dict[str, Any]]:
        """Load node override settings from the root node.
        
        Returns:
            Dictionary mapping node names to their override settings
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            # Check if settings knob exists
            if Storage.SETTINGS_KNOB_NAME not in root_node.knobs():
                logger.debug("No settings knob found - returning empty overrides")
                return {}
            
            # Get YAML data from knob
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            yaml_data = settings_knob.value()
            
            if not yaml_data or not yaml_data.strip():
                logger.debug("Empty settings data - returning empty overrides")
                return {}
            
            # Parse YAML
            storage_data = yaml.safe_load(yaml_data)
            
            if not isinstance(storage_data, dict):
                logger.warning("Invalid storage data format - returning empty overrides")
                return {}
            
            # Extract node overrides
            node_overrides = storage_data.get('node_overrides', {})
            
            # Update sync timestamp
            self._last_sync_timestamp = storage_data.get('timestamp', time.time())
            
            logger.info(f"Loaded settings for {len(node_overrides)} nodes from root node")
            return node_overrides
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error loading node overrides: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading node overrides: {e}", exc_info=True)
            return {}
    
    def sync_with_current_nodes(self, current_node_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Synchronize stored settings with current nodes in the script.
        
        This method removes settings for nodes that no longer exist and
        ensures the stored settings are in sync with the current script state.
        
        Args:
            current_node_names: List of node names currently in the script
            
        Returns:
            Cleaned node overrides dictionary
        """
        try:
            # Load current settings
            stored_overrides = self.load_node_overrides()
            
            if not stored_overrides:
                logger.debug("No stored overrides to sync")
                return {}
            
            # Get sets for efficient comparison
            current_nodes = set(current_node_names)
            stored_nodes = set(stored_overrides.keys())
            
            # Find nodes that were removed
            removed_nodes = stored_nodes - current_nodes
            
            # Find new nodes (that don't have overrides yet)
            new_nodes = current_nodes - stored_nodes
            
            if removed_nodes:
                logger.info(f"Removing settings for deleted nodes: {list(removed_nodes)}")
                for node_name in removed_nodes:
                    del stored_overrides[node_name]
            
            if new_nodes:
                logger.debug(f"Found new nodes without overrides: {list(new_nodes)}")
            
            # Save the cleaned settings if changes were made
            if removed_nodes:
                self.save_node_overrides(stored_overrides)
            
            return stored_overrides
            
        except Exception as e:
            logger.error(f"Error syncing with current nodes: {e}", exc_info=True)
            return {}
    
    def is_value_overridden(self, node_name: str, column: str, 
                           node_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Check if a specific value is overridden for a node.
        
        Args:
            node_name: Name of the node
            column: Column/setting name
            node_overrides: Pre-loaded overrides (optional, will load if not provided)
            
        Returns:
            True if the value is explicitly overridden, False if inherited
        """
        try:
            if node_overrides is None:
                node_overrides = self.load_node_overrides()
            
            if node_name not in node_overrides:
                return False
            
            node_settings = node_overrides[node_name]
            
            # A value is overridden if it exists in the settings and is not None
            return column in node_settings and node_settings[column] is not None
            
        except Exception as e:
            logger.warning(f"Error checking override status for {node_name}.{column}: {e}")
            return False
    
    def set_node_override(self, node_name: str, column: str, value: Any) -> bool:
        """Set an override value for a specific node and column.
        
        Args:
            node_name: Name of the node
            column: Column/setting name
            value: Override value (None to clear override)
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Load current overrides
            node_overrides = self.load_node_overrides()
            
            # Ensure node entry exists
            if node_name not in node_overrides:
                node_overrides[node_name] = {}
            
            # Set or clear the override
            if value is None:
                # Remove the override (inherit from settings)
                if column in node_overrides[node_name]:
                    del node_overrides[node_name][column]
                    
                # Remove node entry if no overrides remain
                if not node_overrides[node_name]:
                    del node_overrides[node_name]
                    
            else:
                # Set the override value
                node_overrides[node_name][column] = value
            
            # Save the updated overrides
            return self.save_node_overrides(node_overrides)
            
        except Exception as e:
            logger.error(f"Error setting override for {node_name}.{column}: {e}", exc_info=True)
            return False
    
    # Phase 3: New methods for enhanced storage integration
    
    def get_config_default_value(self, param_name: str) -> Any:
        """Get default value for a parameter from config system.
        
        Args:
            param_name: The parameter name (e.g., 'priority', 'chunk_size')
            
        Returns:
            Default value from config system
        """
        try:
            config_key = f'submission.{param_name}'
            return config.get(config_key)
        except Exception as e:
            logger.warning(f"Error getting config default for {param_name}: {e}")
            return None
    
    def validate_node_override(self, param_name: str, value: Any) -> Any:
        """Validate and convert a node override value.
        
        Args:
            param_name: The parameter name
            value: The value to validate
            
        Returns:
            Validated/converted value
        """
        try:
            # Get config default to determine expected type
            config_default = self.get_config_default_value(param_name)
            
            if config_default is None:
                # Unknown parameter, return as-is
                return value
            
            # Type conversion based on config default
            expected_type = type(config_default)
            
            if expected_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif expected_type == int:
                return int(value)
            elif expected_type == float:
                return float(value)
            elif expected_type == str:
                return str(value)
            else:
                return value
                
        except Exception as e:
            logger.warning(f"Error validating override for {param_name}: {e}")
            return value
    
    def build_write_node_dict(self, node_name: str, node_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Build WriteNode dictionary for submission with direct parameter mapping.
        
        Args:
            node_name: Name of the write node
            node_overrides: Pre-loaded overrides (optional, will load if not provided)
            
        Returns:
            Dictionary suitable for WriteNode submission with 'write_node' key and overrides
        """
        try:
            if node_overrides is None:
                node_overrides = self.load_node_overrides()
            
            write_node_dict = {'write_node': node_name}
            
            # Add node-specific overrides if they exist
            if node_name in node_overrides:
                node_settings = node_overrides[node_name]
                
                # Direct parameter mapping since names already match submission
                for param_name, value in node_settings.items():
                    if value is not None:  # Only include non-None overrides
                        validated_value = self.validate_node_override(param_name, value)
                        write_node_dict[param_name] = validated_value
            
            logger.debug(f"Built WriteNode dict for {node_name}: {write_node_dict}")
            return write_node_dict
            
        except Exception as e:
            logger.error(f"Error building WriteNode dict for {node_name}: {e}", exc_info=True)
            return {'write_node': node_name}
    
    def build_write_nodes_list(self, node_names: List[str]) -> List[Dict[str, Any]]:
        """Build WriteNodes list for submission with direct parameter mapping.
        
        Args:
            node_names: List of write node names
            
        Returns:
            List of WriteNode dictionaries suitable for submission
        """
        try:
            # Load overrides once for efficiency
            node_overrides = self.load_node_overrides()
            
            write_nodes = []
            for node_name in node_names:
                write_node_dict = self.build_write_node_dict(node_name, node_overrides)
                write_nodes.append(write_node_dict)
            
            logger.debug(f"Built WriteNodes list for {len(node_names)} nodes")
            return write_nodes
            
        except Exception as e:
            logger.error(f"Error building WriteNodes list: {e}", exc_info=True)
            return [{'write_node': name} for name in node_names]
    
    def clear_node_overrides(self, node_name: str) -> bool:
        """Clear all overrides for a specific node (restore inheritance).
        
        Args:
            node_name: Name of the node to clear overrides for
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            node_overrides = self.load_node_overrides()
            
            if node_name in node_overrides:
                del node_overrides[node_name]
                logger.info(f"Cleared all overrides for node: {node_name}")
                return self.save_node_overrides(node_overrides)
            else:
                logger.debug(f"No overrides found for node: {node_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing overrides for {node_name}: {e}", exc_info=True)
            return False
    
    def get_effective_value(self, node_name: str, param_name: str, 
                           node_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> Any:
        """Get the effective value for a parameter (override or config default).
        
        Args:
            node_name: Name of the node
            param_name: Parameter name
            node_overrides: Pre-loaded overrides (optional, will load if not provided)
            
        Returns:
            Override value if exists, otherwise config default
        """
        try:
            if node_overrides is None:
                node_overrides = self.load_node_overrides()
            
            # Check if value is overridden
            if (node_name in node_overrides and 
                param_name in node_overrides[node_name] and 
                node_overrides[node_name][param_name] is not None):
                return node_overrides[node_name][param_name]
            
            # Return config default
            return self.get_config_default_value(param_name)
            
        except Exception as e:
            logger.warning(f"Error getting effective value for {node_name}.{param_name}: {e}")
            return self.get_config_default_value(param_name)
    
    def _ensure_storage_knobs(self) -> bool:
        """Ensure the storage knobs exist on the root node.
        
        Creates the tab knob and settings knob if they don't exist.
        
        Returns:
            True if knobs exist or were created successfully, False otherwise
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            # Check/create tab knob
            if Storage.TAB_KNOB_NAME not in root_node.knobs():
                tab_knob = nuke.Tab_Knob(Storage.TAB_KNOB_NAME, Storage.TAB_KNOB_NAME)
                root_node.addKnob(tab_knob)
                logger.debug(f"Created tab knob '{Storage.TAB_KNOB_NAME}' on root node")
            
            # Check/create settings knob
            if Storage.SETTINGS_KNOB_NAME not in root_node.knobs():
                settings_knob = nuke.Multiline_Eval_String_Knob(
                    Storage.SETTINGS_KNOB_NAME, 
                    Storage.SETTINGS_KNOB_DISPLAY_NAME,
                    ""
                )
                # Do not run the settings_knob.setFlag(nuke.INVISIBLE). It will make the knob invisible in the UI and is not reversible programmatically.
                root_node.addKnob(settings_knob)
                logger.debug(f"Created settings knob '{Storage.SETTINGS_KNOB_NAME}' on root node")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring storage knobs: {e}", exc_info=True)
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the stored settings.
        
        Returns:
            Dictionary containing version, timestamp, and other metadata
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            if Storage.SETTINGS_KNOB_NAME not in root_node.knobs():
                return {'version': None, 'timestamp': None, 'node_count': 0}
            
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            yaml_data = settings_knob.value()
            
            if not yaml_data or not yaml_data.strip():
                return {'version': None, 'timestamp': None, 'node_count': 0}
            
            storage_data = yaml.safe_load(yaml_data)
            
            if isinstance(storage_data, dict):
                node_overrides = storage_data.get('node_overrides', {})
                return {
                    'version': storage_data.get('version'),
                    'timestamp': storage_data.get('timestamp'),
                    'node_count': len(node_overrides)
                }
            
            return {'version': None, 'timestamp': None, 'node_count': 0}
            
        except Exception as e:
            logger.warning(f"Error getting storage metadata: {e}")
            return {'version': None, 'timestamp': None, 'node_count': 0}
    
    def build_submission_args(self, 
                            script_path: str, 
                            write_nodes: Optional[List[str]] = None,
                            **additional_kwargs) -> Dict[str, Any]:
        """Build arguments for NukeSubmission constructor with zero translation.
        
        Combines global settings from SettingsModel with node-specific overrides
        and formats them for direct passing to NukeSubmission constructor.
        
        Args:
            script_path: Path to the Nuke script
            write_nodes: List of write nodes to process. If None, uses all nodes with overrides.
            **additional_kwargs: Additional keyword arguments to include/override
            
        Returns:
            Dictionary of arguments ready for NukeSubmission(**args)
        """
        # Start with required parameters
        args = {
            'script_path': script_path,
            'script_is_open': True,  # Common case for panel usage
        }
        
        # Add global settings from SettingsModel
        if self.settings_model:
            # Get all settings from the model using HeaderSettingsMapping
            from ..constants import HeaderSettingsMapping
            
            for display_name, param_name in HeaderSettingsMapping.ALL_MAPPINGS.items():
                # Get value from settings model
                value = self.settings_model.get_setting(param_name)
                if value is not None:
                    args[param_name] = value
        
        # Handle write nodes with overrides
        if write_nodes:
            write_nodes_with_overrides = []
            
            for node_name in write_nodes:
                if node_name in self.node_overrides:
                    # Node has overrides - create WriteNode dictionary
                    node_dict = {
                        'write_node': node_name,
                        **self.node_overrides[node_name]
                    }
                    write_nodes_with_overrides.append(node_dict)
                else:
                    # Node has no overrides - use simple string
                    write_nodes_with_overrides.append(node_name)
            
            args['write_nodes'] = write_nodes_with_overrides
        
        # Apply additional kwargs (can override any setting)
        args.update(additional_kwargs)
        
        return args
    
    def save_all_settings(self, global_settings: Dict[str, Any], 
                         node_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Save complete settings including global settings and node overrides.
        
        This method saves both global settings and node-specific overrides to the
        root node storage. It validates all settings before saving.
        
        Args:
            global_settings: Dictionary of global settings (from SettingsModel)
            node_overrides: Optional dictionary of node-specific overrides
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Use current node overrides if not provided
            if node_overrides is None:
                node_overrides = self.load_node_overrides()
            
            # Validate settings before saving
            is_valid, errors = self._validate_settings(global_settings, node_overrides)
            if not is_valid:
                logger.error(f"Settings validation failed: {errors}")
                return False
            
            # Apply config defaults for missing values
            complete_settings = self._apply_config_defaults(global_settings)
            
            # Ensure storage knobs exist
            if not self._ensure_storage_knobs():
                logger.error("Failed to create storage knobs")
                return False
            
            # Prepare complete data for storage
            storage_data = {
                'version': self.STORAGE_VERSION,
                'timestamp': time.time(),
                'global_settings': complete_settings,
                'node_overrides': node_overrides
            }
            
            # Serialize to YAML
            yaml_data = yaml.dump(storage_data, default_flow_style=False, 
                                sort_keys=True, indent=2)
            
            # Save to root node knob
            nuke = nuke_module()
            root_node = nuke.root()
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            settings_knob.setValue(yaml_data)
            
            logger.info(f"Saved complete settings: {len(complete_settings)} global, {len(node_overrides)} node overrides")
            return True
            
        except Exception as e:
            logger.error(f"Error saving all settings: {e}", exc_info=True)
            return False
    
    def load_all_settings(self) -> Dict[str, Any]:
        """Load complete settings including global settings and node overrides.
        
        Returns:
            Dictionary containing 'global_settings' and 'node_overrides' keys
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            # Check if settings knob exists
            if Storage.SETTINGS_KNOB_NAME not in root_node.knobs():
                logger.debug("No settings knob found - returning default settings")
                return {
                    'global_settings': self._get_config_default_settings(),
                    'node_overrides': {}
                }
            
            # Get YAML data from knob
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            yaml_data = settings_knob.value()
            
            if not yaml_data or not yaml_data.strip():
                logger.debug("Empty settings data - returning default settings")
                return {
                    'global_settings': self._get_config_default_settings(),
                    'node_overrides': {}
                }
            
            # Parse YAML
            storage_data = yaml.safe_load(yaml_data)
            
            if not isinstance(storage_data, dict):
                logger.warning("Invalid storage data format - returning default settings")
                return {
                    'global_settings': self._get_config_default_settings(),
                    'node_overrides': {}
                }
            
            # Extract global settings (with config defaults for missing values)
            stored_global_settings = storage_data.get('global_settings', {})
            complete_global_settings = self._apply_config_defaults(stored_global_settings)
            
            # Extract node overrides
            node_overrides = storage_data.get('node_overrides', {})
            
            # Update sync timestamp
            self._last_sync_timestamp = storage_data.get('timestamp', time.time())
            
            logger.info(f"Loaded complete settings: {len(complete_global_settings)} global, {len(node_overrides)} node overrides")
            
            return {
                'global_settings': complete_global_settings,
                'node_overrides': node_overrides
            }
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error loading all settings: {e}")
            return {
                'global_settings': self._get_config_default_settings(),
                'node_overrides': {}
            }
        except Exception as e:
            logger.error(f"Error loading all settings: {e}", exc_info=True)
            return {
                'global_settings': self._get_config_default_settings(),
                'node_overrides': {}
            }
    
    def _validate_settings(self, global_settings: Dict[str, Any], 
                          node_overrides: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate complete settings using the schema.
        
        Args:
            global_settings: Dictionary of global settings
            node_overrides: Dictionary of node-specific overrides
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            from ..constants import validate_settings
            
            errors = []
            
            # Validate global settings
            is_valid, global_errors = validate_settings(global_settings)
            if not is_valid:
                errors.extend([f"Global: {error}" for error in global_errors])
            
            # Validate each node's overrides
            for node_name, node_settings in node_overrides.items():
                is_valid, node_errors = validate_settings(node_settings)
                if not is_valid:
                    errors.extend([f"Node {node_name}: {error}" for error in node_errors])
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating settings: {e}", exc_info=True)
            return False, [f"Validation error: {str(e)}"]
    
    def _apply_config_defaults(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply config system defaults for missing settings.
        
        Args:
            settings: Dictionary of settings (may be incomplete)
            
        Returns:
            Complete settings dictionary with config defaults applied
        """
        try:
            from ..constants import SettingsSchema
            
            # Get all available parameters from schema
            complete_settings = settings.copy()
            
            # Apply defaults for missing parameters
            for param_name, schema in SettingsSchema.SCHEMA.items():
                if param_name not in complete_settings:
                    config_key = schema.get('config_key')
                    if config_key:
                        default_value = config.get(config_key)
                        if default_value is not None:
                            complete_settings[param_name] = default_value
                            logger.debug(f"Applied config default for {param_name}: {default_value}")
            
            return complete_settings
            
        except Exception as e:
            logger.error(f"Error applying config defaults: {e}", exc_info=True)
            return settings
    
    def _get_config_default_settings(self) -> Dict[str, Any]:
        """Get complete default settings from config system.
        
        Returns:
            Dictionary of default settings from config system
        """
        try:
            from ..constants import SettingsSchema
            
            default_settings = {}
            
            # Get defaults for all parameters with config keys
            for param_name, schema in SettingsSchema.SCHEMA.items():
                config_key = schema.get('config_key')
                if config_key:
                    default_value = config.get(config_key)
                    if default_value is not None:
                        default_settings[param_name] = default_value
            
            logger.debug(f"Retrieved {len(default_settings)} default settings from config")
            return default_settings
            
        except Exception as e:
            logger.error(f"Error getting config default settings: {e}", exc_info=True)
            return {}
    
    def _convert_and_validate(self, param_name: str, value: Any) -> Tuple[Any, bool, str]:
        """Convert and validate a single setting value using schema.
        
        Args:
            param_name: The parameter name
            value: The value to convert and validate
            
        Returns:
            Tuple of (converted_value, is_valid, error_message)
        """
        try:
            from ..constants import convert_and_validate_setting
            return convert_and_validate_setting(param_name, value)
            
        except Exception as e:
            logger.error(f"Error in convert and validate for {param_name}: {e}", exc_info=True)
            return value, False, f"Conversion error: {str(e)}"
    
    def get_stored_pool_default(self) -> Optional[str]:
        """Get the stored default pool preference.
        
        Returns:
            The stored pool preference, or None if not set
        """
        try:
            # Try to get from global settings in storage
            all_settings = self.load_all_settings()
            global_settings = all_settings.get('global_settings', {})
            
            # Check for pool preference
            stored_pool = global_settings.get('pool')
            
            if stored_pool and stored_pool != 'none':
                logger.debug(f"Found stored pool preference: {stored_pool}")
                return stored_pool
                
        except Exception as e:
            logger.error(f"Error getting stored pool default: {e}", exc_info=True)
        
        return None
    
    def get_stored_group_default(self) -> Optional[str]:
        """Get the stored default group preference.
        
        Returns:
            The stored group preference, or None if not set
        """
        try:
            # Try to get from global settings in storage
            all_settings = self.load_all_settings()
            global_settings = all_settings.get('global_settings', {})
            
            # Check for group preference
            stored_group = global_settings.get('group')
            
            if stored_group and stored_group != 'none':
                logger.debug(f"Found stored group preference: {stored_group}")
                return stored_group
                
        except Exception as e:
            logger.error(f"Error getting stored group default: {e}", exc_info=True)
        
        return None
    
    def save_resource_preferences(self, pool: Optional[str] = None, group: Optional[str] = None) -> bool:
        """Save user's preferred pool and group defaults.
        
        Args:
            pool: Pool preference to save (optional)
            group: Group preference to save (optional)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Load current settings
            all_settings = self.load_all_settings()
            
            # Get global settings
            global_settings = all_settings.get('global_settings', {})
            
            # Update preferences
            if pool is not None:
                global_settings['pool'] = pool
                logger.debug(f"Updated pool preference to: {pool}")
            
            if group is not None:
                global_settings['group'] = group
                logger.debug(f"Updated group preference to: {group}")
            
            # Save back to storage
            return self.save_all_settings(global_settings, all_settings.get('node_overrides', {}))
            
        except Exception as e:
            logger.error(f"Error saving resource preferences: {e}", exc_info=True)
            return False
    
    def save_user_changed_settings(self, user_changed_settings: Dict[str, Any]) -> bool:
        """Save only user-changed settings to storage, creating minimal YAML files.
        
        This method implements the core logic of Phase 2, saving only the settings
        that have been explicitly changed by the user, rather than all settings.
        This results in minimal YAML files and proper visual indication behavior.
        
        Args:
            user_changed_settings: Dictionary of only user-changed settings with their values
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Load current node overrides (preserve existing node-specific settings)
            node_overrides = self.load_node_overrides()
            
            # Ensure storage knobs exist
            if not self._ensure_storage_knobs():
                logger.error("Failed to create storage knobs")
                return False
            
            # Prepare minimal data for storage - only user-changed settings
            storage_data = {
                'version': self.STORAGE_VERSION,
                'timestamp': time.time(),
                'global_settings': user_changed_settings,  # Only user-changed settings
                'node_overrides': node_overrides
            }
            
            # Serialize to YAML with proper formatting
            class CustomDumper(yaml.SafeDumper):
                def increase_indent(self, flow=False, indentless=False):
                    return super(CustomDumper, self).increase_indent(flow, False)
            
            yaml_data = yaml.dump(storage_data, Dumper=CustomDumper, default_flow_style=False, 
                                sort_keys=True, indent=2, width=float('inf'),
                                allow_unicode=True)
            
            # Save to root node knob
            nuke = nuke_module()
            root_node = nuke.root()
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            settings_knob.setValue(yaml_data)
            
            logger.info(f"Saved minimal settings: {len(user_changed_settings)} user-changed global settings, {len(node_overrides)} node overrides")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user-changed settings: {e}", exc_info=True)
            return False
    
    def load_user_changed_settings(self) -> Dict[str, Any]:
        """Load only user-changed settings from storage.
        
        This method returns only the settings that were explicitly saved as user-changed,
        not the complete settings with config defaults applied.
        
        Returns:
            Dictionary containing only user-changed settings
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            # Check if settings knob exists
            if Storage.SETTINGS_KNOB_NAME not in root_node.knobs():
                logger.debug("No settings knob found - returning empty user-changed settings")
                return {}
            
            # Get YAML data from knob
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            yaml_data = settings_knob.value()
            
            if not yaml_data or not yaml_data.strip():
                logger.debug("Empty settings data - returning empty user-changed settings")
                return {}
            
            # Parse YAML
            storage_data = yaml.safe_load(yaml_data)
            
            if not isinstance(storage_data, dict):
                logger.warning("Invalid storage data format - returning empty user-changed settings")
                return {}
            
            # Extract ONLY the stored global settings (these are user-changed)
            user_changed_settings = storage_data.get('global_settings', {})
            
            logger.info(f"Loaded {len(user_changed_settings)} user-changed settings from storage")
            return user_changed_settings
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error loading user-changed settings: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading user-changed settings: {e}", exc_info=True)
            return {}
    
    def create_minimal_storage_if_needed(self) -> bool:
        """Create minimal storage structure if none exists.
        
        This method creates a basic YAML structure when the panel first loads
        if no storage exists, ensuring the storage system is ready for user changes.
        
        Returns:
            True if minimal storage was created or already exists, False on error
        """
        try:
            nuke = nuke_module()
            root_node = nuke.root()
            
            # Check if settings knob already exists and has data
            if Storage.SETTINGS_KNOB_NAME in root_node.knobs():
                settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
                yaml_data = settings_knob.value()
                
                if yaml_data and yaml_data.strip():
                    # Storage already exists with data
                    logger.debug("Storage already exists with data - no need to create minimal structure")
                    return True
            
            # Create minimal storage structure
            minimal_storage_data = {
                'version': self.STORAGE_VERSION,
                'timestamp': time.time(),
                'global_settings': {},  # Empty - will be populated as user makes changes
                'node_overrides': {}    # Empty - will be populated as user makes node overrides
            }
            
            # Ensure storage knobs exist
            if not self._ensure_storage_knobs():
                logger.error("Failed to create storage knobs")
                return False
            
            # Serialize to YAML
            yaml_data = yaml.dump(minimal_storage_data, default_flow_style=False, 
                                sort_keys=True, indent=2)
            
            # Save to root node knob
            settings_knob = root_node[Storage.SETTINGS_KNOB_NAME]
            settings_knob.setValue(yaml_data)
            
            logger.info("Created minimal storage structure for user changes")
            return True
            
        except Exception as e:
            logger.error(f"Error creating minimal storage: {e}", exc_info=True)
            return False 