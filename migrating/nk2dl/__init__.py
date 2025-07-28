"""Nuke to Deadline Submitter (nk2dl)."""

print("\nNuke to Deadline (nk2dl) v0.1")
print("Copyright (c) 2025 Daniel Harkness. All Rights Reserved.\n")

from .common.errors import NK2DLError
from .api import submit_nuke_script


# CLI entry point
def cli_main():
    """Main entry point for the nk2dl CLI."""
    from .cli.commands import main
    import sys
    sys.exit(main())
