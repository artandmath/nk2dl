# NK2DL Project Separation Plan

## Current State Analysis

The nk2dl project currently consists of 3 tightly integrated components:

1. **Core Module (`nk2dl`)**: Core functionality for Nuke script submission to Deadline
2. **CLI Tool (`nk2dl cli`)**: Command-line interface for script submission
3. **GUI Panel (`nk2dl gui`)**: Nuke-integrated GUI panel for submission

### Current Dependencies

```
CLI → Core Module (nk2dl)
GUI → Core Module (nk2dl) + Nuke + PySide
Core Module → Deadline API + Nuke API
```

### Key Dependencies Identified

**CLI Dependencies:**
- `nk2dl.common.config` - Configuration management
- `nk2dl.common.errors` - Error handling
- `nk2dl.common.logging` - Logging system
- `nk2dl.nuke.submission` - Core submission logic

**GUI Dependencies:**
- `nk2dl.common.*` - All common modules
- `nk2dl.nuke.submission` - Core submission logic
- `nk2dl.deadline.connection` - Deadline connectivity
- Nuke API + PySide (Qt)

**Core Module Dependencies:**
- Deadline API
- Nuke API (for script parsing)
- PyYAML (configuration)
- Standard Python libraries

## Detailed File Migration Mapping

### Core Library (nk2dl)
```bash
# Core modules
nk2dl/nk2dl/common/ → nk2dl-core/python/nk2dl/common/
nk2dl/nk2dl/nuke/ → nk2dl-core/python/nk2dl/nuke/
nk2dl/nk2dl/deadline/ → nk2dl-core/python/nk2dl/deadline/
nk2dl/nk2dl/api.py → nk2dl-core/python/nk2dl/api.py
nk2dl/nk2dl/__init__.py → nk2dl-core/python/nk2dl/__init__.py (cleaned up)

# Configuration and assets
nk2dl/nk2dl/config.yaml → nk2dl-core/python/nk2dl/config.yaml

# Core tests
nk2dl/tests/pytest/pytest_config.py → nk2dl-core/python/tests/
nk2dl/tests/pytest/pytest_deadline_connection.py → nk2dl-core/python/tests/
nk2dl/tests/pytest/pytest_submission.py → nk2dl-core/python/tests/
nk2dl/tests/pytest/conftest.py → nk2dl-core/python/tests/
```

### CLI Tool (nk2dl-cli)
```bash
# CLI modules
nk2dl/nk2dl/cli/ → nk2dl-cli/python/nk2dl_cli/
nk2dl/nk2dl/__main__.py → nk2dl-cli/python/nk2dl_cli/__main__.py

# CLI tests
nk2dl/tests/pytest/pytest_cli.py → nk2dl-cli/python/tests/

# Scripts
nk2dl/scripts/nk2dl → nk2dl-cli/scripts/ (if needed)
```

### GUI Panel (nk2dl-gui)
```bash
# GUI modules
nk2dl/nk2dl/gui/ → nk2dl-gui/python/nk2dl_gui/
nk2dl/nk2dl/setup_gui.py → nk2dl-gui/python/nk2dl_gui/setup_gui.py

# Nuke integration
nk2dl/dot_nuke/ → nk2dl-gui/python/nk2dl_gui/nuke_integration/
nk2dl/deadline/plugins/nuke/ → nk2dl-gui/deadline_plugins/

# GUI tests
nk2dl/tests/qt/ → nk2dl-gui/python/tests/
nk2dl/tests/nukescripts/ → nk2dl-gui/python/tests/nukescripts/
```

## Immediate Next Steps

### 1. Setup Repository Structure

**For each repository, create the python folder structure:**

```bash
# Clone the repositories locally (development branch)
git clone -b development https://github.com/artandmath/nk2dl.git nk2dl-core
git clone -b development https://github.com/artandmath/nk2dl-cli.git
git clone -b development https://github.com/artandmath/nk2dl-gui.git

# Create python folder structure in each
mkdir -p nk2dl-core/python/nk2dl
mkdir -p nk2dl-core/python/tests
mkdir -p nk2dl-cli/python/nk2dl_cli
mkdir -p nk2dl-cli/python/tests
mkdir -p nk2dl-gui/python/nk2dl_gui
mkdir -p nk2dl-gui/python/tests
mkdir -p nk2dl-gui/deadline_plugins
```

