"""
Node settings storage repository for persisting node overrides.

This module handles the storage and retrieval of node-specific overrides
from the root node's custom knobs using YAML storage with sync capabilities.
"""

import yaml
import time
from typing import Dict, Any, List, Optional, Set

from ....common.logging import setup_logging
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
    
    def __init__(self):
        """Initialize the settings storage."""
        self._last_sync_timestamp = 0
        logger.debug("NodeSettingsStorage initialized")
    
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
            
            # Serialize to YAML
            yaml_data = yaml.dump(storage_data, default_flow_style=False, 
                                sort_keys=True, indent=2)
            
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
                # Make the knob not visible in the UI (it's for storage only)
                settings_knob.setFlag(nuke.INVISIBLE)
                # Make the knob visible in the UI for debugging purposes
                settings_knob.setFlag(nuke.VISIBLE)
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