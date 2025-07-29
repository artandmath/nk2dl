# Deadline Pools and Groups Dynamic Population - Implementation TODO

## Overview
Implement dynamic population of pool and group dropdown options by querying Deadline when the GUI panel launches, replacing the current hard-coded placeholder values.

## Current State Analysis

### Hard-coded Values (To Be Replaced)
- **File**: `nk2dl/gui/panel/constants.py`
- **Current pools**: `["comp", "lighting", "fx", "render", "general"]`
- **Current groups**: `["none", "high_priority", "overnight", "weekend"]`

### Usage Locations
- **Settings Panel**: `nk2dl/gui/panel/views/settings_view.py` (lines 301, 311, 321)
- **Table Dropdowns**: `nk2dl/gui/panel/constants.py` (lines 200-202)

### Default Values Sources (Priority Order)
1. **Nk2dl Storage**: Values saved in root node's custom knobs
2. **Config System**: `config.yaml` defaults (pool: "nuke", group: "none")
3. **Fallback**: "none" for both

## Implementation Tasks

### Phase 1: Create Background Worker Infrastructure

#### 1.1 Create DeadlineResourceWorker Class
- **File**: `nk2dl/gui/panel/controllers/deadline_resources.py` (new file)
- **Purpose**: Background worker to fetch pools and groups from Deadline
- **Features**:
  - Inherit from `QtCore.QRunnable` (matches existing pattern)
  - Use `SubmissionWorkerSignals` pattern for communication
  - Handle connection errors gracefully
  - Support cancellation

```python
class DeadlineResourceWorkerSignals(QtCore.QObject):
    """Signals for deadline resource worker communication."""
    pools_loaded = QtCore.Signal(list)      # pools list
    groups_loaded = QtCore.Signal(list)     # groups list
    error_occurred = QtCore.Signal(str)     # error message
    finished = QtCore.Signal()              # completion signal

class DeadlineResourceWorker(QtCore.QRunnable):
    """Background worker for fetching pools and groups from Deadline."""
```

#### 1.2 Integrate with Existing Progress System
- **File**: `nk2dl/gui/panel/__init__.py`
- **Integration Points**:
  - Add to `_load_initial_data()` method
  - Use existing `PanelProgressManager`
  - Queue alongside node data loading
  - Handle concurrent operations safely

### Phase 2: Update Constants and Data Storage

#### 2.1 Modify Constants Structure
- **File**: `nk2dl/gui/panel/constants.py`
- **Changes**:
  - Replace static lists with dynamic containers
  - Add state management for loading status
  - Provide fallback values during loading

```python
class Settings:
    """Settings-related constants."""
    
    # Dynamic pool/group options (populated from Deadline)
    _pools_loaded = False
    _groups_loaded = False
    _pool_options = ["none"]  # Fallback during loading
    _group_options = ["none"]  # Fallback during loading
    
    @classmethod
    def get_pool_options(cls):
        """Get current pool options."""
        return cls._pool_options
    
    @classmethod
    def set_pool_options(cls, pools):
        """Set pool options from Deadline."""
        cls._pool_options = ["none"] + pools if pools else ["none"]
        cls._pools_loaded = True
    
    # Similar for groups...
```

#### 2.2 Update Storage System
- **File**: `nk2dl/gui/panel/repositories/storage.py`
- **New Methods**:
  - `get_stored_pool_default()` - get saved pool preference
  - `get_stored_group_default()` - get saved group preference
  - `save_resource_preferences()` - save user's preferred defaults

### Phase 3: Update UI Components

#### 3.1 Make Settings View Dynamic
- **File**: `nk2dl/gui/panel/views/settings_view.py`
- **Changes**:
  - Add methods to refresh dropdown contents
  - Handle initial population with fallback values
  - Connect to resource loading signals

```python
def _refresh_pool_dropdowns(self, pools):
    """Refresh pool dropdown contents with new data."""
    current_pool = self.pool_combo.currentText()
    current_secondary = self.secondary_pool_combo.currentText()
    
    # Update dropdowns while preserving selections
    self.pool_combo.clear()
    self.pool_combo.addItems(pools)
    # Restore selection or set to default...

def _refresh_group_dropdown(self, groups):
    """Refresh group dropdown contents with new data."""
    # Similar implementation...
```

#### 3.2 Update Table Dropdown Columns
- **File**: `nk2dl/gui/panel/constants.py`
- **Changes**:
  - Update `DROPDOWN_COLUMNS` dict to use dynamic options
  - Ensure table delegates get updated options

### Phase 4: Implement Loading Logic

#### 4.1 Initial Value Population Strategy
- **Location**: `nk2dl/gui/panel/__init__.py` - `_load_initial_data()`
- **Logic Flow**:

```python
def _populate_initial_pool_group_values(self):
    """Populate initial pool/group values before Deadline fetch."""
    
    # 1. Try storage first
    stored_pool = self.settings_storage.get_stored_pool_default()
    stored_group = self.settings_storage.get_stored_group_default()
    
    if stored_pool or stored_group:
        # Use stored values
        self._set_initial_selections(stored_pool, stored_group)
        return
    
    # 2. Try config defaults
    config_pool = config.get('submission.pool', 'none')
    config_group = config.get('submission.group', 'none')
    
    self._set_initial_selections(config_pool, config_group)

def _set_initial_selections(self, pool, group):
    """Set initial dropdown selections."""
    # Update settings model and UI...
```

#### 4.2 Background Resource Loading
- **Location**: `nk2dl/gui/panel/__init__.py`
- **Integration**:

```python
def _start_deadline_resource_loading(self):
    """Start background loading of Deadline resources."""
    if hasattr(self, '_deadline_resource_worker'):
        return  # Already loading
    
    # Create and configure worker
    self._deadline_resource_worker = DeadlineResourceWorker()
    
    # Connect signals
    self._deadline_resource_worker.signals.pools_loaded.connect(
        self._on_pools_loaded, QtCore.Qt.QueuedConnection)
    self._deadline_resource_worker.signals.groups_loaded.connect(
        self._on_groups_loaded, QtCore.Qt.QueuedConnection)
    self._deadline_resource_worker.signals.error_occurred.connect(
        self._on_deadline_resource_error, QtCore.Qt.QueuedConnection)
    
    # Start worker in thread pool
    QtCore.QThreadPool.globalInstance().start(self._deadline_resource_worker)
```

### Phase 5: Handle Concurrency and Thread Safety

#### 5.1 Thread-Safe UI Updates
- **Challenge**: Resource loading may complete while node data is loading
- **Solution**: Queue UI updates and apply when safe

```python
def _on_pools_loaded(self, pools):
    """Handle pools loaded from Deadline."""
    # Update constants
    Settings.set_pool_options(pools)
    
    # Update UI if ready
    if self._is_ui_ready_for_updates():
        self._refresh_all_pool_dropdowns()
    else:
        self._queue_ui_update('pools', pools)

def _is_ui_ready_for_updates(self):
    """Check if UI is ready for updates."""
    return (not self._node_loading_in_progress and 
            hasattr(self, 'settings_view') and 
            self.settings_view is not None)
```

#### 5.2 Error Handling and Fallbacks
- **Timeout Handling**: If Deadline query takes too long
- **Connection Failures**: Graceful degradation to hard-coded values
- **Partial Success**: Handle case where pools load but groups fail

### Phase 6: User Experience Enhancements

#### 6.1 Loading Indicators
- **Visual Feedback**: Show "(Loading...)" in dropdowns during fetch
- **Progress Integration**: Use existing progress manager
- **Status Messages**: Inform user about resource loading status

#### 6.2 Caching and Performance
- **Cache Strategy**: Cache results for session duration
- **Refresh Capability**: Allow manual refresh of resources
- **Background Refresh**: Periodically update in background

### Phase 7: Testing and Integration

#### 7.1 Testing Scenarios
- **Cold Start**: Panel launch with no stored values
- **Stored Values**: Panel launch with previous selections
- **Connection Failure**: Deadline unavailable scenarios
- **Partial Data**: Some resources available, others failed
- **Concurrent Loading**: Resource and node loading simultaneously

#### 7.2 Backwards Compatibility
- **Graceful Degradation**: Ensure panel works without Deadline connection
- **Config Compatibility**: Maintain existing config.yaml structure
- **Storage Migration**: Handle existing stored settings gracefully

## Implementation Priority

### High Priority (Must Have)
1. Background worker infrastructure
2. Basic dynamic loading replacement
3. Error handling and fallbacks
4. Thread safety for UI updates

### Medium Priority (Should Have)
1. Storage integration for user preferences
2. Loading indicators and user feedback
3. Caching for performance

### Low Priority (Nice to Have)
1. Automatic refresh capabilities
2. Advanced error recovery
3. Performance optimizations

## Files to Modify

### New Files
- `nk2dl/gui/panel/controllers/deadline_resources.py`

### Modified Files
- `nk2dl/gui/panel/constants.py` - Dynamic options
- `nk2dl/gui/panel/views/settings_view.py` - UI refresh methods
- `nk2dl/gui/panel/__init__.py` - Integration and loading logic
- `nk2dl/gui/panel/repositories/storage.py` - Resource preferences storage

## Notes

### Existing Infrastructure to Leverage
- `QtCore.QThreadPool.globalInstance()` - Thread management
- `PanelProgressManager` - Progress indication
- `SubmissionWorkerSignals` pattern - Worker communication
- `QtCore.QTimer.singleShot()` - Delayed operations
- Storage system - Persistence layer

### Integration Points
- Integrate with `_load_initial_data()` flow
- Use existing progress bar and info label
- Leverage current storage and config systems
- Follow established patterns for thread safety

This implementation will provide a seamless experience where the GUI panel dynamically populates with actual Deadline pools and groups while maintaining backwards compatibility and proper error handling. 