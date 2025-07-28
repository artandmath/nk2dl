# NK2DL Panel Configuration Implementation Plan

## Overview

This plan implements a configuration system for the nk2dl panel that allows controlling the visibility, enabled state, and default values of UI controls. The implementation leverages the existing `nk2dl.common.config.Config` system to maintain consistency with the current configuration methodology.

**New Features**: 
- Configuration-aware tooltips will indicate when controls are modified by configuration, including which source set the value.
- Right-click context menus allow resetting controls to defaults at individual, group, and panel-wide scopes.

## Current Configuration System Analysis

### Configuration Load Order (from `nk2dl/common/config.py`)

The existing configuration system loads in the following precedence (later sources override earlier):

1. **Default Configuration** - `Config.DEFAULT_CONFIG` hardcoded in the module
2. **Project Configuration** - YAML file at `nk2dl/config.yaml` or path from `NK2DL_CONFIG` env var
3. **Environment Variables** - `NK2DL_*` prefixed variables
4. **User Configuration** - `~/.nk2dl/config.yaml` in user's home directory (highest precedence)

### Environment Variable Conventions

- Format: `NK2DL_SECTION_KEY`
- Underscore handling: Single underscores in config keys become double underscores in env vars
  - Example: `panel.use_gpu_checkbox.disabled` → `NK2DL_PANEL_USE__GPU__CHECKBOX_DISABLED`

## Panel Configuration Schema

### New Configuration Section

Add a `panel` section to the existing configuration structure:

```yaml
panel:
  # Control-specific configuration using widget objectName as key
  priority_spin:
    value: 75        # Set default value
    disabled: true   # Control visible but greyed out
  
  use_gpu_check:
    hidden: true     # Control completely hidden
  
  job_status_combo:
    value: "Suspended"  # Set default selection
```

### Configuration Behavior

- **`hidden: true`** - Control is completely removed from UI (invisible to artist)
- **`disabled: true`** - Control is visible but greyed out and non-editable 
- **`value: <val>`** - Sets the initial/default value when panel opens
- If no configuration exists for a control, it uses default behavior

### Environment Variable Examples

```bash
# Hide the GPU checkbox completely
NK2DL_PANEL_USE__GPU__CHECK_HIDDEN=true

# Disable pool selection (visible but greyed out)
NK2DL_PANEL_POOL__COMBO_DISABLED=true

# Set default priority value
NK2DL_PANEL_PRIORITY__SPIN_VALUE=75
```

## Implementation Plan

### Phase 1: Configuration Infrastructure

#### 1.1 Extend Default Configuration (`nk2dl/common/config.py`)

Add the panel section to `DEFAULT_CONFIG`:

```python
DEFAULT_CONFIG = {
    # ... existing sections ...
    'panel': {}
}
```

#### 1.2 Create Panel Configuration Helper (`nk2dl/gui/panel/config.py`)

