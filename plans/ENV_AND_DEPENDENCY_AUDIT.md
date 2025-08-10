## Environment and dependencies audit

Date: 2025-08-10
Status: Findings and recommendations only (no code changes)

### Scope
- `setup_environment.py`
- `requirements.txt`
- `docs/_sphinx/requirements.txt`
- Runtime imports across `src/nk2dl/` and tests

### Summary of findings
- **Runtime deps actually used by code**: `PyYAML` (imported as `yaml`), optional `psutil` (GUI-detection convenience), external environment modules `nuke` and `Deadline.*` (provided by Nuke/Deadline installs, not pip-installed).
- **requirements.txt currently mixes runtime and dev/test tools** (pytest, black, flake8, isort, mypy, types-PyYAML).
- **psutil availability**: Confirmed present in Nuke’s embedded Python. Since import is optional and guarded, we do not need to list `psutil` in `requirements.txt` or as an extra.
- **setup_environment.py version mismatch**: hard-codes Python 3.11 paths while project targets VFX Platform 2024+ (Python 3.10). This affects Unix/Mac site-packages path and the script header text.
- **setup_environment.py hardcodes site-packages paths** (e.g., `lib/python3.11/site-packages`) instead of resolving dynamically from the venv’s interpreter.
- **`--system-site-packages`** is used when creating venvs; can cause conflicts/leakage from system-wide packages.
- **Docs deps** are properly isolated in `docs/_sphinx/requirements.txt`.

### Detailed analysis
- Runtime imports in `src/nk2dl`:
  - `yaml` (PyYAML) in `config.py` and tests → REQUIRED runtime dep
  - `psutil` in `submission.py` (inside try/except) → OPTIONAL; present in Nuke; handled gracefully if missing in non-Nuke runs
  - `Deadline.*` and `nuke` in `connection.py`, `nuke_utils.py` → Provided by external installs (Deadline/Nuke), not to be pip-installed
  - Otherwise stdlib (`subprocess`, `pathlib`, `typing`, `json`, `re`, etc.)
- Tests/dev-only imports:
  - `pytest`, `pytest-cov`, `mypy`, `types-PyYAML`, `black`, `flake8`, `isort` (pytest brings its own transitive deps)
- Deadline plugin file (`src/deadline_plugins/Nuke/Nuke.py`) uses .NET/Deadline stack and `six.moves`; executed in Deadline’s environment; do not add `six` to core requirements.

### Recommendations
- Requirements hygiene
  - Split into:
    - `requirements.txt` (runtime):
      - `pyyaml>=6.0.1`
      - Do NOT list `psutil` (present in Nuke; optional import already guarded)
    - `requirements-dev.txt` (dev/test):
      - `pytest`, `pytest-cov`, `black`, `flake8`, `isort`, `mypy`, `types-PyYAML` (omit pytest’s transitive deps)
    - Keep `docs/_sphinx/requirements.txt` as-is
  - In packaging (`setup.py`): keep `install_requires=["pyyaml>=6.0.1"]`; no need to add a `psutil` extra.
- Optional dependency handling
  - Leave current optional `psutil` import in place for improved detection. In non-Nuke contexts where `psutil` is unavailable, the code already logs a warning and continues.
- setup_environment.py
  - Align to Python 3.10 for VFX Platform 2024; avoid hardcoded `python3.11` anywhere.
  - Compute venv site-packages dynamically via the venv’s interpreter (e.g., `python -c "import site; print(site.getsitepackages()[0])"`) for both Windows/Unix paths.
  - Consider dropping `--system-site-packages` to reduce leakage, unless there is a specific studio need.
  - Keep copying Deadline API into venv only if required for standalone scripts; otherwise prefer relying on `DEADLINE_REPOSITORY_ROOT` and `DEADLINE_PATH` for discovery.
- CI/dev workflow
  - If adopting pip/conda workflows later (see `ENVIRONMENT_SETUP_WITH_CONDA_AND_NUKE_PYTHON.md`), ensure dev installs use `requirements-dev.txt`, while runtime installs (into Nuke’s Python) use `requirements.txt` only.

### Proposed clean lists
- Runtime (minimal):
  - `pyyaml>=6.0.1`
- Dev/test:
  - `pytest>=7.4.0`
  - `pytest-cov>=4.1.0`
  - `black>=23.7.0`
  - `flake8>=6.1.0`
  - `isort>=5.12.0`
  - `mypy>=1.5.1`
  - `types-PyYAML>=6.0.12.12`
- Docs:
  - `sphinx`, `sphinx-rtd-theme`, `sphinx-autodoc-typehints` (already isolated)

### Action items (no code changes yet)
- Create `requirements-dev.txt` and move dev/test tools into it (leave `requirements.txt` minimal).
- Do not add `psutil` to requirements or extras; document its optional usage where relevant.
- Update `setup_environment.py` plan to:
  - Resolve site-packages dynamically
  - Remove 3.11 assumptions; target Python 3.10 per VFX 2024
  - Consider removing `--system-site-packages`
- Update docs to clarify which requirements file to use in each context (runtime vs dev vs docs vs Nuke install).

### Notes
- External modules `nuke` and `Deadline.*` must remain out of pip requirements as they are provided by their respective vendor installations.
- Keeping runtime dependencies minimal reduces risk in embedded Nuke Python environments.
