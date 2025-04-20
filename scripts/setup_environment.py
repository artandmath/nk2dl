#!/usr/bin/env python
"""
nk2dl - Setup Environment Script

This script helps set up the development environment for nk2dl:
1. Creates a virtual environment
2. Installs dependencies from requirements.txt
3. Sets up environment variables (NUKE_PATH, PYTHONPATH)
4. Configures Nuke Python module access
5. Sets up the Deadline Python API

Usage:
    python scripts/setup_environment.py

Requirements:
    - Python 3.11.x
    - virtualenv (or similar tool)
    - Nuke installation (for Python module access)
    - Deadline installation (for API access)
"""

import os
import platform
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional


def get_nuke_install_path():
    """Get Nuke installation path from environment or prompt user."""
    nuke_install_path = os.environ.get("NUKE_INSTALL_PATH", "")
    
    if not nuke_install_path:
        system = platform.system()
        if system == "Windows":
            default_path = "C:\\Program Files\\Nuke15.2v1"
        elif system == "Darwin":  # macOS
            default_path = "/Applications/Nuke15.2/Nuke15.2v1.app/Contents/MacOS/Nuke15.2"
        else:
            default_path = "/opt/Nuke15.2v1/Nuke15.2"
            
        print(f"\nNuke installation path not set.")
        print(f"Default path: {default_path}")
        user_input = input("Enter Nuke installation path (press Enter to use default): ").strip()
        
        if user_input:
            nuke_install_path = user_input
        else:
            nuke_install_path = default_path
            
        print(f"Using Nuke installation path: {nuke_install_path}")
    
    return nuke_install_path


def get_deadline_repository_root():
    """Get the Deadline repository root path from environment or by asking the user."""
    repository_root = os.environ.get('DEADLINE_REPOSITORY_ROOT')
    
    if not repository_root:
        # Try to get it from deadlinecommand if available
        deadline_bin = os.environ.get('DEADLINE_PATH')
        if deadline_bin:
            try:
                cmd = [os.path.join(deadline_bin, 'deadlinecommand'), '-GetRepositoryRoot']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    repository_root = result.stdout.strip()
            except Exception as e:
                print(f"Warning: Failed to get repository root from deadlinecommand: {e}")
    
    if not repository_root:
        print("\nDeadline repository root not found automatically.")
        default_path = "C:\\DeadlineRepository10" if platform.system() == "Windows" else "/opt/Thinkbox/DeadlineRepository10"
        print(f"Default path: {default_path}")
        user_input = input("Enter Deadline repository root path (press Enter to use default): ").strip()
        
        if user_input:
            repository_root = user_input
        else:
            repository_root = default_path
            
        print(f"Using Deadline repository root: {repository_root}")
    
    return repository_root


def find_deadline_api(repository_root: str) -> Optional[Path]:
    """Find the Deadline Python API folder in the repository."""
    # Look for the API folder
    api_path = Path(repository_root) / 'api' / 'python' / 'Deadline'
    if api_path.exists():
        return api_path
    
    return None


def setup_deadline_api(venv_path: str, repository_root: str):
    """Set up the Deadline Python API in the virtual environment."""
    print("Setting up Deadline Python API...")
    
    # Find Deadline API
    api_path = find_deadline_api(repository_root)
    if not api_path:
        print("Could not find Deadline API folder at the specified repository root.")
        print("Please ensure the path is correct.")
        return False
    
    print(f"Found Deadline API at: {api_path}")
    
    # Determine site-packages directory based on the OS
    if platform.system() == "Windows":
        site_packages = Path(venv_path) / "Lib" / "site-packages"
    else:
        site_packages = Path(venv_path) / "lib" / "python3.11" / "site-packages"
    
    # Copy API to site-packages
    dest_path = site_packages / 'Deadline'
    try:
        if dest_path.exists():
            print(f"Removing existing Deadline API from {dest_path}")
            shutil.rmtree(dest_path)
        
        print(f"Copying Deadline API from {api_path} to {dest_path}")
        shutil.copytree(api_path, dest_path)
        print("Deadline Python API successfully installed!")
        return True
    except Exception as e:
        print(f"Error copying API: {e}")
        return False