```python
"""Panel configuration helper module."""

import os
from pathlib import Path
from typing import Any, Optional, Tuple, Dict, Set
from ...common.config import config


# Essential controls that cannot be hidden or disabled
ESSENTIAL_CONTROLS = {
    'render_btn',       # Primary action button
    'tab_widget',       # Main navigation
    'progress_bar',     # Status feedback
    'update_btn',       # Core table functionality
    'all_btn',
    'clear_btn', 
    'selection_btn'
}

# Control groups for context menu actions
CONTROL_GROUPS = {
    'job_settings': {
        'priority_spin', 'chunk_size_spin', 'frames_combo', 'frame_range_edit',
        'use_node_frame_list_check', 'task_timeout_spin', 'enable_auto_timeout_check',
        'render_mode_combo', 'render_nukex_check', 'use_batch_mode_check',
        'reload_plugin_check', 'separate_tasks_check', 'separate_jobs_check',
        'views_separate_jobs_check'
    },
    'machine_settings': {
        'pool_combo', 'secondary_pool_combo', 'group_combo', 'threads_spin',
        'min_ram_spin', 'max_ram_spin', 'gpu_override_spin', 'use_gpu_check',
        'concurrent_tasks_spin', 'limit_tasks_check', 'machine_limit_spin',
        'machine_deny_list_check', 'machine_list_edit', 'limits_edit'
    },
    'table_controls': {
        'update_btn', 'all_btn', 'clear_btn', 'selection_btn',
        'inside_groups_check', 'column_dropdown', 'filter_edit'
    },
    'extra_settings': {
        'job_name_edit', 'comment_edit', 'department_edit'
    }
}

# Store original widget defaults for reset functionality
_widget_defaults: Dict[str, Any] = {}


def apply_panel_config(widget, control_name: Optional[str] = None) -> None:
    """Apply panel configuration to a widget.
    
    Args:
        widget: Qt widget to configure
        control_name: Override for widget objectName
    """
    # Use provided name or fall back to objectName
    name = control_name or widget.objectName()
    if not name:
        return
    
    # Store original default value before applying configuration
    _store_widget_default(widget, name)
    
    # Skip configuration for essential controls but still add context menu
    if name in ESSENTIAL_CONTROLS:
        _add_context_menu(widget, name)
        return
    
    # Get configuration for this control
    control_config = config.get(f'panel.{name}', {})
    
    # Add context menu regardless of configuration
    _add_context_menu(widget, name)
    
    if not control_config:
        return
    
    # Determine configuration sources for tooltip
    config_sources = _get_config_sources(name)
    
    # Apply hidden state first (overrides other settings)
    if control_config.get('hidden'):
        widget.setVisible(False)
        # Hidden controls don't need tooltips
        return
    
    # Apply disabled state
    if control_config.get('disabled'):
        widget.setEnabled(False)
        _apply_disabled_styling(widget)
    
    # Apply default value
    if 'value' in control_config:
        _set_widget_value(widget, control_config['value'])
    
    # Set enhanced tooltip for all visible controls (after all configuration is applied)
    control_display_name = _get_control_display_name(name)
    _set_enhanced_tooltip(widget, control_display_name, config_sources)


def _store_widget_default(widget, control_name: str) -> None:
    """Store the original widget default value before configuration is applied."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets
    
    if isinstance(widget, QtWidgets.QSpinBox):
        _widget_defaults[control_name] = widget.value()
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        _widget_defaults[control_name] = widget.value()
    elif isinstance(widget, QtWidgets.QComboBox):
        _widget_defaults[control_name] = widget.currentIndex()
    elif isinstance(widget, QtWidgets.QCheckBox):
        _widget_defaults[control_name] = widget.isChecked()
    elif isinstance(widget, QtWidgets.QLineEdit):
        _widget_defaults[control_name] = widget.text()


def _add_context_menu(widget, control_name: str) -> None:
    """Add right-click context menu to a widget."""
    try:
        from PySide6 import QtWidgets, QtCore
    except ImportError:
        from PySide2 import QtWidgets, QtCore
    
    # Set context menu policy
    widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    
    # Connect to context menu handler
    widget.customContextMenuRequested.connect(
        lambda pos: _show_context_menu(widget, control_name, pos)
    )


def _show_context_menu(widget, control_name: str, position) -> None:
    """Show context menu for a control."""
    try:
        from PySide6 import QtWidgets, QtCore
    except ImportError:
        from PySide2 import QtWidgets, QtCore
    
    menu = QtWidgets.QMenu()
    
    # Add "Set to Default" action
    default_action = menu.addAction("Set to Default")
    default_action.triggered.connect(lambda: _reset_control_to_default(widget, control_name))
    
    # Determine control group and add group reset actions
    control_group = _get_control_group(control_name)
    if control_group:
        group_name = control_group.replace('_', ' ').title()
        group_action = menu.addAction(f"Set {group_name} to Default")
        group_action.triggered.connect(lambda: _reset_group_to_default(control_group))
    
    # Add separator
    menu.addSeparator()
    
    # Add "Set All to Default" action
    all_action = menu.addAction("Set All to Default")
    all_action.triggered.connect(_reset_all_to_default)
    
    # Show menu at cursor position
    global_pos = widget.mapToGlobal(position)
    menu.exec_(global_pos)


def _get_control_group(control_name: str) -> Optional[str]:
    """Get the group that a control belongs to."""
    for group_name, controls in CONTROL_GROUPS.items():
        if control_name in controls:
            return group_name
    return None


def _reset_control_to_default(widget, control_name: str) -> None:
    """Reset a single control to its default value."""
    if control_name in _widget_defaults:
        default_value = _widget_defaults[control_name]
        _set_widget_value(widget, default_value)


def _reset_group_to_default(group_name: str) -> None:
    """Reset all controls in a group to their default values."""
    if group_name not in CONTROL_GROUPS:
        return
    
    # Find panel instance to access widgets
    panel_instance = _get_panel_instance()
    if not panel_instance:
        return
    
    # Reset each control in the group
    for control_name in CONTROL_GROUPS[group_name]:
        widget = _find_widget_by_name(panel_instance, control_name)
        if widget and control_name in _widget_defaults:
            default_value = _widget_defaults[control_name]
            _set_widget_value(widget, default_value)


def _reset_all_to_default() -> None:
    """Reset all panel controls to their default values."""
    panel_instance = _get_panel_instance()
    if not panel_instance:
        return
    
    # Reset all stored defaults
    for control_name, default_value in _widget_defaults.items():
        widget = _find_widget_by_name(panel_instance, control_name)
        if widget:
            _set_widget_value(widget, default_value)


def _get_panel_instance():
    """Get the current panel instance for accessing widgets."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets
    
    # Find the Nk2dlPanel instance
    app = QtWidgets.QApplication.instance()
    if not app:
        return None
    
    for widget in app.allWidgets():
        if widget.__class__.__name__ == 'Nk2dlPanel':
            return widget
    
    return None


def _find_widget_by_name(parent_widget, control_name: str):
    """Find a widget by its object name within a parent widget."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets
    
    # Check if parent has the widget as an attribute
    if hasattr(parent_widget, control_name):
        return getattr(parent_widget, control_name)
    
    # Search through child widgets
    for child in parent_widget.findChildren(QtWidgets.QWidget):
        if child.objectName() == control_name:
            return child
    
    # Search in view components
    if hasattr(parent_widget, 'settings_view'):
        if hasattr(parent_widget.settings_view, control_name):
            return getattr(parent_widget.settings_view, control_name)
    
    if hasattr(parent_widget, 'node_settings_view'):
        if hasattr(parent_widget.node_settings_view, control_name):
            return getattr(parent_widget.node_settings_view, control_name)
    
    return None


def _get_config_sources(control_name: str) -> dict:
    """Determine which configuration source provided each setting for a control.
    
    Args:
        control_name: Name of the control to check
        
    Returns:
        Dict mapping setting names to their configuration sources
    """
    sources = {}
    base_key = f'panel.{control_name}'
    
    # Check each possible setting
    for setting in ['hidden', 'disabled', 'value']:
        source = _identify_config_source(f'{base_key}.{setting}')
        if source:
            sources[setting] = source
    
    return sources


def _identify_config_source(config_key: str) -> Optional[str]:
    """Identify which configuration source provided a specific key.
    
    Since the Config class doesn't track sources, we need to check them manually
    in reverse precedence order (highest to lowest priority).
    """
    # Convert config key to environment variable format
    env_key = _config_key_to_env_var(config_key)
    
    # Check user config first (highest precedence)
    user_config_path = Path.home() / '.nk2dl' / 'config.yaml'
    if user_config_path.exists() and _key_exists_in_yaml(user_config_path, config_key):
        return f"User Config ({user_config_path})"
    
    # Check environment variables
    if env_key in os.environ:
        return f"Environment Variable ({env_key})"
    
    # Check project config
    project_config_path = os.environ.get('NK2DL_CONFIG')
    if project_config_path:
        project_path = Path(project_config_path)
        if project_path.exists() and _key_exists_in_yaml(project_path, config_key):
            return f"Project Config ({project_path})"
    else:
        # Check default project config location
        try:
            import nuke2dl
            import importlib.resources
            module_dir = Path(importlib.resources.files(nuke2dl))
            default_config = module_dir / 'config.yaml'
            if default_config.exists() and _key_exists_in_yaml(default_config, config_key):
                return f"Project Config ({default_config})"
        except ImportError:
            pass
    
    # If we get here, it might be from default config
    return "Default Configuration"


def _config_key_to_env_var(config_key: str) -> str:
    """Convert a config key to environment variable format.
    
    Args:
        config_key: Dot-separated config key (e.g., 'panel.priority_spin.value')
        
    Returns:
        Environment variable name (e.g., 'NK2DL_PANEL_PRIORITY__SPIN_VALUE')
    """
    parts = config_key.split('.')
    # Replace underscores with double underscores for each part
    env_parts = [part.replace('_', '__') for part in parts]
    return 'NK2DL_' + '_'.join(env_parts).upper()


def _key_exists_in_yaml(yaml_path: Path, config_key: str) -> bool:
    """Check if a configuration key exists in a YAML file."""
    try:
        import yaml
        with yaml_path.open('r') as f:
            data = yaml.safe_load(f) or {}
        
        # Navigate through nested keys
        current = data
        for part in config_key.split('.'):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        return True
    except Exception:
        return False


def _set_enhanced_tooltip(widget, control_name: str, config_sources: dict) -> None:
    """Set enhanced structured tooltip with configuration information.
    
    Args:
        widget: Qt widget to set tooltip on
        control_name: Display name for the control
        config_sources: Dict with configuration sources for different settings
    """
    # Get existing tooltip content (description)
    existing_tooltip = widget.toolTip() or "Control description not available"
    
    # Get current default value
    current_value = _get_current_widget_value(widget)
    
    # Build structured tooltip
    tooltip_parts = [
        "-------------------",
        f"<b>{control_name}</b>",
        "",
        existing_tooltip,
        "",
        f"Default Value: {current_value}"
    ]
    
    # Add configuration source information if available
    if 'value' in config_sources:
        tooltip_parts.append(f"Default Value set by: {config_sources['value']}")
    
    if 'disabled' in config_sources:
        tooltip_parts.append(f"Disabled by: {config_sources['disabled']}")
    
    # Set the enhanced tooltip
    widget.setToolTip("\n".join(tooltip_parts))


def _get_current_widget_value(widget) -> str:
    """Get the current value of a widget as a display string."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets
    
    if isinstance(widget, QtWidgets.QSpinBox):
        return str(widget.value())
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        return str(widget.value())
    elif isinstance(widget, QtWidgets.QComboBox):
        current_text = widget.currentText()
        return current_text if current_text else f"Index {widget.currentIndex()}"
    elif isinstance(widget, QtWidgets.QCheckBox):
        return "Checked" if widget.isChecked() else "Unchecked"
    elif isinstance(widget, QtWidgets.QLineEdit):
        text = widget.text()
        return f'"{text}"' if text else '""'
    else:
        return "Unknown"


def _get_control_display_name(control_name: str) -> str:
    """Convert control object name to human-readable display name."""
    # Control name mapping for better tooltip display
    name_mapping = {
        'priority_spin': 'Priority',
        'chunk_size_spin': 'Chunk Size', 
        'frames_combo': 'Frame Range',
        'frame_range_edit': 'Custom Frame Range',
        'use_node_frame_list_check': 'Use Node Frame List',
        'task_timeout_spin': 'Task Timeout',
        'enable_auto_timeout_check': 'Enable Auto Timeout',
        'render_mode_combo': 'Render Mode',
        'render_nukex_check': 'Render with NukeX',
        'use_batch_mode_check': 'Use Batch Mode',
        'reload_plugin_check': 'Reload Plugin',
        'separate_tasks_check': 'Separate Tasks',
        'separate_jobs_check': 'Separate Jobs',
        'views_separate_jobs_check': 'Views Separate Jobs',
        'pool_combo': 'Pool Selection',
        'secondary_pool_combo': 'Secondary Pool',
        'group_combo': 'Group Selection',
        'threads_spin': 'Thread Count',
        'min_ram_spin': 'Minimum RAM',
        'max_ram_spin': 'Maximum RAM',
        'gpu_override_spin': 'GPU Override',
        'use_gpu_check': 'Use GPU',
        'concurrent_tasks_spin': 'Concurrent Tasks',
        'limit_tasks_check': 'Limit Tasks',
        'machine_limit_spin': 'Machine Limit',
        'machine_deny_list_check': 'Machine Deny List',
        'machine_list_edit': 'Machine List',
        'limits_edit': 'Limits',
        'update_btn': 'Update Button',
        'all_btn': 'Select All Button',
        'clear_btn': 'Clear Selection Button',
        'selection_btn': 'Selection Button',
        'inside_groups_check': 'Include Inside Groups',
        'column_dropdown': 'Column Visibility',
        'filter_edit': 'Filter',
        'render_btn': 'Render Button',
        'progress_bar': 'Progress Bar',
        'tab_widget': 'Tab Widget',
        'job_name_edit': 'Job Name',
        'comment_edit': 'Comment',
        'department_edit': 'Department'
    }
    
    return name_mapping.get(control_name, control_name.replace('_', ' ').title())


def _apply_disabled_styling(widget) -> None:
    """Apply visual styling for disabled controls."""
    current_style = widget.styleSheet()
    disabled_style = "color: #808080; background-color: #f5f5f5;"
    widget.setStyleSheet(f"{current_style} {disabled_style}")


def _set_widget_value(widget, value: Any) -> None:
    """Set widget value based on widget type."""
    try:
        from PySide6 import QtWidgets  # Try PySide6 first
    except ImportError:
        from PySide2 import QtWidgets  # Fall back to PySide2
    
    if isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(int(value))
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        widget.setValue(float(value))
    elif isinstance(widget, QtWidgets.QComboBox):
        # Try setting by text first, then by index
        if isinstance(value, str):
            index = widget.findText(value)
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(value, int) and 0 <= value < widget.count():
            widget.setCurrentIndex(value)
    elif isinstance(widget, QtWidgets.QCheckBox):
        widget.setChecked(bool(value))
    elif isinstance(widget, QtWidgets.QLineEdit):
        widget.setText(str(value))
```

