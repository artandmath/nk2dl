"""Nuke to Deadline Submitter (nk2dl)."""

from .common.errors import NK2DLError

# CLI entry point
def cli_main():
    """Main entry point for the nk2dl CLI."""
    from .cli.commands import main
    import sys
    sys.exit(main())
