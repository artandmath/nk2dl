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
                # Check if this is a dropdown column
                headers = ["Order", "Node", "Filename", "Priority", "ChunkSize", "Frames", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "ReloadPlugin"]
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
        
        # Connect signals for synchronization
        self._connect_signals()
        
        logger.info("FrozenTableWidget created with 3 frozen columns")
    
    def _init_frozen_table(self):
        """Initialize the frozen table overlay."""
        # Set same model (will be set by parent)
        self.frozen_table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.frozen_table.verticalHeader().hide()
        self.frozen_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        
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
        # Synchronize horizontal header resizing
        self.horizontalHeader().sectionResized.connect(self._update_frozen_section_width)
        
        # Synchronize vertical header resizing
        self.verticalHeader().sectionResized.connect(self._update_frozen_section_height)
        
        # Synchronize vertical scrolling
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.verticalScrollBar().setValue
        )
        self.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue
        )
        
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
        
        # Hide non-frozen columns in frozen table
        for col in range(self.frozen_column_count, columns):
            self.frozen_table.setColumnHidden(col, True)
    
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
            self.frozen_table.setColumnWidth(logical_index, new_size)
            self._update_frozen_table_geometry()
    
    def _update_frozen_section_height(self, logical_index, old_size, new_size):
        """Update frozen table row height when main table row is resized."""
        self.frozen_table.setRowHeight(logical_index, new_size)
    
    def _update_frozen_table_geometry(self):
        """Update the geometry of the frozen table overlay."""
        frozen_width = self._get_frozen_table_width()
        
        self.frozen_table.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            frozen_width,
            self.viewport().height() + self.horizontalHeader().height()
        )
        
        # Ensure frozen table stays on top after geometry changes
        self.frozen_table.raise_()
    
    def _get_frozen_table_width(self):
        """Calculate the total width of frozen columns."""
        width = 0
        for col in range(self.frozen_column_count):
            width += self.columnWidth(col)
        return width
    
    def mousePressEvent(self, event):
        """Override to enable single-click editing for dropdown columns."""
        if event.button() == QtCore.Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                # Check if this is a dropdown column
                headers = ["Order", "Node", "Filename", "Priority", "ChunkSize", "Frames", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "ReloadPlugin"]
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
    
    def blockSignals(self, block):
        """Block signals for both main and frozen tables."""
        result = super().blockSignals(block)
        self.frozen_table.blockSignals(block)
        return result 