#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test file for the nk2dl module that submits Nuke scripts to Deadline.
This demonstrates submitting jobs with different configurations.
Run from the root directory with: python tests/test_nk2dl_module.py
Copy and paste the contents of the file into a python interpreter if it fails to run from the command line.
"""

from nk2dl.nuke import submit_nuke_script

def main():
    # First job submission - basic configuration with separate write node jobs
    job_id1 = submit_nuke_script(
        "examples/renderWithDeadline.nk",
        frame_range="input",
        chunk_size=25,
        priority=60,
        use_nuke_x=False,
        render_threads=0,
        use_gpu=True,
        write_nodes_as_separate_jobs=True,
        render_order_dependencies=True,
        batch_name="Test Batch - without GSVs",
        write_nodes=["Write1", "Write2", "Write3", "Write4", "Write5"],
        use_nodes_frame_list=True,
        continue_on_error=True
    )
    print(f"Submitted first job with ID: {job_id1}")
    # Second job submission - with graph scope variables
    job_id2 = submit_nuke_script(
        "examples/renderWithDeadlineGSVs.nk",
        frame_range="input",
        chunk_size=50,
        priority=40,
        use_nuke_x=True,
        render_threads=16,
        use_gpu=False,
        write_nodes_as_separate_jobs=True,
        render_order_dependencies=True,
        batch_name="Test Batch - with GSVs",
        write_nodes=["Write1", "Write2", "Write3", "Write4", "Write5", "Write6"],
        use_nodes_frame_list=True,
        continue_on_error=True,
        graph_scope_variables=["shotcode:ABC_0010,ABC_0020", "res:wh,proxy"]
    )
    print(f"Submitted second job with ID: {job_id2}")

if __name__ == "__main__":
    main() 