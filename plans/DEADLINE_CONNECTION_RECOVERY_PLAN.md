# Deadline Connection Recovery Plan

## Problem Statement

When the Deadline web service fails, the connection automatically falls back to command line mode. However, once the web service is restored, the connection remains in command line mode until Nuke is restarted. This happens because:

1. The `DeadlineConnection` singleton sets `_initialized = True` after first connection
2. The `use_web_service` flag is permanently set to `False` during fallback
3. `ensure_connected()` never re-evaluates web service availability after initialization

## Goals

- **Primary**: Restore web service connection as soon as it becomes available again
- **Secondary**: Minimize performance impact and code complexity
- **Tertiary**: Maintain backward compatibility and existing fallback behavior

## Solution Options

### Option 1: Fresh Connection Per Submission (Simplest - Recommended)

**Approach**: Instead of caching the connection object, create a fresh connection for each submission. This automatically resolves the issue without any state tracking.

**Analysis**: 
Looking at the code, the connection is only used briefly during submission:
1. Line 2602: `self.deadline = get_connection()` 
2. Line 2490: `deadline_response = self.deadline.submit_job(job_info, plugin_info, auxiliary_files)`

The connection object doesn't need to persist between submissions. The only "expensive" operations are:
- Command line: Finding `deadlinecommand` path (done once in `_setup_command_line`)
- Web service: Import check and one test API call (`Groups.GetGroupNames()`)

These are minimal costs that don't justify the complexity of the singleton pattern.

**Implementation**:
```python
# Replace the singleton pattern in connection.py
def get_connection() -> DeadlineConnection:
    """Get a fresh connection instance."""
    return DeadlineConnection()

# Or even simpler, just inline it in submission.py:
def submit(self) -> List[Dict[str, Any]]:
    # Get fresh Deadline connection each time
    self.deadline = DeadlineConnection()
    self.deadline.ensure_connected()
```

**Benefits**:
- **Zero complexity** - no state tracking needed
- **Automatic recovery** - each submission tries web service first
- **No fallback tracking** - connection mode determined fresh each time
- **Clean and simple** - follows your "keep it simple" guideline
- **Performance negligible** - connection setup is very fast

### Option 2: Per-Submission Connection Check (Alternative)

**Approach**: Check web service availability at the start of each submission if currently in fallback mode.

**Implementation**:
```python
class DeadlineConnection:
    def __init__(self):
        self.preferred_web_service = config.get('deadline.use_web_service', False)
        self.use_web_service = self.preferred_web_service
        self._fallback_mode = False  # Track if we're in fallback
        
    def ensure_connected(self):
        # If we're in fallback mode and user prefers web service, try to restore
        if self._fallback_mode and self.preferred_web_service:
            if self._try_restore_web_service():
                self._fallback_mode = False
                self.use_web_service = True
                self._initialized = False  # Force re-init with web service
        
        # Existing connection logic...
        
    def _try_restore_web_service(self) -> bool:
        """Lightweight check to see if web service is available again."""
        try:
            # Quick connection test without full initialization
            host = config.get('deadline.host', 'localhost')
            port = config.get('deadline.port', 8081)
            # ... minimal connection test
            return True
        except:
            return False
            
    def _init_web_service(self):
        # Existing logic, but when falling back:
        self._fallback_mode = True  # Mark that we're in fallback
        self.use_web_service = False
```

**Pros**:
- Simple and targeted - only checks when needed
- Minimal performance impact (one check per submission)
- Restores web service quickly when available
- Low complexity addition

**Cons**:
- Only checks during submissions (not during other operations)
- Slight delay on first submission after web service restoration

### Option 2: Connection Health Monitoring

**Approach**: Add periodic health checks for web service restoration.

**Implementation**:
```python
class DeadlineConnection:
    def __init__(self):
        self._last_restore_check = 0
        self._restore_check_interval = 30  # seconds
        
    def ensure_connected(self):
        if self._should_check_restore():
            self._try_restore_web_service()
        # Existing logic...
        
    def _should_check_restore(self) -> bool:
        import time
        return (self._fallback_mode and 
                time.time() - self._last_restore_check > self._restore_check_interval)
```

