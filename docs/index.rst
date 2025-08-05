Nuke to Deadline (nk2dl) Documentation
=====================================

Welcome to the documentation for **nk2dl**, a pure Python library for submitting Nuke scripts to Thinkbox Deadline render farms.

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   quickstart
   config
   deadline_connection
   nuke_submission
   feature_parity
   faq
   tests
   troubleshooting
   contributing

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/modules

Getting Started
---------------

Follow these steps to get up and running with nk2dl:

1. **Installation**: Follow the :doc:`installation` guide to get nk2dl installed and configured.
2. **Quick Start**: Follow the :doc:`quickstart` guide to verify that nk2dl is up and running.
3. **Configuration**: Review the :doc:`config` documentation to customize nk2dl for your pipeline.

Optional Add-ons
-----------------

* **GUI Components**: Visit the `nk2dl-gui repository <https://github.com/artandmath/nk2dl-gui>`_ to install the GUI components for Nuke.
* **Command Line Tool**: Visit the `nk2dl-cli repository <https://github.com/artandmath/nk2dl-cli>`_ to install the command line interface.

Key Features
------------

* Pure Python implementation - no dependencies on Nuke runtime
* Comprehensive Deadline job submission and management
* Flexible configuration system
* Support for complex render dependencies and frame ranges
* Extensive logging and error handling
* VFX Reference Platform compliant

Quick Example
-------------

.. code-block:: python

   from nk2dl import submit_nuke_script
   
   # Submit a Nuke script to Deadline
   job_id = submit_nuke_script(
       script_path="/path/to/your/script.nk",
       pool="primary",
       group="nuke",
       priority=50
   )
   
   print(f"Submitted job: {job_id}")

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`