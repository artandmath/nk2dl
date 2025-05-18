"""Public API for nk2dl."""

from .nuke.submission import submit_nuke_script as _submit_nuke_script

def submit_nuke_script(*args, **kwargs):
    """Public API for submitting Nuke scripts to Deadline."""
    return _submit_nuke_script(*args, **kwargs)
