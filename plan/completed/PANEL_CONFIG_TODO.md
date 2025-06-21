# NK2DL Panel Configuration Implementation TODO

## Phase 1: Configuration Infrastructure ⚡ HIGH PRIORITY

### 1.1 Extend Default Configuration
- [ ] **File**: `nk2dl/common/config.py`
  - [ ] Add `panel: {}` section to `DEFAULT_CONFIG` dictionary
  - [ ] Verify existing configuration structure remains intact
  - [ ] Test configuration loading with new panel section

### 1.2 Create Panel Configuration Module
- [ ] **File**: `nk2dl/gui/panel/config.py` (NEW FILE)
  - [ ] Implement core configuration constants:
    - [ ] `ESSENTIAL_CONTROLS` set (render_btn, tab_widget, progress_bar, etc.)
    - [ ] `CONTROL_GROUPS` dictionary (job_settings, machine_settings, table_controls, extra_settings)
    - [ ] `_widget_defaults` storage dictionary
  - [ ] Implement main configuration function:
    - [ ] `apply_panel_config(widget, control_name=None)`
    - [ ] Widget default value storage before configuration
    - [ ] Hidden state application
    - [ ] Disabled state application with styling
    - [ ] Default value setting
    - [ ] Enhanced structured tooltip generation with control names and configuration sources
  - [ ] Implement context menu system:
    - [ ] `_add_context_menu(widget, control_name)`
    - [ ] `_show_context_menu(widget, control_name, position)`
    - [ ] Individual control reset: `_reset_control_to_default()`
    - [ ] Group reset: `_reset_group_to_default()`
    - [ ] Panel-wide reset: `_reset_all_to_default()`
  - [ ] Implement utility functions:
    - [ ] `_store_widget_default()` for different widget types
    - [ ] `_set_widget_value()` for different widget types
    - [ ] `_apply_disabled_styling()` for visual feedback
    - [ ] `_get_control_group()` for context menu grouping
    - [ ] `_get_panel_instance()` and `_find_widget_by_name()` for widget discovery
  - [ ] Implement configuration source tracking:
    - [ ] `_get_config_sources()` to identify which config set each value
    - [ ] `_identify_config_source()` to trace precedence
    - [ ] `_config_key_to_env_var()` for environment variable mapping
    - [ ] `_key_exists_in_yaml()` for YAML file checking
    - [ ] `_set_enhanced_tooltip()` with structured format and source attribution
    - [ ] `_get_current_widget_value()` for displaying current widget values
    - [ ] `_get_control_display_name()` for human-readable control names

## Phase 2: Panel Integration ⚡ HIGH PRIORITY

### 2.1 Modify Main Panel Class
- [ ] **File**: `nk2dl/gui/panel/panel.py`
  - [ ] Add import: `from .config import apply_panel_config`
  - [ ] Add `_apply_panel_configuration()` method to `Nk2dlPanel` class
  - [ ] Call configuration method after UI initialization in `__init__()`
  - [ ] Apply configuration to main panel controls:
    - [ ] `render_btn`
    - [ ] `progress_bar` 
    - [ ] `tab_widget`
  - [ ] Delegate to view classes for their controls

### 2.2 Update View Classes
- [ ] **File**: `nk2dl/gui/panel/views.py`
  - [ ] Add import: `from .config import apply_panel_config`
  - [ ] **SettingsView class**:
    - [ ] Add `_apply_configuration()` method
    - [ ] Apply config to job settings controls (15+ controls):
      - [ ] `priority_spin`, `chunk_size_spin`, `frames_combo`, `frame_range_edit`
      - [ ] `use_node_frame_list_check`, `task_timeout_spin`, `enable_auto_timeout_check`
      - [ ] `render_mode_combo`, `render_nukex_check`, `use_batch_mode_check`
      - [ ] `reload_plugin_check`, `separate_tasks_check`, `separate_jobs_check`, `views_separate_jobs_check`
    - [ ] Apply config to machine settings controls (12+ controls):
      - [ ] `pool_combo`, `secondary_pool_combo`, `group_combo`, `threads_spin`
      - [ ] `min_ram_spin`, `max_ram_spin`, `gpu_override_spin`, `use_gpu_check`
      - [ ] `concurrent_tasks_spin`, `limit_tasks_check`, `machine_limit_spin`
      - [ ] `machine_deny_list_check`, `machine_list_edit`, `limits_edit`
  - [ ] **NodeSettingsView class**:
    - [ ] Add `_apply_configuration()` method
    - [ ] Apply config to table controls:
      - [ ] `update_btn`, `all_btn`, `clear_btn`, `selection_btn`
      - [ ] `inside_groups_check`, `column_dropdown`, `filter_edit`

## Phase 3: Widget Naming Audit 📋 MEDIUM PRIORITY

### 3.1 Verify Widget Object Names
- [ ] **Audit existing codebase** for widget `objectName` consistency
  - [ ] Check all widgets have stable `objectName` values
  - [ ] Ensure names match those used in `CONTROL_GROUPS`
  - [ ] Add explicit `setObjectName()` calls where missing

