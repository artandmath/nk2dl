#!/usr/bin/env python
"""
nk2dl - Setup Environment Script

This script helps set up the development environment for nk2dl:
1. Creates a virtual environment
2. Installs dependencies from requirements.txt
3. Sets up environment variables (NUKE_PATH, PYTHONPATH)

Usage:
    python scripts/setup_environment.py

Requirements:
    - Python 3.11.x
    - virtualenv (or similar tool)
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


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


def setup_venv_environment_vars(venv_path):
    """Set up environment variables in the virtual environment activation scripts."""
    print("Setting up environment variables in virtual environment...")
    
    project_root = Path.cwd()
    
    if platform.system() == "Windows":
        # Modify Windows activation script
        activate_bat = Path(venv_path) / "Scripts" / "activate.bat"
        deactivate_bat = project_root / Path(venv_path) / "Scripts" / "deactivate.bat"
        nuke_path = project_root / Path(venv_path) / "Lib" / "site-packages" 
        
        # Add to activate.bat
        with open(activate_bat, "a") as f:
            f.write("\n@REM nk2dl environment variables\n")
            f.write("set _OLD_NUKE_PATH=%NUKE_PATH%\n")
            f.write("set _OLD_PYTHONPATH=%PYTHONPATH%\n")
            f.write(f"set NUKE_PATH={nuke_path}\n")
            f.write(f"set PYTHONPATH=%PYTHONPATH%;{nuke_path}\n")
        
        # Add to deactivate.bat
        with open(deactivate_bat, "a") as f:
            f.write("\n@REM Restore old nk2dl environment variables\n")
            f.write("if defined _OLD_NUKE_PATH set NUKE_PATH=%_OLD_NUKE_PATH%\n")
            f.write("if defined _OLD_PYTHONPATH set PYTHONPATH=%_OLD_PYTHONPATH%\n")
            f.write("set _OLD_NUKE_PATH=\n")
            f.write("set _OLD_PYTHONPATH=\n")
    else:
        # Modify Unix/Linux/Mac activation script
        activate_sh = Path(venv_path) / "bin" / "activate"
        with open(activate_sh, "a") as f:
            f.write("\n# nk2dl environment variables\n")
            f.write('_OLD_NUKE_PATH="$NUKE_PATH"\n')
            f.write('_OLD_PYTHONPATH="$PYTHONPATH"\n')
            f.write(f'export NUKE_PATH="{nuke_path}"\n')
            f.write(f'export PYTHONPATH="$PYTHONPATH:{nuke_path}"\n')
            f.write('\ndeactivate_nk2dl() {\n')
            f.write('    # Revert to original values\n')
            f.write('    export NUKE_PATH="$_OLD_NUKE_PATH"\n')
            f.write('    export PYTHONPATH="$_OLD_PYTHONPATH"\n')
            f.write('    unset _OLD_NUKE_PATH\n')
            f.write('    unset _OLD_PYTHONPATH\n')
            f.write('}\n')
    
    print("Environment variables configured in virtual environment activation scripts")


def main():
    """Main function to run the setup process."""
    print("Setting up nk2dl development environment...\n")
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    
    # Install dependencies
    install_dependencies(venv_path)
    
    # Set up environment variables in virtual environment
    setup_venv_environment_vars(venv_path)
    
    print("\nSetup complete!")
    print(f"To activate the virtual environment:")
    
    if platform.system() == "Windows":
        print(f"    .venv\\Scripts\\activate")
    else:
        print(f"    source .venv/bin/activate")
    
    print("\nAfter activation, the following environment variables will be set:")
    print("- NUKE_PATH: Points to the project directory")
    print("- PYTHONPATH: Includes the project directory")
    print("\nThese variables will be automatically removed when you deactivate the environment.")


if __name__ == "__main__":
    main() 