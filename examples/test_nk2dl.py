import os
from nk2dl.nuke import submit_nuke_script

# Assumes Nuke 15.1 and 15.2 are the versions installed and we are running in Nuke 15.2.

# Set the root directoty to the correct path if running in the Nuke script editor.
root_dir = os.path.dirname(os.path.abspath(__file__))

# Submit the script with the dependencies example.
job_ids = submit_nuke_script(
    root_dir + "/dependencies_example.nk",
    copy_script=True,
    submit_copied_script=True,
    frame_range="input",
    chunk_size=50,
    priority=75,
    write_nodes_as_separate_jobs=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
    use_nodes_frame_list=True,
    continue_on_error=True,
    nuke_version="15.1"
)

# Print the job IDs.
print(f"Dependencies Example Job IDs: {job_ids}")

# Submit the script with the GSVs example.
import nuke
major = nuke.NUKE_VERSION_MAJOR
minor = nuke.NUKE_VERSION_MINOR

if major >= 15 and minor >= 2:
    job_ids = submit_nuke_script(
        root_dir + "/multishot_example.nk",
        copy_script=True,
        submit_copied_script=True,
        frame_range="input",
        chunk_size=50,
        priority=75,
        write_nodes_as_separate_jobs=True,
        render_order_dependencies=True,
        write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
        use_nodes_frame_list=True,
        continue_on_error=True, 
        graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
    )

    # Print the job IDs.
    print(f"Multishot Example Job IDs: {job_ids}")