### Phase 2: Panel Integration

#### 2.1 Modify Main Panel Class (`nk2dl/gui/panel/panel.py`)

```python
# Add import at top of file
from .config import apply_panel_config

class Nk2dlPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # ... existing initialization ...
        
        # Apply configuration after all UI creation
        self._apply_panel_configuration()
    
    def _apply_panel_configuration(self):
        """Apply configuration to all panel controls."""
        # Apply to settings view controls
        if hasattr(self, 'settings_view'):
            self.settings_view._apply_configuration()
        
        # Apply to node settings view controls  
        if hasattr(self, 'node_settings_view'):
            self.node_settings_view._apply_configuration()
        
        # Apply to main panel controls
        if hasattr(self, 'render_btn'):
            apply_panel_config(self.render_btn)
        if hasattr(self, 'progress_bar'):
            apply_panel_config(self.progress_bar)
        if hasattr(self, 'tab_widget'):
            apply_panel_config(self.tab_widget)
```

#### 2.2 Update View Classes (`nk2dl/gui/panel/views.py`)

Add configuration methods to each view class:

```python
# Add import at top of file
from .config_helper import apply_panel_config

class SettingsView(QtWidgets.QWidget):
    def _apply_configuration(self):
        """Apply configuration to all controls in this view."""
        # Job settings controls
        apply_panel_config(self.priority_spin)
        apply_panel_config(self.chunk_size_spin)
        apply_panel_config(self.frames_combo)
        apply_panel_config(self.frame_range_edit)
        apply_panel_config(self.use_node_frame_list_check)
        apply_panel_config(self.task_timeout_spin)
        apply_panel_config(self.enable_auto_timeout_check)
        apply_panel_config(self.render_mode_combo)
        apply_panel_config(self.render_nukex_check)
        apply_panel_config(self.use_batch_mode_check)
        apply_panel_config(self.reload_plugin_check)
        apply_panel_config(self.separate_tasks_check)
        apply_panel_config(self.separate_jobs_check)
        apply_panel_config(self.views_separate_jobs_check)
        
        # Machine settings controls
        apply_panel_config(self.pool_combo)
        apply_panel_config(self.secondary_pool_combo)
        apply_panel_config(self.group_combo)
        apply_panel_config(self.threads_spin)
        apply_panel_config(self.min_ram_spin)
        apply_panel_config(self.max_ram_spin)
        apply_panel_config(self.gpu_override_spin)
        apply_panel_config(self.use_gpu_check)
        apply_panel_config(self.concurrent_tasks_spin)
        apply_panel_config(self.limit_tasks_check)
        apply_panel_config(self.machine_limit_spin)
        apply_panel_config(self.machine_deny_list_check)
        apply_panel_config(self.machine_list_edit)
        apply_panel_config(self.limits_edit)

class NodeSettingsView(QtWidgets.QWidget):
    def _apply_configuration(self):
        """Apply configuration to all controls in this view."""
        apply_panel_config(self.update_btn)
        apply_panel_config(self.all_btn)
        apply_panel_config(self.clear_btn)
        apply_panel_config(self.selection_btn)
        apply_panel_config(self.inside_groups_check)
        apply_panel_config(self.column_dropdown)
        apply_panel_config(self.filter_edit)
```