**Pros**:
- Proactive restoration
- Works for all operations, not just submissions

**Cons**:
- More complex
- Adds background checking overhead
- May check unnecessarily

### Option 3: Explicit Connection Reset Method

**Approach**: Provide a way to manually reset the connection.

**Implementation**:
```python
class DeadlineConnection:
    def reset_connection(self):
        """Reset connection to allow re-evaluation of web service."""
        self._initialized = False
        self.use_web_service = self.preferred_web_service
        self._fallback_mode = False
        self._web_client = None

# Usage in GUI or API
def reset_deadline_connection():
    connection = get_connection()
    connection.reset_connection()
```

**Pros**:
- Simple implementation
- User control over when to retry
- No automatic overhead

**Cons**:
- Requires manual intervention
- Not automatic restoration

### Option 4: Smart Singleton with Auto-Recovery

**Approach**: Modify the singleton pattern to include automatic recovery logic.

**Implementation**:
```python
def get_connection() -> DeadlineConnection:
    """Get connection instance with smart recovery."""
    global _connection
    if _connection is None:
        _connection = DeadlineConnection()
    elif _connection._fallback_mode and _connection.preferred_web_service:
        # Check if we should attempt recovery
        if _connection._should_attempt_recovery():
            _connection._try_restore_web_service()
    return _connection
```

**Pros**:
- Centralized recovery logic
- Works for all connection usage

**Cons**:
- Modifies core singleton behavior
- May add overhead to all connection access

## Recommended Implementation Plan

### Phase 1: Fresh Connection Per Submission (Option 1)
This provides the ultimate simplicity while completely solving the issue.

**Changes needed**:

1. **Remove the singleton pattern from connection.py**:
   ```python
   # OLD CODE:
   _connection = None
   def get_connection() -> DeadlineConnection:
       global _connection
       if _connection is None:
           _connection = DeadlineConnection()
       return _connection
   
   # NEW CODE:
   def get_connection() -> DeadlineConnection:
       """Get a fresh connection instance."""
       return DeadlineConnection()
   ```

2. **That's it!** No other changes needed.

**Alternative even simpler approach**:
Remove `get_connection()` entirely and directly instantiate in submission.py:
```python
# In submission.py, line 2602:
# OLD: self.deadline = get_connection()
# NEW: self.deadline = DeadlineConnection()
#      self.deadline.ensure_connected()
```

### Phase 2: Optional Enhancements

If Phase 1 works well, consider adding:

1. **Configurable check interval**: Allow users to control how often restoration is attempted
2. **Connection status reporting**: Add methods to query current connection state
3. **Manual reset capability**: Add reset method for advanced users

## Testing Strategy

1. **Basic fallback**: Verify existing fallback behavior still works
2. **Automatic restoration**: Test that web service is used immediately when available again
3. **Performance**: Measure that fresh connection creation is negligible (should be < 50ms)
4. **Edge cases**: Test rapid web service on/off cycles
5. **Multiple submissions**: Verify each submission gets fresh connection attempt

## Implementation Notes

- No complex state tracking or fallback logic needed
- Maintain existing error handling and fallback behavior within each connection
- All existing connection methods work unchanged
- Consider updating documentation to reflect non-singleton behavior

## Benefits

- **Immediate restoration**: Web service tried fresh on every submission
- **Zero complexity**: Removes singleton complexity entirely  
- **Performance excellent**: Connection creation is ~10-50ms maximum
- **Backward compatible**: All existing APIs work unchanged
- **User-transparent**: No manual intervention required
- **Eliminates the bug**: Problem cannot occur with fresh connections

## Why This Is The Best Solution

This solution directly addresses the root cause: **persistent state**. By eliminating state persistence:

1. **No state to get stuck** - Each submission starts fresh
2. **No tracking needed** - Web service preference comes from config each time  
3. **Natural recovery** - If web service is available, it will be used
4. **Follows user principles** - "Keep it simple" and "as few lines as possible"
5. **Zero risk** - Cannot break existing functionality

The singleton pattern was premature optimization for a connection that's only used briefly during submission.
