# GSV and Extra Settings Refactor Plan

## Overview
Move GSV Settings and Extra Settings from tab section to main settings area as collapsible ColoredGroupBox sections with green color scheme. This will leave only Node Settings and Console in the tab section.

## Current State Analysis

### Current Tab Structure
- **Node Settings** - Table with node data (stays in tabs)
- **GSVs** - GSV hierarchy tree with primary/secondary GSV inputs (move to main area)
- **Extra Settings** - Job name, comment, department fields (move to main area) 
- **Console** - Logging and output (stays in tabs)

### Current Implementation
- **GSVView**: Complex tree widget with primary/secondary GSV inputs, control buttons
- **ExtraSettingsView**: Simple form with 3 text fields in a group box
- **Version Dependency**: GSV only available in Nuke 15.1+ via `_is_nuke_15_1_or_later()`

## New Color Scheme Design

### Green Color Constants
```python
# Add to nk2dl/gui/panel/constants.py Colors class
GSV_SETTINGS_COLOR = "#27AE60"           # Bright green outline  
GSV_SETTINGS_BACKGROUND = "#1B4D32"      # Dark green background
EXTRA_SETTINGS_COLOR = "#2ECC71"         # Lighter bright green outline
EXTRA_SETTINGS_BACKGROUND = "#1E5A3A"    # Lighter dark green background
```

