# nk2dl
Welcome to `nk2dl` (aka Nuke to Deadline).
- `nk2dl` is a python module for submitting nukescripts to Thinkbox Deadline via a Deadline web service or via the Deadline commandline.
- `nk2dl` features speed and quality of life improvements over the default Thinkbox submitter.
- `nk2dl` can also be used with other python interpreters [where `nuke` module is available to the interpreter](https://learn.foundry.com/nuke/developers/121/pythondevguide/nuke_as_python_module.html).

## Optional Add-ons
- [`nk2dl-gui`](https://github.com/artandmath/nk2dl-gui) is a panel for submitting nodes to Deadline from the Nuke GUI.
- [`nk2dl-cli`](https://github.com/artandmath/nk2dl-cli) is a command line tool for submitting nukescripts to Deadline from a terminal. 

## Getting started

- Read the [documentation](http://artandmath.github.io/nk2dl) to get `nk2dl` up and running.

## Caveats

- We have been using `nk2dl` in a production environment as a replacement to the Thinkbox submitter. We fall back to the Thinkbox submitter when missing a feature or something is broken, although months have passed since we've had to fall back.
- Graph Scope Variable functionality hasn't been tested in production.
- Interfaces to `nk2dl` python module are subject to change.
- The project has only been tested under Windows 11. Linux will be tested at a later date. MacOS at an even later date.
- The project has no plans to implement the Deadline Draft, Eddy, Vray or Frameserver features from the Thinbox submitter.
- `nk2dl` pulls a Nuke render license if it needs to call on the Nuke python module outside of a Nuke interactive session.
- Connection to Deadline Web Service using SSL has yet to be tested.
- The [roadmap](./ROADMAP.md) sets out the path to overcome the caveats and implement planned features.
- [The project is written using 10% supervision and 90% vibes.](https://www.youtube.com/watch?v=IACHfKmZMr8)

## Roadmap

[Public Roadmap](./ROADMAP.md)

## License

[MIT License](./LICENSE)

## Contributing

[Guidelines for contributing to the project](./docs/contributing.md)