### 2. Extract Core Library (nk2dl)

**Move core modules from current repository:**

```bash
# From current nk2dl repository
cp -r nk2dl/common nk2dl-core/python/nk2dl/
cp -r nk2dl/nuke nk2dl-core/python/nk2dl/
cp -r nk2dl/deadline nk2dl-core/python/nk2dl/
cp nk2dl/api.py nk2dl-core/python/nk2dl/
cp nk2dl/config.yaml nk2dl-core/python/nk2dl/

# Move relevant tests
cp tests/pytest/pytest_config.py nk2dl-core/python/tests/
cp tests/pytest/pytest_deadline_connection.py nk2dl-core/python/tests/
cp tests/pytest/pytest_submission.py nk2dl-core/python/tests/
cp tests/pytest/conftest.py nk2dl-core/python/tests/
```

### 3. Update Dependencies

**nk2dl-core/setup.py:**
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nk2dl",
    version="0.1.0",
    author="Daniel Harkness",
    author_email="danielharkness@icloud.com",
    description="Nuke to Deadline Submitter - Core Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artandmath/nk2dl",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    install_requires=[
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "types-PyYAML>=6.0.12.12",
            "pluggy>=1.0.0",
            "exceptiongroup>=1.0.0",
            "iniconfig>=1.0.0",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    package_data={
        "nk2dl": ["config.yaml"],
    },
)
```

**nk2dl-cli/setup.py:**
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nk2dl-cli",
    version="0.1.0",
    author="Daniel Harkness",
    author_email="danielharkness@icloud.com",
    description="Nuke to Deadline Submitter - Command Line Interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artandmath/nk2dl-cli",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    install_requires=[
        "nk2dl>=0.1.0,<0.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "nk2dl=nk2dl_cli.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Environment :: Console",
    ],
    python_requires=">=3.10",
)
```

**nk2dl-gui/setup.py:**
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nk2dl-gui",
    version="0.1.0",
    author="Daniel Harkness",
    author_email="danielharkness@icloud.com",
    description="Nuke to Deadline Submitter - GUI Panel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artandmath/nk2dl-gui",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    install_requires=[
        "nk2dl>=0.1.0,<0.2.0",
        "PySide2>=5.15.0;python_version<'3.10'",
        "PySide6>=6.0.0;python_version>='3.10'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.10",
    package_data={
        "nk2dl_gui": [
            "grizmos/*.nk",
            "nuke_integration/*.py",
        ],
    },
)
```

### 4. Update Import Statements

**In nk2dl-cli, update imports in main.py and commands.py:**
```python
# Old imports
from ..common.config import config
from ..nuke.submission import submit_nuke_script

# New imports
from nk2dl.common.config import config
from nk2dl.nuke.submission import submit_nuke_script
```

**In nk2dl-gui, update imports throughout GUI modules:**
```python
# Old imports
from ..common.config import config
from ..nuke.submission import submit_nuke_script
from ..deadline.connection import DeadlineConnection

# New imports
from nk2dl.common.config import config
from nk2dl.nuke.submission import submit_nuke_script
from nk2dl.deadline.connection import DeadlineConnection
```

### 5. CI/CD Pipeline Configuration

**Create .github/workflows/ci.yml for each repository:**

**nk2dl-core:**
```yaml
name: Core Library CI

