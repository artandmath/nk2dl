"""
Nuke to Deadline Submitter - Core Library

A pure Python library for submitting Nuke scripts to Thinkbox Deadline.
"""

from .api import submit_nuke_script, submit_job
from .common.config import config
from .common.errors import Nk2dlError, SubmissionError, ConfigError
from .deadline.connection import DeadlineConnection

__version__ = "0.1.0"
__author__ = "Daniel Harkness"
__email__ = "danielharkness@icloud.com"

__all__ = [
    "submit_nuke_script",
    "submit_job", 
    "config",
    "Nk2dlError",
    "SubmissionError",
    "ConfigError",
    "DeadlineConnection",
]