## Environment setup and deployment plan (Conda + Nuke Python)

Status: Proposal (do not implement yet)
Owner: Pipeline

### Goal
- Use conda for development and packaging
- Use Nuke’s embedded Python executable for installation and runtime, guaranteeing that nk2dl is available inside Nuke

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
- Match Nuke’s Python major/minor (example uses 3.10)
```powershell
conda create -n nk2dl-dev python=3.10 -y
conda activate nk2dl-dev
python -m pip install -U pip build
# Optional: install dev extras for tests/lint/type-checks
python -m pip install -e .[dev]
```

#### 2) Build distribution artifacts (wheel)
```powershell
python -m build  # creates dist\*.whl and *.tar.gz
```

#### 3) Install into Nuke’s embedded Python (Windows)
- Adjust the path for your installed Nuke version/build
```powershell
$NUKE_PY = "C:\Program Files\Nuke15.1v3\python.exe"
& $NUKE_PY -m ensurepip --upgrade
& $NUKE_PY -m pip install -U pip
& $NUKE_PY -m pip install --no-deps dist\nk2dl-0.1.9a0-py3-none-any.whl
& $NUKE_PY -m pip install -r requirements.txt
```

#### 3) Install into Nuke’s embedded Python (macOS)
```bash
NUKE_BIN="/Applications/Nuke15.1v3/Nuke15.1v3.app/Contents/MacOS/Nuke15.1"
"$NUKE_BIN" -t -m ensurepip --upgrade
"$NUKE_BIN" -t -m pip install -U pip
"$NUKE_BIN" -t -m pip install --no-deps dist/nk2dl-0.1.9a0-py3-none-any.whl
"$NUKE_BIN" -t -m pip install -r requirements.txt
```

#### 3) Install into Nuke’s embedded Python (Linux)
```bash
NUKE_BIN="/usr/local/Nuke15.1v3/Nuke15.1"
"$NUKE_BIN" -t -m ensurepip --upgrade
"$NUKE_BIN" -t -m pip install -U pip
"$NUKE_BIN" -t -m pip install --no-deps dist/nk2dl-0.1.9a0-py3-none-any.whl
"$NUKE_BIN" -t -m pip install -r requirements.txt
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

### Notes
- Use Nuke’s Python for installation and runtime to guarantee importability inside Nuke
- Keep `requirements.txt` slim; compiled deps may require platform-specific handling
- Version is sourced from `src/nk2dl/info.py`; wheel version should match runtime banners

### Open questions
- Which Nuke versions and install paths do we need to support (matrix)?
- Do we want a helper script to locate Nuke’s python automatically per platform?
- Do we want to host a private wheel index (e.g., Artifactory) for controlled deployments?

### Next steps (when ready)
- Pilot the workflow on Windows for a single Nuke version
- Validate import inside Nuke (GUI and terminal `-t`)
- Document studio-specific Nuke paths; add CI to build wheels on tags
