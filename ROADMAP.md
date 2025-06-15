# NK2DL Public Roadmap

This roadmap outlines the planned development path for the Nuke to Deadline Submitter (NK2DL) project.

## Current Status

NK2DL is currently in active development with core CLI functionality established. The project aims to provide a modern, maintainable replacement for the Thinkbox Deadline submitter for Nuke.

## Roadmap

- [X] Feature parity with Thinkbox submitter for the NK2DL Python module
- [X] Support for submitting environment variables with jobs (implemented in v0.1.4-alpha)
- [X] Implement pre and post submit hooks
- [ ] Update tests for core functionality
- [ ] Production testing of Python module
- [ ] Feature parity between CLI and Python module
- [ ] Simplify the install process
- [X] Submission offloader (build job tree on a farm process)
- [X] Basic Nuke menu implementation
- [ ] Basic Nuke panel implementation
- [ ] Production testing of basic panel
- [ ] Advanced UI features and support nodes
- [ ] Production testing of advanced features and support nodes

## Possible Future Expansion

- [ ] Threaded submissions to further improve speed of large submissions
- [ ] De-couple Deadline connection code
- [ ] De-couple CLI code
- [ ] De-couple GUI, possibly in a way that the same GUI can be used for any farm backend (Tractor, OpenCue, Qube etc)
- [ ] Create replacement for functions used of the Nuke python module to make it cheaper/faster/simpler to use nk2dl anywhere in the pipeline.
- [ ] Standalone GUI
- [ ] Deadline monitor lite - Nuke GUI panel indicating progress for the jobs of the currently open script.
- [ ] Integration wih other pipeline tools
- [ ] Refactor with future AI coding tools

---

This roadmap is subject to change based on user feedback and production requirements. The project prioritizes stability and reliability for production environments. 