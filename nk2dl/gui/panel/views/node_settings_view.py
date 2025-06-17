# -*- coding: utf-8 -*-
"""NodeSettingsView component for the nk2dl panel.

This module contains the NodeSettingsView class which handles the UI for the node settings table
(formerly render order), including the table widget, control buttons, filter functionality, and
settings inheritance system.
"""

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from ..widgets import ColoredGroupBox
from ..constants import Settings, Sizes, GSVDefaults


class NodeSettingsView(QtWidgets.QWidget):
    """View for the node settings table with controls.
    
    This view handles the UI for the node settings table (formerly render order),
    including the table widget, control buttons, filter functionality, and
    settings inheritance system.
    """
    
    def __init__(self, table_model, settings_model=None, parent=None):
        super().__init__(parent)
        self.table_model = table_model
        self.settings_model = settings_model
        
        # Connect settings model to table model for inheritance
        if self.settings_model:
            self.table_model.set_settings_model(self.settings_model)
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_data_from_model()
    
    def _create_ui(self):
        """Create the node settings UI components."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Control buttons with filter
        self._create_control_buttons()
        layout.addLayout(self.button_layout)
        
        # Create the table
        self._create_table()
        layout.addWidget(self.render_table)
        
        # Set stretch factor to make table expand
        layout.setStretchFactor(self.render_table, 1)
    
    def _create_control_buttons(self):
        """Create the control buttons and filter."""
        self.button_layout = QtWidgets.QHBoxLayout()
        
        self.update_btn = QtWidgets.QPushButton("Update")
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.button_layout.addWidget(self.update_btn)
        
        self.all_btn = QtWidgets.QPushButton("All")
        self.all_btn.clicked.connect(self._on_all_clicked)
        self.button_layout.addWidget(self.all_btn)
        
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.button_layout.addWidget(self.clear_btn)
        
        self.selection_btn = QtWidgets.QPushButton("Selection")
        self.selection_btn.clicked.connect(self._on_selection_clicked)
        self.button_layout.addWidget(self.selection_btn)
        
        self.inside_groups_check = QtWidgets.QCheckBox("Inside groups")
        self.inside_groups_check.stateChanged.connect(self._on_inside_groups_changed)
        self.button_layout.addWidget(self.inside_groups_check)
        
        # Add spacer to push column dropdown and filter to the right
        self.button_layout.addStretch()
        
        # Column visibility dropdown
        from ..widgets import ColumnVisibilityDropdown
        self.column_dropdown = ColumnVisibilityDropdown()
        self.column_dropdown.column_visibility_changed.connect(self._on_column_visibility_changed)
        self.button_layout.addWidget(self.column_dropdown)
        
        # Filter input on same row
        self.button_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("filter...")
        self.filter_edit.setMaximumWidth(Sizes.FILTER_EDIT_WIDTH)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        self.button_layout.addWidget(self.filter_edit)
    
    def _create_table(self):
        """Create the node settings table."""
        from ..widgets import FrozenTableWidget, CustomHeaderView
        from ..delegates import SettingsAwareDelegate
        from ..constants import TableColumns
        
        self.render_table = FrozenTableWidget()
        self.render_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Set up settings-aware delegate for inheritance and override styling
        self.settings_delegate = SettingsAwareDelegate(self.table_model)
        self.render_table.setItemDelegate(self.settings_delegate)
        
        # Set up table headers with display names
        headers = self.table_model.get_headers()
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(display_headers)
        
        # Apply custom header view for job/machine settings styling
        custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.render_table)
        self.render_table.setHorizontalHeader(custom_header)
        
        # Also apply custom header to frozen table if it exists
        if hasattr(self.render_table, 'frozen_table'):
            frozen_custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.render_table.frozen_table)
            self.render_table.frozen_table.setHorizontalHeader(frozen_custom_header)
            
            # CRITICAL: Reconnect synchronization signals after replacing headers
            # The original signals were disconnected when we replaced the headers
            # Connect the main header's sectionResized signal to the frozen table update method
            custom_header.sectionResized.connect(self.render_table._update_frozen_section_width)
        
        # Connect table signals
        self.render_table.itemChanged.connect(self._on_table_item_changed)
        
        # Table properties are already set in FrozenTableWidget constructor
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.table_model.dataChanged.connect(self._on_model_data_changed)
        
        # Connect settings model change signals to refresh table
        if self.settings_model:
            self.settings_model.jobSettingsChanged.connect(self._on_settings_changed)
            self.settings_model.machineSettingsChanged.connect(self._on_settings_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the table widget."""
        # Block signals during loading to prevent unwanted updates
        self.render_table.blockSignals(True)
        
        try:
            # Get data from model
            data = self.table_model.get_data()
            headers = self.table_model.get_headers()
            
            # Set table size
            self.render_table.setRowCount(len(data))
            
            # Populate table with raw values, but display effective values
            for row, row_data in enumerate(data):
                for col, header in enumerate(headers):
                    # Get raw cell value (may be None for inheritance)
                    raw_value = self.table_model.get_cell_value(row, col)
                    
                    # Create item with raw value for data storage
                    if raw_value is None:
                        # For None values, store empty string but mark as inherited
                        item = QtWidgets.QTableWidgetItem("")
                        item.setData(QtCore.Qt.UserRole, None)  # Store None in user data
                    else:
                        # For explicit values, store the actual value
                        item = QtWidgets.QTableWidgetItem(str(raw_value))
                        item.setData(QtCore.Qt.UserRole, raw_value)
                    
                    # Set display text to effective value (for inheritance display)
                    effective_value = self.table_model.get_effective_cell_value(row, col)
                    item.setText(str(effective_value))
                    
                    # Apply styling based on whether cell is overridden
                    self._apply_cell_styling(item, row, col)
                    
                    self.render_table.setItem(row, col, item)
                    
                    # Sync to frozen table if this is a frozen column
                    self._sync_frozen_item(row, col, item)
            
            # Resize columns to content
            self.render_table.resizeColumnsToContents()
            
        finally:
            # Re-enable signals after loading is complete
            self.render_table.blockSignals(False)
    
    def _apply_cell_styling(self, item, row, col):
        """Apply styling to table cell items based on override status."""
        # Don't apply bold styling to frozen columns (Order, Node, Filename)
        # since they don't support inheritance and are always explicit
        if (hasattr(self.render_table, 'frozen_column_count') and 
            col < self.render_table.frozen_column_count):
            # Frozen columns use normal font and default text color
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            item.setForeground(QtGui.QBrush())
            return
        
        # Check if cell is overridden (has explicit value different from inherited)
        is_overridden = self.table_model.is_cell_overridden(row, col)
        
        if is_overridden:
            # Bold font for override values
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            # White text for explicit values
            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        else:
            # Normal font for inherited values
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            # Default text color for inherited values
            item.setForeground(QtGui.QBrush())
    
    def _sync_frozen_item(self, row, col, item):
        """Sync item to frozen table if it's in a frozen column."""
        # Check if this table has frozen columns and if column is frozen
        if (hasattr(self.render_table, 'frozen_table') and 
            hasattr(self.render_table, 'frozen_column_count') and
            col < self.render_table.frozen_column_count):
            
            # Create a copy of the item for the frozen table
            frozen_item = QtWidgets.QTableWidgetItem(item.text())
            frozen_item.setData(QtCore.Qt.UserRole, item.data(QtCore.Qt.UserRole))
            frozen_item.setFont(item.font())
            frozen_item.setForeground(item.foreground())
            frozen_item.setBackground(item.background())
            
            # Set the item in the frozen table
            self.render_table.frozen_table.setItem(row, col, frozen_item)
    
    def _on_table_item_changed(self, item):
        """Handle table item changes and update the model."""
        if not item:
            return
        
        # Block signals to prevent recursive calls
        self.render_table.blockSignals(True)
        
        try:
            row = item.row()
            col = item.column()
            text_value = item.text()
            
            # Determine the value to store in the model
            if text_value.strip() == "":
                # Empty string means user wants to inherit from settings
                model_value = None
            else:
                # Non-empty string is an explicit value
                model_value = text_value
            
            # Update the model with the appropriate value (suppress signal to prevent full reload)
            self.table_model.set_cell_value(row, col, model_value, emit_signal=False)
            
            # Update the item's user data to reflect the stored value
            item.setData(QtCore.Qt.UserRole, model_value)
            
            # Update display text to show effective value (may be inherited)
            effective_value = self.table_model.get_effective_cell_value(row, col)
            item.setText(str(effective_value))
            
            # Refresh styling for this cell only
            self._apply_cell_styling(item, row, col)
            
            # Sync to frozen table if this is a frozen column
            self._sync_frozen_item(row, col, item)
            
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
    
    def _on_model_data_changed(self):
        """Handle model data changes."""
        # Refresh the table display
        self._load_data_from_model()
    
    def _on_settings_changed(self):
        """Handle settings model changes - refresh table to show updated inherited values."""
        # Update only inherited cells instead of reloading entire table
        self._update_inherited_cells()
    
    def _update_inherited_cells(self):
        """Update only cells that inherit from settings."""
        # Block signals to prevent recursive updates
        self.render_table.blockSignals(True)
        
        try:
            for row in range(self.render_table.rowCount()):
                for col in range(self.render_table.columnCount()):
                    # Check if this cell is inherited (not overridden)
                    if not self.table_model.is_cell_overridden(row, col):
                        item = self.render_table.item(row, col)
                        if item:
                            # Update display text with new inherited value
                            effective_value = self.table_model.get_effective_cell_value(row, col)
                            item.setText(str(effective_value))
                            
                            # Refresh styling
                            self._apply_cell_styling(item, row, col)
                            
                            # Sync to frozen table if this is a frozen column
                            self._sync_frozen_item(row, col, item)
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
    
    def _on_filter_changed(self, text):
        """Handle filter text changes."""
        # TODO: Implement filtering logic
        # For now, just store the filter text
        self.current_filter = text.lower()
    
    def _on_inside_groups_changed(self, state):
        """Handle inside groups checkbox changes."""
        # TODO: Implement inside groups logic
        checked = state == QtCore.Qt.Checked
        print(f"Inside groups: {checked}")
    
    def _on_update_clicked(self):
        """Handle update button click."""
        if NUKE_AVAILABLE:
            nuke.message('Update functionality will be implemented in the final integration phase.')
        else:
            print("Update functionality will be implemented in the final integration phase.")
    
    def _on_all_clicked(self):
        """Handle all button click."""
        if NUKE_AVAILABLE:
            nuke.message('All functionality will be implemented in the final integration phase.')
        else:
            print("All functionality will be implemented in the final integration phase.")
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        # Clear all data
        self.table_model.set_data([])
    
    def _on_selection_clicked(self):
        """Handle selection button click."""
        if NUKE_AVAILABLE:
            nuke.message('Selection functionality will be implemented in the final integration phase.')
        else:
            print("Selection functionality will be implemented in the final integration phase.")
    
    def _on_column_visibility_changed(self):
        """Handle column visibility changes."""
        visible_columns = self.column_dropdown.get_visible_columns()
        
        # Update the table model
        self.table_model.set_visible_columns(visible_columns)
        
        # Hide/show columns in the table widget
        headers = self.table_model.get_headers()
        for i, header in enumerate(headers):
            column_visible = header in visible_columns
            self.render_table.setColumnHidden(i, not column_visible)
            
            # Also hide in frozen table if applicable
            if (hasattr(self.render_table, 'frozen_table') and 
                hasattr(self.render_table, 'frozen_column_count') and
                i < self.render_table.frozen_column_count):
                self.render_table.frozen_table.setColumnHidden(i, not column_visible)
    
    def get_table_model(self):
        """Get the table model.
        
        Returns:
            TableDataModel: The table model instance
        """
        return self.table_model
    
    def get_effective_values(self):
        """Get effective values from the table model.
        
        Returns:
            list: List of effective row values
        """
        return self.table_model.get_data()