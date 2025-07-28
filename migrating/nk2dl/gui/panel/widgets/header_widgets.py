# -*- coding: utf-8 -*-
"""Header widget classes for the nk2dl panel.

This module contains specialized header view widgets used in the nk2dl panel interface.
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

from ..constants import Colors, TableColumns, HeaderSettingsMapping, Sizes
from ....common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel.widgets.header_widgets')


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
            text_rect = text_rect.adjusted(Sizes.HEADER_TEXT_PADDING, 0, -Sizes.HEADER_TEXT_PADDING, 0)  # Consistent padding for secondary GSV headers
        
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
            text_rect = group_rect.adjusted(Sizes.HEADER_TEXT_PADDING, 0, -Sizes.HEADER_TEXT_PADDING, 0)
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
        
        # CRITICAL: Enable sort indicators - this was missing!
        self.setSortIndicatorShown(True)
        
        # Enable section resize mode to maintain standard behavior
        self.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        
        # Cache colors for performance
        self._job_background = QtGui.QColor(Colors.JOB_SETTINGS_BACKGROUND)
        self._job_border = QtGui.QColor(Colors.JOB_SETTINGS_COLOR)
        self._machine_background = QtGui.QColor(Colors.MACHINE_SETTINGS_BACKGROUND)
        self._machine_border = QtGui.QColor(Colors.MACHINE_SETTINGS_COLOR)
        self._default_background = QtGui.QColor("#2a2a2a")  # Dark gray for fixed columns
        self._default_border = QtGui.QColor("#555555")      # Medium gray border
        
        logger.info("CustomHeaderView created with job/machine color schemes and sort indicators enabled")
    
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
        
        # Draw custom sort indicator if column is sorted
        self._draw_sort_indicator(painter, rect, logicalIndex)

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
        """Draw the header text centered in the rectangle with padding.
        
        Args:
            painter: QPainter instance
            rect: Rectangle to draw text in
            text: Text to draw
        """
        # Set text color to white for good contrast on dark backgrounds
        painter.setPen(QtGui.QColor(255, 255, 255))
        
        # Use normal font (not bold) for consistent width calculations
        font = painter.font()
        font.setBold(False)
        painter.setFont(font)
        
        # Add horizontal padding to prevent cramped text
        padded_rect = rect.adjusted(Sizes.HEADER_TEXT_PADDING, 0, -Sizes.HEADER_TEXT_PADDING, 0)
        
        # Draw text centered in padded rectangle
        painter.drawText(padded_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter, str(text))
    
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
    
    def _draw_sort_indicator(self, painter, rect, logical_index):
        """Draw custom sort indicator if the column is sorted.
        
        Args:
            painter: QPainter instance
            rect: Rectangle to draw in
            logical_index: Logical column index
        """
        # Check if this column has sort indicator
        if not self.isSortIndicatorShown():
            return
            
        sort_section = self.sortIndicatorSection()
        sort_order = self.sortIndicatorOrder()
        
        if sort_section != logical_index:
            return  # This column is not sorted
            
        # Calculate indicator position (right side of header)
        indicator_size = 8
        indicator_margin = 4
        indicator_rect = QtCore.QRect(
            rect.right() - indicator_size - indicator_margin,
            rect.center().y() - indicator_size // 2,
            indicator_size,
            indicator_size
        )
        
        # Set up drawing properties
        painter.setPen(QtGui.QColor(255, 255, 255))  # White for visibility
        painter.setBrush(QtGui.QColor(255, 255, 255))
        
        # Draw triangle based on sort order
        if sort_order == QtCore.Qt.AscendingOrder:
            # Up arrow (ascending)
            points = [
                QtCore.QPoint(indicator_rect.center().x(), indicator_rect.top()),
                QtCore.QPoint(indicator_rect.left(), indicator_rect.bottom()),
                QtCore.QPoint(indicator_rect.right(), indicator_rect.bottom())
            ]
        else:
            # Down arrow (descending)
            points = [
                QtCore.QPoint(indicator_rect.left(), indicator_rect.top()),
                QtCore.QPoint(indicator_rect.right(), indicator_rect.top()),
                QtCore.QPoint(indicator_rect.center().x(), indicator_rect.bottom())
            ]
        
        # Draw the triangle
        polygon = QtGui.QPolygon(points)
        painter.drawPolygon(polygon) 