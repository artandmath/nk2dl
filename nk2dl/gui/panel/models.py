# -*- coding: utf-8 -*-
"""Data models for the nk2dl panel.

This module contains all data model classes used for managing data in the nk2dl panel interface.
Models handle data logic, validation, and state management independently of the UI.
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

from .constants import TableColumns


class TableDataModel(QtCore.QObject):
    """Model for managing table data with master row fallback logic.
    
    This model handles the logic for the node settings table, including:
    - Master row values as defaults for other rows
    - Effective value calculation (cell value or master fallback)
    - Data validation for different column types
    - Change notifications
    """
    
    # Signals
    dataChanged = QtCore.Signal()
    masterRowChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.master_row_index = 0
        self._data = []  # List of dictionaries, one per row
        self._headers = TableColumns.HEADERS.copy()
        
    def set_data(self, data):
        """Set the table data.
        
        Args:
            data (list): List of dictionaries, one per row
        """
        self._data = data.copy() if data else []
        self.dataChanged.emit()
    
    def get_data(self):
        """Get the raw table data.
        
        Returns:
            list: List of dictionaries, one per row
        """
        return self._data.copy()
    
    def get_row_count(self):
        """Get the number of rows.
        
        Returns:
            int: Number of rows
        """
        return len(self._data)
    
    def get_column_count(self):
        """Get the number of columns.
        
        Returns:
            int: Number of columns
        """
        return len(self._headers)
    
    def get_headers(self):
        """Get the column headers.
        
        Returns:
            list: List of column header names
        """
        return self._headers.copy()
    
    def get_cell_value(self, row, column):
        """Get the raw cell value (may be empty).
        
        Args:
            row (int): Row index
            column (int): Column index
            
        Returns:
            str: Raw cell value or empty string
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return ""
        
        header = self._headers[column]
        return self._data[row].get(header, "")
    
    def set_cell_value(self, row, column, value):
        """Set a cell value.
        
        Args:
            row (int): Row index
            column (int): Column index
            value (str): Value to set
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return
        
        header = self._headers[column]
        old_value = self._data[row].get(header, "")
        
        if old_value != value:
            self._data[row][header] = value
            
            # Emit appropriate signals
            if row == self.master_row_index:
                self.masterRowChanged.emit()
            else:
                self.dataChanged.emit()
    
    def get_effective_value(self, row, column):
        """Get the effective value for a cell (with master row fallback).
        
        Args:
            row (int): Row index
            column (int): Column index
            
        Returns:
            str: Effective value (cell value or master row fallback)
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return ""
        
        # Get the actual cell value
        cell_value = self.get_cell_value(row, column)
        
        # If cell has a value or this is the master row, return it
        if cell_value.strip() or row == self.master_row_index:
            return cell_value
        
        # Skip Node and Filename columns for fallback (they don't inherit)
        if column in [1, 2]:  # Node, Filename
            return cell_value
        
        # Get master row value as fallback
        master_value = self.get_cell_value(self.master_row_index, column)
        return master_value if master_value.strip() else cell_value
    
    def get_effective_table_values(self):
        """Get effective values from the table, using master row as fallback for blank cells.
        
        Returns:
            List of dictionaries, one per data row (excluding master row).
            Each dict contains the effective values for that row.
        """
        if len(self._data) < 2:  # Need at least master row + 1 data row
            return []
        
        # Get master row values
        master_values = {}
        for col, header in enumerate(self._headers):
            master_values[header] = self.get_cell_value(self.master_row_index, col)
        
        # Process each data row (starting from row 1, skipping master row)
        effective_values = []
        for row in range(1, len(self._data)):
            row_values = {}
            
            for col, header in enumerate(self._headers):
                cell_value = self.get_cell_value(row, col)
                
                # Use cell value if not blank, otherwise fallback to master value
                if cell_value.strip():
                    row_values[header] = cell_value
                else:
                    row_values[header] = master_values[header]
            
            effective_values.append(row_values)
        
        return effective_values
    
    def is_dropdown_column(self, column):
        """Check if a column is a dropdown column.
        
        Args:
            column (int): Column index
            
        Returns:
            bool: True if column is a dropdown column
        """
        if column < 0 or column >= len(self._headers):
            return False
        
        header = self._headers[column]
        return header in TableColumns.DROPDOWN_COLUMNS
    
    def is_yes_no_column(self, column):
        """Check if a column is a Yes/No dropdown column.
        
        Args:
            column (int): Column index
            
        Returns:
            bool: True if column is a Yes/No dropdown column
        """
        if column < 0 or column >= len(self._headers):
            return False
        
        header = self._headers[column]
        return header in TableColumns.YES_NO_COLUMNS
    
    def is_render_mode_column(self, column):
        """Check if a column is the RenderMode column.
        
        Args:
            column (int): Column index
            
        Returns:
            bool: True if column is the RenderMode column
        """
        if column < 0 or column >= len(self._headers):
            return False
        
        header = self._headers[column]
        return header == "RenderMode"
    
    def is_master_row_editable(self, column):
        """Check if a column is editable in the master row.
        
        Args:
            column (int): Column index
            
        Returns:
            bool: True if column is editable in master row
        """
        return column not in TableColumns.MASTER_NON_EDITABLE
    
    def validate_cell_value(self, row, column, value):
        """Validate a cell value for a specific column type.
        
        Args:
            row (int): Row index
            column (int): Column index
            value (str): Value to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if column < 0 or column >= len(self._headers):
            return False, "Invalid column"
        
        header = self._headers[column]
        
        # Yes/No columns
        if header in TableColumns.YES_NO_COLUMNS:
            if row == self.master_row_index:
                # Master row: only Yes/No allowed
                if value not in TableColumns.YES_NO_VALUES:
                    return False, f"Master row {header} must be Yes or No"
            else:
                # Data rows: Yes/No or empty (for inheritance)
                if value and value not in TableColumns.YES_NO_VALUES:
                    return False, f"{header} must be Yes, No, or empty"
        
        # RenderMode column
        elif header == "RenderMode":
            if row == self.master_row_index:
                # Master row: only render mode values allowed
                if value not in TableColumns.RENDER_MODE_VALUES:
                    return False, f"Master row RenderMode must be one of: {', '.join(TableColumns.RENDER_MODE_VALUES)}"
            else:
                # Data rows: render mode values or empty (for inheritance)
                if value and value not in TableColumns.RENDER_MODE_VALUES:
                    return False, f"RenderMode must be one of: {', '.join(TableColumns.RENDER_MODE_VALUES)} or empty"
        
        # TaskTimeout column (integer)
        elif header == "TaskTimeout":
            if value:
                try:
                    timeout_val = int(value)
                    if timeout_val < 0 or timeout_val > 999:
                        return False, "TaskTimeout must be between 0 and 999"
                except ValueError:
                    return False, "TaskTimeout must be a number"
        
        # Priority column (integer)
        elif header == "Priority":
            if value:
                try:
                    priority_val = int(value)
                    if priority_val < 0 or priority_val > 100:
                        return False, "Priority must be between 0 and 100"
                except ValueError:
                    return False, "Priority must be a number"
        
        # Chunk column (integer)
        elif header == "Chunk":
            if value:
                try:
                    chunk_val = int(value)
                    if chunk_val < 1:
                        return False, "Chunk must be 1 or greater"
                except ValueError:
                    return False, "Chunk must be a number"
        
        return True, ""
    
    def add_row(self, row_data=None):
        """Add a new row to the table.
        
        Args:
            row_data (dict, optional): Initial data for the row
            
        Returns:
            int: Index of the new row
        """
        if row_data is None:
            row_data = {}
        
        # Ensure all headers are present
        new_row = {}
        for header in self._headers:
            new_row[header] = row_data.get(header, "")
        
        self._data.append(new_row)
        self.dataChanged.emit()
        
        return len(self._data) - 1
    
    def remove_row(self, row):
        """Remove a row from the table.
        
        Args:
            row (int): Row index to remove
            
        Returns:
            bool: True if row was removed
        """
        if row < 0 or row >= len(self._data):
            return False
        
        # Don't allow removing the master row
        if row == self.master_row_index:
            return False
        
        self._data.pop(row)
        
        # Adjust master row index if necessary
        if row < self.master_row_index:
            self.master_row_index -= 1
        
        self.dataChanged.emit()
        return True
    
    def clear_data(self):
        """Clear all data except master row."""
        if len(self._data) > 1:
            master_row = self._data[self.master_row_index].copy()
            self._data = [master_row]
            self.master_row_index = 0
            self.dataChanged.emit()
    
    def get_master_row_data(self):
        """Get the master row data.
        
        Returns:
            dict: Master row data
        """
        if self.master_row_index < len(self._data):
            return self._data[self.master_row_index].copy()
        return {}
    
    def set_master_row_data(self, data):
        """Set the master row data.
        
        Args:
            data (dict): Master row data
        """
        if self.master_row_index < len(self._data):
            # Update master row with provided data
            for header in self._headers:
                self._data[self.master_row_index][header] = data.get(header, "")
            
            self.masterRowChanged.emit()


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
        from .constants import Settings, DefaultValues
        
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
        
        # Validate frame range format (basic check)
        frame_range = self._job_settings.get('frame_range', '')
        if frame_range and not self._is_valid_frame_range(frame_range):
            errors.append("Frame range format is invalid")
        
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