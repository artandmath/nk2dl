# NK2DL Test Suite

This directory contains the complete test suite for NK2DL, organized into different categories for various testing needs.

## Quick Start

### 1. Environment Setup

**Always activate the NK2DL environment first:**
```bash
# From the project root directory
.\.venv\Scripts\Activate-nk2dl.ps1
```

> **Important**: The environment activation script loads Nuke's Python interpreter, which is required for most tests.

### 2. Run All Tests
```bash
# Run all pytest tests
python -m pytest tests/ -v

# Run with output visible (recommended for debugging)
python -m pytest tests/ -v -s
```

## Test Structure

### 📁 `pytest/` - Unit & Integration Tests
**Purpose**: Core functionality testing using pytest framework  
**Requirements**: Nuke Python environment  

```bash
# Run all pytest tests
python -m pytest tests/pytest/ -v -s

# Run specific test files
python -m pytest tests/pytest/pytest_config.py -v -s
python -m pytest tests/pytest/pytest_submission.py -v -s
python -m pytest tests/pytest/pytest_deadline_connection.py -v -s

# Run specific test patterns
python -m pytest tests/pytest/ -v -s -k "config"
python -m pytest tests/pytest/ -v -s -k "mock"
python -m pytest tests/pytest/ -v -s -k "real"
```

**Key files:**
- `conftest.py` - Test configuration, fixtures, and Nuke environment detection
- `pytest_submission.py` - Submission engine tests (mock and real modes)
- `pytest_config.py` - Configuration system tests
- `pytest_deadline_connection.py` - Deadline connection tests
- `pytest_cli.py` - Command-line interface tests

### 📁 `qt/` - GUI Tests
**Purpose**: Qt/PySide interface testing  
**Requirements**: Nuke Python environment  

```bash
# Standalone Qt tests
python tests/qt/test_qt_app.py

# Nuke-integrated GUI tests
nuke --tg tests/qt/test_main_panel_nuke.py
nuke --tg tests/qt/test_qt_app_nuke.py

# Logic-only tests (no UI)
python tests/qt/test_inheritance_logic.py
```

📖 **See [qt/README.md](qt/README.md) for detailed GUI testing documentation**

### 📁 `nukescripts/` - Nuke Script Tests
**Purpose**: Test Nuke scripts for integration testing  
**Files**: 
- `test_dependencies.nk` - Dependency handling test
- `test_multishot.nk` - Multi-shot rendering test
- `pytest_nukescript.nk` - Script for pytest integration

```bash
# Use these scripts with the main integration tests
python tests/test_nk2dl.py
```

### 📄 Root Level Tests

#### `test_nk2dl.py` - Main Integration Test
**Purpose**: End-to-end submission testing  
```bash
python tests/test_nk2dl.py
```

#### `test_deadline_connection.py` - Connection Tests
**Purpose**: Deadline connectivity and communication  
```bash
python tests/test_deadline_connection.py
```

#### `pre_build_test.py` & `post_build_test.py` - Build Scripts
**Purpose**: Examples and tests for pre/post-build job scripts  
```bash
# These are typically called by the submission system
# Can be tested standalone:
python tests/pre_build_test.py
python tests/post_build_test.py
```

## Test Categories

### 🧪 Unit Tests
Fast, isolated tests for individual components:
```bash
python -m pytest tests/pytest/pytest_config.py -v
python -m pytest tests/pytest/pytest_cli.py -v
```

### 🔗 Integration Tests
End-to-end workflow testing:
```bash
python tests/test_nk2dl.py
python -m pytest tests/pytest/pytest_submission.py -v -s
```

### 🎨 GUI Tests
Interface and user interaction testing:
```bash
python tests/qt/test_qt_app.py
nuke --tg tests/qt/test_main_panel_nuke.py
```

### 🌐 Connection Tests
External service connectivity:
```bash
python tests/test_deadline_connection.py
python -m pytest tests/pytest/pytest_deadline_connection.py -v -s
```

## Test Modes

### Mock Mode
Tests using mocked dependencies (faster, no external dependencies):
```bash
python -m pytest tests/pytest/pytest_submission.py -v -s -k "mock"
```

