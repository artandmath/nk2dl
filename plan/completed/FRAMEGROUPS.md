# Frame Groups Implementation Plan

## Original question

I have an idea for a feature I'd like to explore. Don't make any code changes but rather come up with some avenues on how to implement my idea.

Here is my idea:

For the "frames" arg user could provide a list of strings. say ["f,m,l","1-100"] or a dict say {50:"f,m,l",40:"1-100"}. In the dict the keys indicate priority. Frames can still take strings as it currently does.

In the case where we are providing these multi-dimensional frame args, the NukeSubmission class would create multiple jobs. In the case of the list the jobs would be submitted one after another (f,m,l first, 1-100 next). In the case of the dict, the render order is specified, we would still submit them in the order they occur in the dict.

**Updated considerations:**
- When giving frame range groups, the lower priority or later submitted groups should remove any rendered frames. For example f,m,l subtracted from 1-100 leaves 2-49 (or 2-48 depending on what m actually is) and then 51-99
- Deadline will already do this if supplied as a single frame range string. i.e. "1,49,100,1-100" becomes "1,49,100,2-48,51-99" on the farm. So this feature should be implemented on the cases of list and dict groups only, leaving Deadline to handle string format
- I'm considering renaming FrameRange to Frames too to mirror the Deadline terminology. FrameGroups class should live in the common.frames module

There are a few things to consider and that is render order dependencies and writenodes that take dictionary based argument overrides. I haven't figured out in my head how these will be dealt with with the extra jobs being created. GSVs may also have an influence. Maybe you can look over the current code implementation and make some suggestions.

## Overview

This document outlines the implementation plan for adding multi-dimensional frame arguments support to nk2dl. The feature allows users to specify multiple frame ranges that will be submitted as separate jobs with optional priority-based ordering, dependency management, and automatic frame subtraction to avoid duplicate rendering.

## Feature Requirements

### User Interface
Users can provide frame arguments in three formats:

1. **String (existing)**: `"1-100"` - Single frame range (Deadline handles frame deduplication)
2. **List**: `["f,m,l", "1-100"]` - Multiple frame ranges submitted sequentially with frame subtraction
3. **Dict**: `{50: "f,m,l", 40: "1-100"}` - Multiple frame ranges with explicit priorities and frame subtraction

### Behavior
- **List format**: Jobs submitted in list order (first to last) with frame subtraction
- **Dict format**: Jobs submitted in priority order (highest priority first) with frame subtraction
- **Frame subtraction**: Later/lower priority groups automatically exclude frames already rendered by earlier/higher priority groups
- **Dependencies**: Each subsequent frame group depends on completion of previous groups
- **Integration**: Must work with existing features (GSVs, write node overrides, render order dependencies)

### Frame Subtraction Logic
- **String format**: No subtraction needed - Deadline handles deduplication automatically
- **List/Dict formats**: Each subsequent frame group has previously rendered frames subtracted
- **Example**: `["f,m,l", "1-100"]` where f=1, m=50, l=100 results in:
  - Job 1: "1,50,100" 
  - Job 2: "2-49,51-99" (1-100 minus 1,50,100)

## Current Architecture Analysis

### Key Components Affected
1. **Frame handling**: `self.frames` (string) → `Frames` object (renamed from FrameRange)
2. **Job submission**: `submit()` method with multiple job creation scenarios
3. **Write node overrides**: `WriteNodes` class for per-node parameter overrides
4. **Dependency management**: `self.jobs_by_render_order` tracking
5. **GSV combinations**: `self.gsv_combinations` for multiple GSV jobs
6. **New component**: `FrameGroups` class in `common.frames` module

### Existing Multi-Job Patterns
The codebase already handles multiple job creation for:
- **GSV combinations**: Creates jobs for each GSV combination
- **Write nodes as separate jobs**: Creates one job per write node
- **Render order dependencies**: Creates jobs with render-order-based dependencies

## Implementation Approach

### Approach: Frame Groups with Subtraction (Recommended)

Create frame groups as a new dimension in the job submission matrix, similar to GSV combinations, with automatic frame subtraction logic.

