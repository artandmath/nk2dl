# GUI Documentation

## Installation

To install the nk2dl GUI, add the following to your `menu.py`:

```python
from nk2dl import auto_setup
```
This will add commands to your render menu

## Keeping Both Submitters Available

While nk2dl is in alpha state, you may still wish to keep the default Thinkbox submitter handy. This is how we are keeping both the nk2dl and Thinkbox submitters available:

```python
import DeadlineNukeClient
menubar = nuke.menu("Nuke")
render_menu = menubar.addMenu('Render')
render_menu.addSeparator()
render_menu.addCommand("Submit Nuke to Deadline (Thinkbox)", DeadlineNukeClient.main, "Ctrl+F7")
from nk2dl import auto_setup
```