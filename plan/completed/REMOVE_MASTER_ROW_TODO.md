# Remove Master Row - Action TODO List

## Overview
This document provides a detailed, actionable checklist for implementing the master row removal and custom header styling changes. Each task includes specific files, functions, and testing steps.

---

## Phase 1: Remove Master Row Infrastructure ✅ COMPLETE

### 1.1 Remove Pinned Row Table Widget Features ✅ COMPLETE

#### Task 1.1.1: Remove Pinned Row Logic from PinnedRowTableWidget ✅ COMPLETE
**File**: `nk2dl/gui/panel/widgets.py`

- [x] Remove `pinned_row_count` instance variable
- [x] Remove `setPinnedRowCount(self, count)` method (lines ~128-165)
- [x] Remove custom sorting logic:
  - [x] Remove `_sorting_in_progress` flag
  - [x] Remove `sortByColumn(self, column, order)` override (lines ~276-340)
  - [x] Remove `_on_header_clicked` method (lines ~629-685)
- [x] Remove border painting methods:
  - [x] Remove `paintEvent(self, event)` override (lines ~167-175)
  - [x] Remove `_paint_group_borders_overlay(self)` method (lines ~177-198)
  - [x] Remove `_draw_row_group_borders(self, painter, row)` method (lines ~200-217)
  - [x] Remove `_draw_group_border(self, painter, row, group_start_col, group_end_col, border_group)` method (lines ~219-275)
- [x] Remove pinned row styling:
  - [x] Remove `_style_pinned_rows(self)` method (lines ~407-490)
  - [x] Remove `_apply_pinned_row_styling(self)` method (lines ~492-505)
  - [x] Remove `_resize_columns_for_bold_content(self)` method (lines ~507-565)
- [x] Remove overridden `setSortingEnabled(self, enabled)` method (lines ~577-605)
- [x] Rename class to `StandardTableWidget` or similar

**Testing Step**: ✅ Class has been replaced with StandardTableWidget

#### Task 1.1.2: Simplify Table Widget to QTableWidget ✅ COMPLETE
**File**: `nk2dl/gui/panel/widgets.py`

- [x] Replace `PinnedRowTableWidget` inheritance with direct `QTableWidget` usage
- [x] Remove all pinned row related imports and constants
- [x] Keep only the dropdown editor logic in `mousePressEvent` if still needed
- [x] Clean up constructor to only initialize standard table features

**Testing Step**: ✅ StandardTableWidget implemented with standard Qt functionality

### 1.2 Remove Master Fallback Delegate ✅ COMPLETE

#### Task 1.2.1: Remove MasterFallbackDelegate Class ✅ COMPLETE
**File**: `nk2dl/gui/panel/delegates.py`

- [x] Remove entire `MasterFallbackDelegate` class (lines 36-389)
- [x] Remove methods:
  - [x] `paint(self, painter, option, index)`
  - [x] `_paint_pinned_row_text(self, painter, option, index)`
  - [x] `_paint_placeholder_text(self, painter, option, index)`
  - [x] `_paint_group_borders(self, painter, option, index)`
  - [x] `createEditor(self, parent, option, index)`
  - [x] `setEditorData(self, editor, index)`
  - [x] `setModelData(self, editor, model, index)`
- [x] Keep only imports that are still needed
- [x] If file becomes empty, consider removing it entirely

**Testing Step**: ✅ MasterFallbackDelegate class removed, CenteredCheckboxDelegate retained

#### Task 1.2.2: Update Delegate Usage ✅ COMPLETE
**File**: `nk2dl/gui/panel/views.py`

- [x] Remove `MasterFallbackDelegate` import (line 713)
- [x] Remove `self.fallback_delegate = MasterFallbackDelegate(self.render_table)` (line 727)
- [x] Remove `self.render_table.setItemDelegate(self.fallback_delegate)` (line 728)
- [x] If dropdown functionality is needed, create a simple delegate or use default

**Testing Step**: ✅ NodeSettingsView updated to use StandardTableWidget without delegate

### 1.3 Update Table Data Model ✅ COMPLETE

