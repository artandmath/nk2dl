# Real-Time Job Submission Capture Strategies

## Problem Analysis

The current `submit_nuke_script()` function is **synchronous** and only returns results after completion, which prevents real-time progress updates for individual job submissions. The existing panel implementation uses **logging capture** but this approach has limitations:

1. **Log parsing complexity**: Need to parse unstructured log messages
2. **Timing issues**: Log messages may not align perfectly with job completion
3. **Missing structured data**: Logs don't always contain job IDs in parseable format
4. **No dependency information**: Can't easily extract render order relationships

## Proposed Solutions

### Option 1: Callback-Based submit_nuke_script() Enhancement ⭐ **RECOMMENDED**

Modify the `NukeSubmission` class to accept callback functions for progress reporting, with wrapper function support.

#### Callback Parameter Definitions:

**Connection Status Callback**: `connection_status_callback(message: str, status_type: str)`
- `message`: Human-readable status message  
- `status_type`: Message priority level
  - `"info"`: General information (attempting connection)
  - `"success"`: Successful operation (job submitted)
  - `"warning"`: Issue but operation succeeded (fallback occurred)
  - `"error"`: Operation failed

**Job Submitted Callback**: `job_submitted_callback(node_name: str, job_id: str, render_order: int, status: str, connection_type: str, error: str = None)`
- `connection_type` values:
  - `"web"`: Web Service connection
  - `"command_line"`: Direct Command Line or Command Line Fallback

**Progress Callback**: `progress_callback(message: str)`
- Simple progress messages for current operation

#### Implementation:

**Approach A: Modify NukeSubmission Class (Primary Implementation)**
```python
class NukeSubmission:
    def __init__(self, 
                # ... existing params
                progress_callback=None,
                job_submitted_callback=None,
                connection_status_callback=None):
        """Initialize with optional callbacks for real-time progress reporting."""
        
        # Store callbacks
        self.progress_callback = progress_callback
        self.job_submitted_callback = job_submitted_callback  
        self.connection_status_callback = connection_status_callback
        # ... rest of initialization
        
    def submit(self) -> List[Dict[str, Any]]:
        """Submit with real-time callback support."""
        
        # Get Deadline connection (line ~2718) - this is instantaneous
        self.deadline = get_connection()
        
        # Connection testing happens during first job submission via ensure_connected()
        
        # ... existing setup code ...
        
        # In the write node processing loop (around line 2968)
        for write_node in sorted_write_nodes:
            if self.progress_callback:
                self.progress_callback(f"Submitting {write_node}...")
                
            # Get render order for this node (line ~2972-2973)
            render_order = write_node_render_orders[write_node]
            
            # ... existing job/plugin info setup ...
            
            # Submit individual job (line ~3082)
            try:
                # Connection testing and fallback happens here in submit_job()
                if self.connection_status_callback:
                    # Determine connection method being attempted
                    connection_method = "Web Service" if self.deadline.use_web_service else "Command Line"
                    self.connection_status_callback(f"Submitting via {connection_method}...", "info")
                
                self._submit_job(node_job_info, node_plugin_info, render_order, write_node, None, auxiliary_files)
                
                # Get connection type from last submission (may have changed due to fallback)
                last_job = self.jobs[-1]
                connection_type = last_job["deadline_return"].get("connection_type", "unknown")
                
                if self.connection_status_callback:
                    # Map connection_type to descriptive names
                    connection_names = {
                        "web": "Web Service",
                        "command_line": "Command Line Fallback" if self.deadline.use_web_service else "Command Line"
                    }
                    connection_name = connection_names.get(connection_type, connection_type)
                    
                    if connection_type == "command_line" and self.deadline.use_web_service:
                        # This was a fallback scenario
                        self.connection_status_callback(f"Fell back to Command Line - Job submitted successfully", "warning")
                    else:
                        self.connection_status_callback(f"Job submitted via {connection_name}", "success")
                
                if self.job_submitted_callback:
                    self.job_submitted_callback(
                        node_name=write_node,
                        job_id=last_job["job_id"],
                        render_order=render_order,
                        status='success',
                        connection_type=connection_type
                    )
            except Exception as e:
                if self.connection_status_callback:
                    self.connection_status_callback(f"Submission failed: {str(e)}", "error")
                
                if self.job_submitted_callback:
                    self.job_submitted_callback(
                        node_name=write_node,
                        job_id=None,
                        render_order=render_order,
                        status='failed',
                        error=str(e)
                    )
                raise
        
        return self.jobs
```

