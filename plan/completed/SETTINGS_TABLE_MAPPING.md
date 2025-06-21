# Settings-Table Relationship Mapping Plan

## Overview

This document outlines the implementation of a relationship mapping system between table column headers and job/machine settings. This replaces the previous master row functionality with a more robust inheritance system where table cells can inherit values from settings or override them with explicit values.

## Current State Analysis

### What We Have
- ✅ `StandardTableWidget` without master row functionality
- ✅ `TableDataModel` with simplified data management
- ✅ `SettingsModel` with job and machine settings
- ✅ Working settings panel that updates settings model

### What We Need
- 🔄 Mapping between table columns and settings fields
- 🔄 Inheritance logic (empty cells inherit from settings)
- 🔄 Override detection (explicit values override settings)
- 🔄 Visual indication (bold text for overrides)
- 🔄 Enhanced dropdown menus with inheritance options

## Relationship Mapping Design

### Column-to-Settings Mapping

Based on the current table headers and settings model, here are the relationships:

#### Job Settings Relationships
| Table Column | Settings Field | Widget in Settings Panel |
|--------------|----------------|---------------------------|
| `Priority` | `priority` | Priority spinbox |
| `Chunk` | `chunk_size` | Chunk Size spinbox |
| `NodesFrames` | `use_node_frame_list` | "Use node's frame list" checkbox |
| `TaskTimeout` | `task_timeout` | Task Timeout spinbox |
| `AutoTimeout` | `enable_auto_timeout` | "Enable auto task timeout" checkbox |
| `RenderMode` | `render_mode` | Render Mode dropdown |
| `NukeX` | `use_nukex` | "Use Nuke X" checkbox |
| `BatchMode` | `use_batch_mode` | "Use batch mode" checkbox |
| `Reloadplugin` | `reload_plugin` | "Reload plugin between tasks" checkbox |

#### Machine Settings Relationships
| Table Column | Settings Field | Widget in Settings Panel |
|--------------|----------------|---------------------------|
| `Pool` | `pool` | Pool dropdown |
| `SecondaryPool` | `secondary_pool` | Secondary Pool dropdown |
| `Group` | `group` | Group dropdown |
| `Threads` | `threads` | Threads spinbox |
| `MinRam` | `min_ram` | Min RAM spinbox |
| `MaxRam` | `max_ram` | Max RAM spinbox |
| `UseGPU` | `use_gpu` | "Use GPU" checkbox |
| `GPUId` | `gpu_device` | GPU Device spinbox |
| `ConcurrentTasks` | `concurrent_tasks` | Concurrent Tasks spinbox |
| `WorkerTaskLimit` | `limit_tasks` | "Limit tasks to worker's task limit" checkbox |
| `MachineList` | `machine_list` | Machine List text field |
| `Limits` | `limits` | Limits text field |

#### Unmapped Columns
These columns have no settings relationship and work as normal table cells:
- `Order` - User-defined execution order
- `Node` - Node name (from Nuke scene)
- `Filename` - Output filename (from Write node)
- `Frames` - Frame range (can be overridden per node)

## Implementation Architecture

### 1. Constants and Mapping

```python
# In constants.py
class HeaderSettingsMapping:
    """Mapping between table column headers and job/machine settings."""
    
    # Job Settings Relationships
    JOB_SETTINGS_MAPPING = {
        "Priority": "priority",
        "Chunk": "chunk_size", 
        "NodesFrames": "use_node_frame_list",
        "TaskTimeout": "task_timeout",
        "AutoTimeout": "enable_auto_timeout",
        "RenderMode": "render_mode",
        "NukeX": "use_nukex",
        "BatchMode": "use_batch_mode",
        "Reloadplugin": "reload_plugin"
    }
    
    # Machine Settings Relationships
    MACHINE_SETTINGS_MAPPING = {
        "Pool": "pool",
        "SecondaryPool": "secondary_pool",
        "Group": "group",
        "Threads": "threads",
        "MinRam": "min_ram",
        "MaxRam": "max_ram",
        "UseGPU": "use_gpu",
        "GPUId": "gpu_device",
        "ConcurrentTasks": "concurrent_tasks",
        "WorkerTaskLimit": "limit_tasks",
        "MachineList": "machine_list",
        "Limits": "limits"
    }
    
    # Dropdown inheritance labels
    JOB_SETTINGS_INHERITANCE_LABEL = "Use job settings"
    MACHINE_SETTINGS_INHERITANCE_LABEL = "Use machine settings"
    DROPDOWN_SEPARATOR = "-----"
```

### 2. Enhanced TableDataModel