**Rationale**: 
- Fits naturally into existing architecture
- Follows established patterns (GSV combinations)
- Minimal disruption to existing code
- Maintains backward compatibility
- Leverages Deadline's existing frame deduplication for string inputs
- Implements frame subtraction only where needed (list/dict inputs)

## Implementation Plan

### Phase 1: Core Frame Groups Support (1.5 weeks)

#### 1.1 Rename and Extend Frame Classes
**File**: `nk2dl/common/frames.py` (renamed from `framerange.py`)

```python
# Rename FrameRange to Frames for Deadline terminology consistency
class Frames:
    """
    Class for validating and processing frame range strings with token substitution.
    Renamed from FrameRange to match Deadline terminology.
    """
    # ... existing FrameRange functionality with new name

class FrameGroups:
    """
    Handles multiple frame groups with priority-based ordering and frame subtraction.
    
    Supports:
    - List format: ["f,m,l", "1-100"] - sequential submission with subtraction
    - Dict format: {50: "f,m,l", 40: "1-100"} - priority-based submission with subtraction
    - String format: "1-100" - single submission (no subtraction needed)
    """
    
    def __init__(self, frames_input: Union[str, List[str], Dict[int, str]]):
        """Initialize frame groups from various input formats."""
        self.original_input = frames_input
        self.groups = []
        self.is_single_group = isinstance(frames_input, str)
        
        if self.is_single_group:
            # Single frame range - no groups needed
            self.single_frames = Frames(frames_input)
        else:
            self._parse_groups(frames_input)
    
    def _parse_groups(self, frames_input) -> None:
        """Parse frames input into prioritized groups."""
        if isinstance(frames_input, list):
            # Convert list to priority tuples (index as priority)
            self.groups = [(i, frame_range) for i, frame_range in enumerate(frames_input)]
        elif isinstance(frames_input, dict):
            # Use dict keys as priorities, sort by priority (highest first)
            self.groups = [(priority, frame_range) for priority, frame_range in frames_input.items()]
            self.groups.sort(key=lambda x: x[0], reverse=True)
        else:
            raise ValueError(f"Invalid frames format: {type(frames_input)}")
    
    def get_groups_with_subtraction(self, nuke_context=None) -> List[Tuple[int, str, Frames]]:
        """
        Get frame groups with subtraction applied.
        
        Returns:
            List of (priority, original_range, processed_frames) tuples
        """
        if self.is_single_group:
            return [(0, str(self.single_frames), self.single_frames)]
        
        processed_groups = []
        rendered_frames = set()
        
        for priority, frame_range in self.groups:
            # Create Frames object and substitute tokens if needed
            frames_obj = Frames(frame_range)
            if frames_obj.has_tokens and nuke_context:
                frames_obj.substitute_tokens_from_nuke()
            
            # Get expanded frame list
            current_frames = set(frames_obj.expand_range())
            
            # Subtract already rendered frames
            remaining_frames = current_frames - rendered_frames
            
            if remaining_frames:
                # Create new frame range string from remaining frames
                subtracted_range = self._frames_set_to_range_string(remaining_frames)
                subtracted_frames_obj = Frames(subtracted_range)
                
                processed_groups.append((priority, frame_range, subtracted_frames_obj))
                
                # Add current frames to rendered set
                rendered_frames.update(current_frames)
        
        return processed_groups
    
    @staticmethod
    def _frames_set_to_range_string(frames_set: set) -> str:
        """Convert a set of frame numbers to an optimized range string."""
        if not frames_set:
            return ""
        
        frames_list = sorted(frames_set)
        ranges = []
        start = frames_list[0]
        end = start
        
        for frame in frames_list[1:]:
            if frame == end + 1:
                end = frame
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = frame
        
        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ",".join(ranges)
    
    def validate(self) -> None:
        """Validate all frame groups."""
        if self.is_single_group:
            if not self.single_frames.is_valid_syntax():
                raise ValueError(f"Invalid frame range syntax: {self.single_frames}")
        else:
            for priority, frame_range in self.groups:
                frames_obj = Frames(frame_range)
                if not frames_obj.is_valid_syntax():
                    raise ValueError(f"Invalid frame range syntax: {frame_range}")
```