### Color Harmony Analysis
- **Job Settings**: Blue (#4A90E2) with blue background
- **Machine Settings**: Purple (#8E44AD) with purple background  
- **GSV Settings**: Dark green (#27AE60) - professional, complements blue/purple
- **Extra Settings**: Light green (#2ECC71) - differentiated but harmonious

## Implementation Phases

### Phase 1: Create Green Color Constants

#### 1.1 Add Color Constants
```python
# In nk2dl/gui/panel/constants.py
class Colors:
    # Existing colors...
    GSV_SETTINGS_COLOR = "#27AE60"           # Bright green outline  
    GSV_SETTINGS_BACKGROUND = "#1B4D32"      # Dark green background
    EXTRA_SETTINGS_COLOR = "#2ECC71"         # Lighter bright green outline
    EXTRA_SETTINGS_BACKGROUND = "#1E5A3A"    # Lighter dark green background
```

#### 1.2 Update ColoredGroupBox Color Detection
```python
# In misc_widgets.py ColoredGroupBox.__init__()
elif border_color == Colors.GSV_SETTINGS_COLOR:  # Green border
    self.title_bg_color = QtGui.QColor(Colors.GSV_SETTINGS_BACKGROUND)
elif border_color == Colors.EXTRA_SETTINGS_COLOR:  # Light green border
    self.title_bg_color = QtGui.QColor(Colors.EXTRA_SETTINGS_BACKGROUND)
```

### Phase 2: Create GSV Settings Group in SettingsView

#### 2.1 Add GSV Group Creation Method
```python
# In settings_view.py
def _create_gsv_settings_group(self):
    """Create the GSV Settings group box and controls."""
    self.gsv_settings_group = ColoredGroupBox("GSV Settings", Colors.GSV_SETTINGS_COLOR)
    self.gsv_settings_group.setMinimumWidth(Sizes.GSV_SETTINGS_MIN_WIDTH)  # New constant
    self.gsv_settings_group.set_collapsible(True)
    
    # Move GSV content from GSVView here
    # - Primary/Secondary GSV input fields  
    # - GSV tree widget (simplified version)
    # - Essential control buttons (Refresh, Check/Uncheck All)
```

#### 2.2 Version-Dependent Creation
```python
# In SettingsView._create_ui()
if self._is_gsv_available():
    self._create_gsv_settings_group()
    self.content_layout.addWidget(self.gsv_settings_group, 1)

def _is_gsv_available(self):
    """Check if GSV functionality is available in this Nuke version."""
    if not NUKE_AVAILABLE:
        return False
    try:
        major = nuke.NUKE_VERSION_MAJOR
        minor = nuke.NUKE_VERSION_MINOR
        return (major > 15) or (major == 15 and minor >= 1)
    except:
        return False
```

### Phase 3: Create Extra Settings Group in SettingsView

#### 3.1 Add Extra Settings Group Creation Method  
```python
# In settings_view.py
def _create_extra_settings_group(self):
    """Create the Extra Settings group box and controls."""
    self.extra_settings_group = ColoredGroupBox("Extra Settings", Colors.EXTRA_SETTINGS_COLOR)
    self.extra_settings_group.setMinimumWidth(Sizes.EXTRA_SETTINGS_MIN_WIDTH)  # New constant
    self.extra_settings_group.set_collapsible(True)
    
    # Move extra settings content from ExtraSettingsView here
    # - Job Name field
    # - Comment field
    # - Department field
```

#### 3.2 Always Create Extra Settings
```python
# In SettingsView._create_ui()
self._create_extra_settings_group()
self.content_layout.addWidget(self.extra_settings_group, 1)
```

### Phase 4: Update SettingsView Layout Logic

#### 4.1 Add New Collapse State Tracking
```python
# In SettingsView.__init__()
self._gsv_settings_collapsed = False
self._extra_settings_collapsed = False
```

#### 4.2 Connect New Collapse Signals
```python
# In SettingsView._connect_signals()
if hasattr(self, 'gsv_settings_group'):
    self.gsv_settings_group.collapsed_changed.connect(self._on_gsv_settings_collapsed)
self.extra_settings_group.collapsed_changed.connect(self._on_extra_settings_collapsed)
```

#### 4.3 Update Layout Management
```python
def _update_layout_for_collapse_state(self):
    """Update layout direction based on collapse states."""
    should_force_vertical = (
        self._job_settings_collapsed or 
        self._machine_settings_collapsed or
        self._gsv_settings_collapsed or 
        self._extra_settings_collapsed
    )
    # ... rest of existing logic
```

### Phase 5: Refactor Panel Structure

#### 5.1 Update Panel Creation Order
```python
# In SettingsView._create_ui()
# Order: Job Settings -> Machine Settings -> GSV Settings -> Extra Settings
self._create_job_settings_group()
self._create_machine_settings_group()

if self._is_gsv_available():
    self._create_gsv_settings_group()
    
self._create_extra_settings_group()

# Add to layout in order
self.content_layout.addWidget(self.job_settings_group, 1)
self.content_layout.addWidget(self.machine_settings_group, 1)
if hasattr(self, 'gsv_settings_group'):
    self.content_layout.addWidget(self.gsv_settings_group, 1)
self.content_layout.addWidget(self.extra_settings_group, 1)
```

#### 5.2 Update Panel Tab Creation
```python
# In Nk2dlPanel._create_tabbed_interface()
# Remove GSV and Extra Settings tabs, keep only:
self.tab_widget.addTab(self.node_settings_view, "Node Settings")
self.tab_widget.addTab(self.console_view, "Console")
```

### Phase 6: Content Migration Strategy

#### 6.1 GSV Content Migration
**From GSVView to GSV Settings Group:**
- Primary GSVs input field
- Secondary GSVs input field  
- Refresh Hierarchy button
- Simplified GSV tree widget (compact version)
- Check All / Uncheck All buttons
- Remove: Expand/Collapse All (not needed in compact view)

#### 6.2 Extra Settings Content Migration
**From ExtraSettingsView to Extra Settings Group:**
- Job Name text field
- Comment text field
- Department text field
- Remove: Extra group box wrapper (integrate directly)

### Phase 7: Size and Layout Constants

#### 7.1 Add New Size Constants
```python
# In constants.py Sizes class
GSV_SETTINGS_MIN_WIDTH = 350        # Minimum width for GSV group
EXTRA_SETTINGS_MIN_WIDTH = 300      # Minimum width for Extra group
GSV_TREE_COMPACT_HEIGHT = 200       # Compact height for GSV tree
```

#### 7.2 Update Responsive Breakpoints
```python
# Consider increasing RESPONSIVE_BREAKPOINT to account for 4 groups
RESPONSIVE_BREAKPOINT = 1000  # Increased from 800 for 4 groups
```

### Phase 8: Model Integration

#### 8.1 Update Settings Model
```python
# Ensure SettingsModel handles GSV and Extra settings
# GSV settings stored separately from job/machine settings
# Extra settings already supported via set_extra_setting()
```

#### 8.2 Signal Connections
```python
# Connect new groups to settings model
# GSV changes -> self.gsv_model updates
# Extra changes -> self.settings_model.extraSettingsChanged
```

### Phase 9: Legacy View Cleanup

#### 9.1 Remove Tab References
```python
# In Nk2dlPanel:
# - Remove self.gsv_view creation (unless needed for API compatibility)
# - Remove self.extra_settings_view creation  
# - Keep references if external code depends on them
```

#### 9.2 API Compatibility
```python
# Maintain API compatibility for external access:
def get_selected_gsvs(self):
    """Get selected GSV values."""
    if hasattr(self.settings_view, 'gsv_settings_group'):
        return self.settings_view.get_selected_gsvs()
    return {}
```

### Phase 10: Testing and Validation

#### 10.1 Version Testing
- Test GSV group appears in Nuke 15.1+
- Test GSV group hidden in Nuke 15.0 and earlier
- Test Extra Settings always visible

#### 10.2 Collapsible Testing
- Test all 4 groups collapse/expand independently
- Test forced vertical layout with any group collapsed
- Test responsive behavior when all groups expanded

#### 10.3 Visual Testing
- Test green color scheme matches design
- Test color harmony with existing blue/purple
- Test accessibility and contrast

## Implementation Order

1. **Phase 1**: Add green color constants
2. **Phase 2**: Create GSV settings group structure  
3. **Phase 3**: Create extra settings group structure
4. **Phase 4**: Update layout management for new groups
5. **Phase 5**: Update panel tab structure (remove GSV/Extra tabs)
6. **Phase 6**: Migrate content from views to groups
7. **Phase 7**: Add size constants and responsive updates
8. **Phase 8**: Integrate with models and signals
9. **Phase 9**: Clean up legacy view references
10. **Phase 10**: Test and validate all functionality

## Technical Considerations

### Content Simplification
- **GSV Tree**: Use compact version, remove expand/collapse controls
- **GSV Controls**: Keep essential buttons, remove redundant ones
- **Extra Settings**: Direct integration, remove wrapper group box

### Performance Impact
- **Memory**: Slight increase from 4 groups vs 2 tabs
- **Layout**: More complex responsive calculations
- **Rendering**: Minimal impact from additional ColoredGroupBox widgets

### Version Compatibility
- **GSV Detection**: Reuse existing `_is_nuke_15_1_or_later()` logic
- **Graceful Degradation**: GSV group simply doesn't appear in older versions
- **No Breaking Changes**: Maintain existing API where possible

### User Experience
- **Visual Hierarchy**: Green groups after blue/purple maintains logical flow
- **Collapse Behavior**: Each group can be collapsed independently
- **Responsive Design**: Automatic vertical layout when groups are collapsed
- **Reduced Tabs**: Cleaner tab interface with only Node Settings and Console

## Success Criteria

- ✅ GSV Settings appears as green collapsible group after Machine Settings
- ✅ Extra Settings appears as light green collapsible group after GSV Settings  
- ✅ GSV Settings only visible in Nuke 15.1+
- ✅ Extra Settings always visible
- ✅ Tab section contains only Node Settings and Console
- ✅ All 4 groups support collapsible functionality
- ✅ Collapsed groups force vertical layout
- ✅ Green color scheme harmonizes with blue/purple
- ✅ No regression in existing functionality
- ✅ API compatibility maintained for external access

## Files to Modify

1. **`nk2dl/gui/panel/constants.py`** - Add green color constants and sizes
2. **`nk2dl/gui/panel/widgets/misc_widgets.py`** - Update ColoredGroupBox color detection
3. **`nk2dl/gui/panel/views/settings_view.py`** - Add GSV and Extra settings groups
4. **`nk2dl/gui/panel/__init__.py`** - Update tab creation, remove GSV/Extra tabs
5. **`nk2dl/gui/panel/views/gsv_view.py`** - Extract content for migration (reference)
6. **`nk2dl/gui/panel/views/extra_settings_view.py`** - Extract content for migration (reference)

## Risk Mitigation

1. **Version Dependencies**: Thorough testing across Nuke versions
2. **Content Migration**: Careful preservation of functionality during move
3. **Layout Complexity**: Incremental implementation with testing
4. **API Compatibility**: Maintain existing interfaces where possible
5. **Visual Consistency**: Test color schemes across different themes 