# Code Audit Implementation TODO

**Based on CODE_AUDIT_AND_IMPROVEMENTS.md validation**  
**Date Created:** 2025-01-27  
**Last Updated:** 2025-01-27  

## Status Overview

✅ **Completed Items:**
- Version synchronization (setup.py now reads from info.py)
- Copyright banner environment variable (NK2DL_HIDE_COPYRIGHT implemented)
- Docs gitignore entry (docs/_site/ added to .gitignore)

## Outstanding Tasks

### 🚀 Quick Wins (High Value, Low Risk)

#### 1. Fix Deadline Timeout
- **Status:** ❌ Pending
- **Description:** Increase default deadline timeout from 1 to 10 seconds
- **File:** `src/nk2dl/config.py` line 123
- **Impact:** Prevents timeout failures on real farms
- **Effort:** 5 minutes

#### 2. Fix Sphinx Branch Configuration
- **Status:** ❌ Pending
- **Description:** Update github_version from 'main' to 'development'
- **File:** `docs/_sphinx/conf.py` line 51
- **Impact:** Ensures docs link to correct branch
- **Effort:** 2 minutes

#### 3. Cross-Platform Subprocess Support
- **Status:** ❌ Pending
- **Description:** Add macOS/Linux Nuke Python resolution (currently Windows-only)
- **File:** `src/nk2dl/subprocess.py` line 100
- **Impact:** Enables cross-platform functionality
- **Effort:** 30 minutes

### 🧹 Cleanup & Documentation

#### 4. Update Audit Document
- **Status:** ❌ Pending
- **Description:** Mark completed items and refresh current status in audit document
- **File:** `plans/CODE_AUDIT_AND_IMPROVEMENTS.md`
- **Impact:** Keeps documentation accurate
- **Effort:** 15 minutes

#### 5. Remove Built Docs from Repository
- **Status:** ❌ Pending
- **Description:** Remove existing docs/_site/ directory from repository history
- **Current:** Directory exists but is in .gitignore
- **Impact:** Reduces repository size
- **Effort:** 10 minutes

#### 6. Archive Migration Directory
- **Status:** ❌ Pending
- **Description:** Remove or archive migration/ directory to prevent accidental imports
- **File:** `migration/` directory
- **Impact:** Reduces maintenance confusion
- **Effort:** 15 minutes

### 🔧 Code Quality Improvements

#### 7. Add Debug Logging Guards
- **Status:** ❌ Pending
- **Description:** Protect expensive debug operations with `logger.isEnabledFor(logging.DEBUG)`
- **File:** `src/nk2dl/submission.py` (various locations)
- **Impact:** Improves performance when debug logging disabled
- **Effort:** 45 minutes

#### 8. Complete Parser Implementation
- **Status:** ❌ Pending
- **Description:** Finish NotImplementedError methods or add feature gates
- **File:** `src/nk2dl/parser.py`
- **Impact:** Enables parser-dependent features or provides clear error messages
- **Effort:** 2-4 hours (depending on scope)

### 🏗️ Major Refactoring (Plan and Stage)

#### 9. Refactor submission.py
- **Status:** ❌ Pending
- **Description:** Break down 4,102-line file into focused modules
- **Current:** Single large file with multiple responsibilities
- **Proposed modules:**
  - SubmissionOptions (dataclass)
  - WriteNodeResolver
  - FrameRangeService
  - JobInfoBuilder / PluginInfoBuilder
  - DeadlineSubmitter
  - BuildJobSupport
- **Impact:** Better maintainability, testability, fewer side-effects
- **Effort:** 1-2 weeks (incremental approach recommended)

## Implementation Notes

### Commit Strategy
Follow conventional commit format from the audit:
- `fix(connection): increase default deadline timeout to 10s`
- `fix(docs): update sphinx branch to development`
- `feat(subprocess): add macOS/Linux Nuke Python resolution`
- `chore(docs): remove docs/_site from repo and update gitignore`
- `refactor(submission): extract JobInfoBuilder and PluginInfoBuilder`

### Risk Assessment
- **Quick wins (1-3):** Low risk, high value - can be done immediately
- **Cleanup (4-6):** Low risk, medium value - good for maintenance
- **Code quality (7-8):** Medium risk, high value - needs testing
- **Refactoring (9):** High complexity - requires careful planning and staging

### Dependencies
- Items 1-6 can be done independently
- Item 7 should be done before major refactoring
- Item 8 may inform refactoring decisions
- Item 9 should be planned after completing other items

## References
- Original audit: `plans/CODE_AUDIT_AND_IMPROVEMENTS.md`
- VFX Reference Platform 2024+: https://vfxplatform.com/