on:
  push:
    branches: [ development, main ]
  pull_request:
    branches: [ development, main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Lint with flake8
      run: flake8 python/nk2dl python/tests
    
    - name: Format check with black
      run: black --check python/nk2dl python/tests
    
    - name: Sort imports check with isort
      run: isort --check-only python/nk2dl python/tests
    
    - name: Type check with mypy
      run: mypy python/nk2dl
    
    - name: Test with pytest
      run: pytest python/tests --cov=nk2dl --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  publish:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

**nk2dl-cli:**
```yaml
name: CLI Tool CI

on:
  push:
    branches: [ development, main ]
  pull_request:
    branches: [ development, main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Lint and format checks
      run: |
        flake8 python/nk2dl_cli python/tests
        black --check python/nk2dl_cli python/tests
        isort --check-only python/nk2dl_cli python/tests
    
    - name: Test CLI functionality
      run: |
        pytest python/tests --cov=nk2dl_cli --cov-report=xml
        # Test CLI entry point
        nk2dl --help

  integration-test:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Test with latest nk2dl core
      run: |
        pip install nk2dl  # Install latest from PyPI
        pip install -e .
        nk2dl --help
```

**nk2dl-gui:**
```yaml
name: GUI Panel CI

on:
  push:
    branches: [ development, main ]
  pull_request:
    branches: [ development, main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
        pyside-version: ["PySide6", "PySide2"]
        exclude:
          - python-version: "3.12"
            pyside-version: "PySide2"  # PySide2 doesn't support Python 3.12

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        pip install ${{ matrix.pyside-version }}
    
    - name: Lint and format checks
      run: |
        flake8 python/nk2dl_gui python/tests
        black --check python/nk2dl_gui python/tests
        isort --check-only python/nk2dl_gui python/tests
    
    - name: Test GUI components (without Nuke)
      run: pytest python/tests --cov=nk2dl_gui --cov-report=xml
      env:
        QT_QPA_PLATFORM: offscreen  # For headless testing
```

### 6. Git Branch Management

**Important**: All repositories use `development` as the primary development branch, not `main`.

**Git workflow:**
```bash
# Clone with development branch
git clone -b development https://github.com/artandmath/nk2dl.git
git clone -b development https://github.com/artandmath/nk2dl-cli.git
git clone -b development https://github.com/artandmath/nk2dl-gui.git

# Push to development branch
git push origin development

# Create feature branches from development
git checkout -b feature/core-extraction development
git checkout -b feature/cli-separation development
git checkout -b feature/gui-separation development
```

**Branch strategy:**
- `development` - Primary development branch
- `feature/*` - Feature branches for specific work
- `main` - Release branch (when ready)

### 7. Version Synchronization Strategy

**Version Compatibility Matrix:**
```
nk2dl-core  | nk2dl-cli    | nk2dl-gui    | Notes
------------|--------------|--------------|-------
0.1.x       | 0.1.x        | 0.1.x        | Initial release
0.2.x       | 0.1.x-0.2.x  | 0.1.x-0.2.x  | Backward compatible
1.0.x       | 1.0.x        | 1.0.x        | Major release
```

**Dependency Constraints:**
- CLI and GUI packages pin core to compatible major version: `nk2dl>=0.1.0,<0.2.0`
- Use `~=0.1.0` for patch-level compatibility
- Update constraints with each major release

## Proposed Separation Plan

### 1. Core Library: `nk2dl`

**Repository**: `nk2dl`
**Purpose**: Pure Python library for Nuke script submission to Deadline
**Dependencies**: Minimal external dependencies

**Structure:**
```
nk2dl/
├── .github/
│   └── workflows/
│       └── ci.yml
├── python/
│   ├── nk2dl/
│   │   ├── __init__.py
│   │   ├── api.py              # Public API
│   │   ├── config.yaml         # Default configuration
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Configuration system
│   │   │   ├── errors.py       # Error definitions
│   │   │   ├── logging.py      # Logging system
│   │   │   └── framerange.py   # Frame range utilities
│   │   ├── nuke/
│   │   │   ├── __init__.py
│   │   │   ├── submission.py   # Core submission logic
│   │   │   ├── parser.py       # Script parsing
│   │   │   ├── utils.py        # Nuke utilities
│   │   │   └── subprocess.py   # Subprocess handling
│   │   └── deadline/
│   │       ├── __init__.py
│   │       └── connection.py   # Deadline connectivity
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_config.py
│       ├── test_deadline_connection.py
│       └── test_submission.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Key Features:**
- Pure Python library (no GUI dependencies)
- Comprehensive API for script submission
- Configuration management
- Error handling and logging
- Deadline connectivity
- Nuke script parsing and analysis

**Dependencies:**
```
install_requires=[
    "pyyaml>=6.0.1",
]
```

### 2. CLI Tool: `nk2dl-cli`

**Repository**: `nk2dl-cli`
**Purpose**: Command-line interface for nk2dl
**CLI Command**: `nk2dl` (repository name is nk2dl-cli, but command is nk2dl)
**Dependencies**: nk2dl

**Structure:**
```
nk2dl-cli/
├── .github/
│   └── workflows/
│       └── ci.yml
├── python/
│   ├── nk2dl_cli/
│   │   ├── __init__.py
│   │   ├── main.py             # CLI entry point
│   │   ├── __main__.py         # python -m nk2dl_cli support
│   │   ├── commands.py         # Command implementations
│   │   └── parser.py           # Argument parsing
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_cli.py
│       └── test_commands.py
├── scripts/
│   └── nk2dl                   # Shell script wrapper (if needed)
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Key Features:**
- Command-line interface (`nk2dl` command)
- Argument parsing and validation
- Configuration management
- Error reporting
- Progress feedback

**Dependencies:**
```
install_requires=[
    "nk2dl>=0.1.0,<0.2.0",
]
```

**Entry Point:**
```python
entry_points={
    "console_scripts": [
        "nk2dl=nk2dl_cli.main:main",  # Command is 'nk2dl'
    ],
},
```

### 3. GUI Panel: `nk2dl-gui`

**Repository**: `nk2dl-gui`
**Purpose**: Nuke-integrated GUI panel
**Dependencies**: nk2dl + Nuke + PySide

**Structure:**
```
nk2dl-gui/
├── .github/
│   └── workflows/
│       └── ci.yml
├── python/
│   ├── nk2dl_gui/
│   │   ├── __init__.py
│   │   ├── setup_gui.py        # GUI setup and registration
│   │   ├── menus.py            # Nuke menu integration
│   │   ├── panel/
│   │   │   ├── __init__.py
│   │   │   ├── panel.py        # Main panel class
│   │   │   ├── constants.py    # UI constants
│   │   │   ├── config.py       # Panel configuration
│   │   │   ├── models/         # Data models
│   │   │   ├── views/          # UI views
│   │   │   ├── widgets/        # Custom widgets
│   │   │   ├── delegates.py    # Table delegates
│   │   │   ├── controllers/    # Background workers
│   │   │   └── repositories/   # Data repositories
│   │   ├── grizmos/            # Nuke gizmos
│   │   │   ├── Nk2dl_ModifyMetaData.nk
│   │   │   └── Nk2dl_ModifyMetaDataGui.nk
│   │   └── nuke_integration/   # Nuke setup files
│   │       ├── __init__.py
│   │       ├── init.py         # Nuke init.py content
│   │       └── menu.py         # Nuke menu.py content
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── qt/                 # Qt-specific tests
│       └── nukescripts/        # Nuke script tests
├── deadline_plugins/           # Deadline plugin files
│   └── nuke/
│       ├── Nuke.ico
│       ├── Nuke.options
│       ├── Nuke.param
│       └── Nuke.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Key Features:**
- Nuke panel integration
- Qt-based GUI components (PySide2/PySide6)
- Real-time data updates
- Background processing
- Configuration management
- Nuke gizmo integration
- Deadline plugin files

**Dependencies:**
```
install_requires=[
    "nk2dl>=0.1.0,<0.2.0",
    "PySide2>=5.15.0;python_version<'3.10'",
    "PySide6>=6.0.0;python_version>='3.10'",
]
```

## Migration Strategy

### Phase 1: Core Library Extraction (Week 1-2) ✅ REPOSITORIES CREATED

**Status**: GitHub repositories already created at:
- [nk2dl](https://github.com/artandmath/nk2dl) - Core library
- [nk2dl-cli](https://github.com/artandmath/nk2dl-cli) - CLI tool  
- [nk2dl-gui](https://github.com/artandmath/nk2dl-gui) - GUI panel

**Next Steps**:
1. **Extract core modules** to nk2dl repository
   - Move `common/`, `nuke/`, `deadline/` modules
   - Create new `api.py` with clean public interface
   - Update imports and dependencies
   - Set up CI/CD pipeline
   - Create comprehensive test suite
   - Publish to PyPI (test first, then production)

2. **Clean up core package exports**
   - Update `__init__.py` to export only public API
   - Remove CLI-specific code from core
   - Ensure backward compatibility

### Phase 2: CLI Tool Extraction (Week 3) ✅ REPOSITORY CREATED

**Status**: [nk2dl-cli](https://github.com/artandmath/nk2dl-cli) repository created

**Next Steps**:
1. **Extract CLI modules** to nk2dl-cli repository
   - Move `cli/` modules to `python/nk2dl_cli/`
   - Move `__main__.py` to CLI package
   - Create new entry point structure: `nk2dl=nk2dl_cli.main:main`
   - Update to use `nk2dl` dependency
   - Set up CI/CD pipeline
   - Create CLI-specific tests
   - Test integration with core package
   - Publish to PyPI

2. **Ensure CLI command works as expected**
   - Verify `nk2dl` command functions correctly
   - Test all CLI subcommands
   - Validate help text and documentation

### Phase 3: GUI Panel Extraction (Week 4-5) ✅ REPOSITORY CREATED

**Status**: [nk2dl-gui](https://github.com/artandmath/nk2dl-gui) repository created

**Next Steps**:
1. **Extract GUI modules** to nk2dl-gui repository
   - Move `gui/` modules to `python/nk2dl_gui/`
   - Move `setup_gui.py` to GUI package
   - Move `dot_nuke/` to `nuke_integration/`
   - Move deadline plugins to `deadline_plugins/`
   - Update imports to use `nk2dl` dependency
   - Create GUI-specific setup and configuration
   - Set up CI/CD pipeline with Qt testing
   - Create comprehensive test suite
   - Publish to PyPI

2. **Update Nuke integration**
   - Ensure Nuke menu integration still works
   - Test panel registration and functionality
   - Verify PySide2/PySide6 compatibility

### Phase 4: Integration and Testing (Week 6)

1. **Cross-package integration testing**
   - Test all three components together
   - Verify functionality preservation
   - Test version compatibility
   - Performance benchmarking

2. **Documentation updates**
   - Update installation instructions for each package
   - Create component-specific documentation
   - Update examples and tutorials
   - Create migration guide for existing users

3. **Release coordination**
   - Coordinate initial releases (0.1.0 for all packages)
   - Update dependency constraints
   - Tag releases in all repositories

## Test Distribution Strategy

### Core Library Tests
- **Unit tests**: `nk2dl-core/python/tests/`
- **Integration tests**: Core functionality with Deadline
- **Configuration tests**: YAML parsing and validation
- **API tests**: Public interface validation

### CLI Tests
- **Command tests**: `nk2dl-cli/python/tests/`
- **Argument parsing tests**: CLI interface validation
- **Integration tests**: CLI → Core interaction
- **Entry point tests**: Verify `nk2dl` command works

### GUI Tests
- **Widget tests**: `nk2dl-gui/python/tests/qt/`
- **Nuke integration tests**: `nk2dl-gui/python/tests/nukescripts/`
- **PySide compatibility tests**: Both PySide2 and PySide6
- **Panel functionality tests**: GUI → Core interaction

### Cross-Package Integration Tests
- **End-to-end workflow tests**: Complete submission pipeline
- **Version compatibility tests**: Package version combinations
- **Performance regression tests**: Ensure no degradation

## Benefits of Separation

### 1. **Modularity**
- Each component can be developed independently
- Clear separation of concerns
- Easier to maintain and test
- Better code organization

### 2. **Flexibility**
- Users can install only what they need
- Different deployment strategies possible
- Easier to integrate into existing pipelines
- Support for different Python environments

### 3. **Development Efficiency**
- Parallel development possible
- Smaller, focused codebases
- Easier onboarding for new contributors
- Independent release cycles

### 4. **Distribution**
- Independent versioning and releases
- Better dependency management
- PyPI publication for each component
- Easier package management

## Implementation Details

### Version Management
- Use semantic versioning for all components
- Maintain compatibility matrices
- Pin major versions in dependencies
- Coordinate releases when needed

### Documentation Strategy
- Each component has comprehensive README
- Cross-reference between components
- Central documentation hub with integration guides
- API documentation for all public interfaces

### Testing Strategy
- Unit tests for each component
- Integration tests for component interaction
- End-to-end tests for complete workflows
- Automated testing in CI/CD pipelines

### CI/CD Pipeline
- Separate GitHub Actions for each repository
- Integration testing across components
- Automated dependency updates
- PyPI publication on releases

## Migration Checklist

### Core Library (nk2dl) ✅ REPOSITORY CREATED
- [x] Create new repository
- [ ] Extract core modules
- [ ] Create clean API interface
- [ ] Update imports and dependencies
- [ ] Set up CI/CD pipeline
- [ ] Create comprehensive tests
- [ ] Publish to PyPI (test)
- [ ] Publish to PyPI (production)
- [ ] Update documentation

### CLI Tool (nk2dl-cli) ✅ REPOSITORY CREATED
- [x] Create new repository
- [ ] Extract CLI modules
- [ ] Update to use nk2dl dependency
- [ ] Configure entry point: `nk2dl=nk2dl_cli.main:main`
- [ ] Set up CI/CD pipeline
- [ ] Create CLI-specific tests
- [ ] Test CLI integration with core
- [ ] Publish to PyPI (test)
- [ ] Publish to PyPI (production)
- [ ] Update documentation

### GUI Panel (nk2dl-gui) ✅ REPOSITORY CREATED
- [x] Create new repository
- [ ] Extract GUI modules
- [ ] Move Nuke integration files
- [ ] Move deadline plugins
- [ ] Update to use nk2dl dependency
- [ ] Set up CI/CD pipeline with Qt support
- [ ] Create GUI-specific tests
- [ ] Test GUI integration with core
- [ ] Test Nuke panel functionality
- [ ] Publish to PyPI (test)
- [ ] Publish to PyPI (production)
- [ ] Update documentation

### Integration and Release
- [ ] Cross-package integration testing
- [ ] Version compatibility testing
- [ ] Performance benchmarking
- [ ] Update main documentation
- [ ] Create migration guide
- [ ] Update examples and tutorials
- [ ] Coordinate initial releases (0.1.0)
- [ ] Update package metadata
- [ ] Create release announcements

## Risk Mitigation

### 1. **Breaking Changes**
- Maintain backward compatibility during transition
- Provide clear migration guides
- Use semantic versioning strictly
- Deprecate features before removal

### 2. **Dependency Management**
- Pin dependency versions in setup.py
- Use compatible version ranges
- Regular dependency security updates
- Monitor for dependency conflicts

### 3. **Testing Coverage**
- Comprehensive test suites for each package
- Integration testing across packages
- Automated testing in CI/CD
- Manual testing for critical workflows

### 4. **Documentation and Support**
- Clear installation instructions for each package
- Comprehensive migration guides
- Troubleshooting documentation
- Community support channels

## Timeline

- **Week 1-2**: Core library extraction and initial testing
- **Week 3**: CLI tool extraction and testing
- **Week 4-5**: GUI panel extraction and testing
- **Week 6**: Integration testing and documentation
- **Week 7**: Release coordination and migration support
- **Week 8+**: Ongoing maintenance and improvements

## Success Criteria

1. **Functionality Preservation**: All existing features work as before
2. **Performance**: No performance degradation from separation
3. **Usability**: Installation and usage remain simple or simpler
4. **Maintainability**: Code is easier to maintain and extend
5. **Documentation**: Clear documentation for all components
6. **Testing**: Comprehensive test coverage for all packages
7. **CI/CD**: Automated testing and publishing pipelines
8. **Community**: Smooth transition for existing users
