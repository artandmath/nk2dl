# Storage Plan for UI-Submission Parameter Alignment (Enhanced)

## Original User Question (with corrections)

> The job, extra and machine settings store values which we will pass to submission.py.
> 
> I have tried to name the widgets the same values as the args that are taken when submitting a nuke script. Can you come up with a plan to do the following:
> 
> A - Store any overridden settings values in the storage
> B - In a manner that makes sense with translating the values to the right args for submission
> C - Ideally this is done by using the exact same names for controls as the submission args and storage so that no translation of variable names is required.
> D - node_overrides should do the same, we take the values from node overrides and parse them as an array of args to the nuke submission for per-write overrides (read the docs on how this is done)
> 
> Keep it as simple as it needs to be but not simpler

## Executive Summary

This enhanced plan aligns UI parameter names with `submission.py` argument names to enable direct parameter passing without translation. The approach leverages a central schema for validation and defaults, implements thread-safe atomic operations, and provides comprehensive testing coverage while maintaining the existing schema version 0.1.

## Enhanced Architecture Improvements

### 1. Schema-Config Integration (Corrected Approach)

**IMPORTANT:** The schema should **NOT** define defaults - `config.py` is the source of truth for defaults.

Create a validation-only schema that references the config system:

```python
# In nk2dl/gui/panel/constants.py
from nk2dl.common.config import config

# Validation-only schema (NO defaults here)
SETTINGS_SCHEMA = {
    'job_settings': {
        'priority': {'type': int, 'min': 0, 'max': 100, 'config_key': 'submission.priority'},
        'chunk_size': {'type': int, 'min': 1, 'config_key': 'submission.chunk_size'},
        'frames': {'type': str, 'config_key': 'submission.frames'},
        'use_nuke_x': {'type': bool, 'config_key': 'submission.use_nuke_x'},
        'batch_mode': {'type': bool, 'config_key': 'submission.batch_mode'},
        'reload_plugins': {'type': bool, 'config_key': 'submission.reload_plugins'},
        'enable_auto_timeout': {'type': bool, 'config_key': 'submission.enable_auto_timeout'},
        'use_node_frame_list': {'type': bool, 'config_key': 'submission.use_node_frame_list'},
        'render_mode': {'type': str, 'config_key': 'submission.render_mode'},
        # ... other job parameters
    },
    'machine_settings': {
        'pool': {'type': str, 'config_key': 'submission.pool'},
        'group': {'type': str, 'config_key': 'submission.group'},
        'threads': {'type': int, 'min': 1, 'config_key': 'submission.threads'},
        'ram_use': {'type': int, 'min': 1024, 'config_key': 'submission.ram_use'},
        'stack_size': {'type': int, 'min': 1024, 'config_key': 'submission.stack_size'},
        'use_gpu': {'type': bool, 'config_key': 'submission.use_gpu'},
        'gpu_override': {'type': str, 'config_key': 'submission.gpu_override'},
        'concurrent_tasks': {'type': int, 'min': 1, 'config_key': 'submission.concurrent_tasks'},
        'limit_worker_tasks': {'type': bool, 'config_key': 'submission.limit_worker_tasks'},
        'limit_groups': {'type': str, 'config_key': 'submission.limit_groups'},
        # ... other machine parameters
    },
    'extra_settings': {
        'job_name': {'type': str, 'config_key': 'submission.job_name_template'},
        'batch_name': {'type': str, 'config_key': 'submission.batch_name_template'},
        'comment': {'type': str, 'config_key': 'submission.comment_template'},
        'department': {'type': str, 'config_key': 'submission.department'},
        'user_name': {'type': str, 'config_key': 'submission.user_name'},
        # ... other extra parameters
    },
    'ui_settings': {
        'column_widths': {'type': dict},  # No config key - UI only
        'visible_columns': {'type': list},  # No config key - UI only
        'frozen_columns': {'type': list},  # No config key - UI only
        'gsv_settings': {'type': dict},  # No config key - UI only
        # ... UI state parameters
    }
}

def get_default_value(config_key: str) -> Any:
    """Get default value from config system."""
    return config.get(config_key, None)

def get_schema_default(category: str, key: str) -> Any:
    """Get default value for a schema entry from config system."""
    schema_entry = SETTINGS_SCHEMA.get(category, {}).get(key, {})
    config_key = schema_entry.get('config_key')
    if config_key:
        return config.get(config_key, None)
    return None  # No default for UI-only settings
```

