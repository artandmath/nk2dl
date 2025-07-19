# GUI Widgets Implementation Plan

## Overview
This plan outlines the implementation strategy for completing the "Populate the remainder of the gui widgets" section. The approach prioritizes UI development and visual polish before implementing backend functionality, while working within the existing MVC framework.

## Current Architecture Analysis

### Existing Framework Structure
The panel uses a well-organized MVC/MVP pattern with the following components:

**Models:**
- `SettingsModel` - Manages job, machine, and extra settings with change tracking
- `TableDataModel` - Handles node table data
- `GSVHierarchyModel` - Manages GSV hierarchy data

**Views:**
- `SettingsView` - Job and machine settings (already implemented)
- `ExtraSettingsView` - Basic extra settings (partially implemented)
- `NodeSettingsView` - Node table settings
- `GSVView` - GSV hierarchy view
- `ConsoleView` - Console output

**Widgets:**
- `ColoredGroupBox` - Styled group boxes
- `HighlightableCheckBox`, `HighlightableSpinBox`, `HighlightableComboBox`, `HighlightableLineEdit` - Interactive widgets
- `StandardTableWidget`, `FrozenTableWidget` - Table components

**Key Features Already Available:**
- Change tracking system (`WidgetChangeTrackingMixin`)
- Storage visual indication (`StorageVisualIndicationMixin`)
- Responsive layout system
- Nuke-native styling
- Configuration system integration

## Implementation Strategy

### Phase 1: Extend Settings Model (Priority: High)
Extend the existing `SettingsModel` to support all missing parameters from nuke.submission.

#### 1.1 Add Missing Job Settings
**Current Status**: The settings model already has basic job settings but is missing several key parameters.

**Parameters to add to `SettingsModel._job_settings`:**
- [ ] `render_settings_from_metadata` - Boolean (default: False)
- [ ] `submit_suspended` - Boolean (default: False)  
- [ ] `job_dependencies` - String (default: None)
- [ ] `continue_on_error` - Boolean (default: False)

**Implementation Tasks:**
- [ ] Update `_initialize_defaults()` method in `SettingsModel`
- [ ] Add validation methods for new parameters
- [ ] Update `_filter_supported_parameters()` in main panel
- [ ] Add default values to config system

#### 1.2 Add Missing Extra Settings
**Current Status**: `ExtraSettingsView` only has basic job info (name, comment, department).

**Parameters to add to `SettingsModel._extra_settings`:**
- [ ] `submit_script_as_auxiliary_file` - Boolean (default: None)
- [ ] `submission_is_build_job` - Boolean (default: False)
- [ ] `build_job_name` - String (default: None)
- [ ] `pre_build_job_script` - String/List (default: None)
- [ ] `post_build_job_script` - String/List (default: None)
- [ ] `build_job_as_auxiliary_file` - Boolean (default: None)
- [ ] `delete_build_job_script` - Boolean (default: None)
- [ ] `copy_script` - Boolean (default: None)
- [ ] `copy_script_path` - String/List/Dict (default: None)
- [ ] `submit_copied_script` - Boolean (default: None)
- [ ] `script_job_script_path` - String (default: None)
- [ ] `extra_info` - List (default: None)
- [ ] `on_job_complete` - String (default: None)
- [ ] `pre_job_script` - String (default: None)
- [ ] `post_job_script` - String (default: None)
- [ ] `pre_task_script` - String (default: None)
- [ ] `post_task_script` - String (default: None)
- [ ] `use_current_environment` - Boolean (default: False)
- [ ] `environment_keys` - List (default: None)
- [ ] `environment` - Dict (default: None)
- [ ] `omit_environment_keys` - List (default: None)

### Phase 2: Extend Settings View UI (Priority: High)
Extend the existing `SettingsView` to include the missing job settings.

#### 2.1 Add Missing Job Settings to SettingsView
**Current Status**: `SettingsView` has priority, chunk, frames, timeout, and other basic settings.

**New UI Components to Add:**
- [ ] `render_settings_from_metadata` - Checkbox with tooltip
- [ ] `submit_suspended` - Checkbox with tooltip
- [ ] `job_dependencies` - Text input with browse button
- [ ] `continue_on_error` - Checkbox with tooltip

**Implementation Tasks:**
- [ ] Add new form rows to `_create_job_settings_group()`
- [ ] Create appropriate widgets using existing `Highlightable*` classes
- [ ] Add tooltips using existing tooltip system
- [ ] Connect signals to model updates
- [ ] Add to visual indication and change tracking systems
- [ ] Update responsive layout handling

### Phase 3: Extend Extra Settings View UI (Priority: High)
Significantly expand the `ExtraSettingsView` to include all missing parameters.

#### 3.1 Create Logical Grouping Structure
**Current Status**: `ExtraSettingsView` only has basic job info in a simple grid.

