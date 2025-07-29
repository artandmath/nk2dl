# nk2dl
Nuke to Deadline. A python module for submitting nukescripts to Thinkbox Deadline via a Deadline web service or via the Deadline commandline. It features speed and quality of life improvements over the default Thinkbox submitter.

## Overview

- `nk2dl` is a python module for submitting nukescripts to Deadline from the Nuke python interpreter.
- `nk2dl` can also be used with other python interpereters when [The Foundry's](https://www.foundry.com/products/nuke-family/nuke) `nuke` module is available to the interpereter.

## Add-ons
- [`nk2dl gui`](https://github.com/artandmath/nk2dl-gui) is a panel for submitting nodes to Deadline from the Nuke GUI.
- [`nk2dl cli`](https://github.com/artandmath/nk2dl-cli) is a command line tool for submitting nukescripts to Deadline from a terminal. 

## Getting started

- Read the [documentation](http://artandmath.github.io/nk2dl) to get `nk2dl` up and running.

## This project is in Alpha

- The project is in alpha. We have been using it in a limited capacity in a production environment as a replacement to the Thinkbox submitter. We fall back to the Thinkbox submitter when missing a feature or something is broken.
- Graph Scope Variable functionality hasn't been tested in production.
- Interfaces to `nk2dl` python module and command line are subject to change.
- The `nk2dl cli` command line will often be out of step with the python module during development. The command line implementation may outright not work when out of step.
- The project has only been tested under Windows 11. Linux will be tested at a later date. MacOS at an even later date.
- The project has no plans to implement the Deadline Draft, Eddy, Vray or Frameserver features from the Thinbox submitter.
- nk2dl pulls a Nuke render license if it needs to call on the Nuke python module outside of a Nuke interactive sesssion.
- Connection to Deadline Web Service currently doesn't support SSL.
- The [roadmap](./ROADMAP.md) sets out the path to overcome the caveats and implement planned features.
- [The project is written using 10% supervision and 90% vibes.](https://www.youtube.com/watch?v=IACHfKmZMr8)

## Roadmap

[Public Roadmap](./ROADMAP.md)

## License

[MIT License](./LICENSE)

## Contributing

[Guidelines for contributing to the project](./docs/contributing.md)
