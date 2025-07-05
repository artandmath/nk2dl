# Render Checkbox Column Implementation Plan

## Overview
Add a new checkbox column "Render" as the first column (before "Order") in the node settings table. This column will contain boolean checkboxes to control which nodes should be rendered. Since it becomes the new first column, it will be part of the frozen table (frozen columns = 4 instead of 3).

## Current Architecture Analysis

### Frozen Table Structure
- **Current**: 3 frozen columns: Order (0), Node (1), Filename (2)
- **Target**: 4 frozen columns: Render (0), Order (1), Node (2), Filename (3)
- **Impact**: All column indices shift by +1, frozen_column_count changes from 3 to 4

### Key Files and Components
1. **Constants** (`nk2dl/gui/panel/constants.py`)
   - `TableColumns.HEADERS` list - needs "Render" inserted at position 0
   - `TableColumns.HEADER_DISPLAY_NAMES` - needs "Render" entry
   - `TableColumns.COLUMN_GROUPS["Fixed"]` - needs "Render" added
   - `TableColumns.COLUMN_WIDTH_SETTINGS` - needs checkbox column sizing
   - `HeaderSettingsMapping.MACHINE_SETTINGS_COLUMNS` - indices need updating (+1)
   - New constants for checkbox padding

2. **Frozen Table Widget** (`nk2dl/gui/panel/widgets/table_widgets.py`)
   - `frozen_column_count` changes from 3 to 4
   - All frozen column logic needs to handle the new checkbox column
   - Checkbox rendering and interaction

3. **Table Model** (`nk2dl/gui/panel/models/table_model.py`)
   - Checkbox data storage and retrieval
   - Validation for checkbox column
   - Default values for new nodes

4. **Delegates** (`nk2dl/gui/panel/delegates.py`)
   - Custom checkbox delegate for proper rendering and interaction
   - Exclude checkbox column from inheritance logic

5. **Node Settings View** (`nk2dl/gui/panel/views/node_settings_view.py`)
   - Handle checkbox column in data loading/saving
   - Column width management for non-resizable checkbox column

## Implementation Tasks

### Phase 1: Constants and Data Structure

#### 1.1 Update Constants (`constants.py`)
```python
# Add checkbox padding constant
CHECKBOX_COLUMN_PADDING = 5  # 5 pixels each side as requested

# Update HEADERS list
HEADERS = [
    "Render",  # NEW - checkbox column  
    "Order", "Node", "Filename", "Priority", "ChunkSize", "Frames", 
    "NodesFrames", "TaskTimeout", "AutoTimeout", "RenderMode", 
    "NukeX", "BatchMode", "ReloadPlugin", "Pool", "SecondaryPool", 
    "Group", "Threads", "MinRam", "MaxRam", "UseGPU", "GPUId", 
    "ConcurrentTasks", "WorkerTaskLimit", "MachineList", "Limits"
]

# Update HEADER_DISPLAY_NAMES
HEADER_DISPLAY_NAMES = {
    "Render": "",  # Empty string = no header text shown
    "Order": "Order",
    # ... rest unchanged
}

# Update COLUMN_GROUPS
COLUMN_GROUPS = {
    "Fixed": ["Render", "Order", "Node", "Filename"],  # Added "Render"
    # ... rest unchanged
}

# Update COLUMN_WIDTH_SETTINGS
"min_widths": {
    "Render": 30,  # Checkbox + padding (20px checkbox + 10px padding)
    # ... rest unchanged
},
"max_widths": {
    "Render": 30,  # Same as min (non-resizable)
    # ... rest unchanged
}

# Update MACHINE_SETTINGS_COLUMNS indices (+1 each)
MACHINE_SETTINGS_COLUMNS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]  # All +1
```

#### 1.2 Update HeaderSettingsMapping (`constants.py`)
```python
# Render column has no settings mapping (not inheritable)
# All mapping indices remain the same since we use header names, not indices
# But any hardcoded column indices need updating (+1)
```

### Phase 2: Checkbox Delegate (Create Table-Specific Version)

#### 2.1 Add TableCheckboxDelegate to `delegates.py` (Single File)
**Problem**: `CenteredCheckboxDelegate` is already used by GSV tree widgets. Modifying it could break existing functionality.

**Solution**: Add a new table-specific delegate to the existing `delegates.py` file with organized sections:

```python
# ============================================================================
# Checkbox Delegates
# ============================================================================
class CenteredCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate that centers checkboxes in tree widget columns."""
    # ... existing implementation (unchanged)

class TableCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate for checkbox columns in table widgets."""
    # ... new implementation below

# ============================================================================
# Combined Delegates  
# ============================================================================
class CombinedTableDelegate(QtWidgets.QStyledItemDelegate):
    """Combined delegate handling both checkboxes and settings inheritance."""
    # ... implementation below
```

**New delegate implementation:**

