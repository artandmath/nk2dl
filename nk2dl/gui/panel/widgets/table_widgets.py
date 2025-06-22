# -*- coding: utf-8 -*-
"""Table widget classes for the nk2dl panel.

This module contains specialized table widgets used in the nk2dl panel interface.
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

from ....common.logging import setup_logging
from ..constants import TableColumns, Sizes

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel.widgets.table_widgets')


class StandardTableWidget(QtWidgets.QTableWidget):
    """Standard table widget for node settings without pinned row functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Standard table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setSortingEnabled(True)
        
        logger.info("StandardTableWidget created")
    
    def mousePressEvent(self, event):
        """Override to enable single-click editing for dropdown columns."""
        if event.button() == QtCore.Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                # Check if this is a dropdown column using the correct header list
                headers = TableColumns.HEADERS
                dropdown_columns = ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "ReloadPlugin", "RenderMode"]
                
                if index.column() < len(headers):
                    header = headers[index.column()]
                    
                    if header in dropdown_columns:
                        # Select the row first
                        self.setCurrentIndex(index)
                        
                        # Use a single-shot timer to enter edit mode after selection
                        # This prevents interference between row selection and editor activation
                        QtCore.QTimer.singleShot(0, lambda: self.edit(index))
                        return
        
        # Call parent for normal behavior
        super().mousePressEvent(event)


