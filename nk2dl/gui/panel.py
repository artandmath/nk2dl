"""Advanced dockable panel for nk2dl in Nuke using version-appropriate PySide."""

try:
    import nuke
    import nukescripts
    from nukescripts import panels
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

from ..common.logging import setup_logging

# Create a module-specific logger
logger = setup_logging('nk2dl.gui.panel')


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
        logger.debug(f"GroupedHeaderView resizeEvent: {event.size()}")
        
    def sectionResized(self, logicalIndex, oldSize, newSize):
        """Override to log when sections are resized."""
        super().sectionResized(logicalIndex, oldSize, newSize)
        logger.debug(f"GroupedHeaderView section {logicalIndex} resized from {oldSize}px to {newSize}px")
        
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


class MasterFallbackDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate that shows master row values as placeholder text in blank cells and handles blue borders."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.master_row_index = 0
    
    def paint(self, painter, option, index):
        """Custom paint method to show master row values as placeholders."""
        # Handle placeholder text for non-pinned rows first
        if not self._paint_placeholder_text(painter, option, index):
            # If no placeholder was painted, paint normally
            super().paint(painter, option, index)
    
    def _paint_pinned_row_text(self, painter, option, index):
        """Paint pinned row text with proper padding."""
        # Paint only the background/selection, not the text
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        
        # Create a copy of the option without text to avoid double rendering
        bg_option = QtWidgets.QStyleOptionViewItem(option)
        bg_option.text = ""  # Clear text so only background is painted
        
        # Paint background and selection state
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, bg_option, painter, option.widget)
        
        # Get the cell text
        cell_text = index.data(QtCore.Qt.DisplayRole)
        if not cell_text:
            return
        
        # Save painter state
        painter.save()
        
        # Get the item to check its font and color settings
        if hasattr(index.model(), 'item'):
            item = index.model().item(index.row(), index.column())
            if item:
                # Use the item's font (which may be bold)
                font = item.font()
                painter.setFont(font)
                
                # Use the item's foreground color
                foreground = item.foreground()
                if foreground.style() != QtCore.Qt.NoBrush:
                    painter.setPen(foreground.color())
                else:
                    painter.setPen(option.palette.color(QtGui.QPalette.Text))
        
        # Draw text with proper padding (more than normal cells)
        text_rect = option.rect.adjusted(6, 0, -6, 0)  # 6px horizontal padding
        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(cell_text))
        
        painter.restore()
    
    def _paint_placeholder_text(self, painter, option, index):
        """Paint placeholder text for blank cells using master row values.
        
        Returns:
            bool: True if placeholder was painted, False if normal painting should proceed
        """
        # Skip if this is the master row
        if index.row() == self.master_row_index:
            return False
        
        # Skip Node and Filename columns as they don't use master fallback
        if index.column() in [1, 2]:
            return False
        
        # Get column header to determine if this is a dropdown column
        headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
        dropdown_columns = ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin", "RenderMode"]
        
        if index.column() < len(headers):
            header = headers[index.column()]
            
            # Handle dropdown columns (formerly checkbox columns)
            if header in dropdown_columns:
                # Get current cell value
                actual_value = index.data(QtCore.Qt.DisplayRole)
                
                # If current cell is empty, show master value as the effective value
                if not actual_value or actual_value.strip() == "":
                    # Get master row value for this column
                    master_index = index.model().index(self.master_row_index, index.column())
                    master_value = master_index.data(QtCore.Qt.DisplayRole)
                    
                    # Check if master value is valid for this column type
                    valid_yes_no = master_value in ["Yes", "No"]
                    valid_render_mode = master_value in ["Full", "Proxy", "Both", "Script"]
                    
                    if (header in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin"] and valid_yes_no) or \
                       (header == "RenderMode" and valid_render_mode):
                        # Paint the cell background only (no text) first
                        painter.save()
                        
                        # Paint just the background/selection state without text
                        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
                        bg_option = QtWidgets.QStyleOptionViewItem(option)
                        bg_option.text = ""  # Clear text to avoid double rendering
                        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, bg_option, painter, option.widget)
                        
                        # Set up inherited value text style (greyed out italic)
                        placeholder_color = QtGui.QColor(136, 136, 136)  # #888888
                        painter.setPen(placeholder_color)
                        
                        font = painter.font()
                        font.setItalic(True)
                        font.setBold(False)  # Ensure no bold
                        painter.setFont(font)
                        
                        # Draw just the inherited value
                        text_rect = option.rect.adjusted(4, 0, -4, 0)
                        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, master_value)
                        
                        painter.restore()
                        return True
                else:
                    # For explicit values, let normal painting handle it
                    return False
                
                return False
        
        # Get the actual cell value for non-dropdown columns
        actual_value = index.data(QtCore.Qt.DisplayRole)
        
        # Skip if cell has actual content
        if actual_value and actual_value.strip():
            return False
        
        # Get master row value for this column
        master_index = index.model().index(self.master_row_index, index.column())
        master_value = master_index.data(QtCore.Qt.DisplayRole)
        
        if master_value:
            # Paint the cell background normally first
            super().paint(painter, option, index)
            
            # Save current painter state
            painter.save()
            
            # Set up placeholder text style
            placeholder_color = QtGui.QColor(128, 128, 128)  # Grey color
            painter.setPen(placeholder_color)
            
            font = painter.font()
            font.setItalic(True)
            painter.setFont(font)
            
            # Draw the placeholder text with normal padding (not extra padding like pinned rows)
            text_rect = option.rect.adjusted(4, 0, -4, 0)  # Normal 4px padding for placeholder text
            painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, master_value)
            
            # Restore painter state
            painter.restore()
            return True
        
        return False
    
    def _paint_group_borders(self, painter, option, index):
        """Paint group borders around groups of cells in pinned rows."""
        # Check if this cell is part of a border group
        border_data = index.data(QtCore.Qt.UserRole + 1)
        if not border_data or not border_data.get('border_group'):
            return
        
        # Get group information
        border_group = border_data.get('border_group')
        border_color = border_data.get('border_color', QtGui.QColor("#4A90E2"))
        group_start_col = border_data.get('group_start_col', 0)
        group_end_col = border_data.get('group_end_col', 0)
        
        # Only draw group border if this is a pinned row
        if index.row() >= self.master_row_index + 1:  # Not in pinned rows
            return
        
        # Only draw the border from the first cell in the group to avoid multiple drawings
        current_col = index.column()
        if current_col != group_start_col:
            return
        
        # Get the table widget to calculate group boundaries
        table_widget = None
        if hasattr(option.widget, 'parent') and hasattr(option.widget.parent(), 'columnViewportPosition'):
            table_widget = option.widget.parent()
        elif hasattr(option.widget, 'columnViewportPosition'):
            table_widget = option.widget
        
        if not table_widget:
            return
        
        painter.save()
        
        # Use thick pen for visibility
        pen = QtGui.QPen(border_color, 3)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)  # Sharp corners
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)  # Crisp lines
        
        # Calculate the complete group rectangle
        group_left = table_widget.columnViewportPosition(group_start_col)
        group_width = 0
        for col in range(group_start_col, group_end_col + 1):
            group_width += table_widget.columnWidth(col)
        
        # Create the complete group rectangle that spans all columns in the group
        group_rect = QtCore.QRect(
            group_left,
            option.rect.top(),
            group_width,
            option.rect.height()
        )
        
        # Draw the complete border as a single rectangle
        # Adjust by half the pen width to ensure the border is drawn on the edge, not inset
        pen_width = pen.width()
        half_pen = pen_width // 2
        
        adjusted_rect = QtCore.QRect(
            group_rect.left() - half_pen,
            group_rect.top() - half_pen,
            group_rect.width() + pen_width,
            group_rect.height() + pen_width
        )
        
        painter.drawRect(adjusted_rect)
        
        painter.restore()
    
    def createEditor(self, parent, option, index):
        """Create editor for the cell."""
        # Skip master row Order, Node and Filename columns
        if (index.row() == self.master_row_index and index.column() in [0, 1, 2]):
            return None
        
        # Handle special column types
        column = index.column()
        headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
        
        if column < len(headers):
            header = headers[column]
            
            # Dropdown columns (formerly checkbox columns)
            if header in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin"]:
                combo = QtWidgets.QComboBox(parent)
                if index.row() == self.master_row_index:
                    # Pinned row: only Yes/No options
                    combo.addItems(["Yes", "No"])
                else:
                    # Unpinned rows: Yes/No + separator + Use job settings
                    combo.addItems(["Yes", "No", "Use job settings"])
                    combo.insertSeparator(2)  # Add separator before "Use job settings"
                
                # Connect to selection signal to immediately commit and close editor
                def on_selection_made():
                    self.commitData.emit(combo)
                    self.closeEditor.emit(combo, QtWidgets.QAbstractItemDelegate.NoHint)
                
                combo.activated.connect(on_selection_made)
                return combo
            
            # Dropdown column
            elif header == "RenderMode":
                combo = QtWidgets.QComboBox(parent)
                if index.row() == self.master_row_index:
                    # Pinned row: only render mode options
                    combo.addItems(["Full", "Proxy", "Both", "Script"])
                else:
                    # Unpinned rows: render modes + separator + Use job settings
                    combo.addItems(["Full", "Proxy", "Both", "Script", "Use job settings"])
                    combo.insertSeparator(4)  # Add separator before "Use job settings"
                
                # Connect to selection signal to immediately commit and close editor
                def on_render_mode_selected():
                    self.commitData.emit(combo)
                    self.closeEditor.emit(combo, QtWidgets.QAbstractItemDelegate.NoHint)
                
                combo.activated.connect(on_render_mode_selected)
                return combo
            
            # Integer columns
            elif header in ["TaskTimeout"]:
                spin = QtWidgets.QSpinBox(parent)
                spin.setMinimum(0)
                spin.setMaximum(999)
                return spin
        
        return super().createEditor(parent, option, index)
    
    def setEditorData(self, editor, index):
        """Set data in the editor - only use actual cell value, not placeholder."""
        actual_value = index.data(QtCore.Qt.DisplayRole)
        
        if isinstance(editor, QtWidgets.QComboBox):
            # Handle combo box
            if actual_value:
                current_index = editor.findText(actual_value)
                if current_index >= 0:
                    editor.setCurrentIndex(current_index)
            
            # Show popup immediately for single-click behavior
            QtCore.QTimer.singleShot(0, editor.showPopup)
                    
        elif isinstance(editor, QtWidgets.QSpinBox):
            # Handle spin box
            try:
                value = int(actual_value) if actual_value else 0
                editor.setValue(value)
            except ValueError:
                editor.setValue(0)
        elif hasattr(editor, 'setText'):
            # Handle text editors
            editor.setText(actual_value if actual_value else "")
    
    def setModelData(self, editor, model, index):
        """Set model data from editor and update styling."""
        if isinstance(editor, QtWidgets.QComboBox):
            value = editor.currentText()
            
            # If "Use job settings" was selected, set value to empty string for inheritance
            if value == "Use job settings":
                value = ""
            
            model.setData(index, value, QtCore.Qt.DisplayRole)
            
            # Update cell styling based on value
            item = model.item(index.row(), index.column()) if hasattr(model, 'item') else None
            if item:
                headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
                if index.column() < len(headers):
                    header = headers[index.column()]
                    
                    if header in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin"]:
                        if value == "" and index.row() != self.master_row_index:
                            # Grey out inherited values in unpinned rows
                            item.setForeground(QtGui.QBrush(QtGui.QColor(136, 136, 136)))  # #888888
                        elif value in ["Yes", "No"]:
                            # White text for explicit Yes/No selections
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))  # White
                        else:
                            # Default text color
                            item.setForeground(QtGui.QBrush())
                    elif header == "RenderMode":
                        if value == "" and index.row() != self.master_row_index:
                            # Grey out inherited render mode values in unpinned rows
                            item.setForeground(QtGui.QBrush(QtGui.QColor(136, 136, 136)))  # #888888
                        elif value in ["Full", "Proxy", "Both", "Script"]:
                            # White text for explicit render mode values
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))  # White
                        else:
                            # Default text color
                            item.setForeground(QtGui.QBrush())
        else:
            super().setModelData(editor, model, index)


class CenteredCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate that centers checkboxes in tree widget columns."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Paint the item with centered checkbox."""
        # Only modify secondary columns (column > 0)
        if index.column() == 0:
            super().paint(painter, option, index)
            return
        
        # For checkbox columns, center the checkbox
        if index.flags() & QtCore.Qt.ItemIsUserCheckable:
            # Calculate centered position for checkbox
            checkbox_size = 16  # Standard checkbox size
            checkbox_x = option.rect.x() + (option.rect.width() - checkbox_size) // 2
            checkbox_y = option.rect.y() + (option.rect.height() - checkbox_size) // 2
            
            # Create centered rect for checkbox
            checkbox_rect = QtCore.QRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
            
            # Create new option with centered rect
            centered_option = QtWidgets.QStyleOptionViewItem(option)
            centered_option.rect = checkbox_rect
            
            # Draw only the checkbox indicator
            checkbox_option = QtWidgets.QStyleOptionButton()
            checkbox_option.rect = checkbox_rect
            checkbox_option.state = QtWidgets.QStyle.State_Enabled
            
            # Set checkbox state based on item's check state
            check_state = index.data(QtCore.Qt.CheckStateRole)
            if check_state == QtCore.Qt.Checked:
                checkbox_option.state |= QtWidgets.QStyle.State_On
            elif check_state == QtCore.Qt.PartiallyChecked:
                checkbox_option.state |= QtWidgets.QStyle.State_NoChange
            else:
                checkbox_option.state |= QtWidgets.QStyle.State_Off
            
            # Draw the centered checkbox
            style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
            style.drawControl(QtWidgets.QStyle.CE_CheckBox, checkbox_option, painter, option.widget)
        else:
            super().paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse events for centered checkboxes."""
        # Only handle secondary columns
        if index.column() == 0:
            return super().editorEvent(event, model, option, index)
        
        # Handle checkbox clicks
        if (event.type() == QtCore.QEvent.MouseButtonRelease and 
            index.flags() & QtCore.Qt.ItemIsUserCheckable):
            
            # Calculate if click was in checkbox area
            checkbox_size = 16
            checkbox_x = option.rect.x() + (option.rect.width() - checkbox_size) // 2
            checkbox_y = option.rect.y() + (option.rect.height() - checkbox_size) // 2
            checkbox_rect = QtCore.QRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
            
            if checkbox_rect.contains(event.pos()):
                # Toggle checkbox state
                current_state = index.data(QtCore.Qt.CheckStateRole)
                new_state = QtCore.Qt.Unchecked if current_state == QtCore.Qt.Checked else QtCore.Qt.Checked
                model.setData(index, new_state, QtCore.Qt.CheckStateRole)
                return True
        
        return super().editorEvent(event, model, option, index)


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


class Nk2dlPanel(QtWidgets.QWidget):
    """Advanced nk2dl panel using version-appropriate PySide for Nuke.
    
    This creates a comprehensive interface with proper layout control,
    settings section, tabbed interface, and professional table widget.
    Uses PySide6 for Nuke 16+ and PySide2 for earlier versions.
    """
    
    def __init__(self, parent=None):
        """Initialize the nk2dl panel."""
        if not NUKE_AVAILABLE:
            logger.error("Nuke not available, cannot create panel")
            return
            
        QtWidgets.QWidget.__init__(self, parent)
        
        # Set up the main layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(5)
        self.layout().setContentsMargins(5, 5, 5, 5)
        
        # Create the UI components
        self._create_settings_section()
        self._create_tabbed_interface()
        self._create_bottom_controls()
        
        # Set stretch factors to make render order table expand
        self.layout().setStretchFactor(self.settings_container, 0)  # Settings don't stretch
        self.layout().setStretchFactor(self.tab_widget, 1)         # Table area stretches
        
        # Set size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        logger.info(f"nk2dl panel initialized using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
    
    def _create_settings_section(self):
        """Create separate Job Settings and Machine Settings sections with responsive layout."""
        # Main container with horizontal layout for responsive behavior
        self.settings_container = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QHBoxLayout()  # Start horizontal
        self.content_layout.setSpacing(15)  # Add spacing between groups
        self.content_layout.setContentsMargins(0, 0, 0, 15)  # Add bottom margin for spacing below settings
        self.settings_container.setLayout(self.content_layout)
        
        # === JOB SETTINGS GROUP (Left) ===
        self.job_settings_group = ColoredGroupBox("Job Settings", "#4A90E2")
        job_column = QtWidgets.QVBoxLayout()
        job_column.setContentsMargins(15, 25, 15, 15)  # Increased margins for breathing room
        job_column.setSpacing(8)  # Slightly more spacing
        self.job_settings_group.setLayout(job_column)
        
        # === JOB SETTINGS CONTENT ===
        # Create a more sophisticated layout similar to Machine Settings
        job_main_layout = QtWidgets.QVBoxLayout()
        job_main_layout.setSpacing(8)
        
        # First row: Priority + Chunk Size
        priority_chunk_row = QtWidgets.QHBoxLayout()
        priority_chunk_row.setSpacing(10)
        
        priority_label = QtWidgets.QLabel("Priority")
        priority_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        priority_label.setMinimumWidth(120)
        priority_chunk_row.addWidget(priority_label)
        
        self.priority_spin = QtWidgets.QSpinBox()
        self.priority_spin.setMinimum(0)
        self.priority_spin.setMaximum(100)
        self.priority_spin.setValue(50)
        self.priority_spin.setFixedWidth(60)
        priority_chunk_row.addWidget(self.priority_spin)
        
        chunk_label = QtWidgets.QLabel("Chunk")
        chunk_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        priority_chunk_row.addWidget(chunk_label)
        
        self.chunk_size_spin = QtWidgets.QSpinBox()
        self.chunk_size_spin.setValue(1)
        self.chunk_size_spin.setMinimum(1)
        self.chunk_size_spin.setFixedWidth(60)
        priority_chunk_row.addWidget(self.chunk_size_spin)
        priority_chunk_row.addStretch()
        
        job_main_layout.addLayout(priority_chunk_row)
        
        # Second row: Frames dropdown + string input
        frames_row = QtWidgets.QHBoxLayout()
        frames_row.setSpacing(10)
        
        frames_label = QtWidgets.QLabel("Frames")
        frames_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        frames_label.setMinimumWidth(120)
        frames_row.addWidget(frames_label)
        
        self.frames_combo = QtWidgets.QComboBox()
        self.frames_combo.addItems(["Global", "Custom", "Input"])
        self.frames_combo.setFixedWidth(80)
        frames_row.addWidget(self.frames_combo)
        
        self.frame_range_edit = QtWidgets.QLineEdit("1001-2315")
        self.frame_range_edit.setMinimumWidth(150)
        frames_row.addWidget(self.frame_range_edit)
        frames_row.addStretch()
        
        job_main_layout.addLayout(frames_row)
        
        # Third row: Use node's frame list checkbox
        node_frame_list_row = QtWidgets.QHBoxLayout()
        node_frame_list_row.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label1 = QtWidgets.QLabel("")
        empty_label1.setMinimumWidth(120)
        node_frame_list_row.addWidget(empty_label1)
        
        self.use_node_frame_list_check = QtWidgets.QCheckBox("Use node's frame list")
        node_frame_list_row.addWidget(self.use_node_frame_list_check)
        node_frame_list_row.addStretch()
        
        job_main_layout.addLayout(node_frame_list_row)
        
        # Fourth row: Task Timeout + minutes + checkbox
        timeout_row = QtWidgets.QHBoxLayout()
        timeout_row.setSpacing(10)
        
        timeout_label = QtWidgets.QLabel("Task Timeout")
        timeout_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        timeout_label.setMinimumWidth(120)
        timeout_row.addWidget(timeout_label)
        
        self.task_timeout_spin = QtWidgets.QSpinBox()
        self.task_timeout_spin.setMinimum(0)
        self.task_timeout_spin.setMaximum(999)
        self.task_timeout_spin.setValue(0)
        self.task_timeout_spin.setFixedWidth(60)
        timeout_row.addWidget(self.task_timeout_spin)
        
        minutes_label = QtWidgets.QLabel("minutes")
        minutes_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        timeout_row.addWidget(minutes_label)
        
        self.enable_auto_timeout_check = QtWidgets.QCheckBox("Enable auto task timeout")
        timeout_row.addWidget(self.enable_auto_timeout_check)
        timeout_row.addStretch()
        
        job_main_layout.addLayout(timeout_row)
        
        # Fifth row: Render Mode
        render_mode_row = QtWidgets.QHBoxLayout()
        render_mode_row.setSpacing(10)
        
        render_mode_label = QtWidgets.QLabel("Render Mode")
        render_mode_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        render_mode_label.setMinimumWidth(120)
        render_mode_row.addWidget(render_mode_label)
        
        self.render_mode_combo = QtWidgets.QComboBox()
        self.render_mode_combo.addItems(["Full", "Proxy", "Both", "Script"])
        self.render_mode_combo.setFixedWidth(100)
        render_mode_row.addWidget(self.render_mode_combo)
        render_mode_row.addStretch()
        
        job_main_layout.addLayout(render_mode_row)
        
        # Sixth row: Use Nuke X + Use Batch Mode + Reload plugin between tasks checkboxes
        checkboxes_row = QtWidgets.QHBoxLayout()
        checkboxes_row.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label2 = QtWidgets.QLabel("")
        empty_label2.setMinimumWidth(120)
        checkboxes_row.addWidget(empty_label2)
        
        self.render_nukex_check = QtWidgets.QCheckBox("Use Nuke X")
        checkboxes_row.addWidget(self.render_nukex_check)
        
        self.use_batch_mode_check = QtWidgets.QCheckBox("Use batch mode")
        checkboxes_row.addWidget(self.use_batch_mode_check)
        
        self.reload_plugin_check = QtWidgets.QCheckBox("Reload plugin between tasks")
        checkboxes_row.addWidget(self.reload_plugin_check)
        checkboxes_row.addStretch()
        
        job_main_layout.addLayout(checkboxes_row)
        
        # Add a visual divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setFrameShadow(QtWidgets.QFrame.Sunken)
        divider.setStyleSheet("color: #C0C0C0; margin: 5px 0px;")
        job_main_layout.addWidget(divider)
        
        # Job organization checkboxes
        job_org_row1 = QtWidgets.QHBoxLayout()
        job_org_row1.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label3 = QtWidgets.QLabel("")
        empty_label3.setMinimumWidth(120)
        job_org_row1.addWidget(empty_label3)
        
        self.separate_tasks_check = QtWidgets.QCheckBox("Write node as separate tasks for the same job")
        job_org_row1.addWidget(self.separate_tasks_check)
        job_org_row1.addStretch()
        
        job_main_layout.addLayout(job_org_row1)
        
        job_org_row2 = QtWidgets.QHBoxLayout()
        job_org_row2.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label4 = QtWidgets.QLabel("")
        empty_label4.setMinimumWidth(120)
        job_org_row2.addWidget(empty_label4)
        
        self.separate_jobs_check = QtWidgets.QCheckBox("Write nodes as separate jobs")
        job_org_row2.addWidget(self.separate_jobs_check)
        job_org_row2.addStretch()
        
        job_main_layout.addLayout(job_org_row2)
        
        job_org_row3 = QtWidgets.QHBoxLayout()
        job_org_row3.setSpacing(10)
        
        # Empty label to maintain alignment
        empty_label5 = QtWidgets.QLabel("")
        empty_label5.setMinimumWidth(120)
        job_org_row3.addWidget(empty_label5)
        
        self.views_separate_jobs_check = QtWidgets.QCheckBox("Views as separate jobs")
        job_org_row3.addWidget(self.views_separate_jobs_check)
        job_org_row3.addStretch()
        
        job_main_layout.addLayout(job_org_row3)
        
        job_column.addLayout(job_main_layout)
        job_column.addStretch()
        
        # === MACHINE SETTINGS GROUP (Right) ===
        self.machine_settings_group = ColoredGroupBox("Machine Settings", "#8E44AD")
        machine_column = QtWidgets.QVBoxLayout()
        machine_column.setContentsMargins(15, 25, 15, 15)  # Increased margins for breathing room
        machine_column.setSpacing(8)  # Slightly more spacing
        self.machine_settings_group.setLayout(machine_column)
        
        # === MACHINE SETTINGS CONTENT ===
        # Create a more sophisticated layout with fixed widget sizes
        machine_main_layout = QtWidgets.QVBoxLayout()
        machine_main_layout.setSpacing(8)
        
        # First row: Pool + Secondary Pool + Group
        pool_group_row = QtWidgets.QHBoxLayout()
        pool_group_row.setSpacing(10)
        
        pool_label = QtWidgets.QLabel("Pool")
        pool_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        pool_label.setMinimumWidth(120)  # Fixed label width
        pool_group_row.addWidget(pool_label)
        
        self.pool_combo = QtWidgets.QComboBox()
        self.pool_combo.addItems(["comp", "render", "light", "fx"])
        self.pool_combo.setFixedWidth(100)
        pool_group_row.addWidget(self.pool_combo)
        
        secondary_pool_label = QtWidgets.QLabel("Secondary Pool")
        secondary_pool_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(secondary_pool_label)
        
        self.secondary_pool_combo = QtWidgets.QComboBox()
        self.secondary_pool_combo.addItems(["", "comp", "render", "light", "fx"])
        self.secondary_pool_combo.setFixedWidth(100)
        pool_group_row.addWidget(self.secondary_pool_combo)
        
        group_label = QtWidgets.QLabel("Group")
        group_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        pool_group_row.addWidget(group_label)
        
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(["none", "comp_high", "comp_med", "render_high", "render_low"])
        self.group_combo.setFixedWidth(120)
        pool_group_row.addWidget(self.group_combo)
        pool_group_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(pool_group_row)
        
        # Second row: Threads
        threads_row = QtWidgets.QHBoxLayout()
        threads_row.setSpacing(10)
        
        threads_label = QtWidgets.QLabel("Threads")
        threads_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        threads_label.setMinimumWidth(120)  # Fixed label width
        threads_row.addWidget(threads_label)
        
        self.threads_spin = QtWidgets.QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(64)
        self.threads_spin.setValue(4)
        self.threads_spin.setFixedWidth(60)  # Fixed widget width
        threads_row.addWidget(self.threads_spin)
        threads_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(threads_row)
        
        # Third row: Min RAM + Max RAM
        ram_row = QtWidgets.QHBoxLayout()
        ram_row.setSpacing(10)
        
        min_ram_label = QtWidgets.QLabel("Min RAM (GB)")
        min_ram_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        min_ram_label.setMinimumWidth(120)  # Same fixed label width
        ram_row.addWidget(min_ram_label)
        
        self.min_ram_spin = QtWidgets.QSpinBox()
        self.min_ram_spin.setMinimum(1)
        self.min_ram_spin.setMaximum(64)
        self.min_ram_spin.setValue(0)
        self.min_ram_spin.setFixedWidth(60)  # Fixed widget width
        ram_row.addWidget(self.min_ram_spin)
        
        # Vertical separator
        separator5 = QtWidgets.QFrame()
        separator5.setFrameShape(QtWidgets.QFrame.VLine)
        separator5.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator5.setFixedWidth(1)
        ram_row.addWidget(separator5)
        
        self.max_ram_spin = QtWidgets.QSpinBox()
        self.max_ram_spin.setMinimum(1)
        self.max_ram_spin.setMaximum(512)
        self.max_ram_spin.setValue(0)
        self.max_ram_spin.setFixedWidth(60)  # Fixed widget width
        ram_row.addWidget(self.max_ram_spin)
        
        max_ram_label = QtWidgets.QLabel("Max RAM (GB)")
        max_ram_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        ram_row.addWidget(max_ram_label)
        ram_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(ram_row)
        
        # Fourth row: GPU Device + GPU Override + Use GPU
        gpu_row = QtWidgets.QHBoxLayout()
        gpu_row.setSpacing(10)
        
        gpu_device_label = QtWidgets.QLabel("GPU Device")
        gpu_device_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        gpu_device_label.setMinimumWidth(120)  # Fixed label width
        gpu_row.addWidget(gpu_device_label)
        
        self.gpu_override_spin = QtWidgets.QSpinBox()
        self.gpu_override_spin.setMinimum(0)
        self.gpu_override_spin.setMaximum(16)
        self.gpu_override_spin.setValue(0)
        self.gpu_override_spin.setFixedWidth(60)  # Fixed widget width
        gpu_row.addWidget(self.gpu_override_spin)
        
        # Vertical separator
        separator6 = QtWidgets.QFrame()
        separator6.setFrameShape(QtWidgets.QFrame.VLine)
        separator6.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator6.setFixedWidth(1)
        gpu_row.addWidget(separator6)
        
        self.use_gpu_check = QtWidgets.QCheckBox("Use GPU")
        gpu_row.addWidget(self.use_gpu_check)
        gpu_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(gpu_row)
        
        # Fifth row: Concurrent Tasks + checkbox
        concurrent_row = QtWidgets.QHBoxLayout()
        concurrent_row.setSpacing(10)
        
        concurrent_label = QtWidgets.QLabel("Concurrent Tasks")
        concurrent_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        concurrent_label.setMinimumWidth(120)  # Same fixed label width
        concurrent_row.addWidget(concurrent_label)
        
        self.concurrent_tasks_spin = QtWidgets.QSpinBox()
        self.concurrent_tasks_spin.setMinimum(1)
        self.concurrent_tasks_spin.setMaximum(64)
        self.concurrent_tasks_spin.setValue(2)
        self.concurrent_tasks_spin.setFixedWidth(60)  # Fixed widget width
        concurrent_row.addWidget(self.concurrent_tasks_spin)
        
        # Vertical separator
        separator7 = QtWidgets.QFrame()
        separator7.setFrameShape(QtWidgets.QFrame.VLine)
        separator7.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator7.setFixedWidth(1)
        concurrent_row.addWidget(separator7)
        
        self.limit_tasks_check = QtWidgets.QCheckBox("Limit tasks to worker's task limit")
        concurrent_row.addWidget(self.limit_tasks_check)
        concurrent_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(concurrent_row)
        
        # Sixth row: Machine Limit + checkbox
        limit_row = QtWidgets.QHBoxLayout()
        limit_row.setSpacing(10)
        
        machine_limit_label = QtWidgets.QLabel("Machine Limit")
        machine_limit_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_limit_label.setMinimumWidth(120)  # Same fixed label width
        limit_row.addWidget(machine_limit_label)
        
        self.machine_limit_spin = QtWidgets.QSpinBox()
        self.machine_limit_spin.setMinimum(0)
        self.machine_limit_spin.setMaximum(999)
        self.machine_limit_spin.setValue(0)
        self.machine_limit_spin.setFixedWidth(60)  # Fixed widget width
        limit_row.addWidget(self.machine_limit_spin)
        
        # Vertical separator
        separator8 = QtWidgets.QFrame()
        separator8.setFrameShape(QtWidgets.QFrame.VLine)
        separator8.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator8.setFixedWidth(1)
        limit_row.addWidget(separator8)
        
        self.machine_deny_list_check = QtWidgets.QCheckBox("Machine list is a deny list")
        limit_row.addWidget(self.machine_deny_list_check)
        limit_row.addStretch()  # Push everything to left
        
        machine_main_layout.addLayout(limit_row)
        
        # Seventh row: Machine List + Browse button
        machine_list_row = QtWidgets.QHBoxLayout()
        machine_list_row.setSpacing(10)
        
        machine_list_label = QtWidgets.QLabel("Machine List")
        machine_list_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        machine_list_label.setMinimumWidth(120)  # Same fixed label width
        machine_list_row.addWidget(machine_list_label)
        
        self.machine_list_edit = QtWidgets.QLineEdit()
        self.machine_list_edit.setMinimumWidth(300)  # Fixed minimum width
        machine_list_row.addWidget(self.machine_list_edit)
        
        self.machine_list_browse_btn = QtWidgets.QPushButton("Browse")
        self.machine_list_browse_btn.setFixedWidth(80)  # Fixed button width
        machine_list_row.addWidget(self.machine_list_browse_btn)
        
        machine_main_layout.addLayout(machine_list_row)
        
        # Eighth row: Limits + Browse button
        limits_row = QtWidgets.QHBoxLayout()
        limits_row.setSpacing(10)
        
        limits_label = QtWidgets.QLabel("Limits")
        limits_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        limits_label.setMinimumWidth(120)  # Same fixed label width
        limits_row.addWidget(limits_label)
        
        self.limits_edit = QtWidgets.QLineEdit()
        self.limits_edit.setMinimumWidth(300)  # Fixed minimum width
        limits_row.addWidget(self.limits_edit)
        
        self.limits_browse_btn = QtWidgets.QPushButton("Browse")
        self.limits_browse_btn.setFixedWidth(80)  # Fixed button width
        limits_row.addWidget(self.limits_browse_btn)
        
        machine_main_layout.addLayout(limits_row)
        
        machine_column.addLayout(machine_main_layout)
        machine_column.addStretch()
        
        # Add group box to wrapper
        self.content_layout.addWidget(self.job_settings_group, 1)  # Stretch factor 1
        self.content_layout.addWidget(self.machine_settings_group, 1)  # Stretch factor 1
        
        # Add the settings container to main panel layout
        self.layout().addWidget(self.settings_container)
        
        # Override the resize event for the main panel to handle responsive behavior
        original_resize = self.resizeEvent
        def responsive_resize_event(event):
            self._handle_responsive_resize(event)
            if original_resize:
                original_resize(event)
        self.resizeEvent = responsive_resize_event
    
    def _handle_responsive_resize(self, event):
        """Handle panel resize to make settings responsive."""
        if hasattr(self, 'content_layout'):
            panel_width = event.size().width()
            
            # Calculate if we have enough space for horizontal layout
            # Account for margins and spacing
            available_width = panel_width - 60  # Account for margins and group box padding
            
            if available_width < 700:  # Stack vertically when narrow
                if self.content_layout.direction() == QtWidgets.QBoxLayout.LeftToRight:
                    self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                    self.content_layout.setSpacing(20)  # More spacing when stacked vertically
            else:  # Side by side when wide enough
                if self.content_layout.direction() == QtWidgets.QBoxLayout.TopToBottom:
                    self.content_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)
                    self.content_layout.setSpacing(15)  # Less spacing when side by side
    
    def _create_tabbed_interface(self):
        """Create the tabbed interface for Node Settings, GSVs, Extra Settings, and Console."""
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Node Settings tab (formerly Render Order)
        self._create_node_settings_tab()
        
        # GSVs tab (only for Nuke 15.1+)
        if NUKE_AVAILABLE and self._is_nuke_15_1_or_later():
            self._create_gsvs_tab()
        
        # Extra Settings tab
        self._create_extra_settings_tab()
        
        # Console tab (moved to last)
        self._create_console_tab()
        
        # Add tab widget to main layout
        self.layout().addWidget(self.tab_widget)
    
    def _is_nuke_15_1_or_later(self):
        """Check if Nuke version is 15.1 or later."""
        try:
            major = nuke.NUKE_VERSION_MAJOR
            minor = nuke.NUKE_VERSION_MINOR
            return (major > 15) or (major == 15 and minor >= 1)
        except:
            return False
    
    def _create_node_settings_tab(self):
        """Create the Node Settings tab with table and controls (formerly Render Order)."""
        render_order_widget = QtWidgets.QWidget()
        render_order_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        render_order_layout = QtWidgets.QVBoxLayout()
        render_order_widget.setLayout(render_order_layout)
        
        # Control buttons with filter
        button_layout = QtWidgets.QHBoxLayout()
        
        self.update_btn = QtWidgets.QPushButton("Update")
        self.update_btn.clicked.connect(self._on_update_clicked)
        button_layout.addWidget(self.update_btn)
        
        self.all_btn = QtWidgets.QPushButton("All")
        self.all_btn.clicked.connect(self._on_all_clicked)
        button_layout.addWidget(self.all_btn)
        
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        button_layout.addWidget(self.clear_btn)
        
        self.selection_btn = QtWidgets.QPushButton("Selection")
        self.selection_btn.clicked.connect(self._on_selection_clicked)
        button_layout.addWidget(self.selection_btn)
        
        self.inside_groups_check = QtWidgets.QCheckBox("Inside groups")
        self.inside_groups_check.stateChanged.connect(lambda state: print(f"Inside groups: {state == 2}"))
        button_layout.addWidget(self.inside_groups_check)
        
        # Add spacer to push filter to the right
        button_layout.addStretch()
        
        # Filter input on same row
        button_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("filter...")
        self.filter_edit.setMaximumWidth(150)  # Limit width so it doesn't take too much space
        button_layout.addWidget(self.filter_edit)
        
        render_order_layout.addLayout(button_layout)
        
        # Render Order Table
        self.render_table = PinnedRowTableWidget()
        self.render_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
        self.render_table.setColumnCount(len(headers))
        self.render_table.setHorizontalHeaderLabels(headers)
        
        # Sample data - updated to include new blue group columns
        sample_data = [
            # Master control row (will be styled differently and editable)
            ("All", "All", "All", "5", "1001-2315", "50", "Yes", "0", "Yes", "Full", "Yes", "Yes", "Yes"),
            # Regular data rows - some cells blank to demonstrate fallback to master values
            ("3999", "Write4", "Some_path1_v002.%04d.exr", "", "1350-1650", "", "", "", "", "", "", "", ""),
            ("3100", "Write30", "Some_path3_v002.%04d.exr", "3", "", "40", "", "10", "", "Proxy", "", "", ""),
            ("3050", "Write27", "Some_path5_v002.%04d.exr", "", "1570-1620", "", "", "", "", "", "", "", ""),
            ("3000", "Write9", "Some_path6_v002.%04d.exr", "8", "1350-1650", "60", "No", "", "No", "Both", "No", "No", "No"),
            ("2999", "Write3", "Some_path9_v002.%04d.exr", "", "", "", "", "", "", "", "", "", ""),
        ]
        
        self.render_table.setRowCount(len(sample_data))
        checkbox_columns = [6, 8, 10, 11, 12]  # NodesFrames, AutoTimeout, NukeX, BatchMode, Reloadplugin
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QtWidgets.QTableWidgetItem()
                
                if col in checkbox_columns:
                    # Handle dropdown columns (formerly checkbox columns)
                    item.setText(str(value) if value is not None else "")
                    
                    # Apply styling based on value
                    if str(value) == "" and row != 0:  # Empty string means inherit from master row
                        # Grey out inherited values in unpinned rows
                        item.setForeground(QtGui.QBrush(QtGui.QColor(136, 136, 136)))  # #888888
                    elif str(value) in ["Yes", "No"]:
                        # White text for explicit Yes/No values
                        item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))  # White
                    else:
                        # Default text color
                        item.setForeground(QtGui.QBrush())
                else:
                    # Handle regular text columns
                    item.setText(str(value) if value is not None else "")
                
                self.render_table.setItem(row, col, item)
        
        # Set the first row as pinned master control row
        self.render_table.setPinnedRowCount(1)
        
        # Apply custom delegate to show master row values as placeholders
        self.fallback_delegate = MasterFallbackDelegate(self.render_table)
        self.render_table.setItemDelegate(self.fallback_delegate)
        
        # Connect itemChanged to refresh placeholders when master row changes
        self.render_table.itemChanged.connect(self._on_master_row_changed)
        
        # Table properties
        self.render_table.setAlternatingRowColors(True)
        self.render_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.render_table.setSortingEnabled(True)
        self.render_table.resizeColumnsToContents()
        
        # Apply initial styling to pinned row
        self.render_table._style_pinned_rows()
        
        render_order_layout.addWidget(self.render_table)
        
        # Set stretch factor to make table expand
        render_order_layout.setStretchFactor(self.render_table, 1)
        
        # Add render order tab
        self.tab_widget.addTab(render_order_widget, "Node Settings")
    
    def _create_gsvs_tab(self):
        """Create the GSVs tab with Primary GSVs as tree hierarchy and Secondary GSVs as columns."""
        gsvs_widget = QtWidgets.QWidget()
        gsvs_layout = QtWidgets.QVBoxLayout()
        gsvs_layout.setContentsMargins(15, 15, 15, 15)
        gsvs_layout.setSpacing(10)
        gsvs_widget.setLayout(gsvs_layout)
        
        # GSVs input fields on one line
        input_layout = QtWidgets.QHBoxLayout()
        
        # Primary GSVs (tree hierarchy)
        input_layout.addWidget(QtWidgets.QLabel("Primary GSVs:"))
        self.primary_gsvs_field = QtWidgets.QLineEdit()
        self.primary_gsvs_field.setPlaceholderText("Sequence, Shotcode...")
        self.primary_gsvs_field.setText("Sequence, Shotcode")
        self.primary_gsvs_field.textChanged.connect(self._on_gsvs_text_changed)
        input_layout.addWidget(self.primary_gsvs_field)
        
        # Secondary GSVs (columns)
        input_layout.addWidget(QtWidgets.QLabel("Secondary GSVs:"))
        self.secondary_gsvs_field = QtWidgets.QLineEdit()
        self.secondary_gsvs_field.setPlaceholderText("Resolution, Format...")
        self.secondary_gsvs_field.setText("Resolution, Format")
        self.secondary_gsvs_field.textChanged.connect(self._on_gsvs_text_changed)
        input_layout.addWidget(self.secondary_gsvs_field)
        
        # Refresh button
        refresh_hierarchy_btn = QtWidgets.QPushButton("Refresh Hierarchy")
        refresh_hierarchy_btn.clicked.connect(self._update_gsvs_hierarchy)
        input_layout.addWidget(refresh_hierarchy_btn)
        
        gsvs_layout.addLayout(input_layout)
        
        # Tree widget for hierarchical GSVs with additional columns
        self.gsvs_tree = QtWidgets.QTreeWidget()
        self.gsvs_tree.setRootIsDecorated(True)
        self.gsvs_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.gsvs_tree.setAlternatingRowColors(True)  # Enable alternating row colors
        self.gsvs_tree.itemChanged.connect(self._on_tree_item_changed)
        
        gsvs_layout.addWidget(self.gsvs_tree)
        
        # Control buttons
        controls_layout = QtWidgets.QHBoxLayout()
        
        expand_all_btn = QtWidgets.QPushButton("Expand All")
        expand_all_btn.clicked.connect(self.gsvs_tree.expandAll)
        controls_layout.addWidget(expand_all_btn)
        
        collapse_all_btn = QtWidgets.QPushButton("Collapse All")
        collapse_all_btn.clicked.connect(self.gsvs_tree.collapseAll)
        controls_layout.addWidget(collapse_all_btn)
        
        controls_layout.addStretch()
        
        check_all_btn = QtWidgets.QPushButton("Check All")
        check_all_btn.clicked.connect(self._check_all_items)
        controls_layout.addWidget(check_all_btn)
        
        uncheck_all_btn = QtWidgets.QPushButton("Uncheck All")
        uncheck_all_btn.clicked.connect(self._uncheck_all_items)
        controls_layout.addWidget(uncheck_all_btn)
        
        gsvs_layout.addLayout(controls_layout)
        
        # Store the hierarchy data
        self.primary_gsv_levels = []
        self.secondary_gsv_levels = []
        self.secondary_gsv_data = {
            'Resolution': ['Full', 'Proxy'],
            'Format': ['EXR', 'MOV', 'DWAA']
        }
        self.gsv_data = {}
        
        # Initialize with default hierarchy
        self._create_sample_gsv_data()
        self._update_gsvs_hierarchy()
        
        # Add GSVs tab
        self.tab_widget.addTab(gsvs_widget, "GSVs")
    
    def _create_sample_gsv_data(self):
        """Create sample hierarchical GSV data structure."""
        # Primary GSV hierarchy (tree structure)
        self.gsv_data = {
            'Sequence': {
                'seq010': {
                    'Shotcode': {
                        'sh001': {},
                        'sh002': {},
                        'sh003': {}
                    }
                },
                'seq020': {
                    'Shotcode': {
                        'sh010': {},
                        'sh011': {},
                        'sh012': {}
                    }
                },
                'seq030': {
                    'Shotcode': {
                        'sh020': {},
                        'sh021': {}
                    }
                }
            }
        }
        
        # Secondary GSV data (column values)
        self.secondary_gsv_data = {
            'Resolution': ['Full', 'Proxy'],
            'Format': ['EXR', 'MOV', 'DWAA']
        }
    
    def _on_gsvs_text_changed(self):
        """Handle changes to either GSV text field - update hierarchy after a short delay."""
        # Use a timer to avoid updating on every keystroke
        if hasattr(self, '_gsvs_update_timer'):
            self._gsvs_update_timer.stop()
        
        self._gsvs_update_timer = QtCore.QTimer()
        self._gsvs_update_timer.setSingleShot(True)
        self._gsvs_update_timer.timeout.connect(self._update_gsvs_hierarchy)
        self._gsvs_update_timer.start(500)  # 500ms delay
    
    def _update_gsvs_hierarchy(self):
        """Update the GSV hierarchy tree and columns based on the text fields."""
        # Store current header view to preserve it
        current_header = self.gsvs_tree.header() if hasattr(self.gsvs_tree, 'header') else None
        is_grouped_header = isinstance(current_header, GroupedHeaderView)
        
        # Clear existing tree
        self.gsvs_tree.clear()
        
        # Parse the Primary GSVs text field
        primary_text = self.primary_gsvs_field.text().strip()
        secondary_text = self.secondary_gsvs_field.text().strip()
        
        if not primary_text:
            return
        
        # Split by comma and clean up level names
        self.primary_gsv_levels = [level.strip() for level in primary_text.split(',') if level.strip()]
        self.secondary_gsv_levels = [level.strip() for level in secondary_text.split(',') if level.strip()]
        
        # Set up tree headers with simple format
        headers = ["Primary GSVs"]
        
        # Calculate the maximum text width for secondary columns
        max_text_width = 0
        font_metrics = QtGui.QFontMetrics(self.gsvs_tree.font())
        
        # Add secondary GSV columns with simple format
        for secondary_gsv in self.secondary_gsv_levels:
            if secondary_gsv in self.secondary_gsv_data:
                for value in self.secondary_gsv_data[secondary_gsv]:
                    headers.append(value)
                    # Calculate width for this text
                    try:
                        text_width = font_metrics.horizontalAdvance(value)
                    except AttributeError:
                        # Fallback for older Qt versions
                        text_width = font_metrics.width(value)
                    max_text_width = max(max_text_width, text_width)
        
        self.gsvs_tree.setHeaderLabels(headers)
        self.gsvs_tree.setColumnCount(len(headers))
        
        # Apply grouped header view if we have secondary columns
        if len(headers) > 1:
            # Only create new header if we don't have one or it's not grouped
            if not is_grouped_header:
                grouped_header = GroupedHeaderView(QtCore.Qt.Horizontal, self.gsvs_tree)
                self.gsvs_tree.setHeader(grouped_header)
            else:
                grouped_header = current_header
            
            # Calculate groups for secondary GSVs
            groups = []
            col_index = 1  # Start after Primary GSVs column
            
            for secondary_gsv in self.secondary_gsv_levels:
                if secondary_gsv in self.secondary_gsv_data:
                    values = self.secondary_gsv_data[secondary_gsv]
                    if len(values) > 1:
                        # Create group spanning multiple columns
                        start_col = col_index
                        end_col = col_index + len(values) - 1
                        groups.append((secondary_gsv, start_col, end_col))
                    col_index += len(values)
            
            grouped_header.setGroups(groups)
        
        # Build the tree structure
        if self.primary_gsv_levels:
            self._build_tree_structure()
            
            # Expand first level by default
            self.gsvs_tree.expandToDepth(0)
            
            # Set up column sizing and alignment
            self._setup_column_properties(max_text_width)
            
            # Force column widths after everything is set up
            self._force_column_widths()
            
            # Use a timer to force widths again after UI is fully rendered
            QtCore.QTimer.singleShot(100, self._delayed_force_column_widths)
    
    def _force_column_widths(self):
        """Force column widths after all setup is complete."""
        header = self.gsvs_tree.header()
        
        # Force primary column width
        primary_width = self._calculate_primary_column_width()
        header.resizeSection(0, primary_width)
        
        # Force secondary column widths
        secondary_width = self._calculate_secondary_column_width()
        for i in range(1, self.gsvs_tree.columnCount()):
            header.resizeSection(i, secondary_width)
            # Also try setting maximum width to prevent expansion
            header.setMaximumSectionSize(secondary_width)
        
        # Force update
        self.gsvs_tree.updateGeometry()
        header.updateGeometry()
        
        logger.info(f"Forced column widths: primary={primary_width}px, secondary={secondary_width}px for {self.gsvs_tree.columnCount()-1} columns")
    
    def _delayed_force_column_widths(self):
        """Force column widths after a delay to ensure they stick."""
        header = self.gsvs_tree.header()
        secondary_width = self._calculate_secondary_column_width()
        
        # Force secondary columns to be narrow
        for i in range(1, self.gsvs_tree.columnCount()):
            # Set both resize section and maximum section size
            header.resizeSection(i, secondary_width)
            header.setMaximumSectionSize(secondary_width)
            header.setMinimumSectionSize(secondary_width)  # Also set minimum to lock the width
        
        logger.info(f"Delayed force: locked secondary columns to {secondary_width}px (min=max={secondary_width}px)")
    
    def _setup_column_properties(self, max_text_width):
        """Set up column properties including width, alignment, and resize behavior."""
        header = self.gsvs_tree.header()
        
        # Set up each column independently
        for i in range(self.gsvs_tree.columnCount()):
            if i == 0:
                # Primary GSVs column - completely independent sizing
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Interactive)
                
                # Calculate and set primary column width independently
                primary_width = self._calculate_primary_column_width()
                header.resizeSection(i, primary_width)
                header.setMinimumSectionSize(primary_width)
                
                logger.info(f"Primary column width set to: {primary_width}px")
                
            else:
                # Secondary GSV columns - completely independent sizing
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
                
                # Calculate secondary column width independently (no dependency on primary)
                secondary_width = self._calculate_secondary_column_width()
                header.resizeSection(i, secondary_width)
                
                logger.info(f"Secondary column {i} width set to: {secondary_width}px")
        
        # Center align checkboxes in secondary columns using stylesheet
        checkbox_style = """
            QTreeWidget::item {
                padding-top: 2px;
                padding-bottom: 2px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            QTreeWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QTreeWidget::item:selected:active {
                background-color: transparent;
            }
            QTreeWidget::item:selected:!active {
                background-color: transparent;
            }
        """
        
        self.gsvs_tree.setStyleSheet(checkbox_style)
        
        # Apply centered checkbox delegate
        self.centered_delegate = CenteredCheckboxDelegate(self.gsvs_tree)
        self.gsvs_tree.setItemDelegate(self.centered_delegate)
    
    def _calculate_secondary_column_width(self):
        """Calculate the optimal width for secondary GSV columns based on their content only."""
        # Use a fresh font metrics calculation
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        longest_value = ""
        
        # Only look at actual secondary GSV values - completely independent calculation
        all_values = []
        for secondary_gsv in self.secondary_gsv_levels:
            if secondary_gsv in self.secondary_gsv_data:
                all_values.extend(self.secondary_gsv_data[secondary_gsv])
        
        # Find the longest value among all secondary GSV values
        for value in all_values:
            value_str = str(value)
            try:
                text_width = font_metrics.horizontalAdvance(value_str)
            except AttributeError:
                # Fallback for older Qt versions
                text_width = font_metrics.width(value_str)
            
            if text_width > max_width:
                max_width = text_width
                longest_value = value_str
        
        # Fallback if no values found
        if max_width == 0:
            max_width = 20
            longest_value = "N/A"
        
        # Add padding for checkbox centering AND header text padding
        checkbox_padding = 6  # Minimal padding for checkbox centering
        header_text_padding = 8  # 4px left + 4px right for header text padding
        total_padding = checkbox_padding + header_text_padding
        final_width = max_width + total_padding
        
        # Very small minimum to ensure narrow columns
        min_width = 35  # Reduced to be very narrow
        calculated_width = max(final_width, min_width)
        
        # Debug output
        logger.info(f"Secondary column width: text='{longest_value}' ({max_width}px), checkbox_pad={checkbox_padding}px, header_pad={header_text_padding}px, total={calculated_width}px")
        
        return calculated_width
    
    def _calculate_primary_column_width(self):
        """Calculate the optimal width for the primary GSVs column based on content."""
        if not hasattr(self, 'gsvs_tree') or not self.gsvs_tree.model():
            return 150  # Default fallback
        
        # Use bold font for measurement since tree items may be bold
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        
        # Check the header text width
        header_text = "Primary GSVs"
        try:
            header_width = font_metrics.horizontalAdvance(header_text)
        except AttributeError:
            # Fallback for older Qt versions
            header_width = font_metrics.width(header_text)
        max_width = max(max_width, header_width)
        
        # Check all tree items recursively
        def check_item_width(item, indent_level=0):
            nonlocal max_width
            if item:
                # Calculate text width including indentation
                text = item.text(0)
                if text:
                    try:
                        text_width = font_metrics.horizontalAdvance(text)
                    except AttributeError:
                        text_width = font_metrics.width(text)
                    
                    # Add indentation (approximately 20px per level)
                    indented_width = text_width + (indent_level * 20)
                    max_width = max(max_width, indented_width)
                
                # Check children
                for i in range(item.childCount()):
                    check_item_width(item.child(i), indent_level + 1)
        
        # Check all top-level items
        for i in range(self.gsvs_tree.topLevelItemCount()):
            check_item_width(self.gsvs_tree.topLevelItem(i), 0)
        
        # Add padding for tree decorations, checkboxes, and margins
        padding = 60  # Space for expand/collapse icons, checkboxes, and margins
        final_width = max_width + padding
        
        # Ensure minimum and maximum bounds
        min_width = 120  # Absolute minimum for usability
        max_width_limit = 300  # Don't make it too wide
        
        return max(min_width, min(final_width, max_width_limit))
    
    def _build_tree_structure(self):
        """Build the tree structure from the Primary GSV data."""
        if not self.primary_gsv_levels:
            return
        
        # Start with the first level (root level)
        self._build_tree_level(self.gsv_data, None, 0)
    
    def _build_tree_level(self, data, parent_item, level_index):
        """Recursively build tree levels for Primary GSVs.
        
        Args:
            data (dict): Current level data
            parent_item (QTreeWidgetItem): Parent tree item (None for root)
            level_index (int): Current level in primary hierarchy
        """
        if level_index >= len(self.primary_gsv_levels):
            return
        
        level_name = self.primary_gsv_levels[level_index]
        
        if level_name not in data:
            return
        
        level_data = data[level_name]
        
        # Handle dictionary data (has sub-levels)
        if isinstance(level_data, dict):
            for item_key, item_data in sorted(level_data.items()):
                # Create tree item
                tree_item = QtWidgets.QTreeWidgetItem()
                tree_item.setText(0, item_key)
                
                # Add checkbox to primary column (column 0)
                tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                tree_item.setCheckState(0, QtCore.Qt.Unchecked)
                
                # Store metadata for primary column
                tree_item.setData(0, QtCore.Qt.UserRole, {
                    'level': level_name,
                    'value': item_key,
                    'level_index': level_index,
                    'is_primary': True
                })
                
                # Add checkboxes for secondary GSVs
                column_index = 1
                for secondary_gsv in self.secondary_gsv_levels:
                    if secondary_gsv in self.secondary_gsv_data:
                        for value in self.secondary_gsv_data[secondary_gsv]:
                            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                            tree_item.setCheckState(column_index, QtCore.Qt.Unchecked)
                            
                            # Store metadata for secondary columns
                            tree_item.setData(column_index, QtCore.Qt.UserRole, {
                                'secondary_gsv': secondary_gsv,
                                'secondary_value': value,
                                'is_primary': False
                            })
                            column_index += 1
                
                # Add to parent or root
                if parent_item:
                    parent_item.addChild(tree_item)
                else:
                    self.gsvs_tree.addTopLevelItem(tree_item)
                
                # Recursively build child levels
                self._build_tree_level(item_data, tree_item, level_index + 1)
    
    def _on_tree_item_changed(self, item, column):
        """Handle tree item checkbox state changes.
        
        Args:
            item (QTreeWidgetItem): The item that changed
            column (int): Column index that changed
        """
        # Get item metadata
        item_data = item.data(column, QtCore.Qt.UserRole)
        if not item_data:
            return
        
        # Block signals to prevent recursion
        self.gsvs_tree.blockSignals(True)
        
        try:
            # Get the new check state
            check_state = item.checkState(column)
            
            if column == 0:
                # Handle primary GSV column (column 0)
                level = item_data.get('level', 'Unknown')
                value = item_data.get('value', 'Unknown')
                checked = check_state == QtCore.Qt.Checked
                
                # Update all children for primary column
                self._update_children_primary_gsv(item, check_state)
                
                # Update parent state for primary column
                self._update_parent_primary_gsv(item)
                
                logger.info(f"Primary GSV {level}:{value} = {checked}")
                
            else:
                # Handle secondary GSV column changes
                if not item_data.get('is_primary', True):
                    secondary_gsv = item_data.get('secondary_gsv')
                    secondary_value = item_data.get('secondary_value')
                    
                    # Update all children with the same secondary GSV column
                    self._update_children_secondary_gsv(item, column, check_state)
                    
                    # Update parent state for this column
                    self._update_parent_secondary_gsv(item, column)
                    
                    # Log the change
                    primary_data = item.data(0, QtCore.Qt.UserRole)
                    primary_value = primary_data.get('value', 'Unknown') if primary_data else 'Unknown'
                    checked = check_state == QtCore.Qt.Checked
                    logger.info(f"GSV {primary_value}.{secondary_gsv}:{secondary_value} = {checked}")
        
        finally:
            # Re-enable signals
            self.gsvs_tree.blockSignals(False)
    
    def _update_children_primary_gsv(self, parent_item, check_state):
        """Update all children of an item for the primary GSV column (column 0).
        
        Args:
            parent_item (QTreeWidgetItem): Parent item
            check_state (Qt.CheckState): New check state
        """
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(0, check_state)
            # Recursively update grandchildren
            self._update_children_primary_gsv(child, check_state)
    
    def _update_parent_primary_gsv(self, child_item):
        """Update parent check state for the primary GSV column (column 0).
        
        Args:
            child_item (QTreeWidgetItem): Child item that was changed
        """
        parent = child_item.parent()
        if not parent:
            return
        
        # Count checked and unchecked children for column 0
        total_children = parent.childCount()
        checked_children = 0
        
        for i in range(total_children):
            child = parent.child(i)
            if child.checkState(0) == QtCore.Qt.Checked:
                checked_children += 1
        
        # Set parent state based on children
        if checked_children == 0:
            parent.setCheckState(0, QtCore.Qt.Unchecked)
        elif checked_children == total_children:
            parent.setCheckState(0, QtCore.Qt.Checked)
        else:
            parent.setCheckState(0, QtCore.Qt.PartiallyChecked)
        
        # Recursively update grandparent
        self._update_parent_primary_gsv(parent)
    
    def _update_children_secondary_gsv(self, parent_item, column, check_state):
        """Update all children of an item for a specific secondary GSV column.
        
        Args:
            parent_item (QTreeWidgetItem): Parent item
            column (int): Column index
            check_state (Qt.CheckState): New check state
        """
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(column, check_state)
            # Recursively update grandchildren
            self._update_children_secondary_gsv(child, column, check_state)
    
    def _update_parent_secondary_gsv(self, child_item, column):
        """Update parent check state for a specific secondary GSV column.
        
        Args:
            child_item (QTreeWidgetItem): Child item that was changed
            column (int): Column index
        """
        parent = child_item.parent()
        if not parent:
            return
        
        # Count checked and unchecked children for this column
        total_children = parent.childCount()
        checked_children = 0
        
        for i in range(total_children):
            child = parent.child(i)
            if child.checkState(column) == QtCore.Qt.Checked:
                checked_children += 1
        
        # Set parent state based on children
        if checked_children == 0:
            parent.setCheckState(column, QtCore.Qt.Unchecked)
        elif checked_children == total_children:
            parent.setCheckState(column, QtCore.Qt.Checked)
        else:
            parent.setCheckState(column, QtCore.Qt.PartiallyChecked)
        
        # Recursively update grandparent
        self._update_parent_secondary_gsv(parent, column)
    
    def _check_all_items(self):
        """Check all items in all columns."""
        self.gsvs_tree.blockSignals(True)
        try:
            self._set_all_items_check_state(QtCore.Qt.Checked)
        finally:
            self.gsvs_tree.blockSignals(False)
    
    def _uncheck_all_items(self):
        """Uncheck all items in all columns."""
        self.gsvs_tree.blockSignals(True)
        try:
            self._set_all_items_check_state(QtCore.Qt.Unchecked)
        finally:
            self.gsvs_tree.blockSignals(False)
    
    def _set_all_items_check_state(self, check_state):
        """Set check state for all items in all columns.
        
        Args:
            check_state (Qt.CheckState): State to set all items to
        """
        # Iterate through all top-level items
        for i in range(self.gsvs_tree.topLevelItemCount()):
            item = self.gsvs_tree.topLevelItem(i)
            self._set_item_and_children_check_state(item, check_state)
    
    def _set_item_and_children_check_state(self, item, check_state):
        """Recursively set check state for an item and all its children in all columns.
        
        Args:
            item (QTreeWidgetItem): Item to update
            check_state (Qt.CheckState): State to set
        """
        # Set check state for all columns (including primary column 0)
        for column in range(self.gsvs_tree.columnCount()):
            item.setCheckState(column, check_state)
        
        # Recursively update children
        for i in range(item.childCount()):
            child = item.child(i)
            self._set_item_and_children_check_state(child, check_state)
    
    def _get_selected_gsvs(self):
        """Get the currently selected GSV values.
        
        Returns:
            dict: Dictionary with primary GSV paths and their selected secondary GSVs
        """
        selected_gsvs = {}
        
        # Iterate through all items and collect checked secondary GSVs
        self._collect_checked_secondary_gsvs(selected_gsvs)
        
        return selected_gsvs
    
    def _collect_checked_secondary_gsvs(self, result_dict, parent_item=None):
        """Recursively collect checked secondary GSVs from the tree.
        
        Args:
            result_dict (dict): Dictionary to store results
            parent_item (QTreeWidgetItem): Parent item (None for root level)
        """
        if parent_item is None:
            # Start with top-level items
            for i in range(self.gsvs_tree.topLevelItemCount()):
                item = self.gsvs_tree.topLevelItem(i)
                self._collect_item_secondary_gsvs(item, result_dict)
                # Check children
                self._collect_checked_secondary_gsvs(result_dict, item)
        else:
            # Check children of current item
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                self._collect_item_secondary_gsvs(child, result_dict)
                # Check grandchildren
                self._collect_checked_secondary_gsvs(result_dict, child)
    
    def _collect_item_secondary_gsvs(self, item, result_dict):
        """Collect checked primary and secondary GSVs for a specific item.
        
        Args:
            item (QTreeWidgetItem): Tree item to check
            result_dict (dict): Dictionary to store results
        """
        # Build the primary GSV path for this item
        path_parts = []
        current_item = item
        while current_item:
            primary_data = current_item.data(0, QtCore.Qt.UserRole)
            if primary_data and primary_data.get('is_primary'):
                path_parts.insert(0, f"{primary_data.get('level')}:{primary_data.get('value')}")
            current_item = current_item.parent()
        
        path_key = "/".join(path_parts)
        
        # Check if this item has any selections (primary or secondary)
        has_selections = False
        checked_data = {}
        
        # Check primary GSV (column 0)
        if item.checkState(0) == QtCore.Qt.Checked:
            primary_data = item.data(0, QtCore.Qt.UserRole)
            if primary_data and primary_data.get('is_primary'):
                level = primary_data.get('level')
                value = primary_data.get('value')
                if level and value:
                    checked_data['primary'] = f"{level}:{value}"
                    has_selections = True
        
        # Check all secondary GSV columns for this item
        checked_secondary = {}
        for column in range(1, self.gsvs_tree.columnCount()):
            if item.checkState(column) == QtCore.Qt.Checked:
                column_data = item.data(column, QtCore.Qt.UserRole)
                if column_data:
                    secondary_gsv = column_data.get('secondary_gsv')
                    secondary_value = column_data.get('secondary_value')
                    if secondary_gsv and secondary_value:
                        if secondary_gsv not in checked_secondary:
                            checked_secondary[secondary_gsv] = []
                        checked_secondary[secondary_gsv].append(secondary_value)
                        has_selections = True
        
        if checked_secondary:
            checked_data['secondary'] = checked_secondary
        
        if has_selections:
            result_dict[path_key] = checked_data

    def _get_effective_table_values(self):
        """Get effective values from the table, using master row as fallback for blank cells.
        
        Returns:
            List of dictionaries, one per data row (excluding master row).
            Each dict contains the effective values for that row.
        """
        if not hasattr(self, 'render_table') or self.render_table.rowCount() < 2:
            return []
        
        # Get master row values (row 0)
        master_values = {}
        headers = ["Order", "Node", "Filename", "Chunk", "Frames", "Priority", "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", "NukeX", "BatchMode", "Reloadplugin"]
        
        for col, header in enumerate(headers):
            master_item = self.render_table.item(0, col)
            master_values[header] = master_item.text() if master_item else ""
        
        # Process each data row (starting from row 1)
        effective_values = []
        for row in range(1, self.render_table.rowCount()):
            row_values = {}
            
            for col, header in enumerate(headers):
                cell_item = self.render_table.item(row, col)
                cell_value = cell_item.text().strip() if cell_item else ""
                
                # Use cell value if not blank, otherwise fallback to master value
                if cell_value:
                    row_values[header] = cell_value
                else:
                    row_values[header] = master_values[header]
            
            effective_values.append(row_values)
        
        return effective_values

    def _create_console_tab(self):
        """Create the Console tab for output."""
        console_widget = QtWidgets.QWidget()
        console_layout = QtWidgets.QVBoxLayout()
        console_widget.setLayout(console_layout)
        
        # Console output area
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #2b2b2b; color: #ffffff; font-family: 'Courier New';")
        self.console_output.setText("Ready for submission...\nLatest submission: 2023-10-28 11:10:46")
        
        console_layout.addWidget(self.console_output)
        
        # Add console tab
        self.tab_widget.addTab(console_widget, "Console")
    
    def _create_extra_settings_tab(self):
        """Create the Extra Settings tab with Job Name, Comment, and Department."""
        extra_settings_widget = QtWidgets.QWidget()
        extra_settings_layout = QtWidgets.QVBoxLayout()
        extra_settings_layout.setContentsMargins(15, 15, 15, 15)  # Add padding
        extra_settings_layout.setSpacing(10)  # Add spacing between elements
        extra_settings_widget.setLayout(extra_settings_layout)
        
        # Job Information section
        job_info_group = QtWidgets.QGroupBox("Job Information")
        job_info_layout = QtWidgets.QGridLayout()
        job_info_layout.setSpacing(8)
        job_info_group.setLayout(job_info_layout)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Job Name:"), 0, 0)
        self.job_name_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.job_name_edit, 0, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Comment:"), 1, 0)
        self.comment_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.comment_edit, 1, 1)
        
        job_info_layout.addWidget(QtWidgets.QLabel("Department:"), 2, 0)
        self.department_edit = QtWidgets.QLineEdit()
        job_info_layout.addWidget(self.department_edit, 2, 1)
        
        extra_settings_layout.addWidget(job_info_group)
        
        # Add stretch to push content to top
        extra_settings_layout.addStretch()
        
        # Add extra settings tab
        self.tab_widget.addTab(extra_settings_widget, "Extra Settings")
    
    def _create_bottom_controls(self):
        """Create the bottom controls with version text, progress bar and render button."""
        bottom_layout = QtWidgets.QHBoxLayout()
        
        # Version label on the left
        version_label = QtWidgets.QLabel("NK2DL Submitter v0.1-alpha")
        version_label.setStyleSheet("color: #888888; font-size: 10px;")
        bottom_layout.addWidget(version_label)
        
        # Add stretch to push progress bar and render button to the right
        bottom_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        bottom_layout.addWidget(self.progress_bar)
        
        # Render button
        self.render_btn = QtWidgets.QPushButton("Render")
        self.render_btn.setStyleSheet("QPushButton { background-color: #4a90e2; color: white; font-weight: bold; }")
        self.render_btn.clicked.connect(self._on_render_clicked)
        bottom_layout.addWidget(self.render_btn)
        
        self.layout().addLayout(bottom_layout)
    
    def _on_render_clicked(self):
        """Handle render button click - demonstrate the effective values system."""
        # Get effective values to demonstrate the fallback system
        effective_values = self._get_effective_table_values()
        
        # Create a demo message showing how values are resolved
        demo_message = "Effective Values (Master Fallback System):\n\n"
        
        for i, row_values in enumerate(effective_values, 1):
            demo_message += f"Row {i} ({row_values['Node']}):\n"
            for key, value in row_values.items():
                if key not in ['Node', 'Filename']:  # Skip non-configurable fields
                    demo_message += f"  {key}: {value}\n"
            demo_message += "\n"
        
        demo_message += "\nNote: Blank cells use master row values.\nFilled cells use their own values."
        
        if NUKE_AVAILABLE:
            nuke.message(demo_message)
        else:
            print(demo_message)

    def _on_update_clicked(self):
        """Handle update button click - show development message."""
        if NUKE_AVAILABLE:
            nuke.message('Nuke to Deadline panel is in development and not ready for production use.\n\nUse the "Submit Selected Writes to Deadline" option from the Render menu.')
        else:
            print("Nuke to Deadline panel is in development, Use the 'Submit Selected Writes to Deadline' options from the Render menu")

    def _on_all_clicked(self):
        """Handle all button click - show development message."""
        if NUKE_AVAILABLE:
            nuke.message('Nuke to Deadline panel is in development and not ready for production use.\n\nUse the "Submit Selected Writes to Deadline" option from the Render menu.')
        else:
            print("Nuke to Deadline panel is in development, Use the 'Submit Selected Writes to Deadline' options from the Render menu")

    def _on_clear_clicked(self):
        """Handle clear button click - show development message."""
        if NUKE_AVAILABLE:
            nuke.message('Nuke to Deadline panel is in development and not ready for production use.\n\nUse the "Submit Selected Writes to Deadline" option from the Render menu.')
        else:
            print("Nuke to Deadline panel is in development, Use the 'Submit Selected Writes to Deadline' options from the Render menu")

    def _on_selection_clicked(self):
        """Handle selection button click - show development message."""
        if NUKE_AVAILABLE:
            nuke.message('Nuke to Deadline panel is in development and not ready for production use.\n\nUse the "Submit Selected Writes to Deadline" option from the Render menu.')
        else:
            print("Nuke to Deadline panel is in development, Use the 'Submit Selected Writes to Deadline' options from the Render menu")

    def _on_master_row_changed(self, item):
        """Handle master row change - refresh placeholders."""
        # Only refresh if the master row (row 0) was changed
        if item and item.row() == 0:
            self.render_table.viewport().update()


def register_panel():
    """Create and register the dockable nk2dl panel.
    
    This function registers the nk2dl panel as a dockable PySide widget in Nuke.
    Uses PySide6 for Nuke 16+ and PySide2 for earlier versions.
    Users can access it from the Pane menu.

    Returns:
        True or None: True if panel was registered, or None if Nuke is not available.
    """
    if not NUKE_AVAILABLE:
        logger.warning("Nuke not available, skipping panel creation")
        return None
    
    try:
        # Following the KnobScripter pattern - register in same module as widget class
        # Make the class available in nuke namespace
        nuke.Nk2dlPanel = Nk2dlPanel
        
        # Register the PySide widget as a dockable panel
        nuke.nk2dlPane = panels.registerWidgetAsPanel(
            'nuke.Nk2dlPanel',                  # Class reference in nuke namespace
            'Nuke to Deadline',                 # Display name in Pane menu
            'com.danielharkness.nk2dl.panel'    # Unique ID for layout saving
        )
        
        logger.info(f"nk2dl dockable panel registered successfully using {PYSIDE_VERSION} for Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register nk2dl panel: {str(e)}")
        return None