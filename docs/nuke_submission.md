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
    on_job_complete="Nothing"   # Action on job completion
)
```

### Complete Parameter List

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_path` | str | (Required) | Path to the Nuke script file |
| `script_is_open` | bool | `False` | Whether the script is already open in the current Nuke session |
| `submit_alphabetically` | bool | `False` | Whether to sort write nodes alphabetically by name |
| `submit_in_render_order` | bool | `False` | Whether to sort write nodes by render order |
| `submit_script_as_auxiliary_file` | bool | `None` | Whether to submit the script as an auxiliary file |
| `copy_script` | bool | `None` | Copy the script to configured location(s) before submission |
| `submit_copied_script` | bool | `None` | Use the copied script for rendering instead of the original |
| `job_name` | str | `None` | Job name template |
| `batch_name` | str | `None` | Batch name template |
| `priority` | int | `None` | Job priority (0-100) |
| `pool` | str | `None` | Deadline pool |
| `group` | str | `None` | Deadline group |
| `chunk_size` | int | `None` | Frame chunk size |
| `department` | str | `None` | Department name |
| `comment` | str | `None` | Comment for the job |
| `concurrent_tasks` | int | `None` | Number of concurrent tasks |
| `extra_info` | list | `None` | Extra information for the job |
| `frame_range` | str | `""` | Frame range to render (e.g., "1-100", "f-l") |
| `job_dependencies` | str | `None` | Job dependencies |
| `output_path` | str | `""` | Output path for the rendered files |
| `nuke_version` | str/int/float | `None` | Specific Nuke version to use |
| `use_nuke_x` | bool | `False` | Use NukeX instead of regular Nuke |
| `use_batch_mode` | bool | `True` | Use batch mode for rendering |
| `render_threads` | int | `None` | Number of render threads (0 for auto) |
| `use_gpu` | bool | `False` | Enable GPU rendering |
| `gpu_override` | str | `None` | Specific GPU to use for rendering |
| `max_ram_usage` | int | `None` | Maximum RAM usage in MB |
| `enforce_render_order` | bool | `True` | Enforce write node render order |
| `min_stack_size` | int | `None` | Minimum stack size in MB |
| `continue_on_error` | bool | `False` | Continue rendering if errors occur |
| `reload_plugins` | bool | `False` | Reload plugins between tasks |
| `use_profiler` | bool | `False` | Enable performance profiler |
| `profile_dir` | str | `None` | Directory to store performance profiles |
| `use_proxy` | bool | `False` | Use proxy mode for rendering |
| `write_nodes` | list | `None` | List of write nodes to render (None for all) |
| `render_mode` | str | `"full"` | Render mode to use |
| `write_nodes_as_tasks` | bool | `False` | Submit write nodes as tasks |
| `write_nodes_as_separate_jobs` | bool | `False` | Submit write nodes as separate jobs |
| `render_order_dependencies` | bool | `False` | Create dependencies based on render order |
| `use_nodes_frame_list` | bool | `False` | Use frame list from write nodes |
| `graph_scope_variables` | list | `None` | Graph scope variables specification |

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

### Script as Auxiliary File

The `submit_script_as_auxiliary_file` option makes Deadline treat the Nuke script as an auxiliary file, which has these benefits:

1. The script is automatically uploaded to Deadline's auxiliary files
2. The script becomes part of the job and is available on all render nodes
3. The script is preserved with the job history for future reference
4. Reduces network dependencies as the script is stored within Deadline

> [!WARNING]
> If path mapping is enabled in the plugin settings on the deadline repository then scripts are automatically treated like auxilary files and a modified copy is loaded to each deadline worker regardless of whether `submit_script_as_auxiliary_file` is `True` or `False`. If path mapping is enabled and the nukescript contains a project directory that needs to evaluate the path then it is recommended to use the `copy_script` functionality.

```python
# Submit script as an auxiliary file
job_ids = submit_nuke_script("/path/to/script.nk", submit_script_as_auxiliary_file=True)

# Combine with script copying
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,
    submit_copied_script=True,
    submit_script_as_auxiliary_file=True
)
```

This option is particularly useful when:
- You want to ensure the script is always available for job reruns
- The original script location may be inaccessible to render nodes
- You need to preserve the exact script version used for a particular render
- You're submitting from a temporary location

> [!NOTE]
> When both `submit_copied_script` and `submit_script_as_auxiliary_file` are enabled, the copied script is submitted as the auxiliary file.

### Script Copying Options

You can control whether the Nuke script is copied before submission and whether the copied script is used for rendering:

```python
# Copy script to a farm-specific location before submission
job_ids = submit_nuke_script("/path/to/script.nk", copy_script=True)

# Use the copied script for rendering instead of the original
job_ids = submit_nuke_script("/path/to/script.nk", copy_script=True, submit_copied_script=True)
```

#### What is script copying?

The `copy_script` option creates a copy of your Nuke script in a specified location before submitting it to Deadline. This can be useful to:

1. Create a snapshot of the script at submission time
2. Place the script in a location accessible to render nodes
3. Generate archive copies of scripts for each submission
4. Resolve project directory references to absolute paths

The copy location and naming convention can be configured through:
- Configuration option `submission.copy_script` (default: `False`)
- Configuration option `submission.submit_copied_script` (default: `False`) 
- Configuration options for path and naming:
  - Single copy: `submission.script_copy_path`, `submission.script_copy_relative_to`, `submission.script_copy_name`
  - Multiple copies: `submission.script_copy0_path`, `submission.script_copy0_relative_to`, etc.

#### What is submit_copied_script?

The `submit_copied_script` option makes Deadline render using the copied script instead of the original script. This is useful when:

1. The original script location is not accessible to render nodes
2. You want to ensure rendering uses the exact script state at submission time
3. You're organizing scripts in a farm-specific structure

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

### Performance Profiling (NOT IMPLEMENTED/HALLUCINATION)

Enable performance profiling for optimization:

```python
submit_nuke_script(
    "/path/to/script.nk",
    enable_performance_profiler=True,
    performance_profile_dir="/path/to/profiles"
)
```

### Custom Scripts and Hooks (NOT IMPLEMENTED/HALLUCINATION)

Add custom scripts to run at different stages of the job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    init_script="print('Starting job')",  # Runs before render starts
    post_render_script="print('Render complete')",  # Runs after each frame
    post_job_script="print('Job complete')"  # Runs when job finishes
)
```

### Environment Variables (NOT IMPLEMENTED/HALLUCINATION)

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

### Custom Parameters (NOT IMPLEMENTED/HALLUCINATION)

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

### Progress Callback (NOT IMPLEMENTED/HALLUCINATION)

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

The `submit_nuke_script` function returns a dictionary where keys are integers and values are lists of strings representing Deadline job IDs:

```python
job_ids = submit_nuke_script("/path/to/script.nk")
print(f"Submitted jobs with IDs: {job_ids}")
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

## Using in Nuke GUI (UNTESTED)

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
    priority=50,
    department="comp",
    batch_name="{scriptname}",
    job_name="{batchname} | {write} | {output}",
    chunk_size=5,
    use_nuke_x=True,
    render_threads=0
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
        ["shotcode:shot001,shot002,shot003", "res:full"],
        ["shotcode:shot004,shot005,shot006", "res:half"]
    ],
    frame_range="1-100",
    priority=80,
    write_nodes_as_separate_jobs=True
) 
```
