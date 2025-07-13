# Storage Implementation 2 - Fix Widget Highlighting Issues

## Overview
This plan addresses critical issues with the current storage implementation where widgets are incorrectly highlighted when they should be showing config defaults. The current system saves ALL settings to YAML regardless of whether users actually changed them, causing unnecessary highlighting and bloated YAML files.

## Problem Analysis
Based on the screenshot and code analysis, the current issues are:

1. **Incorrect Highlighting**: Priority (50), chunk size (5), batch mode (1001-1215) are highlighted but not in YAML
2. **Bloated YAML**: All settings are saved to YAML even when they're just config defaults
3. **No User Intent Tracking**: No distinction between "user changed this" vs "this is a default value"
4. **Immediate Save Behavior**: Any widget change triggers saving ALL settings to storage

## Desired Behavior
- **Launch Panel**: Check if YAML exists, if not create minimal one, populate UI with config defaults
- **User Changes Widget**: Add only that specific value to YAML, highlight the widget
- **User Resets Widget**: Remove YAML entry, use config default, remove highlight
- **Minimal YAML**: Only store values that users have explicitly changed

---

## Phase 1: Widget Change Tracking System (2-3 days)

### 1.1 Create Widget Change Tracker
- [ ] **Create new class `WidgetChangeTracker`**
  - [ ] Track which widgets have been explicitly changed by user
  - [ ] Distinguish between programmatic changes and user changes
  - [ ] Store mapping of widget → parameter name → user_changed_flag
  - [ ] Provide methods to mark widget as user-changed/reset

### 1.2 Modify Settings Model
- [ ] **Update SettingsModel to track user changes**
  - [ ] Add `_user_changed_settings` dictionary to track modified parameters
  - [ ] Add `mark_as_user_changed(param_name)` method
  - [ ] Add `mark_as_reset_to_default(param_name)` method
  - [ ] Add `get_user_changed_settings()` method to return only modified values
  - [ ] Add `is_user_changed(param_name)` method

### 1.3 Update Settings Views
- [ ] **Modify SettingsView to track user interactions**
  - [ ] Connect widget change signals to mark parameters as user-changed
  - [ ] Implement context menu "Reset to Default" functionality
  - [ ] Add logic to detect programmatic vs user changes
  - [ ] Update widget signal connections to track user intent

- [ ] **Modify ExtraSettingsView similarly**
  - [ ] Same tracking logic for extra settings
  - [ ] Context menu reset functionality
  - [ ] User change detection

---

## Phase 2: Storage System Refactoring (2-3 days)

### 2.1 Modify Storage Save Logic
- [ ] **Update `_on_settings_changed_save_to_storage()`**
  - [ ] Change to only save user-changed settings instead of all settings
  - [ ] Call `get_user_changed_settings()` instead of `get_all_*_settings()`
  - [ ] Only include parameters that have been explicitly modified by user
  - [ ] Preserve existing node_overrides in YAML

### 2.2 Enhance NodeSettingsStorage
- [ ] **Add selective save methods**
  - [ ] `save_user_changed_settings(user_changed_dict)` - only save changed values
  - [ ] `remove_setting_from_storage(param_name)` - remove specific parameter
  - [ ] `load_user_changed_settings()` - load only stored (user-changed) values
  - [ ] Keep existing `load_all_settings()` for backward compatibility

### 2.3 Update Storage Loading Logic
- [ ] **Modify `_load_settings_from_storage()`**
  - [ ] Load stored (user-changed) settings first
  - [ ] For missing parameters, use config defaults
  - [ ] Update models with distinction between stored vs default values
  - [ ] Ensure proper initialization order

---

## Phase 3: Visual Indication System Fix (1-2 days)

### 3.1 Fix Visual Indication Logic
- [ ] **Update `StorageVisualIndicationManager`**
  - [ ] Modify `_is_parameter_stored()` to check if parameter exists in YAML
  - [ ] Only highlight widgets that have entries in stored settings
  - [ ] Remove highlighting for parameters that only have config defaults
  - [ ] Add method to force unhighlight widget when reset to default