```python
# In models.py - TableDataModel enhancements
class TableDataModel(QtCore.QObject):
    def __init__(self, settings_model=None, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = TableColumns.HEADERS.copy()
        self.settings_model = settings_model
    
    def get_effective_cell_value(self, row, column):
        """Get the effective value for a cell (explicit or inherited)."""
        # Get explicit cell value
        explicit_value = self.get_cell_value(row, column)
        
        # If explicit value exists and is not empty, return it
        if explicit_value and explicit_value.strip():
            return explicit_value
        
        # Otherwise, try to inherit from settings
        return self._get_inherited_value(column)
    
    def _get_inherited_value(self, column):
        """Get inherited value from settings for a column."""
        if not self.settings_model:
            return ""
        
        setting_type, setting_key = self.get_setting_for_column(column)
        if not setting_type or not setting_key:
            return ""
        
        if setting_type == "job":
            value = self.settings_model.get_job_setting(setting_key)
        elif setting_type == "machine":
            value = self.settings_model.get_machine_setting(setting_key)
        else:
            return ""
        
        # Convert setting value to table display format
        return self._convert_setting_to_display(column, value)
    
    def _convert_setting_to_display(self, column, setting_value):
        """Convert setting value to table display format."""
        header = self._headers[column]
        
        # Boolean settings → Yes/No
        if header in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", 
                      "Reloadplugin", "UseGPU", "WorkerTaskLimit"]:
            return "Yes" if setting_value else "No"
        
        # Numeric settings → String
        if header in ["Priority", "Chunk", "TaskTimeout", "Threads", 
                      "MinRam", "MaxRam", "GPUId", "ConcurrentTasks"]:
            return str(setting_value)
        
        # String settings → Direct
        return str(setting_value) if setting_value else ""
    
    def is_cell_overridden(self, row, column):
        """Check if cell has an explicit override value."""
        explicit_value = self.get_cell_value(row, column)
        inherited_value = self._get_inherited_value(column)
        
        # Cell is overridden if it has explicit value different from inherited
        return (explicit_value and explicit_value.strip() and 
                explicit_value != inherited_value)
    
    def get_setting_for_column(self, column):
        """Get setting type and key for a column."""
        if column < 0 or column >= len(self._headers):
            return None, None
        
        header = self._headers[column]
        
        if header in HeaderSettingsMapping.JOB_SETTINGS_MAPPING:
            return "job", HeaderSettingsMapping.JOB_SETTINGS_MAPPING[header]
        elif header in HeaderSettingsMapping.MACHINE_SETTINGS_MAPPING:
            return "machine", HeaderSettingsMapping.MACHINE_SETTINGS_MAPPING[header]
        else:
            return None, None
```

### 3. Settings-Aware Delegate

```python
# In delegates.py - New SettingsAwareDelegate
class SettingsAwareDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate that handles settings inheritance and override styling."""
    
    def __init__(self, table_model, parent=None):
        super().__init__(parent)
        self.table_model = table_model
    
    def paint(self, painter, option, index):
        """Paint cell with bold text for overridden values."""
        # Check if cell is overridden
        if self.table_model.is_cell_overridden(index.row(), index.column()):
            # Create new option with bold font
            new_option = QtWidgets.QStyleOptionViewItem(option)
            new_option.font.setBold(True)
            super().paint(painter, new_option, index)
        else:
            super().paint(painter, option, index)
    
    def displayText(self, value, locale):
        """Display effective value (explicit or inherited)."""
        # This will be called to get the display text
        # The view should already be showing effective values
        return super().displayText(value, locale)
    
    def createEditor(self, parent, option, index):
        """Create editor with inheritance options for dropdown columns."""
        column = index.column()
        
        if not self.table_model.is_dropdown_column(column):
            # Use default editor for non-dropdown columns
            return super().createEditor(parent, option, index)
        
        # Create dropdown editor with inheritance options
        editor = QtWidgets.QComboBox(parent)
        editor.setEditable(False)
        
        # Populate dropdown based on column type
        self._populate_dropdown_editor(editor, column)
        
        return editor
    
    def _populate_dropdown_editor(self, editor, column):
        """Populate dropdown editor with options and inheritance choice."""
        header = self.table_model.get_headers()[column]
        setting_type, setting_key = self.table_model.get_setting_for_column(column)
        
        # Add standard options first
        if header in ["NodesFrames", "AutoTimeout", "NukeX", "BatchMode", "Reloadplugin", "UseGPU", "WorkerTaskLimit"]:
            # Yes/No columns
            editor.addItems(["Yes", "No"])
        elif header == "RenderMode":
            editor.addItems(["Full", "Proxy", "Both", "Script"])
        elif header == "Pool":
            editor.addItems(["comp", "lighting", "render", "fx", "general"])
        elif header == "SecondaryPool":
            editor.addItems(["", "comp", "lighting", "render", "fx", "general"])
        elif header == "Group":
            editor.addItems(["none", "high_priority", "weekend", "overnight"])
        
        # Add separator and inheritance option
        if setting_type:
            editor.insertSeparator(editor.count())
            if setting_type == "job":
                editor.addItem(HeaderSettingsMapping.JOB_SETTINGS_INHERITANCE_LABEL)
            elif setting_type == "machine":
                editor.addItem(HeaderSettingsMapping.MACHINE_SETTINGS_INHERITANCE_LABEL)
    
    def setEditorData(self, editor, index):
        """Set editor data with current effective value."""
        if isinstance(editor, QtWidgets.QComboBox):
            # Get current effective value
            current_value = self.table_model.get_effective_cell_value(
                index.row(), index.column())
            
            # Find and select the current value
            index_to_select = editor.findText(current_value)
            if index_to_select >= 0:
                editor.setCurrentIndex(index_to_select)
            else:
                # If not found, check if it's an inherited value
                explicit_value = self.table_model.get_cell_value(
                    index.row(), index.column())
                if not explicit_value or not explicit_value.strip():
                    # Select inheritance option
                    setting_type, _ = self.table_model.get_setting_for_column(index.column())
                    if setting_type == "job":
                        inheritance_index = editor.findText(
                            HeaderSettingsMapping.JOB_SETTINGS_INHERITANCE_LABEL)
                    elif setting_type == "machine":
                        inheritance_index = editor.findText(
                            HeaderSettingsMapping.MACHINE_SETTINGS_INHERITANCE_LABEL)
                    else:
                        inheritance_index = -1
                    
                    if inheritance_index >= 0:
                        editor.setCurrentIndex(inheritance_index)
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        """Set model data from editor, handling inheritance."""
        if isinstance(editor, QtWidgets.QComboBox):
            selected_text = editor.currentText()
            
            # Check if inheritance option was selected
            if (selected_text == HeaderSettingsMapping.JOB_SETTINGS_INHERITANCE_LABEL or
                selected_text == HeaderSettingsMapping.MACHINE_SETTINGS_INHERITANCE_LABEL):
                # Clear the cell to use inheritance
                model.setData(index, "", QtCore.Qt.EditRole)
            else:
                # Set explicit value
                model.setData(index, selected_text, QtCore.Qt.EditRole)
        else:
            super().setModelData(editor, model, index)
```

