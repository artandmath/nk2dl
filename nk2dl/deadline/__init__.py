"""Deadline-related modules for nk2dl.

This package contains modules for interacting with Deadline.
"""

from .connection import DeadlineConnection, get_connection

__all__ = [
    'DeadlineConnection',
    'get_connection',
]