**New Group Structure:**
- [ ] **Build Job Parameters Group** - Collapsible section
- [ ] **Script Copying Group** - Collapsible section  
- [ ] **ScriptJob Group** - Simple section
- [ ] **Job Info Group** - Expand existing section
- [ ] **Environment Variables Group** - Collapsible section

#### 3.2 Implement Build Job Parameters Group
- [ ] `submission_is_build_job` - Checkbox (enables/disables group)
- [ ] `build_job_name` - Text input
- [ ] `pre_build_job_script` - Multi-line text area with file browse
- [ ] `post_build_job_script` - Multi-line text area with file browse
- [ ] `build_job_as_auxiliary_file` - Checkbox
- [ ] `delete_build_job_script` - Checkbox

#### 3.3 Implement Script Copying Group
- [ ] `copy_script` - Checkbox (enables/disables group)
- [ ] `copy_script_path` - Text input with browse button
- [ ] `submit_copied_script` - Checkbox

#### 3.4 Implement ScriptJob Group
- [ ] `script_job_script_path` - Text input with browse button

#### 3.5 Expand Job Info Group
- [ ] `extra_info` - Multi-line text area
- [ ] `on_job_complete` - Text input
- [ ] `pre_job_script` - Multi-line text area with file browse
- [ ] `post_job_script` - Multi-line text area with file browse
- [ ] `pre_task_script` - Multi-line text area with file browse
- [ ] `post_task_script` - Multi-line text area with file browse

#### 3.6 Implement Environment Variables Group
- [ ] `use_current_environment` - Checkbox
- [ ] `environment_keys` - Multi-line text area
- [ ] `environment` - Key-value pair editor (new widget needed)
- [ ] `omit_environment_keys` - Multi-line text area

### Phase 4: Create New Widgets (Priority: Medium)
Create specialized widgets for complex input types.

#### 4.1 Multi-line Text Area Widget
- [ ] Create `HighlightableTextEdit` widget
- [ ] Add file browse button integration
- [ ] Implement proper sizing and scrolling
- [ ] Add to visual indication and change tracking systems

#### 4.2 Key-Value Pair Editor Widget
- [ ] Create `KeyValueEditor` widget for environment variables
- [ ] Support add/remove key-value pairs
- [ ] Implement validation for key names
- [ ] Add to visual indication and change tracking systems

#### 4.3 Collapsible Group Widget
- [ ] Create `CollapsibleGroupBox` widget
- [ ] Implement expand/collapse functionality
- [ ] Add visual indicators for state
- [ ] Maintain proper spacing and layout

### Phase 5: Visual Polish and UX (Priority: Medium)
Enhance the UI with professional styling and user experience improvements.

#### 5.1 Styling Enhancements
- [ ] Ensure consistent spacing using existing `Sizes` constants
- [ ] Apply proper color schemes using existing `Colors` constants
- [ ] Add hover states for all interactive elements
- [ ] Implement focus indicators for accessibility

#### 5.2 User Experience Improvements
- [ ] Add conditional visibility (build job group only visible when enabled)
- [ ] Implement proper validation feedback
- [ ] Add confirmation dialogs for destructive actions
- [ ] Ensure keyboard navigation support

#### 5.3 Responsive Design
- [ ] Test layout at different panel widths
- [ ] Implement proper text wrapping for long labels
- [ ] Ensure scrollable content when height is limited
- [ ] Add minimum/maximum size constraints

### Phase 6: Integration and Testing (Priority: Low)
Connect all components and ensure proper functionality.

#### 6.1 Data Binding Integration
- [ ] Connect all new UI components to `SettingsModel`
- [ ] Implement two-way data binding
- [ ] Add change event handlers
- [ ] Test save/cancel functionality

#### 6.2 Configuration Integration
- [ ] Update `apply_panel_config()` for new widgets
- [ ] Add object names for all new controls
- [ ] Test configuration loading/saving
- [ ] Ensure proper default values

#### 6.3 Submission Integration
- [ ] Update `_filter_supported_parameters()` in main panel
- [ ] Test parameter passing to nuke.submission
- [ ] Verify all parameters are correctly submitted
- [ ] Add logging for debugging

## Implementation Guidelines

### Code Organization
- **Extend existing classes** rather than creating new ones where possible
- **Use existing widget classes** (`Highlightable*`, `ColoredGroupBox`)
- **Follow existing naming conventions** and patterns
- **Maintain separation of concerns** (UI vs. logic)

### Integration Points
- **Settings Model**: Extend `_job_settings` and `_extra_settings` dictionaries
- **Visual Indication**: Use existing `StorageVisualIndicationMixin`
- **Change Tracking**: Use existing `WidgetChangeTrackingMixin`
- **Configuration**: Use existing `apply_panel_config()` system
- **Constants**: Use existing `Sizes`, `Colors`, `Settings` constants

### Testing Strategy
- **Unit tests** for new model methods
- **Integration tests** for UI-model binding
- **Visual regression tests** for UI consistency
- **Cross-version testing** for Nuke compatibility