### Real Mode  
Tests using actual Deadline connections (requires Deadline setup):
```bash
python -m pytest tests/pytest/pytest_submission.py -v -s -k "real"
```

## Environment Check

Before running tests, verify your environment:
```bash
python -m pytest tests/pytest/pytest_submission.py::test_000_environment_check -v -s
```

## Configuration

### pytest.ini
Located at `tests/pytest.ini`:
```ini
[pytest]
testpaths = .
python_files = pytest_*.py test_*.py
addopts = -v
markers = real_only: marks tests that should only run in real mode
```

### Test Markers
- `real_only` - Tests that require real Deadline connection

## Common Issues & Troubleshooting

### ❌ ImportError: No module named 'nuke'
**Solution**: Activate the NK2DL environment first:
```bash
.\.venv\Scripts\Activate-nk2dl.ps1
```

### ❌ Configuration tests failing
**Expected**: Some config tests may fail due to your personal config file overriding test values. This indicates the config system is working correctly.

### ❌ Deadline connection failures
1. Check if Deadline is running and accessible
2. Verify your config in `~/.nuke/nk2dl/config.yaml`
3. Run connection tests separately:
```bash
python tests/test_deadline_connection.py
```

### ❌ GUI tests not displaying
For Nuke GUI tests, ensure you're using terminal GUI mode:
```bash
nuke --tg tests/qt/test_main_panel_nuke.py
```

### ❌ "Command not found" errors
Ensure you're running from the project root directory:
```bash
cd /path/to/nk2dl-modules/nk2dl
.\.venv\Scripts\Activate-nk2dl.ps1
```

## Test Development

### Adding New Tests
1. **Unit tests**: Add to `tests/pytest/` with `pytest_` or `test_` prefix
2. **GUI tests**: Add to `tests/qt/` and update qt/README.md
3. **Integration tests**: Add to root `tests/` directory

### Test Requirements
- Use the environment activation script for Nuke dependencies
- Follow PEP8 coding standards  
- Add docstrings explaining test purpose
- Use meaningful test names
- Add markers for special test categories

### Running Tests in Development
```bash
# Watch mode (re-run on file changes) - requires pytest-watch
ptw tests/pytest/pytest_config.py -- -v -s

# Coverage reporting - requires pytest-cov
python -m pytest tests/pytest/ --cov=nk2dl --cov-report=html

# Profile slow tests - requires pytest-profiling
python -m pytest tests/pytest/ --profile
```

### Test Modes

NK2DL submission tests support two modes:

#### Mock Mode (Default)
- Uses mocked Deadline connections
- Does NOT submit jobs to the farm
- Fast execution, no external dependencies
- Ideal for development and CI/CD

```bash
# Run only mock tests
python -m pytest tests/pytest/pytest_submission.py -k "mock" -v -s

# Mock mode is used automatically when both modes are run
python -m pytest tests/pytest/pytest_submission.py -v -s
```

#### Real Mode 
- Connects to actual Deadline farm
- DOES submit real jobs to Deadline
- Requires working Deadline connection
- Use with caution on production farms

```bash
# Run only real tests (submits actual jobs!)
python -m pytest tests/pytest/pytest_submission.py -k "real" -v -s

# Run specific real test
python -m pytest tests/pytest/pytest_submission.py::test_submit_job[real] -v -s
```

⚠️ **Important**: Real mode tests will submit actual jobs to your Deadline farm. Only use on development/test environments!

## CI/CD Integration

These tests are designed to run in automated environments:
```bash
# Minimal test run (no GUI, mock mode only)
python -m pytest tests/pytest/ -v -k "not real_only and not gui"

# Full test suite (requires Nuke and Deadline)
.\.venv\Scripts\Activate-nk2dl.ps1
python -m pytest tests/ -v
```

---

📖 **Additional Documentation:**
- [Qt Tests Guide](qt/README.md) - Detailed GUI testing
- [Configuration Guide](../docs/config.md) - Test configuration
- [Troubleshooting Guide](../docs/troubleshooting.md) - Common issues