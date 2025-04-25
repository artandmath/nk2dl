"""Tests for the submission engine."""

import pytest
from unittest.mock import MagicMock, patch

from nk2dl.deadline.submission import SubmissionEngine
from nk2dl.common.framerange import FrameRange
from nk2dl.common.errors import DeadlineError, ValidationError


@pytest.fixture
def submission_engine():
    """Create a submission engine with a mocked connection."""
    with patch('nk2dl.deadline.submission.get_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_connection.submit_job.return_value = "mock-job-id"
        mock_get_connection.return_value = mock_connection
        engine = SubmissionEngine()
        yield engine


def test_submit_job(submission_engine):
    """Test basic job submission."""
    job_id = submission_engine.submit_job(
        job_name="Test Job",
        frames="1-10",
        nuke_script="/path/to/script.nk",
        output_path="/path/to/output.####.exr",
        priority=50,
        chunk_size=5
    )
    
    assert job_id == "mock-job-id"
    submission_engine.connection.submit_job.assert_called_once()
    
    # Extract the job_info from the call
    call_args = submission_engine.connection.submit_job.call_args[0]
    job_info = call_args[0]
    plugin_info = call_args[1]
    
    # Verify job info
    assert job_info["Name"] == "Test Job"
    assert job_info["Frames"] == "1-10"
    assert job_info["ChunkSize"] == 5
    assert job_info["Priority"] == 50
    
    # Verify plugin info
    assert plugin_info["SceneFile"] == "/path/to/script.nk"


def test_submit_write_nodes_as_separate_jobs(submission_engine):
    """Test submitting write nodes as separate jobs."""
    submission_engine.connection.submit_job.side_effect = ["job-1", "job-2", "job-3"]
    
    write_nodes = ["Write1", "Write2", "Write3"]
    job_ids = submission_engine.submit_write_nodes(
        job_name="Multi Write Test",
        nuke_script="/path/to/script.nk",
        write_nodes=write_nodes,
        frames="1-10",
        as_separate_jobs=True,
        set_dependencies=True
    )
    
    assert len(job_ids) == 3
    assert job_ids == ["job-1", "job-2", "job-3"]
    assert submission_engine.connection.submit_job.call_count == 3
    
    # Check that dependencies were set correctly
    call_args_list = submission_engine.connection.submit_job.call_args_list
    
    # First job should have no dependencies
    first_job_info = call_args_list[0][0][0]
    assert "JobDependencies" not in first_job_info
    
    # Second job should depend on the first
    second_job_info = call_args_list[1][0][0]
    assert second_job_info.get("JobDependencies") == "job-1"
    
    # Third job should depend on the second
    third_job_info = call_args_list[2][0][0]
    assert third_job_info.get("JobDependencies") == "job-2"


def test_submit_write_nodes_as_separate_tasks(submission_engine):
    """Test submitting write nodes as separate tasks."""
    job_id = submission_engine.submit_write_nodes(
        job_name="Multi Task Test",
        nuke_script="/path/to/script.nk",
        write_nodes=["Write1", "Write2", "Write3"],
        frames="1-10",
        as_separate_tasks=True
    )
    
    assert job_id == "mock-job-id"
    submission_engine.connection.submit_job.assert_called_once()
    
    # Extract the plugin_info from the call
    call_args = submission_engine.connection.submit_job.call_args[0]
    plugin_info = call_args[1]
    
    # Verify plugin info for separate tasks
    assert plugin_info["WriteNodesAsTasks"] == "True"
    assert plugin_info["SelectedNodes"] == "Write1,Write2,Write3"


def test_validation_error_for_contradictory_options(submission_engine):
    """Test that contradictory options raise a ValidationError."""
    with pytest.raises(ValidationError):
        submission_engine.submit_write_nodes(
            job_name="Invalid Options",
            nuke_script="/path/to/script.nk",
            write_nodes=["Write1", "Write2"],
            frames="1-10",
            as_separate_jobs=True,
            as_separate_tasks=True  # This contradicts as_separate_jobs
        ) 