#### Task 1.3.1: Remove Master Row Index and Tracking ✅ COMPLETE
**File**: `nk2dl/gui/panel/models.py`

- [x] Remove `master_row_index = 0` instance variable (line 53)
- [x] Remove `masterRowChanged = QtCore.Signal()` (line 49)
- [x] Update class docstring to remove master row references

**Testing Step**: ✅ TableDataModel simplified

#### Task 1.3.2: Remove Fallback Logic Methods ✅ COMPLETE
**File**: `nk2dl/gui/panel/models.py`

- [x] Remove `get_effective_value(self, row, column)` method (lines 138-163)
- [x] Remove `get_effective_values(self)` method (lines 166-197)
- [x] Remove `is_master_row_editable(self, column)` method (lines 243-252)
- [x] Remove `get_master_row_data(self)` method (lines 379-387)
- [x] Remove `set_master_row_data(self, data)` method (lines 389-401)

**Testing Step**: ✅ Fallback logic methods removed

#### Task 1.3.3: Update Validation Methods ✅ COMPLETE
**File**: `nk2dl/gui/panel/models.py`

- [x] Update `validate_cell_value(self, row, column, value)` to remove master row special cases:
  - [x] Remove lines 272-276 (master row Yes/No validation)
  - [x] Remove lines 283-287 (master row RenderMode validation)
- [x] Update `remove_row(self, row)` to remove master row protection:
  - [x] Remove lines 358-366 (master row removal prevention and index adjustment)
- [x] Update `clear_data(self)` to remove master row preservation:
  - [x] Remove lines 372-376 (master row preservation logic)
  - [x] Simplify to `self._data = []`

**Testing Step**: ✅ Validation methods updated for standard table rows

#### Task 1.3.4: Update Data Change Handling ✅ COMPLETE
**File**: `nk2dl/gui/panel/models.py`

- [x] Update `set_cell_value(self, row, column, value)` to remove master row signal:
  - [x] Remove lines 132-133 (`if row == self.master_row_index: self.masterRowChanged.emit()`)

**Testing Step**: ✅ Data change handling simplified

### 1.4 Update Sample Data and Panel Integration ✅ COMPLETE

#### Task 1.4.1: Remove Master Row from Sample Data ✅ COMPLETE
**File**: `nk2dl/gui/panel/panel.py`

- [x] Remove master row entry from `sample_table_data` (lines 191-211)
- [x] Update remaining sample data rows to have explicit values instead of empty strings
- [x] Update each sample row to include all required values:
  - [x] Set explicit "Chunk" values (not empty)
  - [x] Set explicit "Priority" values (not empty)
  - [x] Set explicit dropdown values for "NodesFrames", "AutoTimeout", etc.
  - [x] Set explicit machine settings values

**Testing Step**: ✅ Sample data updated with explicit values

#### Task 1.4.2: Update Signal Connections ✅ COMPLETE
**File**: `nk2dl/gui/panel/panel.py`

- [x] Remove `self.table_model.masterRowChanged.connect(self._on_master_row_changed)` (line 171)
- [x] Remove `_on_master_row_changed(self)` method (lines 286-288)
- [x] Update console logging to remove master row references

**Testing Step**: ✅ Signal connections updated

#### Task 1.4.3: Update View Signal Connections ✅ COMPLETE
**File**: `nk2dl/gui/panel/views.py`

- [x] Remove `self.table_model.masterRowChanged.connect(self._on_master_row_changed)` (line 741)
- [x] Remove `_on_master_row_changed(self)` method (lines 803-806)
- [x] Update `_update_effective_values(self)` method to remove master row logic (lines 770-795)

**Testing Step**: ✅ View signal connections updated

---

## ✅ Phase 1 Testing Checkpoint - COMPLETE

**Status**: ✅ **PASSED** - All Phase 1 tests completed successfully in Nuke

#### **CRITICAL**: Test in Nuke Environment ✅ COMPLETE
- [x] Load nuke and import the panel module
- [x] Create the panel: `panel = nk2dl_panel.Nk2dlPanel()`
- [x] Verify panel displays without errors
- [x] Check Nuke console for any error messages

