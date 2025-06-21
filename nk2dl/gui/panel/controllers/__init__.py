"""
Controllers package for managing UI state and business logic.

This package contains controller classes that coordinate between models and views,
managing complex UI state and operations like progress reporting.
"""

from .progress import PanelProgressManager

__all__ = [
    'PanelProgressManager',
] 