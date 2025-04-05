# Using Metadata Overrides for Deadline Submission

This document explains how to use metadata on Nuke write nodes to set per-node Deadline submission parameters.

## Overview

The `nk2dl` library supports reading metadata from Nuke write nodes to override default job submission parameters. This allows artists to set specific render settings for individual write nodes directly within Nuke without having to modify submission scripts.

## Adding Metadata to Write Nodes

Metadata keys should follow these patterns:

- For Job Info parameters: `input/deadline/jobInfo/ParameterName`
- For Plugin Info parameters: `input/deadline/pluginInfo/ParameterName`

**Important**: The `ParameterName` portion should exactly match the Deadline parameter names. The system will automatically map these to the corresponding property names in the code, handling the conversion between different naming conventions (camelCase/snake_case).

### Property Name Mapping

The system intelligently maps between different naming conventions:

| Metadata Key | Internal Property |
|-------------|------------------|
| ChunkSize | chunk_size |
| Priority | priority |
| RamUse | ram_usage |
| UseGpu | use_gpu |
| LimitConcurrentTasks | limit_concurrent_tasks |

### Using the Helper Script

The easiest way to add metadata to write nodes is using the helper script provided at `scripts/add_deadline_metadata.py`. This script provides functions for adding, removing, and listing Deadline metadata on write nodes.

To use it:

1. Load the script in the Nuke Script Editor
2. Select the write nodes you want to modify
3. Call one of the provided functions

Example:

```python
# Add ChunkSize=5 to all selected write nodes
add_job_metadata_to_selected("ChunkSize", 5)

# Set render threads to 16 for all selected write nodes
add_plugin_metadata_to_selected("Threads", 16)

# List all Deadline metadata on selected write nodes
list_deadline_metadata_for_selected()

# Remove all Deadline metadata from selected write nodes
remove_all_deadline_metadata_from_selected()
```

### Manually Adding Metadata

You can add metadata directly using Nuke's Python API:

```python
# Select a write node
node = nuke.selectedNode()

# Add JobInfo parameter
node.addMetadata("input/deadline/jobInfo/ChunkSize", "5")

# Add PluginInfo parameter
node.addMetadata("input/deadline/pluginInfo/Threads", "16")
```

## Available Parameters

### JobInfo Parameters

Here are common JobInfo parameters you can override:

| Metadata Key | Description | Example Value |
|--------------|-------------|---------------|
| ChunkSize | Number of frames per task | "10" |
| Priority | Job priority (0-100) | "50" |
| Pool | Deadline pool | "nuke" |
| Group | Deadline group | "render" |
| ConcurrentTasks | Number of concurrent tasks | "1" |
| Frames | Frame range | "1-100" |
| Department | Department name | "Compositing" |
| LimitGroups | Limit groups | "nuke,gpu" |

### PluginInfo Parameters

Here are common PluginInfo parameters you can override:

| Metadata Key | Description | Example Value |
|--------------|-------------|---------------|
| Threads | Number of render threads | "8" |
| RamUse | RAM limit in MB | "16384" |
| UseGpu | Use GPU for rendering | "True" |
| BatchMode | Keep Nuke script loaded between tasks | "True" |
| ContinueOnError | Continue rendering if errors occur | "False" |
| EnforceRenderOrder | Enforce write node render order | "True" |
| StackSize | Minimum stack size in MB | "0" |

## Submitting Jobs with Metadata Support

To enable metadata support when submitting jobs, set the `metadata_overrides` parameter to `True`:

```python
import nuke
from scripts.analyze_and_submit import submit_selected_write_nodes

# Submit with metadata support enabled
job_ids = submit_selected_write_nodes(
    priority=50,
    pool="nuke",
    chunk_size=5,
    threads=8,
    ram_usage=16384,
    use_gpu=True,
    metadata_overrides=True  # Enable metadata overrides
)
```

When `metadata_overrides` is `True`, settings specified in metadata will override the default parameters provided to the function. This allows different write nodes to have different settings in the same submission.

## Example Workflow

A typical workflow might look like:

1. Artists create Nuke scripts with write nodes
2. For write nodes that need special settings, artists add metadata 
3. When submitting to Deadline, the submission process reads the metadata and applies the settings

This creates a flexible system where most write nodes can use standard farm settings, but specific write nodes can use custom settings when needed. 