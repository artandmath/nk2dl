## nk2dl code audit and improvement plan

Date: 2025-08-10

### Executive summary
- Core architecture is solid and test-backed; submission, config, connection, and frame range handling are present and cohesive.
- There is duplication between `migration/` and `src/nk2dl/` plus unfinished parser stubs; this adds maintenance risk.
- A few high-impact polish items: versioning mismatch, Windows-only subprocess pathing, aggressive default timeouts, and very large `submission.py`.

### Key findings
- Architecture
  - `src/nk2dl/` contains the flattened structure; `migration/` holds old structure references and duplicates. Keeping both increases confusion and risk of accidental imports.
  - `submission.py` is very large and multi-responsibility (config merge, node discovery, render-order logic, frame range building, job/plugin info building, submission, build-job script generation).
- Versioning & packaging
  - Mismatch between runtime and packaging versions:
    - `src/nk2dl/info.py` declares `__version__ = "0.1.9-alpha"`.
    - `setup.py` declares `version="0.1.0"`.
  - `python_requires=">=3.10"` aligns with VFX Platform 2024+. Good.
- Deadline connection
  - Web service submission uses `Jobs.SubmitJob(...)` properly, but default `deadline.timeout` is `1` second which is risky for real farms. Fallback to command-line exists, but error handling relies partly on stderr string matching.
  - Command-line branch parses `JobID=` well but should also consider process return codes and robust stderr handling.
- Subprocess script execution
  - Uses `nuke.EXE_PATH` to find `python.exe` (Windows-specific). No non-Windows branch for Nuke Python.
  - Embeds JSON into a generated Python file; escaping is handled, but base64 would be more robust.
- Parser & utilities
  - `parser.py` exists and `nuke_utils.parser_module()` calls `parser.create_parser()`, but `NukeParser._parse_script()` and several methods remain `NotImplemented`. Any code path that depends on parser functionality will be incomplete.
- Frame range
  - `FrameRange` is feature-complete for tokens and expansion; integrates with Nuke or script content. Good coverage.
- Logging
  - Centralized logger with session handling and config integration is strong. Heavy debug logging in `submission.py` should be guarded with `isEnabledFor(logging.DEBUG)` around expensive formatting.
- Docs & repo hygiene
  - Built docs (`docs/_site/`) are committed; better to exclude from VCS. Sphinx config uses `github_version='main'` while active work occurs on `development`.
- Tests
  - Pytest suite is substantial with mock/real modes. Guidance discourages mocking the Nuke module; good. No CI config in repo; coverage not enforced.

### Quick wins (low risk, high value)
1. Version source of truth
   - Load version in `setup.py` from `nk2dl.info.__version__` to avoid divergence.
   - Adopt semantic prerelease format consistently (e.g., `0.1.9a0`).
2. Increase default Deadline timeout
   - Change `deadline.timeout` default from `1` to `10` seconds.
3. Cross-platform Nuke Python resolution
   - In `subprocess.execute_submission_script`, support macOS/Linux by resolving Nuke Python correctly (app bundle on macOS; `NukeX{ver}` layout on Linux).
4. Remove built docs from repo
   - Add `docs/_site/` to `.gitignore`; host docs via CI or manual builds.
5. Guard expensive debug logs
   - Use `if logger.isEnabledFor(logging.DEBUG):` around heavy `json.dumps(...)`, large list/dict formatting.
6. Align Sphinx branch
   - Update `docs/_sphinx/conf.py` `github_version` to `development` or parameterize via env.

### High-impact refactors (plan and stage)
- Split `submission.py` into focused modules/classes
  - SubmissionOptions (dataclass): typed inputs and defaults resolution from config/env/CLI.
  - WriteNodeResolver: enumerate, filter, sort (alphabetical/render order), and per-node overrides.
  - FrameRangeService: unify `FrameRange` token substitution with Nuke/script and write-node input ranges.
  - JobInfoBuilder and PluginInfoBuilder: pure functions that build dicts; easy to test.
  - DeadlineSubmitter: web-service vs command-line strategy, retries, and error normalization.
  - BuildJobSupport: generation, aux file bundling, and cleanup.
  - Benefits: smaller units, better tests, fewer side-effects.
- Parser completion or feature gate
  - If parser is not on the roadmap, hard-gate features needing it and present clear messages.
  - If parser is required: implement minimal parsing for root frames, write nodes, names, file paths, use_limit, and render_order.
- Migrate/retire `migration/`
  - Either remove from repo (preserve in a branch) or mark as archived; prevent accidental imports.

