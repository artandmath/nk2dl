# -*- coding: utf-8 -*-
"""Widgets module for the nk2dl panel.

This module contains all custom widget classes used in the nk2dl panel interface.
Widgets handle UI presentation and user interaction, connecting to models for data management.
"""

# Import all widgets from their specific extracted modules
from .table_widgets import StandardTableWidget, FrozenTableWidget
from .header_widgets import GroupedHeaderView, CustomHeaderView
from .misc_widgets import ColoredGroupBox, ColumnVisibilityDropdown
from .highlightable_widgets import (
    HighlightableCheckBox, HighlightableSpinBox, 
    HighlightableComboBox, HighlightableLineEdit
)

__all__ = [
    'ColoredGroupBox',
    'StandardTableWidget',
    'GroupedHeaderView', 
    'FrozenTableWidget',
    'ColumnVisibilityDropdown',
    'CustomHeaderView',
    'HighlightableCheckBox',
    'HighlightableSpinBox',
    'HighlightableComboBox',
    'HighlightableLineEdit',
] 