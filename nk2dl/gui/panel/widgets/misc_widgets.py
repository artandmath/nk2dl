# -*- coding: utf-8 -*-
"""Miscellaneous widget classes for the nk2dl panel.

This module contains utility and miscellaneous widgets used in the nk2dl panel interface.
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

from ..constants import Colors, TableColumns
from ....common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel.widgets.misc_widgets')


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
        self.visible_columns = set(TableColumns.HEADERS)
    
    # Signal for when column visibility changes
    column_visibility_changed = QtCore.Signal() 
    
    def _create_menu(self):
        """Create the dropdown menu with grouped checkboxes."""
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