# Real Data Integration Plan

## Overview

This plan outlines how to replace the current sample data in the nk2dl panel with real data retrieved from Nuke nodes in the current script. The integration involves four main components:
1. **Node Discovery**: Automatically finding Write, DeepWrite, and custom write nodes
2. **Data Population**: Populating the first 3 columns with real node data  
3. **Settings Persistence**: Storing user modifications in the root node as YAML
4. **Threading & Progress**: Background data loading with progress indicators

## Current State Analysis

### **Panel Launch Integration**
From `nk2dl/gui/menus.py`, the panel is launched via:
```python
nukescripts.panels.restorePanel("com.danielharkness.nk2dl.panel")
```

### **Sample Data Structure**
The current `SAMPLE_TABLE_DATA` in `nk2dl/gui/panel/sample_data.py` contains:
- **Fixed rows**: 6 hardcoded entries with mixed inheritance patterns
- **Static columns**: All headers populated with sample values
- **Inheritance simulation**: Uses `None` values to simulate settings inheritance

### **Table Model Integration**
The `TableDataModel` in `nk2dl/gui/panel/models/table_model.py`:
- Manages table data as list of dictionaries
- Handles inheritance logic (None values inherit from settings)
- Supports row/column operations
- Connected to settings model for default values

### **Write Node Discovery**
From `nk2dl/nuke/submission.py`, the existing `_all_write_nodes()` method:
- Supports `Write`, `DeepWrite`, and custom write classes from config
- Uses `nuke.allNodes(node_type)` for discovery
- Filters by `custom_write_classes` from configuration

## 🎯 **Implementation Plan**

### **Phase 1: Node Data Extraction with Threading (3-4 hours)**

#### **1.1 Create Threaded Node Data Provider**
Create new module: `nk2dl/gui/panel/node_data.py`

```python
import threading
import time
from typing import List, Dict, Optional, Callable
from PySide2.QtCore import QObject, Signal

class NodeDataProvider(QObject):
    """Provides real node data for the panel table with threading support."""
    
    # Signals for progress and completion
    dataReady = Signal(list)  # Emitted when data is ready
    progressUpdate = Signal(int, str)  # Progress percentage and status message
    errorOccurred = Signal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self._worker_thread = None
        self._should_cancel = False
    
    def refresh_data_async(self):
        """Start background thread to refresh node data."""
        if self._worker_thread and self._worker_thread.is_alive():
            self._should_cancel = True
            self._worker_thread.join()
        
        self._should_cancel = False
        self._worker_thread = threading.Thread(target=self._refresh_worker)
        self._worker_thread.start()
    
    def _refresh_worker(self):
        """Background worker thread for data refresh."""
        try:
            # Use executeInMainThreadWithResult for Nuke API calls
            write_nodes_data = nuke.executeInMainThreadWithResult(
                self._get_write_nodes_data_sync
            )
            
            if not self._should_cancel:
                self.dataReady.emit(write_nodes_data)
                
        except Exception as e:
            if not self._should_cancel:
                self.errorOccurred.emit(str(e))
    
    def _get_write_nodes_data_sync(self):
        """Synchronous data collection (runs in main thread)."""
        node_types = self._get_write_node_types()
        all_nodes = []
        
        # Collect all write nodes
        for i, node_type in enumerate(node_types):
            if self._should_cancel:
                return []
                
            # Update progress
            progress = int((i / len(node_types)) * 50)  # First 50% for discovery
            nuke.executeInMainThread(
                self.progressUpdate.emit, 
                args=(progress, f"Finding {node_type} nodes...")
            )
            
            nodes = nuke.allNodes(node_type)
            all_nodes.extend(nodes)
            time.sleep(0.01)  # Small delay to allow cancellation
        
        # Extract data from nodes
        write_nodes_data = []
        for i, node in enumerate(all_nodes):
            if self._should_cancel:
                return []
                
            # Update progress  
            progress = 50 + int((i / len(all_nodes)) * 50)  # Second 50% for data extraction
            nuke.executeInMainThread(
                self.progressUpdate.emit,
                args=(progress, f"Processing {node.name()}...")
            )
            
            try:
                node_data = self._extract_node_data(node)
                write_nodes_data.append(node_data)
            except Exception as e:
                logger.warning(f"Failed to extract data from {node.name()}: {e}")
            
            time.sleep(0.01)  # Small delay
        
        # Final progress update
        nuke.executeInMainThread(
            self.progressUpdate.emit,
            args=(100, "Data loading complete")
        )
        
        return write_nodes_data
```

