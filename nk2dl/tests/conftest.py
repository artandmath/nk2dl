"""Test configuration and shared fixtures."""

import os
import pytest
import logging
from pathlib import Path

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