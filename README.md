# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline in a "big studio" manner.

## Overview

nk2dl provides a streamlined, robust way to submit Nuke render jobs to Deadline with extensive customization options. It's built for production environments and supports:

- Write node management (submit all nodes or selected ones)
- Complex frame range specifications
- Granular control over rendering parameters
- Template-based job naming
- Graph scope variable support
- Integration with Nuke's interface

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/nk2dl.git
cd nk2dl
pip install .

# Or install directly with pip (when available)
pip install nk2dl
```

## Quick Start

### Python API

```python
from nk2dl.nuke import submit_nuke_script

# Basic usage
job_id = submit_nuke_script("/path/to/script.nk")

# Advanced usage with options
job_id = submit_nuke_script(
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
# Basic submission
nk2dl submit /path/to/script.nk

# With options
nk2dl submit /path/to/script.nk --frame-range 1-100 --priority 75 --use-nuke-x --render-threads 16 --use-gpu
```

## Key Features

- **Write Node Management**: Submit all or selected write nodes
- **Flexible Frame Ranges**: Support for Nuke-style frame ranges with special tokens (f,l,m,i)
- **Job Organization**: Template-based job and batch naming
- **Advanced Rendering Options**: Control threads, memory, GPU usage
- **Pipeline Integration**: Robust configuration system for studio environments
- **Job Dependencies**: Set up complex job dependency chains

## Configuration

nk2dl uses a YAML configuration system with multiple levels:

1. Default configuration
2. Project configuration (.nk2dl.yaml)
3. User configuration (~/.nk2dl/config.yaml)
4. Environment variables (NK2DL_*)

Example configuration:

```yaml
deadline:
  host: deadline-server
  port: 8081
  
submission:
  pool: nuke
  group: none
  priority: 50
  chunk_size: 10
  department: comp
  job_name_template: "{batch} / {write}"
  batch_name_template: "{script_stem}"
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
submit_nuke_script("script.nk", write_nodes=["Write1", "Write2"])

# Submit write nodes as separate jobs
submit_nuke_script("script.nk", write_nodes_as_separate_jobs=True)

# Submit write nodes as separate tasks
submit_nuke_script("script.nk", write_nodes_as_tasks=True)

# Set dependencies based on render order
submit_nuke_script("script.nk", render_order_dependencies=True)
```

### Frame Range Specification

```python
# Standard frame ranges
submit_nuke_script("script.nk", frame_range="1-100")
submit_nuke_script("script.nk", frame_range="1-100x10")
submit_nuke_script("script.nk", frame_range="1,10,20-40")

# Special tokens
submit_nuke_script("script.nk", frame_range="f-l")  # first to last
submit_nuke_script("script.nk", frame_range="f,m,l")  # first, middle, last
submit_nuke_script("script.nk", frame_range="i")  # input range from write node
```

## License

[Specify your license here]

## Contributing

[Guidelines for contributing to the project]