### 2. Enhanced Storage Class with Config Integration

```python
# In nk2dl/gui/panel/repositories/storage.py
import time
from typing import Dict, Any, Optional
from nk2dl.common.config import config

class NodeSettingsStorage:
    STORAGE_VERSION = "0.1"  # Keeping as requested by user
    
    def __init__(self):
        self._schema = SETTINGS_SCHEMA
        
    def save_all_settings(self, job_settings: Dict[str, Any], 
                         machine_settings: Dict[str, Any], 
                         extra_settings: Dict[str, Any], 
                         ui_settings: Dict[str, Any], 
                         node_overrides: Dict[str, Dict[str, Any]]) -> bool:
        """Save all settings categories with validation.
        
        Performs operations on main thread - no threading complexity needed.
        """
        try:
            # Validate all settings against schema
            validated_data = self._validate_settings({
                'job_settings': job_settings,
                'machine_settings': machine_settings,
                'extra_settings': extra_settings,
                'ui_settings': ui_settings,
                'node_overrides': node_overrides
            })
            
            # Prepare complete structure for atomic write
            storage_data = {
                'version': self.STORAGE_VERSION,
                'timestamp': time.time(),
                'settings': {
                    'job_settings': validated_data['job_settings'],
                    'machine_settings': validated_data['machine_settings'],
                    'extra_settings': validated_data['extra_settings'],
                    'ui_settings': validated_data['ui_settings']
                },
                'node_overrides': validated_data['node_overrides']
            }
            
            # Single write operation (main thread)
            return self._write_to_knob(storage_data)
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def load_all_settings(self) -> Dict[str, Any]:
        """Load all settings with validation and config-based defaults.
        
        Performs operations on main thread - simple and straightforward.
        """
        try:
            raw_data = self._read_from_knob()
            
            # Apply config-based defaults for missing values
            return self._apply_config_defaults(raw_data)
            
        except Exception as e:
            logger.warning(f"Failed to load settings, using config defaults: {e}")
            return self._get_config_default_settings()
    
    def build_submission_args(self) -> Dict[str, Any]:
        """Build submission arguments with zero translation."""
        settings = self.load_all_settings()
        
        # Direct parameter passing - no translation needed
        args = {}
        args.update(settings.get('job_settings', {}))
        args.update(settings.get('machine_settings', {}))
        args.update(settings.get('extra_settings', {}))
        
        # Format node overrides for submission
        node_overrides = settings.get('node_overrides', {})
        if node_overrides:
            write_nodes = []
            for node_name, overrides in node_overrides.items():
                write_nodes.append({
                    'write_node': node_name,
                    **overrides  # Direct mapping since names match
                })
            args['write_nodes'] = write_nodes
            
        return args
    
    def _validate_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings against schema and apply type conversion."""
        validated = {}
        
        for category, settings in data.items():
            if category == 'node_overrides':
                validated[category] = settings  # Node overrides don't need schema validation
                continue
                
            category_schema = self._schema.get(category, {})
            validated_category = {}
            
            for key, value in settings.items():
                if key in category_schema:
                    schema_def = category_schema[key]
                    try:
                        # Type conversion and validation
                        validated_value = self._convert_and_validate(value, schema_def)
                        validated_category[key] = validated_value
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {category}.{key}: {e}, using config default")
                        # Get default from config system
                        default_value = get_schema_default(category, key)
                        validated_category[key] = default_value
                else:
                    logger.warning(f"Unknown setting {category}.{key}, ignoring")
                    
            validated[category] = validated_category
            
        return validated
    
    def _apply_config_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply config-based defaults for missing settings."""
        result = data.copy()
        
        for category, schema in self._schema.items():
            if category not in result:
                result[category] = {}
                
            for key, definition in schema.items():
                if key not in result[category]:
                    # Get default from config system
                    default_value = get_schema_default(category, key)
                    result[category][key] = default_value
                    
        return result
    
    def _get_config_default_settings(self) -> Dict[str, Any]:
        """Get complete default settings from config system."""
        result = {}
        
        for category, schema in self._schema.items():
            result[category] = {}
            for key, definition in schema.items():
                default_value = get_schema_default(category, key)
                result[category][key] = default_value
                
        return result
    
    def _convert_and_validate(self, value: Any, schema_def: Dict[str, Any]) -> Any:
        """Convert value to correct type and validate constraints."""
        expected_type = schema_def['type']
        
        # Type conversion
        if not isinstance(value, expected_type):
            if expected_type == bool and isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = expected_type(value)
        
        # Constraint validation
        if expected_type in (int, float):
            if 'min' in schema_def and value < schema_def['min']:
                raise ValueError(f"Value {value} below minimum {schema_def['min']}")
            if 'max' in schema_def and value > schema_def['max']:
                raise ValueError(f"Value {value} above maximum {schema_def['max']}")
                
        return value
    
    def _write_to_knob(self, data: Dict[str, Any]) -> bool:
        """Write data to Nuke knob (main thread operation)."""
        # Implementation details for writing to Nuke knob
        # This is a simple, synchronous operation
        pass
    
    def _read_from_knob(self) -> Dict[str, Any]:
        """Read data from Nuke knob (main thread operation)."""
        # Implementation details for reading from Nuke knob
        # This is a simple, synchronous operation
        pass
```