```python
class TableCheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate for checkbox columns in table widgets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Paint checkbox centered in table cell."""
        value = index.data(QtCore.Qt.CheckStateRole)
        
        if value is not None and index.column() == 0:  # Render column
            # Use Qt's default checkbox rendering for table widgets
            # Qt automatically centers checkboxes when ItemIsUserCheckable is set
            super().paint(painter, option, index)
        else:
            # Normal cell rendering for non-checkbox columns
            super().paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse events for toggling checkbox."""
        if (index.column() == 0 and  # Render column
            event.type() == QtCore.QEvent.MouseButtonRelease and
            event.button() == QtCore.Qt.LeftButton):
            
            # Toggle checkbox state
            current_value = index.data(QtCore.Qt.CheckStateRole)
            new_value = QtCore.Qt.Unchecked if current_value == QtCore.Qt.Checked else QtCore.Qt.Checked
            return model.setData(index, new_value, QtCore.Qt.CheckStateRole)
        
        return super().editorEvent(event, model, option, index)
```

**Why create a new delegate:**
- ✅ **Preserves existing functionality** - GSV tree widgets continue working
- ✅ **Table-specific optimization** - Simpler logic for table widgets
- ✅ **Clear separation of concerns** - Tree vs Table checkbox handling
- ✅ **Future-proof** - Changes to one don't affect the other

### Phase 3: Frozen Table Widget Updates

#### 3.1 Update FrozenTableWidget (`table_widgets.py`)
```python
class FrozenTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # CHANGE: Increase frozen column count from 3 to 4
        self.frozen_column_count = 4  # Render, Order, Node, Filename
        
        # ... rest of initialization unchanged
        
        logger.info("FrozenTableWidget created with 4 frozen columns")

    def setItem(self, row, column, item):
        """Enhanced setItem to handle checkbox column."""
        super().setItem(row, column, item)
        
        # Handle checkbox column specially
        if column == 0:  # Render column
            # Set item as checkable
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            # Set default checked state if not already set
            if item.checkState() == QtCore.Qt.PartiallyChecked:
                item.setCheckState(QtCore.Qt.Checked)  # Default to checked
        
        # Sync to frozen table if frozen column
        if column < self.frozen_column_count:
            # Create copy for frozen table
            frozen_item = QtWidgets.QTableWidgetItem(item.text())
            frozen_item.setData(QtCore.Qt.UserRole, item.data(QtCore.Qt.UserRole))
            frozen_item.setFont(item.font())
            frozen_item.setForeground(item.foreground())
            frozen_item.setBackground(item.background())
            
            # Copy checkbox state for render column
            if column == 0:
                frozen_item.setFlags(frozen_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                frozen_item.setCheckState(item.checkState())
            
            self.frozen_table.setItem(row, column, frozen_item)
```

#### 3.2 Make Render Column Non-Resizable
```python
def _setup_column_resize_modes(self):
    """Set resize modes for columns."""
    header = self.horizontalHeader()
    frozen_header = self.frozen_table.horizontalHeader()
    
    # Make render column (0) non-resizable
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
    frozen_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
    
    # Set fixed width for render column
    render_width = 30  # Checkbox + padding
    self.setColumnWidth(0, render_width)
    self.frozen_table.setColumnWidth(0, render_width)
    
    # All other columns remain Interactive (resizable)
    for col in range(1, self.columnCount()):
        if col < self.frozen_column_count:
            frozen_header.setSectionResizeMode(col, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(col, QtWidgets.QHeaderView.Interactive)
```

### Phase 4: Table Model Updates

#### 4.1 Update TableDataModel (`table_model.py`)
```python
def get_cell_value(self, row, column):
    """Enhanced to handle checkbox column."""
    if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
        return ""
    
    header = self._headers[column]
    
    # Handle checkbox column specially
    if header == "Render":
        # Return boolean value, default to True for new nodes
        return self._data[row].get(header, True)
    
    # Normal handling for other columns
    value = self._data[row].get(header, None)
    return value

def set_cell_value(self, row, column, value, emit_signal=True):
    """Enhanced to handle checkbox column."""
    if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
        return
    
    header = self._headers[column]
    
    # Handle checkbox column
    if header == "Render":
        # Store as boolean
        bool_value = bool(value) if value is not None else True
        old_value = self._data[row].get(header, True)
        
        if old_value != bool_value:
            self._data[row][header] = bool_value
            
            # No settings storage for checkbox column
            
            if emit_signal:
                self.dataChanged.emit()
        return
    
    # Normal handling for other columns...
    # ... existing code unchanged

def is_column_editable(self, column):
    """Enhanced to handle checkbox column."""
    if column < 0 or column >= len(self._headers):
        return False
    
    header = self._headers[column]
    
    # Render column is editable (checkbox toggle)
    if header == "Render":
        return True
    
    # Node and Filename are read-only
    if header in ["Node", "Filename"]:
        return False
    
    # All other columns are editable
    return True
```

### Phase 5: Node Settings View Updates