#### 1.2 Update Imports and References
**Files**: Update all imports from `framerange` to `frames` and `FrameRange` to `Frames`

```python
# nk2dl/nuke/submission.py
from ..common.frames import Frames, FrameGroups

# Update all FrameRange references to Frames
# Update self.fr to self.frames_obj for clarity
```

#### 1.3 Parameter Type Extension
**File**: `nk2dl/nuke/submission.py`

```python
# Modify __init__ method signature
frames: Union[str, List[str], Dict[int, str]] = "",

# Add new instance variables
self.frame_groups = FrameGroups(frames)
self.original_frames_input = frames
```

### Phase 2: Job Submission Integration (1.5 weeks)

#### 2.1 Submit Method Restructure
**File**: `nk2dl/nuke/submission.py`

```python
def submit(self) -> List[Dict[str, Any]]:
    """Submit the Nuke script to Deadline."""
    
    # Handle "both" render mode (existing logic)
    if self.render_mode.lower() == 'both':
        # ... existing both mode logic
    
    # Handle frame groups
    if not self.frame_groups.is_single_group:
        return self._submit_frame_groups()
    else:
        return self._submit_single_group()

def _submit_frame_groups(self) -> List[Dict[str, Any]]:
    """Submit multiple jobs for frame groups with subtraction."""
    all_jobs = []
    previous_job_ids = []
    
    # Get groups with frame subtraction applied
    processed_groups = self.frame_groups.get_groups_with_subtraction(nuke_context=True)
    
    for group_index, (priority, original_range, processed_frames) in enumerate(processed_groups):
        logger.info(f"Submitting frame group {group_index + 1}/{len(processed_groups)}: {original_range} -> {processed_frames}")
        
        # Skip if no frames remain after subtraction
        if not str(processed_frames):
            logger.info(f"Skipping frame group {group_index + 1} - no frames remaining after subtraction")
            continue
        
        # Temporarily set frame range for this group
        original_frames = self.frames
        self.frames = str(processed_frames)
        
        # Parse frame range for this group
        self.frames_obj = processed_frames
        
        try:
            # Submit jobs for this frame group
            group_jobs = self._submit_single_group(
                frame_group_info=(group_index, priority, original_range, str(processed_frames)),
                dependency_job_ids=previous_job_ids
            )
            
            all_jobs.extend(group_jobs)
            previous_job_ids = [job['job_id'] for job in group_jobs]
            
        finally:
            # Restore original frames
            self.frames = original_frames
    
    return all_jobs

def _submit_single_group(self, frame_group_info=None, dependency_job_ids=None) -> List[Dict[str, Any]]:
    """Submit jobs for a single frame group (or original single submission)."""
    # Move existing submit() logic here
    # Add frame group context to job naming and dependencies
```

#### 2.2 Job Naming Extension
**File**: `nk2dl/nuke/submission.py`

```python
def _get_frame_group_job_name(self, base_name: str, frame_group_info=None, write_node=None, gsv_combination=None) -> str:
    """Generate job name with frame group information."""
    if not frame_group_info:
        return base_name
    
    group_index, priority, original_range, processed_range = frame_group_info
    
    # Add frame group tokens
    tokens = {
        'frame_group_index': group_index + 1,
        'frame_group_priority': priority,
        'frame_group_original': original_range,
        'frame_group_processed': processed_range,
        'frame_group': f"grp{group_index + 1}"
    }
    
    # Apply tokens to job name
    job_name = base_name
    for token, value in tokens.items():
        job_name = job_name.replace(f"{{{token}}}", str(value))
    
    return job_name
```

#### 2.3 Dependency Management
**File**: `nk2dl/nuke/submission.py`

```python
def _add_frame_group_dependencies(self, job_info: Dict[str, Any], dependency_job_ids: List[str]) -> None:
    """Add frame group dependencies to job info."""
    if not dependency_job_ids:
        return
    
    # Count existing dependencies
    existing_deps = 0
    if self.job_dependencies:
        existing_deps = len(re.split(r'[,\s]+', self.job_dependencies.strip()))
    
    # Add frame group dependencies
    for i, dep_id in enumerate(dependency_job_ids):
        job_info[f"JobDependency{existing_deps + i}"] = dep_id
```

