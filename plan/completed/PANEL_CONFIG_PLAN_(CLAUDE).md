# Panel Configuration Implementation Plan (Claude)

## Overview

This plan outlines the implementation of a configuration system for the nk2dl panel that allows controlling the visibility, enabled state, and default values of UI controls. The system will follow the existing nk2dl configuration methodology, using the same files, conventions, and load order.

## Current Configuration System Analysis

### Configuration Load Order
Based on `nk2dl/common/config.py` and `docs/config.md`, the current system follows this precedence:

1. **Default configuration** - Built into the package (`Config.DEFAULT_CONFIG`)
2. **Project configuration** - `config.yaml` in nk2dl module directory or `NK2DL_CONFIG` env var
3. **Environment variables** - `NK2DL_*` format with double underscore convention
4. **User configuration** - `~/.nk2dl/config.yaml` in user's home directory

### Naming Conventions
- Environment variables: `NK2DL_SECTION_KEY` format
- Underscore handling: `use_web_service` → `NK2DL_DEADLINE_USE__WEB__SERVICE`
- Double underscores (`__`) in env vars represent single underscores in config keys

### Current Configuration Sections
- `deadline`: Web service/command line settings
- `logging`: Log levels and output
- `submission`: Job submission defaults and templates
- *(Proposed new section)* `panel`: UI control configuration

## Panel Control Analysis

### Identifiable Panel Controls

Based on `nk2dl/gui/panel/views.py` and `nk2dl/gui/panel/constants.py`, the panel contains:

#### Job Settings Controls
```yaml
job_settings_controls:
  priority_spin: SpinBox (0-100)
  chunk_size_spin: SpinBox (1-1000)
  frames_combo: ComboBox ["Global", "Input", "Custom"]
  frame_range_edit: LineEdit
  use_node_frame_list_check: CheckBox
  task_timeout_spin: SpinBox (0-999)
  enable_auto_timeout_check: CheckBox
  render_mode_combo: ComboBox ["Full", "Proxy", "Both", "Script"]
  render_nukex_check: CheckBox
  use_batch_mode_check: CheckBox
  reload_plugin_check: CheckBox
  separate_tasks_check: CheckBox
  separate_jobs_check: CheckBox
  views_separate_jobs_check: CheckBox
```

#### Machine Settings Controls
```yaml
machine_settings_controls:
  pool_combo: ComboBox
  secondary_pool_combo: ComboBox
  group_combo: ComboBox
  threads_spin: SpinBox (1-64)
  min_ram_spin: SpinBox (0-64)
  max_ram_spin: SpinBox (0-512)
  gpu_override_spin: SpinBox (0-16)
  use_gpu_check: CheckBox
  concurrent_tasks_spin: SpinBox (1-64)
  limit_tasks_check: CheckBox
  machine_limit_spin: SpinBox (0+)
  machine_deny_list_check: CheckBox
  machine_list_edit: LineEdit
  limits_edit: LineEdit
```

#### Node Settings Table Controls
```yaml
table_controls:
  update_btn: Button
  all_btn: Button
  clear_btn: Button
  selection_btn: Button
  inside_groups_check: CheckBox
  column_dropdown: ColumnVisibilityDropdown
  filter_edit: LineEdit
```

#### Bottom Controls
```yaml
bottom_controls:
  progress_bar: ProgressBar
  render_btn: Button
```

#### Tab Controls
```yaml
tab_controls:
  tab_widget: TabWidget
  node_settings_tab: Tab
  gsv_tab: Tab (conditional)
  extra_settings_tab: Tab
  console_tab: Tab
```

## Proposed Configuration Schema

### New Panel Configuration Section

Add a new `panel` section to the existing configuration files:

```yaml
panel:
  # Control visibility - artist cannot see the control at all
  hidden_controls: []
  
  # Control enablement - artist can see but cannot modify (greyed out)
  disabled_controls: []
  
  # Default values - pre-populate controls with these values
  default_values: {}
  
  # Essential controls that cannot be hidden/disabled
  # (automatically exempted from hidden_controls and disabled_controls)
  essential_controls:
    - "render_btn"
    - "tab_widget"
    - "update_btn"
    - "all_btn"
    - "clear_btn"
    - "selection_btn"
```

### Configuration Examples

#### Basic Artist Lockdown
```yaml
panel:
  hidden_controls:
    - "secondary_pool_combo"
    - "group_combo"
    - "gpu_override_spin"
    - "machine_limit_spin"
    - "machine_deny_list_check"
    - "machine_list_edit"
    - "limits_edit"
    - "reload_plugin_check"
    - "separate_tasks_check"
    - "separate_jobs_check"
    - "views_separate_jobs_check"
  
  disabled_controls:
    - "pool_combo"
    - "threads_spin"
    - "use_gpu_check"
    - "render_mode_combo"
  
  default_values:
    priority_spin: 75
    chunk_size_spin: 10
    pool_combo: "comp"
    threads_spin: 8
    use_batch_mode_check: true
    render_mode_combo: "Full"
```

#### Environment Variable Examples
```bash
# Hide secondary pool dropdown
NK2DL_PANEL_HIDDEN__CONTROLS="secondary_pool_combo,group_combo"

# Disable specific controls
NK2DL_PANEL_DISABLED__CONTROLS="pool_combo,threads_spin"

# Set default priority
NK2DL_PANEL_DEFAULT__VALUES__PRIORITY__SPIN=75
```

## Implementation Plan

### Phase 1: Configuration Infrastructure

#### 1.1 Extend Config Class (`nk2dl/common/config.py`)

Add panel configuration to `DEFAULT_CONFIG`:

```python
DEFAULT_CONFIG = {
    # ... existing sections ...
    'panel': {
        'hidden_controls': [],
        'disabled_controls': [],
        'default_values': {},
        'essential_controls': [
            'render_btn',
            'tab_widget', 
            'update_btn',
            'all_btn',
            'clear_btn',
            'selection_btn'
        ]
    }
}
```

#### 1.2 Create Panel Configuration Helper (`nk2dl/gui/panel/config_manager.py`)

```python
class PanelConfigManager:
    """Manages panel-specific configuration."""
    
    def __init__(self, config):
        self.config = config
        self._essential_controls = set(config.get('panel.essential_controls', []))
    
    def is_control_hidden(self, control_name: str) -> bool:
        """Check if a control should be hidden."""
        if control_name in self._essential_controls:
            return False
        return control_name in self.config.get('panel.hidden_controls', [])
    
    def is_control_disabled(self, control_name: str) -> bool:
        """Check if a control should be disabled."""
        if control_name in self._essential_controls:
            return False
        return control_name in self.config.get('panel.disabled_controls', [])
    
    def get_default_value(self, control_name: str):
        """Get default value for a control."""
        return self.config.get(f'panel.default_values.{control_name}')
    
    def should_apply_config_to_control(self, control_name: str) -> tuple:
        """Get complete config state for a control."""
        return (
            self.is_control_hidden(control_name),
            self.is_control_disabled(control_name),
            self.get_default_value(control_name)
        )
```

### Phase 2: Panel Integration

#### 2.1 Modify Base Panel Class (`nk2dl/gui/panel/panel.py`)

