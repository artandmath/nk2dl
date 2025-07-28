# Storage Plan (O3)

## Original User Question (context)
> The job, extra and machine settings store values which we will pass to `submission.py`.
>
> I have tried to name the widgets the same values as the args that are taken when submitting a nuke script. Can you come up with a plan to do the following:
>
> **A** – Store any overridden settings values in the storage  
> **B** – In a manner that makes sense with translating the values to the right args for submission  
> **C** – Ideally this is done by using the exact same names for controls as the submission args and storage so that no translation of variable names is required.  
> **D** – `node_overrides` should do the same, we take the values from node overrides and parse them as an array of args to the nuke submission for per-write overrides (read the docs on how this is done)

---

## 1. Goals & Non-negotiables
1. **Zero-translation pipeline** – UI → Storage → Submission must all use the identical argument names.
2. **Atomic storage** – One serialised YAML blob (per script) that stores:
   - Global settings (job, machine, extra)
   - UI state (column widths, visibility, etc.)
   - Per-node overrides
3. **Backward compatibility** – Old blobs (version ≤ 0.1) should load without error.
4. **Future proof** – Versioned schema + migration hooks.
5. **Minimal in-memory coupling** – `NodeSettingsStorage` remains the single source of truth; other modules only interact through its public API.

## 2. Current State (storage.py)
| Area | Status | Gap |
|------|--------|-----|
| Saves `node_overrides` | ✅ | Only per-node, no globals/UI |
| Knob creation / YAML I/O | ✅ | Version fixed at `0.1` |
| Migration hooks | ❌ | Needed for upcoming schema changes |
| Convenience getters for submission | ❌ | Must assemble argument dicts |

## 3. Proposed YAML Structure (v0.2)
```yaml
version: "0.2"
timestamp: 1700000000.000
settings:
  job:
    priority: 50
    chunk_size: 1
    frames: "1001-1010"
    use_nuke_x: false
    batch_mode: true
    # …
  machine:
    pool: "comp"
    group: "none"
    ram_use: 8192
    # …
  extra:
    job_name: "{script}_{write}"
    comment: "Rendered with nk2dl"
  ui:
    column_widths: { Priority: 60, Frames: 120 }
    frozen_columns: [0, 1]
node_overrides:
  Write1:
    priority: 75
    pool: "lighting"
  Write2:
    use_gpu: true
```
*All keys exactly match `submission.py` kwargs.*

## 4. Public API (v0.2)
```python
class NodeSettingsStorage:
    STORAGE_VERSION = "0.2"

    # high-level helpers
    def save_all(self, *, job, machine, extra, ui, node_overrides) -> bool: ...
    def load_all(self) -> dict: ...

    # convenience for submission
    def build_submission_args(self, script_path: str) -> dict: ...
    def get_write_node_overrides(self) -> list[dict[str, Any]]: ...
```
### Key points
* **Atomic write** – one call serialises the entire structure to avoid partial corruption.
* **Migration** – `load_all()` detects `version` and calls `_migrate_<from>_to_<to>()` functions lazily.
* **Thread safety** – use a re-entrant lock around knob I/O (important for multi-threaded UIs).

## 5. Name Alignment Strategy
1. **Widget IDs = Storage keys = `submission.py` kwargs.**
2. `constants.py` will become the single authoritative list of default values using the canonical names.
3. Any legacy aliases (e.g. `use_nukex`) handled only during migration; no alias logic in runtime code.

## 6. Node Override Handling
* Stored overrides already live under `node_overrides` → keep unchanged.
* Extend helper `get_write_node_overrides()` to return a list of `{'write_node': name, **overrides}` dicts ready for `submission.py`.

## 7. UI State Persistence
Minimal but critical items we want to survive reloads:
* Column widths & order
* Visibility & frozen state
* Last active tab / filter settings
These keys stay under `settings.ui` so submission-related code can ignore them safely.

## 8. Migration Path
1. **Detect** missing `settings` root → assume v0.1 (node overrides only).
2. **Wrap** old structure into new schema with empty `settings` dict.
3. **Write-back** upgraded blob on next save.

## 9. Testing Matrix
| Test | Purpose |
|------|---------|
| `test_roundtrip_globals` | Saving & loading global settings retains values |
| `test_roundtrip_overrides` | Ditto for overrides |
| `test_submission_args` | `build_submission_args()` returns expected kwargs |
| `test_migration_v01` | Load legacy v0.1 YAML, auto-migrates to v0.2 |
| `test_ui_state` | Column widths persist |

## 10. Implementation Steps
1. **Refactor** `NodeSettingsStorage`:
   - Add new fields & API methods
   - Introduce version constant `0.2`
2. **Update constants & models** to canonical names (separate PR to keep commits atomic).
3. **Wire-up UI** widgets to use canonical names.
4. **Submission integration** – swap bespoke arg construction with `storage.build_submission_args()`.
5. **Write tests** (pytest) covering matrix above.
6. **Docs** – update `docs/` and CHANGELOG.

## 11. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking existing scenes | 🟥 | Migration & robust fallback to defaults |
| Widget rename regressions | 🟧 | Linter + compile-time checks on constant list |
| YAML size bloat | 🟨 | Use `safe_dump` + `indent=2`; ignore binary data |
| Concurrent knob writes | 🟨 | Thread-safe lock in storage class |

## 12. Success Criteria
* No translation layer between UI and submission.
* Users can close & reopen panel and retain full state.
* Legacy scenes open without warnings.
* All unit & integration tests green.

---

### Next Steps
If this plan is approved, I will:
1. Prepare a **migration-only** PR to introduce `v0.2` schema + tests.
2. Follow with **UI rename** PR.
3. Final PR for submission integration.

— **O3** 