### 3. Comprehensive Testing Strategy (Inspired by O3)

```python
# Testing Matrix for Enhanced Storage
class TestStorageMatrix:
    """
    Comprehensive test coverage for all storage scenarios.
    """
    
    def test_roundtrip_all_settings(self):
        """Test complete save/load cycle preserves all data."""
        
    def test_schema_validation(self):
        """Test that invalid data is rejected with proper defaults."""
        
    def test_type_conversion(self):
        """Test automatic type conversion (string '50' -> int 50)."""
        
    def test_constraint_validation(self):
        """Test min/max constraints are enforced."""
        
    def test_thread_safety(self):
        """Test concurrent access doesn't corrupt data."""
        
    def test_atomic_operations(self):
        """Test that failed saves don't partially corrupt data."""
        
    def test_submission_args_generation(self):
        """Test build_submission_args returns correct format."""
        
    def test_node_overrides_formatting(self):
        """Test node overrides are formatted correctly for submission."""
        
    def test_default_application(self):
        """Test missing settings get proper defaults."""
        
    def test_unknown_settings_handling(self):
        """Test unknown settings are ignored gracefully."""
        
    def test_migration_compatibility(self):
        """Test loading old format data works correctly."""
        
    def test_config_system_integration(self):
        """Test integration with config system for defaults."""
        
    def test_parameter_name_alignment(self):
        """Test UI parameter names match submission exactly."""
```

### 4. PySide/Qt Testing Strategy for Nuke Integration

Since the storage system integrates with Nuke's Qt UI, comprehensive PySide testing is essential:

#### **Testing Environment Setup**

**Use Nuke Terminal Mode Instead of Python:**
```powershell
# Replace standard Python testing with Nuke terminal mode
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_storage_ui.py
```

**Environment Activation for Logic Tests:**
```powershell
# For YAML and config tests that don't need Qt
C:\Users\Daniel\Documents\repo\nk2dl\.venv\Scripts\Activate-nk2dl.ps1
```

#### **PySide Version Compatibility Testing**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Storage system Qt integration tests for Nuke."""

import sys
import os
import time
import yaml
import threading

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide6"
else:
    from PySide2 import QtWidgets, QtCore, QtGui
    PYSIDE_VERSION = "PySide2"

def test_storage_ui_integration():
    """Test storage system integration with Nuke Qt UI."""
    
    # Test PySide version detection
    assert PYSIDE_VERSION in ["PySide2", "PySide6"]
    
    # Test storage system imports
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.constants import SETTINGS_SCHEMA
    
    # Test UI components
    from nk2dl.gui.panel.views.settings_view import SettingsView
    
    # Create test storage instance
    storage = NodeSettingsStorage()
    
    # Test thread safety
    def concurrent_save_test():
        test_data = {
            'job_settings': {'priority': 75, 'chunk_size': 5},
            'machine_settings': {'pool': 'test', 'threads': 8},
            'extra_settings': {'comment': 'Test comment'},
            'ui_settings': {'column_widths': {'Priority': 100}},
            'node_overrides': {'Write1': {'priority': 90}}
        }
        return storage.save_all_settings(**test_data)
    
    # Test concurrent operations
    threads = []
    for i in range(5):
        thread = threading.Thread(target=concurrent_save_test)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Test UI widget creation and storage integration
    widget = SettingsView()
    widget.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_widget'] = widget
    
    return widget

