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
    - Multi-level sorting with configurable primary/secondary sort columns
    """
    
    # Signals
    dataChanged = QtCore.Signal()
    loadingStarted = QtCore.Signal()
    loadingFinished = QtCore.Signal()
    loadingProgress = QtCore.Signal(int, str)
    debugInfo = QtCore.Signal(str)
    sortOrderChanged = QtCore.Signal(int, int)  # primary_column, secondary_column
    dataSorted = QtCore.Signal()  # Emitted when data is reordered (not reloaded)
    
    def __init__(self, settings_model=None, parent=None):
        """Initialize the table data model.
        
        Args:
            settings_model: Optional settings model for inheritance
            parent: Parent QObject
        """
        super().__init__(parent)
        self._data = []
        self._headers = TableColumns.HEADERS.copy()
        
        # Settings integration
        self.settings_model = settings_model
        
        # Real data integration attributes  
        self._node_data_provider = None
        self._settings_storage = None
        
        # Column visibility tracking
        self._visible_columns = set(self._headers)  # All columns visible by default
        
        # Multi-level sorting state
        self._primary_sort_column = None  # Initially None, will be set by _set_initial_sort_order
        self._secondary_sort_column = None  
        self._primary_sort_order = QtCore.Qt.AscendingOrder
        self._secondary_sort_order = QtCore.Qt.AscendingOrder
        
        # Track initial data state to prevent multiple redraws
        self._has_initial_data = False
        
        # Set initial sort order (Order primary, Node secondary)
        self._set_initial_sort_order()
        
    def _set_initial_sort_order(self):
        """Set the initial sort order: Order (primary) and Node (secondary)."""
        try:
            # Find Order column index
            order_column = self._headers.index("Order") if "Order" in self._headers else None
            # Find Node column index  
            node_column = self._headers.index("Node") if "Node" in self._headers else None
            
            if order_column is not None:
                self._primary_sort_column = order_column
                self._primary_sort_order = QtCore.Qt.AscendingOrder
                
            if node_column is not None:
                self._secondary_sort_column = node_column
                self._secondary_sort_order = QtCore.Qt.AscendingOrder
                
        except ValueError:
            # Fallback if columns not found
            self._primary_sort_column = 0 if len(self._headers) > 0 else None
            self._secondary_sort_column = 1 if len(self._headers) > 1 else None
            
    def apply_sort(self, clicked_column, clicked_order):
        """Apply multi-level sorting when a column header is clicked.
        
        Args:
            clicked_column (int): Column index that was clicked
            clicked_order (int): Qt.AscendingOrder or Qt.DescendingOrder
        """
        # Store the previous primary as the new secondary
        if self._primary_sort_column is not None and self._primary_sort_column != clicked_column:
            self._secondary_sort_column = self._primary_sort_column
            self._secondary_sort_order = self._primary_sort_order
        
        # Set the clicked column as the new primary
        self._primary_sort_column = clicked_column
        self._primary_sort_order = clicked_order
        
        # Apply the sort
        self._sort_data()
        
        # Emit signals - use dataSorted instead of dataChanged to avoid full reload
        self.sortOrderChanged.emit(self._primary_sort_column or -1, self._secondary_sort_column or -1)
        self.dataSorted.emit()
        
    def _sort_data(self):
        """Sort the data using multi-level sorting logic."""
        if not self._data or self._primary_sort_column is None:
            return
            
        def sort_key(row_data):
            """Generate sort key for a row using primary and secondary columns."""
            # Get primary sort value
            primary_header = self._headers[self._primary_sort_column]
            primary_value = row_data.get(primary_header, "")
            
            # Convert to appropriate type for sorting
            primary_sort_value = self._convert_value_for_sorting(primary_value)
            
            # Get secondary sort value if secondary column is set
            secondary_sort_value = ""
            if self._secondary_sort_column is not None:
                secondary_header = self._headers[self._secondary_sort_column]
                secondary_value = row_data.get(secondary_header, "")
                secondary_sort_value = self._convert_value_for_sorting(secondary_value)
            
            # Return tuple for multi-level sorting
            # Reverse for descending order by using negative values for numeric types
            if self._primary_sort_order == QtCore.Qt.DescendingOrder:
                if isinstance(primary_sort_value, (int, float)):
                    primary_sort_value = -primary_sort_value
                else:
                    # For strings, we'll reverse the list after sorting
                    pass
            
            if self._secondary_sort_column is not None and self._secondary_sort_order == QtCore.Qt.DescendingOrder:
                if isinstance(secondary_sort_value, (int, float)):
                    secondary_sort_value = -secondary_sort_value
                    
            return (primary_sort_value, secondary_sort_value)
        
        # Sort the data
        reverse_primary = (self._primary_sort_order == QtCore.Qt.DescendingOrder and 
                          isinstance(sort_key(self._data[0])[0] if self._data else "", str))
        
        self._data.sort(key=sort_key, reverse=reverse_primary)
    
    def _convert_value_for_sorting(self, value):
        """Convert a value to an appropriate type for sorting.
        
        Args:
            value: Raw value from the data
            
        Returns:
            Converted value suitable for sorting
        """
        if value is None or value == "":
            return ""
            
        value_str = str(value)
        
        # Try to convert to int first
        try:
            return int(value_str)
        except ValueError:
            pass
            
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            pass
            
        # Return as lowercase string for case-insensitive sorting
        return value_str.lower()
    
    def get_sort_state(self):
        """Get the current sort state.
        
        Returns:
            tuple: (primary_column, primary_order, secondary_column, secondary_order)
        """
        return (
            self._primary_sort_column,
            self._primary_sort_order, 
            self._secondary_sort_column,
            self._secondary_sort_order
        )
        
    def apply_initial_sort(self):
        """Apply the initial sort order to the data."""
        if self._data and self._primary_sort_column is not None:
            self._sort_data()
            # Don't emit dataSorted for initial sort - it will be handled by dataChanged
    
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
            node_data_provider: The NodeDataWorker instance
        """
        self._node_data_provider = node_data_provider
        
        # Connect signals
        if self._node_data_provider:
            self._node_data_provider.signals.data_ready.connect(self._on_data_ready)
            self._node_data_provider.signals.progress_update.connect(self._on_progress_update)
            self._node_data_provider.signals.error_occurred.connect(self._on_error_occurred)
            self._node_data_provider.signals.debug_info.connect(self._on_debug_info)
    
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
            
            # Store the current sort state before updating data
            current_sort_state = self.get_sort_state()
            
            # Update table data
            old_data_count = len(self._data)
            self._data = merged_data
            new_data_count = len(self._data)
            
            # Apply sorting - preserve current sort state if we have data, use initial sort if empty
            if old_data_count == 0:
                # Empty table - apply initial sort (Order primary, Node secondary)
                self.apply_initial_sort()
            else:
                # Table had data - preserve current sort state
                if current_sort_state[0] is not None:  # If we have a valid primary sort
                    self._primary_sort_column = current_sort_state[0]
                    self._primary_sort_order = current_sort_state[1]
                    self._secondary_sort_column = current_sort_state[2]
                    self._secondary_sort_order = current_sort_state[3]
                    self._sort_data()
            
            # Determine signal to emit based on whether table was empty
            if old_data_count == 0:
                # Empty table needs full reload (dataChanged)
                self._has_initial_data = True
                self.dataChanged.emit()
            else:
                # Table had data - use dataSorted to preserve column widths
                self.dataSorted.emit()
            
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
    
    def _on_debug_info(self, debug_message):
        """Handle debug information from node data provider.
        
        Args:
            debug_message: Debug message from the provider
        """
        # Re-emit to UI components
        self.debugInfo.emit(debug_message)
    
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
        
        # Load render selections from storage (special key in node overrides)
        render_selections = self._load_render_selections_from_storage()
        
        from ....common.logging import qt_logger
        qt_logger.debug(f"📖 Loaded render selections from storage: {render_selections}")
        
        # Merge data
        merged_data = []
        for i, node_data in enumerate(node_data_list):
            node_name = node_data.get('Node', '')
            
            # Start with fresh node data
            merged_row = node_data.copy()
            
            # CRITICAL: Initialize Render column from storage or default to True for new nodes
            if node_name in render_selections:
                # Use stored render selection
                merged_row['Render'] = render_selections[node_name]
            else:
                # New node - default to checked (True)
                merged_row['Render'] = True
            
            # Apply any stored overrides
            if node_name in node_overrides:
                overrides = node_overrides[node_name]
                for column, override_value in overrides.items():
                    if override_value is not None:  # None means inherit
                        old_value = merged_row.get(column)
                        merged_row[column] = override_value
            else:
                pass  # No overrides found for this node
            
            merged_data.append(merged_row)
        
        return merged_data
        
    def set_data(self, data):
        """Set the table data.
        
        Args:
            data (list): List of dictionaries, one per row
        """
        from ....common.logging import qt_logger
        qt_logger.debug(f"📊 TableDataModel.set_data() called with {len(data) if data else 0} rows")
        
        # Ensure all rows have explicit Render column values
        processed_data = []
        for row_data in (data or []):
            row_copy = row_data.copy()
            # Ensure Render column is explicitly set - default to True if missing
            if 'Render' not in row_copy:
                row_copy['Render'] = True
            processed_data.append(row_copy)
        
        self._data = processed_data
        
        qt_logger.debug(f"📊 Emitting dataChanged signal")
        self.dataChanged.emit()
        qt_logger.debug(f"📊 TableDataModel.set_data() completed")
    
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
            str, bool, or None: Cell value, None if should inherit, or empty string if bounds invalid
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return ""
        
        header = self._headers[column]
        
        # Handle checkbox column specially
        if header == "Render":
            # Return boolean value, should always be explicit now
            return self._data[row].get(header, False)  # False as fallback (should not happen)
        
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
        inherited_value = self._get_inherited_value(column)
        
        return inherited_value
    
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
            value: Value to set (None means inherit from settings, bool for checkbox)
            emit_signal (bool): Whether to emit dataChanged signal
        """
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return
        
        header = self._headers[column]
        
        # Handle checkbox column
        if header == "Render":
            # Store as boolean
            bool_value = bool(value) if value is not None else True
            old_value = self._data[row].get(header, True)
            
            from ....common.logging import qt_logger
            node_name = self._data[row].get("Node", "")
            qt_logger.debug(f"💾 TableModel.set_cell_value() Render column: row={row}, node={node_name}, old={old_value}, new={bool_value}")
            
            if old_value != bool_value:
                self._data[row][header] = bool_value
                
                # PERFORMANCE: Only save to storage if emit_signal is True (indicating individual user action)
                # When emit_signal=False, it's a batch operation and storage will be saved externally
                if emit_signal and self._settings_storage:
                    qt_logger.debug(f"💾 Saving render selections to storage for node: {node_name}")
                    self._save_render_selections_to_storage()
                elif not self._settings_storage:
                    qt_logger.warning("💾 No settings storage available - cannot save render selections!")
                
                if emit_signal:
                    self.dataChanged.emit()
            else:
                qt_logger.debug(f"💾 No change needed: old_value {old_value} == new_value {bool_value}")
            return
        
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
                if n.fullName() == node_name:
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
        
        # Render column is editable (checkbox toggle)
        if header == "Render":
            return True
        
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
        
        dropdown_columns = TableColumns.get_dropdown_columns()
        return column in dropdown_columns
    
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
    
    def get_node_name(self, row):
        """Get the node name for a specific row.
        
        Args:
            row (int): Row index
            
        Returns:
            str: Node name or empty string if not found
        """
        if row < 0 or row >= len(self._data):
            return ""
        
        # Find the Node column index
        try:
            node_column = self._headers.index("Node")
            return self._data[row].get("Node", "")
        except (ValueError, KeyError):
            return ""
    
    def is_node_selected_for_render(self, row):
        """Check if a node is selected for rendering.
        
        Args:
            row (int): Row index
            
        Returns:
            bool: True if node is selected for rendering, False otherwise
        """
        if row < 0 or row >= len(self._data):
            return False
        
        # Get the render checkbox value from the "Render" column
        try:
            render_value = self._data[row].get("Render", False)  # Should always be explicit now
            return bool(render_value)
        except (ValueError, KeyError):
            return False 
    
    def _load_render_selections_from_storage(self):
        """Load render selections from storage using special key.
        
        Returns:
            dict: Node name -> render selection boolean
        """
        if not self._settings_storage:
            return {}
        
        try:
            # Load node overrides directly (don't use sync_with_current_nodes for _render list)
            node_overrides = self._settings_storage.load_node_overrides()
            
            # Check if we have stored render selections (stored as a list)
            render_list = node_overrides.get('_render', [])
            
            if isinstance(render_list, list):
                if len(render_list) == 0:
                    # Empty _render list means "render all nodes" (optimization)
                    from ....common.logging import qt_logger
                    qt_logger.debug("💾 Empty _render list found - all nodes should be selected")
                    render_selections = {}
                    for row_data in self._data:
                        node_name = row_data.get('Node', '')
                        if node_name:
                            render_selections[node_name] = True  # All nodes selected
                    return render_selections
                else:
                    # Non-empty list - only listed nodes are selected
                    render_selections = {}
                    for row_data in self._data:
                        node_name = row_data.get('Node', '')
                        if node_name:
                            render_selections[node_name] = node_name in render_list
                    return render_selections
            else:
                # No stored render selections or wrong format, return empty dict (will default to True)
                return {}
                
        except Exception as e:
            # If there's any error loading, return empty dict (all default to True)
            from ....common.logging import qt_logger
            qt_logger.debug(f"Could not load render selections from storage: {e}")
            return {}
    
    def _save_render_selections_to_storage(self):
        """Save current render selections to storage using special key."""
        if not self._settings_storage:
            return
        
        try:
            # Collect only the nodes that are selected for rendering
            selected_nodes = []
            total_nodes = 0
            for row_data in self._data:
                node_name = row_data.get('Node', '')
                is_selected = row_data.get('Render', True)
                if node_name:
                    total_nodes += 1
                    if is_selected:
                        selected_nodes.append(node_name)
            
            from ....common.logging import qt_logger
            
            # Optimization: If all nodes are selected, don't store the _render list
            # An empty _render list means "render all nodes"
            if len(selected_nodes) == total_nodes and total_nodes > 0:
                # All nodes are selected - remove _render entry to indicate "render all"
                node_overrides = self._settings_storage.load_node_overrides()
                if '_render' in node_overrides:
                    del node_overrides['_render']
                    qt_logger.debug("💾 All nodes selected - removing _render entry (render all)")
                else:
                    qt_logger.debug("💾 All nodes selected - no _render entry needed (render all)")
            else:
                # Some nodes are not selected - store the list of selected nodes
                qt_logger.debug(f"💾 Saving selected render nodes to storage: {selected_nodes}")
                node_overrides = self._settings_storage.load_node_overrides()
                node_overrides['_render'] = selected_nodes
            
            # Save the updated overrides
            success = self._settings_storage.save_node_overrides(node_overrides)
            
            if success:
                qt_logger.debug("💾 Render selections saved successfully to storage")
            else:
                qt_logger.warning("💾 Failed to save render selections to storage")
            
        except Exception as e:
            # Log error but don't fail - render selections are not critical for app function
            from ....common.logging import qt_logger
            qt_logger.warning(f"Failed to save render selections to storage: {e}") 