### Phase 3: Widget Naming Audit

Ensure all configurable widgets have stable `objectName` values. Based on the current code analysis, most widgets are already accessible as instance attributes. Add explicit naming where needed:

```python
# In view creation methods, ensure object names are set
self.priority_spin.setObjectName("priority_spin")
self.use_gpu_check.setObjectName("use_gpu_check") 
self.pool_combo.setObjectName("pool_combo")
# ... etc for all controls
```

### Phase 4: Documentation

#### 4.1 Update Configuration Documentation

Add to `docs/config.md`:

```markdown
### Panel Configuration

Configure panel UI controls visibility, editability, and default values:

```yaml
panel:
  # Control-specific settings (key = widget objectName)
  priority_spin:
    value: 75        # Set default value
    disabled: true   # Greyed out but visible
  
  use_gpu_check:
    hidden: true     # Completely hidden
  
  pool_combo:
    value: "comp"    # Default selection
```

#### Available Controls

**Job Settings:**
- `priority_spin`, `chunk_size_spin`, `frames_combo`, `frame_range_edit`
- `use_node_frame_list_check`, `task_timeout_spin`, `enable_auto_timeout_check`
- `render_mode_combo`, `render_nukex_check`, `use_batch_mode_check`
- `reload_plugin_check`, `separate_tasks_check`, `separate_jobs_check`, `views_separate_jobs_check`

**Machine Settings:**
- `pool_combo`, `secondary_pool_combo`, `group_combo`, `threads_spin`
- `min_ram_spin`, `max_ram_spin`, `gpu_override_spin`, `use_gpu_check`
- `concurrent_tasks_spin`, `limit_tasks_check`, `machine_limit_spin`
- `machine_deny_list_check`, `machine_list_edit`, `limits_edit`

**Table Controls:**
- `update_btn`, `all_btn`, `clear_btn`, `selection_btn`
- `inside_groups_check`, `column_dropdown`, `filter_edit`

**Essential Controls (Cannot be configured):**
- `render_btn`, `progress_bar`, `tab_widget`
```

