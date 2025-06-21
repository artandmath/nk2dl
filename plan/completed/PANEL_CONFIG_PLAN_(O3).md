# NK2DL Panel Configuration Plan (O3)

This document details how to extend the existing **`nk2dl.common.config.Config`** system so that the GUI panel can be driven entirely from the same configuration hierarchy (defaults → project config → environment → user config).

---
## 1. What already exists

* **Config class** – `nk2dl.common.config.Config` loads configuration in the exact order we need:
  1. `DEFAULT_CONFIG` hard-coded in `config.py` (lowest precedence)
  2. Project YAML (`nk2dl/config.yaml` or path set via `NK2DL_CONFIG`)
  3. Environment variables prefixed with `NK2DL_`
  4. User YAML (`~/.nk2dl/config.yaml`) – highest precedence
* **Env-var underscore convention** – single "_" inside a key becomes double "__" when expressed as an env var. E.g. `panel.my_checkbox.disabled` ⇒ `NK2DL_PANEL_MY__CHECKBOX_DISABLED`.

Because this machinery is stable and already used by non-GUI code, the panel layer only needs **read-only** access to `Config`.

---
## 2. Target behaviours

For every UI control we must be able to:

1. `hidden` – control is completely removed from the UI for artists.
2. `disabled` – control is visible but greyed-out and read-only.
3. `value` – initial value when panel opens.

Some widgets (e.g. Ⓢubmit / Render button, progress bar) are *intrinsic* to the panel's workflow and **must never be hidden or disabled**. We will simply never look them up in the config – see §4.4.

---
## 3. Proposed config schema

```yaml
panel:
  # QSpinBox – priority field
  priority_spinbox:
    value: 75        # int
    disabled: true

  # QComboBox – initial job status
  job_status_combo:
    value: Suspended # string

  # QCheckBox – GPU toggle
  use_gpu_checkbox:
    hidden: true
```

Key points:
* Sub-section name == `QtWidget.objectName()` by convention – no magic mapping tables.
* All keys are optional. Omitting a key means "leave default behaviour".

---
## 4. Implementation steps

### 4.1 Extend default config
Add an empty `panel: {}` entry to `Config.DEFAULT_CONFIG` so the key always exists.

### 4.2 New helper module – `nk2dl/gui/panel_config.py`

```python
from typing import Any
from PySide2 import QtWidgets, QtCore, QtGui  # PySide6 is imported lazily inside panel
from ..common.config import config  # global instance

IGNORED_TYPES = (QtWidgets.QLabel, QtWidgets.QFrame)  # never process


def apply_config(widget: QtWidgets.QWidget, key: str | None = None) -> None:
    """Apply `panel.<key>` settings to *widget*.

    If *key* is None we fall back to widget.objectName(). The function is idempotent.
    """
    key = key or widget.objectName()
    if not key:
        return  # unnamed widgets are skipped

    settings = config.get(f"panel.{key}", {})
    if not settings:
        return

    # 1. hidden
    if settings.get("hidden") is True:
        widget.hide()
        return  # no further work necessary

    # 2. disabled
    if settings.get("disabled") is True:
        widget.setEnabled(False)

    # 3. value – depends on widget type
    if "value" in settings:
        _set_widget_value(widget, settings["value"])


def _set_widget_value(widget: QtWidgets.QWidget, value: Any) -> None:
    """Best-effort setter that covers the widgets we use on the panel."""
    from PySide2 import QtWidgets  # runtime safe
    if isinstance(widget, QtWidgets.QAbstractButton):  # QCheckBox / QPushButton (toggle)
        if hasattr(widget, "setChecked"):
            widget.setChecked(bool(value))
    elif isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(int(value))
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        widget.setValue(float(value))
    elif isinstance(widget, QtWidgets.QComboBox):
        # try to select by text; fall back to index if int
        if isinstance(value, int):
            if 0 <= value < widget.count():
                widget.setCurrentIndex(value)
        else:
            idx = widget.findText(str(value))
            if idx >= 0:
                widget.setCurrentIndex(idx)
    elif isinstance(widget, QtWidgets.QLineEdit):
        widget.setText(str(value))
```

Notes:
* Small helper keeps logic self-contained, no panel code duplication.
* We only *read* from `config`, no writes.

### 4.3 Wire-up inside `nk2dl.gui.panel.panel.Nk2dlPanel`

1. After constructing each widget (before it is shown) call `apply_config(widget)`.
2. Ensure every controllable widget has a stable object name (`setObjectName("priority_spinbox")`). Most are already named – audit during implementation.
3. Skip intrinsic controls (render button, progress bar, etc.).

### 4.4 Intrinsic control list
Document and hard-code the following to *never* be processed:
* `render_btn`
* `progress_bar`
* any `QLabel` used for branding/version information

### 4.5 Tests / validation
* Unit test: create fake `Config` with in-memory dict and assert `apply_config` mutates a dummy `QSpinBox`, `QCheckBox`, etc.
* Integration smoke test: launch panel under pytest-qt and check visibility/enable state.

---
## 5. Environment variable mapping examples

| Desired effect | YAML key | Env var equivalent |
|----------------|----------|--------------------|
| Hide GPU checkbox | `panel.use_gpu_checkbox.hidden=true` | `NK2DL_PANEL_USE__GPU__CHECKBOX_HIDDEN=true` |
| Disable priority | `panel.priority_spinbox.disabled=true` | `NK2DL_PANEL_PRIORITY__SPINBOX_DISABLED=true` |
| Set default status | `panel.job_status_combo.value=Suspended` | `NK2DL_PANEL_JOB__STATUS__COMBO_VALUE=Suspended` |

The double-underscore rule ensures internal underscores are preserved when round-tripping through environment variables.

---
## 6. Roll-out strategy

1. Merge code but keep all widgets un-configured ⇒ behaviour remains unchanged.
2. Provide template snippet in main `config.yaml` so show TDs can copy/paste.
3. Announce to production: *"You can now hide/lock default values through `panel:` section."*

---
## 7. Estimated effort

* **1 d** – audit widgets and assign `objectName`s where missing.
* **0.5 d** – implement `panel_config` module + unit tests.
* **0.5 d** – integrate into panel class.
* **0.5 d** – docs, review, QA.

**Total:** ≈ **2.5 developer days**. 