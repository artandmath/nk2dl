# Qt Test Files

This directory contains Qt-based test applications for debugging and testing the NK2DL panel inheritance system.

## Files

### `test_main_panel_nuke.py`
**Purpose**: Main NK2DL panel test in Nuke  
**Usage**: `nuke --tg tests/qt/test_main_panel_nuke.py`  
**Description**: Tests the complete NK2DL panel with all tabs and features in Nuke's Qt environment. Includes sample data demonstrating inheritance behavior.

### `test_qt_app_nuke.py`
**Purpose**: Nuke-compatible Qt test application  
**Usage**: `nuke --tg tests/qt/test_qt_app_nuke.py`  
**Description**: Tests the inheritance system within Nuke's Qt environment. Avoids relative import issues by implementing a simplified view without complex dependencies.

### `test_qt_app.py`
**Purpose**: Standalone Qt test application  
**Usage**: `python tests/qt/test_qt_app.py`  
**Description**: Tests the inheritance system in a standalone Qt environment (requires PySide2/PySide6).

### `test_inheritance_logic.py`
**Purpose**: Logic-only inheritance test (no UI)  
**Usage**: `python tests/qt/test_inheritance_logic.py`  
**Description**: Tests the core inheritance logic without Qt dependencies using mock objects.

### `debug_styling.py`
**Purpose**: Styling logic debugging  
**Usage**: `python tests/qt/debug_styling.py`  
**Description**: Debugs the styling logic that determines when cells should be bold (explicit) vs normal (inherited).

## Expected Behavior

All tests should demonstrate:
- **Bold text**: Explicit values (overrides)
- **Normal text**: Inherited values from settings
- **Proper inheritance**: `None` values inherit from job/machine settings
- **Override detection**: Non-`None` values are treated as explicit overrides

## Test Data Structure

The tests use sample data with:
- **Row 1**: Mix of explicit and inherited values
- **Row 2**: All explicit values (should all be bold)
- **Row 3**: All inherited values (should all be normal text)

## Recent Fixes

### Signal Blocking Fix
Fixed double styling issue where inherited cells were incorrectly showing as bold:
- **Problem**: `itemChanged` signals during initial load caused inherited values to be converted to explicit values
- **Solution**: Added signal blocking during `_load_data_from_model()` to prevent unwanted signal triggers
- **Applied to**: Both test applications and main panel code

## Troubleshooting

If you encounter import errors:
1. Ensure you're running from the repository root directory
2. Check that the nk2dl package path is correctly resolved
3. For Nuke tests, ensure you're using `nuke --tg` (terminal GUI mode) 