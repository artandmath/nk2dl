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


class CenteredCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate that centers checkboxes in tree widget columns."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Paint the item with centered checkbox."""
        # Get the data value
        value = index.data(QtCore.Qt.CheckStateRole)
        
        if value is not None:
            # Calculate the checkbox rect
            checkbox_style = QtWidgets.QApplication.style()
            checkbox_rect = checkbox_style.subElementRect(
                QtWidgets.QStyle.SE_CheckBoxIndicator, 
                option
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