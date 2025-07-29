# Collapsible Settings Groups Implementation Plan

## Overview
Add collapsible functionality to Job Settings and Machine Settings groups with arrow indicators. This prepares for adding two more colored settings sections above the node settings.

## Requirements Analysis
1. **Arrow Widget**: Clickable triangle in title area of each ColoredGroupBox
2. **Collapse State**: Right arrow (►) = collapsed, Down arrow (▼) = expanded  
3. **Layout Behavior**: Collapsed groups force full-width, vertical layout
4. **Visual Design**: Collapsed view shows only title bar with background color and border
5. **Future Extensibility**: Support for additional settings sections

## Implementation Steps

### Phase 1: Enhance ColoredGroupBox Widget

#### 1.1 Add Collapsible State Management
```python
class ColoredGroupBox(QtWidgets.QGroupBox):
    # Add new signals
    collapsed_changed = QtCore.Signal(bool)  # emitted when collapse state changes
    
    def __init__(self, title, border_color, parent=None):
        # Add new attributes
        self._is_collapsed = False
        self._content_widget = None
        self._original_height = None
```

#### 1.2 Add Arrow Widget in Title Area
- Create clickable triangle icon in top-right of title bar
- Use Unicode arrows: ► (right) and ▼ (down)
- Position arrow with proper margins from right edge
- Make arrow respond to mouse hover/click

#### 1.3 Implement Collapse/Expand Logic
```python
def set_collapsed(self, collapsed):
    """Set the collapsed state of the group box."""
    if self._is_collapsed == collapsed:
        return
        
    self._is_collapsed = collapsed
    
    if collapsed:
        # Store original height and hide content
        self._original_height = self.height()
        if self.layout():
            self._hide_content()
        self.setFixedHeight(self._get_title_height())
    else:
        # Restore content and height
        if self.layout():
            self._show_content()
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        
    self.collapsed_changed.emit(collapsed)
    self.update()  # Trigger repaint
```

#### 1.4 Modify Paint Event
- Draw arrow in title area
- Handle collapsed vs expanded visual states
- Ensure proper title bar height calculation

### Phase 2: Update SettingsView Layout Logic

#### 2.1 Add Collapse State Tracking
```python
class SettingsView(QtWidgets.QWidget):
    def __init__(self, settings_model, parent=None):
        # Add tracking for group collapse states
        self._job_settings_collapsed = False
        self._machine_settings_collapsed = False
        self._force_vertical_layout = False
```

#### 2.2 Connect Collapse Signals
```python
def _connect_signals(self):
    # ... existing signals ...
    
    # Connect collapse signals
    self.job_settings_group.collapsed_changed.connect(self._on_job_settings_collapsed)
    self.machine_settings_group.collapsed_changed.connect(self._on_machine_settings_collapsed)
```

#### 2.3 Update Layout Management
```python
def _on_job_settings_collapsed(self, collapsed):
    """Handle job settings group collapse state change."""
    self._job_settings_collapsed = collapsed
    self._update_layout_for_collapse_state()

def _on_machine_settings_collapsed(self, collapsed):
    """Handle machine settings group collapse state change."""
    self._machine_settings_collapsed = collapsed
    self._update_layout_for_collapse_state()

def _update_layout_for_collapse_state(self):
    """Update layout direction based on collapse states."""
    # Force vertical layout if any group is collapsed
    should_force_vertical = self._job_settings_collapsed or self._machine_settings_collapsed
    
    if should_force_vertical != self._force_vertical_layout:
        self._force_vertical_layout = should_force_vertical
        
        if should_force_vertical:
            # Force vertical layout
            self.content_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            self.content_layout.setSpacing(10)  # Compact spacing for collapsed mode
        else:
            # Restore responsive behavior
            self._handle_responsive_resize(QtGui.QResizeEvent(self.size(), self.size()))
```

#### 2.4 Override Responsive Behavior
```python
def _handle_responsive_resize(self, event):
    """Handle resize to make settings responsive."""
    # Skip responsive behavior if any group is collapsed
    if self._force_vertical_layout:
        return
        
    # ... existing responsive logic ...
```

### Phase 3: Visual Design Implementation

