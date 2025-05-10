# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline.

## Overview

The Nuke to Deadline toolset consists of 3 parts:
- `nk2dl python` module for submitting nukescripts to Deadline from the python interpreter within Nuke or from any other python interpreter.
- `nk2dl cli` for submitting nukescripts to Deadline from the console.
- `nk2dl gui` is a panel for submitting the currently open nukescript (features still in planning phase, likely to also include nodes to support panel features)

## Caveats

- The project is in alpha. We have been using it in a limited capacity in a production environment as a replacement for the default submitter. We fall back to the default submitter when missing a feature or something is broken.
- Graph Scope Variable functionality hasn't been tested in production.
- Interfaces to `nk2dl python` module and command line are subject to change.
- The `nk2dl cli` command line will often be out of step with the python module during development. It may outright not work when out of step.
- The project has only been tested under Windows 11. Linux will be tested at a later date. MacOS at an even later date.
- The project aims to have feature parity with the default Deadline submitter on top of `nk2dl`'s other features. At this point in time there are parity features missing.
- The project has no plans to implement Deadline draft.
- Standard Writes only, DeepWrites and other kinds of write nodes to come.
- nk2dl pulls a Nuke interactive license if it needs to call on the Nuke python module.
- Connection to Deadline Web Service currently doesn't support SSL.
- The [roadmap](./roadmap.md) sets out the path to overcome the caveats and implememnt planned features.
- [The project is written using 10% supervision and 90% vibes.](https://www.youtube.com/watch?v=IACHfKmZMr8)

## Installation

### Install from source 
In a Windows powershell:
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

# Install the commandline within the virtual environment (optional)
pip install -e .
```

### Install from release
- Alternatively `nk2dl` can be installed from a release.
- Releases can be found in the sidebar on the github repositiory page.
- Download the source code from a release. 
- Unzip the source code.

In a Windows powershell:
```
# Install from release
cd /path/to/nk2dl-0.1.x-alpha

# Create virtual environment
python ./scripts/setup_environment

# The setup script will ask for a Nuke location
# This is the Nuke python interpreter that will be used in the virtual environment

# The setup script will ask for the Deadline repository location
# The script will copy the Deadline api from the repository to the virtual environment

# Set the virtual environment (only powershell tested thus far)
./.venv/Scripts/Activate-nk2dl.ps1

# Install the commandline within the virtual environment (optional)
pip install -e .
```

### Install for Nuke GUI, single user (.nuke method)

- Copy the folder `nkd2l` into the user's `.nuke` folder. If installed from source, the `nk2dl` folder is the one inside the parent `nk2dl` folder that contains this README.md and LICENSE.
- Copy the folder `yaml` from `.venv/Lib/site-packages` into the user's `.nuke` folder

### Install for Nuke GUI, many users (init.py method)

- Copy the `nk2dl` folder to a location available to all users.
- If nessessary, add the following line to any of the init.py files available to nuke during the launch of your pipleine:
```python
nuke.pluginAddPath('/path/to/parent/folder/containing/nk2dl')
```
- The python module `yaml` must be available in nk2dl. If it is not installed in your pipeline, copy it from `.venv/Lib/site-packages` into the same parent folder that contains `nk2dl`

### Install the Deadline Plugin for Nuke 15.2+ (optional)

- To use Graph Scope Variables with Nuke 15.2+, a modified version of the deadline plugin is required.
- Make a backup of `/path/to/deadline/repo/plugins/nuke`.
- Replace the contents of `/path/to/deadline/repo/plugins/nuke` with the contents of `/path/to/nk2dl-repo/deadline/plugins/nuke`.

### Install Deadline Web Service (optional)

![I feel the need, the need for speed!](./docs/img/nk2dl_vs_default.gif)

For best performance, an instance of a Deadline Web Service is recommended. Instructions on setting up a Deadline Web Service are found via the Deadline documentation:
- [How to install Deadline Web Service](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/install-client-web-server-installation.html)
- [Deadline Web Service Manual](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/web-service.html)
 
After setting up an instance of Deadline Web Service, [configure](./docs/config.md) and [test the connection.](./docs/deadline_connection.md)

## Configuration

nk2dl uses a YAML configuration system with multiple levels:

1. Default configuration
2. Project configuration (from $NK2DL_CONFIG or .nk2dl.yaml in project root)
3. Environment variables ($NK2DL_*)
4. User configuration (~/.nk2dl/config.yaml)

### Configuring for single user (.nuke method)

- Create a file with the name `.nk2dl.yaml` in the `.nuke` directory
- Add configuration to the file in yaml syntax.

### Configuring for multiple users.

- Create a `your_config_name.yaml` in a location avaialble to all users.
- Add configuration to the file in yaml syntax.
- Create an environment variable `NL2DL_CONFIG` and point it to the location of `your_config_name.yaml`

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
  job_name_template: "{batch} / {write} / {file)"
  extra_info_templates:
    - "Write: {write}"
    - "Order: {render_order}"
    - "Frames: {range}"
    - "Output: {file}"
    # - "GSVs: {gsvs}"
```

## Usage example

- The `examples` folder contains 2 simple nukescripts and a python script.
  - an example nukescript for Nuke without GSVs.
  - an example nukescript for Nuke 15.2+ using GSVs to demo multishot output.
  - a python script that can be run in the Nuke Python interpeter (or a Python interpereter that can call upon the Nuke module) or the contents of the python script can be pasted into and executed in the Nuke script editor.
- The example nukescripts use relative paths. If your Deadline is set to remap paths, then relative pathing will break.
- `nk2dl` has a feature that will create a backup copy of submitted scripts. `nk2dl` will resolve relative paths before submission.
- To set up script copying, use one of the following config options

### Script copy config example - one copy of submitted nukescript
```yaml
submission:
  # The following are the defaults if no config is provided
  script_copy_path: ./.farm/  # relative to script or output directory
  script_copy_relative_to: OUTPUT  # SCRIPT or OUTPUT
  script_copy_name: $BASENAME.$EXT # Avalable tokens: $BASENAME, $EXT, YYYY, MM, DD, etc.
```
### Script copy config example - many copies of submitted nukescript

```yaml
submission:
  script_copy0_path: ./.farm/
  script_copy0_relative_to: OUTPUT
  script_copy0_name: $BASENAME.$EXT
  
  script_copy1_path: ./archive/
  script_copy1_relative_to: SCRIPT
  script_copy1_name: $BASENAME_YYYY-MM-DD_hh-mm-ss.$EXT

  #script_copy2_path: etc
```

- Run the `test_nk2dl.py` python script to submit the example nukescripts to Deadline

```bash
cd /path/to/nk2dl-0.1.x-alpha/
./.venv/Scripts/Activate-nk2dl.ps1
python ./examples/test_nk2dl.py
```

## Quick Start

### Python

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
    batch_name="{scriptname}",
    job_name="{batchname}_{write}"
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

## Advanced Options

### Job and Batch Naming

Job names, batch names, comments and extra info fields support tokens such as:
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
    frame_range="1001-1100",
    write_nodes=["Write1", "Write2"],
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
)
```

## License

[MIT License](./LICENSE)

## Contributing

[Guidelines for contributing to the project](./docs/contributing.md)
