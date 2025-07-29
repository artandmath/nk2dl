#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for storage visual indication system.

This script tests the visual indication functionality for widgets that have
stored values, demonstrating the light blue highlight feature.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide6"
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
    except ImportError:
        print("Neither PySide6 nor PySide2 is available")
        sys.exit(1)

from nk2dl.gui.panel.widgets.highlightable_widgets import (
    HighlightableCheckBox, HighlightableSpinBox, 
    HighlightableComboBox, HighlightableLineEdit
)
from nk2dl.gui.panel.storage_visual_indication import StorageVisualIndicationManager
from nk2dl.gui.panel.constants import Colors


class TestStorageVisualIndicationApp(QtWidgets.QWidget):
    """Test application for storage visual indication system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Storage Visual Indication Test ({PYSIDE_VERSION})")
        self.setGeometry(100, 100, 600, 400)
        
        # Create visual indication manager
        self.visual_manager = StorageVisualIndicationManager()
        
        self._create_ui()
        self._register_widgets()
    
    def _create_ui(self):
        """Create the test UI."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QtWidgets.QLabel("Storage Visual Indication Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Info label
        info_label = QtWidgets.QLabel(
            f"Testing highlightable widgets with light blue color: {Colors.WIDGET_HIGHLIGHT_COLOR}\n"
            "Use the buttons below to toggle highlights and test the functionality."
        )
        info_label.setStyleSheet("margin: 10px; color: #666666;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Test widgets group
        widgets_group = QtWidgets.QGroupBox("Test Widgets")
        widgets_layout = QtWidgets.QGridLayout()
        widgets_group.setLayout(widgets_layout)
        
        # Row 1: Checkbox and SpinBox
        widgets_layout.addWidget(QtWidgets.QLabel("Checkbox:"), 0, 0)
        self.test_checkbox = HighlightableCheckBox("Test Checkbox")
        widgets_layout.addWidget(self.test_checkbox, 0, 1)
        
        widgets_layout.addWidget(QtWidgets.QLabel("SpinBox:"), 0, 2)
        self.test_spinbox = HighlightableSpinBox()
        self.test_spinbox.setRange(0, 100)
        self.test_spinbox.setValue(50)
        widgets_layout.addWidget(self.test_spinbox, 0, 3)
        
        # Row 2: ComboBox and LineEdit
        widgets_layout.addWidget(QtWidgets.QLabel("ComboBox:"), 1, 0)
        self.test_combobox = HighlightableComboBox()
        self.test_combobox.addItems(["Option 1", "Option 2", "Option 3"])
        widgets_layout.addWidget(self.test_combobox, 1, 1)
        
        widgets_layout.addWidget(QtWidgets.QLabel("LineEdit:"), 1, 2)
        self.test_lineedit = HighlightableLineEdit()
        self.test_lineedit.setPlaceholderText("Enter text here...")
        widgets_layout.addWidget(self.test_lineedit, 1, 3)
        
        layout.addWidget(widgets_group)
        
        # Control buttons
        buttons_group = QtWidgets.QGroupBox("Controls")
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_group.setLayout(buttons_layout)
        
        self.highlight_all_btn = QtWidgets.QPushButton("Highlight All")
        self.highlight_all_btn.clicked.connect(self._highlight_all)
        buttons_layout.addWidget(self.highlight_all_btn)
        
        self.clear_all_btn = QtWidgets.QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self._clear_all)
        buttons_layout.addWidget(self.clear_all_btn)
        
        self.toggle_checkbox_btn = QtWidgets.QPushButton("Toggle Checkbox")
        self.toggle_checkbox_btn.clicked.connect(self._toggle_checkbox)
        buttons_layout.addWidget(self.toggle_checkbox_btn)
        
        self.toggle_spinbox_btn = QtWidgets.QPushButton("Toggle SpinBox")
        self.toggle_spinbox_btn.clicked.connect(self._toggle_spinbox)
        buttons_layout.addWidget(self.toggle_spinbox_btn)
        
        layout.addWidget(buttons_group)
        
        # Status label
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("margin: 10px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Stretch
        layout.addStretch()
    
    def _register_widgets(self):
        """Register widgets with the visual indication manager."""
        # Register each widget with a fake parameter name
        self.visual_manager.register_widget(self.test_checkbox, 'test_checkbox')
        self.visual_manager.register_widget(self.test_spinbox, 'test_spinbox')
        self.visual_manager.register_widget(self.test_combobox, 'test_combobox')
        self.visual_manager.register_widget(self.test_lineedit, 'test_lineedit')
        
        # Update status
        self._update_status()
    
    def _highlight_all(self):
        """Highlight all widgets."""
        self.test_checkbox.set_highlighted(True)
        self.test_spinbox.set_highlighted(True)
        self.test_combobox.set_highlighted(True)
        self.test_lineedit.set_highlighted(True)
        self.status_label.setText("All widgets highlighted")
    
    def _clear_all(self):
        """Clear all highlights."""
        self.test_checkbox.set_highlighted(False)
        self.test_spinbox.set_highlighted(False)
        self.test_combobox.set_highlighted(False)
        self.test_lineedit.set_highlighted(False)
        self.status_label.setText("All highlights cleared")
    
    def _toggle_checkbox(self):
        """Toggle checkbox highlight."""
        current = self.test_checkbox.is_highlighted
        self.test_checkbox.set_highlighted(not current)
        self.status_label.setText(f"Checkbox highlight: {'ON' if not current else 'OFF'}")
    
    def _toggle_spinbox(self):
        """Toggle spinbox highlight."""
        current = self.test_spinbox.is_highlighted
        self.test_spinbox.set_highlighted(not current)
        self.status_label.setText(f"SpinBox highlight: {'ON' if not current else 'OFF'}")
    
    def _update_status(self):
        """Update status information."""
        stats = {
            'tracked_widgets': self.visual_manager.get_tracked_widget_count(),
            'highlighted_widgets': self.visual_manager.get_highlighted_widget_count()
        }
        self.status_label.setText(
            f"Tracked widgets: {stats['tracked_widgets']}, "
            f"Highlighted widgets: {stats['highlighted_widgets']}"
        )


def main():
    """Run the test application."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Create test window
    test_window = TestStorageVisualIndicationApp()
    test_window.show()
    
    print(f"Storage Visual Indication Test running with {PYSIDE_VERSION}")
    print(f"Highlight color: {Colors.WIDGET_HIGHLIGHT_COLOR}")
    print("Use the buttons to test highlighting functionality")
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 