#### 3.1 Arrow Positioning and Styling
- Position arrow 10px from right edge of title bar
- Use 12px font size for arrow characters
- Add hover effect (lighter color on hover)
- Ensure arrow is vertically centered in title area

#### 3.2 Collapsed State Visuals
- Show only title bar with full background color
- Maintain border styling when collapsed
- Set collapsed height to match title bar height (≈30px)
- Smooth transition animation (optional enhancement)

#### 3.3 Layout Adjustments
- Collapsed groups take full width
- Expanded groups maintain current responsive behavior
- Proper spacing between collapsed and expanded groups

### Phase 4: Integration and Testing

#### 4.1 Integration Points
```python
# In SettingsView._create_job_settings_group():
self.job_settings_group = ColoredGroupBox("Job Settings", "#4A90E2")
self.job_settings_group.setCollapsible(True)  # Enable collapsible functionality

# In SettingsView._create_machine_settings_group():
self.machine_settings_group = ColoredGroupBox("Machine Settings", "#8E44AD") 
self.machine_settings_group.setCollapsible(True)  # Enable collapsible functionality
```

#### 4.2 State Persistence (Future Enhancement)
- Save collapse states to user preferences
- Restore states on panel initialization
- Per-user/per-project state management

### Phase 5: Future Extensibility

#### 5.1 Additional Settings Sections
- Node Settings group (existing functionality)
- Render Settings group (future)
- Advanced Settings group (future)
- Export Settings group (future)

#### 5.2 Group Management
```python
class SettingsView(QtWidgets.QWidget):
    def add_settings_group(self, group_widget, position=None):
        """Add a new settings group at specified position."""
        # Generic method for adding new collapsible groups
        
    def remove_settings_group(self, group_widget):
        """Remove a settings group."""
        # Generic method for removing groups
```

## Implementation Order

1. **First**: Modify ColoredGroupBox to add arrow and collapse functionality
2. **Second**: Update SettingsView to handle collapse state changes
3. **Third**: Implement layout management for collapsed groups
4. **Fourth**: Polish visual design and interaction feedback
5. **Fifth**: Test integration and edge cases

## Technical Considerations

### Mouse Event Handling
- Detect clicks in arrow area vs title area vs content area
- Prevent accidental collapses when interacting with content
- Add visual feedback for clickable arrow area

### Layout Constraints
- Handle minimum width constraints for collapsed groups
- Ensure proper resizing behavior during collapse/expand
- Maintain responsive breakpoints when appropriate

### Performance
- Avoid layout thrashing during rapid collapse/expand
- Cache original dimensions for smooth restoration
- Minimize repaints during state transitions

### Accessibility
- Add keyboard shortcuts for collapse/expand (Space, Enter on focused group)
- Provide screen reader announcements for state changes
- Maintain tab order through collapsed groups

## Files to Modify

1. **`nk2dl/gui/panel/widgets/misc_widgets.py`**
   - Enhance ColoredGroupBox class
   - Add collapsible functionality and arrow widget

2. **`nk2dl/gui/panel/views/settings_view.py`**
   - Update layout management logic
   - Add collapse state handling
   - Modify responsive behavior

3. **`nk2dl/gui/panel/constants.py`** (if needed)
   - Add any new size constants for collapsed heights
   - Add arrow-related styling constants

## Success Criteria

- ✅ Arrow widgets appear in both Job Settings and Machine Settings
- ✅ Clicking arrow toggles between collapsed/expanded states
- ✅ Arrow direction changes: ► (collapsed) ↔ ▼ (expanded)
- ✅ Collapsed groups force vertical layout regardless of window width
- ✅ Expanded groups maintain current responsive behavior
- ✅ Visual design matches requirements (title bar only when collapsed)
- ✅ No regression in existing functionality
- ✅ Ready for future additional settings sections

## Risk Mitigation

1. **Layout Complexity**: Implement incremental changes with thorough testing
2. **Performance Impact**: Profile paint events and layout calculations
3. **Interaction Conflicts**: Clear click area definitions and event handling
4. **Visual Inconsistency**: Use existing color constants and styling patterns
5. **Future Scaling**: Design generic interfaces for additional groups 