### 3.2 Update Widget Highlighting Integration
- [ ] **Modify visual indication refresh logic**
  - [ ] Only highlight widgets with stored values, not all populated values
  - [ ] Add logic to immediately unhighlight when parameter is reset
  - [ ] Ensure highlighting state matches actual storage state

---

## Phase 4: Panel Initialization Logic (1 day)

### 4.1 Fix Panel Startup Behavior
- [ ] **Update panel initialization in `__init__.py`**
  - [ ] Check if YAML exists on startup
  - [ ] Create minimal YAML if none exists (empty global_settings, empty node_overrides)
  - [ ] Populate UI with config defaults for all parameters
  - [ ] Only highlight widgets that have stored values

### 4.2 Create Minimal YAML Structure
- [ ] **Define minimal YAML template**
  ```yaml
  version: "0.1"
  timestamp: 1234567890.123
  global_settings: {}
  node_overrides: {}
  ```
- [ ] **Implement creation logic**
  - [ ] Create YAML file with minimal structure
  - [ ] Ensure proper knob initialization
  - [ ] Handle file creation errors gracefully

---

## Phase 5: Context Menu Reset Functionality (1-2 days)

### 5.1 Implement Widget Reset Feature
- [ ] **Add context menu to highlightable widgets**
  - [ ] Right-click menu with "Reset to Default" option
  - [ ] Only show for widgets that are currently highlighted
  - [ ] Connect to reset functionality

### 5.2 Reset Implementation
- [ ] **Create reset logic**
  - [ ] Get config default for parameter
  - [ ] Update widget value to config default
  - [ ] Remove parameter from YAML storage
  - [ ] Remove highlight from widget
  - [ ] Update model state to reflect reset

---

## Phase 6: Testing and Validation (1 day)

### 6.1 Core Functionality Tests
- [ ] **Test panel initialization**
  - [ ] Fresh panel launch with no YAML
  - [ ] Fresh panel launch with existing YAML
  - [ ] Verify only stored values are highlighted

- [ ] **Test widget modification**
  - [ ] Change widget value → verify YAML entry created
  - [ ] Change widget value → verify highlighting applied
  - [ ] Reset widget value → verify YAML entry removed
  - [ ] Reset widget value → verify highlighting removed

### 6.2 Edge Case Testing
- [ ] **Test various scenarios**
  - [ ] Multiple widget changes in sequence
  - [ ] Panel close/reopen with stored values
  - [ ] Config changes with stored values
  - [ ] Invalid YAML handling

---

## Phase 7: Documentation and Cleanup (0.5 days)

### 7.1 Code Documentation
- [ ] **Document new classes and methods**
  - [ ] WidgetChangeTracker class
  - [ ] New storage methods
  - [ ] Reset functionality

### 7.2 Update Existing Documentation
- [ ] **Update relevant docs**
  - [ ] Storage behavior documentation
  - [ ] User interaction documentation
  - [ ] Reset functionality documentation

---

## Implementation Notes

### Key Architectural Changes
1. **User Intent Tracking**: New system to distinguish user changes from programmatic changes
2. **Selective Storage**: Only save values that users have explicitly modified
3. **Minimal YAML**: Start with empty storage, add only as needed
4. **Reset Functionality**: Allow users to revert to config defaults

### Backward Compatibility
- Keep existing `load_all_settings()` method
- Maintain current YAML structure
- Ensure existing stored values continue to work

### Performance Considerations
- Only save individual parameters when changed (not all settings)
- Batch operations where possible
- Minimize YAML file size

### Error Handling
- Graceful fallback to config defaults
- Handle missing/corrupted YAML files
- Proper logging for debugging

---

## Success Criteria
- [ ] Fresh panel launch shows no highlighted widgets
- [ ] Only user-modified widgets are highlighted
- [ ] YAML contains only user-changed values
- [ ] Right-click reset functionality works
- [ ] Panel state persists correctly across restarts
- [ ] No regression in existing functionality 