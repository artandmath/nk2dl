#!/usr/bin/env python
"""Setup script for nk2dl."""

from setuptools import setup, find_packages
import os
import re


def read_version() -> str:
    """Read __version__ from src/nk2dl/info.py without importing the package."""
    version_path = os.path.join("src", "nk2dl", "info.py")
    with open(version_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*[\"\']([^\"\']+)[\"\']', content, re.M)
    if not match:
        raise RuntimeError("Cannot find __version__ in src/nk2dl/info.py")
    return match.group(1)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nk2dl",
    version=read_version(),
    author="Daniel Harkness",
    author_email="danielharkness@icloud.com",
    description="Nuke to Deadline Submitter - Core Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artandmath/nk2dl",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "types-PyYAML>=6.0.12.12"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    package_data={
        "nk2dl": ["config.yaml"],
    },
) 