## Enhanced Configuration Tooltips

### Tooltip Format

All tooltips will follow a structured format that provides comprehensive information:

```
-------------------
ControlName (bold)

The original tooltip content

Default Value: X
Default Value set by: <Path to config file or envvar> (optional)
Disabled by: <Path to config file or envvar> (optional)
```

### Tooltip Examples

**Priority Spinbox (with default value and disabled):**
```
-------------------
Priority

Set the job priority for render queue (0-100)

Default Value: 75
Default Value set by: Environment Variable (NK2DL_PANEL_PRIORITY_SPIN_VALUE)
Disabled by: User Config (/home/user/.nk2dl/config.yaml)
```

**Pool Combo (with default value only):**
```
-------------------
Pool Selection

Choose the render farm pool for job execution

Default Value: comp
Default Value set by: Project Config (/studio/nk2dl/config.yaml)
```

**Standard Control (no configuration):**
```
-------------------
Chunk Size

Number of frames to render per task

Default Value: 10
```

**Hidden Control:**
- Hidden controls don't display tooltips since they're not visible

### Tooltip Behavior

- **Structured Format**: All tooltips follow the same clear structure with separator line and bold control name
- **Preserves Original Content**: Original widget tooltip content is maintained in the description area
- **Always Shows Default**: Even unconfigured controls show their current default value
- **Optional Config Info**: Configuration source lines only appear when values are actually set by configuration
- **Clear Attribution**: Shows exact config source (file path or environment variable name)
- **Multiple Sources**: Can show both default value source and disabled state source independently

