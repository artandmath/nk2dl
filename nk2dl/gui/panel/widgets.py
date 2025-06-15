# -*- coding: utf-8 -*-
"""Custom Qt widgets for the nk2dl panel.

This module contains all custom widget classes used in the nk2dl panel interface.
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

from .constants import Colors, TableColumns, HeaderSettingsMapping
from ...common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel.widgets')

class ColoredGroupBox(QtWidgets.QGroupBox):
    """Custom QGroupBox that draws colored borders and full-width dark title backgrounds without affecting layout."""
    
    def __init__(self, title, border_color, parent=None):
        super().__init__(title, parent)
        self.border_color = QtGui.QColor(border_color)
        self.border_width = 2
        
        # Use background color constants for consistency with pinned rows
        if border_color == Colors.JOB_SETTINGS_COLOR:  # Blue border
            self.title_bg_color = QtGui.QColor(Colors.JOB_SETTINGS_BACKGROUND)
        elif border_color == Colors.MACHINE_SETTINGS_COLOR:  # Purple border
            self.title_bg_color = QtGui.QColor(Colors.MACHINE_SETTINGS_BACKGROUND)
        else:
            self.title_bg_color = QtGui.QColor("#262626")  # Default very dark grey
    
    def paintEvent(self, event):
        """Custom paint event to draw colored border and full-width dark title background."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Calculate title dimensions with extra padding below
        font_metrics = QtGui.QFontMetrics(self.font())
        title_text = self.title()
        title_height = font_metrics.height() + 12  # Increased padding (was 8, now 12)
        
        # Draw full-width title background bar (like user's yellow highlighting)
        title_bar_rect = QtCore.QRect(
            self.border_width,  # Start after left border
            self.border_width,  # Start after top border  
            self.width() - (self.border_width * 2),  # Full width minus borders
            title_height
        )
        painter.fillRect(title_bar_rect, self.title_bg_color)
        
        # Draw title text in white for contrast (not bold)
        if title_text:
            painter.setPen(QtGui.QColor("white"))
            font = painter.font()
            # Removed setBold(True) - using normal weight
            painter.setFont(font)
            
            text_rect = QtCore.QRect(
                10 + self.border_width,  # Left margin plus border
                self.border_width + 2,   # Top margin plus border
                self.width() - 20 - (self.border_width * 2),  # Width minus margins and borders
                title_height - 4
            )
            painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, title_text)
        
        # Draw the main group box frame (without the title - Qt will handle content area)
        frame_rect = QtCore.QRect(
            self.border_width,
            title_height + self.border_width,  # Start below title bar
            self.width() - (self.border_width * 2),
            self.height() - title_height - (self.border_width * 2)
        )
        
        # Draw background for content area
        painter.fillRect(frame_rect, self.palette().color(QtGui.QPalette.Base))
        
        # Draw the colored border around everything
        pen = QtGui.QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        
        border_rect = self.rect().adjusted(
            self.border_width // 2, 
            self.border_width // 2, 
            -self.border_width // 2, 
            -self.border_width // 2
        )
        painter.drawRect(border_rect)


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


