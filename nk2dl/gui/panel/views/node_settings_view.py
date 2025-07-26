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
from ..constants import Settings, Sizes, GSVDefaults, Timing
from ..config import apply_panel_config
from ....common.logging import setup_logging

# Create logger for this module
logger = setup_logging('nk2dl.gui.panel.views.node_settings_view')


class NodeSettingsView(QtWidgets.QWidget):
    """View for the node settings table with controls.
    
    This view handles the UI for the node settings table (formerly render order),
    including the table widget, control buttons, filter functionality, and
    settings inheritance system.
    """
    
    def __init__(self, table_model, settings_model=None, parent=None):
        """Initialize the NodeSettingsView widget."""
        super().__init__(parent)
        
        self.table_model = table_model
        self.settings_model = settings_model
        
        # Initialize filter text
        self.filter_text = ""
        
        # Track refresh state to prevent unwanted updates during refresh
        self._is_refreshing = False
        
        # Track column widths to preserve them during updates  
        self._stored_column_widths = None
        
        # Skip next data loaded recalculation flag
        self._skip_next_data_loaded_recalculation = False
        
        # Add recursion guard for signal handling
        self._handling_checkbox_change = False
        
        self._create_ui()
        self._connect_signals()
        self._connect_table_events()
        
        # Load initial data
        self._load_data_from_model()
    
    def _connect_table_events(self):
        """Connect to table events for responsive column width calculation."""
        # Connect to table show event for initial column width calculation
        # This ensures the table is fully visible and fonts are properly loaded
        if hasattr(self.render_table, 'showEvent'):
            original_show_event = self.render_table.showEvent
            
            def enhanced_show_event(event):
                # Call original show event first
                if original_show_event:
                    original_show_event(event)
                
                # Calculate column widths when table becomes visible
                self._on_table_ready_for_sizing()
            
            self.render_table.showEvent = enhanced_show_event
        
        # Also connect to resize events for responsive column width updates
        if hasattr(self.render_table, 'resizeEvent'):
            original_resize_event = self.render_table.resizeEvent
            
            def enhanced_resize_event(event):
                # Call original resize event first
                if original_resize_event:
                    original_resize_event(event)
                
                # Recalculate column widths on significant size changes
                if event.size().width() != event.oldSize().width():
                    self._on_table_width_changed()
            
            self.render_table.resizeEvent = enhanced_resize_event

    def _on_table_ready_for_sizing(self):
        """Handle table ready for initial column width calculation."""
        try:
            from ....common.logging import qt_logger
            
            if hasattr(self, 'render_table') and self.render_table and hasattr(self.render_table, 'calculate_optimal_column_widths'):
                qt_logger.debug("Event-based column width calculation (table ready)")
                self.render_table.calculate_optimal_column_widths()
            else:
                qt_logger.debug("Event-based column width calculation skipped - table not ready")
                
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in event-based column width calculation: {e}")

    def _on_table_width_changed(self):
        """Handle table width changes for responsive column sizing."""
        try:
            from ....common.logging import qt_logger
            
            # FIXED: Never trigger column width recalculations on resize events
            # Column widths should only be calculated when data actually changes, not when window resizes
            # This prevents all resize-triggered flickering regardless of table state
            qt_logger.debug("Window resize event - skipping column width recalculation (resize events never trigger recalculations)")
                
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in width change handling: {e}")

    def _emit_data_loaded_event(self, data):
        """Emit a custom event when data loading is complete."""
        try:
            from ....common.logging import qt_logger
            
            # Use QTimer.singleShot with 0ms delay to queue the column width calculation
            # This ensures it runs after the current event loop iteration completes
            # and all table items are fully rendered
            QtCore.QTimer.singleShot(0, lambda: self._on_data_loaded(data))
            
            qt_logger.debug("Data loaded event queued for column width calculation")
            
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in data loaded event emission: {e}")

    def _on_data_loaded(self, data):
        """Handle data loaded event for column width calculation."""
        try:
            from ....common.logging import qt_logger
            
            # FIXED: Skip redundant recalculation if we just did one during button operation
            # This prevents the double recalculation cycle that causes flickering
            if getattr(self, '_skip_next_data_loaded_recalculation', False):
                qt_logger.debug("Event-based column width calculation skipped - redundant recalculation prevented")
                self._skip_next_data_loaded_recalculation = False  # Reset the flag
                return
            
            # Calculate column widths when data changes (both loading and clearing)
            qt_logger.debug("Event-based column width calculation (data changed)")
            
            if hasattr(self, 'render_table') and self.render_table and hasattr(self.render_table, 'calculate_optimal_column_widths'):
                self.render_table.calculate_optimal_column_widths(data)
            else:
                qt_logger.debug("Event-based column width calculation skipped - table not ready")
                
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in data loaded column width calculation: {e}")

    def _schedule_frozen_table_update(self):
        """Schedule frozen table geometry update via event queue."""
        try:
            from ....common.logging import qt_logger
            
            # Queue geometry update to happen after current event processing
            QtCore.QTimer.singleShot(0, self._on_frozen_table_geometry_ready)
            
            qt_logger.debug("Frozen table geometry update scheduled")
            
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in frozen table update scheduling: {e}")

    def _on_frozen_table_geometry_ready(self):
        """Handle frozen table geometry ready event."""
        try:
            from ....common.logging import qt_logger
            
            if hasattr(self.render_table, '_update_frozen_table_geometry'):
                qt_logger.debug("Event-based frozen table geometry update")
                self.render_table._update_frozen_table_geometry()
                
                # Queue a repaint after geometry update
                QtCore.QTimer.singleShot(0, self._on_frozen_table_repaint_ready)
            else:
                qt_logger.debug("Event-based frozen table geometry update skipped - method not available")
                
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in frozen table geometry update: {e}")

    def _on_frozen_table_repaint_ready(self):
        """Handle frozen table repaint ready event."""
        try:
            from ....common.logging import qt_logger
            
            if hasattr(self.render_table, 'frozen_table'):
                qt_logger.debug("Event-based frozen table repaint")
                self.render_table.frozen_table.update()
            else:
                qt_logger.debug("Event-based frozen table repaint skipped - frozen table not available")
                
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.error(f"Exception in frozen table repaint: {e}")
    
    def _create_ui(self):
        """Create the node settings UI components."""
        from ....common.logging import qt_logger
        qt_logger.debug("_create_ui() called")
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Control buttons with filter
        qt_logger.debug("About to call _create_control_buttons()")
        self._create_control_buttons()
        layout.addLayout(self.button_layout)
        
        # Create the table
        qt_logger.debug("About to call _create_table()")
        self._create_table()
        layout.addWidget(self.render_table)
        qt_logger.debug("Table added to layout")
        
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
        from ....common.logging import qt_logger
        qt_logger.debug("Starting _create_table method")
        from ..widgets import FrozenTableWidget, CustomHeaderView
        from ..constants import TableColumns
        
        qt_logger.debug("About to create FrozenTableWidget")
        self.render_table = FrozenTableWidget()
        qt_logger.debug("Created FrozenTableWidget successfully")
        self.render_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Set up combined delegate for both checkboxes and settings inheritance
        from ..delegates import CombinedTableDelegate
        self.combined_delegate = CombinedTableDelegate(self.table_model)
        self.render_table.setItemDelegate(self.combined_delegate)
        
        # Set up table headers with display names
        headers = self.table_model.get_headers()
        display_headers = [TableColumns.HEADER_DISPLAY_NAMES.get(h, h) for h in headers]
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(display_headers)
        
        # Calculate initial column widths BEFORE applying custom headers to prevent flashing
        # This sets proper widths immediately instead of waiting for events
        qt_logger.debug("Setting initial column widths during table creation")
        self._set_initial_column_widths(headers)
        
        # Apply custom header view for job/machine settings styling
        custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.render_table)
        self.render_table.setHorizontalHeader(custom_header)
        
        # Re-apply display headers after custom header is set to ensure they're preserved
        self.render_table.setHorizontalHeaderLabels(display_headers)
        qt_logger.debug(f"Set display headers: {display_headers[:5]}...")  # Show first 5
        
        # Also apply custom header to frozen table if it exists
        if hasattr(self.render_table, 'frozen_table'):
            logger.debug(f"Setting up frozen table with {self.render_table.frozen_column_count} frozen columns")
            
            frozen_custom_header = CustomHeaderView(QtCore.Qt.Horizontal, self.render_table.frozen_table)
            self.render_table.frozen_table.setHorizontalHeader(frozen_custom_header)
            
            # Re-apply display headers to frozen table after custom header is set
            self.render_table.frozen_table.setHorizontalHeaderLabels(display_headers)
            qt_logger.debug(f"Set frozen table display headers: {display_headers[:3]}...")  # Show first 3 frozen
            
            # CRITICAL: Reconnect synchronization after replacing headers
            # When we replace headers, the original signal connections are broken
            # Use the FrozenTableWidget's built-in method to restore all synchronization
            self.render_table.reconnect_frozen_signals()
            
            # Schedule frozen table geometry update via event system
            # This ensures proper synchronization without fixed delays
            self._schedule_frozen_table_update()
            
            logger.debug("Frozen table setup completed")
        
        # Connect table signals
        from ....common.logging import qt_logger
        qt_logger.debug("🔗 Connecting table signals...")
        
        # Use only itemChanged signal to handle all checkbox and cell changes
        # This prevents recursive loops from multiple overlapping signal handlers
        self.render_table.itemChanged.connect(self._on_table_item_changed)
        qt_logger.debug("🔗 Connected itemChanged signal")
        
        # Connect signals to frozen table if it exists (for frozen checkbox column)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            qt_logger.debug("🔗 Connecting signals to frozen table")
            self.render_table.frozen_table.itemChanged.connect(self._on_table_item_changed)
        
        # Column widths will be calculated when data is loaded or via timer
        # This prevents multiple calculations during initialization
        
        # Table properties are already set in FrozenTableWidget constructor
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.table_model.dataChanged.connect(self._on_model_data_changed)
        self.table_model.dataSorted.connect(self._on_data_sorted)  # Handle sorting without full reload
        
        # DISABLE Qt's built-in sorting to use our custom multi-level sorting
        self.render_table.setSortingEnabled(False)
        if hasattr(self.render_table, 'frozen_table'):
            self.render_table.frozen_table.setSortingEnabled(False)
            
            # Disconnect frozen table's existing sort signal connections to avoid conflicts
            try:
                self.render_table.horizontalHeader().sortIndicatorChanged.disconnect()
                self.render_table.frozen_table.horizontalHeader().sortIndicatorChanged.disconnect()
            except (TypeError, RuntimeError):
                pass  # Signals may not be connected yet
        
        # Connect sort order changes to update header indicators
        self.table_model.sortOrderChanged.connect(self._on_sort_order_changed)
        
        # Connect header clicks to custom sorting instead of Qt's default
        self.render_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        if hasattr(self.render_table, 'frozen_table'):
            self.render_table.frozen_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
        # Connect settings model change signals to refresh table
        if self.settings_model:
            self.settings_model.jobSettingsChanged.connect(self._on_settings_changed)
            self.settings_model.machineSettingsChanged.connect(self._on_settings_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the table widget."""
        from ....common.logging import qt_logger
        qt_logger.debug("📋 _load_data_from_model() called")
        # Disable sorting during data loading to prevent sorting synchronization
        # from interfering with initial data population. The FrozenTableWidget
        # has complex sorting sync between main and frozen tables that can corrupt
        # data display if triggered during loading.
        sorting_enabled = self.render_table.isSortingEnabled()
        frozen_sorting_enabled = False
        if hasattr(self.render_table, 'frozen_table'):
            frozen_sorting_enabled = self.render_table.frozen_table.isSortingEnabled()
            self.render_table.frozen_table.setSortingEnabled(False)
        self.render_table.setSortingEnabled(False)
        
        # Block signals during loading to prevent unwanted updates
        self.render_table.blockSignals(True)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            self.render_table.frozen_table.blockSignals(True)
        
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
                    
                    # Handle checkbox column specially
                    if col == 0:  # Render column
                        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                        # Get checkbox value from model
                        render_value = self.table_model.get_cell_value(row, col)
                        checkbox_state = QtCore.Qt.Checked if render_value else QtCore.Qt.Unchecked
                        item.setCheckState(checkbox_state)
                        # Don't set text for checkbox column
                        item.setText("")
                        
                        # Debug: Log checkbox creation
                        node_name = self.table_model.get_node_name(row)
                        qt_logger.debug(f"☑️ Created checkbox for row {row}, node '{node_name}', value={render_value}, state={checkbox_state}")
                    else:
                        # Set display text to effective value (for inheritance display)
                        effective_value = self.table_model.get_effective_cell_value(row, col)
                        item.setText(str(effective_value))
                        
                        # Apply styling based on whether cell is overridden
                        self._apply_cell_styling(item, row, col)
                    
                    self.render_table.setItem(row, col, item)
                    
                    # Sync to frozen table if this is a frozen column (use safe method to prevent signals)
                    self._sync_frozen_item_safe(row, col, item)
            
            # Setup column resize modes (particularly important for checkbox column)
            if hasattr(self.render_table, '_setup_column_resize_modes'):
                self.render_table._setup_column_resize_modes()
                
                if len(data) == 0:
                    # FIXED: For clear operations, skip width calculations but preserve geometry updates
                    # This maintains frozen table alignment without triggering column width recalculations
                    qt_logger.debug("📋 Clear operation: Skipping column width calculations, maintaining geometry")
                    
                    # Essential: Schedule delayed geometry update to ensure vertical header width is calculated correctly
                    if hasattr(self.render_table, '_update_frozen_table_geometry'):
                        QtCore.QTimer.singleShot(Timing.FROZEN_TABLE_GEOMETRY_DELAY, self.render_table._update_frozen_table_geometry)
                        qt_logger.debug("📋 Scheduled delayed frozen table geometry update for clear operation")
                else:
                    # FIXED: Skip redundant "data loaded" recalculation since _setup_column_resize_modes 
                    # already calculated optimal column widths during button operations
                    # This prevents the double recalculation cycle that causes flickering
                    self._skip_next_data_loaded_recalculation = True
                    
                    # Emit data loaded event to trigger column width calculation
                    # This event-based approach ensures column widths are calculated
                    # after all data is loaded and the table is properly rendered
                    self._emit_data_loaded_event(data)
                    
                    # Schedule delayed geometry update for data loading to ensure vertical header updates
                    if hasattr(self.render_table, '_update_frozen_table_geometry'):
                        QtCore.QTimer.singleShot(Timing.FROZEN_TABLE_GEOMETRY_DELAY_LOADING, self.render_table._update_frozen_table_geometry)
                        qt_logger.debug("📋 Scheduled delayed frozen table geometry update for data loading")
            
        finally:
            # Re-enable signals after loading is complete
            self.render_table.blockSignals(False)
            if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
                self.render_table.frozen_table.blockSignals(False)
            
            # Keep sorting DISABLED - we use custom multi-level sorting instead of Qt's built-in sorting
            # Note: Qt's sorting is permanently disabled in _connect_signals()
            self.render_table.setSortingEnabled(False)
            if hasattr(self.render_table, 'frozen_table'):
                self.render_table.frozen_table.setSortingEnabled(False)
            

    
    def _apply_cell_styling(self, item, row, col):
        """Apply styling to table cell items based on override status."""
        # Skip styling for Render column (checkbox)
        if col == 0:
            return
            
        # Don't apply highlighting to other frozen columns (Order, Node, Filename)
        # since they don't support inheritance and are always explicit
        if (hasattr(self.render_table, 'frozen_column_count') and 
            col < self.render_table.frozen_column_count):
            # Frozen columns use default colors
            item.setForeground(QtGui.QBrush())
            item.setBackground(QtGui.QBrush())
            return
        
        # Check if cell is overridden (has explicit value different from inherited)
        is_overridden = self.table_model.is_cell_overridden(row, col)
        
        if is_overridden:
            # Use highlight color background for override values (same as other highlightable widgets)
            from ..constants import Colors
            # White text for explicit values
            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            # Light blue background for highlighting (same as other widgets)
            item.setBackground(QtGui.QBrush(QtGui.QColor(Colors.WIDGET_HIGHLIGHT_COLOR)))
        else:
            # Default colors for inherited values
            # Default text color for inherited values
            item.setForeground(QtGui.QBrush())
            # Default background for inherited values
            item.setBackground(QtGui.QBrush())
    
    def _sync_frozen_item(self, row, col, item):
        """Sync item to frozen table if it's in a frozen column."""
        # Check if this table has frozen columns and if column is frozen
        if (hasattr(self.render_table, 'frozen_table') and 
            hasattr(self.render_table, 'frozen_column_count') and
            col < self.render_table.frozen_column_count):
            
            try:
                # Validate the item hasn't been deleted by Qt before accessing its properties
                try:
                    item_text = item.text()
                    item_data = item.data(QtCore.Qt.UserRole)
                    item_font = item.font()
                    item_foreground = item.foreground()
                    item_background = item.background()
                    if col == 0:  # Render column
                        item_checkstate = item.checkState()
                except RuntimeError:
                    # Item has been deleted, skip sync
                    logger.debug(f"Skipping sync for deleted item: row={row}, col={col}")
                    return
                
                # Ensure the frozen table has the correct row count
                if self.render_table.frozen_table.rowCount() <= row:
                    self.render_table.frozen_table.setRowCount(row + 1)
                
                # Create a copy of the item for the frozen table using cached values
                frozen_item = QtWidgets.QTableWidgetItem(item_text)
                frozen_item.setData(QtCore.Qt.UserRole, item_data)
                frozen_item.setFont(item_font)
                frozen_item.setForeground(item_foreground)
                frozen_item.setBackground(item_background)
                
                # Copy checkbox state for render column
                if col == 0:  # Render column
                    frozen_item.setFlags(frozen_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    frozen_item.setCheckState(item_checkstate)
                
                # Set the item in the frozen table
                self.render_table.frozen_table.setItem(row, col, frozen_item)
                
                logger.debug(f"Synced item to frozen table: row={row}, col={col}, text='{item_text}'")
                
            except Exception as e:
                logger.warning(f"Failed to sync item to frozen table: row={row}, col={col}, error={e}")
                
    def _sync_frozen_item_safe(self, row, col, item):
        """Sync item to frozen table with signal blocking to prevent recursion."""
        # Check if this table has frozen columns and if column is frozen
        if (hasattr(self.render_table, 'frozen_table') and 
            hasattr(self.render_table, 'frozen_column_count') and
            col < self.render_table.frozen_column_count):
            
            # Validate the item hasn't been deleted by Qt
            try:
                # Try to access item properties to check if it's still valid
                _ = item.row()
                _ = item.column()
                _ = item.text()
            except RuntimeError:
                # Item has been deleted by Qt, skip sync
                from ....common.logging import qt_logger
                qt_logger.debug(f"🗑️ Skipping sync for deleted item: row={row}, col={col}")
                return
            
            # Block signals on both main and frozen tables during sync
            frozen_table = self.render_table.frozen_table
            main_table = self.render_table
            
            # Block signals on both tables
            frozen_table.blockSignals(True)
            main_table.blockSignals(True)
            
            try:
                self._sync_frozen_item(row, col, item)
            finally:
                # Re-enable signals on both tables
                frozen_table.blockSignals(False)
                main_table.blockSignals(False)
    
    def _on_table_item_changed(self, item):
        """Handle table item changes and update the model."""
        from ....common.logging import qt_logger
        
        # Recursion guard: prevent infinite loops
        if self._handling_checkbox_change:
            qt_logger.debug("🔧 Recursion guard: already handling checkbox change, skipping")
            return
            
        if not item:
            qt_logger.debug("🔧 Item is None, returning")
            return
        
        # Validate the item hasn't been deleted by Qt
        try:
            row = item.row()
            col = item.column()
            text = item.text()
        except RuntimeError:
            qt_logger.debug("🗑️ Item has been deleted by Qt, skipping")
            return
        
        qt_logger.debug(f"🔧 _on_table_item_changed: row={row}, col={col}, text='{text}'")
        
        # Set recursion guard and block all table signals during processing
        self._handling_checkbox_change = True
        
        # Block signals on both main and frozen tables to prevent cascading changes
        self.render_table.blockSignals(True)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            self.render_table.frozen_table.blockSignals(True)
        
        try:
            # Handle checkbox column specially
            if col == 0:  # Render column
                # Get checkbox state and convert to boolean
                checkbox_state = item.checkState()
                model_value = checkbox_state == QtCore.Qt.Checked
                
                qt_logger.debug(f"☑️ Checkbox changed: row={row}, new_value={model_value}")
                
                # For checkboxes, always save to storage (this is an intentional user action)
                self.table_model.set_cell_value(row, col, model_value, emit_signal=True)
                
                # Update the item's user data
                item.setData(QtCore.Qt.UserRole, model_value)
                
                # Sync to frozen table if this is a frozen column (with signal blocking)
                self._sync_frozen_item_safe(row, col, item)
                return
            
            # Handle text columns - only save if user intentionally changed the value
            text_value = item.text()
            
            # Get the current stored value from the model
            current_stored_value = self.table_model.get_cell_value(row, col)
            current_effective_value = self.table_model.get_effective_cell_value(row, col)
            
            # Check if this is a cascading signal from checkbox change vs intentional edit
            if str(current_effective_value) == text_value:
                # This appears to be a cascading signal - the text hasn't actually changed
                # Just update the display but don't save to storage
                qt_logger.debug(f"📄 Cascading signal detected for row={row}, col={col}, keeping inherited value")
                
                # Update the item's user data to keep the current stored value (may be None for inheritance)
                item.setData(QtCore.Qt.UserRole, current_stored_value)
                
                # Refresh styling for this cell only
                self._apply_cell_styling(item, row, col)
                
                # Sync to frozen table if this is a frozen column (with signal blocking)
                self._sync_frozen_item_safe(row, col, item)
                return
            
            # This appears to be an intentional edit - determine the value to store
            if text_value.strip() == "":
                # Empty string means user wants to inherit from settings
                model_value = None
                qt_logger.debug(f"📝 User cleared cell row={row}, col={col} - setting to inherit")
            else:
                # Non-empty string is an explicit value
                model_value = text_value
                qt_logger.debug(f"📝 User edited cell row={row}, col={col} - setting explicit value: {model_value}")
            
            # Save to storage only for intentional edits
            self.table_model.set_cell_value(row, col, model_value, emit_signal=False)
            
            # Update the item's user data to reflect the stored value
            item.setData(QtCore.Qt.UserRole, model_value)
            
            # Update display text to show effective value (may be inherited)
            effective_value = self.table_model.get_effective_cell_value(row, col)
            item.setText(str(effective_value))
            
            # Refresh styling for this cell only
            self._apply_cell_styling(item, row, col)
            
            # Sync to frozen table if this is a frozen column (with signal blocking)
            self._sync_frozen_item_safe(row, col, item)
            
        finally:
            # Re-enable signals on both tables
            self.render_table.blockSignals(False)
            if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
                self.render_table.frozen_table.blockSignals(False)
            
            # Clear recursion guard
            self._handling_checkbox_change = False
    
    def _batch_sync_frozen_checkboxes(self, check_state):
        """Efficiently sync all frozen table checkboxes to the same state.
        
        Args:
            check_state: QtCore.Qt.Checked or QtCore.Qt.Unchecked
        """
        if not (hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table):
            return
        
        try:
            frozen_table = self.render_table.frozen_table
            
            # Update all frozen checkbox items at once
            for row in range(frozen_table.rowCount()):
                frozen_item = frozen_table.item(row, 0)  # Column 0 is Render
                if frozen_item:
                    frozen_item.setCheckState(check_state)
                    
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.warning(f"Error in batch frozen checkbox sync: {e}")
    
    def _batch_sync_frozen_checkboxes_from_main(self):
        """Efficiently sync all frozen table checkboxes from main table states."""
        if not (hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table):
            return
        
        try:
            frozen_table = self.render_table.frozen_table
            
            # Copy checkbox states from main table to frozen table
            for row in range(min(self.render_table.rowCount(), frozen_table.rowCount())):
                main_item = self.render_table.item(row, 0)  # Column 0 is Render
                frozen_item = frozen_table.item(row, 0)
                
                if main_item and frozen_item:
                    frozen_item.setCheckState(main_item.checkState())
                    
        except Exception as e:
            from ....common.logging import qt_logger
            qt_logger.warning(f"Error in batch frozen checkbox sync from main: {e}")
    
    def test_checkbox_signal(self):
        """Debug method to test checkbox signal handling manually."""
        from ....common.logging import qt_logger
        qt_logger.debug("🔧 Manual checkbox test - triggering checkbox change for row 0")
        
        if self.render_table.rowCount() > 0:
            item = self.render_table.item(0, 0)
            if item:
                # Toggle the checkbox state - this should trigger our signal handler
                current_state = item.checkState()
                new_state = QtCore.Qt.Unchecked if current_state == QtCore.Qt.Checked else QtCore.Qt.Checked
                item.setCheckState(new_state)
                qt_logger.debug(f"🔧 Manually changed checkbox from {current_state} to {new_state}")
                qt_logger.debug("🔧 Manual test completed")
    
    def _on_model_data_changed(self):
        """Handle model data changes."""
        from ....common.logging import qt_logger
        qt_logger.debug("📈 _on_model_data_changed() called")
        
        # Refresh the table display
        qt_logger.debug("📈 Calling _load_data_from_model()")
        self._load_data_from_model()
        qt_logger.debug("📈 _load_data_from_model() completed")
        
        # Restore column widths if they were stored before refresh
        if self._stored_column_widths:
            qt_logger.debug("📈 Scheduling _restore_column_widths() with timer")
            # Use a timer to ensure table is fully rendered before restoring widths
            QtCore.QTimer.singleShot(Timing.COLUMN_WIDTH_RESTORE_DELAY, self._restore_column_widths)
        else:
            qt_logger.debug("📈 No stored column widths to restore")
        
        # Reset refresh flag
        qt_logger.debug("📈 Setting _is_refreshing = False")
        self._is_refreshing = False
        qt_logger.debug("📈 _on_model_data_changed() completed")
    
    def _on_data_sorted(self):
        """Handle data sorting without full reload to preserve column widths."""
        # Get the sorted data from the model
        sorted_data = self.table_model.get_data()
        headers = self.table_model.get_headers()
        
        if not sorted_data:
            # Reset refresh flag even if no data
            self._is_refreshing = False
            return
        
        # Check if table is empty - if so, fallback to full data load
        if self.render_table.rowCount() == 0:
            # Table is empty, need full data load instead of reordering
            self._on_model_data_changed()
            return
            
        # Block signals to prevent unwanted updates during reordering  
        self.render_table.blockSignals(True)
        
        try:
            # Store all current table items organized by node name
            current_items_by_node = {}
            for row in range(self.render_table.rowCount()):
                # Get node name from the table item
                node_item = self.render_table.item(row, 2)  # Node is column 2 (after Render)
                if node_item:
                    node_name = node_item.text()
                    current_items_by_node[node_name] = {}
                    
                    # Store all items for this row
                    for col in range(self.render_table.columnCount()):
                        item = self.render_table.takeItem(row, col)
                        if item:
                            current_items_by_node[node_name][col] = item
            
            # Reorder items according to sorted data
            for new_row, row_data in enumerate(sorted_data):
                node_name = row_data.get("Node", "")
                
                if node_name in current_items_by_node:
                    # Move items from stored position to new sorted position
                    for col in range(len(headers)):
                        if col in current_items_by_node[node_name]:
                            item = current_items_by_node[node_name][col]
                            
                            # Update item data with current values from model
                            raw_value = self.table_model.get_cell_value(new_row, col)
                            
                            # Handle checkbox column specially
                            if col == 0:  # Render column
                                item.setData(QtCore.Qt.UserRole, raw_value)
                                checkbox_state = QtCore.Qt.Checked if raw_value else QtCore.Qt.Unchecked
                                item.setCheckState(checkbox_state)
                                item.setText("")  # No text for checkbox
                            else:
                                effective_value = self.table_model.get_effective_cell_value(new_row, col)
                                
                                # Update item data and text
                                item.setData(QtCore.Qt.UserRole, raw_value)
                                item.setText(str(effective_value))
                                
                                # Apply styling 
                                self._apply_cell_styling(item, new_row, col)
                            
                            # Place item in new row position
                            self.render_table.setItem(new_row, col, item)
                            
                            # Sync to frozen table if this is a frozen column
                            self._sync_frozen_item(new_row, col, item)
                        
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
            
            # Reset refresh flag
            self._is_refreshing = False
    
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
                    # Skip columns that don't have settings inheritance (like Render checkbox column)
                    setting_type, setting_key = self.table_model.get_setting_for_column(col)
                    if not setting_type or not setting_key:
                        continue  # Skip columns without settings mapping
                    
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
        self.filter_text = text.lower()
    
    def _on_inside_groups_changed(self, state):
        """Handle inside groups checkbox changes."""
        # TODO: Implement inside groups logic
        checked = state == QtCore.Qt.Checked
        print(f"Inside groups: {checked}")
    
    def _on_update_clicked(self):
        """Handle update button click."""
        from ....common.logging import qt_logger
        qt_logger.debug("🔵 UPDATE BUTTON CLICKED - Starting operation")
        
        # Prevent multiple concurrent refreshes
        if self._is_refreshing:
            qt_logger.debug("Update already in progress, ignoring additional click")
            return
        
        qt_logger.debug("🔵 Checking if need to store column widths...")
        # Store current column widths if table has existing data
        if self.render_table and self.render_table.rowCount() > 0:
            qt_logger.debug("🔵 Calling _store_column_widths()")
            self._store_column_widths()
            qt_logger.debug("🔵 _store_column_widths() completed")
        
        # Mark as refreshing and trigger refresh through the table model
        qt_logger.debug("🔵 Setting _is_refreshing = True")
        self._is_refreshing = True
        if hasattr(self.table_model, 'refresh_from_nodes_async'):
            qt_logger.debug("🔵 Calling table_model.refresh_from_nodes_async()")
            self.table_model.refresh_from_nodes_async()
            qt_logger.debug("🔵 table_model.refresh_from_nodes_async() call completed")
        else:
            # Fallback message if real functionality not available
            qt_logger.debug("🔵 No refresh_from_nodes_async method, using fallback")
            self._is_refreshing = False
            if NUKE_AVAILABLE:
                nuke.message('Update functionality will be implemented in the final integration phase.')
            else:
                print("Update functionality will be implemented in the final integration phase.")
        qt_logger.debug("🔵 UPDATE BUTTON OPERATION COMPLETED")
        
        # DEBUG: Test checkbox signal handling after data is loaded
        QtCore.QTimer.singleShot(1000, self.test_checkbox_signal)
    
    def _on_all_clicked(self):
        """Handle all button click - check all render checkboxes."""
        from ....common.logging import qt_logger
        
        # PERFORMANCE: Enable UI operation mode to throttle debug logging during batch operation
        qt_logger.set_ui_operation_mode(True)
        qt_logger.debug("🟢 ALL BUTTON CLICKED - Checking all render checkboxes")
        
        # Block signals to prevent multiple updates
        self.render_table.blockSignals(True)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            self.render_table.frozen_table.blockSignals(True)
        
        try:
            # PERFORMANCE: Batch update all checkboxes without individual sync operations
            for row in range(self.render_table.rowCount()):
                # Set checkbox to checked in model
                self.table_model.set_cell_value(row, 0, True, emit_signal=False)  # Column 0 is Render
                
                # Update the table item
                item = self.render_table.item(row, 0)
                if item:
                    item.setCheckState(QtCore.Qt.Checked)
            
            # PERFORMANCE: Batch sync all frozen checkboxes at once
            self._batch_sync_frozen_checkboxes(QtCore.Qt.Checked)
            
            # Emit single change signal at the end
            self.table_model.dataChanged.emit()
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
            if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
                self.render_table.frozen_table.blockSignals(False)
            
        # PERFORMANCE: Save to storage only once at the end
        if hasattr(self.table_model, '_save_render_selections_to_storage'):
            self.table_model._save_render_selections_to_storage()
            
        qt_logger.debug("🟢 ALL BUTTON OPERATION COMPLETED")
    
    def _on_clear_clicked(self):
        """Handle clear button click - uncheck all render checkboxes."""
        from ....common.logging import qt_logger
        qt_logger.debug("🔴 CLEAR BUTTON CLICKED - Unchecking all render checkboxes")
        
        # Block signals to prevent multiple updates
        self.render_table.blockSignals(True)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            self.render_table.frozen_table.blockSignals(True)
        
        try:
            # PERFORMANCE: Batch update all checkboxes without individual sync operations
            for row in range(self.render_table.rowCount()):
                # Set checkbox to unchecked in model
                self.table_model.set_cell_value(row, 0, False, emit_signal=False)  # Column 0 is Render
                
                # Update the table item
                item = self.render_table.item(row, 0)
                if item:
                    item.setCheckState(QtCore.Qt.Unchecked)
            
            # PERFORMANCE: Batch sync all frozen checkboxes at once
            self._batch_sync_frozen_checkboxes(QtCore.Qt.Unchecked)
            
            # Emit single change signal at the end
            self.table_model.dataChanged.emit()
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
            if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
                self.render_table.frozen_table.blockSignals(False)
            
        # PERFORMANCE: Save to storage only once at the end
        if hasattr(self.table_model, '_save_render_selections_to_storage'):
            self.table_model._save_render_selections_to_storage()
            
        qt_logger.debug("🔴 CLEAR BUTTON OPERATION COMPLETED")
    
    def _on_selection_clicked(self):
        """Handle selection button click - check render checkboxes for selected nodes only."""
        from ....common.logging import qt_logger
        qt_logger.debug("🟡 SELECTION BUTTON CLICKED - Checking checkboxes for selected nodes")
        
        # Get selected node names from Nuke
        selected_node_names = set()
        if NUKE_AVAILABLE:
            try:
                import nuke
                selected_nodes = nuke.selectedNodes()
                selected_node_names = {node.fullName() for node in selected_nodes}
                qt_logger.debug(f"Found {len(selected_node_names)} selected nodes: {list(selected_node_names)}")
            except Exception as e:
                qt_logger.error(f"Error getting selected nodes: {e}")
                if NUKE_AVAILABLE:
                    nuke.message('Error getting selected nodes from Nuke.')
                return
        else:
            # For testing without Nuke, select first 2 nodes if they exist
            if self.render_table.rowCount() >= 2:
                first_node = self.render_table.item(0, 2)  # Column 2 is Node name
                second_node = self.render_table.item(1, 2)
                if first_node and second_node:
                    selected_node_names = {first_node.text(), second_node.text()}
                    qt_logger.debug(f"Testing mode: selecting first 2 nodes: {list(selected_node_names)}")
        
        # Block signals to prevent multiple updates
        self.render_table.blockSignals(True)
        if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
            self.render_table.frozen_table.blockSignals(True)
        
        try:
            # PERFORMANCE: Batch update all checkboxes without individual sync operations
            for row in range(self.render_table.rowCount()):
                # Get node name for this row
                node_item = self.render_table.item(row, 2)  # Column 2 is Node name
                if not node_item:
                    continue
                    
                node_name = node_item.text()
                is_selected = node_name in selected_node_names
                
                # Set checkbox state based on selection
                self.table_model.set_cell_value(row, 0, is_selected, emit_signal=False)  # Column 0 is Render
                
                # Update the table item
                item = self.render_table.item(row, 0)
                if item:
                    checkbox_state = QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
                    item.setCheckState(checkbox_state)
            
            # PERFORMANCE: Batch sync all frozen checkboxes at once
            self._batch_sync_frozen_checkboxes_from_main()
            
            # Emit single change signal at the end
            self.table_model.dataChanged.emit()
        finally:
            # Re-enable signals
            self.render_table.blockSignals(False)
            if hasattr(self.render_table, 'frozen_table') and self.render_table.frozen_table:
                self.render_table.frozen_table.blockSignals(False)
            
        # PERFORMANCE: Save to storage only once at the end
        if hasattr(self.table_model, '_save_render_selections_to_storage'):
            self.table_model._save_render_selections_to_storage()
            
        qt_logger.debug("🟡 SELECTION BUTTON OPERATION COMPLETED")
    
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
    
    def _apply_configuration(self):
        """Apply panel configuration to table control widgets."""
        # Add debug logging - move outside try block for error handling
        from nk2dl.common.logging import setup_logging
        logger = setup_logging('nk2dl.gui.panel.views.node_settings_view')
        
        try:
            logger.debug("Starting _apply_configuration for NodeSettingsView")
            
            # Set object names for table control widgets - MUST match control names passed to apply_panel_config
            self.update_btn.setObjectName("update")
            self.all_btn.setObjectName("all")
            self.clear_btn.setObjectName("clear")
            self.selection_btn.setObjectName("selection")
            self.inside_groups_check.setObjectName("inside_groups")
            self.column_dropdown.setObjectName("column_dropdown")
            self.filter_edit.setObjectName("filter")
            
            # Apply configuration to table control widgets
            apply_panel_config(self.update_btn, "update")
            apply_panel_config(self.all_btn, "all")
            apply_panel_config(self.clear_btn, "clear")
            apply_panel_config(self.selection_btn, "selection")
            apply_panel_config(self.inside_groups_check, "inside_groups")
            apply_panel_config(self.column_dropdown, "column_dropdown")
            apply_panel_config(self.filter_edit, "filter")
            
        except Exception as e:
            logger.error(f"Error applying configuration to NodeSettingsView: {e}")

    def _set_initial_column_widths(self, headers):
        """Set initial column widths during table creation to prevent UI flashing.
        
        Args:
            headers: List of header names (internal names like 'ChunkSize')
        """
        try:
            from ..constants import TableColumns, Sizes
            from ....common.logging import qt_logger
            
            # Get font metrics for width calculation
            font = self.render_table.font()
            font_metrics = QtGui.QFontMetrics(font)
            
            qt_logger.debug(f"Calculating initial widths for {len(headers)} columns")
            
            # Set default section size to prevent Qt's 100px override
            self.render_table.horizontalHeader().setDefaultSectionSize(Sizes.HEADER_DEFAULT_SECTION_SIZE)
            
            # Ensure header is in Interactive mode for individual column widths
            self.render_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            
            # Calculate and set width for each column
            for col, header_name in enumerate(headers):
                # Calculate optimal width using display name
                optimal_width = TableColumns.calculate_column_width(header_name, font_metrics)
                
                # Set the column width immediately
                self.render_table.setColumnWidth(col, optimal_width)
                
                # Also set in frozen table if this is a frozen column
                if (hasattr(self.render_table, 'frozen_table') and 
                    hasattr(self.render_table, 'frozen_column_count') and 
                    col < self.render_table.frozen_column_count):
                    self.render_table.frozen_table.setColumnWidth(col, optimal_width)
                
                display_name = TableColumns.HEADER_DISPLAY_NAMES.get(header_name, header_name)
                qt_logger.debug(f"Set initial width for column {col} ({header_name} -> '{display_name}'): {optimal_width}px")
                
        except Exception as e:
            qt_logger.error(f"Exception in _set_initial_column_widths: {e}")
            import traceback
            traceback.print_exc()

    def _on_header_clicked(self, logical_index):
        """Handle header clicks for custom multi-level sorting.
        
        Args:
            logical_index (int): Column index that was clicked
        """
        # Determine the new sort order (toggle between ascending/descending)
        current_primary, current_primary_order, _, _ = self.table_model.get_sort_state()
        
        if current_primary == logical_index:
            # Same column clicked - toggle order
            new_order = (QtCore.Qt.DescendingOrder if current_primary_order == QtCore.Qt.AscendingOrder 
                        else QtCore.Qt.AscendingOrder)
        else:
            # Different column clicked - start with ascending
            new_order = QtCore.Qt.AscendingOrder
        
        # Apply the sort through the model
        self.table_model.apply_sort(logical_index, new_order)
        
    def _on_sort_order_changed(self, primary_column, secondary_column):
        """Handle sort order changes to update header indicators.
        
        Args:
            primary_column (int): Primary sort column index (-1 if none)
            secondary_column (int): Secondary sort column index (-1 if none)
        """
        # Get the current sort state
        primary_col, primary_order, secondary_col, secondary_order = self.table_model.get_sort_state()
        
        # Update main table header indicators
        if primary_col is not None:
            self.render_table.horizontalHeader().setSortIndicator(primary_col, primary_order)
            self.render_table.horizontalHeader().setSortIndicatorShown(True)
        else:
            self.render_table.horizontalHeader().setSortIndicatorShown(False)
        
        # Update frozen table header indicators if applicable
        if hasattr(self.render_table, 'frozen_table') and hasattr(self.render_table, 'frozen_column_count'):
            frozen_header = self.render_table.frozen_table.horizontalHeader()
            
            # Show indicator on frozen table only if primary column is frozen
            if primary_col is not None and primary_col < self.render_table.frozen_column_count:
                frozen_header.setSortIndicator(primary_col, primary_order)
                frozen_header.setSortIndicatorShown(True)
                # Hide main table indicator when frozen column is sorted
                self.render_table.horizontalHeader().setSortIndicatorShown(False)
            else:
                frozen_header.setSortIndicatorShown(False)

    def _store_column_widths(self):
        """Store current column widths before data refresh."""
        if not self.render_table:
            return
            
        self._stored_column_widths = {}
        headers = self.table_model.get_headers()
        
        for col, header in enumerate(headers):
            width = self.render_table.columnWidth(col)
            self._stored_column_widths[header] = width
            
        from ....common.logging import qt_logger
        qt_logger.debug(f"Stored column widths: {self._stored_column_widths}")
    
    def _restore_column_widths(self):
        """Restore column widths after data refresh."""
        if not self.render_table or not self._stored_column_widths:
            return
            
        headers = self.table_model.get_headers()
        
        for col, header in enumerate(headers):
            if header in self._stored_column_widths:
                stored_width = self._stored_column_widths[header]
                self.render_table.setColumnWidth(col, stored_width)
                
                # Also set on frozen table if applicable
                if (hasattr(self.render_table, 'frozen_table') and 
                    hasattr(self.render_table, 'frozen_column_count') and
                    col < self.render_table.frozen_column_count):
                    self.render_table.frozen_table.setColumnWidth(col, stored_width)
        
        from ....common.logging import qt_logger
        qt_logger.debug(f"Restored column widths for {len(self._stored_column_widths)} columns")