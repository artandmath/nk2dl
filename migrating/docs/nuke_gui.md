# GUI Documentation

## Installation

To install the nk2dl GUI into nuke, add the following to your `menu.py`:

```python
from nk2dl import setup_gui
```
The followng commands will be added to the render menu:
- Submit Nuke to Deadline - `shift + F7`
- Submit Selected Writes to Deadline - `alt + shift + F7`

## Keeping the Thinkbox submitter available

While nk2dl is in alpha state, you may still wish to keep the default Thinkbox submitter handy.Keep both the nk2dl and Thinkbox submitters available with the following, or re-purpose the setup functions from `setup_gui` to create your own menus that call the `nk2dl` commands:

```python
import DeadlineNukeClient
menubar = nuke.menu("Nuke")
render_menu = menubar.addMenu('Render')
render_menu.addSeparator()
render_menu.addCommand("Submit Nuke to Deadline (Thinkbox)", DeadlineNukeClient.main, "Ctrl+F7")
from nk2dl import setup_gui
```