### PySide/Qt Testing for Nuke Environment

#### Testing Qt Applications in Nuke
When creating or testing Qt/PySide applications that need to run in Nuke:

**Use Nuke Terminal Mode Instead of Python**
Replace standard `python script.py` commands with Nuke's terminal GUI mode:
```powershell
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg script.py
```

**When to Use Nuke Terminal Mode**
- Testing Qt widgets and panels that will be integrated into Nuke
- Debugging PySide2/PySide6 compatibility issues
- Testing inheritance systems that depend on Nuke's Qt environment
- Validating UI behavior in Nuke's specific Qt context
- Avoiding relative import issues when testing Nuke plugins

#### Nuke Qt Best Practices
1. **PySide Version Detection**: Always detect Nuke version for correct PySide import:
   ```python
   import nuke
   if nuke.NUKE_VERSION_MAJOR >= 16:
       from PySide6 import QtWidgets, QtCore, QtGui
   else:
       from PySide2 import QtWidgets, QtCore, QtGui
   ```

2. **Keep Windows Responsive**: In Nuke terminal mode, process Qt events to maintain responsiveness:
   ```python
   while True:
       QtWidgets.QApplication.processEvents()
       time.sleep(0.1)
       if not window.isVisible():
           break
   ```

3. **Prevent Garbage Collection in tests**: Store global references to prevent Qt widgets from being destroyed:
   ```python
   globals()['_widget_reference'] = widget
   ```

4. **Path Resolution**: When testing from subdirectories, adjust import paths:
   ```python
   nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
   #or be very direct:    nk2dl_path = "C:/Users/Daniel/Documents/repo/nk2dl/"
   sys.path.insert(0, nk2dl_path)
   ```

#### Nuke Command Line Options
- `--tg`: Terminal GUI mode (keeps Qt event loop active)
- `--nc`: No crash reporter
- `--safe`: Safe mode (minimal plugins)

#### Example Test Structure for UI Components
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Qt test for Nuke environment."""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
import nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui

def main():
    widget = MyQtWidget()
    widget.show()
    
    # Keep alive for Nuke terminal mode
    globals()['_test_widget'] = widget
    
    try:
        while True:
            QtWidgets.QApplication.processEvents()
            time.sleep(0.001)
            if not widget.isVisible():
                break
    except KeyboardInterrupt:
        pass
    
    return widget

if __name__ == "__main__":
    main()
```

#### Testing Commands
- **Nuke Qt Test**: `& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --tg tests/qt/test_file.py`
- **Environment Setup**: Run PowerShell environment `C:\Users\Daniel\Documents\repo\nk2dl\.venv\Scripts\Activate-nk2dl.ps1` for YAML support
- **Launch Time**: Allow up to 180 seconds for Nuke to launch

#### Testing Phases
- **Phase 2-3**: Test individual UI components in Nuke terminal mode
- **Phase 4**: Test new widgets (HighlightableTextEdit, KeyValueEditor, CollapsibleGroupBox)
- **Phase 5**: Test visual polish and responsive design
- **Phase 6**: Test full integration with existing panel

## Success Criteria

### UI Completion
- [ ] All form fields are visually complete and properly styled
- [ ] Layout is responsive and works at different panel sizes
- [ ] Styling is consistent with existing Nuke-native appearance
- [ ] All interactive elements have proper hover and focus states
- [ ] Tooltips provide clear, helpful information

### User Experience
- [ ] Interface is intuitive and easy to navigate
- [ ] Form validation provides clear feedback
- [ ] Error states are clearly communicated
- [ ] Keyboard navigation works properly
- [ ] Accessibility requirements are met

### Code Quality
- [ ] Code follows existing project style guidelines
- [ ] Components are properly documented
- [ ] Unit tests provide good coverage
- [ ] Performance meets acceptable standards
- [ ] Code is maintainable and extensible

## Timeline Estimate

- **Phase 1 (Model Extension)**: 1 week
- **Phase 2 (Settings View Extension)**: 1 week
- **Phase 3 (Extra Settings View Extension)**: 2-3 weeks
- **Phase 4 (New Widgets)**: 1-2 weeks
- **Phase 5 (Visual Polish)**: 1 week
- **Phase 6 (Integration)**: 1 week

**Total Estimated Time**: 7-9 weeks

## Risk Mitigation

### Technical Risks
- **Complex UI Layout**: Break down into smaller, manageable components
- **Widget Integration**: Test each widget individually before integration
- **Performance Issues**: Monitor widget creation and update performance

### Timeline Risks
- **Scope Creep**: Focus on UI-first approach, defer functionality
- **Complex Requirements**: Implement in logical phases
- **Testing Overhead**: Implement automated testing early

## Next Steps

1. **Review and approve this updated plan**
2. **Begin Phase 1: Extend Settings Model**
3. **Create UI mockups for complex components**
4. **Establish regular review and feedback cycles** 