**Approach B: Wrapper Function Support**

The wrapper function `submit_nuke_script()` requires **no changes** since it already passes `**kwargs` directly to `NukeSubmission.__init__()` at line 4100:

```python
# Existing code at line ~4100 already works:
submission = NukeSubmission(script_path=script_path, **kwargs)
return submission.submit()
```

Any callback parameters passed to `submit_nuke_script()` will automatically be forwarded to the `NukeSubmission` constructor.

#### Advantages:
- ✅ **Clean integration**: Builds on existing NukeSubmission architecture
- ✅ **Structured data**: Get exact job info when available
- ✅ **Backward compatible**: Optional callbacks don't break existing usage
- ✅ **Real-time updates**: Immediate feedback as each job submits

#### Important Considerations:
- ⚠️ **Subprocess mode**: When `launch_subprocess = True`, callbacks won't work across process boundaries
- ⚠️ **Build job mode**: Callbacks may not work in build job submissions (`submission_is_build_job = True`)
- ⚠️ **Thread safety**: GUI callbacks must be thread-safe
- ⚠️ **Error handling**: Callback failures shouldn't break submission process
- ⚠️ **Dynamic connection fallback**: Connection type can change mid-submission (Web Service → Command Line)
- ⚠️ **Connection testing is per-job**: Real connection validation happens during `submit_job()`, not at connection time

### Option 2: Event-Based Submission System

Create an event-driven submission system that emits events during the submission process.

#### Implementation:
```python
from typing import Protocol
import threading

class SubmissionEventHandler(Protocol):
    def on_connection_status(self, status: str, details: str): ...
    def on_job_submitted(self, node: str, job_id: str, order: int): ...
    def on_progress_update(self, message: str, percentage: int): ...

class EventDrivenSubmitter:
    def __init__(self, event_handler: SubmissionEventHandler):
        self.event_handler = event_handler
        
    def submit_with_events(self, script_path, **kwargs):
        # Emit events throughout submission
        self.event_handler.on_connection_status("connecting", "192.168.1.5")
        
        for i, write_node in enumerate(write_nodes):
            self.event_handler.on_progress_update(f"Submitting {write_node}", 
                                                 int((i/len(write_nodes)) * 100))
            
            job_result = self._submit_single_job(write_node)
            self.event_handler.on_job_submitted(write_node, job_result['job_id'], 
                                               get_render_order(write_node))
```

#### Advantages:
- ✅ **Event-driven**: Clean separation of concerns
- ✅ **Flexible**: Easy to add new event types
- ✅ **Testable**: Events can be mocked for testing

#### Disadvantages:
- ❌ **More complex**: Requires more significant code changes

### Option 3: Enhanced Logging with Structured Messages ⭐ **IMMEDIATE IMPROVEMENT**

Improve the current logging approach with **structured log messages** that can be easily parsed.

#### Implementation:
```python
import json
import logging

# In submission code
logger = logging.getLogger('nk2dl.submission.structured')

def submit_job_with_structured_logging(write_node):
    # Structured progress update
    logger.info(json.dumps({
        'type': 'progress',
        'action': 'submitting',
        'node': write_node,
        'timestamp': time.time()
    }))
    
    # Submit job
    result = deadline_submit(write_node)
    
    # Structured job result
    logger.info(json.dumps({
        'type': 'job_submitted',
        'node': write_node,
        'job_id': result['job_id'],
        'render_order': get_render_order(write_node),
        'timestamp': time.time(),
        'status': 'success'
    }))
    
    return result
```