### Phase 3: Complex Feature Integration (1 week)

#### 3.1 GSV Integration
**File**: `nk2dl/nuke/submission.py`

Update the GSV submission loop to work within frame groups:

```python
# In _submit_single_group method
if self.graph_scope_variables and self.gsv_combinations:
    for gsv_combination in self.gsv_combinations:
        # Existing GSV logic, but with frame group context
        job_info = self._prepare_job_info(gsv_combination)
        
        # Add frame group dependencies
        if dependency_job_ids:
            self._add_frame_group_dependencies(job_info, dependency_job_ids)
        
        # Update job name with frame group info
        if frame_group_info:
            job_info["Name"] = self._get_frame_group_job_name(
                job_info["Name"], frame_group_info, None, gsv_combination
            )
```

#### 3.2 Write Node Override Integration
**File**: `nk2dl/nuke/submission.py`

Write node overrides should work seamlessly since they operate at the job level:

```python
# In write node submission loop
for write_node in sorted_write_nodes:
    # Existing write node override logic
    job_overrides = self.write_nodes_config.get_job_info_overrides(write_node)
    plugin_overrides = self.write_nodes_config.get_plugin_info_overrides(write_node)
    
    # Apply overrides (existing logic)
    # ...
    
    # Add frame group dependencies
    if dependency_job_ids:
        self._add_frame_group_dependencies(node_job_info, dependency_job_ids)
    
    # Update job name with frame group info
    if frame_group_info:
        node_job_info["Name"] = self._get_frame_group_job_name(
            node_job_info["Name"], frame_group_info, write_node
        )
```

#### 3.3 Render Order Dependencies
**File**: `nk2dl/nuke/submission.py`

Render order dependencies need special handling with frame groups:

```python
def _handle_render_order_with_frame_groups(self, render_order, unique_render_orders, dependency_count, frame_group_deps):
    """Handle render order dependencies with frame group context."""
    
    # Existing render order dependency logic
    if self.render_order_dependencies:
        current_index = unique_render_orders.index(render_order)
        if current_index > 0:
            previous_order = unique_render_orders[current_index - 1]
            if previous_order in self.jobs_by_render_order:
                render_order_deps = self.jobs_by_render_order[previous_order]
            else:
                render_order_deps = []
        else:
            render_order_deps = []
    else:
        render_order_deps = []
    
    # Combine frame group dependencies with render order dependencies
    all_deps = frame_group_deps + render_order_deps
    
    return all_deps
```

### Phase 4: CLI and API Integration (0.5 weeks)

#### 4.1 CLI Parameter Parsing
**File**: `nk2dl/cli/parser.py`

```python
# Update frames argument to support JSON input
frame_group.add_argument(
    "--Frames", "-f",
    metavar="RANGE",
    help="Frame range to render. Supports single range (e.g., '1-100'), "
         "list of ranges (e.g., '[\"f,m,l\", \"1-100\"]'), "
         "or priority dict (e.g., '{50: \"f,m,l\", 40: \"1-100\"}'). "
         "List and dict formats automatically subtract overlapping frames."
)
```

**File**: `nk2dl/cli/commands.py`

```python
def _parse_frames_argument(frames_str: str) -> Union[str, List[str], Dict[int, str]]:
    """Parse frames argument from CLI."""
    if not frames_str:
        return ""
    
    # Try to parse as JSON for list/dict formats
    try:
        parsed = json.loads(frames_str)
        if isinstance(parsed, (list, dict)):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Return as string for single frame range
    return frames_str

# In _args_to_kwargs function
if hasattr(args, "Frames") and args.Frames is not None:
    kwargs["frames"] = _parse_frames_argument(args.Frames)
```

#### 4.2 API Documentation Update
**File**: `docs/nuke_submission.md`

Add documentation for the new frame groups feature with examples and frame subtraction behavior.