## Implementation Steps

### Step 1: Add Constants and Mapping
1. Add `HeaderSettingsMapping` class to `constants.py`
2. Define all column-to-setting relationships
3. Add inheritance labels and separator constants

### Step 2: Enhance TableDataModel
1. Add settings_model parameter to constructor
2. Implement `get_effective_cell_value()` method
3. Implement `is_cell_overridden()` method
4. Implement `get_setting_for_column()` method
5. Add value conversion methods

### Step 3: Create SettingsAwareDelegate
1. Create new delegate class in `delegates.py`
2. Implement bold text styling for overrides
3. Implement dropdown editors with inheritance options
4. Handle inheritance selection logic

### Step 4: Update Views and Integration
1. Update `NodeSettingsView` to pass settings_model to table_model
2. Update `StandardTableWidget` to use `SettingsAwareDelegate`
3. Connect settings model change signals to table refresh
4. Update panel integration

### Step 5: Update Display Logic
1. Modify table loading to show effective values
2. Ensure bold styling appears for overrides
3. Test inheritance behavior with settings changes

## Testing Strategy

### Unit Testing
- Test mapping constants are complete and correct
- Test inheritance logic with various setting values
- Test override detection with different cell states
- Test value conversion between settings and display formats

### Integration Testing
- Test settings panel changes update table immediately
- Test table cell editing updates model correctly
- Test inheritance vs override behavior
- Test dropdown menus show correct options

### Visual Testing
- Verify bold text appears only for override values
- Verify inherited values display correctly
- Test dropdown menus with inheritance options
- Confirm separator lines display properly

### User Experience Testing
- Test workflow: change setting → see table update
- Test workflow: edit cell → see override in bold
- Test workflow: clear cell → revert to inheritance
- Test workflow: select "Use job/machine settings" → clear override

## Benefits of This Approach

1. **Clear Separation**: Settings and table data are clearly separated
2. **Visual Feedback**: Bold text clearly indicates overrides
3. **Flexible**: Users can override any setting per row
4. **Intuitive**: Dropdown inheritance options are self-explanatory
5. **Maintainable**: Mapping is centralized and easy to modify
6. **Extensible**: Easy to add new column-setting relationships

## Migration from Master Row

This approach provides the same functionality as the master row system but with better UX:

| Master Row System | New Inheritance System |
|-------------------|------------------------|
| First row contains defaults | Settings panel contains defaults |
| Empty cells inherit from row 0 | Empty cells inherit from settings |
| No visual indication of inheritance | Bold text shows overrides |
| Master row can be accidentally edited | Settings are protected in settings panel |
| Complex fallback logic | Simple inheritance logic |
| Confusing for users | Intuitive dropdown options |

This system is more robust, user-friendly, and maintainable than the previous master row approach. 