#### **1.2 Node Data Extraction Logic**
```python
def _extract_node_data(self, node):
    """Extract the first 3 columns from node."""
    return {
        "Node": node.name(),                    # Read-only
        "Filename": self._get_filename_only(node),  # Read-only  
        "Order": str(self._get_render_order(node)), # Editable
        # All other columns: None (inherit from settings)
    }

def _get_filename_only(self, node):
    """Extract filename only from node['file'].value()."""
    import os
    try:
        full_path = node['file'].value()
        return os.path.basename(full_path) if full_path else ""
    except:
        return ""

def _get_render_order(self, node):
    """Get render_order, create if doesn't exist."""
    try:
        if 'render_order' not in node.knobs():
            # Add render_order knob if it doesn't exist
            render_order_knob = nuke.Int_Knob('render_order', 'Render Order', 0)
            node.addKnob(render_order_knob)
        return node['render_order'].value()
    except:
        return 0
```

### **Phase 2: Progress UI Integration (1-2 hours)**

#### **2.1 Existing Progress Bar Integration**

**Use Existing Panel Progress Bar**
```python
class PanelProgressManager:
    """Manages the existing progress bar next to the render button."""
    
    def __init__(self, progress_bar, info_label):
        self.progress_bar = progress_bar
        self.info_label = info_label
        self._original_info_text = ""
        self._is_busy = False
    
    def start_operation(self, operation_name: str):
        """Start showing progress for an operation."""
        self._is_busy = True
        self._original_info_text = self.info_label.text()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.info_label.setText(f"{operation_name}...")
    
    def update_progress(self, progress: int, message: str):
        """Update progress and status message."""
        if self._is_busy:
            self.progress_bar.setValue(progress)
            self.info_label.setText(message)
    
    def finish_operation(self, success: bool = True, final_message: str = ""):
        """Finish the operation and reset UI."""
        self._is_busy = False
        if success:
            self.progress_bar.setValue(100)
            if final_message:
                self.info_label.setText(final_message)
                # Reset to original text after a delay
                QTimer.singleShot(2000, lambda: self.info_label.setText(self._original_info_text))
            else:
                self.info_label.setText(self._original_info_text)
        else:
            self.info_label.setText("Operation failed")
            QTimer.singleShot(3000, lambda: self.info_label.setText(self._original_info_text))
        
        # Hide progress bar after a short delay
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
```

#### **2.2 Update Button Enhancement**
```python
class NodeUpdateButton(QPushButton):
    """Enhanced update button with progress state."""
    
    def __init__(self, text="Update", parent=None):
        super().__init__(text, parent)
        self._is_updating = False
        self._original_text = text
    
    def set_updating_state(self, updating: bool, progress: int = 0):
        """Set the updating state of the button."""
        self._is_updating = updating
        if updating:
            self.setText(f"Updating... {progress}%")
            self.setEnabled(False)
        else:
            self.setText(self._original_text)
            self.setEnabled(True)
```

### **Phase 3: Settings Persistence with Sync (3-4 hours)**

#### **3.1 Root Node Storage with Node Sync**
```python
class NodeSettingsStorage:
    """Handles storage of user settings in root node with node synchronization."""
    
    def __init__(self):
        self._ensure_storage_knobs()
    
    def _ensure_storage_knobs(self):
        """Create nk2dl storage knobs if they don't exist."""
        root_node = nuke.root()
        all_knob_names = [knob.name() for knob in root_node.allKnobs()]
        
        if 'nk2dl' not in all_knob_names:
            root_node.addKnob(nuke.Tab_Knob('nk2dl', 'Nk2dl'))
        if 'nk2dl_settings' not in all_knob_names:
            root_node.addKnob(nuke.Multiline_Eval_String_Knob('nk2dl_settings', 'Nk2dl Settings'))
    
    def sync_with_current_nodes(self, current_nodes: List[str]):
        """Sync stored settings with current nodes in script."""
        stored_overrides = self.load_node_overrides()
        node_overrides = stored_overrides.get('node_overrides', {})
        
        # Remove settings for deleted nodes
        nodes_to_remove = []
        for node_name in node_overrides.keys():
            if node_name not in current_nodes:
                nodes_to_remove.append(node_name)
                logger.info(f"Removing settings for deleted node: {node_name}")
        
        for node_name in nodes_to_remove:
            del node_overrides[node_name]
        
        # Save updated settings if changes were made
        if nodes_to_remove:
            stored_overrides['node_overrides'] = node_overrides
            self.save_node_overrides(stored_overrides)
        
        return stored_overrides
```

