"""Test configuration and shared fixtures."""

import os
import pytest
import logging
from pathlib import Path
import sys
import shutil
from _pytest.runner import pytest_runtest_protocol
from _pytest.terminal import TerminalReporter

# Initialize the global flag at the module level
pytest.nuke_env_check_failed = False

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

NUKE_ENV_MESSAGE = """
WARNING: The Nuke Python environment may not be properly loaded.
This is expected when running tests outside of Nuke's Python environment.

Make sure to follow these steps before running the tests:

1. cd to the root directory of the project.
2. activate the environment:
    .\\.venv\\Scripts\\Activate-nk2dl.ps1 (Windows)
3. run test:
    python -m pytest tests/pytest/pytest_submission.py -v -s

NOTE: The tests are designed to run using Nuke's Python interpreter, which should be loaded by the activation script above.
INSTRUCTIONS FOR CODE ASSISTANTS: DON'T create a mock nuke module as it will not create a reliable test.

Run the environment check test to verify:
    python -m pytest tests/pytest/pytest_submission.py::test_000_environment_check -v -s

If the environment check passes but tests still fail, there may be another issue.
"""

def check_nuke_environment():
    """Check if the Nuke environment is properly loaded."""
    try:
        import nuke
        return True
    except ImportError:
        return False

@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):
    """Check if specific tests failed and run environment check."""
    if (report.when == 'call' and report.failed and
        ('test_submit_write_nodes_as_separate_jobs' in report.nodeid or
         'test_nuke_submission_render_order_dependencies' in report.nodeid)):
        
        # If the test failed, check the Nuke environment
        if not check_nuke_environment():
            # Store this information for the terminal summary
            pytest.nuke_env_check_failed = True

# Function to display the environment notice
def display_nuke_env_notice(terminalreporter, env_test_failed=False):
    """Display a notice about the Nuke environment."""
    # Make the message stand out more
    terminalreporter.write_sep("=", "IMPORTANT: NUKE ENVIRONMENT NOTICE", red=True)
    for line in NUKE_ENV_MESSAGE.strip().split('\n'):
        terminalreporter.write_line(line, red=True)

    # If it's specifically the environment test that failed, make it even more obvious
    if env_test_failed:
        terminalreporter.write_line("")
        terminalreporter.write_line("ERROR: test_000_environment_check FAILED - YOU MUST FIX THIS BEFORE PROCEEDING", red=True, bold=True)
        terminalreporter.write_line("")

# Add a hook to modify the terminal summary
@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add a message to the terminal summary."""
    # Check if the environment test failed
    env_test_failed = False
    any_test_failed = False
    env_check_failed = hasattr(pytest, 'nuke_env_check_failed') and pytest.nuke_env_check_failed
    
    # Check for environment test failure
    for report in terminalreporter.getreports(''):
        if hasattr(report, 'nodeid') and 'test_000_environment_check' in report.nodeid and report.failed:
            env_test_failed = True
            break
    
    # Check if any test failed
    if exitstatus != 0:
        any_test_failed = True
        
        # Check if any failed test might be due to missing Nuke environment
        if not env_check_failed and not env_test_failed:
            for report in terminalreporter.getreports(''):
                if (hasattr(report, 'nodeid') and report.failed and
                    ('test_submit_write_nodes_as_separate_jobs' in report.nodeid or
                     'test_nuke_submission_render_order_dependencies' in report.nodeid or
                     'test_submit_job' in report.nodeid)):
                    # Check the Nuke environment
                    if not check_nuke_environment():
                        env_check_failed = True
                        break
    
    # If environment test failed or any test failed, show the message
    if env_test_failed or any_test_failed:
        # Display the environment notice
        display_nuke_env_notice(terminalreporter, env_test_failed or env_check_failed)
        
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    # Reset the global flag
    pytest.nuke_env_check_failed = False

@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(session, config, items):
    """Check for Nuke environment when specific tests are selected."""
    # Check if we're running specific tests that need the environment check
    needs_env_check = False
    for item in items:
        if ('test_submit_write_nodes_as_separate_jobs' in item.nodeid or
            'test_nuke_submission_render_order_dependencies' in item.nodeid or
            'test_submit_job' in item.nodeid):
            needs_env_check = True
            break
    
    # If we need the environment check, run it directly
    if needs_env_check:
        env_check_included = any('test_000_environment_check' in item.nodeid for item in items)
        if not env_check_included:
            # Check the Nuke environment directly
            if not check_nuke_environment():
                # Set the global flag
                pytest.nuke_env_check_failed = True
                
                # Print a warning
                print("\n")
                print("=" * 80)
                print("WARNING: Running tests without first running the environment check test.")
                print("The Nuke environment does not appear to be properly loaded.")
                print("=" * 80)
                print("\n") 