### Detailed recommendations
- Versioning and packaging
  - Single source of truth for version (import in `setup.py`). Ensure `__version__` conforms to PEP 440.
  - Add `pyproject.toml` for build-system, Black/Flake8/isort configs, and mypy.
- Connection robustness
  - Increase default timeout to 10; add configurable retry count for transient failures.
  - In command-line path: check `returncode` first; treat non-zero as failure regardless of stderr content.
  - Normalize Deadline error messages to `DeadlineError` with helpful context.
  - Respect `ssl_cert` when `ssl=True` and verify certificate path exists.
- Subprocess
  - macOS: find Python inside the Nuke app bundle (`.../Contents/MacOS/python3` or `.../Contents/MacOS/Nuke{ver} --t` approach) or shell out to `nuke` with `-t`.
  - Linux: detect `nuke` binary dir and use shipped Python if present; otherwise `nuke -t`.
  - Switch kwargs passing to base64 blob to avoid quoting pitfalls.
- Config
  - Consider a typed accessor layer or dataclasses for sections (submission, deadline, logging).
  - Add schema validation for submission keys (types, ranges). E.g., `priority 0–100`, `chunk_size >= 1`.
- Logging
  - Add `get_nk2dl_logger(name)` convenience in public API; keep `setup_logging` but prefer one path.
  - Route startup/banner output through the logger and only at DEBUG level.
    - Specifically, in `src/nk2dl/__init__.py` the banner `print(...)` should either be removed or sent to the logger and shown only when `logging.level` is DEBUG (or when an explicit env flag is set). Keep `NK2DL_HIDE_COPYRIGHT` as an override, defaulting to hide by default in non-DEBUG runs.
    - Branding banner: keep the `print(...)` in `src/nk2dl/__init__.py` by design (branding intent).
      - Document `NK2DL_HIDE_COPYRIGHT=1` for CI/tests or log-sensitive environments to suppress output.
      - Optionally add a minimal/one-line mode via `NK2DL_BRAND_MINIMAL=1` in the future (non-breaking).
    - Ensure `config.debug_config_info()` only triggers when `logging.level` is DEBUG (it already does) and never on import unless explicitly requested by the user.
- Tests & CI
  - Add CI to run unit tests (mock mode) and lint/type checks.
  - Add coverage threshold (e.g., 80%).
  - Add tests for: version sync, cross-platform subprocess path selection, connection timeout/retry behavior.
- Docs
  - Remove `docs/_site/` from VCS; add a Make target and README note for generating docs locally.
  - Ensure docs match current module paths (`src/nk2dl/...`).

### VFX Reference Platform 2024+ compliance
- Python 3.10+ already required; good.
- Ensure no hard dependency on Qt/PySide in core library (GUI split appears respected).
- Keep dependencies minimal and well-pinned for reproducibility.

### Risks and mitigations
- Refactoring `submission.py` may introduce regressions.
  - Mitigation: incremental extraction with tests per builder/resolver; maintain feature flags.
- Parser implementation scope creep.
  - Mitigation: minimal viable parser or explicit gating.

### Suggested task breakdown (conventional commits)
- fix(pkg): sync version to info.__version__ and bump to 0.1.9a0
- fix(connection): increase default deadline timeout to 10s and improve error handling
- fix(subprocess): add macOS/Linux Nuke Python resolution and base64 kwargs transport
- chore(docs): remove docs/_site from repo and update gitignore; set sphinx branch
- refactor(submission): extract JobInfoBuilder and PluginInfoBuilder
- refactor(submission): extract WriteNodeResolver and FrameRangeService
- chore(repo): archive/remove migration/ directory (move to branch)
- test(connection): add timeout/retry tests; test JobID parsing vs returncode
- test(subprocess): add cross-platform path selection tests

### References to current code (for context)
- Version mismatch
  - info version:
    - src/nk2dl/info.py → `__version__ = "0.1.9-alpha"`
  - package version:
    - setup.py → `version="0.1.0"`
- Parser stubs
  - src/nk2dl/parser.py → `NukeParser._parse_script()` and several methods are `NotImplemented`.
- Windows-only Nuke Python pathing
  - src/nk2dl/subprocess.py → assumes `os.path.join(os.path.dirname(nuke.EXE_PATH), "python.exe")`.
- Aggressive default timeout
  - src/nk2dl/config.py → `deadline.timeout: 1`.

---

If you want, I can implement the Quick wins in a single small PR next, then plan the submission refactor across 2–3 incremental commits with tests.