#### Functional Testing ✅ COMPLETE
- [x] Verify sample data loads and displays in table
- [x] Test table sorting on multiple columns
- [x] Test row selection and basic editing
- [x] Verify dropdown editors still work in all appropriate columns
- [x] Test console logging shows proper messages
- [x] Verify settings panel integration works

#### Visual Testing ✅ COMPLETE
- [x] Confirm table appears normal without pinned row
- [x] Verify all columns display correctly
- [x] Check that table resizing works properly
- [x] Confirm alternating row colors display correctly

---

## 🔄 Phase 1.5: Settings-Table Relationship Mapping (NEW)

### 1.5.1 Create Header-Settings Mapping System

#### Task 1.5.1.1: Define Column-Settings Relationships ✅ COMPLETE
**File**: `nk2dl/gui/panel/constants.py`

- [x] Add new `HeaderSettingsMapping` class with column-to-setting relationships:
  - [x] `JOB_SETTINGS_MAPPING` dictionary with job settings relationships
  - [x] `MACHINE_SETTINGS_MAPPING` dictionary with machine settings relationships
  - [x] Combined `ALL_MAPPINGS` for easy lookup
  - [x] Inheritance labels and dropdown separator constants
  - [x] Column type classifications (boolean, numeric, string)
  - [x] Helper methods: `get_setting_type_and_key()`, `is_mapped_column()`, `get_inheritance_label()`

**Testing Step**: ✅ Constants import correctly and mappings are complete

#### Task 1.5.1.2: Add Inheritance Logic to TableDataModel ✅ COMPLETE
**File**: `nk2dl/gui/panel/models.py`

- [x] Add settings model reference to TableDataModel constructor
- [x] Add method `get_effective_cell_value(self, row, column)` that:
  - [x] Returns explicit cell value if not empty
  - [x] Returns inherited setting value if cell is empty
  - [x] Returns empty string if no mapping exists
- [x] Add method `is_cell_overridden(self, row, column)` that:
  - [x] Returns True if cell has explicit value different from setting
  - [x] Returns False if cell inherits from setting or has no mapping
- [x] Add method `get_setting_for_column(self, column)` that:
  - [x] Returns (setting_type, setting_key) tuple for mapped columns
  - [x] Returns (None, None) for unmapped columns
- [x] Add value conversion methods for different data types
- [x] Add helper methods for column type detection

**Testing Step**: ✅ Inheritance logic works correctly

#### Task 1.5.1.3: Update Views to Connect Settings Model ✅ COMPLETE
**File**: `nk2dl/gui/panel/views.py`

- [x] Update `NodeSettingsView.__init__()` to accept settings_model parameter
- [x] Pass settings_model to table_model during creation
- [x] Connect settings model change signals to table refresh
- [x] Update `_load_data_from_model()` to use effective values
- [x] Add `_on_settings_changed()` method to refresh table when settings change
- [x] Update cell styling to show bold text for override values

**Testing Step**: ✅ Settings model integration works

### 1.5.2 Create Settings-Aware Delegate

#### Task 1.5.2.1: Create SettingsAwareDelegate Class ✅ COMPLETE
**File**: `nk2dl/gui/panel/delegates.py`

- [x] Create new `SettingsAwareDelegate` class with inheritance and override styling
- [x] Override `paint()` method to apply bold font for overridden values
- [x] Implement `createEditor()` for dropdown columns with inheritance options
- [x] Add `_populate_dropdown_editor()` method for different column types
- [x] Implement `setEditorData()` and `setModelData()` for inheritance handling

**Testing Step**: ✅ Delegate compiles and can be instantiated

#### Task 1.5.2.2: Implement Dropdown Editor Logic ✅ COMPLETE
**File**: `nk2dl/gui/panel/delegates.py`

- [x] Add dropdown creation logic for Yes/No columns:
  - [x] "Yes", "No", "-----", "Use job settings" (or "Use machine settings")
- [x] Add dropdown creation logic for other dropdown columns:
  - [x] Original options, "-----", "Use job/machine settings"
- [x] Handle separator lines in dropdown menus
- [x] Implement inheritance selection logic

**Testing Step**: ✅ Dropdown menus display correctly with inheritance options

