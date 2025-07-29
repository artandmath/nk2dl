# NK2DL Structure Migration Plan

## Overview
This document outlines the migration plan to flatten the nk2dl directory structure for better organization and maintainability. **Note: This migration only affects the main `src/nk2dl/` directory. The `migration/` folder will remain untouched as a rollback reference.**

## Current Structure
```
src/nk2dl/
├── __init__.py
├── api.py
├── config.yaml
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py
│   ├── framerange.py
│   └── logging.py
├── deadline/
│   ├── __init__.py
│   └── connection.py
└── nuke/
    ├── __init__.py
    ├── parser.py
    ├── submission.py
    ├── subprocess.py
    └── utils.py
```

## Target Structure
```
src/nk2dl/
├── __init__.py
├── api.py
├── config.yaml
├── config.py (moved from common/)
├── errors.py (moved from common/)
├── framerange.py (moved from common/)
├── logging.py (moved from common/)
├── connection.py (moved from deadline/)
├── parser.py (renamed from nukescript_parser.py, originally from nuke/parser.py)
├── submission.py (moved from nuke/)
├── subprocess.py (moved from nuke/)
└── nuke_utils.py (renamed from nuke/utils.py)
```

## Migration Steps

### 1. Remove Directory Nesting
- **Remove `common/` directory**: Move all files up one level
  - `common/config.py` → `config.py`
  - `common/errors.py` → `errors.py`
  - `common/framerange.py` → `framerange.py`
  - `common/logging.py` → `logging.py`
- **Remove `deadline/` directory**: Move all files up one level
  - `deadline/connection.py` → `connection.py`
- **Remove `nuke/` directory**: Move all files up one level
  - `nuke/submission.py` → `submission.py`
  - `nuke/subprocess.py` → `subprocess.py`

### 2. File Renames
- `nuke/parser.py` → `nukescript_parser.py` → `parser.py`
- `nuke/utils.py` → `nuke_utils.py`

### 3. Import Updates Required
Update all import statements throughout the codebase to reflect the new structure:

#### Common Module Imports
- `from nk2dl.common.config import ...` → `from nk2dl.config import ...`
- `from nk2dl.common.errors import ...` → `from nk2dl.errors import ...`
- `from nk2dl.common.framerange import ...` → `from nk2dl.framerange import ...`
- `from nk2dl.common.logging import ...` → `from nk2dl.logging import ...`

#### Deadline Module Imports
- `from nk2dl.deadline.connection import ...` → `from nk2dl.connection import ...`

#### Nuke Module Imports
- `from nk2dl.nuke.submission import ...` → `from nk2dl.submission import ...`
- `from nk2dl.nuke.subprocess import ...` → `from nk2dl.subprocess import ...`
- `from nk2dl.nuke.parser import ...` → `from nk2dl.nukescript_parser import ...` → `from nk2dl.parser import ...`
- `from nk2dl.nuke.utils import ...` → `from nk2dl.nuke_utils import ...`

### 4. Files Requiring Import Updates
Based on search results, the following files will need import updates:

#### Main Source Files
- `src/nk2dl/nuke/subprocess.py` - imports from nuke.submission

#### Test Files
- `tests/test_deadline_connection.py`
- `tests/pytest/pytest_deadline_connection.py`
- `tests/pytest/pytest_submission.py`
- `tests/pytest/pytest_config.py`
- `tests/pytest/conftest.py`

### 5. Benefits
- **Simplified imports**: Shorter, cleaner import paths
- **Reduced nesting**: Easier to navigate and understand
- **Better organization**: Related functionality at the same level
- **Improved maintainability**: Less directory traversal needed
- **Cleaner API**: More intuitive module structure

### 6. Considerations
- **Backward compatibility**: May need to maintain compatibility during transition
- **Testing**: All tests will need import path updates
- **Documentation**: Update any documentation referencing old paths
- **External dependencies**: Check if any external code depends on current structure
- **Internal imports**: Update any self-referential imports within the codebase
- **Migration folder preservation**: The `migration/` folder serves as a rollback reference and should not be modified

## Implementation Plan
1. Create backup branch
2. Update imports in all files (search and replace) - **excluding migration/ folder**
3. Move files to new locations using `git mv`
4. Rename specific files using `git mv`
5. Update `__init__.py` files to reflect new structure
6. Run tests to verify functionality
7. Update documentation
8. Commit changes with proper conventional commit message

## Rollback Plan
If issues arise, the backup branch can be used to quickly revert changes. The `migration/` folder serves as an additional rollback reference with the original structure.

## Notes
- This migration only affects the main `src/nk2dl/` directory
- The `migration/` folder will remain untouched as a rollback reference
- All import statements need to be updated before moving files to avoid breaking the codebase
- The migration should be done in a single atomic commit to maintain clean git history