def create_virtual_environment():
    """Create a virtual environment for development."""
    print("Creating virtual environment...")
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return str(venv_path)
    
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print(f"Virtual environment created at {venv_path}")
        return str(venv_path)
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)


def install_dependencies(venv_path):
    """Install dependencies from requirements.txt."""
    print("Installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("requirements.txt not found. Skipping dependency installation.")
        return
    
    # Determine the pip executable path based on the OS
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    try:
        subprocess.check_call([pip_path, "install", "-r", str(requirements_file)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


def setup_venv_environment_vars(venv_path, nuke_install_path, deadline_repository_root):
    """Set up environment variables in the virtual environment activation scripts."""
    print("Setting up environment variables in virtual environment...")
    
    project_root = Path.cwd()
    
    if platform.system() == "Windows":
        # Modify Windows activation script
        activate_bat = Path(venv_path) / "Scripts" / "activate.bat"
        deactivate_bat = Path(venv_path) / "Scripts" / "deactivate.bat"
        nuke_path = project_root / "nk2dl" 
        python_path = project_root / Path(venv_path) / "Lib" / "site-packages" 
        
        # Create a separate PowerShell script for nk2dl setup
        nk2dl_ps1 = Path(venv_path) / "Scripts" / "nk2dl_setup.ps1"
        with open(nk2dl_ps1, "w") as f:
            f.write("# nk2dl environment variables\n")
            f.write('$script:_OLD_NUKE_PATH = $env:NUKE_PATH\n')
            f.write('$script:_OLD_PYTHONPATH = $env:PYTHONPATH\n')
            f.write('$script:_OLD_NUKE_INSTALL_PATH = $env:NUKE_INSTALL_PATH\n')
            f.write('$script:_OLD_NUKE_INTERACTIVE = $env:NUKE_INTERACTIVE\n')
            f.write('$script:_OLD_DEADLINE_REPOSITORY_ROOT = $env:DEADLINE_REPOSITORY_ROOT\n')
            f.write('$script:_OLD_PATH = $env:PATH\n')
            
            # Set basic environment variables
            f.write(f'$env:NUKE_PATH = "{nuke_path}"\n')
            f.write(f'$env:NUKE_INSTALL_PATH = "{nuke_install_path}"\n')
            f.write(f'$env:DEADLINE_REPOSITORY_ROOT = "{deadline_repository_root}"\n')
            f.write('$env:NUKE_INTERACTIVE = 1\n')
            
            # Set PYTHONPATH without doubling
            f.write('# Set PYTHONPATH without duplication\n')
            f.write(f'$pythonPath = "{python_path}"\n')
            f.write(f'$nukePythonPath = "{nuke_install_path}"\n')
            f.write('if (-not $env:PYTHONPATH) {\n')
            f.write('    $env:PYTHONPATH = "$pythonPath;$nukePythonPath"\n')
            f.write('} else {\n')
            f.write('    if (-not $env:PYTHONPATH.Contains($pythonPath)) {\n')
            f.write('        $env:PYTHONPATH = "$env:PYTHONPATH;$pythonPath"\n')
            f.write('    }\n')
            f.write('    if (-not $env:PYTHONPATH.Contains($nukePythonPath)) {\n')
            f.write('        $env:PYTHONPATH = "$env:PYTHONPATH;$nukePythonPath"\n')
            f.write('    }\n')
            f.write('}\n')
            
            # Add Nuke to the beginning of PATH
            f.write('# Add Nuke to the beginning of PATH without duplication\n')
            f.write(f'$nukePath = "{nuke_install_path}"\n')
            f.write('if (-not $env:PATH.Contains($nukePath)) {\n')
            f.write('    $env:PATH = "$nukePath;$env:PATH"\n')
            f.write('}\n')
            
            # Add deactivation function
            f.write('\n# Function to revert the changes when deactivating\n')
            f.write('function global:_nk2dl_deactivate {\n')
            f.write('    # Revert environment variables\n')
            f.write('    if (Test-Path variable:script:_OLD_NUKE_PATH) {\n')
            f.write('        $env:NUKE_PATH = $script:_OLD_NUKE_PATH\n')
            f.write('        Remove-Variable "_OLD_NUKE_PATH" -Scope script\n')
            f.write('    }\n')
            f.write('    if (Test-Path variable:script:_OLD_PYTHONPATH) {\n')
            f.write('        $env:PYTHONPATH = $script:_OLD_PYTHONPATH\n')
            f.write('        Remove-Variable "_OLD_PYTHONPATH" -Scope script\n')
            f.write('    }\n')
            f.write('    if (Test-Path variable:script:_OLD_NUKE_INSTALL_PATH) {\n')
            f.write('        $env:NUKE_INSTALL_PATH = $script:_OLD_NUKE_INSTALL_PATH\n')
            f.write('        Remove-Variable "_OLD_NUKE_INSTALL_PATH" -Scope script\n')
            f.write('    }\n')
            f.write('    if (Test-Path variable:script:_OLD_NUKE_INTERACTIVE) {\n')
            f.write('        $env:NUKE_INTERACTIVE = $script:_OLD_NUKE_INTERACTIVE\n')
            f.write('        Remove-Variable "_OLD_NUKE_INTERACTIVE" -Scope script\n')
            f.write('    }\n')
            f.write('    if (Test-Path variable:script:_OLD_DEADLINE_REPOSITORY_ROOT) {\n')
            f.write('        $env:DEADLINE_REPOSITORY_ROOT = $script:_OLD_DEADLINE_REPOSITORY_ROOT\n')
            f.write('        Remove-Variable "_OLD_DEADLINE_REPOSITORY_ROOT" -Scope script\n')
            f.write('    }\n')
            f.write('    if (Test-Path variable:script:_OLD_PATH) {\n')
            f.write('        $env:PATH = $script:_OLD_PATH\n')
            f.write('        Remove-Variable "_OLD_PATH" -Scope script\n')
            f.write('    }\n')
            f.write('}\n')
            f.write('\n# Hook deactivation\n')
            f.write('$env:_OLD_VIRTUAL_DEACTIVATE = $function:deactivate\n')
            f.write('function global:deactivate {\n')
            f.write('    # Run the original deactivate function first\n')
            f.write('    if (Test-Path function:_OLD_VIRTUAL_DEACTIVATE) {\n')
            f.write('        & $env:_OLD_VIRTUAL_DEACTIVATE\n')
            f.write('    }\n')
            f.write('    # Run our custom deactivation\n')
            f.write('    _nk2dl_deactivate\n')
            f.write('}\n')
        
        # Add to activate.bat
        with open(activate_bat, "a") as f:
            f.write("\n@REM nk2dl environment variables\n")
            f.write("set _OLD_NUKE_PATH=%NUKE_PATH%\n")
            f.write("set _OLD_PYTHONPATH=%PYTHONPATH%\n")
            f.write("set _OLD_NUKE_INSTALL_PATH=%NUKE_INSTALL_PATH%\n")
            f.write("set _OLD_NUKE_INTERACTIVE=%NUKE_INTERACTIVE%\n")
            f.write("set _OLD_DEADLINE_REPOSITORY_ROOT=%DEADLINE_REPOSITORY_ROOT%\n")
            f.write("set _OLD_PATH=%PATH%\n")
            
            # Basic environment variables
            f.write(f"set NUKE_PATH={nuke_path}\n")
            f.write(f"set NUKE_INSTALL_PATH={nuke_install_path}\n")
            f.write(f"set DEADLINE_REPOSITORY_ROOT={deadline_repository_root}\n")
            f.write("set NUKE_INTERACTIVE=1\n")
            
            # We can't do conditional checks in batch, so just set these
            # Doubling risk exists, but CMD users can manually fix if needed
            f.write(f"set PYTHONPATH=%PYTHONPATH%;{python_path};{nuke_install_path}\n")
            
            # Add Nuke to the beginning of PATH
            f.write(f"set PATH={nuke_install_path};%PATH%\n")

        # Add to deactivate.bat
        with open(deactivate_bat, "a") as f:
            f.write("\n@REM Restore old nk2dl environment variables\n")
            f.write("if defined _OLD_NUKE_PATH set NUKE_PATH=%_OLD_NUKE_PATH%\n")
            f.write("if defined _OLD_PYTHONPATH set PYTHONPATH=%_OLD_PYTHONPATH%\n")
            f.write("if defined _OLD_NUKE_INSTALL_PATH set NUKE_INSTALL_PATH=%_OLD_NUKE_INSTALL_PATH%\n")
            f.write("if defined _OLD_NUKE_INTERACTIVE set NUKE_INTERACTIVE=%_OLD_NUKE_INTERACTIVE%\n")
            f.write("if defined _OLD_DEADLINE_REPOSITORY_ROOT set DEADLINE_REPOSITORY_ROOT=%_OLD_DEADLINE_REPOSITORY_ROOT%\n")
            f.write("if defined _OLD_PATH set PATH=%_OLD_PATH%\n")
            f.write("set _OLD_NUKE_PATH=\n")
            f.write("set _OLD_PYTHONPATH=\n")
            f.write("set _OLD_NUKE_INSTALL_PATH=\n")
            f.write("set _OLD_NUKE_INTERACTIVE=\n")
            f.write("set _OLD_DEADLINE_REPOSITORY_ROOT=\n")
            f.write("set _OLD_PATH=\n")
    else:
        # Modify Unix/Linux/Mac activation script
        activate_sh = Path(venv_path) / "bin" / "activate"
        nuke_path = project_root / "nk2dl"
        python_path = project_root / Path(venv_path) / "lib" / "python3.11" / "site-packages"
        
        with open(activate_sh, "a") as f:
            f.write("\n# nk2dl environment variables\n")
            f.write('_OLD_NUKE_PATH="$NUKE_PATH"\n')
            f.write('_OLD_PYTHONPATH="$PYTHONPATH"\n')
            f.write('_OLD_NUKE_INSTALL_PATH="$NUKE_INSTALL_PATH"\n')
            f.write('_OLD_NUKE_INTERACTIVE="$NUKE_INTERACTIVE"\n')
            f.write('_OLD_DEADLINE_REPOSITORY_ROOT="$DEADLINE_REPOSITORY_ROOT"\n')
            f.write('_OLD_PATH="$PATH"\n')
            
            # Basic environment variables
            f.write(f'export NUKE_PATH="{nuke_path}"\n')
            f.write(f'export NUKE_INSTALL_PATH="{nuke_install_path}"\n')
            f.write(f'export DEADLINE_REPOSITORY_ROOT="{deadline_repository_root}"\n')
            f.write('export NUKE_INTERACTIVE=1\n')
            
            # For Unix, add conditional logic to avoid duplication
            f.write('\n# Add paths without duplication\n')
            f.write(f'PYTHON_PATH_ENTRY="{python_path}"\n')
            f.write(f'NUKE_PYTHON_PATH="{nuke_install_path}"\n')
            f.write('NUKE_BIN_PATH="${NUKE_INSTALL_PATH}/bin"\n\n')
            
            # PYTHONPATH setup with checks
            f.write('# Update PYTHONPATH\n')
            f.write('if [ -z "$PYTHONPATH" ]; then\n')
            f.write('    export PYTHONPATH="${PYTHON_PATH_ENTRY}:${NUKE_PYTHON_PATH}"\n')
            f.write('else\n')
            f.write('    if [[ ":$PYTHONPATH:" != *":${PYTHON_PATH_ENTRY}:"* ]]; then\n')
            f.write('        export PYTHONPATH="$PYTHONPATH:${PYTHON_PATH_ENTRY}"\n')
            f.write('    fi\n')
            f.write('    if [[ ":$PYTHONPATH:" != *":${NUKE_PYTHON_PATH}:"* ]]; then\n')
            f.write('        export PYTHONPATH="$PYTHONPATH:${NUKE_PYTHON_PATH}"\n')
            f.write('    fi\n')
            f.write('fi\n\n')
            
            # PATH setup with check
            f.write('# Update PATH with Nuke bin directory\n')
            f.write('if [[ ":$PATH:" != *":${NUKE_BIN_PATH}:"* ]]; then\n')
            f.write('    export PATH="${NUKE_BIN_PATH}:$PATH"\n')
            f.write('fi\n')
            
            # Deactivation function
            f.write('\ndeactivate_nk2dl() {\n')
            f.write('    # Revert to original values\n')
            f.write('    export NUKE_PATH="$_OLD_NUKE_PATH"\n')
            f.write('    export PYTHONPATH="$_OLD_PYTHONPATH"\n')
            f.write('    export NUKE_INSTALL_PATH="$_OLD_NUKE_INSTALL_PATH"\n')
            f.write('    export NUKE_INTERACTIVE="$_OLD_NUKE_INTERACTIVE"\n')
            f.write('    export DEADLINE_REPOSITORY_ROOT="$_OLD_DEADLINE_REPOSITORY_ROOT"\n')
            f.write('    export PATH="$_OLD_PATH"\n')
            f.write('    unset _OLD_NUKE_PATH\n')
            f.write('    unset _OLD_PYTHONPATH\n')
            f.write('    unset _OLD_NUKE_INSTALL_PATH\n')
            f.write('    unset _OLD_NUKE_INTERACTIVE\n')
            f.write('    unset _OLD_DEADLINE_REPOSITORY_ROOT\n')
            f.write('    unset _OLD_PATH\n')
            f.write('    unset PYTHON_PATH_ENTRY\n')
            f.write('    unset NUKE_PYTHON_PATH\n')
            f.write('    unset NUKE_BIN_PATH\n')
            f.write('}\n')
    
    print("Environment variables configured in virtual environment activation scripts")


def create_powershell_wrapper(venv_path):
    """Create a PowerShell wrapper script to activate both environments in one step."""
    if platform.system() == "Windows":
        print("Creating PowerShell wrapper script...")
        scripts_dir = Path(venv_path) / "Scripts"
        wrapper_path = scripts_dir / "Activate-nk2dl.ps1"
        
        with open(wrapper_path, "w") as f:
            f.write("# NK2DL Activation Script\n")
            f.write("# This script activates the virtual environment and sets up nk2dl environment variables in one step\n\n")
            f.write("Write-Host \"Activating NK2DL development environment...\" -ForegroundColor Cyan\n\n")
            f.write("# Activate the virtual environment\n")
            f.write("# Get the directory where this script is located\n")
            f.write("$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path\n\n")
            f.write("# Activate the venv\n")
            f.write("& \"$scriptDir\\Activate.ps1\"\n\n")
            f.write("# Source the nk2dl setup script\n")
            f.write("if (Test-Path \"$scriptDir\\nk2dl_setup.ps1\") {\n")
            f.write("    Write-Host \"Setting up NK2DL environment variables...\" -ForegroundColor Cyan\n")
            f.write("    . \"$scriptDir\\nk2dl_setup.ps1\"\n")
            f.write("    Write-Host \"Environment activated and ready!\" -ForegroundColor Green\n")
            f.write("} else {\n")
            f.write("    Write-Host \"Error: nk2dl setup script not found. Run 'python scripts/setup_environment.py' first.\" -ForegroundColor Red\n")
            f.write("}\n")
        
        print(f"PowerShell wrapper script created at: {wrapper_path}")


def main():
    """Main function to run the setup process."""
    print("Setting up nk2dl development environment...\n")
    
    # Get project root path
    project_root = Path.cwd()
    
    # Get Nuke installation path
    nuke_install_path = get_nuke_install_path()
    
    # Get Deadline repository root
    deadline_repository_root = get_deadline_repository_root()
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    
    # Install dependencies
    install_dependencies(venv_path)
    
    # Set up Deadline API
    setup_deadline_api(venv_path, deadline_repository_root)
    
    # Set up environment variables in virtual environment
    setup_venv_environment_vars(venv_path, nuke_install_path, deadline_repository_root)
    
    # Create PowerShell wrapper script for one-step activation
    create_powershell_wrapper(venv_path)
    
    print("\nSetup complete!")
    print(f"To activate the virtual environment:")
    
    if platform.system() == "Windows":
        print(f"    CMD: .venv\\Scripts\\activate.bat")
        print(f"    PowerShell: .venv\\Scripts\\Activate-nk2dl.ps1")
    else:
        print(f"    source .venv/bin/activate")
    
    print("\nAfter activation, the following environment variables will be set:")
    print("- NUKE_PATH: Points to the project directory")
    print("- PYTHONPATH: Points to the required python packages")
    print("- NUKE_INSTALL_PATH: Points to your Nuke installation")
    print("- DEADLINE_REPOSITORY_ROOT: Points to your Deadline repository")
    print("- NUKE_INTERACTIVE: Set to 1 for interactive Nuke Python module access")
    print("- PATH: Updated to include Nuke installation for direct executable access")
    print("\nThese variables will be automatically removed when you deactivate the environment.")


if __name__ == "__main__":
    main() 