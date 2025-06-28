# NODE SETTINGS BUTTON REDRAW FIX TODO

## 🎯 OBJECTIVE
Fix button redraw issues in the GUI panel, specifically eliminating intermediate redraws and progress bar length changes that create flickering during button operations.

## 🚨 CRITICAL ISSUES IDENTIFIED
- **Clear button**: columns refresh to smaller size, then wider widths (2 redraws → 1 redraw)
- **Update button**: columns refresh 3 times during progress updates (remove intermediate redraws)
- **Progress bar**: **LENGTH changes during text updates** (not just size, but actual bar length) - keep consistent length
- **Threading concerns**: Some operations may happen off the main thread causing redraw issues

## 🧪 TESTING STRATEGY

### Enhanced Baseline Tests  
**File**: `tests/qt/test_button_redraw_comprehensive.py` (to be created)
- [ ] **Use FULL panel with all settings windows, tabs etc** to simulate production exactly
- [ ] **Use sample data in TEST CODE only** - no sample data in production code
- [ ] Capture current refresh patterns with comprehensive VFX production scenarios
- [ ] Track column width changes during clear and update button operations  
- [ ] **Monitor progress bar LENGTH changes** (not just size) during text updates
- [ ] **Investigate threading issues** - track which thread operations occur on
- [ ] Test with realistic data loading scenarios that trigger background threads
- [ ] Use automated button clicking with QtTest for consistent testing

### Sample Data Requirements
- [ ] Keep ALL sample data within test file only (never in production codebase)
- [ ] Use realistic VFX production data (long filenames, complex node names, varied settings)
- [ ] Include stereo, cryptomatte, deep comp, and review scenarios
- [ ] Test both initial population and update scenarios

### Threading Investigation
- [ ] **Identify which operations happen on background threads vs main Qt thread**
- [ ] **Track progress bar updates and determine if they trigger redraws from worker threads**
- [ ] **Investigate if column width calculations happen on background threads**
- [ ] **Map the complete signal/slot chain for update operations across threads**
- [ ] **Test with Qt thread debugging enabled to see cross-thread signal emissions**

## 📋 IMPLEMENTATION PHASES

### PHASE 1: COMPREHENSIVE INVESTIGATION & BASELINE
**Status: NOT STARTED**
- [ ] Create full production-like test environment with complete panel setup
- [ ] Implement comprehensive sample data within test file only
- [ ] **Investigate threading model for update operations**
- [ ] **Track progress bar LENGTH changes during text updates (not just size)**
- [ ] **Map all background thread → main thread signal emissions**
- [ ] Capture accurate baseline with threading information
- [ ] Identify ROOT CAUSE of intermediate redraws including thread interactions

**Key Questions to Answer:**
- Which operations trigger background threads?
- Do progress updates from worker threads cause main thread column recalculations?
- Does the progress bar length change due to cross-thread signal emissions?
- Are column width calculations queued vs immediate?

### PHASE 2: CLEAR BUTTON OPTIMIZATION
**Status: NOT STARTED**  
- [ ] **Analyze clear button with threading context**
- [ ] Implement solution that prevents intermediate redraws
- [ ] Ensure thread-safe operations if background threads involved
- [ ] Test with full panel environment
- [ ] Validate: ≤1 column width change event

### PHASE 3: UPDATE BUTTON OPTIMIZATION
**Status: NOT STARTED**
- [ ] **Analyze update button threading model**
- [ ] **Fix progress bar LENGTH changes during text updates**
- [ ] Implement deferred column width recalculations
- [ ] **Handle cross-thread signal emissions properly**
- [ ] Test with realistic data loading scenarios
- [ ] Validate: 0 column width changes during progress updates
- [ ] Validate: 0 progress bar length changes during text updates

### PHASE 4: PROGRESS BAR STABILIZATION  
**Status: NOT STARTED**
- [ ] **Investigate why progress bar LENGTH changes during text updates**
- [ ] **Fix threading issues that may cause progress bar redraws**
- [ ] Ensure consistent progress bar length regardless of text content
- [ ] Test with various progress text lengths
- [ ] Validate: 0 progress bar length changes during updates

### PHASE 5: THREADING OPTIMIZATION
**Status: NOT STARTED**
- [ ] **Optimize cross-thread signal emissions**
- [ ] **Ensure all UI updates happen on main thread**
- [ ] **Batch background thread notifications to main thread**
- [ ] **Implement proper thread-safe UI update patterns**
- [ ] Final validation with complete production-like scenarios

## 🎯 SUCCESS CRITERIA

### Performance Targets
- Clear button: ≤1 column width change event (eliminate intermediate redraws)
- Update button: 0 column width changes during progress updates
- **Progress bar: 0 length changes during text updates**
- **No cross-thread UI update violations**

### Quality Requirements
- Final column widths: Allow natural resizing to accommodate new content
- **Thread safety: All UI updates occur on main Qt thread**
- Performance: No degradation in overall operation speed
- **Production accuracy: Test with full panel setup exactly like production**

## 🔧 TECHNICAL INVESTIGATION AREAS

### Threading Analysis Required
- [ ] **Map NodeDataProvider background thread operations**
- [ ] **Track ProgressManager signal emissions across threads**
- [ ] **Identify TableDataModel thread safety issues** 
- [ ] **Analyze NodeSettingsView thread interactions**
- [ ] **Check FrozenTableWidget thread safety**

### Progress Bar Investigation  
- [ ] **Why does progress bar length change with different text content?**
- [ ] **Is this due to Qt automatic sizing or explicit width calculations?**
- [ ] **Are progress updates queued properly or causing immediate redraws?**
- [ ] **Does threading affect progress bar update frequency?**

### Cross-Thread Signal Chain Mapping
- [ ] **Background thread: NodeDataProvider → signals**
- [ ] **Main thread: ProgressManager receives and re-emits**
- [ ] **Main thread: NodeSettingsView receives progress updates**
- [ ] **Main thread: Progress bar updates and potential column recalculations**

## 📝 NOTES

### Key Requirements from Investigation
- **MUST test with full panel (all settings windows, tabs, etc) to match production**
- **MUST keep sample data in test code only, never in production code**
- **MUST investigate threading model thoroughly before implementing fixes**
- **MUST fix progress bar length changes, not just column width issues**
- **MUST ensure all UI updates are thread-safe and happen on main thread**

### Expected Challenges
- Threading issues may be complex and require Qt threading expertise
- Progress bar length changes may be due to Qt automatic sizing mechanisms
- Cross-thread signal emissions may require careful synchronization
- Full panel testing may reveal additional redraw issues not seen in isolated tests 