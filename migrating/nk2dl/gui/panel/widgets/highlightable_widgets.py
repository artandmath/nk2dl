# -*- coding: utf-8 -*-
"""Highlightable widget classes for the nk2dl panel.

This module contains custom Qt widgets that can display background highlights
when they have stored values, indicating to users which settings have been
persisted to storage.
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

from ..constants import Colors
from ....common.logging import setup_logging

logger = setup_logging('nk2dl.gui.panel.widgets.highlightable_widgets')


class HighlightableCheckBox(QtWidgets.QCheckBox):
    """A checkbox widget that can display a highlight color when it has stored values."""
    
    def __init__(self, text="", parent=None, highlight_color=Colors.WIDGET_HIGHLIGHT_COLOR):
        super().__init__(text, parent)
        self.highlight_color = QtGui.QColor(highlight_color)
        self.is_highlighted = False
        self.original_palette = self.palette()
        # Don't enable auto fill background - let it be transparent
        self.setAutoFillBackground(False)
    
    def set_highlight_color(self, color):
        """Set the highlight color for this widget.
        
        Args:
            color (str): The highlight color in hex format (e.g., "#547699")
        """
        self.highlight_color = QtGui.QColor(color)
        if self.is_highlighted:
            self._apply_highlight()
    
    def set_highlighted(self, highlighted):
        """Set whether this widget should be highlighted.
        
        Args:
            highlighted (bool): True to highlight, False to remove highlight
        """
        self.is_highlighted = highlighted
        if highlighted:
            self._apply_highlight()
        else:
            self._remove_highlight()
    
    def _apply_highlight(self):
        """Apply the highlight using palette background."""
        palette = self.palette()
        if not self.isEnabled():
            from ..constants import Colors
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(Colors.WIDGET_HIGHLIGHT_DISABLED_CHECKBOX_COLOR))
        else:
            palette.setColor(QtGui.QPalette.Base, self.highlight_color)
        self.setPalette(palette)
    
    def _remove_highlight(self):
        """Remove the highlight by restoring original palette."""
        self.setPalette(self.original_palette)
    
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if self.is_highlighted:
            self._apply_highlight()


class HighlightableSpinBox(QtWidgets.QSpinBox):
    """A spin box widget that can display a highlight color when it has stored values."""
    
    def __init__(self, parent=None, highlight_color=Colors.WIDGET_HIGHLIGHT_COLOR):
        super().__init__(parent)
        self.highlight_color = QtGui.QColor(highlight_color)
        self.is_highlighted = False
        self.original_palette = self.palette()
        
        # Don't enable auto fill background - let it be transparent
        self.setAutoFillBackground(False)
        
    def set_highlight_color(self, color):
        """Set the highlight color for this widget.
        
        Args:
            color (str): The highlight color in hex format (e.g., "#547699")
        """
        self.highlight_color = QtGui.QColor(color)
        if self.is_highlighted:
            self._apply_highlight()
    
    def set_highlighted(self, highlighted):
        """Set whether this widget should be highlighted.
        
        Args:
            highlighted (bool): True to highlight, False to remove highlight
        """
        if self.is_highlighted != highlighted:
            self.is_highlighted = highlighted
            if highlighted:
                self._apply_highlight()
            else:
                self._remove_highlight()
    
    def _apply_highlight(self):
        """Apply the highlight using palette background."""
        palette = self.palette()
        # Only set Base color (for the text input area)
        palette.setColor(QtGui.QPalette.Base, self.highlight_color)
        self.setPalette(palette)
    
    def _remove_highlight(self):
        """Remove the highlight by restoring original palette."""
        self.setPalette(self.original_palette)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if self.is_highlighted:
            self._apply_highlight()


class HighlightableComboBox(QtWidgets.QComboBox):
    """A combo box widget that can display a highlight color when it has stored values."""
    
    def __init__(self, parent=None, highlight_color=Colors.WIDGET_HIGHLIGHT_COLOR):
        super().__init__(parent)
        self.highlight_color = highlight_color
        self.is_highlighted = False
        self.original_stylesheet = self.styleSheet()
        
    def set_highlight_color(self, color):
        """Set the highlight color for this widget.
        
        Args:
            color (str): The highlight color in hex format (e.g., "#547699")
        """
        self.highlight_color = color
        if self.is_highlighted:
            self._apply_highlight()
    
    def set_highlighted(self, highlighted):
        """Set whether this widget should be highlighted.
        
        Args:
            highlighted (bool): True to highlight, False to remove highlight
        """
        self.is_highlighted = highlighted
        if highlighted:
            self._apply_highlight()
        else:
            self._remove_highlight()
    
    def _apply_highlight(self):
        """Apply the highlight styling to the widget."""
        color = self.highlight_color
        if not self.isEnabled():
            from ..constants import Colors
            color = Colors.WIDGET_HIGHLIGHT_DISABLED_COLOR
        highlight_style = f"""
            QComboBox {{
                background-color: {color};
            }}
        """
        combined_style = self.original_stylesheet + highlight_style
        self.setStyleSheet(combined_style)
    
    def _remove_highlight(self):
        """Remove the highlight styling from the widget."""
        self.setStyleSheet(self.original_stylesheet)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if self.is_highlighted:
            self._apply_highlight()


class HighlightableLineEdit(QtWidgets.QLineEdit):
    """A line edit widget that can display a highlight color when it has stored values."""
    
    def __init__(self, parent=None, highlight_color=Colors.WIDGET_HIGHLIGHT_COLOR):
        super().__init__(parent)
        self.highlight_color = highlight_color
        self.is_highlighted = False
        self.original_stylesheet = self.styleSheet()
        
    def set_highlight_color(self, color):
        """Set the highlight color for this widget.
        
        Args:
            color (str): The highlight color in hex format (e.g., "#547699")
        """
        self.highlight_color = color
        if self.is_highlighted:
            self._apply_highlight()
    
    def set_highlighted(self, highlighted):
        """Set whether this widget should be highlighted.
        
        Args:
            highlighted (bool): True to highlight, False to remove highlight
        """
        self.is_highlighted = highlighted
        if highlighted:
            self._apply_highlight()
        else:
            self._remove_highlight()
    
    def _apply_highlight(self):
        """Apply the highlight styling to the widget."""
        # Don't apply highlight if widget is disabled
        if not self.isEnabled():
            return
            
        color = self.highlight_color
        highlight_style = f"""
            QLineEdit {{
                background-color: {color};
            }}
        """
        combined_style = self.original_stylesheet + highlight_style
        self.setStyleSheet(combined_style)
    
    def _remove_highlight(self):
        """Remove the highlight styling from the widget."""
        self.setStyleSheet(self.original_stylesheet)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if self.is_highlighted:
            if enabled:
                # Re-apply highlight when enabled
                self._apply_highlight()
            else:
                # Remove highlight when disabled
                self._remove_highlight() 