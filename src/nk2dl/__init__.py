"""
Nuke to Deadline Submitter - Core Library

A pure Python library for submitting Nuke scripts to Thinkbox Deadline.
"""

print("\nNuke to Deadline (nk2dl) v0.1")
print("Copyright (c) 2025 Daniel Harkness. All Rights Reserved.\n")

from .api import submit_nuke_script
from .config import config
from .errors import NK2DLError, SubmissionError, ConfigError
from .connection import DeadlineConnection

__version__ = "0.1.0"
__author__ = "Daniel Harkness"
__email__ = "danielharkness@icloud.com"

__all__ = [
    "submit_nuke_script",
    "config",
    "NK2DLError",
    "SubmissionError", 
    "ConfigError",
    "DeadlineConnection",
]