#### 5.1 Update NodeSettingsView (`node_settings_view.py`)
```python
def _create_table(self):
    """Enhanced table creation with checkbox delegate."""
    # ... existing code ...
    
    # Set up combined delegate
    combined_delegate = CombinedTableDelegate(self.table_model)
    self.render_table.setItemDelegate(combined_delegate)
    
    # ... rest unchanged

def _setup_column_properties(self):
    """Set up column-specific properties."""
    headers = self.table_model.get_headers()
    
    for col, header in enumerate(headers):
        if header == "Render":
            # Set fixed width for checkbox column
            width = 30  # Checkbox + padding
            self.render_table.setColumnWidth(col, width)
            
            # Set non-resizable
            self.render_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.Fixed)
            
            if hasattr(self.render_table, 'frozen_table'):
                self.render_table.frozen_table.setColumnWidth(col, width)
                self.render_table.frozen_table.horizontalHeader().setSectionResizeMode(
                    col, QtWidgets.QHeaderView.Fixed)

def _load_data_from_model(self):
    """Enhanced data loading with checkbox handling."""
    # ... existing code for loading data ...
    
    # Set up checkbox items
    for row in range(self.render_table.rowCount()):
        checkbox_item = self.render_table.item(row, 0)  # Render column
        if checkbox_item:
            checkbox_item.setFlags(checkbox_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            
            # Get checkbox value from model
            render_value = self.table_model.get_cell_value(row, 0)
            checkbox_state = QtCore.Qt.Checked if render_value else QtCore.Qt.Unchecked
            checkbox_item.setCheckState(checkbox_state)
```

#### 5.2 Create Combined Delegate (Using New Table Delegate)
```python
class CombinedTableDelegate(QtWidgets.QStyledItemDelegate):
    """Combined delegate handling both checkboxes and settings inheritance."""
    
    def __init__(self, table_model, parent=None):
        super().__init__(parent)
        self.table_model = table_model
        self.checkbox_delegate = TableCheckboxDelegate()  # Use new table-specific delegate
        self.settings_delegate = SettingsAwareDelegate(table_model)
    
    def paint(self, painter, option, index):
        if index.column() == 0:  # Render column
            self.checkbox_delegate.paint(painter, option, index)
        else:
            self.settings_delegate.paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index):
        if index.column() == 0:  # Render column
            return self.checkbox_delegate.editorEvent(event, model, option, index)
        else:
            return self.settings_delegate.editorEvent(event, model, option, index)
    
    def createEditor(self, parent, option, index):
        if index.column() == 0:  # Render column
            return None  # No editor needed for checkbox
        else:
            return self.settings_delegate.createEditor(parent, option, index)
```

## Testing Strategy

### Test Cases
1. **Checkbox Functionality**
   - Click checkbox toggles state
   - State persists through data refreshes
   - Default state for new nodes is checked

2. **Frozen Table Synchronization**
   - Checkbox state syncs between main and frozen tables
   - Column resizing works correctly with fixed render column
   - Scrolling doesn't affect checkbox column visibility

3. **Column Width Management**
   - Render column maintains fixed 30px width
   - Non-resizable behavior works correctly
   - Other columns remain resizable

4. **Data Persistence**
   - Checkbox states saved/loaded correctly
   - No interference with existing inheritance system
   - Column mappings work correctly after index shift

### Backwards Compatibility
- Existing data files without "Render" column should default to checked
- All existing functionality should work with new column indices
- No breaking changes to API or data formats

## Implementation Order

1. **Phase 1**: Update constants and data structures
2. **Phase 2**: Create checkbox delegate
3. **Phase 3**: Update frozen table widget
4. **Phase 4**: Update table model  
5. **Phase 5**: Update node settings view
6. **Testing**: Verify all functionality works correctly

## Risk Mitigation

### Potential Issues
1. **Column Index Shifts**: All hardcoded column indices need updating
2. **Frozen Table Sync**: Checkbox state must sync between tables
3. **Signal Connections**: Existing signals must handle checkbox column
4. **Performance**: Adding column increases data processing

### Solutions
1. Use header names instead of indices where possible
2. Enhanced setItem() method handles synchronization
3. Delegate pattern isolates checkbox logic
4. Minimal performance impact for single column addition

## File Changes Summary

### Modified Files
- `nk2dl/gui/panel/constants.py` - Add constants and update lists
- `nk2dl/gui/panel/widgets/table_widgets.py` - Update frozen column count and handling
- `nk2dl/gui/panel/models/table_model.py` - Add checkbox data handling  
- `nk2dl/gui/panel/delegates.py` - Add `TableCheckboxDelegate` and `CombinedTableDelegate` (organized single file)
- `nk2dl/gui/panel/views/node_settings_view.py` - Update table creation and data loading

### Testing Files
- Create checkbox-specific test cases
- Update existing tests for new column indices
- Verify frozen table functionality with 4 columns

This plan ensures the checkbox column is properly integrated while maintaining all existing functionality and avoiding breaking changes to the frozen table synchronization system. 