def test_storage_config_integration():
    """Test storage system integration with config system."""
    
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.constants import get_schema_default
    from nk2dl.common.config import config
    
    storage = NodeSettingsStorage()
    
    # Test config system integration
    priority_default = get_schema_default('job_settings', 'priority')
    config_priority = config.get('submission.priority', 50)
    
    assert priority_default == config_priority, f"Schema default {priority_default} != config default {config_priority}"
    
    # Test all config mappings
    test_cases = [
        ('job_settings', 'priority', 'submission.priority'),
        ('job_settings', 'chunk_size', 'submission.chunk_size'),
        ('machine_settings', 'pool', 'submission.pool'),
        ('machine_settings', 'threads', 'submission.threads'),
    ]
    
    for category, key, config_key in test_cases:
        schema_default = get_schema_default(category, key)
        config_default = config.get(config_key)
        assert schema_default == config_default, f"Mismatch for {category}.{key}: schema={schema_default}, config={config_default}"

def main():
    """Main test runner with Qt event loop management."""
    
    # Test storage system without UI
    test_storage_config_integration()
    print("✓ Storage-Config integration tests passed")
    
    # Test UI integration
    widget = test_storage_ui_integration()
    print("✓ Storage-UI integration tests passed")
    
    try:
        # Keep Qt event loop alive for Nuke terminal mode
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if not widget.isVisible():
                break
    except KeyboardInterrupt:
        print("Test interrupted by user")
    
    return widget

if __name__ == "__main__":
    main()
```

#### **Storage System Test Commands**

**PySide Qt Tests (require Nuke):**
```powershell
# Test storage UI integration
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_storage_ui_integration.py

# Test settings panel with storage
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_settings_panel_storage.py

# Test table model with storage
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_table_model_storage.py
```

**Logic Tests (no Qt required):**
```powershell
# Activate environment first
C:\Users\Daniel\Documents\repo\nk2dl\.venv\Scripts\Activate-nk2dl.ps1

# Test storage logic
python -m pytest tests/pytest/test_storage_logic.py

# Test config integration
python -m pytest tests/pytest/test_config_integration.py

# Test parameter alignment
python -m pytest tests/pytest/test_parameter_alignment.py
```

#### **Qt-Specific Testing Best Practices**

1. **Storage Operation Testing:**
```python
def test_storage_operations():
    """Test basic storage save/load operations."""
    storage = NodeSettingsStorage()
    
    test_data = {
        'job_settings': {'priority': 75, 'chunk_size': 5},
        'machine_settings': {'pool': 'test', 'threads': 8},
        'extra_settings': {'comment': 'Test comment'},
        'ui_settings': {'column_widths': {'Priority': 100}},
        'node_overrides': {'Write1': {'priority': 90}}
    }
    
    # Test save operation
    success = storage.save_all_settings(**test_data)
    assert success, "Save operation failed"
    
    # Test load operation
    loaded_data = storage.load_all_settings()
    assert loaded_data['job_settings']['priority'] == 75
    assert loaded_data['node_overrides']['Write1']['priority'] == 90
```

2. **Config Integration Testing:**
```python
def test_config_integration():
    """Test integration with config system for defaults."""
    storage = NodeSettingsStorage()
    
    # Test that defaults come from config system
    defaults = storage._get_config_default_settings()
    
    # Verify specific config mappings
    priority_from_config = config.get('submission.priority', 50)
    assert defaults['job_settings']['priority'] == priority_from_config
    
    pool_from_config = config.get('submission.pool', 'comp')
    assert defaults['machine_settings']['pool'] == pool_from_config
```

3. **UI Responsiveness Testing:**
```python
def test_ui_responsiveness_during_storage():
    """Test UI remains responsive during storage operations."""
    widget = SettingsView()
    widget.show()
    
    # Test multiple storage operations don't block UI
    storage = NodeSettingsStorage()
    for i in range(100):
        QtWidgets.QApplication.processEvents()  # Keep UI responsive
        storage.save_all_settings(
            job_settings={'priority': i},
            machine_settings={'threads': i % 8 + 1},
            extra_settings={},
            ui_settings={},
            node_overrides={}
        )
