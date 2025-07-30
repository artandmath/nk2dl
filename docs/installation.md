# Installation

## System Requirements
- **Operating System**: Windows 10 (currently tested only on Windows; Linux and MacOS support planned)
- **Nuke**: Compatible with Nuke 13+ (required for Graph Scope Variables: Nuke 15.2+)
- **Deadline**: Thinkbox Deadline 10+ with Repository access
- **Python**: Python 3.7+ 

## 1. Install from source or release

`nk2dl` can be installed from [source](#install-from-source) or from a [point release](#install-from-release).

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
## 2. Install for a single user or multiple users in Nuke

If `nk2dl` will be used in Nuke then Nuke will need to find `nk2dl` during the application launch process.

### Install for Nuke GUI, single user (.nuke method)

- Copy the folder `nk2dl` into the user's `.nuke` folder. If installed from source, the `nk2dl` folder is the one inside the parent `nk2dl` folder that contains this README.md and LICENSE.
- Copy the folder `yaml` from `.venv/Lib/site-packages` into the user's `.nuke` folder

### Install for Nuke GUI, multiple users (init.py method)

- Copy the `nk2dl` folder to a location available to all users.
- If necessary, add the following line to any of the init.py files available to nuke during the launch of your pipleine:
```python
nuke.pluginAddPath('/path/to/parent/folder/containing/nk2dl')
```
- The python module `yaml` must be available in nk2dl. If it is not installed in your pipeline, copy it from `.venv/Lib/site-packages` into the same parent folder that contains `nk2dl`

## 3. Install the Deadline Plugin for Nuke 15.2+ (optional)

- To use Graph Scope Variables with Nuke 15.2+, a modified version of the deadline plugin is required.
- Make a backup of `/path/to/your/deadline/repository/plugins/nuke`.
- Replace the contents of `/path/to/your/deadline/repository/plugins/nuke` with the contents of `/path/to/nk2dl/src/deadline_plugins/nuke`.

## 4. Install Deadline Web Service (optional)

![I feel the need, the need for speed!](./img/nk2dl_vs_default.gif)

For best performance, an instance of a Deadline Web Service is recommended. Instructions on setting up a Deadline Web Service are found via the Deadline documentation:
- [How to install Deadline Web Service](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/install-client-web-server-installation.html)
- [Deadline Web Service Manual](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/web-service.html)
 
After setting up an instance of Deadline Web Service, [configure](./config.md) and [test the connection.](./deadline_connection.md)

# Configuration

nk2dl uses a YAML configuration system with multiple levels:

1. Default configuration
2. Project configuration (from $NK2DL_CONFIG or config.yaml in nk2dl module)
3. Environment variables ($NK2DL_*)
4. User configuration (~/.nk2dl/config.yaml)

## Configuring for single user (.nuke method)

- Edit the `config.yaml` file in the `nk2dl` module directory
- OR create a configuration file and set the `NK2DL_CONFIG` environment variable to point to it

## Configuring for multiple users

- Create a `your_config_name.yaml` in a location available to all users
- Add configuration to the file in yaml syntax
- Create an environment variable `NK2DL_CONFIG` and point it to the location of `your_config_name.yaml`

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
  extra_info_templates:
    - "Write: {write}"
    - "Order: {render_order}"
    - "Frames: {range}"
    - "Output: {file}"
    # - "GSVs: {gsvs}"
```

# Usage example

- The `tests/nukescripts` folder contains 2 simple nukescripts.
  - an example nukescript for Nuke without GSVs.
  - an example nukescript for Nuke 15.2+ using GSVs to demo multishot output.
- Run the `tests/test_nk2dl.py` python script to submit the example nukescripts to Deadline

```bash
cd /path/to/nk2dl-0.1.x-alpha/
./.venv/Scripts/Activate-nk2dl.ps1
python ./tests/test_nk2dl.py
``` 
## Script Copy functions
- The example nukescripts use relative paths. If your Deadline is set to remap paths, then relative pathing can break if the project root is derived from the script location.
- `nk2dl` has a feature that will create a backup copy(s) of the submitted script. `nk2dl` will resolve the project root on the copy(s) before submission and can submit the resolved copy.
- The example python script includes a demonstation of how to use the script copy features. 
- To set up script copying, you can:
  - Use the `copy_script_path` parameter directly in the function call (full path with directory and filename)
  - Or use one of the following config options:

### Direct parameter usage example
```python
submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,
    copy_script_path="{outdir}/farm/{nkstem}_{YYYY}-{MM}-{DD}.nk"
)

# For multiple copies, provide lists:
submit_nuke_script(
    "/path/to/script.nk",
    copy_script=True,
    copy_script_path=[
        "{outdir}/.farm/{scriptname}", 
        "{nkdir}/archive/{nkstem}_{YYYY}-{MM}-{DD}.nk"
    ]
)
```

### Script copy config example - one copy of submitted nukescript
```yaml
submission:
  # Full path template including directory and filename
  # Available tokens: {nkdir}, {nkstem}, {output}, {YYYY}, etc.
  script_copy_path: '{outdir}/.farm/{nkstem}.nk'  
```

### Available tokens for script_copy_path
- Script directory tokens: `{nkdir}`, `{scriptdir}`, `{nukescriptdir}`
- Script stem tokens: `{nkstem}`, `{scriptstem}`, `{nukescriptstem}`
- Script name tokens: `{nk}`, `{script}`, `{scriptname}`, `{nukescript}`
- Output directory tokens: `{outdir}`, `{outputdir}`
- Output stem tokens: `{filestem}`, `{filenamestem}`, `{outstem}`, `{outputstem}`
- Output tokens: `{output}`
- Date tokens: `{YYYY}` (year), `{YY}` (2-digit year), `{MM}` (month), `{DD}` (day), `{hh}` (hour), `{mm}` (minute), `{ss}` (second)
- Temp directory tokens: `{tmp}`, `{temp}`, `{tmpdir}`, `{tempdir}`
- UUID token: `{uuid}`

### Script copy config example - many copies of submitted nukescript

```yaml
submission:
  script_copy0_path: '{outdir}/.farm/{nukescript}'
  script_copy1_path: '{nkdir}/archive/{basename}_{YYYY}-{MM}-{DD}_{hh}-{mm}-{ss}.nk'
  #script_copy2_path: etc
```