#### **3.2 YAML Data Structure**
```yaml
# Structure for storing user overrides
node_overrides:
  Write1:
    Priority: "75"
    ChunkSize: "5" 
    Pool: "lighting"
    UseGPU: "Yes"
  Write2:
    Priority: "90"
    Frames: "1001-1500"
    Group: "high_priority" 
  # Only store explicitly set values, not inherited ones

# Metadata for sync tracking
_metadata:
  last_updated: "2024-01-15T10:30:00"
  nk2dl_version: "1.0.0"
```

### **Phase 4: Table Model Integration with Threading (2-3 hours)**

#### **4.1 Enhanced Table Model**
```python
class TableDataModel(QtCore.QObject):
    # Additional signals for loading states
    loadingStarted = Signal()
    loadingFinished = Signal()
    loadingProgress = Signal(int, str)
    
    def __init__(self, settings_model=None, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = TableColumns.HEADERS.copy()
        self.settings_model = settings_model
        self.node_data_provider = None
        self.settings_storage = NodeSettingsStorage()
        self._is_loading = False
        
    def set_node_data_provider(self, provider):
        """Set the node data provider and connect signals."""
        self.node_data_provider = provider
        provider.dataReady.connect(self._on_data_ready)
        provider.progressUpdate.connect(self._on_progress_update)
        provider.errorOccurred.connect(self._on_error_occurred)
    
    def refresh_from_nodes_async(self):
        """Refresh table data from current Nuke script nodes (async)."""
        if not self.node_data_provider or self._is_loading:
            return
            
        self._is_loading = True
        self.loadingStarted.emit()
        self.node_data_provider.refresh_data_async()
    
    def _on_data_ready(self, node_data):
        """Handle when node data is ready."""
        try:
            # Get current node names for sync
            current_nodes = [data.get("Node", "") for data in node_data]
            
            # Sync stored settings with current nodes
            stored_overrides = self.settings_storage.sync_with_current_nodes(current_nodes)
            
            # Merge node data with stored overrides
            merged_data = self._merge_node_data_with_overrides(node_data, stored_overrides)
            
            self.set_data(merged_data)
            
        finally:
            self._is_loading = False
            self.loadingFinished.emit()
    
    def _on_progress_update(self, progress, message):
        """Handle progress updates."""
        self.loadingProgress.emit(progress, message)
    
    def _on_error_occurred(self, error_message):
        """Handle errors during data loading."""
        logger.error(f"Node data loading failed: {error_message}")
        self._is_loading = False
        self.loadingFinished.emit()
        # Could emit a signal to show error in UI
```

### **Phase 5: Panel Integration (1-2 hours)**

