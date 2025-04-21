#!/usr/bin/env python
"""Setup script for nk2dl."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nk2dl",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Nuke to Deadline Submitter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nk2dl",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "nk2dl=nk2dl:cli_main",
        ],
    },
    install_requires=[
        "pyyaml",
    ],
) 