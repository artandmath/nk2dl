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
| `render_settings_from_metadata` | bool | `False` | Extract submission settings from write node metadata |
| `script_job_script_path` | str | `None` | Path to a Python script to submit as a script job. When specified, sets ScriptJob=True and ScriptFilename to the provided path. ScriptJob is built-in functionality of the Deadline Nuke plugin that runs the script as a Python script job in the nuke script editor as a terminal session but cannot take any arguments. Consider using build job parameters instead as build jobs can use pre and post build job scripts to run Python scripts with arguments. |
| `submission_is_build_job` | bool | `False` | Submit as a Python script job that calls submit_nuke_script and enters a ready state loop |
| `build_job_script_path` | str | `None` | Full path template for the build job script file, supporting tokens for both directory and filename components (see below for available tokens) |
| `build_job_as_auxiliary_file` | bool | `True` | Whether to submit the build job script as an auxiliary file (default: True). When True, the job can be recovered if it fails since Deadline will re-copy the script to the worker. When False, the job cannot be restarted if the script file is deleted.
| `delete_build_job_script` | bool | `True` | Whether to automatically delete the build job script after execution (default: True)

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
| `user_name` | str | Config | User name |
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
| `performance_profiler_path` | str | `None` | Directory for profile files |
| `views` | list | `None` | List of view names to render |
| `write_nodes` | list/dict | `None` | Write nodes to render. Can be a simple list of names, a dict with overrides, or a list of dicts for multiple nodes with individual overrides |
| `render_mode` | str | `"full"` | Render mode (full, proxy, both). When set to "both", two separate submissions are created - one with "full" and one with "proxy" |
| `proxy_args` | dict | `{}` | Dictionary of arguments to override for the proxy submission when render_mode="both".rwise ignored. |
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
| `copy_script_path` | str/list/dict | Config | Full path template(s) for script copying (directory + filename); can be string, list of strings, or dict with integer keys |
| `submit_copied_script` | bool | Config | Submit copied script path |

## Script Copying

nk2dl provides options to copy scripts before submission:

```python
from nk2dl import submit_nuke_script

# Basic copying with defaults
submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,  # Make a copy of the script
    submit_copied_script=True  # Submit the copied script
)

# Specify custom location for the copy (full path with directory and filename)
submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,
    copy_script_path="{output}/farm/{basename}_{YYYY}-{MM}-{DD}.{ext}",
    submit_copied_script=True
)

# Create multiple copies in different locations
submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,
    copy_script_path=[
        "{outdir}/farm/{nkstem}.nk", 
        "{nkdir}/archive/{nkstem}_{YYYY}-{MM}-{DD}.nk"
    ],
    submit_copied_script=True
)
```

### Available Script Copy Tokens

For `copy_script_path` (full path including directory and filename):
- Script directory tokens: `{nkdir}`, `{scriptdir}`, `{nukescriptdir}`
- Script stem tokens: `{nkstem}`, `{scriptstem}`, `{nukescriptstem}`
- Script name tokens: `{nk}`, `{script}`, `{scriptname}`, `{nukescript}`
- Output directory tokens: `{outdir}`, `{outputdir}`
- Output stem tokens: `{filestem}`, `{filenamestem}`, `{outstem}`, `{outputstem}`
- Output tokens: `{output}`
- Date tokens: `{YYYY}` (year), `{YY}` (2-digit year), `{MM}` (month), `{DD}` (day), `{hh}` (hour), `{mm}` (minute), `{ss}` (second)
- Temp directory tokens: `{tmp}`, `{temp}`, `{tmpdir}`, `{tempdir}`
- UUID token: `{uuid}`

## ScriptJob Submission

nk2dl supports submitting Python scripts as ScriptJobs using the Deadline Nuke plugin's built-in ScriptJob functionality:

```python
from nk2dl import submit_nuke_script

# Submit a Python script as a ScriptJob
submit_nuke_script(
    "/path/to/nukescript.nk",
    script_job_script_path="/path/to/my_python_script.py"
)
```

ScriptJob submissions are also supported via the command line interface:

```bash
# Submit a Python script as a ScriptJob via CLI
nk2dl submit /path/to/nukescript.nk --ScriptJobScript "/path/to/my_python_script.py"
```

### ScriptJob vs Build Job

There are two ways to run Python scripts in nk2dl:

1. **ScriptJob** (`script_job_script_path`): Uses Deadline's built-in Nuke plugin ScriptJob functionality
   - Runs the script in Nuke's script editor as a terminal session
   - Cannot pass arguments to the script
   - Simpler setup, but limited functionality

2. **Build Job** (`submission_is_build_job=True`): Creates a custom Python script that calls `submit_nuke_script`
   - Can use pre and post build job scripts with arguments
   - More flexible and powerful
   - Can handle complex submission workflows

Example of ScriptJob usage:

```python
# Simple ScriptJob - no arguments supported
submit_nuke_script(
    "/path/to/nukescript.nk",
    script_job_script_path="/shared/scripts/render_setup.py"
)

# Build Job alternative - supports arguments and workflows
submit_nuke_script(
    "/path/to/nukescript.nk", 
    submission_is_build_job=True,
    pre_build_job_script=["/shared/scripts/pre_render.py", "arg1", "arg2"],
    post_build_job_script=["/shared/scripts/post_render.py", "success"]
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

### Write Node Overrides

The `write_nodes` parameter now supports advanced configuration with per-node overrides:

```python
# Single write node with overrides
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes={
        'write_node': 'Write1',   # Required key
        'priority': 90,           # Override job priority
        'use_gpu': True           # Enable GPU rendering
    }
)

# Multiple write nodes with individual settings
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=[
        {
            'write_node': 'Write1',
            'priority': 90,       # Higher priority
            'chunk_size': 5       # Smaller chunks
        },
        {
            'write_node': 'Write2',
            'priority': 50,       # Lower priority
            'ram_use': 16000,     # More RAM
            'threads': 16         # More threads
        },
        'Write3'  # Regular write node without overrides
    ]
)
```

#### Override Parameters

You can use both nk2dl parameter names or direct Deadline job/plugin info keys:

- **nk2dl parameters** (automatically translated to Deadline keys):
  ```python
  write_nodes={
      'write_node': 'Write1',
      'priority': 90,           # Translated to 'Priority'
      'chunk_size': 5,          # Translated to 'ChunkSize'
      'use_gpu': True,          # Translated to 'UseGpu': '1'
      'ram_use': 16000          # Translated to 'RamUse': '16000'
  }
  ```

- **Direct Deadline keys**:
  ```python
  write_nodes={
      'write_node': 'Write1',
      'Priority': 90,           # Direct Deadline job info parameter
      'ChunkSize': 5,           # Direct Deadline job info parameter
      'UseGpu': '1',            # Direct Deadline plugin info parameter
      'RamUse': '16000'         # Direct Deadline plugin info parameter
  }
  ```

- **Mixed approach** (both nk2dl and Deadline parameters):
  ```python
  write_nodes={
      'write_node': 'Write1',
      'priority': 90,           # nk2dl parameter
      'ChunkSize': 5,           # Direct Deadline parameter
      'use_gpu': True,          # nk2dl parameter
      'RamUse': '16000'         # Direct Deadline parameter
  }
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

## Dual Render Mode (Full + Proxy)

nk2dl supports submitting both full and proxy renders simultaneously with different settings for each:

```python
from nk2dl import submit_nuke_script

# Submit both full and proxy renders with same settings
submit_nuke_script(
    "/path/to/script.nk",
    render_mode="both",
    priority=50,
    chunk_size=10
)

# Submit both renders with different settings for proxy
submit_nuke_script(
    "/path/to/script.nk",
    render_mode="both",
    priority=50,              # Applied to both full and proxy
    chunk_size=10,            # Applied to both full and proxy
    proxy_args={
        'priority': 30,       # Lower priority for proxy
        'chunk_size': 20,     # Larger chunks for proxy
        'pool': 'proxy_pool', # Different pool for proxy
        'comment': 'Proxy render for review'
    }
)

# Advanced example with write node overrides
submit_nuke_script(
    "/path/to/script.nk",
    render_mode="both",
    write_nodes_as_separate_jobs=True,
    write_nodes=[
        {
            'write_node': 'Write1',
            'priority': 80,
            'use_gpu': True
        },
        'Write2'
    ],
    proxy_args={
        'priority': 40,       # Override base priority for all proxy jobs
        'use_gpu': False,     # Disable GPU for proxy renders
        'batch_name': 'Proxy Batch'
    }
)
```

### How Dual Render Mode Works

When `render_mode="both"` is specified:

1. **Full Render**: Uses all the provided parameters with `render_mode="full"`
2. **Proxy Render**: Uses all the provided parameters with `render_mode="proxy"`, plus any overrides from `proxy_args`

The `proxy_args` dictionary can contain any valid submission parameter and will override the base parameters only for the proxy submission.

## Render Settings from Write Node Metadata

You can store submission settings directly in write node metadata and have them automatically applied during submission:

```python
from nk2dl import submit_nuke_script

# Enable metadata-based settings
submit_nuke_script(
    "/path/to/script.nk",
    write_nodes=["Write1", "Write2", "Write3"],
    write_nodes_as_separate_jobs=True,
    render_settings_from_metadata=True  # Extract settings from write node metadata
)
```

### Available Script Tokens

For `build_job_script_path`:
- Script directory tokens: `{sdir}`, `{nkdir}`, `{s_dir}`, `{nk_dir}`, `{scriptdir}`, `{script_dir}`, `{nukescriptdir}`, `{nukescript_dir}`, `{nuke_script_dir}`
- Script stem tokens: `{ss}`, `{basename}`, `{stem}`, `{sstem}`, `{nstem}`, `{nkstem}`, `{scriptstem}`, `{script_stem}`, `{nukescriptstem}`, `{nukescript_stem}`, `{nuke_script_stem}`
- Script name tokens: `{s}`, `{ns}`, `{nk}`, `{script}`, `{scriptname}`, `{script_name}`, `{nukescript}`, `{nuke_script}`
- Date tokens: `{YYYY}` (year), `{YY}` (2-digit year), `{MM}` (month), `{DD}` (day), `{hh}`