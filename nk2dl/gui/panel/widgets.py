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

from .constants import Colors


class ColoredGroupBox(QtWidgets.QGroupBox):
    """Custom QGroupBox that draws colored borders and full-width dark title backgrounds without affecting layout."""
    
    def __init__(self, title, border_color, parent=None):
        super().__init__(title, parent)
        self.border_color = QtGui.QColor(border_color)
        self.border_width = 2
        
        # Use very dark grey variations for title backgrounds
        if border_color == "#4A90E2":  # Blue border
            self.title_bg_color = QtGui.QColor("#2A2633")  # Very dark grey with blue tint
        elif border_color == "#8E44AD":  # Purple border
            self.title_bg_color = QtGui.QColor("#332633")  # Very dark grey with purple tint
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


class PinnedRowTableWidget(QtWidgets.QTableWidget):
    """Custom QTableWidget that supports pinned rows at the top."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pinned_row_count = 0
        self.original_sort_enabled = True
        
    def setPinnedRowCount(self, count):
        """Set the number of rows that should be pinned at the top."""
        self.pinned_row_count = count
    
    def paintEvent(self, event):
        """Custom paint event to draw the table and then add group borders on top."""
        # First, paint the table normally
        super().paintEvent(event)
        
        # Then draw group borders on top
        self._paint_group_borders_overlay()
    
    def _paint_group_borders_overlay(self):
        """Draw group borders as an overlay on top of the table."""
        if self.pinned_row_count == 0:
            return
        
        painter = QtGui.QPainter(self.viewport())
        painter.save()
        
        # Set up the pen for group borders
        border_color = QtGui.QColor("#4A90E2")  # Job Settings blue
        pen = QtGui.QPen(border_color, 3)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        
        # Draw borders for each pinned row
        for row in range(self.pinned_row_count):
            self._draw_row_group_borders(painter, row)
        
        painter.restore()
    
    def _draw_row_group_borders(self, painter, row):
        """Draw group borders for a specific row."""
        # Define the blue group columns (3-12: Chunk through Reloadplugin)
        group_start_col = 3
        group_end_col = 12
        
        # Check if we have enough columns
        if self.columnCount() <= group_end_col:
            return
        
        # Check if any cell in the group has border data
        has_border_group = False
        for col in range(group_start_col, group_end_col + 1):
            item = self.item(row, col)
            if item:
                border_data = item.data(QtCore.Qt.UserRole + 1)
                if border_data and border_data.get('border_group') == 'blue':
                    has_border_group = True
                    break
        
        if not has_border_group:
            return
        
        # Calculate the group rectangle
        group_left = self.columnViewportPosition(group_start_col)
        group_width = 0
        for col in range(group_start_col, group_end_col + 1):
            group_width += self.columnWidth(col)
        
        row_top = self.rowViewportPosition(row)
        row_height = self.rowHeight(row)
        
        # Create the group rectangle
        group_rect = QtCore.QRect(
            group_left,
            row_top,
            group_width,
            row_height
        )
        
        # Draw the border rectangle
        # Adjust to draw exactly on the edges
        pen_width = painter.pen().width()
        half_pen = pen_width // 2
        
        border_rect = QtCore.QRect(
            group_rect.left() + half_pen,
            group_rect.top() + half_pen,
            group_rect.width() - pen_width,
            group_rect.height() - pen_width
        )
        
        painter.drawRect(border_rect)
    
    def sortByColumn(self, column, order):
        """Override sorting to exclude pinned rows."""
        if self.pinned_row_count == 0:
            super().sortByColumn(column, order)
            return
            
        # Temporarily disable sorting to extract pinned rows
        self.setSortingEnabled(False)
        
        # Store pinned rows data
        pinned_rows_data = []
        for row in range(self.pinned_row_count):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    row_data.append(item.clone())
                else:
                    row_data.append(None)
            pinned_rows_data.append(row_data)
        
        # Create a temporary table for sorting non-pinned rows
        temp_table = QtWidgets.QTableWidget()
        temp_table.setColumnCount(self.columnCount())
        temp_table.setRowCount(self.rowCount() - self.pinned_row_count)
        
        # Copy non-pinned data to temp table
        for row in range(self.pinned_row_count, self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    temp_table.setItem(row - self.pinned_row_count, col, item.clone())
        
        # Sort the temp table
        temp_table.setSortingEnabled(True)
        temp_table.sortByColumn(column, order)
        
        # Clear current table and repopulate with pinned rows first
        self.setRowCount(0)
        self.setRowCount(len(pinned_rows_data) + temp_table.rowCount())
        
        # Restore pinned rows
        for row, row_data in enumerate(pinned_rows_data):
            for col, item in enumerate(row_data):
                if item:
                    self.setItem(row, col, item)
        
        # Add sorted non-pinned rows
        for row in range(temp_table.rowCount()):
            for col in range(temp_table.columnCount()):
                item = temp_table.item(row, col)
                if item:
                    self.setItem(row + self.pinned_row_count, col, item.clone())
        
        # Style pinned rows
        self._style_pinned_rows()
        
        # Re-enable sorting
        self.setSortingEnabled(self.original_sort_enabled)
    
    def _style_pinned_rows(self):
        """Apply different styling to pinned rows with blue borders and default backgrounds."""
        job_settings_blue = QtGui.QColor("#4A90E2")  # Same blue as job settings
        job_settings_bg = QtGui.QColor("#2A2633")  # Same background as Job Settings title
        very_dark_grey = QtGui.QColor("#1A1A1A")  # Very dark grey for "All" cells
        grey_text = QtGui.QColor("#888888")  # Grey text for "All" cells
        
        for row in range(self.pinned_row_count):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    cell_text = item.text().strip()
                    
                    # Check if this is an "All" cell - use very dark grey background with grey text
                    if cell_text.lower() == "all":
                        # Use very dark grey background for "All" cells
                        item.setBackground(QtGui.QBrush(very_dark_grey))
                        item.setForeground(QtGui.QBrush(grey_text))  # Grey text color
                        font = item.font()
                        font.setBold(False)  # Remove bold
                        item.setFont(font)
                        # Make it non-editable
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                        # Clear any border data
                        item.setData(QtCore.Qt.UserRole + 1, None)
                    else:
                        # For non-"All" cells in pinned rows
                        # Make text bold for non-"All" pinned cells
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        
                        # Make Order, Node and Filename columns non-editable in master row
                        if col in [0, 1, 2]:  # Order, Node and Filename columns
                            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                            # Use default background for non-group columns
                            item.setBackground(QtGui.QBrush())
                            item.setForeground(QtGui.QBrush())
                        else:
                            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                        
                        # Store group border info for continuous outline
                        # Define which columns belong to the blue group (columns 3-12: Chunk through Reloadplugin)
                        if col >= 3 and col <= 12:  # Blue group columns
                            # Use Job Settings background color for blue group cells
                            item.setBackground(QtGui.QBrush(job_settings_bg))
                            item.setForeground(QtGui.QBrush())  # Default text color
                            
                            item.setData(QtCore.Qt.UserRole + 1, {
                                'border_group': 'blue',
                                'border_color': job_settings_blue,
                                'group_start_col': 3,
                                'group_end_col': 12
                            })
                        else:
                            # Use default background for non-group columns
                            item.setBackground(QtGui.QBrush())
                            item.setForeground(QtGui.QBrush())
                            # Clear border data for non-group columns
                            item.setData(QtCore.Qt.UserRole + 1, None)
        
        # After styling, resize columns to fit bold content
        self._resize_columns_for_bold_content()
        
        # Apply subtle CSS for better text spacing in pinned rows
        self._apply_pinned_row_styling()
    
    def _apply_pinned_row_styling(self):
        """Apply subtle styling for better text spacing in pinned rows."""
        # Use minimal CSS that doesn't interfere with background colors
        # Just add a bit more padding to the text within cells
        pinned_row_style = """
            QTableWidget::item {
                padding-left: 6px;
                padding-right: 6px;
            }
        """
        # Only apply to the first row (pinned row)
        # Note: This is a simple approach - Qt CSS doesn't easily target specific rows
        # So we'll rely on the column width adjustments we already have
        pass  # For now, let the column width adjustments handle the spacing
    
    def _resize_columns_for_bold_content(self):
        """Resize columns to fit bold content in pinned rows."""
        if self.pinned_row_count == 0:
            return
        
        # Calculate required width for each column based on bold content
        for col in range(self.columnCount()):
            max_width = 0
            
            # Check header width
            header_text = self.horizontalHeaderItem(col)
            if header_text:
                header_font = self.font()
                header_metrics = QtGui.QFontMetrics(header_font)
                try:
                    header_width = header_metrics.horizontalAdvance(header_text.text())
                except AttributeError:
                    header_width = header_metrics.width(header_text.text())
                max_width = max(max_width, header_width + 20)  # Add padding
            
            # Check pinned row content (which may be bold) - add extra padding for visual hierarchy
            for row in range(self.pinned_row_count):
                item = self.item(row, col)
                if item:
                    text = item.text()
                    if text:
                        # Use the item's actual font (which may be bold)
                        item_font = item.font()
                        item_metrics = QtGui.QFontMetrics(item_font)
                        try:
                            text_width = item_metrics.horizontalAdvance(text)
                        except AttributeError:
                            text_width = item_metrics.width(text)
                        # Add extra padding for pinned rows (30px instead of 20px)
                        max_width = max(max_width, text_width + 30)
            
            # Check a few non-pinned rows for comparison
            for row in range(self.pinned_row_count, min(self.rowCount(), self.pinned_row_count + 3)):
                item = self.item(row, col)
                if item:
                    text = item.text()
                    if text:
                        # Use normal font for non-pinned rows
                        normal_font = self.font()
                        normal_metrics = QtGui.QFontMetrics(normal_font)
                        try:
                            text_width = normal_metrics.horizontalAdvance(text)
                        except AttributeError:
                            text_width = normal_metrics.width(text)
                        max_width = max(max_width, text_width + 20)  # Normal padding
            
            # Set the column width if we calculated a meaningful width
            if max_width > 0:
                current_width = self.columnWidth(col)
                # Only increase width, don't make it smaller
                new_width = max(current_width, max_width)
                self.setColumnWidth(col, new_width)
    
    def selectRow(self, row):
        """Override to allow selection of pinned rows for editing."""
        super().selectRow(row)
    
    def setCurrentCell(self, row, column):
        """Override to allow focusing pinned rows for editing."""
        super().setCurrentCell(row, column)

    def setSortingEnabled(self, enabled):
        """Override to track original sorting state."""
        self.original_sort_enabled = enabled
        super().setSortingEnabled(enabled)
    
    def mousePressEvent(self, event):
        """Override to enable single-click editing for dropdown columns."""
        if event.button() == QtCore.Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                # Check if this is a dropdown column
                headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
                dropdown_columns = ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin", "RenderMode"]
                
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