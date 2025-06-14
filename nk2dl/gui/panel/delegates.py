# -*- coding: utf-8 -*-
"""Custom Qt item delegates for the nk2dl panel.

This module contains all custom delegate classes used for rendering and editing
items in the nk2dl panel interface.
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