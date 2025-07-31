# Installation

## System Requirements
- **Operating System**: Windows 10 (currently tested only on Windows; Testing Linux and MacOS support planned. Linux and MacOS may already work)
- **Nuke**: Compatible with Nuke 13+ (Nuke 15.2+ required for Graph Scope Variables)
- **Deadline**: Thinkbox Deadline 10+ with Repository access
- **Python Version**: Python 3.7+
- **Python Dependencies**: YAML, Deadline API (these are installed into the virtual environment)

## 1. Download

`nk2dl` can be downloaded from [source](#download-from-source) or from a [point release](#download-from-release).

### Download from source 
From the shell:
```bash
git clone https://github.com/artandmath/nk2dl.git
cd nk2dl
```
### Download from release
- Alternatively `nk2dl` can be installed from a release.
- [Download the source code from a release](https://github.com/artandmath/nk2dl/releases). 
- Unzip the source code.

From the shell:
```
cd /path/to/nk2dl-0.1.x-alpha
```

## 2. Install dependencies

Create the virtual environment will also install the dependencies:
```bash
python setup_environment.py
```
The setup script will ask for a Nuke location. The Nuke location contains the python interpreter that will be used in the virtual environment.
```
Nuke installation path not set.
Default path: C:\Program Files\Nuke15.2v1
Enter Nuke installation path (press Enter to use default):
```
The setup script may ask for the Deadline repository location if it cannot automatically find the repository.  The script will copy the Deadline API from the repository to the virtual environment.
```
Deadline repository root not found automatically.
Default path: C:\DeadlineRepository10
Enter Deadline repository root path (press Enter to use default):
```

## 3. Verify
Set the virtual environment (only powershell tested thus far).
```bash
# Windows
./.venv/Scripts/Activate-nk2dl.ps1

# Linux/MacOSX
source ./.venv/Scripts/activate
```
A success message will output to the terminal:
```bash
Activating NK2DL development environment...
Setting up NK2DL environment variables...
Environment activated and ready!
```
Open a python interpreter from the terminal. The python interpreter should indicate that the Foundry's Nuke version of python is in use.
```bash
> python
Python 3.10.10 (remotes/origin/foundry/v3.10.10:693bcebd65, Feb  7 2024, 11:52:25) [MSC v.1935 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```
If the python interpreter is not the version by the Foundry, launch Nuke in terminal mode, which is essentially the same as launching the Nuke python interpreter.
```bash
# Windows:
& 'C:\Program Files\Nuke15.1v1\Nuke15.1.exe' --t
```
Import the `nk2dl` module. A copyright message for `nk2dl` will display and Nuke will load.
```python
>>> import nk2dl
 
Nuke to Deadline (nk2dl) v0.1.0
Copyright (c) 2025 Daniel Harkness. All Rights Reserved.
```

## 4. Install for a single user or multiple users in Nuke

If `nk2dl` will be used in the Nuke application, then Nuke will need to be able find `nk2dl` and its dependencies during the application launch process.

### Install for single user (.nuke method)

- Copy the folder `nk2dl` from `src` into the user's `.nuke` folder.
- Copy the folders `yaml` and `Deadline` from `.venv/Lib/site-packages` into the user's `.nuke` folder
- The `.nuke` folder will contain the following structure

```bash
~/.nuke/
 ├─ Deadline/
 ├─ nk2dl/
 ├─ yaml/
 ├─ init.py
 ├─ menu.py
 │
etc
```

### Install for multiple users (init.py method)

- Copy the `nk2dl` folder to a location available to all users.
- If necessary, add the location to an init.py file available to Nuke during the launch of your pipeline:

```python
# Use nuke.pluginAddPath()
nuke.pluginAddPath('/path/to/parent/folder/containing/nk2dl')

# Or append/insert to sys.path
import sys
sys.path.insert(0, '/path/to/parent/folder/containing/nk2dl')
```
- The python modules `yaml` and `Deadline` must be available in nk2dl.
- If they are not already available in the pipeline, copy `yaml` and `Deadline` from `.venv/Lib/site-packages` to a location that is available to `sys.path`.

## 5. Install the Deadline Plugin for Nuke 15.2+ (optional)

- To use Graph Scope Variables with Nuke 15.2+, a modified version of the deadline plugin is required.
- Make a backup of `/path/to/your/deadline/repository/plugins/nuke`.
- Replace the contents of `/path/to/your/deadline/repository/plugins/nuke` with the contents of `/path/to/nk2dl/src/deadline_plugins/nuke`.

## 6. Install Deadline Web Service (optional)

![I feel the need, the need for speed!](./img/nk2dl_vs_default.gif)

For best performance, an instance of a Deadline Web Service is recommended. Instructions on setting up a Deadline Web Service can be found via the Deadline documentation:
- [How to install Deadline Web Service](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/install-client-web-server-installation.html)
- [Deadline Web Service Manual](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/web-service.html)
 
After setting up an instance of Deadline Web Service, [configure](./config.md) and [test the connection](./deadline_connection.md) to the Deadline Web Service.

# Configuration

> [!IMPORTANT]
> Configuration is recommended, but not required.

nk2dl uses a YAML configuration system with multiple levels of precedence (`~/.nk2dl/config.yaml` has the highest precedence):

1. Default configuration hard coded into the system.
2. Facility level configuraton via `config.yaml` in the `nk2dl` module.
2. Project/facility level configuration via `$NK2DL_CONFIG`.
3. Project/facility level configuration via environment variables (`$NK2DL_*`)
4. User configuration (`~/.nuke/nk2dl/config.yaml`)

In the case of a single user install in the user's `.nuke` folder, level 2 and level 5 may be the same file. If using `$NK2DL_*` environment variables or the `NK2DL_CONFIG` that points to a config, file remove the `config.yaml` from the `nk2dl` folder in the `.nuke` firectory to avoid this file taking precedence over the environemnt variables.

## Setting the config

- Copy the example `config.yaml` from the `nk2dl` module to a location available to all users.
- Edit the config file. The config file can be renamed.
- Create an environment variable `NK2DL_CONFIG` and point it to the location of `your_config_name.yaml`

Alternatively:

- Edit the `config.yaml` file in the `nk2dl` module directory
- The `config.yaml` in the `nk2dl` cannot be renamed, otherwise the configuration will not be read by the `nk2dl` pyhton module.

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
- Run the `tests/test_nk2dl.py` python script to submit the example nukescripts to Deadline.

```bash
cd /path/to/downloaded/nk2dl-repository/
./.venv/Scripts/Activate-nk2dl.ps1
python ./tests/test_nk2dl.py
``` 
- Test jobs should appear in the Deadline monitor after running `tests/test_nk2dl.py`.

## Script Copy functions
- The example nukescripts use relative paths. If your Deadline is set to remap paths, then relative pathing can break if the project root is derived from the script location.
- `nk2dl` has a feature that will create a backup copy(s) of the submitted script. `nk2dl` will resolve the project root on the copy(s) before submission and can submit the resolved copy.
- The example python script includes a demonstration of how to use the script copy features. 
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