#### In Worker:
```python
class StructuredLogHandler(logging.Handler):
    def __init__(self, progress_dialog):
        super().__init__()
        self.progress_dialog = progress_dialog
        
    def emit(self, record):
        try:
            # Try to parse as structured JSON
            data = json.loads(record.getMessage())
            
            if data['type'] == 'job_submitted':
                self.progress_dialog.add_job_to_tree(
                    data['node'], data['job_id'], data['render_order']
                )
            elif data['type'] == 'progress':
                self.progress_dialog.update_progress(data['action'], data['node'])
                
        except (json.JSONDecodeError, KeyError):
            # Fall back to regular log handling
            self.progress_dialog.add_log_message(record.getMessage())
```

#### Advantages:
- ✅ **Immediate implementation**: Can be done with current architecture
- ✅ **Structured data**: JSON provides clean data extraction
- ✅ **Backward compatible**: Regular logs still work
- ✅ **Minimal changes**: Only affects logging statements

### Option 4: Threaded Submission with Shared State

Use a shared data structure between submission thread and UI thread.

#### Implementation:
```python
import threading
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class JobSubmissionState:
    submitted_jobs: List[dict]
    current_job: Optional[str]
    connection_status: str
    lock: threading.Lock

class ThreadedSubmitter:
    def __init__(self):
        self.state = JobSubmissionState([], None, "disconnected", threading.Lock())
        
    def submit_with_state_sharing(self, script_path, **kwargs):
        for write_node in write_nodes:
            with self.state.lock:
                self.state.current_job = write_node
                
            job_result = submit_single_job(write_node)
            
            with self.state.lock:
                self.state.submitted_jobs.append({
                    'node': write_node,
                    'job_id': job_result['job_id'],
                    'render_order': get_render_order(write_node)
                })
                
    def get_current_state(self):
        with self.state.lock:
            return {
                'submitted_jobs': self.state.submitted_jobs.copy(),
                'current_job': self.state.current_job,
                'connection_status': self.state.connection_status
            }
```

#### In Progress Dialog:
```python
class JobSubmissionProgressDialog(QtWidgets.QDialog):
    def __init__(self, submitter: ThreadedSubmitter):
        self.submitter = submitter
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.poll_submission_state)
        self.update_timer.start(100)  # Poll every 100ms
        
    def poll_submission_state(self):
        state = self.submitter.get_current_state()
        self.update_tree_from_state(state['submitted_jobs'])
        self.update_current_task(state['current_job'])
```

#### Advantages:
- ✅ **Thread-safe**: Uses proper locking
- ✅ **Real-time**: Polling provides frequent updates
- ✅ **Simple**: Easy to understand and implement

#### Disadvantages:
- ❌ **Polling overhead**: Regular polling uses CPU cycles
- ❌ **Shared state complexity**: Needs careful lock management

## Recommended Implementation Strategy

### Phase 1: Quick Win with Structured Logging (Option 3)
- ✅ **Immediate**: Can be implemented right away
- ✅ **Low risk**: Minimal changes to existing code
- ✅ **Good results**: Much better than current unstructured logging

### Phase 2: Enhanced Core Function (Option 1)  
- ✅ **Ideal solution**: Clean, efficient, and flexible
- ✅ **Future-proof**: Sets up proper architecture for other improvements
- ✅ **Backward compatible**: Doesn't break existing usage

### Phase 3: Event System (Option 2) - If Needed
- Only if more complex event handling is required
- Good for extensive plugin systems or multiple UI components

## Implementation for Menu Progress Bar

For the immediate menu-based progress bar implementation, I recommend:

### 1. Use Structured Logging Approach
```python
# In submit_selected_writes_to_deadline()
def submit_selected_writes_to_deadline():
    # ... existing validation code ...
    
    # Create progress dialog
    progress_dialog = JobSubmissionProgressDialog("Job Submission Progress")
    progress_dialog.show()
    
    # Create enhanced worker with structured log parsing
    worker = StructuredSubmissionWorker(
        script_path=nuke.root().name(),
        write_nodes=write_node_names,
        progress_dialog=progress_dialog
    )
    
    # Start worker
    QtCore.QThreadPool.globalInstance().start(worker)
```