class FrozenTableWidget(QtWidgets.QTableWidget):
    """Table widget with frozen first 3 columns (Order, Node, Filename).
    
    Based on Qt's frozen column example. The first 3 columns are pinned and don't scroll
    horizontally, while the rest of the columns scroll normally. This is useful for
    keeping node-specific information (Order, Node, Filename) always visible.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Number of columns to freeze (Order, Node, Filename)
        self.frozen_column_count = 3
        
        # Create the frozen table view as an overlay
        self.frozen_table = QtWidgets.QTableWidget(self)
        
        # Initialize the frozen table
        self._init_frozen_table()
        
        # Standard table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setSortingEnabled(True)
        
        # Set selection behavior for frozen table as well
        self.frozen_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        # IMPORTANT: Enable sorting on frozen table for sortByColumn() but disable header clicks
        self.frozen_table.setSortingEnabled(True)
        
        # Connect signals for synchronization
        self._connect_signals()
        
        logger.info("FrozenTableWidget created with 3 frozen columns")
    
    def _init_frozen_table(self):
        """Initialize the frozen table overlay."""
        # Set same model (will be set by parent)
        self.frozen_table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.frozen_table.verticalHeader().hide()
        
        # CRITICAL: Set frozen table header to Interactive mode to allow resizing
        # This is different from Qt's example - we want both tables to be resizable
        self.frozen_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        
        # Enable clickable behavior on frozen table header for sorting frozen columns
        self.frozen_table.horizontalHeader().setSectionsClickable(True)
        
        # Stack the frozen table ON TOP of the main viewport (not under!)
        self.frozen_table.raise_()
        
        # Style the frozen table with darker alternating rows and no custom selection color
        self.frozen_table.setStyleSheet("""
            QTableWidget { 
                border: none;
                background-color: #2a2a2a;
                alternate-background-color: #1a1a1a;
            }
        """)
        
        # Enable alternating row colors for frozen table (darker than main table)
        self.frozen_table.setAlternatingRowColors(True)
        
        # Share selection model
        self.frozen_table.setSelectionModel(self.selectionModel())
        
        # Hide scrollbars on frozen table
        self.frozen_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.frozen_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Set scroll mode for smooth scrolling
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.frozen_table.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        
        # Show the frozen table
        self.frozen_table.show()
    
    def _connect_signals(self):
        """Connect signals for synchronization between main and frozen tables."""
        # BIDIRECTIONAL horizontal header resizing synchronization
        self.horizontalHeader().sectionResized.connect(self._update_frozen_section_width)
        self.frozen_table.horizontalHeader().sectionResized.connect(self._update_main_section_width)
        
        # Synchronize vertical header resizing
        self.verticalHeader().sectionResized.connect(self._update_frozen_section_height)
        
        # Synchronize vertical scrolling
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.verticalScrollBar().setValue
        )
        self.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue
        )
        
        # Synchronize sorting - BIDIRECTIONAL between main and frozen tables
        self.horizontalHeader().sortIndicatorChanged.connect(self._on_main_sort_indicator_changed)
        self.frozen_table.horizontalHeader().sortIndicatorChanged.connect(self._on_frozen_sort_indicator_changed)
        
        # Handle exclusive selection between frozen and main tables
        self.itemSelectionChanged.connect(self._on_main_table_selection_changed)
        self.frozen_table.itemSelectionChanged.connect(self._on_frozen_table_selection_changed)
    
    def _on_main_table_selection_changed(self):
        """Handle selection changes in the main table - clear frozen table selection."""
        if self.selectionModel().hasSelection():
            # Block signals to prevent recursive calls
            self.frozen_table.blockSignals(True)
            try:
                # Clear frozen table selection
                self.frozen_table.clearSelection()
            finally:
                self.frozen_table.blockSignals(False)
    
    def _on_frozen_table_selection_changed(self):
        """Handle selection changes in the frozen table - clear main table selection."""
        if self.frozen_table.selectionModel().hasSelection():
            # Block signals to prevent recursive calls
            self.blockSignals(True)
            try:
                # Clear main table selection
                self.clearSelection()
            finally:
                self.blockSignals(False)
    
    def setColumnCount(self, columns):
        """Set column count for both main and frozen tables."""
        super().setColumnCount(columns)
        self.frozen_table.setColumnCount(columns)
        
        # Hide non-frozen columns in frozen table and show frozen columns
        for col in range(columns):
            if col < self.frozen_column_count:
                # Show frozen columns
                self.frozen_table.setColumnHidden(col, False)
                logger.debug(f"Showing frozen column {col}")
            else:
                # Hide non-frozen columns
                self.frozen_table.setColumnHidden(col, True)
                logger.debug(f"Hiding non-frozen column {col}")
    
    def setRowCount(self, rows):
        """Set row count for both main and frozen tables."""
        super().setRowCount(rows)
        self.frozen_table.setRowCount(rows)
    
    def setHorizontalHeaderLabels(self, labels):
        """Set header labels for both tables."""
        super().setHorizontalHeaderLabels(labels)
        self.frozen_table.setHorizontalHeaderLabels(labels)
    
    def setItem(self, row, column, item):
        """Set item in both tables (frozen table gets copy for frozen columns)."""
        super().setItem(row, column, item)
        
        # If this is a frozen column, also set in frozen table
        if column < self.frozen_column_count:
            # Create a copy of the item for the frozen table
            frozen_item = QtWidgets.QTableWidgetItem(item.text())
            frozen_item.setData(QtCore.Qt.UserRole, item.data(QtCore.Qt.UserRole))
            frozen_item.setFont(item.font())
            frozen_item.setForeground(item.foreground())
            frozen_item.setBackground(item.background())
            
            self.frozen_table.setItem(row, column, frozen_item)
    
    def resizeEvent(self, event):
        """Handle resize events and update frozen table geometry."""
        super().resizeEvent(event)
        self._update_frozen_table_geometry()
    
    def moveCursor(self, cursor_action, modifiers):
        """Handle cursor movement to ensure visibility."""
        current = super().moveCursor(cursor_action, modifiers)
        
        # If moving left and cursor would be hidden behind frozen columns
        if (cursor_action == QtWidgets.QAbstractItemView.MoveLeft and 
            current.column() >= self.frozen_column_count):
            
            # Calculate if the current cell is visible
            visual_rect = self.visualRect(current)
            frozen_width = self._get_frozen_table_width()
            
            if visual_rect.left() < frozen_width:
                # Adjust horizontal scroll to make cell visible
                new_value = (self.horizontalScrollBar().value() + 
                           visual_rect.left() - frozen_width)
                self.horizontalScrollBar().setValue(new_value)
        
        return current
    
    def _update_frozen_section_width(self, logical_index, old_size, new_size):
        """Update frozen table column width when main table column is resized."""
        if logical_index < self.frozen_column_count:
            # Block signals to prevent infinite recursion
            self.frozen_table.horizontalHeader().blockSignals(True)
            try:
                self.frozen_table.setColumnWidth(logical_index, new_size)
                logger.debug(f"Main->Frozen: Updated column {logical_index} width to {new_size}")
            finally:
                self.frozen_table.horizontalHeader().blockSignals(False)
            
            # Update geometry and force repaint to prevent artifacts
            self._update_frozen_table_geometry()
    
    def _update_main_section_width(self, logical_index, old_size, new_size):
        """Update main table column width when frozen table column is resized."""
        if logical_index < self.frozen_column_count:
            # Block signals to prevent infinite recursion
            self.horizontalHeader().blockSignals(True)
            try:
                self.setColumnWidth(logical_index, new_size)
                logger.debug(f"Frozen->Main: Updated column {logical_index} width to {new_size}")
            finally:
                self.horizontalHeader().blockSignals(False)
            
            # Update geometry and force repaint to prevent artifacts
            self._update_frozen_table_geometry()
    
    def _update_frozen_section_height(self, logical_index, old_size, new_size):
        """Update frozen table row height when main table row is resized."""
        self.frozen_table.setRowHeight(logical_index, new_size)
    
    def _on_main_sort_indicator_changed(self, logical_index, sort_order):
        """Handle main table sort indicator changes to synchronize frozen table sorting.
        
        Based on Qt Centre forum solution but adapted for frozen columns.
        """
        try:
            logger.debug(f"Main table sort indicator changed: column {logical_index}, order {sort_order}")
            
            # Block signals to prevent infinite recursion
            self.frozen_table.blockSignals(True)
            
            try:
                # CRITICAL: Manage sort indicators - only one table should show indicator at a time
                if logical_index >= self.frozen_column_count:
                    # Main table is sorting a non-frozen column, hide frozen table sort indicator
                    # and ensure main table indicator is shown
                    self.frozen_table.horizontalHeader().setSortIndicatorShown(False)
                    self.horizontalHeader().setSortIndicatorShown(True)
                    logger.debug("Hidden frozen table sort indicator, shown main table indicator (sorting non-frozen column)")
                else:
                    # Main table is sorting a frozen column, show the indicator on frozen table too
                    # and hide main table indicator
                    self.horizontalHeader().setSortIndicatorShown(False)
                    self.frozen_table.horizontalHeader().setSortIndicatorShown(True)
                    self.frozen_table.horizontalHeader().setSortIndicator(logical_index, sort_order)
                    logger.debug(f"Hidden main table indicator, shown frozen table sort indicator: column {logical_index}, order {sort_order}")
                
                # Get the current row order from the main table after sorting
                row_count = self.rowCount()
                if row_count == 0:
                    return
                
                # Create a list to store the new order of frozen table items
                frozen_rows_data = []
                
                # Collect all frozen column data in the current main table order
                for row in range(row_count):
                    row_data = []
                    for col in range(self.frozen_column_count):
                        # Get item from main table (which is now sorted)
                        main_item = self.item(row, col)
                        if main_item:
                            # Create a copy for frozen table
                            frozen_item = QtWidgets.QTableWidgetItem(main_item.text())
                            frozen_item.setData(QtCore.Qt.UserRole, main_item.data(QtCore.Qt.UserRole))
                            frozen_item.setFont(main_item.font())
                            frozen_item.setForeground(main_item.foreground())
                            frozen_item.setBackground(main_item.background())
                            row_data.append(frozen_item)
                        else:
                            row_data.append(None)
                    frozen_rows_data.append(row_data)
                
                # Update frozen table with the new order
                for row, row_data in enumerate(frozen_rows_data):
                    for col, item in enumerate(row_data):
                        if item:
                            self.frozen_table.setItem(row, col, item)
                        else:
                            # Clear the cell if no item
                            self.frozen_table.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                
                logger.debug(f"Synchronized frozen table row order for {row_count} rows")
                
            finally:
                self.frozen_table.blockSignals(False)
                
        except Exception as e:
            logger.error(f"Error synchronizing frozen table sorting: {e}")
            # Restore signals even if there was an error
            self.frozen_table.blockSignals(False)
    
    def _on_frozen_sort_indicator_changed(self, logical_index, sort_order):
        """Handle frozen table sort indicator changes to synchronize main table sorting.
        
        When user clicks on frozen column headers, sort the main table by that column.
        """
        try:
            # Only handle sorting for frozen columns
            if logical_index >= self.frozen_column_count:
                logger.debug(f"Ignoring sort on non-frozen column {logical_index}")
                return
            
            logger.debug(f"Frozen table sort indicator changed: column {logical_index}, order {sort_order}")
            
            # Block signals to prevent infinite recursion
            self.blockSignals(True)
            
            try:
                # CRITICAL: Hide sort indicator on main table when frozen table is sorted
                # Only one table should show sort indicator at a time
                self.horizontalHeader().setSortIndicatorShown(False)
                logger.debug("Hidden main table sort indicator (frozen table sorting)")
                
                # Sort the main table by the same column and order
                self.sortByColumn(logical_index, sort_order)
                logger.debug(f"Synchronized main table sorting: column {logical_index}, order {sort_order}")
                
                # The main table's sortIndicatorChanged signal will then trigger
                # _on_main_sort_indicator_changed to update the frozen table
                
            finally:
                self.blockSignals(False)
                
        except Exception as e:
            logger.error(f"Error synchronizing main table sorting from frozen table: {e}")
            # Restore signals even if there was an error
            self.blockSignals(False)
    
    def _update_frozen_table_geometry(self):
        """Update the geometry of the frozen table overlay."""
        frozen_width = self._get_frozen_table_width()
        
        # Calculate proper positioning
        x = self.verticalHeader().width() + self.frameWidth()
        y = self.frameWidth()
        width = frozen_width
        height = self.viewport().height() + self.horizontalHeader().height()
        
        logger.debug(f"Updating frozen table geometry: x={x}, y={y}, width={width}, height={height}")
        
        # Get old geometry to determine what area needs repainting
        old_geometry = self.frozen_table.geometry()
        
        # Update frozen table geometry
        self.frozen_table.setGeometry(x, y, width, height)
        
        # Ensure frozen table stays on top after geometry changes
        self.frozen_table.raise_()
        
        # Force a repaint of both the frozen table and the main table viewport
        # This is critical to prevent rendering artifacts when resizing columns
        self.frozen_table.update()
        
        # Calculate the area that needs repainting in the main table
        # This includes both the old and new frozen table areas
        repaint_rect = old_geometry.united(self.frozen_table.geometry())
        
        # Expand the repaint area slightly to ensure complete cleanup
        repaint_rect = repaint_rect.adjusted(-2, -2, 2, 2)
        
        # Force repaint of the main table viewport in the affected area
        self.viewport().update(repaint_rect)
        
        # Also force a full viewport repaint to be absolutely sure
        # This is more expensive but ensures no artifacts remain
        self.viewport().repaint()
    
    def _get_frozen_table_width(self):
        """Calculate the total width of frozen columns."""
        width = 0
        for col in range(min(self.frozen_column_count, self.columnCount())):
            if not self.isColumnHidden(col):
                width += self.columnWidth(col)
        logger.debug(f"Calculated frozen table width: {width} (from {self.frozen_column_count} columns)")
        return width
    
    def mousePressEvent(self, event):
        """Override to enable single-click editing for dropdown columns."""
        if event.button() == QtCore.Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                # Check if this is a dropdown column using the correct header list
                headers = TableColumns.HEADERS
                dropdown_columns = ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "ReloadPlugin", "RenderMode"]
                
                if index.column() < len(headers):
                    header = headers[index.column()]
                    
                    if header in dropdown_columns:
                        # Select the row first
                        self.setCurrentIndex(index)
                        
                        # Use a single-shot timer to enter edit mode after selection
                        # This prevents interference between row selection and editor activation
                        QtCore.QTimer.singleShot(0, lambda: self.edit(index))
                        return
        
        # Call parent for normal behavior
        super().mousePressEvent(event)
    
    def reconnect_frozen_signals(self):
        """Reconnect all frozen table synchronization signals.
        
        This should be called after replacing header views to restore
        synchronization between main and frozen tables.
        """
        logger.debug("Reconnecting frozen table synchronization signals...")
        
        # Disconnect any existing connections to avoid duplicates
        try:
            self.horizontalHeader().sectionResized.disconnect(self._update_frozen_section_width)
            self.frozen_table.horizontalHeader().sectionResized.disconnect(self._update_main_section_width)
            self.verticalHeader().sectionResized.disconnect(self._update_frozen_section_height)
            self.frozen_table.verticalScrollBar().valueChanged.disconnect(self.verticalScrollBar().setValue)
            self.verticalScrollBar().valueChanged.disconnect(self.frozen_table.verticalScrollBar().setValue)
            self.horizontalHeader().sortIndicatorChanged.disconnect(self._on_main_sort_indicator_changed)
            self.frozen_table.horizontalHeader().sortIndicatorChanged.disconnect(self._on_frozen_sort_indicator_changed)
            self.itemSelectionChanged.disconnect(self._on_main_table_selection_changed)
            self.frozen_table.itemSelectionChanged.disconnect(self._on_frozen_table_selection_changed)
            logger.debug("Disconnected existing signals")
        except (TypeError, RuntimeError):
            # Signals may not be connected, which is fine
            logger.debug("No existing signals to disconnect")
        
        # Reconnect all synchronization signals - BIDIRECTIONAL header resize sync
        self.horizontalHeader().sectionResized.connect(self._update_frozen_section_width)
        self.frozen_table.horizontalHeader().sectionResized.connect(self._update_main_section_width)
        self.verticalHeader().sectionResized.connect(self._update_frozen_section_height)
        self.frozen_table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozen_table.verticalScrollBar().setValue)
        self.horizontalHeader().sortIndicatorChanged.connect(self._on_main_sort_indicator_changed)
        self.frozen_table.horizontalHeader().sortIndicatorChanged.connect(self._on_frozen_sort_indicator_changed)
        self.itemSelectionChanged.connect(self._on_main_table_selection_changed)
        self.frozen_table.itemSelectionChanged.connect(self._on_frozen_table_selection_changed)
        
        # Ensure frozen table header is interactive (resizable) and clickable for sorting
        self.frozen_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.frozen_table.horizontalHeader().setSectionsClickable(True)
        self.frozen_table.setSortingEnabled(True)
        
        # Ensure column visibility is correct
        for col in range(self.columnCount()):
            if col < self.frozen_column_count:
                self.frozen_table.setColumnHidden(col, False)
            else:
                self.frozen_table.setColumnHidden(col, True)
        
        # Force geometry update and repaint
        self._update_frozen_table_geometry()
        
        # Synchronize column widths
        for col in range(self.frozen_column_count):
            main_width = self.columnWidth(col)
            self.frozen_table.setColumnWidth(col, main_width)
            logger.debug(f"Synchronized column {col} width to {main_width}")
        
        logger.debug("Frozen table synchronization signals reconnected successfully")
    
    def blockSignals(self, block):
        """Block signals for both main and frozen tables."""
        result = super().blockSignals(block)
        self.frozen_table.blockSignals(block)
        return result

    def calculate_optimal_column_widths(self, sample_data=None):
        """Calculate optimal column widths based on font metrics and content.
        
        Args:
            sample_data: Optional list of sample row data to consider for width calculation
        """
        try:
            # Get Qt logger for debugging
            from ....common.logging import qt_logger
            
            # Enable UI operation mode to reduce logging verbosity during width calculation
            qt_logger.set_ui_operation_mode(True)
            
            qt_logger.debug("Starting optimal column width calculation")
            logger.debug("Starting optimal column width calculation")
            
            # Get font metrics from the table
            font = self.font()
            font_metrics = QtGui.QFontMetrics(font)
            qt_logger.debug(f"Using font: {font.family()}, {font.pointSize()}pt")
            
            # Check default section size
            default_size = self.horizontalHeader().defaultSectionSize()
            qt_logger.debug(f"Header default section size: {default_size}px")
            
            # Set default section size to a reasonable minimum to prevent 100px override
            self.horizontalHeader().setDefaultSectionSize(Sizes.HEADER_DEFAULT_SECTION_SIZE)
            qt_logger.debug(f"Set header default section size to {Sizes.HEADER_DEFAULT_SECTION_SIZE}px")
            
            # Check and fix header resize mode that might be forcing uniform widths
            resize_mode = self.horizontalHeader().sectionResizeMode(0)  # Check first column's resize mode
            qt_logger.debug(f"Current header resize mode: {resize_mode}")
            
            # Ensure header is in Interactive mode (allows individual column widths)
            self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            qt_logger.debug("Set header resize mode to Interactive")
            
            logger.debug(f"Using font: {font.family()}, {font.pointSize()}pt")
            
            # Get headers directly from TableColumns.HEADERS to avoid display name confusion
            # This ensures we use the correct header names for width calculation
            headers = TableColumns.HEADERS[:self.columnCount()]
            
            qt_logger.debug(f"Processing {len(headers)} columns: {headers}")
            qt_logger.debug(f"Table has {self.columnCount()} columns, {self.rowCount()} rows")
            logger.debug(f"Processing {len(headers)} columns: {headers}")
            
            # PHASE 1: Calculate all optimal widths without setting them (prevents UI flashing)
            calculated_widths = {}
            qt_logger.debug("=== PHASE 1: Calculating all column widths ===")
            
            for col, header_name in enumerate(headers):
                qt_logger.debug(f"Processing column {col}: {header_name}")
                
                # Collect sample values for this column
                sample_values = []
                
                # Add sample values from actual table data
                for row in range(min(10, self.rowCount())):  # Sample first 10 rows
                    item = self.item(row, col)
                    if item and item.text():
                        sample_values.append(item.text())
                
                # Add sample values from provided data
                if sample_data:
                    for row_data in sample_data[:10]:  # Sample first 10 rows
                        if isinstance(row_data, dict) and header_name in row_data:
                            value = row_data[header_name]
                            if value is not None:
                                sample_values.append(str(value))
                        elif isinstance(row_data, list) and col < len(row_data):
                            value = row_data[col]
                            if value is not None:
                                sample_values.append(str(value))
                
                # Add some typical values for this column type
                if header_name == "Order":
                    sample_values.extend(["1", "1000", "2000"])
                elif header_name == "Node":
                    sample_values.extend(["Write1", "Write123", "WriteNode_v001"])
                elif header_name == "Filename":
                    sample_values.extend(["output.%04d.exr", "/long/path/to/output_file.%04d.exr"])
                elif header_name == "Priority":
                    sample_values.extend(["50", "100"])
                elif header_name in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "ReloadPlugin", "UseGPU", "WorkerTaskLimit"]:
                    sample_values.extend(["Yes", "No"])
                elif header_name == "RenderMode":
                    sample_values.extend(["Full", "Proxy", "Both", "Script"])
                elif header_name in ["Pool", "SecondaryPool"]:
                    sample_values.extend(["comp", "lighting", "render"])
                elif header_name == "Group":
                    sample_values.extend(["none", "high_priority", "overnight"])
                
                qt_logger.debug(f"Column {col} sample values: {sample_values[:5]}")
                
                # Calculate optimal width using the internal header name (which will be converted to display name inside the method)
                optimal_width = TableColumns.calculate_column_width(header_name, font_metrics, sample_values)
                display_name = TableColumns.HEADER_DISPLAY_NAMES.get(header_name, header_name)
                qt_logger.debug(f"Column {col} ({header_name} -> '{display_name}'): calculated width = {optimal_width}px")
                qt_logger.debug(f"Width calculation used display name: '{display_name}' (length: {len(display_name)} chars)")
                logger.debug(f"Column {col} ({header_name}): calculated width = {optimal_width}px, samples = {sample_values[:3]}")
                
                # Store the calculated width for batch application
                calculated_widths[col] = optimal_width
            
            # PHASE 2: Apply all widths in a single batch operation (prevents UI flashing)
            qt_logger.debug("=== PHASE 2: Applying all column widths in batch ===")
            
            # Block signals to prevent multiple repaints and signal emissions during width setting
            qt_logger.debug("Blocking signals for batch width update")
            self.blockSignals(True)
            if hasattr(self, 'frozen_table'):
                self.frozen_table.blockSignals(True)
            
            # Temporarily disconnect resize signals to prevent cascade updates
            try:
                self.horizontalHeader().sectionResized.disconnect()
                if hasattr(self, 'frozen_table'):
                    self.frozen_table.horizontalHeader().sectionResized.disconnect()
                qt_logger.debug("Disconnected resize signals for batch update")
            except (TypeError, RuntimeError):
                qt_logger.debug("No resize signals to disconnect")
            
            try:
                # Apply all calculated widths at once
                for col, optimal_width in calculated_widths.items():
                    header_name = headers[col]
                    
                    # Set main table column width
                    qt_logger.debug(f"Setting column {col} ({header_name}) width to {optimal_width}px")
                    self.setColumnWidth(col, optimal_width)
                    
                    # Set frozen table column width if applicable
                    if (hasattr(self, 'frozen_table') and 
                        hasattr(self, 'frozen_column_count') and 
                        col < self.frozen_column_count):
                        self.frozen_table.setColumnWidth(col, optimal_width)
                        qt_logger.debug(f"Set frozen table column {col} ({header_name}) width to {optimal_width}px")
                
                qt_logger.debug(f"Applied {len(calculated_widths)} column widths in batch")
                
            finally:
                # Re-enable signals and reconnect resize signals
                qt_logger.debug("Re-enabling signals after batch update")
                self.blockSignals(False)
                if hasattr(self, 'frozen_table'):
                    self.frozen_table.blockSignals(False)
                
                # Reconnect resize signals
                try:
                    self.horizontalHeader().sectionResized.connect(self._update_frozen_section_width)
                    if hasattr(self, 'frozen_table'):
                        self.frozen_table.horizontalHeader().sectionResized.connect(self._update_main_section_width)
                    qt_logger.debug("Reconnected resize signals after batch update")
                except (TypeError, RuntimeError):
                    qt_logger.debug("Could not reconnect some resize signals")
            
            # PHASE 3: Single UI update and verification
            qt_logger.debug("=== PHASE 3: Final verification and single UI update ===")
            
            # Force a single geometry update for both tables
            self.updateGeometry()
            if hasattr(self, 'frozen_table'):
                self.frozen_table.updateGeometry()
                self._update_frozen_table_geometry()
            
            # Single repaint to show all changes at once
            self.update()
            if hasattr(self, 'frozen_table'):
                self.frozen_table.update()
            
            qt_logger.debug(f"Completed optimal column width calculation for {len(headers)} columns")
            logger.debug(f"Completed optimal column width calculation for {len(headers)} columns")
            
            # Final verification - show current state of all column widths
            qt_logger.debug("Final column width verification:")
            for col in range(min(10, len(headers))):  # Show first 10 columns to see more variety
                main_width = self.columnWidth(col)
                frozen_width = self.frozen_table.columnWidth(col) if col < self.frozen_column_count else "N/A"
                qt_logger.debug(f"  Column {col} ({headers[col]}): main={main_width}px, frozen={frozen_width}px")
            
            # Also check if all columns are actually the same width
            all_widths = [self.columnWidth(col) for col in range(len(headers))]
            unique_widths = set(all_widths)
            if len(unique_widths) == 1:
                qt_logger.error(f"All {len(headers)} columns have the same width: {list(unique_widths)[0]}px - this suggests a resize mode issue!")
            else:
                qt_logger.debug(f"Found {len(unique_widths)} different column widths: {sorted(unique_widths)}")
            
        except Exception as e:
            qt_logger.error(f"Exception in calculate_optimal_column_widths: {str(e)}")
            qt_logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            qt_logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Exception in calculate_optimal_column_widths: {str(e)}", exc_info=True)
            
            # Ensure signals are re-enabled even if an exception occurs
            try:
                self.blockSignals(False)
                if hasattr(self, 'frozen_table'):
                    self.frozen_table.blockSignals(False)
            except:
                pass
        
        finally:
            # Disable UI operation mode to restore full logging
            try:
                qt_logger.set_ui_operation_mode(False)
            except:
                pass 