#### **5.1 Panel Integration with Existing Progress Bar**
Based on the [Nuke Custom Panels documentation](https://learn.foundry.com/nuke/developers/63/pythondevguide/custom_panels.html), integrate with existing UI:

```python
# In the main panel class
def __init__(self):
    # ... existing initialization ...
    
    # Set up progress manager with existing widgets
    # Assuming the panel already has these widgets:
    # self.progress_bar (next to render button)
    # self.info_label (info area to the left)
    self.progress_manager = PanelProgressManager(
        self.progress_bar, 
        self.info_label
    )
    
    # Connect progress signals
    self.table_model.loadingStarted.connect(self._on_loading_started)
    self.table_model.loadingFinished.connect(self._on_loading_finished)
    self.table_model.loadingProgress.connect(self._on_loading_progress)
    
    # Auto-refresh on panel show
    if nuke_available():
        QTimer.singleShot(100, self._refresh_node_data)

def _refresh_node_data(self):
    """Refresh node data with progress indication."""
    if self.table_model and hasattr(self.table_model, 'refresh_from_nodes_async'):
        self.table_model.refresh_from_nodes_async()

def _on_loading_started(self):
    """Handle loading start."""
    self.progress_manager.start_operation("Loading node data")

def _on_loading_finished(self):
    """Handle loading completion."""
    # Count how many nodes were loaded
    node_count = self.table_model.get_row_count() if self.table_model else 0
    success_message = f"Loaded {node_count} write nodes"
    self.progress_manager.finish_operation(success=True, final_message=success_message)

def _on_loading_progress(self, progress, message):
    """Handle progress updates."""
    self.progress_manager.update_progress(progress, message)
```

#### **5.2 Update Button Integration**
```python
def setup_update_button(self):
    """Set up the update button with progress state."""
    self.update_button = NodeUpdateButton("Update Node Data")
    self.update_button.clicked.connect(self._refresh_node_data)
    
    # Connect to loading signals
    self.table_model.loadingStarted.connect(
        lambda: self.update_button.set_updating_state(True)
    )
    self.table_model.loadingFinished.connect(
        lambda: self.update_button.set_updating_state(False)
    )
    self.table_model.loadingProgress.connect(
        lambda p, m: self.update_button.set_updating_state(True, p)
    )
```

## 🔧 **Implementation Details**

### **Existing UI Integration**
- **Progress Bar**: Reuse the existing progress bar next to the render button
- **Info Area**: Use the existing info/status area to the left for operation messages
- **Update Button**: Enhance the existing "Update" button to show progress state
- **No Overlays**: Avoid creating modal overlays that would interrupt user workflow

### **Threading Best Practices** 
Based on [Nuke Threading documentation](https://learn.foundry.com/nuke/developers/63/pythondevguide/threading.html):

1. **Nuke API Access**: Always use `nuke.executeInMainThread()` or `nuke.executeInMainThreadWithResult()` for Nuke API calls from background threads
2. **UI Updates**: Use Qt signals to communicate from worker threads to UI thread
3. **Cancellation**: Implement proper cancellation mechanism for long-running operations
4. **Error Handling**: Graceful error handling in background threads

### **File Structure**
```
nk2dl/gui/panel/
├── node_data.py          # NEW: Threaded node data provider
├── storage.py            # NEW: Root node storage with sync
├── progress.py           # NEW: Panel progress manager (reuses existing widgets)
├── models/
│   ├── table_model.py    # MODIFY: Add threading support
│   └── ...
├── sample_data.py        # KEEP: For fallback/testing
└── ...
```

### **Performance Considerations**
- **Lazy Loading**: Only load data when panel is actually shown
- **Caching**: Cache node data until script changes or manual refresh
- **Cancellation**: Allow users to cancel long-running node discovery
- **Batch Processing**: Process nodes in batches with progress updates

### **Error Handling**
- **No Nuke available**: Fall back to sample data or show disabled state
- **No write nodes**: Show empty table with helpful message
- **YAML parsing errors**: Log warning, use empty overrides
- **Node access errors**: Skip problematic nodes, log warnings
- **Threading errors**: Graceful fallback to synchronous mode

## 🚨 **Migration Strategy**

### **Phase 1: Parallel Implementation**
- Keep existing sample data functional
- Add new real data system alongside
- Use feature flag to switch between modes

### **Phase 2: Gradual Rollout**
- Default to real data when Nuke is available
- Fall back to sample data for testing/development
- Validate behavior matches existing expectations

### **Phase 3: Cleanup**
- Remove sample data dependencies
- Update documentation
- Clean up unused code

## 📋 **Configuration Support**

### **Config Integration**
Support existing configuration patterns:
```yaml
submission:
  custom_write_classes: ['MyCustomWrite', 'StudioWrite']
panel:
  auto_refresh_nodes: true
  default_render_order: 0
  node_data_columns: ['Node', 'Filename', 'Order']  # Configurable first columns
  progress_mode: 'overlay'  # 'overlay' or 'header'
  background_refresh: true
  sync_on_script_change: true
```

## 🔍 **Success Criteria**

1. **Functionality**: Table populates with real write nodes from current script
2. **Performance**: Background loading doesn't block UI, shows progress  
3. **Editability**: Render order can be modified and persists to nodes  
4. **Persistence**: User overrides save/load correctly from root node
5. **Synchronization**: Settings stay in sync when nodes are added/removed
6. **Compatibility**: Works with existing Write, DeepWrite, and custom node types
7. **Error Handling**: Graceful fallback when Nuke unavailable or errors occur
8. **User Experience**: Clear progress indication and cancellation option

## 🚀 **Future Enhancements**

- **Live Updates**: Auto-refresh when nodes added/removed in script
- **Bulk Operations**: Select multiple nodes for batch render order changes
- **Validation**: Warn about duplicate render orders or missing files
- **Export/Import**: Save/load node configurations across scripts
- **Advanced Filtering**: Hide disabled nodes, filter by node type, etc.
- **Smart Caching**: Detect script changes and invalidate cache automatically

## ⚖️ **Risk Assessment**

### **Low Risk**
- Node data extraction (existing patterns in codebase)
- YAML storage (standard library, simple structure)  
- Qt threading (well-documented patterns)

### **Medium Risk**  
- Root node knob management (could conflict with other tools)
- Performance with large numbers of write nodes
- Thread synchronization complexity

### **High Risk**
- Nuke API threading requirements (must use executeInMainThread)
- UI responsiveness during heavy node operations
- Data consistency during concurrent access

### **Mitigation**
- Use unique knob names with 'nk2dl' prefix
- Implement proper Nuke threading patterns from documentation
- Add comprehensive error handling and fallbacks
- Extensive testing with various script configurations
- Progressive loading with cancellation support

This plan provides a comprehensive approach to replacing sample data with real Nuke node data while maintaining excellent user experience through proper threading and progress indication. 