class GroupedHeaderView(QtWidgets.QHeaderView):
    """Custom header view that displays grouped headers with categories spanning multiple columns."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.groups = []  # List of (group_name, start_col, end_col)
        self.group_height = 25  # Height for group headers
        
    def setGroups(self, groups):
        """Set the group definitions.
        
        Args:
            groups (list): List of tuples (group_name, start_column, end_column)
        """
        self.groups = groups
        self.updateGeometry()
        
    def sizeHint(self):
        """Return size hint with extra height for grouped headers."""
        base_hint = super().sizeHint()
        if self.groups:
            # Add extra height for group row
            return QtCore.QSize(base_hint.width(), base_hint.height() + self.group_height)
        return base_hint
    
    def resizeEvent(self, event):
        """Override resize event to prevent automatic column resizing."""
        # Call parent but don't let it auto-resize columns
        super().resizeEvent(event)
        # Note: logger is not available in this module, so we skip logging
        
    def sectionResized(self, logicalIndex, oldSize, newSize):
        """Override to log when sections are resized."""
        super().sectionResized(logicalIndex, oldSize, newSize)
        # Note: logger is not available in this module, so we skip logging
        
    def paintSection(self, painter, rect, logicalIndex):
        """Paint section with grouped headers."""
        painter.save()
        
        # Fill background
        header_color = self.palette().color(QtGui.QPalette.Base)
        painter.fillRect(rect, header_color)
        
        # Only draw borders for individual sections if we don't have groups
        # (groups will handle all border drawing)
        if not self.groups:
            painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Mid), 1))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
        
        # Get the section text
        text = self.model().headerData(logicalIndex, self.orientation(), QtCore.Qt.DisplayRole)
        if not text:
            painter.restore()
            return
        
        # Set up font and colors
        font = painter.font()
        painter.setFont(font)
        text_color = self.palette().color(QtGui.QPalette.Text)
        painter.setPen(text_color)
        
        # Calculate text area (leave space for group header at top)
        text_rect = rect
        if self.groups:
            text_rect = rect.adjusted(0, self.group_height, 0, 0)
        
        # Add horizontal padding for secondary columns (skip primary column 0)
        if logicalIndex > 0:
            text_rect = text_rect.adjusted(4, 0, -4, 0)  # 4px left and right padding for secondary GSV headers
        
        # Draw the column text
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, str(text))
        
        painter.restore()
        
    def paintEvent(self, event):
        """Paint the entire header including groups and consistent borders."""
        # Paint normal sections first
        super().paintEvent(event)
        
        if not self.groups:
            return
            
        painter = QtGui.QPainter(self.viewport())
        painter.save()
        
        # Set up consistent border style
        border_pen = QtGui.QPen(self.palette().color(QtGui.QPalette.Mid), 1)
        painter.setPen(border_pen)
        
        # Draw vertical lines between all columns
        for i in range(self.count()):
            if i > 0:  # Don't draw line before first column
                x = self.sectionPosition(i)
                painter.drawLine(x, 0, x, self.height())
        
        # Draw horizontal line separating groups from individual columns
        painter.drawLine(0, self.group_height, self.width(), self.group_height)
        
        # Draw outer border
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Set up font for group headers
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # Use darker text for group headers
        text_color = self.palette().color(QtGui.QPalette.Text)
        painter.setPen(text_color)
        
        # Draw group headers with backgrounds
        for group_name, start_col, end_col in self.groups:
            # Calculate the span rectangle
            start_x = self.sectionPosition(start_col)
            end_x = self.sectionPosition(end_col) + self.sectionSize(end_col)
            
            group_rect = QtCore.QRect(start_x, 0, end_x - start_x, self.group_height)
            
            # Fill group header background with slightly different color
            group_color = self.palette().color(QtGui.QPalette.Button)
            painter.fillRect(group_rect, group_color)
            
            # Draw group text with horizontal padding
            text_rect = group_rect.adjusted(3, 0, -3, 0)
            painter.drawText(text_rect, QtCore.Qt.AlignCenter, group_name)
        
        # Re-draw group borders to ensure they're on top
        painter.setPen(border_pen)
        for group_name, start_col, end_col in self.groups:
            start_x = self.sectionPosition(start_col)
            end_x = self.sectionPosition(end_col) + self.sectionSize(end_col)
            
            # Draw vertical borders around groups
            if start_col > 1:  # Don't draw line after primary column
                painter.drawLine(start_x, 0, start_x, self.group_height)
            painter.drawLine(end_x, 0, end_x, self.group_height)
        
        # Draw bottom border of group headers (divider line below Resolution/Format)
        painter.drawLine(0, self.group_height, self.width(), self.group_height)
        
        painter.restore() 


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

class ColumnVisibilityDropdown(QtWidgets.QPushButton):
    """Dropdown button with column visibility checkboxes grouped by categories."""
    
    def __init__(self, parent=None):
        super().__init__("Columns ▼", parent)
        self.setToolTip("Show/hide table columns")
        self.setMaximumWidth(80)
        
        self.column_checkboxes = {}  # header -> checkbox mapping
        self.group_checkboxes = {}   # group_name -> checkbox mapping
        self.visible_columns = set()  # Track visible columns
        
        # Create the dropdown menu
        self._create_menu()
        
        # Connect button click to show menu
        self.clicked.connect(self._show_menu)
        
        # Initialize all columns as visible by default (including fixed columns)
        from .constants import TableColumns
        self.visible_columns = set(TableColumns.HEADERS)
    
    def _create_menu(self):
        """Create the dropdown menu with grouped checkboxes."""
        from .constants import TableColumns
        
        self.menu = QtWidgets.QMenu(self)
        
        # Add "All Columns" checkbox at the top
        all_action = QtWidgets.QWidgetAction(self.menu)
        all_checkbox = QtWidgets.QCheckBox("All Columns")
        all_checkbox.setChecked(True)
        all_checkbox.stateChanged.connect(self._on_all_changed)
        all_action.setDefaultWidget(all_checkbox)
        self.menu.addAction(all_action)
        self.group_checkboxes["All"] = all_checkbox
        
        self.menu.addSeparator()
        
        # Add groups (skip "Fixed" group)
        for group_name, headers in TableColumns.COLUMN_GROUPS.items():
            if group_name == "Fixed":
                continue  # Skip the Fixed group entirely
                
            # Add group header with "All" checkbox
            group_action = QtWidgets.QWidgetAction(self.menu)
            group_widget = QtWidgets.QWidget()
            group_layout = QtWidgets.QHBoxLayout(group_widget)
            group_layout.setContentsMargins(5, 2, 5, 2)
            
            # Group label
            group_label = QtWidgets.QLabel(f"<b>{group_name}</b>")
            group_layout.addWidget(group_label)
            
            # Group "All" checkbox
            group_layout.addStretch()
            group_all_checkbox = QtWidgets.QCheckBox("All")
            group_all_checkbox.setChecked(True)
            group_all_checkbox.stateChanged.connect(
                lambda state, group=group_name: self._on_group_all_changed(group, state)
            )
            group_layout.addWidget(group_all_checkbox)
            self.group_checkboxes[group_name] = group_all_checkbox
            
            group_action.setDefaultWidget(group_widget)
            self.menu.addAction(group_action)
            
            # Add individual column checkboxes for this group
            for header in headers:
                column_action = QtWidgets.QWidgetAction(self.menu)
                column_widget = QtWidgets.QWidget()
                column_layout = QtWidgets.QHBoxLayout(column_widget)
                column_layout.setContentsMargins(20, 2, 5, 2)  # Indent for grouping
                
                checkbox = QtWidgets.QCheckBox(TableColumns.HEADER_DISPLAY_NAMES.get(header, header))
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(
                    lambda state, h=header: self._on_column_changed(h, state)
                )
                
                column_layout.addWidget(checkbox)
                column_action.setDefaultWidget(column_widget)
                self.menu.addAction(column_action)
                
                self.column_checkboxes[header] = checkbox
            
            # Add separator after each group except the last
            remaining_groups = [g for g in TableColumns.COLUMN_GROUPS.keys() if g != "Fixed"]
            if group_name != remaining_groups[-1]:
                self.menu.addSeparator()
    
    def _show_menu(self):
        """Show the dropdown menu."""
        # Position the menu below the button
        pos = self.mapToGlobal(QtCore.QPoint(0, self.height()))
        self.menu.exec_(pos)
    
    def _on_all_changed(self, state):
        """Handle "All Columns" checkbox change."""
        checked = state == QtCore.Qt.Checked
        
        # Block signals to prevent recursion
        for header, checkbox in self.column_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        
        for group_name, checkbox in self.group_checkboxes.items():
            if group_name != "All":
                checkbox.blockSignals(True)
                checkbox.setChecked(checked)
                checkbox.blockSignals(False)
        
        # Update visible columns (always keep fixed columns visible)
        from .constants import TableColumns
        fixed_columns = set(TableColumns.COLUMN_GROUPS["Fixed"])
        
        if checked:
            self.visible_columns = set(TableColumns.HEADERS)
        else:
            # Keep only fixed columns visible when unchecked
            self.visible_columns = fixed_columns.copy()
        
        self.column_visibility_changed.emit()
    
    def _on_group_all_changed(self, group_name, state):
        """Handle group "All" checkbox change."""
        checked = state == QtCore.Qt.Checked
        
        from .constants import TableColumns
        group_headers = TableColumns.COLUMN_GROUPS.get(group_name, [])
        
        # Update individual column checkboxes in this group
        for header in group_headers:
            if header in self.column_checkboxes:
                checkbox = self.column_checkboxes[header]
                checkbox.blockSignals(True)
                checkbox.setChecked(checked)
                checkbox.blockSignals(False)
                
                # Update visible columns
                if checked:
                    self.visible_columns.add(header)
                else:
                    self.visible_columns.discard(header)
        
        self._update_all_checkbox()
        self.column_visibility_changed.emit()
    
    def _on_column_changed(self, header, state):
        """Handle individual column checkbox change."""
        checked = state == QtCore.Qt.Checked
        
        if checked:
            self.visible_columns.add(header)
        else:
            self.visible_columns.discard(header)
        
        self._update_group_checkboxes()
        self._update_all_checkbox()
        self.column_visibility_changed.emit()
    
    def _update_group_checkboxes(self):
        """Update group "All" checkboxes based on individual column states."""
        from .constants import TableColumns
        
        for group_name, headers in TableColumns.COLUMN_GROUPS.items():
            if group_name == "Fixed" or group_name not in self.group_checkboxes:
                continue
            
            # Check if all columns in this group are visible
            all_visible = all(header in self.visible_columns for header in headers)
            any_visible = any(header in self.visible_columns for header in headers)
            
            group_checkbox = self.group_checkboxes[group_name]
            group_checkbox.blockSignals(True)
            
            if all_visible:
                group_checkbox.setCheckState(QtCore.Qt.Checked)
            elif any_visible:
                group_checkbox.setCheckState(QtCore.Qt.PartiallyChecked)
            else:
                group_checkbox.setCheckState(QtCore.Qt.Unchecked)
            
            group_checkbox.blockSignals(False)
    
    def _update_all_checkbox(self):
        """Update the main "All Columns" checkbox based on individual column states."""
        from .constants import TableColumns
        
        # Count non-fixed columns that are shown in the dropdown
        dropdown_headers = []
        for group_name, headers in TableColumns.COLUMN_GROUPS.items():
            if group_name != "Fixed":
                dropdown_headers.extend(headers)
        
        all_visible = all(header in self.visible_columns for header in dropdown_headers)
        any_visible = any(header in self.visible_columns for header in dropdown_headers)
        
        all_checkbox = self.group_checkboxes["All"]
        all_checkbox.blockSignals(True)
        
        if all_visible:
            all_checkbox.setCheckState(QtCore.Qt.Checked)
        elif any_visible:
            all_checkbox.setCheckState(QtCore.Qt.PartiallyChecked)
        else:
            all_checkbox.setCheckState(QtCore.Qt.Unchecked)
        
        all_checkbox.blockSignals(False)
    
    def get_visible_columns(self):
        """Get the set of visible column headers.
        
        Returns:
            set: Set of visible column header names
        """
        return self.visible_columns.copy()
    
    def set_visible_columns(self, visible_columns):
        """Set the visible columns.
        
        Args:
            visible_columns (set): Set of column header names to make visible
        """
        from .constants import TableColumns
        
        # Always ensure fixed columns are included
        fixed_columns = set(TableColumns.COLUMN_GROUPS["Fixed"])
        self.visible_columns = set(visible_columns) | fixed_columns
        
        # Update all checkboxes
        for header, checkbox in self.column_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(header in self.visible_columns)
            checkbox.blockSignals(False)
        
        self._update_group_checkboxes()
        self._update_all_checkbox()
        self.column_visibility_changed.emit()
    
    # Signal for when column visibility changes
    column_visibility_changed = QtCore.Signal() 

class CustomHeaderView(QtWidgets.QHeaderView):
    """Custom header view that styles columns based on job/machine settings classification.
    
    This header view applies different color schemes to columns based on whether they
    belong to job settings (blue) or machine settings (purple), using colors from
    the constants module. It maintains full compatibility with FrozenTableWidget
    synchronization.
    """
    
    def __init__(self, orientation, parent=None):
        """Initialize the custom header view.
        
        Args:
            orientation: Qt.Horizontal or Qt.Vertical
            parent: Parent widget
        """
        super().__init__(orientation, parent)
        
        # Set default header properties to match standard behavior
        self.setSectionsClickable(True)
        self.setSectionsMovable(False)
        self.setStretchLastSection(False)
        
        # Enable section resize mode to maintain standard behavior
        self.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        
        # Cache colors for performance
        self._job_background = QtGui.QColor(Colors.JOB_SETTINGS_BACKGROUND)
        self._job_border = QtGui.QColor(Colors.JOB_SETTINGS_COLOR)
        self._machine_background = QtGui.QColor(Colors.MACHINE_SETTINGS_BACKGROUND)
        self._machine_border = QtGui.QColor(Colors.MACHINE_SETTINGS_COLOR)
        self._default_background = QtGui.QColor("#2a2a2a")  # Dark gray for fixed columns
        self._default_border = QtGui.QColor("#555555")      # Medium gray border
        
        logger.info("CustomHeaderView created with job/machine color schemes")
    
    def resizeEvent(self, event):
        """Override resize event to maintain proper header behavior."""
        super().resizeEvent(event)
        # Ensure the header repaints after resize
        self.update()
    
    def mousePressEvent(self, event):
        """Override to maintain standard header interaction behavior."""
        # Call parent to handle standard header interactions (sorting, resizing, etc.)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Override to maintain standard header resize cursor behavior."""
        # Call parent to handle resize cursors and interactions
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Override to maintain standard header interaction behavior."""
        # Call parent to handle standard header interactions
        super().mouseReleaseEvent(event)
    
    def paintSection(self, painter, rect, logicalIndex):
        """Paint header section with custom styling based on column type.
        
        Args:
            painter: QPainter instance
            rect: Rectangle to paint in
            logicalIndex: Logical index of the column
        """
        if not self.model():
            super().paintSection(painter, rect, logicalIndex)
            return
            
        painter.save()
        
        # Get column header name to determine styling
        header_name = self._get_header_name(logicalIndex)
        if not header_name:
            super().paintSection(painter, rect, logicalIndex)
            painter.restore()
            return
        
        # Determine column type and colors
        setting_type, _ = HeaderSettingsMapping.get_setting_type_and_key(header_name)
        
        if setting_type == "job":
            bg_color = self._job_background
            border_color = self._job_border
        elif setting_type == "machine":
            bg_color = self._machine_background
            border_color = self._machine_border
        else:
            # Fixed columns (Order, Node, Filename) or unmapped columns
            bg_color = self._default_background
            border_color = self._default_border
        
        # Fill background with dark color
        painter.fillRect(rect, bg_color)
        
        # Draw the column text
        display_name = self._get_display_name(header_name)
        self._draw_header_text(painter, rect, display_name)
        
        # Draw borders (sides and top with subtle border, bottom with bright color)
        self._draw_header_borders(painter, rect, border_color)
        
        painter.restore()
    
    def _get_header_name(self, logical_index):
        """Get the header name for a logical index.
        
        Args:
            logical_index: Logical column index
            
        Returns:
            str: Header name or None if not found
        """
        header_data = self.model().headerData(logical_index, self.orientation(), QtCore.Qt.DisplayRole)
        if not header_data:
            return None
            
        # Convert display name back to header name using reverse lookup
        display_to_header = {v: k for k, v in TableColumns.HEADER_DISPLAY_NAMES.items()}
        return display_to_header.get(str(header_data), str(header_data))
    
    def _get_display_name(self, header_name):
        """Get the display name for a header.
        
        Args:
            header_name: Internal header name
            
        Returns:
            str: Display name for the header
        """
        return TableColumns.HEADER_DISPLAY_NAMES.get(header_name, header_name)
    
    def _draw_header_text(self, painter, rect, text):
        """Draw the header text centered in the rectangle.
        
        Args:
            painter: QPainter instance
            rect: Rectangle to draw text in
            text: Text to draw
        """
        # Set text color to white for good contrast on dark backgrounds
        painter.setPen(QtGui.QColor(255, 255, 255))
        
        # Set font (slightly bold for headers)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # Draw text centered
        painter.drawText(rect, QtCore.Qt.AlignCenter, str(text))
    
    def _draw_header_borders(self, painter, rect, border_color):
        """Draw header borders with bright bottom edge only.
        
        Args:
            painter: QPainter instance
            rect: Rectangle to draw borders around
            border_color: Color for the bright bottom border only
        """
        # Use system default header border color for sides and top
        default_border_color = self.palette().color(QtGui.QPalette.Mid)
        painter.setPen(QtGui.QPen(default_border_color, 1))
        
        # Left border (system default)
        painter.drawLine(rect.topLeft(), rect.bottomLeft())
        
        # Right border (system default)
        painter.drawLine(rect.topRight(), rect.bottomRight())
        
        # Top border (system default)
        painter.drawLine(rect.topLeft(), rect.topRight())
        
        # Bright bottom border ONLY (full opacity, slightly thicker)
        painter.setPen(QtGui.QPen(border_color, 2))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight()) 