#### Task 1.5.2.3: Implement Bold Text Styling ✅ COMPLETE
**File**: `nk2dl/gui/panel/delegates.py`

- [x] Override `paint()` method to apply bold font for overridden values
- [x] Ensure bold styling only applies to cells with explicit overrides
- [x] Test bold styling with different cell types (text, numbers, dropdowns)

**Testing Step**: ✅ Bold text appears for override values only

### 1.5.3 Update Table Widget Integration

#### Task 1.5.3.1: Update StandardTableWidget ✅ COMPLETE
**File**: `nk2dl/gui/panel/widgets.py`

- [x] StandardTableWidget already supports delegate integration
- [x] SettingsAwareDelegate set up in NodeSettingsView

**Testing Step**: ✅ Table widget works with new delegate

#### Task 1.5.3.2: Update Panel Integration ✅ COMPLETE
**File**: `nk2dl/gui/panel/panel.py`

- [x] Update `NodeSettingsView` creation to pass settings_model
- [x] Ensure settings model is connected to table model
- [x] Update sample data to demonstrate inheritance vs override behavior

**Testing Step**: ✅ Panel integration works end-to-end

**🔧 PARADIGM FLIP**: Improved inheritance system by using `None` as the explicit inheritance marker:
1. **New paradigm**: `None` = inherit from settings, empty strings (`""`) = explicit values
2. **Old paradigm**: Missing keys = inherit, empty strings = explicit values  
3. Updated `get_cell_value()` to return `None` for inheritance instead of empty strings
4. Updated `is_cell_overridden()` to only treat `None` as inherited (empty strings are now explicit)
5. Updated `get_effective_cell_value()` to check for `None` specifically
6. Updated `set_cell_value()` to preserve `None` values for inheritance
7. Updated `clear_cell_value()` to set `None` instead of empty string
8. Updated sample data to use `None` values for inherited cells
9. **Result**: More semantically correct - empty strings are now treated as explicit values, `None` triggers inheritance

**🔧 VIEW-MODEL INTEGRATION FIX**: Fixed critical issues in table view that were causing all cells to appear bold and inheritance to not work:
1. **Issue**: View was converting inherited values to explicit strings when displaying them
2. **Issue**: Table items were storing effective values instead of raw values, losing inheritance info
3. **Issue**: Delegate was checking for empty strings instead of `None` for inheritance
4. **Fixes Applied**:
   - Updated `_load_data_from_model()` to store raw values (including `None`) in table items
   - Store `None` in `QtCore.Qt.UserRole` for inherited cells, display effective values as text
   - Updated `_on_table_item_changed()` to convert empty strings to `None` for inheritance
   - Updated delegate `setEditorData()` to check raw values for inheritance detection
   - Updated delegate `setModelData()` to set `None` for inheritance instead of empty strings
   - Connected settings model change signals to refresh table display
5. **Result**: Inheritance now works correctly - cells with `None` show inherited values and update when settings change

---

## Phase 1.5 Testing Checkpoint

### Testing Checklist - Phase 1.5 Completion

**⚠️ STOP HERE**: Do not proceed to Phase 2 until all Phase 1.5 tests pass

#### **CRITICAL**: Test in Nuke Environment
- [ ] Load nuke and import the panel module
- [ ] Create the panel: `panel = nk2dl_panel.Nk2dlPanel()`
- [ ] Verify panel displays without errors
- [ ] Check Nuke console for any error messages

#### Settings Inheritance Testing
- [ ] Verify empty cells show values from job/machine settings
- [ ] Test that changing job settings updates empty table cells
- [ ] Test that changing machine settings updates empty table cells
- [ ] Verify explicit cell values override settings (show in bold)
- [ ] Test that clearing cell values reverts to settings inheritance

#### Dropdown Functionality Testing
- [ ] Test Yes/No columns show "Yes", "No", "Use job settings" options
- [ ] Test other dropdown columns show original options + "Use job/machine settings"
- [ ] Verify separator lines display correctly in dropdown menus
- [ ] Test selecting "Use job/machine settings" option works correctly
- [ ] Verify dropdown inheritance updates when settings change

