""" usage
```bash
cd /path/to/nk2dl-0.1.x-alpha/
./.venv/Scripts/Activate-nk2dl.ps1
python ./tests/test_nk2dl.py
``` 
"""# Assumes Nuke 15.1 and 15.2 are the versions installed and we are running in Nuke 15.2.
# Set the root directoty to the correct path if running in the Nuke script editor.
import os
root_dir = os.path.dirname(os.path.abspath(__file__))

from nk2dl import submit_nuke_script
from unittest.mock import patch
from pathlib import Path


# Submit the script with the dependencies example.
job_ids = submit_nuke_script(
    root_dir + "/nukescripts/test_dependencies.nk",
    copy_script=True,
    submit_copied_script=True,
    frames="input",
    chunk_size=50,
    priority=75,
    write_nodes_as_separate_jobs=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
    use_node_frame_list=True,
    continue_on_error=True,
    nuke_version="15.1",
    use_current_environment=False,
    environment_keys=["OCIO","PATH"],
    environment={"TEST": "TEST", "TEST2": "TEST2", "TEST3": "TEST3"},
    omit_environment_keys=["TEST2"]
)

# Print the job IDs.
print(f"Dependencies Example Job IDs: {job_ids}")

# Submit the script with the GSVs example.
import nuke
major = nuke.NUKE_VERSION_MAJOR
minor = nuke.NUKE_VERSION_MINOR

if major >= 15 and minor >= 2:
    job_ids = submit_nuke_script(
        root_dir + "/nukescripts/test_multishot.nk",
        copy_script=True,
        submit_copied_script=True,
        frames="input",
        chunk_size=50,
        priority=75,
        write_nodes_as_separate_jobs=True,
        render_order_dependencies=True,
        nuke_version="15.2",
        write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
        use_node_frame_list=True,
        continue_on_error=True, 
        graph_scope_variables=["shotcode:ABC_0010,ABC_0020"],
        use_current_environment=False,
        environment_keys=["OCIO","PATH"],
        environment={"TEST": "TEST", "TEST2": "TEST2", "TEST3": "TEST3"},
        omit_environment_keys=["TEST2"]
    )

    # Print the job IDs.
    print(f"Multishot Example Job IDs: {job_ids}")
