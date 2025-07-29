# NK2DL Panel Configuration Plan

This document outlines a plan to implement a flexible configuration system for the nk2dl GUI panel. The goal is to allow administrators to control the visibility, editability, and default values of panel controls.

## 1. Background Research: Existing Configuration System

The existing configuration system in `nk2dl` is managed by the `nk2dl.common.config.Config` class. It provides a solid foundation for the panel configuration.

### Configuration Load Order

Configuration is loaded from multiple sources, with later sources overriding earlier ones. The load order is as follows:

1.  **Default Config**: A dictionary (`DEFAULT_CONFIG`) hardcoded within the `nk2dl.common.config` module.
2.  **Project Config**: A YAML file located at `nk2dl/config.yaml`. The path to this file can be overridden by the `NK2DL_CONFIG` environment variable.
3.  **Environment Variables**: Environment variables prefixed with `NK2DL_` can override specific settings. For example, `NK2DL_DEADLINE_POOL=new_pool` would set the `deadline.pool` value.
    -   **Underscore Convention**: To set a config key that contains an underscore (e.g., `use_web_service`), the environment variable must use a double underscore (e.g., `NK2DL_DEADLINE_USE__WEB__SERVICE`).
4.  **User Config**: A YAML file located at `~/.nk2dl/config.yaml`. This file has the highest precedence.

This existing system is well-suited for our needs and will be used for the panel configuration.

## 2. Panel Configuration Proposal

We will introduce a new top-level section in the configuration named `panel`. This section will contain all the settings related to the GUI panel's controls.

### Configuration Structure

The `panel` section will have subsections for each control on the panel. The name of the subsection will match the internal object name of the widget/control. Each control's configuration will have three optional keys:

-   `value`: Sets the default value of the control when the panel is opened.
-   `hidden`: If `true`, the control will be completely hidden from the user.
-   `disabled`: If `true`, the control will be visible but greyed out and not editable by the user.

### Example Configuration (`config.yaml`)

```yaml
# ... existing deadline, logging, submission sections ...

panel:
  # Configuration for the 'Priority' control
  priority_control:
    value: 75
    disabled: true

  # Configuration for the 'Initial Job Status' control
  job_status_control:
    value: "Suspended"

  # Configuration for the 'Use GPU' checkbox
  use_gpu_checkbox:
    hidden: true
```

In this example:
-   The "Priority" control will be visible but disabled, and its value will be set to 75.
-   The "Initial Job Status" control will be editable, with its initial value set to "Suspended".
-   The "Use GPU" checkbox will be completely hidden from the panel.

If a control is not mentioned in the `panel` section, it will use its default, hard-coded behavior in the panel's source code.

## 3. Implementation Plan

The implementation will involve changes primarily in the GUI-related part of the `nk2dl` codebase.

1.  **Update `Config` Defaults**: Add the `panel: {}` section to the `DEFAULT_CONFIG` dictionary in `nk2dl/common/config.py`. This ensures the `panel` key always exists.

2.  **Create a Panel Configuration Module**: A new module, `nk2dl.gui.panel_config`, will be created. This module will be responsible for:
    -   Getting the application-wide `Config` instance.
    -   Providing simple helper functions to apply the configuration to Qt widgets. For example:
        -   `apply_config(widget, control_name)`: A generic function that takes a Qt widget and its configuration name. It will read the `panel.<control_name>` section and apply the `value`, `hidden`, and `disabled` properties.
        -   This function will be smart enough to handle different types of widgets (e.g., `QSpinBox`, `QComboBox`, `QCheckBox`).

3.  **Modify the Panel UI Code**: The main panel's UI code (likely in a file like `nk2dl/gui/panel.py`) will be modified.
    -   When the panel is initialized, it will import the `apply_config` function from `nk2dl.gui.panel_config`.
    -   For each relevant control in the panel, it will call `apply_config(self.my_control, "my_control_config_name")`.

### Handling Intrinsic Controls

Some controls are essential for the panel's core functionality and should not be hidden or disabled. For example, the "Submit" button.

-   **By Convention**: We will simply not call the `apply_config` function for these intrinsic controls. Their behavior will remain as defined in the UI code.
-   **Documentation**: We will document which controls are considered intrinsic and cannot be configured. This will be part of the general documentation for the panel configuration.

This approach gives us the desired flexibility without adding excessive complexity. It reuses the existing, powerful configuration system and provides a clear and predictable way to manage the panel's user interface. 