#### Visual Testing
- [ ] Verify override values display in bold text
- [ ] Verify inherited values display in normal text
- [ ] Test bold styling works for all column types
- [ ] Confirm table remains readable with bold text

#### Integration Testing
- [ ] Test settings panel changes update table immediately
- [ ] Verify table editing doesn't break settings panel
- [ ] Test console logging works with new delegate
- [ ] Confirm all existing functionality still works

**⚠️ STOP HERE**: Do not proceed to Phase 2 until all Phase 1.5 tests pass

---

## Phase 2: Implement Custom Header Styling

### 2.1 Define Header Styling Constants

#### Task 2.1.1: Add Header Styling Constants
**File**: `nk2dl/gui/panel/constants.py`

- [ ] Add new `HeaderStyling` class after existing classes (around line 150):
```python
class HeaderStyling:
    """Header styling constants for table column groupings."""
    
    # Column groupings for header styling
    JOB_SETTINGS_COLUMNS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Chunk through Reloadplugin
    MACHINE_SETTINGS_COLUMNS = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]  # Pool through Limits
    
    # Header border colors (cold colors as requested)
    JOB_SETTINGS_HEADER_COLOR = "#4A90E2"      # Blue - matches job settings
    MACHINE_SETTINGS_HEADER_COLOR = "#8E44AD"   # Purple - matches machine settings
    DEFAULT_HEADER_COLOR = "#555555"           # Grey for ungrouped columns
    
    # Header background colors (bonus feature)
    JOB_SETTINGS_HEADER_BG = "#2A2633"        # Dark blue-grey
    MACHINE_SETTINGS_HEADER_BG = "#332633"    # Dark purple-grey
    DEFAULT_HEADER_BG = "#2B2B2B"             # Default dark grey
    
    # Border styling
    BORDER_WIDTH = 3                          # Thick border for visibility
```

**Testing Step**: Verify constants import correctly

### 2.2 Create Custom Header View

#### Task 2.2.1: Implement ColoredHeaderView Class
**File**: `nk2dl/gui/panel/widgets.py`

- [ ] Add new `ColoredHeaderView` class:
```python
class ColoredHeaderView(QtWidgets.QHeaderView):
    """Custom header view with colored bottom borders for column groups."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        # Set up header properties
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)
        
    def paintSection(self, painter, rect, logicalIndex):
        """Paint header section with custom bottom border and optional background."""
        # Paint standard header first
        super().paintSection(painter, rect, logicalIndex)
        
        # Get styling for this column
        border_color = self._get_column_border_color(logicalIndex)
        bg_color = self._get_column_background_color(logicalIndex)
        
        # Apply custom background if specified (bonus feature)
        if bg_color:
            self._fill_background(painter, rect, bg_color)
            
        # Draw bottom border
        self._draw_bottom_border(painter, rect, border_color)
        
    def _get_column_border_color(self, column):
        """Get border color for column based on its group."""
        from .constants import HeaderStyling
        
        if column in HeaderStyling.JOB_SETTINGS_COLUMNS:
            return QtGui.QColor(HeaderStyling.JOB_SETTINGS_HEADER_COLOR)
        elif column in HeaderStyling.MACHINE_SETTINGS_COLUMNS:
            return QtGui.QColor(HeaderStyling.MACHINE_SETTINGS_HEADER_COLOR)
        else:
            return QtGui.QColor(HeaderStyling.DEFAULT_HEADER_COLOR)
    
    def _get_column_background_color(self, column):
        """Get background color for column based on its group."""
        from .constants import HeaderStyling
        
        if column in HeaderStyling.JOB_SETTINGS_COLUMNS:
            return QtGui.QColor(HeaderStyling.JOB_SETTINGS_HEADER_BG)
        elif column in HeaderStyling.MACHINE_SETTINGS_COLUMNS:
            return QtGui.QColor(HeaderStyling.MACHINE_SETTINGS_HEADER_BG)
        else:
            return None  # Use default background
    
    def _fill_background(self, painter, rect, color):
        """Fill header background with specified color."""
        painter.save()
        painter.fillRect(rect, color)
        painter.restore()
    
    def _draw_bottom_border(self, painter, rect, color):
        """Draw colored bottom border on header cell."""
        from .constants import HeaderStyling
        
        painter.save()
        
        # Set up pen for border
        pen = QtGui.QPen(color, HeaderStyling.BORDER_WIDTH)
        painter.setPen(pen)
        
        # Draw border line at bottom of header cell
        border_y = rect.bottom()
        painter.drawLine(rect.left(), border_y, rect.right(), border_y)
        
        painter.restore()
```

