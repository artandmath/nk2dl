# Panel Refactoring Plan

## Overview

This document outlines the refactoring plan for `nk2dl/gui/panel.py` (2600+ lines) into a maintainable, modular architecture following proven patterns from similar projects like [nuke_node_table](https://gitlab.com/filmkorn/nuke_node_table/-/tree/master/node_table).

## Current Issues

- **Monolithic file**: 2600+ lines in a single file
- **Mixed responsibilities**: UI, data, and business logic intertwined
- **Hard to test**: Components tightly coupled
- **Difficult maintenance**: Changes affect multiple concerns
- **Poor reusability**: Custom widgets embedded in main class

## Goals

- **Separation of concerns**: Logical grouping of related functionality
- **Maintainability**: Smaller, focused files that are easier to understand
- **Testability**: Components can be unit tested in isolation
- **Reusability**: Custom widgets can be reused across projects
- **Simplicity**: Keep it simple - avoid over-engineering

## Proposed File Structure

**Simple 6-file structure** (inspired by nuke_node_table):

```
nk2dl/gui/
├── __init__.py
├── panel/                    # Panel module
│   ├── __init__.py
│   ├── constants.py          # ✅ Colors, themes, sizes (already created)
│   ├── widgets.py           # All custom widgets (~400 lines)
│   ├── delegates.py         # All custom delegates (~350 lines)
│   ├── models.py           # All data models (~200 lines)
│   ├── views.py            # All view components (~600 lines)
│   └── panel.py            # Main panel class (~300 lines)
└── panel.py                 # Legacy file (will be removed after refactoring)
```

**Total: 6 files in panel module instead of current 1 monolithic file**

## File Breakdown

### 1. `panel/constants.py` ✅ (Already Created)
**Purpose**: Centralized configuration
**Size**: ~50 lines
**Content**:
- Color themes and styling
- Table column definitions
- Default values and messages
- Size constants

### 2. `panel/widgets.py` (~400 lines)
**Purpose**: All custom widget classes
**Content**:
```python
# Extract from current panel.py:
class ColoredGroupBox(QtWidgets.QGroupBox):          # Lines 546-607
class PinnedRowTableWidget(QtWidgets.QTableWidget):  # Lines 27-376  
class GroupedHeaderView(QtWidgets.QHeaderView):      # Lines 378-544

# New helper classes:
class ResponsiveContainer(QtWidgets.QWidget):        # Extract responsive logic
```

### 3. `panel/delegates.py` (~350 lines)
**Purpose**: All custom item delegates
**Content**:
```python
# Extract from current panel.py:
class MasterFallbackDelegate(QtWidgets.QStyledItemDelegate):  # Lines 609-900
class CenteredCheckboxDelegate(QtWidgets.QStyledItemDelegate): # Lines 902-970

# Simplified dropdown handling:
class DropdownEditorMixin:  # Extract dropdown creation logic
```

### 4. `panel/models.py` (~200 lines)
**Purpose**: Data handling and business logic
**Content**:
```python
class TableDataModel:
    """Handles table data and master row fallback logic"""
    
class GSVHierarchyModel:
    """Manages GSV tree structure and selection state"""
    
class SettingsModel:
    """Handles job and machine settings data"""
```

### 5. `panel/views.py` (~600 lines)
**Purpose**: UI layout and view components
**Content**:
```python
class SettingsView(QtWidgets.QWidget):
    """Job and Machine settings UI (lines 1086-1440)"""
    
class NodeSettingsView(QtWidgets.QWidget):
    """Node settings table interface (lines 1525-1700)"""
    
class GSVView(QtWidgets.QWidget):
    """GSV tree interface (lines 1702-2200)"""
    
class ExtraSettingsView(QtWidgets.QWidget):
    """Extra settings tab"""
    
class ConsoleView(QtWidgets.QWidget):
    """Console output tab"""
```

### 6. `panel/panel.py` (~300 lines)
**Purpose**: Main panel coordination and registration
**Content**:
```python
class Nk2dlPanel(QtWidgets.QWidget):
    """Main panel using composition pattern"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create models
        self.table_model = TableDataModel()
        self.gsv_model = GSVHierarchyModel()
        self.settings_model = SettingsModel()
        
        # Create views
        self.settings_view = SettingsView(self.settings_model)
        self.node_view = NodeSettingsView(self.table_model)
        self.gsv_view = GSVView(self.gsv_model)
        
        # Set up layout and connections
        self._setup_layout()
        self._connect_signals()

def register_panel():
    """Panel registration function"""
```

## Implementation Strategy

### Phase 1: Extract Widgets ⭐ **START HERE**
**Why first**: Widgets are self-contained and lowest risk

1. **Extract `ColoredGroupBox`** → `panel/widgets.py`
   - Lines 546-607 from current panel.py
   - Update imports in panel.py
   - Test widget works independently

2. **Extract `PinnedRowTableWidget`** → `panel/widgets.py`
   - Lines 27-376 from current panel.py
   - Include all table-specific methods
   - Update panel.py to import from panel.widgets

3. **Extract `GroupedHeaderView`** → `panel/widgets.py`
   - Lines 378-544 from current panel.py
   - Keep header grouping logic intact

### Phase 2: Extract Delegates
**Why second**: Delegates depend on widgets but are still isolated

1. **Extract `MasterFallbackDelegate`** → `panel/delegates.py`
   - Lines 609-900 from current panel.py
   - Keep all fallback and dropdown logic

2. **Extract `CenteredCheckboxDelegate`** → `panel/delegates.py`
   - Lines 902-970 from current panel.py
   - Simple checkbox centering logic

### Phase 3: Create Models
**Why third**: Models handle data logic that views will depend on

1. **Create `TableDataModel`**
   - Extract `_get_effective_table_values()` logic
   - Handle master row fallback calculations
   - Emit signals for data changes

2. **Create `GSVHierarchyModel`**
   - Extract GSV tree building logic
   - Handle primary/secondary GSV parsing
   - Manage selection state

3. **Create `SettingsModel`**
   - Extract job/machine settings data
   - Provide validation and defaults

### Phase 4: Create Views
**Why fourth**: Views coordinate widgets, delegates, and models

1. **Extract settings UI** → `SettingsView`
2. **Extract table UI** → `NodeSettingsView`  
3. **Extract GSV UI** → `GSVView`
4. **Extract other tabs** → `ExtraSettingsView`, `ConsoleView`

### Phase 5: Refactor Main Panel
**Why last**: Main panel becomes a simple coordinator

- Transform `Nk2dlPanel` into composition-based coordinator
- Remove all extracted code
- Connect models and views
- Keep panel registration logic

## Benefits of Simplified Approach

### Manageable Complexity
- **6 files** instead of 19 files
- **Logical grouping** - related functionality stays together
- **Easier imports** - fewer import statements needed
- **Simpler testing** - fewer test files to maintain

### Proven Pattern
- **Follows nuke_node_table structure** - proven in production
- **Industry standard** - common in Qt applications
- **Easy to understand** - clear separation without over-engineering

### Practical Implementation
- **Low risk** - extract one component at a time
- **Testable** - each file can be tested independently
- **Maintainable** - easier to find and fix issues
- **Reusable** - widgets can be used in other projects

## Migration Strategy

### Keep It Working
1. **Incremental changes** - extract one component at a time
2. **Test after each step** - ensure nothing breaks
3. **Update imports gradually** - maintain functionality
4. **Preserve existing API** - no breaking changes

### Testing Approach
- **Unit tests** for each extracted component
- **Integration tests** for model/view interactions
- **Visual tests** to ensure UI consistency
- **Mock Nuke environment** for testing without Nuke

### Error Handling
- **Graceful degradation** if components fail to load
- **Better logging** throughout all components
- **User-friendly error messages**
- **Fallback to basic functionality**

## Code Quality Standards

### VFX Reference Platform Compliance
- **Python 3.9+** compatibility
- **PySide2/6** version detection and handling
- **PEP 8** code style
- **Type hints** where appropriate

### Documentation
- **Docstrings** for all public methods
- **Usage examples** for complex components
- **Clear API documentation**
- **Migration notes** for any breaking changes

## Success Criteria

- [ ] All existing functionality preserved
- [ ] Startup time unchanged or improved
- [ ] Memory usage unchanged or reduced
- [ ] Clean separation achieved with 6 focused files
- [ ] Components are reusable and testable
- [ ] No regression in user experience
- [ ] Code is easier to maintain and understand

## Next Steps

1. **Start with Phase 1** - Extract widgets to `panel/widgets.py`
2. **Test each extraction** - Ensure widgets work independently
3. **Update imports** - Use new widget locations in panel.py
4. **Move to Phase 2** - Extract delegates once widgets are stable
5. **Continue incrementally** - One phase at a time

## References

- [Nuke Node Table Project](https://gitlab.com/filmkorn/nuke_node_table/-/tree/master/node_table) - Inspiration for simplified structure
- [Qt Model/View Programming](https://doc.qt.io/qt-6/model-view-programming.html)
- [VFX Reference Platform 2024](https://vfxplatform.com/)
- [Code Refactoring Best Practices](https://www.freecodecamp.org/news/how-to-refactor-complex-codebases/) 