# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline.

## Overview

The Nuke to Deadline toolset consists of 3 parts:
- `nk2dl python` module for submitting nukescripts to Deadline from the python interpreter within Nuke or from any other python interpreter.
- `nk2dl cli` for submitting nukescripts to Deadline from the console.
- `nk2dl nuke` is a panel for submitting the currently open nukescript (features still in planning phase, likely to also include nodes to support panel features)

## Caveats

The project is still under development
- The project is in alpha. We have been using it in a limited capacity in a production environemnt as a replacement for the default submitter. We fall back to the default submitter when missing a feature or something is broken.
- Graph Scope Variable functionality hasn't been tested in production.
- Interfaces to `nk2dl` module and command line are subject to change.
- The `nk2dl` command line will often be out of step with the python module during development. It may outright not work when out of step.
- The project has only been tested under Windows 11. Linux will be tested at a later date. MacOS at an even later date.
- The project aims to have feature parity with the default Deadline submitter on top of `nk2dl`'s other features. At this point in time there are parity features missing.
- The project has no plans to implement Deadline draft.
- Standard Writes only, DeepWrites and other kinds of write nodes to come.
- Connection to Deadline Web Service currently doesn't support SSL.
- [The project is written using 10% supervision and 90% vibes.](https://www.youtube.com/watch?v=IACHfKmZMr8) Use at your own risk!

## Installation

```bash
# Install from source
git clone https://github.com/artandmath/nk2dl.git
cd nk2dl

# Create virtual environment
python ./scripts/setup_environment

# The setup script will ask for a Nuke location
# This is the Nuke python interpreter that will be used in the virtual environment

# The setup script will ask for the Deadline repository location
# The script will copy the Deadline api from the repository to the virtual environment

# Set the virtual environment (only powershell tested thus far)
./.venv/Scripts/Activate-nk2dl.ps1

# Install the commandline within the virtual environment
pip install -e .
```
To make nk2dl available to Nuke GUI, add the path to nk2dl in an init.py. Development and testing is still being done outside of the Nuke GUI, no additional information for Nuke GUI can be offered at this stage.

To use Graph Scope Variables with Nuke 15.2+, copy or diff the content of deadline/plugins/nuke to the same location on your Deadline repository. Be sure to create a backup of your existing Nuke plugin.


## Deadline Web Service

![I feel the need, the need for speed!](./docs/img/nk2dl_vs_default.gif)

For best performance an instance of a Deadline Web Service is recommended.
- [How to install Deadline Web Service](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/install-client-web-server-installation.html)
- [Deadline Web Service Manual](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/web-service.html)
 
After setting up an instance of Deadline Web Service, check the docs on how to [configure](./docs/config.md) and [test the connection.](./docs/deadline_connection.md)


## Quick Start

### Python API

```python
from nk2dl.nuke import submit_nuke_script

# Basic usage
job_ids = submit_nuke_script("/path/to/script.nk")

# Advanced usage with options
job_ids = submit_nuke_script(
    "/path/to/script.nk",
    frame_range="1-100",
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True,
    write_nodes=["Write1", "Write2"],
    job_name="{script_stem}_{write}",
    batch_name="Project_123"
)
```

### Command Line Interface

```bash
# Help docs
nk2dl submit --help

# Basic submission
nk2dl submit /path/to/script.nk

# With options
nk2dl submit /path/to/script.nk --frame-range 1-100 --priority 75 --use-nuke-x --render-threads 16 --use-gpu
```

## Configuration

nk2dl uses a YAML configuration system with multiple levels:

1. Default configuration
2. Project configuration (from NK2DL_CONFIG envvar or .nk2dl.yaml in project root))
3. Environment variables (NK2DL_*)
4. User configuration (~/.nk2dl/config.yaml)

Example configuration:

```yaml
deadline:
  use_web_service: True
  host: deadline-web-server
  port: 8081
  ssl: False
  commandline_on_fail: True

logging:
  level: DEBUG
  file: null
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

submission:
  pool: nuke
  group: none
  priority: 50
  chunk_size: 10
  department: comp
  batch_name_template: "{scriptname}"
  job_name_template: "{batch} / {write} / {file}"
```

## Advanced Options

### Job and Batch Naming

Templates support tokens such as:
- `{script}` - Script name with extension
- `{script_stem}` - Script name without extension
- `{write}` - Write node name
- `{file}` - Output file name (from write node)
- `{range}` - Frame range
- `{batch}` - Batch name (for job names only)

### Write Node Control

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

### Frame Range Specification

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

### Graph Scope Variables

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
    frame_range="1-100",
    write_nodes=["Write1", "Write2"],
    graph_scope_variables=["shotcode:ABC_0010"]
)
```

## License

[MIT License](./LICENSE)

## Contributing

[Guidelines for contributing to the project](./docs/contributing.md)