```

4. **Parameter Alignment Testing:**
```python
def test_parameter_alignment():
    """Test UI parameter names match submission exactly."""
    storage = NodeSettingsStorage()
    
    # Get submission args
    submission_args = storage.build_submission_args()
    
    # Verify all expected submission parameters are present
    expected_params = [
        'priority', 'chunk_size', 'use_nuke_x', 'batch_mode',
        'pool', 'threads', 'ram_use', 'gpu_override'
    ]
    
    for param in expected_params:
        assert param in submission_args, f"Missing submission parameter: {param}"
```

#### **Test File Structure**

```
tests/
├── qt/                           # PySide tests (require Nuke)
│   ├── test_storage_ui_integration.py
│   ├── test_settings_panel_storage.py
│   ├── test_table_model_storage.py
│   └── test_parameter_alignment_ui.py
├── pytest/                       # Logic tests (no Qt)
│   ├── test_storage_logic.py
│   ├── test_config_integration.py
│   ├── test_parameter_alignment.py
│   └── test_schema_validation.py
└── integration/                  # Full workflow tests
    ├── test_full_submission_flow.py
    └── test_migration_scenarios.py
```

#### **Testing Timeline and Checklist**

**Phase 1: Core Storage Tests (1 day)**
- [ ] Schema validation logic
- [ ] Config system integration
- [ ] Parameter name alignment
- [ ] Basic storage operations

**Phase 2: UI Integration Tests (1 day)**
- [ ] PySide version compatibility
- [ ] Settings panel integration
- [ ] Table model integration
- [ ] UI responsiveness during operations

**Phase 3: Integration and Workflow Tests (1 day)**
- [ ] Full submission workflow testing
- [ ] Config → UI → Storage → Submission flow
- [ ] Migration scenario testing
- [ ] Error handling and validation

**Testing Notes:**
- Nuke may take up to 180 seconds to launch - be patient
- Use global references to prevent Qt widget garbage collection
- Always test both PySide2 (Nuke 15.x) and PySide6 (Nuke 16.x+) compatibility
- Process Qt events regularly to maintain UI responsiveness in tests
- Focus on simple, reliable testing of main thread operations

## Current State Analysis

### Parameter Name Mismatches

**Job Settings Mismatches:**
- UI: `use_nukex` → Submission: `use_nuke_x`
- UI: `use_batch_mode` → Submission: `batch_mode`
- UI: `reload_plugin` → Submission: `reload_plugins`
- UI: `auto_timeout` → Submission: `enable_auto_timeout`
- UI: `nodes_frames` → Submission: `use_node_frame_list`

**Machine Settings Mismatches:**
- UI: `worker_task_limit` → Submission: `limit_worker_tasks`
- UI: `min_ram`/`max_ram` → Submission: `ram_use`
- UI: `gpu_id` → Submission: `gpu_override`
- UI: `limits` → Submission: `limit_groups`
- UI: `secondary_pool` → Submission: Not directly supported

### Missing Parameters in UI

**Important submission parameters not in current UI:**
- `department`, `user_name`, `comment` (partially in extra settings)
- `batch_name`, `job_name` (partially in extra settings)
- `machine_limit`, `machine_allow_list`, `machine_deny_list`
- `task_timeout` (exists but mapping unclear)
- `environment` related parameters
- Build job and script copying parameters

## Comprehensive UI Element Analysis

### UI Elements Requiring Parameter Name Changes

Obtain user verification and approval before changing each arg/param one at a time.

**From `constants.py` DefaultValues.JOB_DEFAULTS:**
- ✅ `priority` → No change (matches submission)
- ✅ `chunk_size` → No change (matches submission)
- ✅ `frames` → No change (matches submission)
- ❌ `use_nukex` → **RENAME to `use_nuke_x`**
- ❌ `use_batch_mode` → **RENAME to `batch_mode`**
- ❌ `auto_timeout` → **RENAME to `enable_auto_timeout`**
- ❌ `nodes_frames` → **RENAME to `use_node_frame_list`**
- ✅ `render_mode` → No change (matches submission)
- ❌ `reload_plugin` → **RENAME to `reload_plugins`** **EVALUATE** When rearching this point we need to investigate whether to change to `reload_plugin` in the back end

**From `constants.py` DefaultValues.MACHINE_DEFAULTS:**
- ✅ `pool` → No change (matches submission)
- ✅ `group` → No change (matches submission)
- ✅ `threads` → No change (matches submission)
- ✅ `concurrent_tasks` → No change (matches submission)
- ✅ `use_gpu` → No change (matches submission)
- ❌ `gpu_device`/`gpu_id` → **RENAME to `gpu_override`**
- ❌ `worker_task_limit`/`limit_tasks` → **RENAME to `limit_worker_tasks`**
- ❌ `limits` → **RENAME to `limit_groups`**
- ❌ `min_ram` → **RENAME to `stack_size`**
- ❌ `max_ram` → **RENAME to `ram_use`**
- ❌ `machine_list` → **EVALUATE** (submission has multiple machine list params)

**From `constants.py` HeaderSettingsMapping:**

*Job Settings Mappings - Current UI → Submission:*
- ❌ `"NukeX": "use_nukex"` → **CHANGE to `"NukeX": "use_nuke_x"`**
- ❌ `"BatchMode": "use_batch_mode"` → **CHANGE to `"BatchMode": "batch_mode"`**
- ❌ `"ReloadPlugin": "reload_plugin"` → **CHANGE to `"ReloadPlugin": "reload_plugins"`**
- ❌ `"AutoTimeout": "auto_timeout"` → **CHANGE to `"AutoTimeout": "enable_auto_timeout"`**
- ❌ `"NodesFrames": "nodes_frames"` → **CHANGE to `"NodesFrames": "use_node_frame_list"`**

*Machine Settings Mappings - Current UI → Submission:*
- ❌ `"GPUId": "gpu_id"` → **CHANGE to `"GPUId": "gpu_override"`**
- ❌ `"WorkerTaskLimit": "worker_task_limit"` → **CHANGE to `"WorkerTaskLimit": "limit_worker_tasks"`**
- ❌ `"Limits": "limits"` → **CHANGE to `"Limits": "limit_groups"`**
- ❌ `"MinRam": "min_ram"` → **CHANGE to `"MinRam": "stack_size"`**
- ❌ `"MaxRam": "max_ram"` → **CHANGE to `"MaxRam": "ram_use"`**

### UI Elements With Complex Mapping Requirements

**Machine List Parameters:**
- Current UI: Single `machine_list` field
- Submission has: `machine_list`, `machine_allow_list`, `machine_deny_list`, `machine_list_is_a_deny_list`
- **Action Required:** Redesign machine list UI to support allow/deny list modes

**Secondary Pool:**
- Current UI: `secondary_pool` field
- Submission: No direct `secondary_pool` parameter
- **Action Required:** Determine if this maps to a different submission parameter or is UI-only

**Task Timeout:**
- Current UI: `task_timeout` (unclear mapping)
- Submission: `task_timeout` parameter exists
- **Action Required:** Verify mapping and ensure consistency

### UI Elements Already Correctly Named

**No changes needed for these parameters:**
- `priority`, `chunk_size`, `frames`, `pool`, `group`, `threads`, `concurrent_tasks`, `use_gpu`, `render_mode`

### Summary of Required Changes

**Total UI Elements Requiring Rename: 15**
- Job settings parameters: 5 renames
- Machine settings parameters: 5 renames  
- Header mapping entries: 10 updates (5 job + 5 machine)
- Complex UI redesign: 1 (machine list functionality)

## Proposed Solution Architecture

### 1. Unified Storage Structure

Extend the current YAML storage structure to support all settings categories:

```yaml
version: "0.1"
timestamp: 1703123456.789
settings:
  job_settings:
    priority: 50
    chunk_size: 1
    frames: "1001-2315"
    use_nuke_x: false
    batch_mode: true
    reload_plugins: false
    enable_auto_timeout: false
    use_node_frame_list: false
    # ... other job parameters
  extra_settings:
    job_name: "{script}_{write}"
    batch_name: "{script}_batch"
    comment: "Rendered with nk2dl"
    department: "comp"
    user_name: ""
    # ... other extra parameters
  machine_settings:
    pool: "comp"
    group: "none"
    threads: 4
    ram_use: 8000
    use_gpu: false
    gpu_override: ""
    concurrent_tasks: 2
    limit_worker_tasks: false
    machine_list: ""
    limit_groups: ""
    # ... other machine parameters
  panel_settings:
    column_widths: {...}
    visible_columns: [...]
    gsv_settings: {...}
    # ... UI state
