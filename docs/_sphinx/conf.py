# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the source directory to the Python path
sys.path.insert(0, os.path.abspath('../../src'))

# Import version info
from nk2dl import info

# -- Project information -----------------------------------------------------
project = 'nk2dl'
copyright = f'{info.__copyright__}'
author = info.__author__
version = info.__version__
release = info.__version__

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f"{project} v{version}"

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx mapping to link to other documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Autosummary settings
autosummary_generate = True

# Suppress warnings for better CI output
suppress_warnings = [
    'docutils',  # Suppress docstring formatting warnings
]

# Make warnings less verbose
nitpicky = False