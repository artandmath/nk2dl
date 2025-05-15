> [!NOTE]
> Documentation is auto-generated with claude-3.7, may not be current or accurate and is subject to change.

# Nuke Submission

The `nk2dl` Python module provides a flexible API for submitting Nuke scripts to Deadline.

## Basic Usage

To submit a Nuke script to Deadline:

```python
from nk2dl import submit_nuke_script

# Basic submission with minimal parameters
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    frames="1-100",         # Frame range to render
    write_nodes=["Write1"],  # Specific write nodes to render
)
```

## Parameters

`submit_nuke_script()` accepts the following parameters:

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_path` | str | - | Path to the Nuke script file |

### Optional nk2dl Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_is_open` | bool | `False` | Whether this script path is already open in the current Nuke session |
| `use_parser_instead_of_nuke` | bool | `False` | Use parser instead of Nuke for script analysis |
| `submit_writes_alphabetically` | bool | `False` | Sort write nodes alphabetically |
| `submit_writes_in_render_order` | bool | `False` | Sort write nodes by render order |
| `submit_script_as_auxiliary_file` | bool | `False` | Submit script as auxiliary file |

### Optional Job Info Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_name` | str | Config | Job name template |
| `batch_name` | str | Config | Batch name template |
| `priority` | int | Config | Job priority |
| `pool` | str | Config | Worker pool |
| `group` | str | Config | Worker group |
| `chunk_size` | int | Config | Number of frames per task |
| `department` | str | Config | Department |
| `comment` | str | Config | Job comment |
| `concurrent_tasks` | int | `1` | Number of parallel tasks for the job |
| `extra_info` | list | `[]` | List of extra info fields |
| `frames` | str | `""` | Frame range to render (e.g., "1-100", "f-l") |
| `job_dependencies` | str | `None` | Comma or space separated list of job IDs |
| `machine_list` | list | `None` | List of machine names to allow or deny |
| `machine_list_is_a_deny_list` | bool | `False` | Whether the machine list is a deny list |
| `machine_allow_list` | list | `None` | Alternative to machine_list, explicitly specifies an allow list |
| `machine_deny_list` | list | `None` | List of machine names to deny |

### Optional Plugin Info Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_file_path` | str | `""` | Output path for the rendered files |
| `parse_output_paths_to_deadline` | bool | `False` | Parse output paths to add as OutputFilename entries in job info |
| `nuke_version` | str/int/float | Config | Version of Nuke to use for rendering |
| `use_nuke_x` | bool | `False` | Use NukeX for rendering |
| `batch_mode` | bool | `True` | Use batch mode |
| `threads` | int | `None` | Number of render threads |
| `use_gpu` | bool | `False` | Use GPU for rendering |
| `gpu_override` | str | `None` | Specific GPU to use |
| `ram_use` | int | `None` | Maximum RAM usage (MB) |
| `enforce_render_order` | bool | `True` | Enforce write node render order |
| `stack_size` | int | `None` | Minimum stack size (MB) |
| `continue_on_error` | bool | `False` | Continue rendering on error |
| `reload_plugins` | bool | `False` | Reload plugins between tasks |
| `performance_profiler` | bool | `False` | Use the profiler |
| `performance_profiler_dir` | str | `None` | Directory for profile files |
| `use_proxy` | bool | `False` | Use proxy mode for rendering |
| `write_nodes` | list | `None` | List of write nodes to render |
| `render_mode` | str | `"full"` | Render mode (full, proxy) |
| `write_nodes_as_tasks` | bool | `False` | Submit write nodes as separate tasks |
| `write_nodes_as_separate_jobs` | bool | `False` | Submit write nodes as separate jobs |
| `render_order_dependencies` | bool | `False` | Set job dependencies based on render order |
| `use_node_frame_list` | bool | `False` | Use frame list from write nodes |

### Optional Environment Variables Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_current_environment` | bool | `False` | Use current environment variables |
| `environment_keys` | list | `[]` | List of environment variable keys to include from current environment |
| `environment` | dict | `{}` | Dictionary of environment variables to add |
| `omit_environment_keys` | list | `[]` | List of environment variable keys to omit |

### Optional Advanced Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `copy_script` | bool | Config | Copy script before submission |
| `submit_copied_script` | bool | Config | Submit copied script path |

## Script Copying

nk2dl provides options to copy scripts before submission:

```python
from nk2dl import submit_nuke_script

submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,  # Make a copy of the script
    submit_copied_script=True  # Submit the copied script
)
```

## Frame Ranges

The `frames` parameter accepts several formats:

### Numeric Frame Ranges

```python
submit_nuke_script("/path/to/script.nk", frames="1-100")       # Frames 1 to 100
submit_nuke_script("/path/to/script.nk", frames="1-100x10")    # Every 10th frame
submit_nuke_script("/path/to/script.nk", frames="1,10,20-40")  # Mixed specification
```

### Token-based Frame Ranges

```python
submit_nuke_script("/path/to/script.nk", frames="f-l")    # First to last frame in script
submit_nuke_script("/path/to/script.nk", frames="f,m,l")  # First, middle, and last frame
submit_nuke_script("/path/to/script.nk", frames="i")      # Input range from write node
```

## Write Nodes

Specify which write nodes to render:

```python
from nk2dl import submit_nuke_script

# Render specific write nodes
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"]
)
```

### Write Nodes as Separate Tasks

Submit write nodes as separate tasks in a single job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"],
    write_nodes_as_tasks=True
)
```

### Write Nodes as Separate Jobs

Submit each write node as a separate job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"],
    write_nodes_as_separate_jobs=True
)
```

### Render Order Dependencies

Create dependencies between write nodes based on their render order:

```python
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"],
    render_order_dependencies=True  # Automatically sets write_nodes_as_separate_jobs=True
)
```

## Environment Variables

Control environment variables for the Deadline job:

```python
submit_nuke_script(
    "/path/to/script.nk",
    use_current_environment=True  # Use all current environment variables
)
```

Or specify specific environment variables:

```python
submit_nuke_script(
    "/path/to/script.nk",
    environment_keys=["NUKE_PATH", "PYTHONPATH", "LICENSE_SERVER"],
    environment={"OCIO": "/path/to/config.ocio"}
)
```

## Machine Lists

Control which machines can or cannot render your job:

```python
# Allow specific machines only
submit_nuke_script(
    "/path/to/script.nk",
    machine_list=["render01", "render02", "render03"]
)

# Deny specific machines
submit_nuke_script(
    "/path/to/script.nk",
    machine_list=["render01", "render02"],
    machine_list_is_a_deny_list=True
)

# Alternative explicit syntax
submit_nuke_script(
    "/path/to/script.nk",
    machine_allow_list=["render01", "render02", "render03"]  # Same as machine_list
)

submit_nuke_script(
    "/path/to/script.nk",
    machine_deny_list=["render04", "render05"]  # Deny specific machines
)
```

Note: You cannot use both allow and deny lists in the same submission.

### Configuration

Machine lists can also be specified in the configuration files:

```yaml
submission:
  machine_allow_list: ["render01", "render02", "render03"]
  # OR
  machine_deny_list: ["render04", "render05"]
```

These configuration values will be used if no machine lists are explicitly provided in the submission parameters. The same validation rules apply - you cannot have both allow and deny lists in the configuration.

## Graph Scope Variables (Nuke 15.2+)

Submit multiple job variations using Graph Scope Variables:

```python
submit_nuke_script(
    "/path/to/script.nk",
    frames="1-100",
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020", "resolution:HD,2K,4K"]
)
```

This will generate 6 jobs (2 shotcodes × 3 resolutions) with all combinations.

You can also specify specific combinations to use:

```python
submit_nuke_script(
    "/path/to/script.nk",
    frames="1-100",
    graph_scope_variables=[
        ["shotcode:ABC_0010", "resolution:HD"],
        ["shotcode:ABC_0020", "resolution:4K"]
    ]
)
```

This will generate 2 jobs with specific combinations.

## Name and Comment Templates

The `job_name` and `comment` parameters support tokens that will be replaced at submission time:

```python
submit_nuke_script(
    "/path/to/script.nk",
    job_name="{file} / {write} / {range}",
    comment="Rendering frames {range} for {batch} in {write}"
)
```

### Available Tokens

| Token | Description |
|-------|-------------|
| `{file}` | Nuke script filename (without extension) |
| `{write}` | Write node name |
| `{range}` | Frame range |
| `{batch}` | Batch name |
| `{script}` | Full script filename with extension |
| `{output}` | Output filename from write node |
| `{render_order}` | Render order of write node |

## Job Return Values

The `submit_nuke_script` function returns a dictionary of job IDs:

```python
job_ids = submit_nuke_script("/path/to/script.nk", frames="1-100")
print(job_ids)  # {0: ['12345']}
```

For `render_order_dependencies`, the dictionary keys are render order values:

```python
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"],
    render_order_dependencies=True
)
print(job_ids)  # {10: ['12345'], 20: ['67890']}
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
