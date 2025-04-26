> [!NOTE]
> Documentation is auto-generated with claude-3.7, may not be current or accurate and is subject to change.

# nk2dl Command Line Interface

The `nk2dl` command line interface allows you to submit Nuke scripts to Deadline directly from your terminal.

## Installation

The CLI is automatically installed when you install the nk2dl package:

```bash
# Within your virtual environment
pip install -e .
```

## Basic Usage

```bash
# Display help information
nk2dl --help

# Display help for the submit command
nk2dl submit --help

# Submit a Nuke script with default settings
nk2dl submit /path/to/script.nk
```

## Command Options

The `submit` command supports the following options:

| Option | Description |
|--------|-------------|
| `--frame-range TEXT` | Frame range to render (e.g., "1-100", "1-100x10", "f-l") |
| `--priority INTEGER` | Job priority (0-100) |
| `--use-nuke-x` | Use NukeX instead of regular Nuke |
| `--use-nuke-studio` | Use Nuke Studio instead of regular Nuke |
| `--render-threads INTEGER` | Number of render threads to use |
| `--use-gpu` | Enable GPU rendering |
| `--write-nodes TEXT` | Specific write nodes to render (comma-separated) |
| `--job-name TEXT` | Custom job name template |
| `--batch-name TEXT` | Custom batch name |
| `--department TEXT` | Department name |
| `--pool TEXT` | Deadline pool |
| `--group TEXT` | Deadline group |
| `--chunk-size INTEGER` | Frame chunk size |
| `--graph-scope-variables TEXT` | Graph scope variables (format: "var:val1,val2") |

## Examples

```bash
# Render specific frame range with high priority
nk2dl submit /path/to/script.nk --frame-range 1-100 --priority 75

# Use NukeX with GPU rendering and specific write nodes
nk2dl submit /path/to/script.nk --use-nuke-x --use-gpu --write-nodes Write1,Write2

# Specify graph scope variables
nk2dl submit /path/to/script.nk --graph-scope-variables "shotcode:ABC_0010,ABC_0020"

# Full example with multiple options
nk2dl submit /path/to/script.nk \
    --frame-range 1-100 \
    --priority 75 \
    --use-nuke-x \
    --render-threads 16 \
    --use-gpu \
    --write-nodes Write1,Write2 \
    --job-name "{script_stem}_{write}" \
    --batch-name "Project_123" \
    --department comp \
    --pool nuke \
    --group farm \
    --chunk-size 10
```

## Environment Variables

The CLI respects the same environment variables and configuration files as the Python API. See the [Configuration documentation](config.md) for details. 