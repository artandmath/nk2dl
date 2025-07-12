# UI Updates and Functionality Updates TODO

## Job Settings Panel - Frame Handling Enhancement

- [ ] **Frames Field Dynamic Behavior**
  - [ ] Implement dropdown-based frame field behavior
  - [ ] Add dropdown options:
    - [x] "Global" (existing)
    - [x] "Input" (existing) 
    - [ ] "First Middle Last" (new)
    - [ ] "Hero Frames" (new)
    - [x] "Custom" (existing)
  - [ ] Implement text box behavior per dropdown selection:
    - [ ] **"global"**: 
      - Fetch first and last frames from nuke root node
      - Display as "X-Y" format (e.g., "1001-1050")
      - Text box greyed out and not modifiable
    - [ ] **"input"**: 
      - Text box greyed out
      - Contents should display "input"
    - [ ] **"First Middle Last"**: 
      - Text box greyed out
      - Contents should display "f,m,l"
    - [ ] **"Hero Frames"**: 
      - Text box greyed out
      - Contents should display "hero"
    - [ ] **"custom"**: 
      - Text box enabled (not greyed out)
      - User can enter custom values
      - Preserve previous values when switching to custom
      - Future: retrieve stored custom frame_range values
  - [ ] **Technical Implementation**:
    - [ ] Locate current hardcoded "1001-2315" value
    - [ ] Create function to fetch nuke root node frame range
    - [ ] Implement dropdown change handler
    - [ ] Add text box enable/disable logic
    - [ ] Add validation for custom frame range input
    - [ ] Add storage mechanism for custom frame ranges (future enhancement)

---

## Job Settings Panel - Write Node Checkbox Dependencies

- [ ] **Write Node Job Handling Checkbox Logic**
  - [ ] Implement checkbox dependency logic for write node job handling
  - [ ] **When "Write nodes as separate jobs" is ENABLED**:
    - [ ] "Views as separate jobs" - enable clicking
    - [ ] "Render order dependencies" - enable clicking  
    - [ ] "Write nodes as separate tasks for the same job" - disable clicking (greyed out, strikethrough if possible, unchecked)
  - [ ] **When "Write nodes as separate jobs" is NOT ENABLED**:
    - [ ] "Views as separate jobs" - disable clicking (greyed out, strikethrough if possible, unchecked)
    - [ ] "Render order dependencies" - disable clicking (greyed out, strikethrough if possible, unchecked)
    - [ ] "Write nodes as separate tasks for the same job" - enable clicking
  - [ ] **When "Write nodes as separate tasks for the same job" is ENABLED**:
    - [ ] "Write nodes as separate jobs" - disable clicking (greyed out, strikethrough if possible, unchecked)
    - [ ] "Views as separate jobs" - disable clicking (greyed out, strikethrough if possible, unchecked)
    - [ ] "Render order dependencies" - disable clicking (greyed out, strikethrough if possible, unchecked)
  - [ ] **Technical Implementation**:
    - [ ] Locate checkbox UI elements in the codebase
    - [ ] Implement checkbox state change handlers
    - [ ] Add enable/disable logic for dependent checkboxes
    - [ ] Add visual styling for disabled state (greyed out, strikethrough)
    - [ ] Add automatic unchecking of disabled checkboxes
    - [ ] Test mutual exclusivity between "separate jobs" and "separate tasks" options

---

## Job Settings Panel - Layout Alignment

- [ ] **Checkbox Alignment Fix**
  - [ ] Align left side of "Views as separate jobs" to match left side of "Reload plugins between tasks"
  - [ ] **Technical Implementation**:
    - [ ] Locate UI elements for "Views as separate jobs" and "Reload plugins between tasks"
    - [ ] Identify current layout/margin/padding differences
    - [ ] Adjust CSS/styling or layout properties to align left edges
    - [ ] Test alignment across different window sizes/resolutions
    - [ ] Ensure consistent alignment with other checkbox elements

---

## Job Settings Panel - UI Cleanup and Text Improvements

- [ ] **Remove Version Text Display**
  - [ ] Remove "NK2DL Submitter v0.1-alpha" from lower left of display
  - [ ] **Technical Implementation**:
    - [ ] Locate UI element displaying version text in lower left
    - [ ] Remove or hide the version text element
    - [ ] Ensure layout adjusts properly after removal
    - [ ] Test that removal doesn't affect other UI elements

- [ ] **Feedback Text Enhancement**
  - [ ] Make feedback text (currently "Ready") larger
  - [ ] **Technical Implementation**:
    - [ ] Locate feedback text UI element (status text showing "Ready")
    - [ ] Increase font size for better visibility
    - [ ] Test readability at different font sizes
    - [ ] Ensure text still fits within allocated space
    - [ ] Test with different status messages (not just "Ready")

---

## Status: Complete
This TODO list contains all the UI update items to be implemented. Ready for implementation phase. 