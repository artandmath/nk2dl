"""Test configuration and shared fixtures."""

import os
import pytest
import logging
from pathlib import Path
import sys
import shutil

# Import directly from your project
from nk2dl.common.logging import setup_logging

@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before and after each test."""
    # Store existing env vars
    old_env = {}
    for key in list(os.environ.keys()):
        if key.startswith('NK2DL_'):
            old_env[key] = os.environ[key]
            del os.environ[key]
    
    yield
    
    # Restore old env vars and remove any new ones
    for key in list(os.environ.keys()):
        if key.startswith('NK2DL_'):
            del os.environ[key]
    for key, value in old_env.items():
        os.environ[key] = value

@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests."""
    # Set up test logger
    logger = setup_logging('nk2dl.tests')
    logger.debug("Test logging configured")
    return logger

# Store whether -s flag is used (capture disabled)
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    global _capture_disabled
    # Check the actual capture setting directly
    _capture_disabled = config.option.capture == "no"
    # Print for debugging
    print(f"Output capture is {'disabled' if _capture_disabled else 'enabled'}")

# Helper function to get terminal width
def get_terminal_width():
    """Get the terminal width or default to 80 if it can't be determined."""
    try:
        return shutil.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80

# Add spacing before test output (after test title)
def pytest_runtest_logstart(nodeid, location):
    """Add a newline after the test title but before any output."""
    # Only add newlines when output capturing is disabled (-s flag)
    if not globals().get('_capture_disabled', False):
        return
    
    width = get_terminal_width()
    separator = ">" * width
    sys.stdout.write(f"\n{separator}\n")

# Add spacing between test results for better readability
def pytest_runtest_logreport(report):
    """Add spacing between test results for better readability."""
    # Only add newlines when output capturing is disabled (-s flag)
    if not globals().get('_capture_disabled', False):
        return
        
    if report.when == 'call':  # Only print after the test has completed
        width = get_terminal_width()
        separator = "<" * width
        if report.passed:
            sys.stdout.write(f"\n{separator}\n\n")  # Add a blank line after PASSED
        elif report.failed:
            sys.stdout.write(f"\n{separator}\n\n")  # Add a blank line after FAILED
        elif report.skipped:
            sys.stdout.write(f"\n{separator}\n\n")  # Add a blank line after SKIPPED 