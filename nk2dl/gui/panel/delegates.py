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

from .constants import HeaderSettingsMapping, Sizes


# ============================================================================
# Settings and Inheritance Delegates
# ============================================================================

class SettingsAwareDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate that handles settings inheritance and override styling.
    
    This delegate provides:
    - Bold text styling for cells with override values
    - Enhanced dropdown menus with inheritance options
    - Proper handling of inheritance vs explicit values
    """
    
    def __init__(self, table_model, parent=None):
        super().__init__(parent)
        self.table_model = table_model
    
    def paint(self, painter, option, index):
        """Paint cell with highlight color background for overridden values."""
        # Check if cell is overridden
        if self.table_model.is_cell_overridden(index.row(), index.column()):
            # Create new option with highlight color background for override values
            new_option = QtWidgets.QStyleOptionViewItem(option)
            # Set background color to match other highlightable widgets
            from .constants import Colors
            new_option.backgroundBrush = QtGui.QBrush(QtGui.QColor(Colors.WIDGET_HIGHLIGHT_COLOR))
            super().paint(painter, new_option, index)
        else:
            # Use normal styling for inherited values
            super().paint(painter, option, index)
    
    def displayText(self, value, locale):
        """Display effective value (explicit or inherited)."""
        # The view should already be showing effective values
        return super().displayText(value, locale)
    
    def createEditor(self, parent, option, index):
        """Create editor with inheritance options for dropdown columns."""
        column = index.column()
        
        if not self.table_model.is_dropdown_column(column):
            # Use default editor for non-dropdown columns
            return super().createEditor(parent, option, index)
        
        # Create dropdown editor with inheritance options
        editor = QtWidgets.QComboBox(parent)
        editor.setEditable(False)
        
        # Populate dropdown based on column type
        self._populate_dropdown_editor(editor, column)
        
        return editor
    
    def _populate_dropdown_editor(self, editor, column):
        """Populate dropdown editor with options and inheritance choice."""
        headers = self.table_model.get_headers()
        if column >= len(headers):
            return
        
        header = headers[column]
        setting_type, setting_key = self.table_model.get_setting_for_column(column)
        
        # Add standard options first based on column type
        if header in HeaderSettingsMapping.BOOLEAN_COLUMNS:
            # Yes/No columns
            editor.addItems(["Yes", "No"])
        elif header == "RenderMode":
            editor.addItems(["Full", "Proxy", "Both", "Script"])
        elif header == "Pool":
            from .constants import Settings
            editor.addItems(Settings.get_pool_options())
        elif header == "SecondaryPool":
            from .constants import Settings
            editor.addItems([""] + Settings.get_pool_options())
        elif header == "Group":
            from .constants import Settings
            editor.addItems(Settings.get_group_options())
        else:
            # For other dropdown columns, use default options
            # This handles any columns defined in TableColumns.get_dropdown_columns()
            from .constants import TableColumns
            dropdown_columns = TableColumns.get_dropdown_columns()
            if column in dropdown_columns:
                options = dropdown_columns[column]
                editor.addItems(options)
        
        # Add separator and inheritance option if column has settings mapping
        if setting_type:
            editor.insertSeparator(editor.count())
            inheritance_label = HeaderSettingsMapping.get_inheritance_label(header)
            if inheritance_label:
                editor.addItem(inheritance_label)
    
    def setEditorData(self, editor, index):
        """Set editor data with current effective value."""
        if isinstance(editor, QtWidgets.QComboBox):
            # Get current effective value for display
            current_value = self.table_model.get_effective_cell_value(
                index.row(), index.column())
            
            # Check if this is an inherited value by looking at raw value
            raw_value = self.table_model.get_cell_value(
                index.row(), index.column())
            
            if raw_value is None:
                # Cell is inheriting - select inheritance option
                headers = self.table_model.get_headers()
                if index.column() < len(headers):
                    header = headers[index.column()]
                    inheritance_label = HeaderSettingsMapping.get_inheritance_label(header)
                    if inheritance_label:
                        inheritance_index = editor.findText(inheritance_label)
                        if inheritance_index >= 0:
                            editor.setCurrentIndex(inheritance_index)
                            return
            
            # Find and select the current effective value
            index_to_select = editor.findText(current_value)
            if index_to_select >= 0:
                editor.setCurrentIndex(index_to_select)
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        """Set model data from editor, handling inheritance."""
        if isinstance(editor, QtWidgets.QComboBox):
            selected_text = editor.currentText()
            
            # Check if inheritance option was selected
            headers = self.table_model.get_headers()
            if index.column() < len(headers):
                header = headers[index.column()]
                inheritance_label = HeaderSettingsMapping.get_inheritance_label(header)
                
                if selected_text == inheritance_label:
                    # Set None to use inheritance
                    self.table_model.set_cell_value(index.row(), index.column(), None)
                else:
                    # Set explicit value
                    self.table_model.set_cell_value(index.row(), index.column(), selected_text)
        else:
            super().setModelData(editor, model, index)


# ============================================================================
# Checkbox Delegates
# ============================================================================

class CenteredCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate that centers checkboxes in tree widget columns."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Paint the item with centered checkbox."""
        # Get the data value
        value = index.data(QtCore.Qt.CheckStateRole)
        
        if value is not None:
            # For primary column (column 0), use default painting
            # Qt will automatically draw the checkbox since we set ItemIsUserCheckable
            if index.column() == 0:
                # Just use the default painting - Qt handles the checkbox
                super().paint(painter, option, index)
                return
            else:
                # For secondary columns (1+), draw centered checkbox
                checkbox_style = QtWidgets.QApplication.style()
                checkbox_rect = checkbox_style.subElementRect(
                    QtWidgets.QStyle.SE_CheckBoxIndicator, 
                    option,
                    None  # widget parameter - can be None for basic checkbox rendering
                )
                
                # Center the checkbox within the cell
                center_x = option.rect.center().x() - checkbox_rect.width() // 2
                center_y = option.rect.center().y() - checkbox_rect.height() // 2
                checkbox_rect.moveTopLeft(QtCore.QPoint(center_x, center_y))
            
            # Create style option for checkbox
            checkbox_option = QtWidgets.QStyleOptionButton()
            checkbox_option.rect = checkbox_rect
            checkbox_option.state = option.state | QtWidgets.QStyle.State_Enabled
            
            # Set checkbox state based on data value
            if value == QtCore.Qt.Checked:
                checkbox_option.state |= QtWidgets.QStyle.State_On
            else:
                checkbox_option.state |= QtWidgets.QStyle.State_Off
            
            # Draw the checkbox
            checkbox_style.drawControl(QtWidgets.QStyle.CE_CheckBox, checkbox_option, painter)
        else:
            # No checkbox data, paint normally
            super().paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse events for toggling checkbox."""
        if (event.type() == QtCore.QEvent.MouseButtonRelease and
            event.button() == QtCore.Qt.LeftButton):
            
            # Toggle the checkbox state
            current_value = index.data(QtCore.Qt.CheckStateRole)
            new_value = QtCore.Qt.Unchecked if current_value == QtCore.Qt.Checked else QtCore.Qt.Checked
            return model.setData(index, new_value, QtCore.Qt.CheckStateRole)
        
        return super().editorEvent(event, model, option, index)


class TableCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate for checkbox columns in table widgets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Paint checkbox centered in table cell."""
        value = index.data(QtCore.Qt.CheckStateRole)
        
        if value is not None and index.column() == 0:  # Render column
            # Use Qt's default checkbox rendering for table widgets
            # Qt automatically centers checkboxes when ItemIsUserCheckable is set
            super().paint(painter, option, index)
        else:
            # Normal cell rendering for non-checkbox columns
            super().paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse events for toggling checkbox."""
        if (index.column() == 0 and  # Render column
            event.type() == QtCore.QEvent.MouseButtonRelease and
            event.button() == QtCore.Qt.LeftButton):
            
            # Toggle checkbox state
            current_value = index.data(QtCore.Qt.CheckStateRole)
            new_value = QtCore.Qt.Unchecked if current_value == QtCore.Qt.Checked else QtCore.Qt.Checked
            return model.setData(index, new_value, QtCore.Qt.CheckStateRole)
        
        return super().editorEvent(event, model, option, index)


# ============================================================================
# Combined Delegates
# ============================================================================

class CombinedTableDelegate(QtWidgets.QStyledItemDelegate):
    """Combined delegate handling both checkboxes and settings inheritance."""
    
    def __init__(self, table_model, parent=None):
        super().__init__(parent)
        self.table_model = table_model
        self.checkbox_delegate = TableCheckboxDelegate()
        self.settings_delegate = SettingsAwareDelegate(table_model)
    
    def paint(self, painter, option, index):
        if index.column() == 0:  # Render column
            self.checkbox_delegate.paint(painter, option, index)
        else:
            self.settings_delegate.paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        if index.column() == 0:  # Render column
            return self.checkbox_delegate.editorEvent(event, model, option, index)
        else:
            return self.settings_delegate.editorEvent(event, model, option, index)
    
    def createEditor(self, parent, option, index):
        if index.column() == 0:  # Render column
            return None  # No editor needed for checkbox
        else:
            return self.settings_delegate.createEditor(parent, option, index)
    
    def setEditorData(self, editor, index):
        if index.column() == 0:  # Render column
            return  # No editor for checkbox
        else:
            return self.settings_delegate.setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        if index.column() == 0:  # Render column
            return  # No editor for checkbox
        else:
            return self.settings_delegate.setModelData(editor, model, index) 