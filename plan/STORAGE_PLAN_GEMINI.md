# Storage Plan (Gemini)

## 1. Core Principles

This plan is guided by three principles:

1.  **Data-Driven Design:** The structure, defaults, and types of all settings (job, machine, etc.) will be defined in a single, centralized schema. The code will read this schema to build the UI, validate data, and format it for storage. This makes adding or changing settings trivial and reduces hardcoded strings.
2.  **Simplicity and Clarity:** The storage format will be flat and human-readable. The `NodeSettingsStorage` class will have a clear, minimal API for interacting with the Nuke script's data blob.
3.  **Robustness through Validation:** Every load operation will validate the data against the central schema, automatically applying defaults for missing values and logging warnings for unrecognized data. This prevents corruption and ensures stability.

## 2. Proposed Architecture

### A. The Central Schema (`constants.py`)

We will define a master `SCHEMA` dictionary in `nk2dl.gui.panel.constants`. This schema becomes the single source of truth for all configurable parameters.

```python
# In nk2dl/gui/panel/constants.py

SCHEMA = {
    'job': {
        'priority': {'default': 50, 'type': int},
        'chunk_size': {'default': 1, 'type': int},
        'frames': {'default': '1-100', 'type': str},
        'use_nuke_x': {'default': False, 'type': bool},
        'batch_mode': {'default': True, 'type': bool},
        # ... all other job settings
    },
    'machine': {
        'pool': {'default': 'none', 'type': str},
        'group': {'default': 'none', 'type': str},
        'ram_use': {'default': 8192, 'type': int},
        # ... all other machine settings
    },
    'extra': {
        'job_name': {'default': '{script}_{write}', 'type': str},
        'batch_name': {'default': '{script}', 'type': str},
        # ... all other extra settings
    },
    'ui': {
        'column_widths': {'default': {}, 'type': dict},
        'visible_columns': {'default': [], 'type': list},
        # ... any other UI state
    }
}
```

### B. The Storage Format (YAML v0.2)

The data will be stored in a flat, versioned YAML structure inside the `nk2dl_settings` knob. This moves away from the nested `settings` dictionary for simplicity.

```yaml
version: "0.2"
timestamp: 1700000000.000
# Global settings for the submission
job:
  priority: 50
  chunk_size: 5
  use_nuke_x: true
machine:
  pool: "comp"
  ram_use: 16384
extra:
  batch_name: "My Cool Project"
# UI state, ignored by submission
ui:
  column_widths:
    Priority: 70
    Frames: 150
# Per-node values that override globals
node_overrides:
  Write_Main_v01:
    priority: 80
    pool: "lighting"
  Write_Reflection_v03:
    use_gpu: true
```

### C. The Storage Class (`storage.py`)

The `NodeSettingsStorage` class will be refactored to be schema-aware. It will be responsible for I/O, validation, and migration.

```python
# In nk2dl/gui/panel/repositories/storage.py

class NodeSettingsStorage:
    STORAGE_VERSION = "0.2"

    def __init__(self, schema):
        self._schema = schema
        # ...

    def save_settings(self, data: dict) -> bool:
        """Saves a complete data dictionary to the root knob."""
        # ... validation and yaml.dump logic ...

    def load_settings(self) -> dict:
        """Loads, validates, and migrates settings from the root knob."""
        # 1. Read YAML from knob
        # 2. Check version, run self._migrate(raw_data) if old
        # 3. Validate against schema, apply defaults
        # 4. Return clean, validated data dictionary

    def build_submission_args(self) -> dict:
        """Constructs the kwargs for the NukeSubmission class."""
        # ... loads settings and formats them for submission ...

    def _migrate(self, data: dict) -> dict:
        """Handles migration from older storage versions."""
        # ... logic to convert v0.1 to v0.2 format ...
```

## 3. Parameter Name Alignment & Migration

**The Goal:** The names in the UI, `SCHEMA`, YAML file, and `submission.py` arguments must be identical.

**The Process:**

1.  **Unification:** All existing names will be updated to match the canonical `submission.py` argument names. For example, `use_nukex` becomes `use_nuke_x`. This change will happen in `constants.py`, UI widget object names, and models.
2.  **Migration from v0.1:** The `load_settings` method will detect the old format (which only contains `node_overrides`). The migration logic will:
    *   Create a new v0.2 structure.
    *   Populate the `job`, `machine`, etc., sections with default values from the `SCHEMA`.
    *   Copy the existing `node_overrides` into the new structure.
    *   The next `save_settings` call will transparently overwrite the old data with the new, migrated format.

## 4. Step-by-Step Implementation Plan

1.  **Phase 1: Schema & Storage Foundation**
    *   Create the canonical `SCHEMA` in `constants.py` with all known job, machine, extra, and UI settings, using the final, submission-aligned names.
    *   Refactor `NodeSettingsStorage` to implement the new `save_settings` and `load_settings` methods.
    *   Implement the schema-based validation and default-value logic within `load_settings`.
    *   Implement the migration path from v0.1 to v0.2.

2.  **Phase 2: UI & Model Refactoring**
    *   Go through all UI panels and settings models.
    *   Rename all widgets and model attributes to match the keys in the `SCHEMA`.
    *   Update controllers to call the new `storage.load_settings()` and `storage.save_settings()` methods, passing the entire data dictionary.

3.  **Phase 3: Submission Integration**
    *   Update the submission entry point to use `storage.build_submission_args()`. This method will load the settings and correctly format the `node_overrides` into the list of dictionaries required by `NukeSubmission`.

4.  **Phase 4: Testing**
    *   Write unit tests for `NodeSettingsStorage`:
        *   Test save/load roundtrip.
        *   Test that loading a file with missing keys correctly applies defaults from the schema.
        *   Test the v0.1 -> v0.2 migration path.
        *   Test `build_submission_args` output.
    *   Perform manual UI testing to confirm state is saved and loaded correctly across script reloads.

## 5. Benefits of this Approach

*   **Maintainability:** Adding a new setting is a one-line change in the `SCHEMA`. All other code (storage, validation, defaults) adapts automatically.
*   **Reliability:** Centralized schema validation prevents malformed data from being loaded or saved.
*   **Clarity:** The code has a single, authoritative source for what constitutes a "setting," eliminating confusion and duplicate definitions.
*   **Direct Mapping:** Achieves the core goal of a zero-translation pipeline from UI to submission. 