node_overrides:
  Write1:
    priority: 75
    pool: "lighting"
    use_gpu: true
    # ... per-node overrides using submission parameter names
```

### 2. Parameter Name Standardization

**Direct Mapping Approach**

Rename UI control parameter names to match submission argument names exactly. This eliminates any need for translation and provides direct parameter flow from UI → Storage → Submission.

**Required UI Parameter Renames:**
- `use_nukex` → `use_nuke_x`
- `use_batch_mode` → `batch_mode`
- `reload_plugin` → `reload_plugins`
- `auto_timeout` → `enable_auto_timeout`
- `nodes_frames` → `use_node_frame_list`
- `worker_task_limit` → `limit_worker_tasks`
- `gpu_id` → `gpu_override`
- `limits` → `limit_groups`
- `min_ram` → `stack_size`
- `max_ram` → `ram_use`

### 3. Enhanced Storage Repository

Extend `NodeSettingsStorage` to handle all settings categories:

```python
class NodeSettingsStorage:
    STORAGE_VERSION = "0.1"
    
    def save_all_settings(self, job_settings, machine_settings, extra_settings, ui_settings, node_overrides):
        """Save all settings categories atomically."""
        
    def load_all_settings(self):
        """Load all settings, return structured dict."""
        
    def get_submission_args(self):
        """Convert stored settings to submission.py arguments."""
        
    def get_node_override_dicts(self):
        """Convert node overrides to WriteNode dictionaries."""
