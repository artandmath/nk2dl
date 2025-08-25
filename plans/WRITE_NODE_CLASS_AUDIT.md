# Write Node Class Audit and Fix Plan

## Overview

This document identifies instances in the codebase where write node class checks are incomplete - only checking for "Write" nodes but missing "DeepWrite" and custom write node classes. The proper implementation should check for all write node types as defined in the configuration.

## Current Proper Implementation

The correct implementation exists in `src/nk2dl/submission.py` in the `_all_write_nodes()` method (lines 970-1003) and in the worker code:

```python
def _all_write_nodes(self, filter_types=None):
    """Get all write nodes of specified types.
    
    Args:
        filter_types: Optional list of write node types to include.
                     Defaults to ['Write', 'DeepWrite'] plus any custom_write_classes from config.
                     
    Returns:
        List of write nodes matching the specified types
    """
    # Set default filter types if none provided
    if filter_types is None:
        # Start with default write node types
        filter_types = ['Write', 'DeepWrite']
        # Add any custom write classes from config
        custom_classes = config.get('submission.custom_write_classes', [])
        if custom_classes:
            filter_types.extend(custom_classes)
    
    # Ensure the script is open
    nuke = self._ensure_script_can_be_parsed()
    
    # Get all nodes of the specified types
    all_write_nodes = []
    for node_type in filter_types:
        all_nodes = nuke.allNodes(recurseGroups=True)
        for node in all_nodes:
            if node.Class() == node_type:
                all_write_nodes.append(node)
    
    return all_write_nodes
```

## Problematic Areas Identified

### 1. Token Replacement for Output Stems (Line 1145)

**File:** `src/nk2dl/submission.py`  
**Location:** `_replace_job_name_tokens()` method, line 1145

```python
if node and node.Class() == "Write":
```

**Issue:** Only checks for "Write" class when extracting output file stems for token replacement.

**Impact:** DeepWrite and custom write nodes won't have their output paths used for job name token replacement.

### 2. Token Replacement for Output Directories (Line 1162)

**File:** `src/nk2dl/submission.py`  
**Location:** `_replace_job_name_tokens()` method, line 1162

```python
if node and node.Class() == "Write":
```

**Issue:** Similar to above, only checks for "Write" class for output directory token replacement.

**Impact:** DeepWrite and custom write nodes won't have their output directories used for token replacement.

### 3. General Token Replacement (Line 1237)

**File:** `src/nk2dl/submission.py`  
**Location:** `_replace_job_name_tokens()` method, line 1237

```python
if node and node.Class() == "Write":
```

**Issue:** Only checks for "Write" class for general write node token replacement.

**Impact:** Various tokens related to write nodes won't work with DeepWrite and custom write nodes.

### 4. Movie Format Detection (Line 1614)

**File:** `src/nk2dl/submission.py`  
**Location:** `_is_movie_format()` method, line 1614

```python
if node and node.Class() == "Write" and 'file_type' in node.knobs():
```

**Issue:** Only checks "Write" nodes for movie format detection.

**Impact:** DeepWrite and custom write nodes that output movie formats won't be detected properly, potentially affecting job submission parameters.

### 5. Output Filename Collection for Tasks (Line 1879)

**File:** `src/nk2dl/submission.py`  
**Location:** `_prepare_job_info()` method, line 1879

```python
if node and node.Class() == "Write" and not node['disable'].value():
```

**Issue:** Only collects output filenames from "Write" nodes when using write_nodes_as_tasks.

**Impact:** DeepWrite and custom write nodes won't have their output filenames included in the job submission when using task-based submission.

### 6. Single Write Node Output (Line 1888)

**File:** `src/nk2dl/submission.py`  
**Location:** `_prepare_job_info()` method, line 1888

```python
if node and node.Class() == "Write" and not node['disable'].value():
```

**Issue:** Similar to above for single write node submissions.

**Impact:** DeepWrite and custom write nodes won't have their output filenames included in single node submissions.

### 7. Frame Range Detection (Line 2118)

**File:** `src/nk2dl/submission.py`  
**Location:** `_prepare_plugin_info()` method, line 2118

```python
if node and node.Class() == "Write":
```

**Issue:** Only checks "Write" nodes when determining frame ranges for individual write nodes.

**Impact:** DeepWrite and custom write nodes won't have their frame ranges properly detected when using use_node_frame_list or input token resolution.

### 8. Separate Jobs Output Collection (Line 2727)

**File:** `src/nk2dl/submission.py`  
**Location:** `_prepare_plugin_info()` method, line 2727

