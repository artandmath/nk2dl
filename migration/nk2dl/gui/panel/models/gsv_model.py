# -*- coding: utf-8 -*-
"""GSV hierarchy model for managing GSV tree data and selection state.

This module contains the GSVHierarchyModel class that handles the logic for the GSV tree,
including primary GSV hierarchy, secondary GSV columns, and selection state management.
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


class GSVHierarchyModel(QtCore.QObject):
    """Model for managing GSV hierarchy data and selection state.
    
    This model handles the logic for the GSV tree, including:
    - Primary GSV hierarchy (tree structure)
    - Secondary GSV columns and values
    - Selection state management
    - Tree building and parsing logic
    """
    
    # Signals
    hierarchyChanged = QtCore.Signal()
    selectionChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.primary_gsv_levels = []
        self.secondary_gsv_levels = []
        self.gsv_data = {}  # Hierarchical data structure
        self.secondary_gsv_data = {}  # Secondary GSV values
        self.selection_state = {}  # Track selection state
        
        # Initialize with default data
        self._create_default_data()
    
    def _create_default_data(self):
        """Create default GSV data structure."""
        # Primary GSV hierarchy (tree structure)
        self.gsv_data = {
            'Sequence': {
                'seq010': {
                    'Shotcode': {
                        'sh001': {},
                        'sh002': {},
                        'sh003': {}
                    }
                },
                'seq020': {
                    'Shotcode': {
                        'sh010': {},
                        'sh011': {},
                        'sh012': {}
                    }
                },
                'seq030': {
                    'Shotcode': {
                        'sh020': {},
                        'sh021': {}
                    }
                }
            }
        }
        
        # Secondary GSV data (column values)
        self.secondary_gsv_data = {
            'Resolution': ['Full', 'Proxy'],
            'Format': ['EXR', 'MOV', 'DWAA']
        }
        
        # Default levels
        self.primary_gsv_levels = ['Sequence', 'Shotcode']
        self.secondary_gsv_levels = ['Resolution', 'Format']
    
    def set_primary_gsv_text(self, text):
        """Set primary GSV levels from text input.
        
        Args:
            text (str): Comma-separated GSV level names
        """
        if not text.strip():
            self.primary_gsv_levels = []
        else:
            self.primary_gsv_levels = [level.strip() for level in text.split(',') if level.strip()]
        
        self.hierarchyChanged.emit()
    
    def set_secondary_gsv_text(self, text):
        """Set secondary GSV levels from text input.
        
        Args:
            text (str): Comma-separated GSV level names
        """
        if not text.strip():
            self.secondary_gsv_levels = []
        else:
            self.secondary_gsv_levels = [level.strip() for level in text.split(',') if level.strip()]
        
        self.hierarchyChanged.emit()
    
    def get_primary_gsv_text(self):
        """Get primary GSV levels as text.
        
        Returns:
            str: Comma-separated GSV level names
        """
        return ', '.join(self.primary_gsv_levels)
    
    def get_secondary_gsv_text(self):
        """Get secondary GSV levels as text.
        
        Returns:
            str: Comma-separated GSV level names
        """
        return ', '.join(self.secondary_gsv_levels)
    
    def get_primary_gsv_levels(self):
        """Get the primary GSV levels.
        
        Returns:
            list: List of primary GSV level names
        """
        return self.primary_gsv_levels.copy()
    
    def get_secondary_gsv_levels(self):
        """Get the secondary GSV levels.
        
        Returns:
            list: List of secondary GSV level names
        """
        return self.secondary_gsv_levels.copy()
    
    def get_gsv_data(self):
        """Get the hierarchical GSV data.
        
        Returns:
            dict: Hierarchical GSV data structure
        """
        return self.gsv_data.copy()
    
    def set_gsv_data(self, data):
        """Set the hierarchical GSV data.
        
        Args:
            data (dict): Hierarchical GSV data structure
        """
        self.gsv_data = data.copy() if data else {}
        self.hierarchyChanged.emit()
    
    def get_secondary_gsv_data(self):
        """Get the secondary GSV data.
        
        Returns:
            dict: Secondary GSV data (level_name -> list of values)
        """
        return self.secondary_gsv_data.copy()
    
    def set_secondary_gsv_data(self, data):
        """Set the secondary GSV data.
        
        Args:
            data (dict): Secondary GSV data (level_name -> list of values)
        """
        self.secondary_gsv_data = data.copy() if data else {}
        self.hierarchyChanged.emit()
    
    def get_tree_headers(self):
        """Get the headers for the tree widget.
        
        Returns:
            list: List of header names
        """
        headers = ["Primary GSVs"]
        
        # Add secondary GSV columns
        for secondary_gsv in self.secondary_gsv_levels:
            if secondary_gsv in self.secondary_gsv_data:
                for value in self.secondary_gsv_data[secondary_gsv]:
                    headers.append(value)
        
        return headers
    
    def get_tree_groups(self):
        """Get the header groups for grouped header view.
        
        Returns:
            list: List of (group_name, start_col, end_col) tuples
        """
        groups = []
        col_index = 1  # Start after Primary GSVs column
        
        for secondary_gsv in self.secondary_gsv_levels:
            if secondary_gsv in self.secondary_gsv_data:
                values = self.secondary_gsv_data[secondary_gsv]
                if len(values) > 1:
                    # Create group spanning multiple columns
                    start_col = col_index
                    end_col = col_index + len(values) - 1
                    groups.append((secondary_gsv, start_col, end_col))
                col_index += len(values)
        
        return groups
    
    def build_tree_structure(self):
        """Build tree structure data for the tree widget.
        
        Returns:
            list: List of tree item data dictionaries
        """
        if not self.primary_gsv_levels:
            return []
        
        tree_items = []
        self._build_tree_level(self.gsv_data, None, 0, tree_items)
        return tree_items
    
    def _build_tree_level(self, data, parent_path, level_index, tree_items):
        """Recursively build tree levels for Primary GSVs.
        
        Args:
            data (dict): Current level data
            parent_path (list): Path to parent item
            level_index (int): Current level in primary hierarchy
            tree_items (list): List to append tree items to
        """
        if level_index >= len(self.primary_gsv_levels):
            return
        
        level_name = self.primary_gsv_levels[level_index]
        
        if level_name not in data:
            return
        
        level_data = data[level_name]
        
        # Handle dictionary data (has sub-levels)
        if isinstance(level_data, dict):
            for item_key, item_data in sorted(level_data.items()):
                # Create item path
                current_path = (parent_path or []) + [f"{level_name}:{item_key}"]
                
                # Create tree item data
                item_info = {
                    'text': item_key,
                    'path': current_path,
                    'level': level_name,
                    'value': item_key,
                    'level_index': level_index,
                    'parent_path': parent_path,
                    'children': []
                }
                
                # Add to tree items
                tree_items.append(item_info)
                
                # Recursively build child levels
                self._build_tree_level(item_data, current_path, level_index + 1, item_info['children'])
    
    def set_item_selection(self, item_path, column, checked):
        """Set selection state for a tree item and column.
        
        Args:
            item_path (list): Path to the tree item
            column (int): Column index
            checked (bool): Whether item is checked
        """
        path_key = '/'.join(item_path) if item_path else ''
        
        if path_key not in self.selection_state:
            self.selection_state[path_key] = {}
        
        old_state = self.selection_state[path_key].get(column, False)
        if old_state != checked:
            self.selection_state[path_key][column] = checked
            self.selectionChanged.emit()
    
    def get_item_selection(self, item_path, column):
        """Get selection state for a tree item and column.
        
        Args:
            item_path (list): Path to the tree item
            column (int): Column index
            
        Returns:
            bool: Whether item is checked
        """
        path_key = '/'.join(item_path) if item_path else ''
        return self.selection_state.get(path_key, {}).get(column, False)
    
    def clear_all_selections(self):
        """Clear all selections."""
        if self.selection_state:
            self.selection_state.clear()
            self.selectionChanged.emit()
    
    def set_all_selections(self, checked):
        """Set all selections to checked or unchecked.
        
        Args:
            checked (bool): Whether to check or uncheck all items
        """
        # Build all possible paths from tree structure
        tree_items = self.build_tree_structure()
        headers = self.get_tree_headers()
        
        changed = False
        for item in tree_items:
            path_key = '/'.join(item['path'])
            
            if path_key not in self.selection_state:
                self.selection_state[path_key] = {}
            
            # Set state for all columns
            for col in range(len(headers)):
                old_state = self.selection_state[path_key].get(col, False)
                if old_state != checked:
                    self.selection_state[path_key][col] = checked
                    changed = True
            
            # Recursively handle children
            self._set_children_selections(item['children'], headers, checked)
        
        if changed:
            self.selectionChanged.emit()
    
    def _set_children_selections(self, children, headers, checked):
        """Recursively set selections for children.
        
        Args:
            children (list): List of child items
            headers (list): List of headers
            checked (bool): Whether to check or uncheck
        """
        for child in children:
            path_key = '/'.join(child['path'])
            
            if path_key not in self.selection_state:
                self.selection_state[path_key] = {}
            
            # Set state for all columns
            for col in range(len(headers)):
                self.selection_state[path_key][col] = checked
            
            # Recursively handle grandchildren
            self._set_children_selections(child['children'], headers, checked)
    
    def get_selected_gsvs(self):
        """Get the currently selected GSV values.
        
        Returns:
            dict: Dictionary with primary GSV paths and their selected secondary GSVs
        """
        selected_gsvs = {}
        
        for path_key, column_states in self.selection_state.items():
            if not path_key:  # Skip empty paths
                continue
            
            # Check if any columns are selected for this path
            has_selections = any(column_states.values())
            if not has_selections:
                continue
            
            # Parse the path
            path_parts = path_key.split('/')
            
            # Collect selected data
            checked_data = {}
            
            # Check primary GSV selection (column 0)
            if column_states.get(0, False):
                checked_data['primary'] = path_parts[-1] if path_parts else ''
            
            # Check secondary GSV selections
            checked_secondary = {}
            headers = self.get_tree_headers()
            
            col_index = 1  # Start after primary column
            for secondary_gsv in self.secondary_gsv_levels:
                if secondary_gsv in self.secondary_gsv_data:
                    for value in self.secondary_gsv_data[secondary_gsv]:
                        if col_index < len(headers) and column_states.get(col_index, False):
                            if secondary_gsv not in checked_secondary:
                                checked_secondary[secondary_gsv] = []
                            checked_secondary[secondary_gsv].append(value)
                        col_index += 1
            
            if checked_secondary:
                checked_data['secondary'] = checked_secondary
            
            if checked_data:
                selected_gsvs[path_key] = checked_data
        return selected_gsvs 