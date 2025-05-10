> [!NOTE]
> Documentation is auto-generated with claude-3.7, may not be current or accurate and is subject to change.

# nk2dl Configuration

The `nk2dl` package uses a multi-level configuration system that allows for flexible settings at different levels of scope.

## Configuration Hierarchy

Configuration values are loaded and overridden in the following order (later sources override earlier ones):

1. **Default configuration** - Baseline values built into the package
2. **Project configuration** - `.nk2dl.yaml` in the project directory
3. **Environment variables** - `NK2DL_*` variables
4. **User configuration** - `~/.nk2dl/config.yaml` in the user's home directory

## Configuration File Format

Configuration files use YAML format:

```yaml
deadline:
  use_web_service: true
  host: deadline-server
  port: 8081
  ssl: false
  commandline_on_fail: true

logging:
  level: INFO
  file: null
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

submission:
  pool: nuke
  group: none
  priority: 50
  chunk_size: 10
  department: comp
  batch_name_template: "{script_stem}"
  job_name_template: "{batch} / {write} / {file}"
```

## Available Configuration Sections

### Deadline Connection

```yaml
deadline:
  # Whether to use Deadline Web Service (vs command line)
  use_web_service: true
  
  # Deadline Web Service host
  host: deadline-server
  
  # Deadline Web Service port
  port: 8081
  
  # Whether to use SSL for the web service connection
  ssl: false
  
  # Path to SSL certificate file (required if ssl is true)
  ssl_cert: null
  
  # Fall back to command line if web service fails
  commandline_on_fail: true
```

### Logging

```yaml
logging:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: INFO
  
  # Log file path (null for no file logging)
  file: null
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Job Submission

```yaml
submission:
  # Deadline pool
  pool: nuke
  
  # Deadline group
  group: none
  
  # Job priority (0-100)
  priority: 50
  
  # Frame chunk size
  chunk_size: 10
  
  # Department name
  department: comp
  
  # Template for batch names
  batch_name_template: "{script_stem}"
  
  # Template for job names
  job_name_template: "{batch} / {write} / {file}"
  
  # Whether to submit write nodes as separate jobs
  write_nodes_as_separate_jobs: false
  
  # Whether to submit write nodes as tasks
  write_nodes_as_tasks: false
  
  # Whether to create dependencies based on render order
  render_order_dependencies: false
  
  # Default number of render threads
  render_threads: 0
  
  # Whether to use GPU by default
  use_gpu: false
  
  # Whether to use NukeX by default
  use_nuke_x: false
  
  # Whether to use Nuke Studio by default
  use_nuke_studio: false
  
  # Script copying options
  copy_script: false
  submit_copied_script: false
  
  # Script copy path (relative to script or output directory)
  script_copy_path: ./.farm/
  script_copy_relative_to: OUTPUT  # Can be SCRIPT or OUTPUT
  script_copy_name: $BASENAME.$EXT  # Can use tokens: $BASENAME, $EXT, YYYY, MM, DD, etc.
  
  # Multiple copy locations (optional)
  script_copy0_path: ./.farm/
  script_copy0_relative_to: OUTPUT
  script_copy0_name: $BASENAME.$EXT
  
  script_copy1_path: ./archive/
  script_copy1_relative_to: SCRIPT
  script_copy1_name: $BASENAME.YYYY-MM-DD_hh-mm-ss.$EXT
```

### Nuke Settings

```yaml
nuke:
  # Default version to use (null for auto-detect)
  version: null
  
  # Path to Nuke executable (null for auto-detect)
  executable: null
```

## Environment Variables

All configuration settings can be overridden with environment variables using the format `NK2DL_SECTION_KEY`:

```bash
# Windows PowerShell
$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "deadline-server"
$env:NK2DL_SUBMISSION_PRIORITY = "75"
$env:NK2DL_LOGGING_LEVEL = "DEBUG"

# Linux/macOS
export NK2DL_DEADLINE_USE__WEB__SERVICE=True
export NK2DL_DEADLINE_HOST=deadline-server
export NK2DL_SUBMISSION_PRIORITY=75
export NK2DL_LOGGING_LEVEL=DEBUG
```

Note that:
- Section and key are separated by single underscores (`_`)
- For keys containing underscores, use double underscores (`__`) in the environment variable
- Boolean values should be `True` or `False` (case-sensitive)

Examples:
- `deadline.use_web_service` → `NK2DL_DEADLINE_USE__WEB__SERVICE`
- `submission.chunk_size` → `NK2DL_SUBMISSION_CHUNK__SIZE`

### Why Double Underscores?

The double underscore convention is necessary because environment variables use underscores to separate the prefix (`NK2DL`), section (`DEADLINE`), and key name. Since some configuration keys also contain underscores (like `use_web_service`), we need a way to distinguish between:

1. The underscores that separate parts of the environment variable name
2. The underscores that are part of the original configuration key

By replacing underscores in configuration keys with double underscores in environment variables, the configuration system can correctly parse the variable names back into their proper configuration paths. When processed, the double underscores are converted back to single underscores.

## Project Configuration

Create a `.nk2dl.yaml` file in your project directory to set project-specific defaults:

```yaml
submission:
  pool: nuke
  group: workstations
  priority: 50
  department: compositing
  batch_name_template: "{scriptname}"
```

## User Configuration

Create a `config.yaml` file in `~/.nk2dl/` to set user-specific defaults:

```yaml
deadline:
  host: my-deadline-server
  port: 8081

logging:
  level: INFO
  file: "~/nk2dl_logs/nk2dl.log"
```

## Templating

Templates for batch and job names support the following variables:

| Variable | Description |
|----------|-------------|
| `{script}` | Script name with extension |
| `{script_stem}` | Script name without extension |
| `{write}` | Write node name |
| `{file}` | Output file name (from write node) |
| `{range}` | Frame range |
| `{batch}` | Batch name (for job names only) |

Example:
```yaml
submission:
  batch_name_template: "Project_{script_stem}"
  job_name_template: "{batch} / {write} / {range}"
``` 