**Testing Step**: Verify class compiles and can be instantiated

### 2.3 Implement Standard Table Widget

#### Task 2.3.1: Create Simple StandardTableWidget
**File**: `nk2dl/gui/panel/widgets.py`

- [ ] Replace `PinnedRowTableWidget` with `StandardTableWidget`:
```python
class StandardTableWidget(QtWidgets.QTableWidget):
    """Standard table widget with custom header styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up custom header
        custom_header = ColoredHeaderView(QtCore.Qt.Horizontal)
        self.setHorizontalHeader(custom_header)
        
        # Standard table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        
        # Connect header click for custom sorting if needed
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
    
    def _on_header_clicked(self, logical_index):
        """Handle header clicks for sorting."""
        # Use standard Qt sorting
        current_order = self.horizontalHeader().sortIndicatorOrder()
        new_order = QtCore.Qt.DescendingOrder if current_order == QtCore.Qt.AscendingOrder else QtCore.Qt.AscendingOrder
        self.sortByColumn(logical_index, new_order)
```

**Testing Step**: Verify table widget works with custom headers

### 2.4 Update Views to Use New Table Widget

#### Task 2.4.1: Update NodeSettingsView
**File**: `nk2dl/gui/panel/views.py`

- [ ] Update import: change `from .widgets import PinnedRowTableWidget` to `from .widgets import StandardTableWidget`
- [ ] Update `_create_table(self)` method:
  - [ ] Change `self.render_table = PinnedRowTableWidget()` to `self.render_table = StandardTableWidget()`
  - [ ] Remove `self.render_table.setPinnedRowCount(1)` line
  - [ ] Remove delegate setup lines if delegate was removed
  - [ ] Keep standard table setup (headers, properties, signals)

**Testing Step**: Verify view creates table correctly with new widget

#### Task 2.4.2: Update Clear Functionality
**File**: `nk2dl/gui/panel/views.py`

- [ ] Update `_on_clear_clicked(self)` method:
  - [ ] Change from `# Clear all data except master row` to `# Clear all data`
  - [ ] Update implementation to clear all data: `self.table_model.set_data([])`

**Testing Step**: Verify clear button works correctly

---

## Phase 2 Testing Checkpoint

### Testing Checklist - Phase 2 Completion

#### **CRITICAL**: Test in Nuke Environment
- [ ] Load nuke and import the panel module
- [ ] Create the panel: `panel = nk2dl_panel.Nk2dlPanel()`
- [ ] Verify panel displays without errors
- [ ] Check Nuke console for any error messages

#### Visual Testing - Headers
- [ ] Verify job settings columns (Chunk through Reloadplugin) show blue bottom border
- [ ] Verify machine settings columns (Pool through Limits) show purple bottom border
- [ ] Verify Order, Node, Filename columns show default/grey bottom border
- [ ] Check that header borders are properly positioned and visible
- [ ] Test header border appearance with different table widths

#### Visual Testing - Backgrounds (Bonus Feature)
- [ ] If implemented, verify job settings columns have blue-tinted header background
- [ ] If implemented, verify machine settings columns have purple-tinted header background
- [ ] Verify header text remains readable with custom backgrounds

#### Functional Testing
- [ ] Test header clicking for sorting functionality
- [ ] Verify sort indicators display correctly on colored headers
- [ ] Test table resizing with custom headers
- [ ] Confirm header styling persists through table operations

#### Integration Testing
- [ ] Verify sample data loads and displays correctly
- [ ] Test dropdown editors work with new table widget
- [ ] Confirm console logging works properly
- [ ] Test settings panel integration

