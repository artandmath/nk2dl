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

from .constants import Colors, TableColumns


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


class PinnedRowTableWidget(QtWidgets.QTableWidget):
    """Custom QTableWidget that supports pinned rows at the top."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pinned_row_count = 0
        self.original_sort_enabled = True
        self.current_sort_column = -1
        self.current_sort_order = QtCore.Qt.AscendingOrder
        self._sorting_in_progress = False
        
        if NUKE_AVAILABLE:
            nuke.tprint("PinnedRowTableWidget created")
        else:
            print("PinnedRowTableWidget created")
        
        # Connect to header clicks to ensure our custom sorting is used
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
    def setPinnedRowCount(self, count):
        """Set the number of rows that should be pinned at the top."""
        if NUKE_AVAILABLE:
            nuke.tprint(f"setPinnedRowCount called with count={count}")
        else:
            print(f"setPinnedRowCount called with count={count}")
        
        self.pinned_row_count = count
        
        # Reconfigure sorting behavior based on pinned row count
        if count > 0:
            if NUKE_AVAILABLE:
                nuke.tprint(f"Setting up custom sorting for {count} pinned rows")
            else:
                print(f"Setting up custom sorting for {count} pinned rows")
            
            # Completely disable Qt's built-in sorting
            super().setSortingEnabled(False)
            
            # Disconnect all existing header signals to avoid conflicts
            try:
                self.horizontalHeader().sectionClicked.disconnect()
            except:
                pass
            
            # Make header clickable and connect our custom handler
            self.horizontalHeader().setSectionsClickable(True)
            self.horizontalHeader().setSortIndicatorShown(True)
            self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
            
            if NUKE_AVAILABLE:
                nuke.tprint("Custom header click handler connected")
            else:
                print("Custom header click handler connected")
        else:
            # Re-enable normal sorting if no pinned rows
            super().setSortingEnabled(self.original_sort_enabled)
    
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
        from .constants import TableColumns
        
        # Define the blue group columns (3-12: Chunk through Reloadplugin)
        blue_group_start_col = 3
        blue_group_end_col = 12
        
        # Define the purple group columns (machine settings)
        purple_group_start_col = min(TableColumns.MACHINE_SETTINGS_COLUMNS)
        purple_group_end_col = max(TableColumns.MACHINE_SETTINGS_COLUMNS)
        
        # Draw blue group border
        self._draw_group_border(painter, row, blue_group_start_col, blue_group_end_col, 'blue')
        
        # Draw purple group border
        self._draw_group_border(painter, row, purple_group_start_col, purple_group_end_col, 'purple')
    
    def _draw_group_border(self, painter, row, group_start_col, group_end_col, border_group):
        """Draw a specific group border."""
        # Check if we have enough columns
        if self.columnCount() <= group_end_col:
            return
        
        # Check if any cell in the group has border data
        has_border_group = False
        border_color = None
        for col in range(group_start_col, group_end_col + 1):
            item = self.item(row, col)
            if item:
                border_data = item.data(QtCore.Qt.UserRole + 1)
                if border_data and border_data.get('border_group') == border_group:
                    has_border_group = True
                    border_color = border_data.get('border_color', QtGui.QColor("#4A90E2"))
                    break
        
        if not has_border_group or not border_color:
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
        
        # Save current painter state
        painter.save()
        
        # Set up the pen for this group border
        pen = QtGui.QPen(border_color, 3)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        
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
        
        # Restore painter state
        painter.restore()
    
    def sortByColumn(self, column, order):
        """Override sorting to exclude pinned rows."""
        if NUKE_AVAILABLE:
            nuke.tprint(f"sortByColumn called: column {column}, order {'DESC' if order == QtCore.Qt.DescendingOrder else 'ASC'}")
        else:
            print(f"sortByColumn called: column {column}, order {'DESC' if order == QtCore.Qt.DescendingOrder else 'ASC'}")
        
        # Prevent recursion during sorting
        if self._sorting_in_progress:
            return
        
        if self.pinned_row_count == 0:
            super().sortByColumn(column, order)
            return
        
        # Set flag to prevent recursion
        self._sorting_in_progress = True
        
        try:
            if NUKE_AVAILABLE:
                nuke.tprint("Starting sort process...")
            else:
                print("Starting sort process...")
            
            # Get all row data as (index, data) tuples
            row_data = []
            for row in range(self.rowCount()):
                row_items = []
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    row_items.append(item.text() if item else "")
                row_data.append((row, row_items))
            
            if NUKE_AVAILABLE:
                nuke.tprint(f"Total rows: {len(row_data)}, Pinned: {self.pinned_row_count}")
            else:
                print(f"Total rows: {len(row_data)}, Pinned: {self.pinned_row_count}")
            
            # Separate pinned and non-pinned rows
            pinned_rows = row_data[:self.pinned_row_count]
            non_pinned_rows = row_data[self.pinned_row_count:]
            
            # Show before sort
            if non_pinned_rows:
                if NUKE_AVAILABLE:
                    nuke.tprint(f"Before sort - first non-pinned row col {column}: '{non_pinned_rows[0][1][column] if column < len(non_pinned_rows[0][1]) else 'N/A'}'")
                else:
                    print(f"Before sort - first non-pinned row col {column}: '{non_pinned_rows[0][1][column] if column < len(non_pinned_rows[0][1]) else 'N/A'}'")
            
            # Sort non-pinned rows by the specified column
            def sort_key(row_tuple):
                _, row_items = row_tuple
                if column >= len(row_items):
                    return ""
                text = row_items[column]
                # Try numeric sort first
                try:
                    return float(text) if text.strip() else 0.0
                except ValueError:
                    return text.lower()
            
            if NUKE_AVAILABLE:
                nuke.tprint("About to sort...")
            else:
                print("About to sort...")
            
            non_pinned_rows.sort(key=sort_key, reverse=(order == QtCore.Qt.DescendingOrder))
            
            if NUKE_AVAILABLE:
                nuke.tprint("Sort completed, now updating table...")
            else:
                print("Sort completed, now updating table...")
            
            # Show after sort
            if non_pinned_rows:
                if NUKE_AVAILABLE:
                    nuke.tprint(f"After sort - first non-pinned row col {column}: '{non_pinned_rows[0][1][column] if column < len(non_pinned_rows[0][1]) else 'N/A'}'")
                else:
                    print(f"After sort - first non-pinned row col {column}: '{non_pinned_rows[0][1][column] if column < len(non_pinned_rows[0][1]) else 'N/A'}'")
            
            # Rebuild the table: pinned rows first, then sorted non-pinned rows
            all_sorted_rows = pinned_rows + non_pinned_rows
            
            # Clear and rebuild table data
            self.blockSignals(True)
            
            if NUKE_AVAILABLE:
                nuke.tprint("Updating table items...")
            else:
                print("Updating table items...")
            
            # Update each row with sorted data
            for new_row, (original_row, row_items) in enumerate(all_sorted_rows):
                for col, text in enumerate(row_items):
                    item = QtWidgets.QTableWidgetItem(text)
                    self.setItem(new_row, col, item)
            
            self.blockSignals(False)
            
            if NUKE_AVAILABLE:
                nuke.tprint("About to apply pinned row styling...")
            else:
                print("About to apply pinned row styling...")
            
        except Exception as e:
            if NUKE_AVAILABLE:
                nuke.tprint(f"ERROR in sortByColumn: {str(e)}")
                import traceback
                nuke.tprint(f"Traceback: {traceback.format_exc()}")
            else:
                print(f"ERROR in sortByColumn: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
        finally:
            self._sorting_in_progress = False
        
        # Reapply pinned row styling
        try:
            self._style_pinned_rows()
            if NUKE_AVAILABLE:
                nuke.tprint("Sort process fully completed")
            else:
                print("Sort process fully completed")
        except Exception as e:
            if NUKE_AVAILABLE:
                nuke.tprint(f"ERROR in _style_pinned_rows: {str(e)}")
            else:
                print(f"ERROR in _style_pinned_rows: {str(e)}")
    
    def _style_pinned_rows(self):
        """Apply different styling to pinned rows with blue borders and default backgrounds."""
        # Use consistent color constants for both settings panels and pinned rows
        job_settings_blue = QtGui.QColor(Colors.PINNED_JOB_BORDER)
        job_settings_bg = QtGui.QColor(Colors.PINNED_JOB_BACKGROUND)
        machine_settings_purple = QtGui.QColor(Colors.PINNED_MACHINE_BORDER)
        machine_settings_bg = QtGui.QColor(Colors.PINNED_MACHINE_BACKGROUND)
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
                        # Define which columns belong to the machine settings group (columns 13-24)
                        elif col in TableColumns.MACHINE_SETTINGS_COLUMNS:  # Machine settings columns
                            # Use Machine Settings background color for machine settings cells
                            item.setBackground(QtGui.QBrush(machine_settings_bg))
                            item.setForeground(QtGui.QBrush())  # Default text color
                            
                            item.setData(QtCore.Qt.UserRole + 1, {
                                'border_group': 'purple',
                                'border_color': machine_settings_purple,
                                'group_start_col': min(TableColumns.MACHINE_SETTINGS_COLUMNS),
                                'group_end_col': max(TableColumns.MACHINE_SETTINGS_COLUMNS)
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
        """Override to track original sorting state and disable Qt's built-in sorting for pinned rows."""
        if NUKE_AVAILABLE:
            nuke.tprint(f"setSortingEnabled called: enabled={enabled}, pinned_count={self.pinned_row_count}")
        else:
            print(f"setSortingEnabled called: enabled={enabled}, pinned_count={self.pinned_row_count}")
        
        self.original_sort_enabled = enabled
        
        if self.pinned_row_count > 0:
            if NUKE_AVAILABLE:
                nuke.tprint("Using custom sorting due to pinned rows")
            else:
                print("Using custom sorting due to pinned rows")
            # Force custom sorting when we have pinned rows
            super().setSortingEnabled(False)
            self.horizontalHeader().setSectionsClickable(True)
            self.horizontalHeader().setSortIndicatorShown(True)
            
            # Ensure our handler is connected
            try:
                self.horizontalHeader().sectionClicked.disconnect()
            except:
                pass
            self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        else:
            if NUKE_AVAILABLE:
                nuke.tprint("Using normal Qt sorting")
            else:
                print("Using normal Qt sorting")
            # Normal behavior when no pinned rows
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

    def _on_header_clicked(self, logical_index):
        """Handle header clicks to trigger custom sorting."""
        if NUKE_AVAILABLE:
            nuke.tprint(f"Header clicked: column {logical_index}")
        else:
            print(f"Header clicked: column {logical_index}")
        
        # Prevent recursion during sorting
        if self._sorting_in_progress:
            return
        
        if self.pinned_row_count == 0:
            # No pinned rows, use default sorting
            return
        
        if NUKE_AVAILABLE:
            nuke.tprint(f"Processing sort for column {logical_index}")
        else:
            print(f"Processing sort for column {logical_index}")
        
        # Determine sort order - toggle if same column, otherwise ascending
        if logical_index == self.current_sort_column:
            # Same column - toggle order
            if self.current_sort_order == QtCore.Qt.AscendingOrder:
                new_order = QtCore.Qt.DescendingOrder
            else:
                new_order = QtCore.Qt.AscendingOrder
        else:
            # Different column - start with ascending
            new_order = QtCore.Qt.AscendingOrder
        
        # Update tracking variables
        self.current_sort_column = logical_index
        self.current_sort_order = new_order
        
        # Call our custom sort method (don't set flag here, let sortByColumn handle it)
        self.sortByColumn(logical_index, new_order)
        
        # Update the header visual indicator
        self.horizontalHeader().setSortIndicator(logical_index, new_order)


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