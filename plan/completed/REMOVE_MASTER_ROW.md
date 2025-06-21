# Remove Master Row Implementation Plan

## Overview

This document outlines the plan to remove the master row (pinned row) functionality from the nk2dl panel and replace it with custom header styling. The master row was previously used as a "fallback" system where empty cells would inherit values from the first row. Instead, we will implement a settings-based override system with custom header styling.

## ✅ Phase 1: COMPLETED - Master Row Infrastructure Removed

**Status**: ✅ **COMPLETE** - Tested and working in Nuke

All master row functionality has been successfully removed:
- `PinnedRowTableWidget` → `StandardTableWidget`
- `MasterFallbackDelegate` completely removed
- `TableDataModel` simplified (no master row tracking)
- Sample data updated with explicit values
- All signal connections cleaned up

**Testing Results**: ✅ Panel loads and functions correctly in Nuke

---

## 🔄 Phase 1.5: Settings-Table Relationship Mapping (NEW)

### Overview
Before implementing custom headers, we need to establish the relationship between table column headers and job/machine settings. This will enable a proper override system where table cells inherit from settings unless explicitly overridden.

### 1.5.1 Create Header-Settings Mapping
Create a mapping system that defines relationships between:
- Table column headers → Job/Machine setting fields
- Override behavior (bold text for explicit values)
- Dropdown menu structure with "Use job/machine settings" options

### 1.5.2 Implement Override System
- Empty cells inherit from related job/machine settings
- Explicit cell values override settings (displayed in bold)
- Dropdown menus include setting inheritance options
- Yes/No columns show "Yes", "No", "Use job settings" format
- Other dropdowns show "Options...", "Use job/machine settings" format

### 1.5.3 Update Table Delegates
- Create new delegate for settings-aware editing
- Handle dropdown menus with inheritance options
- Apply bold styling for override values
- Manage inheritance vs explicit value logic

---

## Phase 2: Implement Custom Header Styling

### 2.1 Create Custom Header Delegate
Create a new `CustomHeaderDelegate` class that:
- Inherits from `QHeaderView` or creates a custom header widget
- Implements custom painting for header cells
- Draws colored bottom borders based on column groups
- Optionally changes header cell background colors

### 2.2 Define Header Styling Groups
Update `constants.py` to define header styling groups:
```python
class HeaderStyling:
    """Header styling constants."""
    
    # Column groupings for header styling
    JOB_SETTINGS_COLUMNS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Chunk through Reloadplugin
    MACHINE_SETTINGS_COLUMNS = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]  # Pool through Limits
    
    # Header border colors
    JOB_SETTINGS_HEADER_COLOR = "#4A90E2"      # Blue - matches job settings
    MACHINE_SETTINGS_HEADER_COLOR = "#8E44AD"   # Purple - matches machine settings
    DEFAULT_HEADER_COLOR = "#555555"           # Grey for ungrouped columns
    
    # Header background colors (optional enhancement)
    JOB_SETTINGS_HEADER_BG = "#2A2633"        # Dark blue-grey
    MACHINE_SETTINGS_HEADER_BG = "#332633"    # Dark purple-grey
    DEFAULT_HEADER_BG = "#2B2B2B"             # Default dark grey
```

### 2.3 Implement Custom Header View
Create a custom header view class:
```python
class ColoredHeaderView(QtWidgets.QHeaderView):
    """Custom header view with colored bottom borders for column groups."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
    def paintSection(self, painter, rect, logicalIndex):
        """Paint header section with custom bottom border."""
        # Paint standard header background and text
        super().paintSection(painter, rect, logicalIndex)
        
        # Determine column group and color
        border_color = self._get_column_border_color(logicalIndex)
        bg_color = self._get_column_background_color(logicalIndex)
        
        # Draw custom bottom border
        self._draw_bottom_border(painter, rect, border_color)
        
        # Optionally fill background with group color
        if bg_color:
            self._fill_background(painter, rect, bg_color)
    
    def _get_column_border_color(self, column):
        """Get border color for column based on its group."""
        # Implementation details
        
    def _draw_bottom_border(self, painter, rect, color):
        """Draw colored bottom border on header cell."""
        # Implementation details
```

### 2.4 Integration with Table Widget
- Replace `StandardTableWidget` header with custom `ColoredHeaderView`
- Ensure standard table functionality works correctly
- Apply header styling based on column groupings

---

## Files to Modify

### Phase 1.5 Files
1. **`nk2dl/gui/panel/constants.py`**
   - Add `HeaderSettingsMapping` class
   - Define column-to-setting relationships

2. **`nk2dl/gui/panel/delegates.py`**
   - Create new `SettingsAwareDelegate` class
   - Handle inheritance and override logic

3. **`nk2dl/gui/panel/models.py`**
   - Add methods for settings inheritance
   - Update validation for override system

4. **`nk2dl/gui/panel/views.py`**
   - Update table to use new delegate
   - Connect settings model to table model

### Phase 2 Files
1. **`nk2dl/gui/panel/widgets.py`**
   - Create new `ColoredHeaderView` class
   - Update `StandardTableWidget` to use custom header

2. **`nk2dl/gui/panel/constants.py`**
   - Add new `HeaderStyling` class

---

## Success Criteria

### Phase 1.5 Success Criteria
1. **Settings Relationship**
   - Clear mapping between table columns and settings
   - Inheritance works correctly for empty cells
   - Override values display in bold

2. **Dropdown Functionality**
   - Yes/No columns show proper inheritance options
   - Other dropdowns include "Use job/machine settings"
   - Dropdown behavior matches original master row system

### Phase 2 Success Criteria
1. **Functional Requirements**
   - Table displays and functions normally
   - All dropdown editors work correctly
   - Sorting and selection work on all columns
   - Settings panel integration remains functional

2. **Visual Requirements**
   - Header cells show colored bottom borders matching column groups
   - Colors match existing job settings (blue) and machine settings (purple) theme
   - Headers remain readable and functional
   - Visual styling is consistent across different table states

3. **Code Quality**
   - Clean, maintainable header styling implementation
   - Proper separation of concerns between models, views, and delegates
   - Consistent with VFX Reference Platform requirements

## Timeline Estimate

- **Phase 1**: ✅ **COMPLETE** (4-6 hours)
- **Phase 1.5 (Settings Mapping)**: 6-8 hours
- **Phase 2 (Header Implementation)**: 4-6 hours  
- **Phase 3 (Testing & Polish)**: 2-4 hours
- **Total**: 16-24 hours

## Dependencies

- ✅ Phase 1 testing completed successfully in Nuke
- Phase 1.5 requires understanding of current settings model structure
- Phase 2 requires completion of Phase 1.5 settings relationship
- May need color adjustments based on visual testing
- Coordination with existing UI color scheme 