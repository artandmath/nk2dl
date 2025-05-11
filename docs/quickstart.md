# Quickstart Usage Guide 

This guide provides a quick overview of how to use nk2dl to submit Nuke scripts to Deadline. For detailed installation and configuration, refer to the [Installation Guide](./installation.md).

## Table of Contents
- [Python API Usage](#python)
- [Command Line Interface](#command-line-interface)
- [Advanced Options](#advanced-options)
  - [Environment Variables](#environment-variables)
  - [Job and Batch Naming](#job-and-batch-naming)
  - [Write Node Control](#write-node-control)
  - [Frame Range Specification](#frame-range-specification)
  - [Graph Scope Variables](#graph-scope-variables)
- [Troubleshooting Tips](#troubleshooting-tips)

## Python

```python
from nk2dl.nuke import submit_nuke_script

# Basic usage
job_ids = submit_nuke_script("/path/to/script.nk")

# Advanced usage with options
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    frame_range="1001-1100",
    priority=40,
    concurrent_tasks=4,
    render_threads=4,
    write_nodes=["Write1", "Write2"],
    batch_name="{script_stem}",
    job_name="{batch}_{write}"
)
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

When using GSVs, Deadline will render multiple versions of the script, each with a different value for `shotcode`.

## Troubleshooting Tips

### Common Issues

1. **No write nodes found**: Ensure your Nuke script contains at least one write node that's not disabled.

2. **Path remapping issues**: If using relative paths in Nuke scripts with Deadline path remapping, use the script copy feature to create versions with resolved paths.

3. **Permission denied**: Ensure the Deadline worker has access to all necessary file paths, including input files and output directories.

4. **Missing environment variables**: Check that required environment variables are being passed to Deadline using the environment options.

5. **GSV errors**: For Graph Scope Variables, ensure Nuke 15.2+ is used with the patched Deadline plugin.

### Debugging Strategies

1. **Check job logs**: In Deadline Monitor, view the job's detailed task logs for error messages.

2. **Test locally**: Run the same render locally in Nuke to see if the issue is with the script or with Deadline.

3. **Script permission issues**: Make sure your submission environment has the necessary permissions to read the script and write to output directories.

4. **Deadline connection issues**: Use the [Deadline Connection](./deadline_connection.md) guide to verify connectivity to Deadline. 