### 3.2 Widget Name Verification
- [ ] **File**: Various view files
  - [ ] Job settings widgets: `priority_spin`, `chunk_size_spin`, etc.
  - [ ] Machine settings widgets: `pool_combo`, `threads_spin`, etc.
  - [ ] Table control widgets: `update_btn`, `all_btn`, etc.
  - [ ] Essential widgets: `render_btn`, `progress_bar`, `tab_widget`

## Phase 4: Testing 🧪 HIGH PRIORITY

### 4.1 Unit Tests
- [ ] **File**: `tests/qt/test_panel_config.py` (NEW FILE)
  - [ ] Test `apply_panel_config()` with mock widgets
  - [ ] Test configuration parsing and precedence
  - [ ] Test environment variable handling
  - [ ] Test essential controls protection
  - [ ] Test widget value setting for different types
  - [ ] Test configuration source tracking
  - [ ] Test context menu functionality

### 4.2 Integration Tests
- [ ] **File**: `tests/qt/test_panel_integration.py` (NEW FILE)
  - [ ] Panel functionality with various config scenarios
  - [ ] Configuration precedence (file vs env vars vs user config)
  - [ ] Widget state verification after configuration
  - [ ] Hidden/disabled widget behavior
  - [ ] Context menu reset functionality
  - [ ] Tooltip generation and display

### 4.3 Manual Testing Scenarios
- [ ] **Create test configurations**:
  - [ ] Artist lockdown config (hide advanced controls)
  - [ ] Default value config (set conservative defaults)
  - [ ] Mixed hidden/disabled config
  - [ ] Environment variable config
- [ ] **Test configuration precedence**:
  - [ ] User config overrides project config
  - [ ] Environment variables override file config
  - [ ] Invalid configurations fail gracefully
- [ ] **Test UI behavior**:
  - [ ] Hidden controls are invisible
  - [ ] Disabled controls are greyed out but visible
  - [ ] Tooltips show configuration sources
  - [ ] Context menus work on all controls
  - [ ] Reset functionality works at all levels

## Phase 5: Documentation 📚 MEDIUM PRIORITY

### 5.1 Configuration Documentation
- [ ] **File**: `docs/config.md`
  - [ ] Add Panel Configuration section
  - [ ] Document all available controls by category
  - [ ] Provide configuration examples (YAML and env vars)
  - [ ] Document essential controls that cannot be configured
  - [ ] Document control groups for context menus
  - [ ] Document tooltip behavior and source attribution

### 5.2 Example Configurations
- [ ] **File**: `examples/panel_configs/` (NEW DIRECTORY)
  - [ ] `artist_lockdown.yaml` - Hide advanced controls
  - [ ] `studio_defaults.yaml` - Set conservative defaults
  - [ ] `development.yaml` - Enable all debugging features
  - [ ] `README.md` - Explain each example configuration

## Phase 6: Deployment & Rollout 🚀 LOW PRIORITY

### 6.1 Backwards Compatibility
- [ ] Verify panel works identically with no configuration
- [ ] Test with existing user configurations
- [ ] Ensure no breaking changes to current behavior

### 6.2 Rollout Strategy
- [ ] **Phase 1**: Merge with empty default config (no behavior change)
- [ ] **Phase 2**: Documentation and examples
- [ ] **Phase 3**: Studio deployment with lockdown configs
- [ ] **Phase 4**: Feedback collection and iteration

## Additional Tasks 🔧

### Error Handling & Robustness
- [ ] Handle missing/invalid widget references gracefully
- [ ] Handle malformed configuration values safely
- [ ] Handle missing configuration files without errors
- [ ] Add logging for configuration application (debug level)

### Code Quality
- [ ] Add type hints throughout config.py
- [ ] Add comprehensive docstrings
- [ ] Follow PEP8 style guidelines
- [ ] Add error handling for PySide2/PySide6 compatibility

### Performance Considerations
- [ ] Minimize configuration overhead during panel startup
- [ ] Cache configuration lookups where appropriate
- [ ] Optimize widget discovery for large panels

## Dependencies & Prerequisites

### Required Files to Examine/Modify
- [ ] `nk2dl/common/config.py` - Understand existing config system
- [ ] `nk2dl/gui/panel/panel.py` - Main panel class structure
- [ ] `nk2dl/gui/panel/views.py` - View classes and widget references
- [ ] Any existing test files for patterns

### External Dependencies
- [ ] Verify PySide2/PySide6 compatibility
- [ ] Check PyYAML availability for config source tracking
- [ ] Ensure Qt context menu functionality works as expected

## Estimated Timeline
- **Day 1**: Phase 1 (Configuration Infrastructure) 
- **Day 2**: Phase 2 (Panel Integration)
- **Day 3**: Phase 3 (Widget Audit) + Phase 4 (Testing)
- **Day 4**: Phase 5 (Documentation) + Phase 6 (Deployment prep)

**Total: 4 developer days**

---

## Quick Start Checklist ✅

For immediate implementation, focus on these critical path items:

1. [ ] Create `config.py` with basic `apply_panel_config()` function
2. [ ] Add `panel: {}` to default configuration 
3. [ ] Integrate configuration calls in main panel `__init__()`
4. [ ] Test with simple hidden/disabled widget configuration
5. [ ] Verify no regression in panel functionality without configuration 