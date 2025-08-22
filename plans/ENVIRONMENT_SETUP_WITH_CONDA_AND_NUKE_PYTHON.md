## Environment setup and deployment plan (Conda + Nuke Python)

Status: Ready for implementation
Owner: Pipeline
Last Updated: 2025-01-XX

### Goal
- Use conda for development and packaging
- Use Nuke's embedded Python executable for installation and runtime, guaranteeing that nk2dl is available inside Nuke
- Align with VFX Reference Platform 2024 (Python 3.10)

### Rationale/Constraints
- Studio uses custom activation to load Foundry/Nuke’s Python
- We must install into the Python that ships with Nuke, not merely match its version
- Keep workflows reproducible and easy for artists/TDs

### Recommended workflow
- Development/build happens in a conda env (matching Nuke’s major.minor Python)
- We build a wheel (`.whl`) from the repo
- We install that wheel into Nuke’s embedded Python via `-m pip`, along with runtime deps

### Steps

#### 1) Create development environment (conda)
- Match Nuke's Python major/minor (VFX Platform 2024 = Python 3.10)

**Option A: From environment.yml (Recommended)**
```powershell
# Create environment from file
conda env create -f environment-dev.yml
conda activate nk2dl-dev
```

**Option B: Manual creation**
```powershell
conda create -n nk2dl-dev python=3.10 -y
conda activate nk2dl-dev
python -m pip install -U pip build
# Install dev extras for tests/lint/type-checks
python -m pip install -e .[dev]
```

**Required environment files:**

`environment.yml` (runtime-only):
```yaml
name: nk2dl
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - pip:
    - pyyaml>=6.0.1
```

`environment-dev.yml` (development):
```yaml
name: nk2dl-dev
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - pytest>=7.4.0
  - black>=23.7.0
  - flake8>=6.1.0
  - isort>=5.12.0
  - mypy>=1.5.1
  - pip:
    - pyyaml>=6.0.1
    - pytest-cov>=4.1.0
    - types-PyYAML>=6.0.12.12
    - build
```

#### 2) Build distribution artifacts (wheel)
```powershell
python -m build  # creates dist\*.whl and *.tar.gz
```

#### 3) Install into Nuke's embedded Python

**Windows (PowerShell):**
```powershell
# Auto-detect Nuke installation or set manually
$NUKE_PY = & python scripts/find_nuke_python.py --platform windows
# Or manually: $NUKE_PY = "C:\Program Files\Nuke15.2v1\python.exe"

# Verify Nuke Python version compatibility
& $NUKE_PY --version  # Should show Python 3.10.x

# Setup pip in Nuke's Python
& $NUKE_PY -m ensurepip --upgrade
& $NUKE_PY -m pip install -U pip

# Install nk2dl wheel (runtime-only dependencies)
& $NUKE_PY -m pip install --no-deps dist\nk2dl-0.1.9-alpha-py3-none-any.whl

# Install runtime dependencies
& $NUKE_PY -m pip install pyyaml>=6.0.1

# Copy Deadline API (still required)
python scripts/setup_deadline_api.py --nuke-python $NUKE_PY
```

**macOS (Bash):**
```bash
# Auto-detect Nuke installation
NUKE_BIN=$(python scripts/find_nuke_python.py --platform macos)
# Or manually: NUKE_BIN="/Applications/Nuke15.2v1/Nuke15.2v1.app/Contents/MacOS/Nuke15.2"

# Verify compatibility
"$NUKE_BIN" -t -c "import sys; print(sys.version)"

# Setup pip and install
"$NUKE_BIN" -t -m ensurepip --upgrade
"$NUKE_BIN" -t -m pip install -U pip
"$NUKE_BIN" -t -m pip install --no-deps dist/nk2dl-0.1.9-alpha-py3-none-any.whl
"$NUKE_BIN" -t -m pip install pyyaml>=6.0.1

# Setup Deadline API
python scripts/setup_deadline_api.py --nuke-python "$NUKE_BIN -t"
```

**Linux (Bash):**
```bash
# Auto-detect or set manually
NUKE_BIN=$(python scripts/find_nuke_python.py --platform linux)
# Or manually: NUKE_BIN="/usr/local/Nuke15.2v1/Nuke15.2"

# Setup and install (same pattern as macOS)
"$NUKE_BIN" -t -m ensurepip --upgrade
"$NUKE_BIN" -t -m pip install -U pip
"$NUKE_BIN" -t -m pip install --no-deps dist/nk2dl-0.1.9-alpha-py3-none-any.whl
"$NUKE_BIN" -t -m pip install pyyaml>=6.0.1

python scripts/setup_deadline_api.py --nuke-python "$NUKE_BIN -t"
```

### Optional workflows

#### Editable dev directly into Nuke’s Python
- For quick iteration (not recommended for production deploys):
```powershell
& $NUKE_PY -m pip install -e .[dev]
```

#### Offline/controlled dependencies
- Pre-resolve deps in conda, then ship a wheelhouse to Nuke’s Python
```powershell
mkdir wheelhouse
python -m pip download -r requirements.txt -d wheelhouse
& $NUKE_PY -m pip install --no-index --find-links=wheelhouse -r requirements.txt
```