## Right-Click Context Menus

### Context Menu Features

All configurable controls will have right-click context menus with reset options:

#### **Individual Reset**
- **"Set to Default"** - Resets just the clicked control to its original default value

#### **Group Reset**
- **"Set Job Settings to Default"** - Resets all job-related controls (priority, chunk size, render mode, etc.)
- **"Set Machine Settings to Default"** - Resets all machine-related controls (pool, threads, RAM, GPU, etc.)
- **"Set Table Controls to Default"** - Resets table interaction controls (filters, column visibility, etc.)
- **"Set Extra Settings to Default"** - Resets job information controls (name, comment, department)

#### **Panel-Wide Reset**
- **"Set All to Default"** - Resets every control in the panel to original defaults

### Control Groups

Controls are organized into logical groups for context menu actions:

```python
CONTROL_GROUPS = {
    'job_settings': {
        'priority_spin', 'chunk_size_spin', 'frames_combo', 'frame_range_edit',
        'use_node_frame_list_check', 'task_timeout_spin', 'enable_auto_timeout_check',
        'render_mode_combo', 'render_nukex_check', 'use_batch_mode_check',
        'reload_plugin_check', 'separate_tasks_check', 'separate_jobs_check',
        'views_separate_jobs_check'
    },
    'machine_settings': {
        'pool_combo', 'secondary_pool_combo', 'group_combo', 'threads_spin',
        'min_ram_spin', 'max_ram_spin', 'gpu_override_spin', 'use_gpu_check',
        'concurrent_tasks_spin', 'limit_tasks_check', 'machine_limit_spin',
        'machine_deny_list_check', 'machine_list_edit', 'limits_edit'
    },
    'table_controls': {
        'update_btn', 'all_btn', 'clear_btn', 'selection_btn',
        'inside_groups_check', 'column_dropdown', 'filter_edit'
    },
    'extra_settings': {
        'job_name_edit', 'comment_edit', 'department_edit'
    }
}
```

