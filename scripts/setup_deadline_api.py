#!/usr/bin/env python3
"""Script to set up the Deadline Python API in your Python environment.

This script will:
1. Find your Python site-packages directory
2. Locate the Deadline repository API folder
3. Copy the Deadline API to your site-packages
4. Verify the installation
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess
from typing import Optional

def get_site_packages_dir() -> Path:
    """Get the site-packages directory for the current Python environment."""
    import site
    if hasattr(site, 'getsitepackages'):
        site_packages = site.getsitepackages()[0]
    else:
        # Fallback for virtual environments
        site_packages = site.getusersitepackages()
    return Path(site_packages)

def find_deadline_api(repository_root: Optional[str] = None) -> Optional[Path]:
    """Find the Deadline Python API folder in the repository.
    
    Args:
        repository_root: Optional path to Deadline repository root
        
    Returns:
        Path to the Deadline Python API folder or None if not found
    """
    # Try environment variable first
    if not repository_root:
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
        return None
    
    # Look for the API folder
    api_path = Path(repository_root) / 'api' / 'python' / 'Deadline'
    if api_path.exists():
        return api_path
    
    return None

def copy_deadline_api(src: Path, dest: Path) -> None:
    """Copy the Deadline API folder to site-packages.
    
    Args:
        src: Source Deadline API folder
        dest: Destination in site-packages
    """
    if dest.exists():
        print(f"Removing existing Deadline API from {dest}")
        shutil.rmtree(dest)
    
    print(f"Copying Deadline API from {src} to {dest}")
    shutil.copytree(src, dest)

def verify_installation() -> bool:
    """Verify that the Deadline API was installed correctly."""
    try:
        import Deadline.DeadlineConnect
        print("✓ Successfully imported Deadline API")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Deadline API: {e}")
        return False

def main():
    """Main function to set up the Deadline Python API."""
    print("Setting up Deadline Python API")
    print("=============================")
    
    # Get site-packages directory
    site_packages = get_site_packages_dir()
    print(f"Python site-packages directory: {site_packages}")
    
    # Find Deadline API
    api_path = find_deadline_api()
    if not api_path:
        print("\nCould not find Deadline API folder automatically.")
        print("Please enter the path to your Deadline repository root:")
        repository_root = input("> ").strip()
        api_path = find_deadline_api(repository_root)
        
    if not api_path:
        print("\n✗ Error: Could not find Deadline API folder.")
        print("Please ensure one of the following:")
        print("1. DEADLINE_REPOSITORY_ROOT environment variable is set")
        print("2. DEADLINE_PATH environment variable is set")
        print("3. Manually provide the repository root path")
        sys.exit(1)
    
    print(f"\nFound Deadline API at: {api_path}")
    
    # Copy API to site-packages
    dest_path = site_packages / 'Deadline'
    try:
        copy_deadline_api(api_path, dest_path)
    except Exception as e:
        print(f"\n✗ Error copying API: {e}")
        sys.exit(1)
    
    # Verify installation
    print("\nVerifying installation...")
    if verify_installation():
        print("\n✓ Deadline Python API successfully installed!")
        sys.exit(0)
    else:
        print("\n✗ Installation verification failed.")
        sys.exit(1)

if __name__ == '__main__':
    main() 