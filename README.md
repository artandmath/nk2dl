# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline.

## Overview

`nk2dl` is a python module for submitting nukescripts to Deadline from the Nukw python interpreter.
`nk2dl` can also be used with other python interpereters if [The Foundry's](https://www.foundry.com/products/nuke-family/nuke) `nuke` module is available to the interpereter.

## Add-ons
- [`nk2dl gui`](https://github.com/artandmath/nk2dl-gui) is a panel for submitting nodes to Deadline from the Nuke GUI.
- [`nk2dl cli`](https://github.com/artandmath/nk2dl-cli) is a commandline interface for submitting nukescripts to Deadline from a terminal. 

## Documentation

- [Installation, Configuration, and Tests](./docs/installation.md)
- [Quickstart Usage Guide](./docs/quickstart.md)
- [Configuration Details](./docs/config.md)
- [Deadline Connection](./docs/deadline_connection.md)
- [Nuke Submission](./docs/nuke_submission.md)
- [Feature parity table](./docs/feature_parity.md)

## Getting started

- Follow the steps in the [Installation, Configuration, and Tests](./docs/installation.md) doc to get `nk2dl` up and running.

## Caveats

- The project is in alpha. We have been using it in a limited capacity in a production environment as a replacement to the Thinkbox submitter. We fall back to the Thinkbox submitter when missing a feature or something is broken.
- Graph Scope Variable functionality hasn't been tested in production.
- Interfaces to `nk2dl python` module and command line are subject to change.
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
