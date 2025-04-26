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

### Job identification options

| Option | Description |
|--------|-------------|
| `--BatchName NAME` | Batch name for the job (default: Nuke script filename) |
| `--JobName NAME` | Job name (default: <nukescript_filename>/<write_nodename>) |
| `--Comment TEXT` | Comment for the job |
| `--Department NAME` | Department for the job |

### Priority and pool options

| Option | Description |
|--------|-------------|
| `--Pool NAME` | Worker pool to use |
| `--Group NAME` | Worker group to use |
| `--Priority VALUE` | Job priority (0-100, default: 50) |
| `--TaskTimeout MINUTES` | Task timeout in minutes (0 for no timeout) |
| `--AutoTaskTimeout` | Enable automatic task timeout |
| `--ConcurrentTasks COUNT` | Maximum number of concurrent tasks per job (default: 1) |
| `--LimitWorkerTasks` | Limit tasks to one per worker |
| `--MachineLimit COUNT` | Maximum number of machines to use (0 for no limit) |
| `--MachineList LIST` | List of machines to allow or deny (format: allow:machine1,machine2 or deny:machine1,machine2) |
| `--Limits LIST` | Resource limits to use (comma-separated) |

### Dependencies and submission options

| Option | Description |
|--------|-------------|
| `--Dependencies JOB_IDS` | Job IDs this job depends on (comma-separated) |
| `--SubmitJobsAsSuspended` | Submit jobs as suspended |
| `--SubmitNukeScript` | Submit the Nuke script as an auxiliary file |

### Write node options

| Option | Description |
|--------|-------------|
| `--WriteNodes`, `--Writes`, `--Nodes`, `-w`, `-n` | Write nodes to render (comma-separated, default: all) |
| `--WritesAsSeparateJobs` | Submit each write node as a separate job |
| `--WritesAsSeparateTasks` | Submit write nodes as separate tasks for the same job |
| `--NodeFrameRange` | Use frame range from write nodes instead of global frame range |
| `--RenderOrderDependencies` | Set dependencies based on write node render order |

### Frame range options

| Option | Description |
|--------|-------------|
| `--Frames`, `-f` | Frame range to render (Nuke syntax, special tokens: f,l,m,h,i) |
| `--FramesPerTask`, `--TaskSize`, `--ChunkSize`, `--Chunk` | Number of frames per task (default: 1) |

### Nuke options

| Option | Description |
|--------|-------------|
| `--NukeX`, `-nx`, `--UseNukeX` | Use NukeX for rendering |
| `--BatchMode` | Use batch mode |
| `--RenderThreads COUNT` | Number of render threads to use |
| `--Gpu`, `--UseGPU` | Use GPU for rendering |
| `--RAM GB` | Maximum RAM usage in GB |
| `--ContinueOnError` | Continue rendering if an error occurs |
| `--ReloadBetweenTasks`, `--ReloadBetweenChunks` | Reload plugins between tasks |
| `--PerformanceProfiler` | Use performance profiler |
| `--XMLDirectory`, `--XMLDir` | Directory to save performance profile XML files |
| `--Proxy` | Render in proxy mode |
| `--Views VIEWS` | Views to render (comma-separated, default: all) |

### Graph scope variables options

| Option | Description |
|--------|-------------|
| `--Var`, `--Variable`, `--GSV` | Graph scope variables (format: var:value1,value2,var2:value3,value4) |

### Job completion options

| Option | Description |
|--------|-------------|
| `--OnJobComplete` | Action to take when job completes (choices: Nothing, Archive, Delete) |

## Examples

```bash
# Render specific frame range with high priority
nk2dl submit /path/to/script.nk --Frames 1-100 --Priority 75

# Use NukeX with GPU rendering and specific write nodes
nk2dl submit /path/to/script.nk --NukeX --Gpu --WriteNodes Write1,Write2

# Specify graph scope variables
nk2dl submit /path/to/script.nk --Var "shotcode:ABC_0010,ABC_0020"

# Full example with multiple options
nk2dl submit /path/to/script.nk \
    --Frames 1-100 \
    --Priority 75 \
    --NukeX \
    --RenderThreads 16 \
    --Gpu \
    --WriteNodes Write1,Write2 \
    --JobName "{script_stem}_{write}" \
    --BatchName "Project_123" \
    --Department comp \
    --Pool nuke \
    --Group farm \
    --FramesPerTask 10
```

## Environment Variables

The CLI respects the same environment variables and configuration files as the Python API. See the [Configuration documentation](config.md) for details. 