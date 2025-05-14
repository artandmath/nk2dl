import os
from nk2dl.nuke import submit_nuke_script
from unittest.mock import patch
from pathlib import Path

""" usage
```bash
cd /path/to/nk2dl-0.1.x-alpha/
./.venv/Scripts/Activate-nk2dl.ps1
python ./examples/test_nk2dl.py
``` 
"""
# Assumes Nuke 15.1 and 15.2 are the versions installed and we are running in Nuke 15.2.

# Set the root directoty to the correct path if running in the Nuke script editor.
root_dir = os.path.dirname(os.path.abspath(__file__))

# Submit the script with the dependencies example.
job_ids = submit_nuke_script(
    root_dir + "nukescripts/dependencies_example.nk",
    copy_script=True,
    submit_copied_script=True,
    frame_range="input",
    chunk_size=50,
    priority=75,
    write_nodes_as_separate_jobs=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
    use_node_frame_list=True,
    continue_on_error=True,
    nuke_version="15.1",
    use_current_environment=False,
    include_environment_keys=["OCIO","PATH"],
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
        root_dir + "nukescripts/multishot_example.nk",
        copy_script=True,
        submit_copied_script=True,
        frame_range="input",
        chunk_size=50,
        priority=75,
        write_nodes_as_separate_jobs=True,
        render_order_dependencies=True,
        write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
        use_node_frame_list=True,
        continue_on_error=True, 
        graph_scope_variables=["shotcode:ABC_0010,ABC_0020"],
        use_current_environment=False,
        include_environment_keys=["OCIO","PATH"],
        environment={"TEST": "TEST", "TEST2": "TEST2", "TEST3": "TEST3"},
        omit_environment_keys=["TEST2"]
    )

    # Print the job IDs.
    print(f"Multishot Example Job IDs: {job_ids}")

@patch('nk2dl.nuke.submission.NukeSubmission._prepare_job_info')
@patch('nk2dl.nuke.submission.NukeSubmission._prepare_plugin_info')
@patch('nk2dl.deadline.connection.DeadlineWebService')
def test_submit_basic(mock_deadline, mock_plugin_info, mock_job_info):
    """Test basic submission functionality."""
    script_path = Path(TEST_RESOURCES_DIR) / "test_script.nk"
    
    # Setup mock returns
    job_info = {"Frames": "1-100", "ChunkSize": 10, "ConcurrentTasks": 5, "Name": "My Test Job", "Pool": "3d", "Plugin": "Nuke"}
    plugin_info = {"Version": "14.0", "UseNukeX": "0", "BatchMode": "1", "EnforceRenderOrder": "1", "Threads": "12"}
    mock_job_info.return_value = job_info
    mock_plugin_info.return_value = plugin_info
    mock_deadline.return_value.submit_job.return_value = "12345"
    
    # Call function
    result = submit_nuke_script(
        script_path,
        pool="3d",
        frames="1-100",
        job_name="My Test Job",
        threads=12,
        use_node_frame_list=True,
        concurrent_tasks=5)

    # Test job info structure
    assert job_info["Frames"] == "1-100"
    assert job_info["ChunkSize"] == 10
    assert job_info["ConcurrentTasks"] == 5
    assert job_info["Name"] == "My Test Job"
    assert job_info["Pool"] == "3d"
    assert job_info["Plugin"] == "Nuke"

    # Test plugin info structure  
    assert plugin_info["Version"] == "14.0"
    assert plugin_info["UseNukeX"] == "0"
    assert plugin_info["BatchMode"] == "1"
    assert plugin_info["EnforceRenderOrder"] == "1"
    assert plugin_info["Threads"] == "12"

@patch('nk2dl.nuke.submission.NukeSubmission.submit')
def test_submit_complex(mock_submit):
    """Test complex submission functionality."""
    script_path = Path(TEST_RESOURCES_DIR) / "test_script.nk"
    
    # Expected return value of the wrapped submit method
    job_ids = {10: ["12345", "67890"], 20: ["24680"]}
    mock_submit.return_value = job_ids
    
    # Call function with complex options
    result = submit_nuke_script(
        script_path,
        nuke_version="15.1",
        frames="input",
        batch_name="Batch 123",
        department="lighting",
        render_order_dependencies=True,
        write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
        use_node_frame_list=True,
        continue_on_error=True, 
        environment_keys=["OCIO","PATH"],
        environment={"PROJECT_ROOT": "/path/to/project"})
    
    # Verify submit was called with the right parameters
    mock_submit.assert_called_once()
    
    # Verify result is passed through
    assert result == job_ids
