# UI Updates and Functionality Updates TODO - Round 2

## Overview
This document tracks the second round of UI updates and functionality improvements for the nk2dl project.

---

## Status: In Progress 🔄
Ready to add new UI update items as they are described.

---

## Settings Storage Visual Indication System

- [ ] **Persistent UI Settings with Visual Feedback**
  - [ ] **Storage Integration**:
    - [ ] Ensure all UI setting changes are automatically saved to nk2dl storage
    - [ ] Implement storage read/write hooks for UI widgets
    - [ ] Add storage key mapping for each UI setting
  - [ ] **Visual Indication System**:
    - [ ] Implement yellow box/outline rendering for settings loaded from storage
    - [ ] **Widget-specific visual feedback**:
      - [ ] **Checkbox**: Yellow outline around checkbox only (not label)
      - [ ] **Spin widget**: Yellow outline around spin control only (not label)  
      - [ ] **Menu/ComboBox**: Yellow outline around dropdown only (not label)
      - [ ] **Text fields**: Yellow outline around text input only (not label)
    - [ ] **Technical Implementation**:
      - [ ] Research alternatives to stylesheets for widget outlining
      - [ ] Investigate custom painting approaches (paintEvent override)
      - [ ] Consider QFrame/border-based solutions
      - [ ] Test widget-specific decoration methods
      - [ ] Implement visual state tracking (stored vs default values)
  - [ ] **Integration Points**:
    - [ ] Hook into existing storage system to detect "loaded from storage" state
    - [ ] Add visual state management for each widget
    - [ ] Implement visual feedback toggle/refresh mechanism
    - [ ] Test with different widget types across the panel
  - [ ] **Validation & Testing**:
    - [ ] Test visual feedback with various widget types
    - [ ] Verify storage persistence across panel open/close cycles
    - [ ] Test visual indication removal when settings are reset to defaults
    - [ ] Ensure visual feedback doesn't interfere with widget functionality
    - [ ] Test across different UI themes/styles

---

## Implementation Priority
**HIGH PRIORITY**: Complete and verify this enhancement fully before moving to next UI update.

---

## Tab Widget Tooltip Fix

- [ ] **Fix Tab Widget Tooltip Behavior**
  - [ ] **Problem**: Hovering over tab content areas shows the main tab widget's tooltip instead of no tooltip
  - [ ] **Goal**: Tooltips should only show when hovering over individual tabs, with specific tooltip text for each tab
  - [ ] **Technical Implementation**:
    - [ ] **Clear main tab widget tooltip**:
      - [ ] Remove or clear the main QTabWidget's tooltip property
      - [ ] Ensure no fallback tooltip is set on the tab widget itself
    - [ ] **Implement individual tab tooltips**:
      - [ ] Use `setTabToolTip(index, tooltip_text)` for each tab
      - [ ] Create specific tooltip text for each tab based on its purpose
      - [ ] Map tab indices to appropriate tooltip content
    - [ ] **Prevent tooltip bubbling**:
      - [ ] Ensure content areas don't inherit/bubble up to parent tooltips
      - [ ] Test that hovering over tab content shows no tooltip
      - [ ] Verify tooltips only appear when hovering over tab headers
    - [ ] **Optional fine-tuning**:
      - [ ] Override `event()` method if needed for precise tooltip control
      - [ ] Handle `QEvent.ToolTip` events for more granular control
      - [ ] Test tooltip behavior across different tab states (active/inactive)
  - [ ] **Testing**:
    - [ ] Test tooltip behavior on each tab
    - [ ] Verify no tooltips appear over content areas
    - [ ] Test tooltip positioning and timing
    - [ ] Ensure tooltips work correctly when switching between tabs

---

## Items to be added:
- Additional items will be added here as they are described... 