"""
Repositories package for data access layer.

This package contains repository classes that handle data access and business logic
for the GUI panel, following the repository pattern to separate data concerns
from UI logic.
"""

from .storage import NodeSettingsStorage

__all__ = [
    'NodeSettingsStorage',
] 