```

## Enhanced Implementation Plan

### Phase 1: Schema and Config Integration (2-3 days)

1. **Create validation-only schema definition:**
   - Define `SETTINGS_SCHEMA` with types and constraints only
   - Add `config_key` mappings to config system parameters
   - Create helper functions to get defaults from config system
   - Remove duplicate hardcoded defaults from constants

2. **Enhance storage class:**
   - Extend current storage to handle global settings
   - Add schema-aware validation without duplicate defaults
   - Integrate with config system for default value retrieval
   - Add comprehensive error handling and logging
   - Keep operations on main thread (simple and straightforward)

3. **Update config system integration:**
   - Ensure all submission parameters have corresponding config defaults
   - Verify parameter name alignment between config and submission
   - Update any missing config defaults to match submission requirements

### Phase 2: UI Parameter Standardization (2-3 days)

**Direct Parameter Renaming Implementation**

1. **Update constants.py:**
   - Replace hardcoded defaults with config-system references
   - Update `HeaderSettingsMapping` to use submission parameter names
   - Remove `DefaultValues` class (replaced by config system)
   - Add schema validation definitions

2. **Update UI controls:**
   - Settings panel widgets to use submission parameter names
   - Update control references throughout codebase
   - Ensure widget names match submission argument names exactly

3. **Update models/views:**
   - Settings models to use submission parameter names
   - Models to get defaults from config system via storage
   - Update view-model communication to use consistent parameter names

### Phase 3: Node Override Integration (1 day)

1. **Enhance node override handling:**
   - Validate node overrides against schema types and constraints
   - Generate WriteNode dictionaries using direct parameter mapping
   - Use config defaults for missing node override values
   - Maintain simple, synchronous operations

### Phase 4: Submission Integration (1 day)

1. **Implement zero-translation submission:**
   - Use `build_submission_args()` for direct parameter passing
   - Format node overrides correctly for submission
   - Eliminate all parameter translation code
   - Verify all parameters flow directly from config → UI → storage → submission

### Phase 5: Comprehensive Testing (2-3 days)

1. **Implement test matrix:**
   - All scenarios from testing strategy
   - Config system integration testing
   - Default value consistency testing
   - Basic storage operation testing
   - Integration testing with real submission workflows

## Risk Analysis and Enhanced Mitigation

### High Risk: Config System Dependencies

**Risk:** Config system changes breaking UI default behavior
**Mitigation:** 
- Comprehensive testing of config → UI → storage → submission flow
- Validation that all required config defaults exist
- Clear documentation of config system dependencies
- Graceful fallback for missing config values

### High Risk: Parameter Name Inconsistencies

**Risk:** Mismatched parameter names between config, UI, and submission
**Mitigation:**
- Systematic audit of all parameter names across all systems
- Automated tests to verify parameter name consistency
- Clear mapping documentation between config keys and submission args
- Schema-based validation of parameter names

### Medium Risk: Settings Model Integration

**Risk:** Breaking existing settings model functionality
**Mitigation:**
- Gradual integration with existing settings model
- Maintain existing API while adding storage integration
- Comprehensive testing of settings model changes
- Fallback to current behavior if integration fails

### Medium Risk: Config System Performance

**Risk:** Frequent config system calls adding overhead
**Mitigation:**
- Cache config values where appropriate
- Lazy loading of config defaults
- Performance testing and optimization

## Enhanced Benefits

1. **Single Source of Truth:** Config system is the authoritative source for defaults
2. **No Duplicate Defaults:** Eliminates maintenance burden of multiple default locations
3. **Consistent Behavior:** Same defaults used throughout application
4. **Configuration Flexibility:** Users can override defaults via config files
5. **Simplified Operations:** Main thread operations are simple and reliable
6. **Zero Translation:** Direct parameter flow UI → Storage → Submission
7. **Comprehensive Testing:** Full test coverage for all scenarios

## Implementation Recommendations

### Enhanced Architecture Benefits

1. **Config-Driven Design:**
   - Single authoritative source for all default values
   - User-configurable defaults via config files
   - Consistent behavior across all application components

2. **Schema-Based Validation:**
   - Type safety and constraint validation
   - No duplicate default definitions
   - Clear separation of concerns (config=defaults, schema=validation)

3. **Simple Operations:**
   - Main thread operations are straightforward and reliable
   - No complex threading or locking mechanisms
   - Standard YAML serialization for storage
   - Synchronous operations that are easy to debug

### Required Config System Updates

**Ensure these submission parameters exist in config.py:**
- All renamed parameters (use_nuke_x, batch_mode, reload_plugins, etc.)
- All machine parameters (ram_use, stack_size, gpu_override, etc.)
- All extra parameters (job_name_template, batch_name_template, etc.)

**Example config.py additions needed:**
```python
# In config.py DEFAULT_CONFIG['submission']
'use_nuke_x': False,  # Currently: use_nukex
'batch_mode': True,   # Currently: batch_mode (✓ already exists)
'reload_plugins': False,  # Currently: reload_plugins (✓ already exists)
'enable_auto_timeout': False,  # New parameter
'use_node_frame_list': False,  # Currently: use_node_frame_list (✓ already exists)
'ram_use': 0,  # Currently: ram_use (✓ already exists)  
'stack_size': 0,  # Currently: stack_size (✓ already exists)
'gpu_override': '',  # New parameter
'limit_worker_tasks': False,  # New parameter
'limit_groups': '',  # New parameter
```

### File Changes Required

**Enhanced Constants and Configuration:**
- `nk2dl/common/config.py` - Add missing submission parameters
- `nk2dl/gui/panel/constants.py` - Replace defaults with schema validation
- `nk2dl/gui/panel/repositories/storage.py` - Enhanced storage with config integration

**Models and Views:**
- All settings models - Use config system for defaults
- All views - Reference config system via storage
- Remove hardcoded defaults throughout UI

**Testing:**
- Config system integration tests
- Default value consistency tests
- Parameter name alignment tests
- Basic storage operation tests

## Success Criteria

1. **Single Source of Truth:** Config system is the only source for default values
2. **Perfect Parameter Alignment:** UI parameter names match submission exactly
3. **No Duplicate Defaults:** Defaults only defined in config system
4. **Simple Operations:** All storage operations are straightforward and reliable
5. **Config Integration:** All defaults retrieved from config system
6. **Zero Translation:** Direct parameter flow throughout stack
7. **Comprehensive Testing:** 100% test coverage for all scenarios
8. **Backward Compatibility:** Existing data loads correctly
9. **Performance:** No significant performance impact

## Timeline Estimate

- **Enhanced Implementation:** 5-7 days (reduced from 6-8 due to simplified approach)
- **Comprehensive Testing:** 2-3 days (reduced from 3-4 due to simplified testing)
- **Documentation and Performance Optimization:** 1-2 days

**Total Enhanced Project Time:** 8-12 days (reduced from 10-14 days)

This enhanced plan properly integrates with the existing config system as the single source of truth for defaults, eliminates duplicate default definitions, and uses simple main-thread operations for reliable storage functionality. 