Nuke to Deadline (nk2dl) API Documentation
==========================================

Welcome to the API documentation for **nk2dl**, a pure Python library for submitting Nuke scripts to Thinkbox Deadline render farms.

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/modules

Quick Example
-------------

.. code-block:: python

   from nk2dl import submit_nuke_script
   
   # Submit a Nuke script to Deadline
   job_results = submit_nuke_script(
       script_path="/path/to/your/script.nk",
       pool="primary",
       group="nuke",
       priority=50
   )
   
   # Extract job ID from the first job result
   job_id = job_results[0]["job_id"]
   print(f"Submitted job: {job_id}")
   
   # Or print all job information
   for job in job_results:
       print(f"Job ID: {job['job_id']}, Render Order: {job['render_order']}")

Key Features
------------

* Comprehensive Deadline job submission
* Flexible configuration system
* Support for complex render dependencies and frame ranges
* Extensive logging and error handling
* VFX Reference Platform compliant

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`