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

from ..constants import Colors, TableColumns, Sizes
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

class ScrollableTabWidget(QtWidgets.QTabWidget):
    """Tab widget that automatically enables scrolling for tab content when height is limited.
    
    This widget wraps each tab's content in a QScrollArea when the tab widget height
    falls below a configurable threshold. This ensures all content remains accessible
    even in limited vertical space.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_threshold = Sizes.TAB_WIDGET_SCROLL_THRESHOLD
        self._content_min_height = Sizes.TAB_CONTENT_MIN_HEIGHT
        self._original_widgets = {}  # Store original widgets before wrapping
        self._scroll_areas = {}      # Store scroll areas for each tab
        self._scrolling_enabled = False
        
        # Connect resize event to check if scrolling should be enabled
        self.resizeEvent = self._on_resize_event
    
    def addTab(self, widget, label, icon=None):
        """Override addTab to store original widget and potentially wrap in scroll area."""
        # Store the original widget
        tab_index = self.count()
        self._original_widgets[tab_index] = widget
        
        # Check if we need scrolling based on current height
        if self._should_enable_scrolling():
            scroll_widget = self._create_scroll_area(widget)
            self._scroll_areas[tab_index] = scroll_widget
            # Handle different PySide versions for addTab signature
            if PYSIDE_VERSION == "PySide6" and icon is not None:
                super().addTab(scroll_widget, label, icon)
            else:
                super().addTab(scroll_widget, label)
        else:
            # Handle different PySide versions for addTab signature
            if PYSIDE_VERSION == "PySide6" and icon is not None:
                super().addTab(widget, label, icon)
            else:
                super().addTab(widget, label)
        
        return tab_index
    
    def insertTab(self, index, widget, label, icon=None):
        """Override insertTab to handle scroll areas."""
        # Store the original widget
        self._original_widgets[index] = widget
        
        # Check if we need scrolling based on current height
        if self._should_enable_scrolling():
            scroll_widget = self._create_scroll_area(widget)
            self._scroll_areas[index] = scroll_widget
            # Handle different PySide versions for insertTab signature
            if PYSIDE_VERSION == "PySide6" and icon is not None:
                super().insertTab(index, scroll_widget, label, icon)
            else:
                super().insertTab(index, scroll_widget, label)
        else:
            # Handle different PySide versions for insertTab signature
            if PYSIDE_VERSION == "PySide6" and icon is not None:
                super().insertTab(index, widget, label, icon)
            else:
                super().insertTab(index, widget, label)
        
        return index
    
    def removeTab(self, index):
        """Override removeTab to clean up stored widgets."""
        # Remove from our tracking dictionaries
        self._original_widgets.pop(index, None)
        self._scroll_areas.pop(index, None)
        
        # Call parent implementation
        super().removeTab(index)
    
    def widget(self, index):
        """Override widget to return original widget, not scroll area."""
        if index in self._original_widgets:
            return self._original_widgets[index]
        return super().widget(index)
    
    def _should_enable_scrolling(self):
        """Check if scrolling should be enabled based on current height or panel scroll state."""
        # Check if our height is below threshold
        height_check = self.height() < self._scroll_threshold
        
        # Check if we're in a scrollable panel (Nuke's panel system)
        panel_scroll_check = self._is_in_scrollable_panel()
        
        # Enable scrolling if either condition is true
        return height_check or panel_scroll_check
    
    def _is_in_scrollable_panel(self):
        """Check if this widget is inside a scrollable panel (Nuke's panel system)."""
        try:
            # Walk up the parent hierarchy to find if we're in a scroll area
            parent = self.parent()
            while parent:
                # Check if parent is a scroll area
                if isinstance(parent, QtWidgets.QScrollArea):
                    return True
                
                # Check if parent has scroll bars enabled
                if hasattr(parent, 'verticalScrollBarPolicy'):
                    if parent.verticalScrollBarPolicy() != QtCore.Qt.ScrollBarAlwaysOff:
                        # Check if scroll bar is actually visible
                        scroll_bar = parent.verticalScrollBar()
                        if scroll_bar and scroll_bar.isVisible():
                            return True
                
                # Check if parent is a scrollable widget
                if hasattr(parent, 'verticalScrollBar'):
                    scroll_bar = parent.verticalScrollBar()
                    if scroll_bar and scroll_bar.isVisible():
                        return True
                
                parent = parent.parent()
            
            return False
            
        except Exception:
            # If any error occurs during parent traversal, assume not scrollable
            return False
    
    def _create_scroll_area(self, widget):
        """Create a scroll area wrapper for the given widget."""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        # Set minimum height to ensure content is accessible
        scroll_area.setMinimumHeight(self._content_min_height)
        
        # Style the scroll area to match the panel theme
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2a2a2a;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #777777;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        return scroll_area
    
    def _on_resize_event(self, event):
        """Handle resize events to enable/disable scrolling as needed."""
        # Call parent resize event first
        super().resizeEvent(event)
        
        # Check if scrolling state should change
        should_scroll = self._should_enable_scrolling()
        
        if should_scroll != self._scrolling_enabled:
            self._scrolling_enabled = should_scroll
            self._update_scrolling_state()
    
    def _update_scrolling_state(self):
        """Update all tabs to use or remove scroll areas based on current state."""
        # Store current tab index
        current_index = self.currentIndex()
        
        # Remove all tabs temporarily
        tab_data = []
        for i in range(self.count()):
            original_widget = self._original_widgets.get(i, self.widget(i))
            label = self.tabText(i)
            icon = self.tabIcon(i)
            tab_data.append((original_widget, label, icon))
        
        # Clear the tab widget
        self.clear()
        
        # Re-add tabs with appropriate wrapping
        for i, (widget, label, icon) in enumerate(tab_data):
            if self._scrolling_enabled:
                scroll_widget = self._create_scroll_area(widget)
                self._scroll_areas[i] = scroll_widget
                # Handle different PySide versions for addTab signature
                if PYSIDE_VERSION == "PySide6" and icon is not None:
                    super().addTab(scroll_widget, label, icon)
                else:
                    super().addTab(scroll_widget, label)
            else:
                # Remove scroll area if it exists
                self._scroll_areas.pop(i, None)
                # Handle different PySide versions for addTab signature
                if PYSIDE_VERSION == "PySide6" and icon is not None:
                    super().addTab(widget, label, icon)
                else:
                    super().addTab(widget, label)
            
            # Store original widget
            self._original_widgets[i] = widget
        
        # Restore current tab
        if current_index >= 0 and current_index < self.count():
            self.setCurrentIndex(current_index)
    
    def set_scroll_threshold(self, threshold):
        """Set the height threshold for enabling scrolling."""
        self._scroll_threshold = threshold
        self._update_scrolling_state()
    
    def set_content_min_height(self, min_height):
        """Set the minimum height for tab content."""
        self._content_min_height = min_height
        self._update_scrolling_state()
    
    def get_original_widget(self, index):
        """Get the original widget for a tab index (not the scroll area wrapper)."""
        return self._original_widgets.get(index)
    
    def is_scrolling_enabled(self):
        """Check if scrolling is currently enabled."""
        return self._scrolling_enabled
    
    def force_enable_scrolling(self):
        """Force enable scrolling for all tabs (for testing/debugging)."""
        if not self._scrolling_enabled:
            self._scrolling_enabled = True
            self._update_scrolling_state()
    
    def force_disable_scrolling(self):
        """Force disable scrolling for all tabs (for testing/debugging)."""
        if self._scrolling_enabled:
            self._scrolling_enabled = False
            self._update_scrolling_state() 