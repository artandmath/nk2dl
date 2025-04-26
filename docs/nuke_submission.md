> [!NOTE]
> Documentation is auto-generated with claude-3.7, may not be current or accurate and is subject to change.

# Nuke Submission

The `nk2dl` Python module provides a flexible API for submitting Nuke scripts to Deadline.

## Basic Usage

```python
from nk2dl.nuke import submit_nuke_script

# Submit a Nuke script with default settings
job_ids = submit_nuke_script("/path/to/script.nk")
```

## Advanced Options

### General Submission Options

```python
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    frame_range="1-100",         # Frame range to render
    priority=75,                 # Job priority (0-100)
    use_nuke_x=True,             # Use NukeX instead of regular Nuke
    use_nuke_studio=False,       # Use Nuke Studio instead of regular Nuke
    render_threads=16,           # Number of render threads to use
    use_gpu=True,                # Enable GPU rendering
    job_name="{script_stem}_{write}",  # Job name template
    batch_name="Project_123",    # Batch name
    department="comp",           # Department name
    pool="nuke",                 # Deadline pool
    group="farm",                # Deadline group
    chunk_size=10,               # Frame chunk size
    machine_limit=0,             # Limit number of machines (0 for unlimited)
    concurrent_tasks=1,          # Number of concurrent tasks
    enable_auto_timeout=False,   # Enable auto timeout
    task_timeout_minutes=0,      # Task timeout in minutes (0 for none)
    limit_tasks_to_cpus=True,    # Limit concurrent tasks to number of CPUs
    on_job_complete="Nothing"    # Action on job completion)
```

### Complete Parameter List

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_path` | str | (Required) | Path to the Nuke script file |
| `frame_range` | str | `None` | Frame range to render (e.g., "1-100", "f-l") |
| `priority` | int | 50 | Job priority (0-100) |
| `department` | str | "comp" | Department name |
| `pool` | str | "none" | Deadline pool |
| `secondary_pool` | str | `""` | Secondary Deadline pool |
| `group` | str | "none" | Deadline group |
| `chunk_size` | int | 10 | Frame chunk size |
| `job_name` | str | `"{script_stem}_{write}"` | Job name template |
| `batch_name` | str | `"{script_stem}"` | Batch name template |
| `use_nuke_x` | bool | `False` | Use NukeX instead of regular Nuke |
| `use_nuke_studio` | bool | `False` | Use Nuke Studio instead of regular Nuke |
| `render_threads` | int | 0 | Number of render threads (0 for auto) |
| `use_gpu` | bool | `False` | Enable GPU rendering |
| `enable_performance_profiler` | bool | `False` | Enable performance profiler |
| `performance_profile_dir` | str | `""` | Directory to store performance profiles |
| `machine_limit` | int | 0 | Limit number of machines (0 for unlimited) |
| `concurrent_tasks` | int | 1 | Number of concurrent tasks |
| `enable_auto_timeout` | bool | `False` | Enable auto timeout |
| `task_timeout_minutes` | int | 0 | Task timeout in minutes (0 for none) |
| `limit_tasks_to_cpus` | bool | `True` | Limit concurrent tasks to number of CPUs |
| `on_job_complete` | str | "Nothing" | Action on job completion |
| `init_script` | str | `""` | Script to run before rendering |
| `post_job_script` | str | `""` | Script to run after job completes |
| `environment` | dict | `{}` | Environment variables to set for the job |
| `write_nodes` | list | `None` | List of write nodes to render (None for all) |
| `write_nodes_as_separate_jobs` | bool | `False` | Submit write nodes as separate jobs |
| `write_nodes_as_tasks` | bool | `False` | Submit write nodes as tasks |
| `render_order_dependencies` | bool | `False` | Create dependencies based on render order |
| `graph_scope_variables` | list | `None` | Graph scope variables specification |
| `post_render_script` | str | `""` | Script to run after rendering |
| `submit_suspended` | bool | `False` | Submit job in suspended state |
| `nuke_executable` | str | `None` | Custom path to Nuke executable |
| `nuke_version` | str | `None` | Specific Nuke version to use |
| `progress_callback` | callable | `None` | Callback function for progress updates |
| `custom_plugin_info` | dict | `{}` | Additional plugin info parameters |
| `custom_job_info` | dict | `{}` | Additional job info parameters |

### Write Node Control

You can control which write nodes to render and how they are submitted:

```python
# Submit specific write nodes
job_ids = submit_nuke_script("/path/to/script.nk", write_nodes=["Write1", "Write2"])

# Submit write nodes as separate jobs
job_ids = submit_nuke_script("/path/to/script.nk", write_nodes_as_separate_jobs=True)

# Submit write nodes as separate tasks
job_ids = submit_nuke_script("/path/to/script.nk", write_nodes_as_tasks=True)

# Set dependencies based on render order
job_ids = submit_nuke_script("/path/to/script.nk", render_order_dependencies=True)
```

### Frame Range Specification

The `frame_range` parameter accepts several formats:

```python
# Standard frame ranges
submit_nuke_script("/path/to/script.nk", frame_range="1-100")       # Frames 1 to 100
submit_nuke_script("/path/to/script.nk", frame_range="1-100x10")    # Every 10th frame
submit_nuke_script("/path/to/script.nk", frame_range="1,10,20-40")  # Mixed specification