```python
if node_obj and node_obj.Class() == "Write" and not node_obj['disable'].value():
```

**Issue:** Only collects output filenames from "Write" nodes when using write_nodes_as_separate_jobs.

**Impact:** DeepWrite and custom write nodes won't have their output filenames included when submitting as separate jobs.

### 9. Render Order Dependencies Output (Line 2896)

**File:** `src/nk2dl/submission.py`  
**Location:** `_prepare_plugin_info()` method, line 2896

```python
if node_obj and node_obj.Class() == "Write" and not node_obj['disable'].value():
```

**Issue:** Only collects output filenames from "Write" nodes when using render_order_dependencies.

**Impact:** DeepWrite and custom write nodes won't have their output filenames included when using render order dependencies.

### 10. Metadata Extraction (Line 3583)

**File:** `src/nk2dl/submission.py`  
**Location:** `_extract_metadata_from_write_node()` method, line 3583

```python
if not node or node.Class() != "Write":
```

**Issue:** Only allows metadata extraction from "Write" nodes.

**Impact:** DeepWrite and custom write nodes can't have their metadata extracted for render_settings_from_metadata feature.

### 11. Parser Implementation (Line 196)

**File:** `src/nk2dl/parser.py`  
**Location:** `allNodes()` method, line 196

```python
return [node for node in self.nodes.values() if node.Class() == node_type]
```

**Issue:** The parser only has a WriteNode class but no DeepWriteNode or custom write node classes.

**Impact:** When using the parser instead of Nuke, only Write nodes will be recognized.

## Recommended Fixes

### 1. Create a Helper Method

Add a helper method to `NukeSubmission` class to centralize write node type checking:

```python
def _is_write_node(self, node):
    """Check if a node is any type of write node (Write, DeepWrite, or custom).
    
    Args:
        node: Nuke node to check
        
    Returns:
        bool: True if node is a write node type, False otherwise
    """
    if not node:
        return False
        
    node_class = node.Class()
    
    # Check standard write node types
    if node_class in ['Write', 'DeepWrite']:
        return True
        
    # Check custom write classes from config
    custom_classes = config.get('submission.custom_write_classes', [])
    return node_class in custom_classes
```

### 2. Replace All Hard-coded Checks

Replace all instances of `node.Class() == "Write"` with calls to `self._is_write_node(node)`.

### 3. Update Parser Implementation

Extend the parser to support DeepWrite and custom write node classes:

```python
class DeepWriteNode(NukeNode):
    """Class representing a DeepWrite node in a Nuke script."""
    
    def __init__(self, name: str):
        super().__init__(name, "DeepWrite")
        # Add similar knobs as WriteNode
        self._knobs["file"] = NukeKnob("file", "")
        self._knobs["file_type"] = NukeKnob("file_type", "exr")
        self._knobs["disable"] = NukeKnob("disable", False)
        self._knobs["render_order"] = NukeKnob("render_order", 0)
        self._knobs["use_limit"] = NukeKnob("use_limit", False)
        self._knobs["first"] = NukeKnob("first", 1)
        self._knobs["last"] = NukeKnob("last", 100)
```

And update the parser to create appropriate node types based on configuration.

### 4. Testing Considerations

Add test cases that verify:
- DeepWrite nodes are properly handled in all the identified problematic areas
- Custom write node classes (configured via `custom_write_classes`) work correctly
- Mixed scenarios with Write, DeepWrite, and custom nodes all work together

## Implementation Priority

1. **High Priority:** Core functionality issues (items 5, 6, 7, 8, 9) - these affect actual job submission
2. **Medium Priority:** Token replacement issues (items 1, 2, 3) - these affect job naming and organization
3. **Medium Priority:** Metadata extraction (item 10) - affects render_settings_from_metadata feature
4. **Low Priority:** Movie format detection (item 4) - affects some job optimization features
5. **Low Priority:** Parser implementation (item 11) - only affects scenarios where parser is used instead of Nuke

## Configuration Requirements

Ensure that `custom_write_classes` in the configuration is properly documented and tested:

```yaml
submission:
  # Additional custom write node types (Write and DeepWrite are always included)
  # Example: custom_write_classes: ["CustomWrite", "StudioWrite", "MyWriteNode"]
  custom_write_classes: []
```

## Backward Compatibility

All proposed changes maintain backward compatibility as they expand functionality rather than change existing behavior. Scripts that only use "Write" nodes will continue to work exactly as before.
