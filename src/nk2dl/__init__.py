"""
Nuke to Deadline Submitter - Core Library

A pure Python library for submitting Nuke scripts to Thinkbox Deadline.
"""

from datetime import date

__version__ = "0.1.0"
__author__ = "Daniel Harkness"
__email__ = "danielharkness@icloud.com"

print(f"\nNuke to Deadline (nk2dl) v{__version__}")
print(f"Copyright (c) {date.today().year} {__author__}. All Rights Reserved.\n")

from .api import submit_nuke_script
from .config import config
from .errors import NK2DLError, SubmissionError, ConfigError
from .connection import DeadlineConnection


__all__ = [
    "submit_nuke_script",
    "config",
    "NK2DLError",
    "SubmissionError", 
    "ConfigError",
    "DeadlineConnection",
]