#### PYTHONPATH approach (no install)
- For pure-Python testing you can rely on PYTHONPATH; less reproducible
```powershell
conda activate nk2dl-dev
$Env:PYTHONPATH = "$PWD\src;$Env:PYTHONPATH"
Start-Process "C:\Program Files\Nuke15.1v3\Nuke15.1.exe"
```

### Helper Scripts Required

The plan references several helper scripts that need to be created:

#### `scripts/find_nuke_python.py`
Auto-detects Nuke installations and returns the correct Python executable path:
- Windows: `C:\Program Files\Nuke{version}\python.exe`
- macOS: `/Applications/Nuke{version}/Nuke{version}.app/Contents/MacOS/Nuke{version}`
- Linux: `/usr/local/Nuke{version}/Nuke{version}` or `/opt/Nuke{version}/Nuke{version}`

#### `scripts/setup_deadline_api.py`
Improved version of current Deadline API setup:
- Finds Deadline repository automatically
- Copies Deadline API to target Python's site-packages
- Handles permissions and path issues
- Validates API installation

#### `scripts/validate_installation.py`
Validates the installation in Nuke's Python:
- Tests `import nk2dl` succeeds
- Verifies version matches built wheel
- Tests basic functionality (config loading, etc.)
- Can be run in Nuke terminal mode

### Validation and Testing

#### 4) Validate Installation
After installation, validate that nk2dl works correctly in Nuke:

```powershell
# Test import in Nuke's Python (terminal mode)
& $NUKE_PY -c "import nk2dl; print(f'nk2dl version: {nk2dl.__version__}')"

# Run validation script
python scripts/validate_installation.py --nuke-python $NUKE_PY

# Test in Nuke GUI (manual)
# 1. Launch Nuke GUI
# 2. Open Script Editor
# 3. Run: import nk2dl; print(nk2dl.__version__)
```

#### 5) Integration Testing
Test with actual Nuke scripts:

```powershell
# Set up test environment
$ENV:NUKE_PATH = "$PWD\tests\nukescripts"

# Test script submission
& $NUKE_PY -t tests/test_nk2dl.py
```

### Deployment Strategies

#### Single User Deployment
- Install directly into user's Nuke Python environment
- Suitable for individual artists/TDs
- Easy to update and manage

#### Studio-wide Deployment
- Install into shared Nuke installation
- Use network-accessible wheel repository
- Consider version locking for stability
- Automate via deployment scripts

#### Notes
- Use Nuke's Python for installation and runtime to guarantee importability inside Nuke
- Keep runtime dependencies minimal; only PyYAML is required
- Version is sourced from `src/nk2dl/info.py`; wheel version should match runtime banners
- Deadline API still requires manual copying (not pip-installable)
- Test across all target Nuke versions before deployment

### Answered Questions (Previously Open)

#### Supported Nuke Versions and Paths
**Target Matrix:**
- **Nuke 15.1+**: Required for Graph Scope Variables support
- **Python 3.10**: VFX Platform 2024 standard
- **Platforms**: Windows (primary), Linux, macOS

**Standard Installation Paths:**
- Windows: `C:\Program Files\Nuke{version}\`
- macOS: `/Applications/Nuke{version}/Nuke{version}.app/`
- Linux: `/usr/local/Nuke{version}/` or `/opt/Nuke{version}/`

#### Helper Script for Nuke Detection
**Answer: Yes** - `scripts/find_nuke_python.py` will:
- Scan standard installation directories
- Parse version information
- Return compatible Python executable path
- Support override via environment variables

#### Private Wheel Index
**Answer: Optional** - For studios wanting controlled deployments:
- Can use `devpi`, `Artifactory`, or simple file server
- Enables `pip install nk2dl` directly in Nuke Python
- Supports version pinning and rollback
- Not required for basic installation workflow

### Implementation Roadmap

#### Phase 1: Core Environment (Week 1)
- [ ] Create `environment.yml` and `environment-dev.yml` files
- [ ] Update `requirements.txt` to runtime-only dependencies
- [ ] Create `scripts/find_nuke_python.py`
- [ ] Test conda environment creation and wheel building

#### Phase 2: Installation Scripts (Week 2)
- [ ] Create `scripts/setup_deadline_api.py`
- [ ] Create `scripts/validate_installation.py`
- [ ] Create unified installation script wrapping all steps
- [ ] Test on Windows with Nuke 15.2

#### Phase 3: Cross-Platform Support (Week 3)
- [ ] Test and refine macOS support
- [ ] Test and refine Linux support
- [ ] Document platform-specific requirements
- [ ] Create platform-specific installation guides

#### Phase 4: Documentation and CI (Week 4)
- [ ] Update `docs/installation.md` with conda workflow
- [ ] Create CI/CD pipeline for wheel building
- [ ] Add automated testing with Nuke Python
- [ ] Create deployment documentation for studios

### Success Criteria
- [ ] Conda environment creates successfully on all platforms
- [ ] Wheel builds without errors from conda environment
- [ ] Installation into Nuke Python succeeds
- [ ] `import nk2dl` works in Nuke GUI and terminal mode
- [ ] All existing tests pass in new environment
- [ ] Documentation is clear and complete

### Migration from Current venv Setup
For existing users:
1. Backup current `.venv` directory
2. Install conda if not already available
3. Create new conda environment using `environment-dev.yml`
4. Rebuild wheels and test installation
5. Update documentation bookmarks and procedures