### Context Menu Behavior

- **Available on All Controls**: Even essential controls get context menus (though they can't be hidden/disabled)
- **Intelligent Grouping**: Menu shows group-specific reset options based on the control's category
- **Original Values**: System stores original widget defaults before applying any configuration
- **Disabled Controls**: Context menu works even on configuration-disabled controls
- **Hidden Controls**: Hidden controls obviously don't show context menus since they're invisible

### Example Context Menu

For a priority spinbox in the Job Settings group:
```
┌─────────────────────────────┐
│ Set to Default              │
│ Set Job Settings to Default │
│ ─────────────────────────── │
│ Set All to Default          │
└─────────────────────────────┘
```

For a control not in a specific group:
```
┌─────────────────────────────┐
│ Set to Default              │
│ ─────────────────────────── │
│ Set All to Default          │
└─────────────────────────────┘
```

### Implementation Details

#### **Default Value Storage**
- Original widget values are captured in `_widget_defaults` before configuration is applied
- This ensures "default" means the original widget state, not configuration-modified state

#### **Widget Discovery**
- Context menu handlers can find and reset other widgets through the panel hierarchy
- Smart widget lookup through direct attributes and `findChildren()` methods

#### **Safe Reset**
- Reset operations handle missing widgets gracefully
- Type-appropriate value setting for different widget types

#### **Menu Positioning**
- Context menus appear at the cursor position relative to the clicked widget

## Implementation Examples

### Artist Lockdown Configuration

```yaml
panel:
  # Hide advanced machine controls
  secondary_pool_combo:
    hidden: true
  group_combo:
    hidden: true
  machine_limit_spin:
    hidden: true
  machine_deny_list_check:
    hidden: true
  machine_list_edit:
    hidden: true
  limits_edit:
    hidden: true
  
  # Disable core settings but show current values
  pool_combo:
    disabled: true
  threads_spin:
    disabled: true
    value: 8
  
  # Set conservative defaults
  priority_spin:
    value: 50
  chunk_size_spin:
    value: 5
  use_batch_mode_check:
    value: true
```

### Environment Variable Deployment

```bash
# Studio environment setup
export NK2DL_PANEL_SECONDARY__POOL__COMBO_HIDDEN=true
export NK2DL_PANEL_POOL__COMBO_DISABLED=true  
export NK2DL_PANEL_PRIORITY__SPIN_VALUE=50
```

## Risk Mitigation

### Essential Controls Protection
- Essential controls (`render_btn`, `tab_widget`, etc.) are automatically protected
- Configuration attempts on essential controls are ignored

### Invalid Configuration Handling
- Invalid control names are silently ignored (no errors)
- Invalid values fall back to widget defaults
- Malformed config sections don't break panel functionality

### Tooltip Safety
- Missing or inaccessible config files don't break tooltip functionality
- Tooltip generation failures are handled gracefully
- Original widget tooltips are preserved

### Backwards Compatibility  
- Panel works identically when no configuration provided
- New `panel` section is completely optional
- Existing configuration sections remain unchanged

## Testing Strategy

### Unit Tests
- Test `apply_panel_config()` with mock widgets
- Test configuration parsing and environment variable handling
- Test essential controls protection

### Integration Tests
- Panel functionality with various configuration scenarios
- Configuration precedence testing (file vs env vars vs user config)
- Widget state verification after configuration application

## Timeline Estimate

- **Day 1:** Configuration infrastructure and helper module
- **Day 2:** Panel integration, widget naming audit, and context menu implementation
- **Day 3:** View class updates, tooltip functionality, and testing
- **Day 4:** Documentation and final QA

**Total: 4 developer days**

## Roll-out Strategy

1. **Phase 1:** Merge code with empty default configuration (no behavior change)
2. **Phase 2:** Provide example configurations in documentation
3. **Phase 3:** Studio deployment with artist lockdown configurations
4. **Phase 4:** Gather feedback and iterate on control granularity 