```python
class Nk2dlPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # ... existing initialization ...
        
        # Initialize configuration manager
        from ...common.config import config
        from .config_manager import PanelConfigManager
        self.config_manager = PanelConfigManager(config)
        
        # Apply configuration after UI creation
        self._apply_panel_configuration()
    
    def _apply_panel_configuration(self):
        """Apply configuration to all panel controls."""
        # Apply to all named controls
        for control_name in self._get_all_control_names():
            control = getattr(self, control_name, None)
            if control:
                self._configure_control(control_name, control)
    
    def _configure_control(self, control_name: str, control):
        """Configure a single control based on config."""
        hidden, disabled, default_value = self.config_manager.should_apply_config_to_control(control_name)
        
        if hidden:
            control.setVisible(False)
        elif disabled:
            control.setEnabled(False)
            # Apply visual styling for disabled state
            self._apply_disabled_styling(control)
        
        if default_value is not None:
            self._set_control_default_value(control, default_value)
    
    def _apply_disabled_styling(self, control):
        """Apply greyed-out styling to disabled controls."""
        current_style = control.styleSheet()
        disabled_style = "color: #808080; background-color: #f0f0f0;"
        control.setStyleSheet(f"{current_style} {disabled_style}")
    
    def _set_control_default_value(self, control, value):
        """Set default value based on control type."""
        if isinstance(control, QtWidgets.QSpinBox):
            control.setValue(int(value))
        elif isinstance(control, QtWidgets.QComboBox):
            index = control.findText(str(value))
            if index >= 0:
                control.setCurrentIndex(index)
        elif isinstance(control, QtWidgets.QCheckBox):
            control.setChecked(bool(value))
        elif isinstance(control, QtWidgets.QLineEdit):
            control.setText(str(value))
    
    def _get_all_control_names(self) -> list:
        """Get list of all configurable control names."""
        return [
            # Job settings controls
            'priority_spin', 'chunk_size_spin', 'frames_combo', 'frame_range_edit',
            'use_node_frame_list_check', 'task_timeout_spin', 'enable_auto_timeout_check',
            'render_mode_combo', 'render_nukex_check', 'use_batch_mode_check',
            'reload_plugin_check', 'separate_tasks_check', 'separate_jobs_check',
            'views_separate_jobs_check',
            
            # Machine settings controls  
            'pool_combo', 'secondary_pool_combo', 'group_combo', 'threads_spin',
            'min_ram_spin', 'max_ram_spin', 'gpu_override_spin', 'use_gpu_check',
            'concurrent_tasks_spin', 'limit_tasks_check', 'machine_limit_spin',
            'machine_deny_list_check', 'machine_list_edit', 'limits_edit',
            
            # Table controls
            'update_btn', 'all_btn', 'clear_btn', 'selection_btn',
            'inside_groups_check', 'column_dropdown', 'filter_edit',
            
            # Bottom controls
            'progress_bar', 'render_btn',
            
            # Tab controls
            'tab_widget'
        ]
```

#### 2.2 Modify View Classes

Each view class (`SettingsView`, `NodeSettingsView`, etc.) will need:

1. Accept `config_manager` in constructor
2. Call `_apply_view_configuration()` after UI creation
3. Implement control configuration logic

### Phase 3: Special Cases and Edge Cases

#### 3.1 Essential Controls Protection

Controls that are essential for panel functionality are automatically protected:
- `render_btn`: Primary action button
- `tab_widget`: Main navigation
- Core table buttons: `update_btn`, `all_btn`, `clear_btn`, `selection_btn`

#### 3.2 Dependency Handling

Some controls have dependencies:
- If `frames_combo` is set to "Custom", `frame_range_edit` should be enabled
- If parent control is hidden/disabled, dependent controls should follow suit

#### 3.3 Table Column Configuration

Extend `ColumnVisibilityDropdown` to support configuration-based column hiding:

```python
def _apply_column_configuration(self):
    """Apply configuration to column visibility."""
    hidden_columns = self.config_manager.get_hidden_columns()
    for column in hidden_columns:
        if column not in TableColumns.COLUMN_GROUPS["Fixed"]:
            self.visible_columns.discard(column)
```

### Phase 4: Environment Variable Support

Extend environment variable processing to handle complex data types:

```python
def _process_panel_env_vars(self) -> None:
    """Process panel-specific environment variables."""
    for key, value in os.environ.items():
        if key.startswith('NK2DL_PANEL_'):
            # Handle list values (comma-separated)
            if 'HIDDEN__CONTROLS' in key or 'DISABLED__CONTROLS' in key:
                value = [item.strip() for item in value.split(',')]
            
            # Handle nested default values
            elif 'DEFAULT__VALUES__' in key:
                # NK2DL_PANEL_DEFAULT__VALUES__PRIORITY__SPIN=75
                control_name = key.replace('NK2DL_PANEL_DEFAULT__VALUES__', '').lower()
                self._set_config_value(['panel', 'default_values', control_name], value)
                continue
            
            # Process normally
            self._set_config_value(['panel', key_without_prefix], value)
```

### Phase 5: Documentation Updates

#### 5.1 Configuration Documentation (`docs/config.md`)

Add new section:

```markdown
### Panel Configuration

```yaml
panel:
  # Controls to hide from artists (not visible at all)
  hidden_controls: 
    - "secondary_pool_combo"
    - "gpu_override_spin"
  
  # Controls to disable (visible but greyed out)
  disabled_controls:
    - "pool_combo"
    - "threads_spin"
  
  # Default values for controls
  default_values:
    priority_spin: 75
    chunk_size_spin: 10
    use_batch_mode_check: true
```

#### Control Names Reference

**Job Settings:**
- `priority_spin`, `chunk_size_spin`, `frames_combo`, `frame_range_edit`
- `use_node_frame_list_check`, `task_timeout_spin`, `enable_auto_timeout_check`
- `render_mode_combo`, `render_nukex_check`, `use_batch_mode_check`
- `reload_plugin_check`, `separate_tasks_check`, `separate_jobs_check`

**Machine Settings:**
- `pool_combo`, `secondary_pool_combo`, `group_combo`, `threads_spin`
- `min_ram_spin`, `max_ram_spin`, `gpu_override_spin`, `use_gpu_check`
- `concurrent_tasks_spin`, `limit_tasks_check`, `machine_limit_spin`
- `machine_deny_list_check`, `machine_list_edit`, `limits_edit`

**Essential Controls (Cannot be hidden/disabled):**
- `render_btn`, `tab_widget`, `update_btn`, `all_btn`, `clear_btn`, `selection_btn`
```

## Implementation Timeline

### Week 1: Infrastructure
- [ ] Extend `Config` class with panel section
- [ ] Create `PanelConfigManager` class
- [ ] Add environment variable processing
- [ ] Write unit tests for configuration logic

### Week 2: Panel Integration  
- [ ] Modify `Nk2dlPanel` class for configuration support
- [ ] Update `SettingsView` with configuration awareness
- [ ] Update `NodeSettingsView` with configuration awareness
- [ ] Implement control naming and identification

### Week 3: Advanced Features
- [ ] Implement default value setting logic
- [ ] Add disabled control styling
- [ ] Handle control dependencies
- [ ] Extend column visibility configuration

### Week 4: Testing and Documentation
- [ ] Comprehensive testing with various configurations
- [ ] Update documentation
- [ ] Create example configuration files
- [ ] Performance testing and optimization

## Risk Mitigation

### Configuration Conflicts
- Essential controls are protected from hiding/disabling
- Invalid control names are logged and ignored
- Malformed configuration values fall back to defaults

### User Experience
- Disabled controls show visual feedback (greyed out)
- Hidden controls don't break layout
- Configuration changes require panel restart

### Backwards Compatibility
- New configuration section is optional
- Default behavior unchanged when no panel config provided
- Existing panel functionality preserved

## Testing Strategy

### Unit Tests
- Configuration loading and parsing
- Control identification and configuration
- Environment variable processing
- Default value setting

### Integration Tests  
- Full panel with various configurations
- Configuration precedence (file vs env vars vs user config)
- Edge cases (invalid controls, malformed values)

### User Acceptance Tests
- Artist workflow with locked-down panel
- Supervisor workflow with full access
- Studio configuration deployment 