### Phase 5: Testing and Validation (0.5 weeks)

#### 5.1 Unit Tests
**File**: `tests/test_frame_groups.py`

```python
def test_frame_groups_parsing():
    """Test frame groups parsing logic."""
    # Test list format
    # Test dict format
    # Test validation
    # Test error cases

def test_frame_subtraction():
    """Test frame subtraction logic."""
    # Test basic subtraction: ["f,m,l", "1-100"] 
    # Test complex overlaps
    # Test no remaining frames
    # Test edge cases

def test_frame_groups_job_creation():
    """Test job creation with frame groups."""
    # Test dependency creation
    # Test job naming
    # Test integration with other features

def test_frame_groups_with_gsv():
    """Test frame groups with GSV combinations."""
    
def test_frame_groups_with_write_nodes():
    """Test frame groups with write node overrides."""
```

#### 5.2 Integration Tests
Create comprehensive tests covering:
- Frame groups + GSVs
- Frame groups + write node overrides  
- Frame groups + render order dependencies
- All combinations together
- Frame subtraction accuracy

## Implementation Considerations

### Backward Compatibility
- Existing string `frames` parameter continues to work unchanged
- No breaking changes to existing API
- All existing functionality preserved
- FrameRange class renamed to Frames but functionality identical

### Performance
- Frame groups parsing happens once during initialization
- Frame subtraction computed once per submission
- Job submission scales linearly with number of groups
- Memory usage scales with number of jobs created

### Frame Subtraction Accuracy
- Uses set operations for precise frame subtraction
- Optimizes resulting frame ranges (e.g., "1,2,3,4,5" becomes "1-5")
- Handles complex overlapping scenarios correctly
- Skips groups with no remaining frames after subtraction

### Error Handling
- Clear validation of frame groups formats
- Meaningful error messages for invalid combinations
- Graceful handling of partial failures
- Validation of frame subtraction results

### Job Organization
- Clear job naming conventions with frame group information
- Logical dependency chains between frame groups
- Integration with existing job tracking and monitoring
- Frame subtraction information in job metadata

## Timeline

- **Phase 1**: Core Frame Groups Support - 1.5 weeks
- **Phase 2**: Job Submission Integration - 1.5 weeks  
- **Phase 3**: Complex Feature Integration - 1 week
- **Phase 4**: CLI and API Integration - 0.5 weeks
- **Phase 5**: Testing and Validation - 0.5 weeks

**Total**: 5 weeks

## Risks and Mitigations

### Risk: Complex Interaction Matrix
**Issue**: Frame groups × GSVs × Write nodes × Render order creates complex interaction matrix
**Mitigation**: Implement incrementally, test each combination thoroughly

### Risk: Frame Subtraction Complexity
**Issue**: Complex frame overlaps could lead to incorrect subtraction
**Mitigation**: Comprehensive unit tests, use proven set operations, validate results

### Risk: Job Explosion
**Issue**: Many frame groups with many write nodes could create excessive jobs
**Mitigation**: Add validation limits, clear warnings to users

### Risk: Dependency Chain Complexity
**Issue**: Long dependency chains could cause issues if early jobs fail
**Mitigation**: Implement robust error handling, consider parallel execution options

### Risk: Job Naming Conflicts
**Issue**: Complex naming with multiple dimensions could cause conflicts
**Mitigation**: Implement comprehensive job naming system with conflict detection

### Risk: Performance Impact
**Issue**: Frame subtraction computation could be expensive for large frame ranges
**Mitigation**: Optimize algorithms, cache results, profile performance

## Future Enhancements

1. **Parallel Frame Groups**: Option to submit frame groups in parallel rather than sequentially
2. **Conditional Dependencies**: More sophisticated dependency logic based on job outcomes
3. **Frame Group Templates**: Predefined frame group configurations
4. **UI Integration**: Nuke panel support for frame group configuration
5. **Monitoring Integration**: Enhanced job monitoring for frame group workflows
6. **Smart Frame Subtraction**: Machine learning-based optimization of frame group ordering
7. **Frame Group Validation**: Pre-submission validation of frame overlap efficiency 