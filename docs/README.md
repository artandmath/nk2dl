# Documentation Setup

This documentation setup uses **Sphinx** for Python API documentation while maintaining compatibility with your existing **Jekyll** markdown files.

## What's Been Set Up

### Sphinx Configuration (`conf.py`)
- **MyST Parser**: Enables Sphinx to read both `.rst` and `.md` files
- **Autodoc**: Automatically generates API documentation from Python docstrings
- **RTD Theme**: Modern, responsive documentation theme
- **Napoleon**: Supports Google/NumPy style docstrings
- **Intersphinx**: Links to external Python documentation

### File Structure
```
docs/
├── index.rst              # Main Sphinx entry point (replaces index.md for Sphinx)
├── conf.py                # Sphinx configuration
├── requirements.txt       # Documentation dependencies
├── Makefile               # Build commands for Unix/Linux
├── make.bat              # Build commands for Windows
├── .nojekyll             # Prevents GitHub Pages Jekyll processing
├── api/                  # API documentation
│   ├── modules.rst       # API reference index
│   └── nk2dl.rst        # Module documentation
├── _static/              # Static files (CSS, images, etc.)
├── _templates/           # Custom templates
└── *.md                  # Your existing markdown files (work with both)
```

### GitHub Actions Workflow
The workflow (`.github/workflows/docs.yml`):
1. **Installs Dependencies**: Sphinx, MyST parser, RTD theme, and project dependencies
2. **Builds Documentation**: Uses `make html` to generate static HTML
3. **Deploys to GitHub Pages**: Only on pushes to `development` branch

## How It Works with Jekyll

### Dual Compatibility
Your existing markdown files work with both:
- **Jekyll**: Uses `_config.yaml` for GitHub Pages
- **Sphinx**: Uses MyST parser to include `.md` files in Sphinx builds

### GitHub Pages Setup
- Sphinx builds override Jekyll
- `.nojekyll` file prevents Jekyll processing of Sphinx output
- Both documentation systems can coexist

## Building Documentation

### Locally (for testing)
```bash
cd docs
pip install -r requirements.txt
make html
# Output in _build/html/
```

### Via GitHub Actions
- Push to `development` branch
- Actions automatically build and deploy to GitHub Pages
- Available at: `https://yourusername.github.io/nk2dl/`

## Adding New Documentation

### For Python Code
1. Add docstrings to your Python modules
2. Sphinx autodoc will automatically include them
3. Update `docs/api/nk2dl.rst` if you add new modules

### For User Guides
1. Create `.md` files in `docs/` directory
2. Add them to the `toctree` in `docs/index.rst`
3. They'll work with both Jekyll and Sphinx

## Key Features

- ✅ **API Documentation**: Auto-generated from Python docstrings
- ✅ **Markdown Support**: Existing `.md` files work unchanged
- ✅ **Modern Theme**: Responsive RTD theme
- ✅ **Search**: Full-text search built-in
- ✅ **Cross-references**: Links between docs and code
- ✅ **GitHub Actions**: Automated building and deployment
- ✅ **Jekyll Compatibility**: Existing Jekyll setup still works