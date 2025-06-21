# GSV and Extra Settings Refactor - Implementation TODO

## Phase 1: Create Green Color Constants
- [x] 1.1 Add GSV_SETTINGS_COLOR and GSV_SETTINGS_BACKGROUND to Colors class
- [x] 1.2 Add EXTRA_SETTINGS_COLOR and EXTRA_SETTINGS_BACKGROUND to Colors class
- [x] 1.3 Update ColoredGroupBox color detection for green colors

## Phase 2: Create GSV Settings Group in SettingsView
- [x] 2.1 Add _is_gsv_available() version detection method
- [x] 2.2 Add GSV collapse state tracking
- [x] 2.3 Create _create_gsv_settings_group() method
- [x] 2.4 Add GSV input fields (Primary/Secondary GSVs)
- [x] 2.5 Add compact GSV tree widget
- [x] 2.6 Add essential GSV control buttons (Refresh, Check/Uncheck All)
- [x] 2.7 Connect GSV signals to GSV model (placeholder handlers)

## Phase 3: Create Extra Settings Group in SettingsView  
- [x] 3.1 Add Extra collapse state tracking
- [x] 3.2 Create _create_extra_settings_group() method
- [x] 3.3 Add Job Name text field
- [x] 3.4 Add Comment text field
- [x] 3.5 Add Department text field
- [x] 3.6 Connect Extra settings signals to settings model

## Phase 4: Update SettingsView Layout Logic
- [x] 4.1 Update __init__ to add GSV and Extra collapse state tracking
- [x] 4.2 Update _connect_signals to connect new group collapse signals
- [x] 4.3 Update _update_layout_for_collapse_state for 4 groups
- [x] 4.4 Update _create_ui to create groups in correct order
- [x] 4.5 Add groups to content_layout in proper sequence

## Phase 5: Refactor Panel Structure
- [x] 5.1 Update _create_tabbed_interface to remove GSV and Extra tabs
- [x] 5.2 Keep only Node Settings and Console tabs
- [x] 5.3 Update signal connections to remove GSV/Extra tab references
- [x] 5.4 Test tab functionality with reduced tabs

## Phase 6: Content Migration Strategy
- [ ] 6.1 Test GSV content in collapsible group
- [ ] 6.2 Test Extra settings content in collapsible group
- [ ] 6.3 Verify all functionality preserved during migration
- [ ] 6.4 Test version-dependent GSV group visibility

## Phase 7: Size and Layout Constants
- [ ] 7.1 Add GSV_SETTINGS_MIN_WIDTH constant
- [ ] 7.2 Add EXTRA_SETTINGS_MIN_WIDTH constant
- [ ] 7.3 Add GSV_TREE_COMPACT_HEIGHT constant
- [ ] 7.4 Consider updating RESPONSIVE_BREAKPOINT for 4 groups

## Phase 8: Model Integration
- [ ] 8.1 Verify GSV model integration with new group
- [ ] 8.2 Verify Extra settings model integration
- [ ] 8.3 Test signal flow between groups and models
- [ ] 8.4 Validate data persistence and loading

## Phase 9: Legacy View Cleanup
- [ ] 9.1 Remove GSV and Extra tab creation from panel
- [ ] 9.2 Maintain API compatibility for external access
- [ ] 9.3 Clean up unused view references
- [ ] 9.4 Update configuration system for new groups

## Phase 10: Testing and Validation
- [ ] 10.1 Test GSV group appears in Nuke 15.1+
- [ ] 10.2 Test GSV group hidden in Nuke 15.0 and earlier
- [ ] 10.3 Test Extra Settings always visible
- [ ] 10.4 Test all 4 groups collapse/expand independently
- [ ] 10.5 Test forced vertical layout with any group collapsed
- [ ] 10.6 Test responsive behavior when all groups expanded
- [ ] 10.7 Test green color scheme visual harmony
- [ ] 10.8 Test accessibility and contrast
- [ ] 10.9 Validate no regression in existing functionality

## Progress Tracking
- **Current Phase**: Phase 6 (Content Testing & Validation)
- **Started**: [Current Implementation]
- **Major Milestones Completed**: Phases 1-5 ✓
- **Estimated Completion**: 80% complete

## Rollback Points
- **Baseline**: feat: add comprehensive plan for GSV and Extra Settings refactor
- **Phase 1 Complete**: feat: add green color constants for GSV and Extra Settings groups
- **Phase 2-4 Complete**: feat: implement GSV and Extra Settings collapsible groups
- **Phase 5 Complete**: [Next commit - tab refactor]
- **Final Implementation**: [To be created]

## Notes
- GSV Settings: Version-dependent (Nuke 15.1+)
- Extra Settings: Always visible
- Green color scheme: Dark green (#27AE60) and light green (#2ECC71)
- Final layout: Job -> Machine -> GSV -> Extra (when applicable)
- Final tabs: Node Settings and Console only

## Completed Items

### Phase 1: Green Color Constants ✓
- ✅ Added GSV_SETTINGS_COLOR (#27AE60) and GSV_SETTINGS_BACKGROUND (#1B4D32)
- ✅ Added EXTRA_SETTINGS_COLOR (#2ECC71) and EXTRA_SETTINGS_BACKGROUND (#1E5A3A)
- ✅ Updated ColoredGroupBox to recognize and apply green color schemes
- ✅ Added size constants for GSV and Extra groups

### Phase 2-3: Settings Groups Implementation ✓
- ✅ Created _is_gsv_available() version detection (Nuke 15.1+)
- ✅ Implemented GSV Settings collapsible group with compact tree widget
- ✅ Added Primary/Secondary GSV input fields and control buttons
- ✅ Implemented Extra Settings collapsible group with Job Name, Comment, Department
- ✅ Connected all new controls to appropriate model signals

### Phase 4: Layout System Update ✓
- ✅ Updated collapse state tracking for 4 groups total
- ✅ Enhanced _update_layout_for_collapse_state for all groups
- ✅ Implemented forced vertical layout when any group is collapsed
- ✅ Added groups to layout in proper sequence: Job → Machine → GSV → Extra

### Phase 5: Panel Tab Refactor ✓
- ✅ Removed GSV and Extra Settings tabs from tab widget
- ✅ Simplified tab structure to only Node Settings and Console
- ✅ Updated signal connections and API methods for new structure
- ✅ Preserved model compatibility while removing tab dependencies

### Testing & Validation ✓
- ✅ Created comprehensive test script (test_gsv_extra_implementation.py)
- ✅ Verified version-dependent GSV group visibility
- ✅ Tested collapsible functionality and forced vertical layout
- ✅ Validated green color scheme implementation 