# Special tokens
submit_nuke_script("/path/to/script.nk", frame_range="f-l")    # First to last frame in script
submit_nuke_script("/path/to/script.nk", frame_range="f,m,l")  # First, middle, and last frame
submit_nuke_script("/path/to/script.nk", frame_range="i")      # Input range from write node
```

### Graph Scope Variables

Graph Scope Variables (available in Nuke 15.2+) can be specified in several ways:

```python
# Single variable
submit_nuke_script("/path/to/script.nk", graph_scope_variables=["shotcode:ABC_0010"])

# Multiple values for a single variable
submit_nuke_script("/path/to/script.nk", graph_scope_variables=["shotcode:ABC_0010,ABC_0020"])

# Sets of variables (creates multiple jobs with different combinations)
submit_nuke_script("/path/to/script.nk", graph_scope_variables=[
    ["shotcode:ABC_0010,ABC_0020", "res:wh,hh"],
    ["shotcode:XYZ_0010,XYZ_0020,XYZ_0030", "res:wh"]
])

# Combined with other options
submit_nuke_script(
    "/path/to/script.nk",
    frame_range="1-100",
    write_nodes=["Write1", "Write2"],
    graph_scope_variables=["shotcode:ABC_0010"]
)
```

### Performance Profiling

Enable performance profiling for optimization:

```python
submit_nuke_script(
    "/path/to/script.nk",
    enable_performance_profiler=True,
    performance_profile_dir="/path/to/profiles"
)
```

### Custom Scripts and Hooks

Add custom scripts to run at different stages of the job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    init_script="print('Starting job')",  # Runs before render starts
    post_render_script="print('Render complete')",  # Runs after each frame
    post_job_script="print('Job complete')"  # Runs when job finishes
)
```

### Environment Variables

Set environment variables for the render job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    environment={
        "MY_PROJECT_ROOT": "/path/to/project",
        "CUSTOM_LUT_PATH": "/path/to/luts",
        "NUKE_PATH": "/path/to/nuke/plugins"
    }
)
```

### Custom Parameters

Pass custom parameters directly to Deadline:

```python
submit_nuke_script(
    "/path/to/script.nk",
    custom_job_info={
        "BuildGroup": "build_123",
        "ExtraInfo0": "ClientX",
        "ExtraInfo1": "ProjectY"
    },
    custom_plugin_info={
        "SceneFile": "/path/to/additional/file.txt",
        "CustomProperty": "value"
    }
)
```

### Progress Callback

Register a callback function to receive progress updates:

```python
def my_progress_callback(progress, message):
    print(f"Progress: {progress}% - {message}")

submit_nuke_script(
    "/path/to/script.nk",
    progress_callback=my_progress_callback
)
```

## Return Value

The `submit_nuke_script` function returns a list of Deadline job IDs that were created:

```python
job_ids = submit_nuke_script("/path/to/script.nk")
print(f"Submitted {len(job_ids)} jobs with IDs: {job_ids}")
```

## Error Handling

The function may raise exceptions if there are issues with submission:

```python
from nk2dl.common.errors import DeadlineError, NukeError

try:
    job_ids = submit_nuke_script("/path/to/script.nk")
    print(f"Successfully submitted {len(job_ids)} jobs")
except DeadlineError as e:
    print(f"Deadline error: {e}")
except NukeError as e:
    print(f"Nuke error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Using in Nuke GUI

To use `nk2dl` within the Nuke GUI:

1. Ensure that the `nk2dl` package is available in your Nuke Python path
2. Create an init.py file that adds the path to your `nk2dl` installation
3. Import and use the module in your Nuke Python scripts or panels

Example init.py:

```python
import sys
import os

# Add nk2dl to the Python path
nk2dl_path = "/path/to/nk2dl"
if os.path.exists(nk2dl_path) and nk2dl_path not in sys.path:
    sys.path.append(nk2dl_path)
```

## Practical Examples

### Basic Production Setup

```python
from nk2dl.nuke import submit_nuke_script

# Submit a show with standard settings
job_ids = submit_nuke_script(
    "/shows/project123/shots/shot001/comp/shot001_comp_v003.nk",
    pool="nuke",
    group="renderfarm",
    priority=60,
    department="comp",
    batch_name="Project123_dailies",
    job_name="{script_stem}_{write}",
    chunk_size=5,
    use_nuke_x=True,
    render_threads=16
)
```

### Multi-Shot Submission with Variables

```python
from nk2dl.nuke import submit_nuke_script

# Submit multiple shots using graph scope variables
job_ids = submit_nuke_script(
    "/shows/project123/templates/shot_template.nk",
    batch_name="Project123_overnight",
    graph_scope_variables=[
        ["shotcode:shot001,shot002,shot003", "version:v001,v002"]
    ],
    frame_range="1-100",
    priority=80,
    write_nodes_as_separate_jobs=True
) 
