# -*- coding: utf-8 -*-
"""Table data model for the nk2dl panel.

This module contains the TableDataModel class for managing table data,
including data storage, validation, and settings inheritance.
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

from ..constants import TableColumns, HeaderSettingsMapping


class TableDataModel(QtCore.QObject):
    """Model for managing table data.
    
    This model handles the logic for the node settings table, including:
    - Data storage and retrieval
    - Data validation for different column types
    - Settings inheritance (empty cells inherit from job/machine settings)
    - Override detection (explicit values override settings)
    - Change notifications
    - Real node data integration with background loading
    """
    
    # Signals
    dataChanged = QtCore.Signal()
    loadingStarted = QtCore.Signal()
    loadingFinished = QtCore.Signal()
    loadingProgress = QtCore.Signal(int, str)
    
    def __init__(self, settings_model=None, parent=None):
        super().__init__(parent)
        self._data = []  # List of dictionaries, one per row
        self._headers = TableColumns.HEADERS.copy()
        self.settings_model = settings_model
        
        # Column visibility tracking
        self._visible_columns = set(self._headers)  # All columns visible by default
        
        # Repository integration
        self._node_data_provider = None
        self._settings_storage = None
        
    def set_settings_model(self, settings_model):
        """Set the settings model for inheritance.
        
        Args:
            settings_model: The SettingsModel instance
        """
        self.settings_model = settings_model
        # Emit data changed to refresh display with inherited values
        self.dataChanged.emit()
    
    def set_node_data_provider(self, node_data_provider):
        """Set the node data provider for real data integration.
        
        Args:
            node_data_provider: The NodeDataProvider instance
        """
        self._node_data_provider = node_data_provider
        
        # Connect signals
        if self._node_data_provider:
            self._node_data_provider.dataReady.connect(self._on_data_ready)
            self._node_data_provider.progressUpdate.connect(self._on_progress_update)
            self._node_data_provider.errorOccurred.connect(self._on_error_occurred)
    
    def set_settings_storage(self, settings_storage):
        """Set the settings storage for persistence.
        
        Args:
            settings_storage: The NodeSettingsStorage instance
        """
        self._settings_storage = settings_storage
    
    def refresh_from_nodes_async(self):
        """Refresh table data from real Nuke nodes asynchronously.
        
        This method triggers background loading of node data and merges it
        with any existing user overrides.
        """
        if not self._node_data_provider:
            return
        
        self.loadingStarted.emit()
        self._node_data_provider.refresh_data_async()
    
    def _on_data_ready(self, node_data_list):
        """Handle completion of node data extraction.
        
        Args:
            node_data_list: List of extracted node data dictionaries
        """
        try:
            # Merge node data with stored overrides
            merged_data = self._merge_node_data_with_overrides(node_data_list)
            
            # Update table data
            self._data = merged_data
            
            # Emit signals
            self.dataChanged.emit()
            self.loadingFinished.emit()
            
        except Exception as e:
            # Handle errors gracefully
            self._on_error_occurred(f"Error processing node data: {str(e)}")
    
    def _on_progress_update(self, progress_percent, status_message):
        """Handle progress updates from node data provider.
        
        Args:
            progress_percent: Progress percentage (0-100)
            status_message: Status message
        """
        self.loadingProgress.emit(progress_percent, status_message)
    
    def _on_error_occurred(self, error_message):
        """Handle errors from node data provider.
        
        Args:
            error_message: Error message
        """
        # For now, just finish loading - could be enhanced to show error state
        self.loadingFinished.emit()
        # Could emit a separate error signal if needed
    
    def _merge_node_data_with_overrides(self, node_data_list):
        """Merge fresh node data with stored user overrides.
        
        Args:
            node_data_list: List of fresh node data from provider
            
        Returns:
            List of merged data dictionaries
        """
        # Get stored overrides
        node_overrides = {}
        if self._settings_storage:
            node_names = [node_data.get('Node', '') for node_data in node_data_list]
            node_overrides = self._settings_storage.sync_with_current_nodes(node_names)
        
        # Merge data
        merged_data = []
        for node_data in node_data_list:
            node_name = node_data.get('Node', '')
            
            # Start with fresh node data
            merged_row = node_data.copy()
            
            # Apply any stored overrides
            if node_name in node_overrides:
                overrides = node_overrides[node_name]
                for column, override_value in overrides.items():
                    if override_value is not None:  # None means inherit
                        merged_row[column] = override_value
            
            merged_data.append(merged_row)
        
        return merged_data
        
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
        """Get the explicit cell value (raw data, no inheritance).
        
        Args:
            row (int): Row index
            column (int): Column index
            
        Returns:
            str or None: Cell value, None if should inherit, or empty string if bounds invalid
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return ""
        
        header = self._headers[column]
        value = self._data[row].get(header, None)  # Default to None for inheritance
        
        return value
    
    def get_effective_cell_value(self, row, column):
        """Get the effective value for a cell (explicit or inherited).
        
        This method returns the explicit cell value if it exists and is not None,
        otherwise it returns the inherited value from settings.
        
        Args:
            row (int): Row index
            column (int): Column index
            
        Returns:
            str: Effective cell value (explicit or inherited)
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return ""
        
        header = self._headers[column]
        
        # Check if key exists and has a non-None value (including empty strings)
        if header in self._data[row]:
            value = self._data[row][header]
            if value is not None:
                return str(value)  # Empty strings are explicit values
        
        # Otherwise, try to inherit from settings
        return self._get_inherited_value(column)
    
    def _get_inherited_value(self, column):
        """Get inherited value from settings for a column.
        
        Args:
            column (int): Column index
            
        Returns:
            str: Inherited value from settings or empty string
        """
        if not self.settings_model:
            return ""
        
        setting_type, setting_key = self.get_setting_for_column(column)
        if not setting_type or not setting_key:
            return ""
        
        # Get value from appropriate settings model
        if setting_type == "job":
            value = self.settings_model.get_job_setting(setting_key)
        elif setting_type == "machine":
            value = self.settings_model.get_machine_setting(setting_key)
        else:
            return ""
        
        # Convert setting value to table display format
        converted_value = self._convert_setting_to_display(column, value)
        
        return converted_value
    
    def _convert_setting_to_display(self, column, setting_value):
        """Convert setting value to table display format.
        
        Args:
            column (int): Column index
            setting_value: Value from settings model
            
        Returns:
            str: Converted value for table display
        """
        if column < 0 or column >= len(self._headers):
            return ""
        
        header = self._headers[column]
        
        # Boolean settings → Yes/No
        if header in HeaderSettingsMapping.BOOLEAN_COLUMNS:
            return "Yes" if setting_value else "No"
        
        # Numeric settings → String
        if header in HeaderSettingsMapping.NUMERIC_COLUMNS:
            return str(setting_value) if setting_value is not None else ""
        
        # String settings → Direct
        if header in HeaderSettingsMapping.STRING_COLUMNS:
            return str(setting_value) if setting_value else ""
        
        # Default: convert to string
        return str(setting_value) if setting_value is not None else ""
    
    def is_cell_overridden(self, row, column):
        """Check if cell has an explicit override value.
        
        A cell is considered overridden if it has an explicit value (not None),
        regardless of whether that value matches the inherited value from settings.
        Empty strings are considered explicit values.
        
        Args:
            row (int): Row index
            column (int): Column index
            
        Returns:
            bool: True if cell has an explicit override value
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return False
        
        header = self._headers[column]
        
        # Check if key exists in the row data
        if header not in self._data[row]:
            return False  # Missing key = inherited
        
        value = self._data[row][header]
        
        # If value is None, it's not overridden (it's inherited)
        # Empty strings are considered explicit values
        if value is None:
            return False
        
        # If column has no settings mapping, any explicit value is considered an override
        setting_type, setting_key = self.get_setting_for_column(column)
        if not setting_type or not setting_key:
            return True  # No inheritance possible, so any explicit value is an override
        
        # If there's an explicit value and the column has settings mapping,
        # it's an override regardless of whether it matches the inherited value
        return True
    
    def get_setting_for_column(self, column):
        """Get setting type and key for a column.
        
        Args:
            column (int): Column index
            
        Returns:
            tuple: (setting_type, setting_key) where setting_type is 
                   "job", "machine", or None
        """
        if column < 0 or column >= len(self._headers):
            return None, None
        
        header = self._headers[column]
        return HeaderSettingsMapping.get_setting_type_and_key(header)
    
    def set_cell_value(self, row, column, value, emit_signal=True):
        """Set a cell value.
        
        Args:
            row (int): Row index
            column (int): Column index
            value: Value to set (None means inherit from settings)
            emit_signal (bool): Whether to emit dataChanged signal
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return
        
        header = self._headers[column]
        
        # Keep None as None for inheritance, convert other types to string
        if value is not None:
            value = str(value)
        
        old_value = self._data[row].get(header, None)
        
        if old_value != value:
            self._data[row][header] = value
            
            # Handle special cases for certain columns
            if header == "Order":
                # Update the actual node's render_order knob
                self._update_node_render_order(row, value)
            
            # Persist the override to storage
            if self._settings_storage and header not in ["Node", "Filename"]:
                node_name = self._data[row].get("Node", "")
                if node_name:
                    self._settings_storage.set_node_override(node_name, header, value)
            
            if emit_signal:
                self.dataChanged.emit()
    
    def _update_node_render_order(self, row, order_value):
        """Update the render_order knob on the actual Nuke node.
        
        Args:
            row: Table row index
            order_value: New render order value
        """
        try:
            # Import here to avoid circular imports
            from ....nuke.utils import nuke_module
            
            node_name = self._data[row].get("Node", "")
            if not node_name:
                return
            
            nuke = nuke_module()
            
            # Find the node
            node = None
            for n in nuke.allNodes():
                if n.name() == node_name:
                    node = n
                    break
            
            if not node:
                return
            
            # Update or create render_order knob
            if 'render_order' in node.knobs():
                if order_value is not None:
                    try:
                        node['render_order'].setValue(int(order_value))
                    except (ValueError, TypeError):
                        node['render_order'].setValue(1000)  # Default fallback
            else:
                # Create the knob if it doesn't exist
                try:
                    render_order_knob = nuke.Int_Knob('render_order', 'Render Order')
                    order_int = int(order_value) if order_value else 1000
                    render_order_knob.setValue(order_int)
                    node.addKnob(render_order_knob)
                except Exception:
                    pass  # Silently fail if we can't create the knob
                    
        except Exception:
            # Silently handle any errors - this is a convenience feature
            pass
    
    def clear_cell_value(self, row, column):
        """Clear a cell value to revert to inheritance.
        
        Args:
            row (int): Row index
            column (int): Column index
        """
        self.set_cell_value(row, column, None)
    
    def is_column_editable(self, column):
        """Check if a column is editable by the user.
        
        Args:
            column (int): Column index
            
        Returns:
            bool: True if column is editable
        """
        if column < 0 or column >= len(self._headers):
            return False
        
        header = self._headers[column]
        
        # Node and Filename are read-only (extracted from nodes)
        if header in ["Node", "Filename"]:
            return False
        
        # All other columns are editable
        return True
    
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
        return header in HeaderSettingsMapping.BOOLEAN_COLUMNS
    
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
    
    def validate_cell_value(self, row, column, value):
        """Validate a cell value for the given row and column.
        
        Args:
            row (int): Row index
            column (int): Column index
            value (str): Value to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if column < 0 or column >= len(self._headers):
            return False, "Invalid column index"
        
        header = self._headers[column]
        
        # Yes/No dropdown columns
        if header in TableColumns.YES_NO_COLUMNS:
            if value.strip() in ["", "Yes", "No"]:
                return True, ""
            return False, f"{header} must be Yes or No (or blank)"
        
        # RenderMode dropdown column
        if header == "RenderMode":
            if value.strip() in ["", "Full", "Proxy", "Both", "Script"]:
                return True, ""
            return False, f"RenderMode must be one of: {', '.join(TableColumns.RENDER_MODE_VALUES)} (or blank)"
        
        # Integer columns
        if header in ["TaskTimeout", "Priority", "Chunk"]:
            if value.strip() == "":
                return True, ""
            try:
                int_val = int(value)
                if int_val < 0:
                    return False, f"{header} must be non-negative"
                return True, ""
            except ValueError:
                return False, f"{header} must be a valid integer"
        
        # All other columns - accept any text
        return True, ""
    
    def add_row(self, row_data=None):
        """Add a new row to the table.
        
        Args:
            row_data (dict, optional): Initial data for the row
            
        Returns:
            int: Index of the added row
        """
        if row_data is None:
            row_data = {}
        
        # Only include keys that are explicitly provided
        # Missing keys will be inherited from settings
        new_row = row_data.copy()
        
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
        
        self._data.pop(row)
        self.dataChanged.emit()
        return True
    
    def set_visible_columns(self, visible_columns):
        """Set which columns should be visible.
        
        Args:
            visible_columns (set): Set of column header names to show
        """
        self._visible_columns = set(visible_columns)
        self.dataChanged.emit()
    
    def get_visible_columns(self):
        """Get the set of visible column headers.
        
        Returns:
            set: Set of visible column header names
        """
        return self._visible_columns.copy()
    
    def get_visible_headers(self):
        """Get only the visible column headers in order.
        
        Returns:
            list: List of visible column header names in order
        """
        return [h for h in self._headers if h in self._visible_columns] 