### 2. Enhanced Worker Implementation (Updated for Callback Support)
```python
class CallbackSubmissionWorker(QtCore.QRunnable):
    def __init__(self, script_path, write_nodes, progress_dialog):
        super().__init__()
        self.script_path = script_path
        self.write_nodes = write_nodes
        self.progress_dialog = progress_dialog
        
    def run(self):
        try:
            # Define callback functions
            def on_progress(message):
                # Thread-safe progress update
                QtCore.QMetaObject.invokeMethod(
                    self.progress_dialog, 
                    "update_progress", 
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, message)
                )
            
            def on_job_submitted(node_name, job_id, render_order, status, error=None):
                # Thread-safe job tree update
                QtCore.QMetaObject.invokeMethod(
                    self.progress_dialog, 
                    "add_job_to_tree", 
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, node_name),
                    QtCore.Q_ARG(str, job_id or ""),
                    QtCore.Q_ARG(int, render_order),
                    QtCore.Q_ARG(str, status)
                )
            
            def on_connection_status(message, status_type):
                # Thread-safe connection status update
                # status_type can be: "info", "success", "warning", "error"
                # Allows UI to color-code or prioritize messages appropriately
                QtCore.QMetaObject.invokeMethod(
                    self.progress_dialog, 
                    "update_connection_status", 
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, message),
                    QtCore.Q_ARG(str, status_type)
                )
            
            # Call submission with callbacks
            from nk2dl import submit_nuke_script
            results = submit_nuke_script(
                self.script_path,
                script_is_open=True,
                write_nodes=self.write_nodes,
                progress_callback=on_progress,
                job_submitted_callback=on_job_submitted,
                connection_status_callback=on_connection_status
                # ... other args
            )
            
            # Show completion
            QtCore.QMetaObject.invokeMethod(
                self.progress_dialog, 
                "show_completion", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(list, results)
            )
            
        except Exception as e:
            # Handle errors thread-safely
            QtCore.QMetaObject.invokeMethod(
                self.progress_dialog, 
                "show_error", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, str(e))
            )
```

### 3. Fallback: Enhanced Structured Logging (For Subprocess/Build Job Cases)
```python
class StructuredSubmissionWorker(QtCore.QRunnable):
    """Fallback worker for cases where callbacks don't work (subprocess mode, etc.)"""
    def __init__(self, script_path, write_nodes, progress_dialog):
        super().__init__()
        self.script_path = script_path
        self.write_nodes = write_nodes
        self.progress_dialog = progress_dialog
        
    def run(self):
        # Set up structured log handler as fallback
        handler = StructuredLogHandler(self.progress_dialog)
        
        # Add to nk2dl loggers
        for logger_name in ['nk2dl.submission', 'nk2dl.deadline']:
            logger = logging.getLogger(logger_name)
            logger.addHandler(handler)
            
        try:
            # Call existing submission function (without callbacks for compatibility)
            from nk2dl import submit_nuke_script
            results = submit_nuke_script(
                self.script_path,
                script_is_open=True,
                write_nodes=self.write_nodes,
                # Note: No callbacks here - relies on enhanced logging
            )
            
            self.progress_dialog.show_completion(results)
            
        finally:
            # Clean up handlers
            for logger_name in ['nk2dl.submission', 'nk2dl.deadline']:
                logger = logging.getLogger(logger_name)
                logger.removeHandler(handler)
```

This approach provides:
- ✅ **Real-time updates** as jobs submit via callbacks
- ✅ **Structured data** for job IDs and render orders  
- ✅ **Connection status** monitoring
- ✅ **Incremental tree building** as requested
- ✅ **Thread-safe GUI updates** using Qt's QMetaObject.invokeMethod
- ✅ **Fallback compatibility** for subprocess/build job modes using enhanced logging
- ✅ **Backward compatibility** with existing submission workflows

## Implementation Priority

1. **Primary**: Implement callback-based approach in `NukeSubmission` class for direct submission cases
2. **Secondary**: Enhance structured logging for subprocess/build job fallback scenarios  
3. **Testing**: Verify both approaches work across different submission modes (separate jobs, tasks, GSV, etc.)

The key is to enhance the **nk2dl core submission architecture** with callback support while maintaining structured logging as a fallback, giving us reliable real-time updates across all submission scenarios.