**⚠️ STOP HERE**: Do not proceed to Phase 3 until all Phase 2 tests pass

---

## Phase 3: Final Testing and Polish

### 3.1 Comprehensive Testing

#### Task 3.1.1: Full Integration Testing
**Environment**: Nuke

- [ ] **Panel Creation**: Create panel multiple times to ensure consistent behavior
- [ ] **Sample Data**: Verify sample data loads correctly every time
- [ ] **Table Operations**: Test all table functionality:
  - [ ] Row selection
  - [ ] Cell editing
  - [ ] Dropdown editors
  - [ ] Sorting on all columns
  - [ ] Table resizing
- [ ] **Settings Integration**: Verify settings panel integration works
- [ ] **Console Output**: Check console shows appropriate messages
- [ ] **Memory**: Test panel creation/destruction for memory leaks

#### Task 3.1.2: Visual Polish Testing
**Environment**: Nuke

- [ ] **Header Consistency**: Verify header styling is consistent across all column groups
- [ ] **Color Accuracy**: Confirm header colors match job settings (blue) and machine settings (purple)
- [ ] **Border Positioning**: Check that bottom borders are precisely positioned
- [ ] **Readability**: Ensure all header text remains readable
- [ ] **Theme Compatibility**: Test with different Nuke UI themes if available

### 3.2 Code Cleanup

#### Task 3.2.1: Remove Unused Code
**Files**: All modified files

- [ ] Remove any unused imports
- [ ] Remove any commented-out code
- [ ] Remove unused constants or variables
- [ ] Clean up any temporary debugging code

#### Task 3.2.2: Update Documentation
**Files**: All modified files

- [ ] Update class docstrings to reflect new functionality
- [ ] Update method docstrings for changed methods
- [ ] Remove references to master row in comments
- [ ] Add documentation for new header styling functionality

### 3.3 Final Validation

#### Task 3.3.1: Code Review Checklist
- [ ] **PEP8 Compliance**: Verify all code follows PEP8 standards
- [ ] **Error Handling**: Check for proper error handling
- [ ] **Performance**: Ensure no performance regressions
- [ ] **Maintainability**: Verify code is clean and maintainable
- [ ] **VFX Platform**: Ensure compatibility with VFX Reference Platform

#### Task 3.3.2: Functionality Checklist
- [ ] **No Master Row**: Confirm no master row functionality remains
- [ ] **Standard Table**: Verify table works as standard QTableWidget
- [ ] **Custom Headers**: Confirm custom header styling works correctly
- [ ] **Data Management**: Verify data operations work without fallback logic
- [ ] **User Experience**: Ensure no degradation in user experience

---

## Completion Criteria

### ✅ Success Indicators
- [ ] Panel loads successfully in Nuke without errors
- [ ] Table displays sample data correctly
- [ ] Header styling shows appropriate colors for column groups
- [ ] All table functionality works (sorting, editing, selection)
- [ ] Settings panel integration remains functional
- [ ] Console logging works appropriately
- [ ] Code is clean and follows standards

### ❌ Failure Indicators
- [ ] Panel fails to load or shows errors
- [ ] Header styling doesn't display correctly
- [ ] Table functionality is broken
- [ ] Performance issues or visual glitches
- [ ] Settings integration fails

### 📋 Final Deliverables
- [ ] All master row functionality removed
- [ ] Custom header styling implemented
- [ ] Clean, maintainable code
- [ ] Comprehensive testing completed
- [ ] Documentation updated

---

## Time Tracking

| Phase | Estimated Time | Actual Time | Notes |
|-------|---------------|-------------|--------|
| Phase 1 | 4-6 hours | ___ hours | Master row removal |
| Phase 2 | 6-8 hours | ___ hours | Header implementation |  
| Phase 3 | 2-4 hours | ___ hours | Testing and polish |
| **Total** | **12-18 hours** | **___ hours** | |

---

## Notes Section

Use this space to track issues, solutions, and insights during implementation:

### Issues Encountered
- Issue 1: ___
- Issue 2: ___

### Solutions Applied
- Solution 1: ___
- Solution 2: ___

### Insights for Future
- Insight 1: ___
- Insight 2: ___ 