# Quickstart Usage Guide 

This guide provides a quick overview of how to use nk2dl to submit Nuke scripts to Deadline. For installation and configuration, refer to the [Installation Guide](./installation.md).

## Python

```python
from nk2dl.nuke import submit_nuke_script

# Basic usage
job_ids = submit_nuke_script("/path/to/script.nk")

# Advanced usage with options
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    frames="1001-1100",
    job_name="My Nuke Job",
    batch_name="My Batch",
    write_nodes=["Write1", "Write2"],
    threads=16,
    ram_use=16384,
    use_node_frame_list=True,
    environment_keys=["NUKE_PATH", "OCIO"],
    environment={"PROJECT_ROOT": "/path/to/project"},
)

print(f"Job IDs: {job_ids}")
```

## Command Line Interface

```bash
# Help docs
nk2dl submit --help

# Basic submission
nk2dl submit /path/to/script.nk

# With options
nk2dl submit /path/to/script.nk --frame-range 1-100 --priority 75 --use-nuke-x --render-threads 16 --use-gpu
```

# Advanced Options

## Environment Variables

When submitting to Deadline, you can control which environment variables are passed to the render jobs using these configuration options:

```yaml
submission:
  # Pass all environment variables from the submitting environment to Deadline jobs
  use_current_environment: false
  
  # Include only specific environment variables from current environment
  include_environment_keys:
    - "NUKE_PATH"
    - "PYTHONPATH"
    - "LICENSE_SERVER"
  
  # Specify exact environment variables to pass to Deadline jobs
  environment:
    NUKE_PATH: "/path/to/nuke/tools"
    PYTHONPATH: "/path/to/python/modules"
    LICENSE_SERVER: "license-server:port"
  
  # Exclude specific environment variables (useful with use_current_environment: true)
  omit_environment_keys:
    - "TEMP"
    - "TMP"
    - "USERNAME"
```

These environment variables are sent to Deadline in the jobinfo file using Deadline's `EnvironmentKeyValue` format and will be available to the render process on the worker.

## Job and Batch Naming

Job names, batch names, comments and extra info fields support tokens such as:
- `{script}` - Script name with extension
- `{script_stem}` - Script name without extension
- `{write}` - Write node name
- `{file}` - Output file name (from write node)
- `{range}` - Frame range
- `{batch}` - Batch name (for job names only)

```python
# Custom job and batch naming
submit_nuke_script(
    "path/to/script.nk",
    batch_name="{script_stem}",
    job_name="{batch} | {write}",
    comment="Output={file}",
    extra_info=["Write={write}", "Output={file}"]
)
```

## Write Node Control

You can control which write nodes are rendered and how they're submitted to Deadline:

```python
# Submit specific write nodes
submit_nuke_script("path/to/script.nk", write_nodes=["Write1", "Write2"])

# Submit write nodes as separate jobs
submit_nuke_script("path/to/script.nk", write_nodes_as_separate_jobs=True)

# Submit write nodes as separate tasks
submit_nuke_script("path/to/script.nk", write_nodes_as_tasks=True)

# Set dependencies based on render order
submit_nuke_script("path/to/script.nk", render_order_dependencies=True)
```

## Frame Range Specification

Several formats are available for specifying frame ranges:

```python
# Standard frame ranges
submit_nuke_script("path/to/script.nk", frame_range="1-100")
submit_nuke_script("path/to/script.nk", frame_range="1-100x10")
submit_nuke_script("path/to/script.nk", frame_range="1,10,20-40")

# Special tokens
submit_nuke_script("path/to/script.nk", frame_range="f-l")  # first to last
submit_nuke_script("path/to/script.nk", frame_range="f,m,l")  # first, middle, last
submit_nuke_script("path/to/script.nk", frame_range="i")  # input range from write node
```

## Graph Scope Variables

Graph Scope Variables (GSVs) allow you to set variables for multi-shot or parametric rendering. This is particularly useful for rendering multiple shots or variations from a single Nuke script.

### Understanding Graph Scope Variables

GSVs follow the format `variable_name:value1,value2,...` where:
- `variable_name` is the name of the GSV in your Nuke script
- `value1, value2, ...` are the values to assign to that variable

For complex setups, you can provide multiple GSV definitions as a list.

```python
# Simple usage with a single variable
submit_nuke_script("path/to/script.nk", graph_scope_variables=["shotcode:ABC_0010"])

# Multiple values for a single variable
submit_nuke_script("path/to/script.nk", graph_scope_variables=["shotcode:ABC_0010,ABC_0020"])

# Sets of variables
submit_nuke_script("path/to/script.nk", graph_scope_variables=[
    ["shotcode:ABC_0010,ABC_0020","res:wh,hh"],
    ["shotcode:XYZ_0010,XYZ_0020,XYZ_0030","res:wh"]
])

# Combined with other options
submit_nuke_script(
    "path/to/script.nk",
    frame_range="1001-1100",
    write_nodes=["Write1", "Write2"],
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
)
```

### GSV Example

In your Nuke script, you might have expressions like:
```
[value this.shotcode]
```

```python
from nk2dl import submit_nuke_script

# Basic usage with frame range patterns
submit_nuke_script("path/to/script.nk", frames="1-100")  # Explicit frame range
submit_nuke_script("path/to/script.nk", frames="1-100x10")  # Every 10th frame
submit_nuke_script("path/to/script.nk", frames="1,10,20-40")  # Mixed specification
submit_nuke_script("path/to/script.nk", frames="f-l")  # First to last frame in script
submit_nuke_script("path/to/script.nk", frames="f,m,l")  # First, middle, and last frame
submit_nuke_script("path/to/script.nk", frames="i")  # Input range from write node
```

### Full Example with Multiple Options

```python
job_ids = submit_nuke_script(
    "path/to/script.nk",
    frames="1001-1100",
    job_name="{batch} / {write} / {range}",
    batch_name="Project_ABC",
    write_nodes=["Write1", "Write2", "Write3"],
    priority=75,
    pool="nuke",
    threads=16,
    ram_use=16384,
    stack_size=32768,
    use_node_frame_list=True,
    chunk_size=10,
    concurrent_tasks=5,
    render_order_dependencies=True,
    use_gpu=True,
    copy_script=True,
    environment_keys=["NUKE_PATH", "PATH"],
    environment={"PROJECT_ROOT": "/path/to/project"},
    performance_profiler=True,
    performance_profiler_path="/path/to/profiles"
)
```

## Script Copying

Control how scripts are copied before submission:

```python
# Enable script copying with default paths
submit_nuke_script("path/to/script.nk", copy_script=True)

# Specify custom full path for the copy (directory + filename)
submit_nuke_script(
    "path/to/script.nk",
    copy_script=True,
    copy_script_path="{outdir}/.farm/{scriptname}_{YYYY}-{MM}-{DD}.nk",
    submit_copied_script=True  # Submit the copied script instead of original
)

# Create multiple copies in different locations
submit_nuke_script(
    "path/to/script.nk",
    copy_script=True,
    copy_script_path=[
        "{outdir}/.farm/{scriptname}.nk", 
        "{nkdir}/archive/{scriptname}_{YYYY}-{MM}-{DD}.nk"
    ]
)
```
