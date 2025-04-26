Documentation is auto-generated with claude-3.7 and subject to change, may not be 100% accurate or current.

# Deadline Connection

The `nk2dl` package provides utilities for connecting to Deadline render management systems through both command-line and web service interfaces.

## Connection Types

There are two ways to connect to Deadline:

1. **Command-line interface** - Uses the Deadline command-line tools directly installed on your system
2. **Web service** - Connects to the Deadline Web Service over HTTP/HTTPS

## Configuration

Connection settings can be configured via:

- Configuration files (see [Config Documentation](config.md))
- Environment variables

### Environment Variables for Deadline Connection

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `NK2DL_DEADLINE_USE__WEB__SERVICE` | Use web service instead of command line | `False` |
| `NK2DL_DEADLINE_HOST` | Hostname for Deadline Web Service | `localhost` |
| `NK2DL_DEADLINE_PORT` | Port for Deadline Web Service | `8081` |
| `NK2DL_DEADLINE_SSL` | Enable SSL connection | `False` |
| `NK2DL_DEADLINE_SSL__CERT` | Path to SSL certificate file | `None` |
| `NK2DL_DEADLINE_COMMANDLINE__ON__FAIL` | Fall back to command line if web service fails | `True` |

**Note on double underscores:** Notice that some environment variables contain double underscores (`__`). This is a special convention used in `nk2dl` where single underscores in configuration keys are replaced with double underscores in environment variables. For example, `use_web_service` becomes `USE__WEB__SERVICE`. This allows the configuration system to distinguish between underscores that separate parts of the variable name (prefix, section, key) and underscores that are part of the actual configuration key. See the [Config Documentation](config.md#why-double-underscores) for more details.

## Command-line Connection

The command-line connection requires:

- Deadline Client installed on the system
- `deadlinecommand` executable in your system PATH
- Proper repository configuration

## Web Service Connection

The web service connection requires:

- Deadline Web Service installed and running on a server
- Network access to the web service
- Proper authentication if required

For best performance, it's recommended to use the Deadline Web Service.

## Testing Deadline Connectivity

The `nk2dl` package includes a test script to verify connectivity to your Deadline server.

### Using test_deadline_connection.py

This script tests both command-line and web service connectivity to ensure your Deadline setup is working correctly.

#### Running the Test Script

```bash
# Basic usage
python tests/test_deadline_connection.py

# With virtual environment
./.venv/Scripts/python tests/test_deadline_connection.py
```

#### Environment Setup for Testing

Set these environment variables before running the test:

```bash
# Windows PowerShell
$env:PYTHONPATH = "C:\path\to\nk2dl"  # Location of the nk2dl package
$env:DEADLINE_PATH = "C:\Program Files\Thinkbox\Deadline10\bin"  # Deadline installation directory

# Linux/macOS
export PYTHONPATH=/path/to/nk2dl
export DEADLINE_PATH=/path/to/deadline/bin
```

#### Testing Web Service Connection

To test web service connectivity:

```bash
# Windows PowerShell
$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "deadline-server"
$env:NK2DL_DEADLINE_PORT = "8081"
$env:NK2DL_DEADLINE_SSL = "False"
python tests/test_deadline_connection.py

# Linux/macOS
export NK2DL_DEADLINE_USE__WEB__SERVICE=True
export NK2DL_DEADLINE_HOST=deadline-server
export NK2DL_DEADLINE_PORT=8081
export NK2DL_DEADLINE_SSL=False
python tests/test_deadline_connection.py
```

#### Testing with SSL Enabled

> [!WARNING]
> SSL support appears to be currently broken

For secure connections with SSL:

```bash
# Windows PowerShell
$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "deadline-server"
$env:NK2DL_DEADLINE_PORT = "4434"  # Typical SSL port
$env:NK2DL_DEADLINE_SSL = "True"
$env:NK2DL_DEADLINE_SSL__CERT = "C:\path\to\certificate.pxf"
python tests/test_deadline_connection.py

# Linux/macOS
export NK2DL_DEADLINE_USE__WEB__SERVICE=True
export NK2DL_DEADLINE_HOST=deadline-server
export NK2DL_DEADLINE_PORT=4434
export NK2DL_DEADLINE_SSL=True
export NK2DL_DEADLINE_SSL__CERT=/path/to/certificate.pxf
python tests/test_deadline_connection.py
```

### Test Results

The test script will:

1. Test command-line connectivity
2. Test web service connectivity
3. Retrieve available render groups
4. Submit a test job to verify submission works

If all tests pass, the script will exit with code 0. If any test fails, it will exit with code 1.

## Using DeadlineConnection in Code

```python
from nk2dl.deadline.connection import DeadlineConnection
from nk2dl.common.errors import DeadlineError

try:
    # Create connection (uses configuration from config files/environment)
    conn = DeadlineConnection()
    
    # Ensure connection is established
    conn.ensure_connected()
    
    # Get available groups
    groups = conn.get_groups()
    print(f"Available groups: {groups}")
    
    # Submit a job
    job_info = {
        'BatchName': 'Test Batch',
        'Name': 'Test Job',
        'Plugin': 'Python',
        # ... other job parameters
    }
    
    plugin_info = {
        'Version': '3.7',
        # ... plugin-specific parameters
    }
    
    job_id = conn.submit_job(job_info, plugin_info)
    print(f"Submitted job with ID: {job_id}")
    
except DeadlineError as e:
    print(f"Deadline error: {e}") 