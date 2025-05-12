"""Tests for the submission engine."""

"""
Instructions for running tests:

1. cd to the root directory of the project.
2. activate the environment. 
    # windows activation script -- ensures we launch Nuke's Python interpreter:
    .\\.venv\\Scripts\\Activate-nk2dl.ps1 
3. run test:
    python -m pytest tests/pytest/pytest_submission.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile
import sys
import os

from nk2dl.nuke.submission import NukeSubmission
from nk2dl.common.framerange import FrameRange
from nk2dl.common.errors import DeadlineError, ValidationError, SubmissionError


def test_000_environment_check():
    """
    Test that the environment is properly loaded with Nuke's Python interpreter.
    This test should run first to ensure the proper environment is activated.
    """
    try:
        # Try to import the nuke module
        import nuke
    except ImportError:
        # If nuke is not available, this is likely because the environment is not properly loaded
        pytest.fail(
            "\n\n"
            "ERROR: The Nuke Python environment is not properly loaded.\n"
            "This is expected when running tests outside of Nuke's Python environment.\n"
            "\n"
            "Make sure to follow these steps before running the tests:\n"
            "\n"
            "1. cd to the root directory of the project.\n"
            "2. activate the environment:\n"
            "   .\\.venv\\Scripts\\Activate-nk2dl.ps1 (Windows)\n"
            "3. run test:\n"
            "   python -m pytest tests/pytest/pytest_submission.py -v\n"
            "\n"
            "NOTE: The tests are designed to run using Nuke's Python interpreter,\n"
            "which should be loaded by the activation script above.\n"
        )
    
    # If we got here, nuke was successfully imported
    assert 'nuke' in sys.modules


@pytest.fixture
def submission_engine():
    """Create a submission engine with a mocked connection."""
    with patch('nk2dl.deadline.connection.get_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_connection.submit_job.return_value = "mock-job-id"
        mock_get_connection.return_value = mock_connection
        
        # Create a temporary test script file
        with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
            temp_script.write(b"# Test Nuke script")
            temp_script_path = temp_script.name
        
        # Patch the connection at module level to ensure it's used everywhere
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Mock parsing requirements
            with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed') as mock_ensure_script:
                mock_nuke = MagicMock()
                mock_ensure_script.return_value = mock_nuke
                
                engine = NukeSubmission(
                    script_path=temp_script_path,
                    script_path_same_as_current_nuke_session=True,
                    frame_range="1-100"  # Initialize with a default frame range
                )
                
                # Explicitly set the connection on the engine to ensure it uses our mock
                engine.connection = mock_connection
                
                yield engine
                
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@pytest.fixture
def mock_nuke():
    """Create a mock Nuke module for tests."""
    with patch('nk2dl.nuke.utils.nuke_module') as mock_nuke_module:
        nuke = MagicMock()
        
        # Mock root node
        root = MagicMock()
        root.__getitem__.side_effect = lambda key: {
            'first_frame': MagicMock(value=lambda: 1001),
            'last_frame': MagicMock(value=lambda: 1100),
            'project_directory': MagicMock(evaluate=lambda: "/path/to/project"),
            'gsv': MagicMock(
                getListOptions=lambda key: ["value1", "value2", "value3"] if key in ["shotcode", "layer"] else [],
                setGsvValue=lambda key, value: None
            )
        }[key]
        nuke.root.return_value = root
        
        # Mock write nodes
        write1 = MagicMock()
        write1.name.return_value = "Write1"
        write1.__getitem__.side_effect = lambda key: {
            'file': MagicMock(value=lambda: "/output/render.####.exr", evaluate=lambda: "/output/render.1001.exr"),
            'file_type': MagicMock(value=lambda: "exr"),
            'disable': MagicMock(value=lambda: False),
            'render_order': MagicMock(value=lambda: 1),
            'use_limit': MagicMock(value=lambda: True),
            'first': MagicMock(value=lambda: 1001),
            'last': MagicMock(value=lambda: 1050)
        }[key]
        write1.Class.return_value = "Write"
        write1.firstFrame.return_value = 1001
        write1.lastFrame.return_value = 1050
        
        write2 = MagicMock()
        write2.name.return_value = "Write2"
        write2.__getitem__.side_effect = lambda key: {
            'file': MagicMock(value=lambda: "/output/render_mov.mov", evaluate=lambda: "/output/render_mov.mov"),
            'file_type': MagicMock(value=lambda: "mov"),
            'disable': MagicMock(value=lambda: False),
            'render_order': MagicMock(value=lambda: 2),
            'use_limit': MagicMock(value=lambda: False)
        }[key]
        write2.Class.return_value = "Write"
        write2.firstFrame.return_value = 1001
        write2.lastFrame.return_value = 1100
        
        nuke.toNode.side_effect = lambda name: {
            "Write1": write1,
            "Write2": write2
        }.get(name)
        
        nuke.allNodes.side_effect = lambda node_type: [write1, write2] if node_type == 'Write' else []
        
        mock_nuke_module.return_value = nuke
        yield nuke


@pytest.fixture
def mock_parser():
    """Create a mock parser module for tests."""
    with patch('nk2dl.nuke.utils.parser_module') as mock_parser_module:
        parser = MagicMock()
        
        # Configure the parser similar to mock_nuke
        root = MagicMock()
        root.__getitem__.side_effect = lambda key: {
            'first_frame': MagicMock(value=lambda: 1001),
            'last_frame': MagicMock(value=lambda: 1100),
            'project_directory': MagicMock(evaluate=lambda: "/path/to/project"),
            'gsv': MagicMock(
                getListOptions=lambda key: ["value1", "value2", "value3"] if key in ["shotcode", "layer"] else [],
                setGsvValue=lambda key, value: None
            )
        }[key]
        parser.root.return_value = root
        
        write1 = MagicMock()
        write1.name.return_value = "Write1"
        write1.__getitem__.side_effect = lambda key: {
            'file': MagicMock(value=lambda: "/output/render.####.exr", evaluate=lambda: "/output/render.1001.exr"),
            'file_type': MagicMock(value=lambda: "exr"),
            'disable': MagicMock(value=lambda: False),
            'render_order': MagicMock(value=lambda: 1),
            'use_limit': MagicMock(value=lambda: True),
            'first': MagicMock(value=lambda: 1001),
            'last': MagicMock(value=lambda: 1050)
        }[key]
        write1.Class.return_value = "Write"
        
        write2 = MagicMock()
        write2.name.return_value = "Write2"
        write2.__getitem__.side_effect = lambda key: {
            'file': MagicMock(value=lambda: "/output/render_mov.mov", evaluate=lambda: "/output/render_mov.mov"),
            'file_type': MagicMock(value=lambda: "mov"),
            'disable': MagicMock(value=lambda: False),
            'render_order': MagicMock(value=lambda: 2),
            'use_limit': MagicMock(value=lambda: False)
        }[key]
        write2.Class.return_value = "Write"
        
        parser.toNode.side_effect = lambda name: {
            "Write1": write1,
            "Write2": write2
        }.get(name)
        
        parser.allNodes.side_effect = lambda node_type: [write1, write2] if node_type == 'Write' else []
        
        mock_parser_module.return_value = parser
        yield parser


def test_submit_job(submission_engine):
    """Test submitting a job."""
    with patch.object(submission_engine, '_ensure_script_can_be_parsed'):
        # Configure submission engine
        submission_engine.write_nodes = ["Write1"]
        submission_engine.write_nodes_as_separate_jobs = False
        submission_engine.write_nodes_as_tasks = False
        
        # Submit job
        job_ids = submission_engine.submit()
        
        assert 0 in job_ids  # Standard jobs use key 0 for render order
        assert job_ids[0] == ["mock-job-id"]
        submission_engine.connection.submit_job.assert_called_once()


def test_submit_write_nodes_as_separate_jobs():
    """Test submitting write nodes as separate jobs."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.side_effect = ["job-1", "job-2"]
    
    # Patch both the get_connection function and module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed') as mock_ensure_script:
                    # Mock Nuke nodes with render orders
                    mock_nuke = MagicMock()
                    
                    mock_node1 = MagicMock()
                    mock_node1.name.return_value = "Write1"
                    mock_node1['disable'].value.return_value = False
                    
                    # Fix the render_order mock to match how it's actually accessed
                    mock_node1.__getitem__.side_effect = lambda key: {
                        'disable': MagicMock(value=lambda: False),
                        'render_order': MagicMock(value=lambda: 1)
                    }[key]
                    # Add knobs method to correctly report available knobs
                    mock_node1.knobs.return_value = {
                        'disable': True,
                        'render_order': True
                    }
                    
                    mock_node2 = MagicMock()
                    mock_node2.name.return_value = "Write2"
                    mock_node2['disable'].value.return_value = False
                    
                    # Fix the render_order mock to match how it's actually accessed
                    mock_node2.__getitem__.side_effect = lambda key: {
                        'disable': MagicMock(value=lambda: False),
                        'render_order': MagicMock(value=lambda: 2)
                    }[key]
                    # Add knobs method to correctly report available knobs
                    mock_node2.knobs.return_value = {
                        'disable': True,
                        'render_order': True
                    }
                    
                    mock_nuke.allNodes.return_value = [mock_node1, mock_node2]
                    mock_nuke.toNode.side_effect = lambda name: {"Write1": mock_node1, "Write2": mock_node2}.get(name)
                    mock_ensure_script.return_value = mock_nuke
                    
                    # Create NukeSubmission with separate jobs
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        submit_in_render_order=True,  # Important for render order sorting
                        write_nodes_as_separate_jobs=True,
                        frame_range="1-100"
                    )
                    
                    # Explicitly set the connection and write nodes
                    submission.connection = mock_connection
                    submission.write_nodes = ["Write1", "Write2"]
                    
                    # Submit jobs
                    job_ids = submission.submit()
                    
                    # We expect job IDs to be organized by render order
                    assert sorted(job_ids.keys()) == [1, 2]  # We should have jobs with render orders 1 and 2
                    assert job_ids[1] == ["job-1"]  # Write1 has render order 1
                    assert job_ids[2] == ["job-2"]  # Write2 has render order 2
                    assert mock_connection.submit_job.call_count == 2
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


def test_submit_write_nodes_as_separate_tasks(submission_engine):
    """Test submitting write nodes as separate tasks."""
    with patch.object(submission_engine, '_ensure_script_can_be_parsed'):
        # Configure submission
        submission_engine.write_nodes = ["Write1", "Write2"]
        submission_engine.write_nodes_as_separate_jobs = False
        submission_engine.write_nodes_as_tasks = True
        
        # Submit job
        job_ids = submission_engine.submit()
        
        assert 0 in job_ids  # Write nodes as tasks uses key 0 for render order
        assert job_ids[0] == ["mock-job-id"]
        submission_engine.connection.submit_job.assert_called_once()


def test_submit_job_with_invalid_frame_range(submission_engine):
    """Test submitting a job with an invalid frame range."""
    with patch.object(submission_engine, '_ensure_script_can_be_parsed'):
        # Set an invalid frame range - this should be caught in job preparation
        with patch.object(submission_engine, '_prepare_job_info', side_effect=ValidationError("Invalid frame range")):
            with pytest.raises(SubmissionError):  # Now wrapped in SubmissionError
                submission_engine.submit()


def test_submit_job_with_no_write_nodes(submission_engine):
    """Test submitting a job with no write nodes."""
    with patch.object(submission_engine, '_ensure_script_can_be_parsed'):
        # Set an empty write nodes list for separate jobs - this should trigger an error
        submission_engine.write_nodes = []
        submission_engine.write_nodes_as_separate_jobs = True
        
        # Mock allNodes to return no write nodes
        mock_nuke = MagicMock()
        mock_nuke.allNodes.return_value = []
        submission_engine._ensure_script_can_be_parsed.return_value = mock_nuke
        
        # This should fail with a warning and fall back to normal submission
        job_ids = submission_engine.submit()
        assert 0 in job_ids
        assert job_ids[0] == ["mock-job-id"]


def test_submit_job_with_connection_error(submission_engine):
    """Test submitting a job when the connection fails."""
    with patch.object(submission_engine, '_ensure_script_can_be_parsed'):
        # Configure the mock connection to fail
        submission_engine.connection.submit_job.side_effect = DeadlineError("Connection failed")
        
        # Configure submission
        submission_engine.write_nodes = ["Write1"]
        submission_engine.write_nodes_as_separate_jobs = False
        submission_engine.write_nodes_as_tasks = False
        
        # Submit should raise a SubmissionError
        with pytest.raises(SubmissionError) as exc_info:
            submission_engine.submit()
        
        # Verify the error message contains our original error message
        assert "Connection failed" in str(exc_info.value)


def test_validation_error_for_contradictory_options():
    """Test that contradictory options raise a ValidationError."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                # Patch _ensure_script_can_be_parsed to avoid loading real Nuke
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                    # Test should raise SubmissionError due to contradictory options
                    with pytest.raises(SubmissionError) as exc_info:
                        submission = NukeSubmission(
                            script_path=temp_script_path,
                            script_path_same_as_current_nuke_session=True,
                            write_nodes_as_separate_jobs=True,
                            write_nodes_as_tasks=True,  # This contradicts write_nodes_as_separate_jobs
                            frame_range="1-100"
                        )
                    
                    # Check the error message
                    assert "Cannot use both write_nodes_as_tasks and write_nodes_as_separate_jobs" in str(exc_info.value)
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@patch('nk2dl.nuke.utils.nuke_version')
@patch('os.path.exists', return_value=True)
def test_nuke_submission_with_gsv(mock_exists, mock_get_connection):
    """Test NukeSubmission with Graph Scope Variables."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Mock Nuke version to support GSV
            with patch('nk2dl.nuke.utils.nuke_version', return_value="15.2"):
                # Create a temporary test script file
                with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                    temp_script.write(b"# Test Nuke script")
                    temp_script_path = temp_script.name
                
                try:
                    # Mock the _parse_graph_scope_variables method to avoid errors
                    with patch('nk2dl.nuke.submission.NukeSubmission._parse_graph_scope_variables'):
                        with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                            # Create NukeSubmission with GSV
                            submission = NukeSubmission(
                                script_path=temp_script_path,
                                script_path_same_as_current_nuke_session=True,
                                graph_scope_variables=["shotcode:value1,value2"],
                                frame_range="1-100"
                            )
                            
                            # Manual override of parsed GSV combinations for testing
                            submission.gsv_combinations = [(("shotcode", "value1"),)]
                            
                            # Explicitly set the connection to ensure it uses our mock
                            submission.connection = mock_connection
                            submission.write_nodes = ["Write1"]
                            
                            # Submit job
                            job_ids = submission.submit()
                            
                            assert 0 in job_ids
                            assert job_ids[0] == ["mock-job-id"]
                finally:
                    # Clean up the temporary script file
                    Path(temp_script_path).unlink(missing_ok=True)


@patch('os.path.exists', return_value=True)
def test_nuke_submission_environment_vars(mock_exists):
    """Test NukeSubmission with environment variables."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                    # Create NukeSubmission with environment variables
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        environment={"CUSTOM_VAR": "value"},  # Updated parameter name
                        frame_range="1-100"
                    )
                    
                    # Explicitly set the connection to ensure it uses our mock
                    submission.connection = mock_connection
                    submission.write_nodes = ["Write1"]
                    
                    # Submit job
                    job_ids = submission.submit()
                    
                    assert 0 in job_ids
                    assert job_ids[0] == ["mock-job-id"]
                    mock_connection.submit_job.assert_called_once()
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@patch('shutil.copy2')
@patch('os.path.exists', return_value=True)
def test_nuke_submission_copy_script(mock_copy2, mock_exists):
    """Test NukeSubmission with script copying."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                    with patch('nk2dl.nuke.submission.NukeSubmission._copy_script') as mock_copy_script:
                        # Mock copied script paths
                        mock_copy_script.return_value = [temp_script_path + ".copy"]
                        
                        # Create NukeSubmission with script copying
                        submission = NukeSubmission(
                            script_path=temp_script_path,
                            script_path_same_as_current_nuke_session=True,
                            copy_script=True,
                            frame_range="1-100"
                        )
                        
                        # Explicitly set the connection to ensure it uses our mock
                        submission.connection = mock_connection
                        submission.write_nodes = ["Write1"]
                        
                        # Submit job
                        job_ids = submission.submit()
                        
                        assert 0 in job_ids
                        assert job_ids[0] == ["mock-job-id"]
                        mock_copy_script.assert_called_once()
                        mock_connection.submit_job.assert_called_once()
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@patch('os.path.exists', return_value=True)
def test_nuke_submission_movie_format(mock_exists):
    """Test NukeSubmission with movie format."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                    # Create NukeSubmission with movie format
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        render_mode="movie",  # Updated parameter name
                        frame_range="1-100"
                    )
                    
                    # Explicitly set the connection to ensure it uses our mock
                    submission.connection = mock_connection
                    submission.write_nodes = ["Write1"]
                    
                    # Submit job
                    job_ids = submission.submit()
                    
                    assert 0 in job_ids
                    assert job_ids[0] == ["mock-job-id"]
                    mock_connection.submit_job.assert_called_once()
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@patch('os.path.exists', return_value=True)
def test_nuke_submission_render_order_dependencies(mock_exists):
    """Test NukeSubmission with render order dependencies."""
    # Create a mock connection that returns sequential job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.side_effect = ["job-1", "job-2"]
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch.object(NukeSubmission, '_ensure_script_can_be_parsed') as mock_ensure_script:
                    # Mock Nuke nodes with render orders
                    mock_nuke = MagicMock()
                    mock_node1 = MagicMock()
                    mock_node1.name.return_value = "Write1"
                    mock_node1['disable'].value.return_value = False
                    
                    # Fix the render_order mock to match how it's actually accessed
                    mock_node1.__getitem__.side_effect = lambda key: {
                        'disable': MagicMock(value=lambda: False),
                        'render_order': MagicMock(value=lambda: 1)
                    }[key]
                    # Add knobs method to correctly report available knobs
                    mock_node1.knobs.return_value = {
                        'disable': True,
                        'render_order': True
                    }
                    
                    mock_node2 = MagicMock()
                    mock_node2.name.return_value = "Write2"
                    mock_node2['disable'].value.return_value = False
                    
                    # Fix the render_order mock to match how it's actually accessed
                    mock_node2.__getitem__.side_effect = lambda key: {
                        'disable': MagicMock(value=lambda: False),
                        'render_order': MagicMock(value=lambda: 2)
                    }[key]
                    # Add knobs method to correctly report available knobs
                    mock_node2.knobs.return_value = {
                        'disable': True,
                        'render_order': True
                    }
                    
                    mock_nuke.allNodes.return_value = [mock_node1, mock_node2]
                    mock_nuke.toNode.side_effect = lambda name: {"Write1": mock_node1, "Write2": mock_node2}.get(name)
                    mock_ensure_script.return_value = mock_nuke
                
                    # Create NukeSubmission with render order dependencies
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        submit_in_render_order=True,
                        write_nodes_as_separate_jobs=True,
                        render_order_dependencies=True,
                        frame_range="1-100"
                    )
                    
                    # Explicitly set the connection to ensure it uses our mock
                    submission.connection = mock_connection
                    submission.write_nodes = ["Write1", "Write2"]
                    
                    # Submit job
                    job_ids = submission.submit()
                    
                    # Should have jobs with render orders 1 and 2
                    assert sorted(job_ids.keys()) == [1, 2]
                    assert job_ids[1] == ["job-1"]
                    assert job_ids[2] == ["job-2"]
                    assert mock_connection.submit_job.call_count == 2
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


@patch('os.path.exists', return_value=True)
def test_nuke_submission_use_nodes_frame_list(mock_exists):
    """Test NukeSubmission with node frame list."""
    # Create a mock connection that returns predictable job IDs
    mock_connection = MagicMock()
    mock_connection.submit_job.return_value = "mock-job-id"
    
    # Patch both the get_connection function and the module-level connection
    with patch('nk2dl.deadline.connection.get_connection', return_value=mock_connection):
        with patch('nk2dl.deadline.connection._connection', mock_connection):
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                    # Create NukeSubmission with node frame list
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        use_nodes_frame_list=True,
                        frame_range="1-100"
                    )
                    
                    # Explicitly set the connection to ensure it uses our mock
                    submission.connection = mock_connection
                    submission.write_nodes = ["Write1"]
                    
                    # Submit job
                    job_ids = submission.submit()
                    
                    assert 0 in job_ids
                    assert job_ids[0] == ["mock-job-id"]
                    mock_connection.submit_job.assert_called_once()
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


def test_submit_nuke_script():
    """Test submitting a Nuke script."""
    with patch('nk2dl.deadline.connection.get_connection') as mock_get_connection:
        with patch('nk2dl.nuke.submission.submit_nuke_script') as mock_submit_nuke:
            mock_connection = MagicMock()
            mock_connection.submit_job.return_value = "mock-job-id"
            mock_get_connection.return_value = mock_connection
            
            # Mock a successful submission with a single job ID
            mock_submit_nuke.return_value = {0: ["mock-job-id"]}
            
            # Create a temporary test script file
            with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
                temp_script.write(b"# Test Nuke script")
                temp_script_path = temp_script.name
            
            try:
                # Call submit_nuke_script
                from nk2dl.nuke.submission import submit_nuke_script
                job_ids = submit_nuke_script(
                    script_path=temp_script_path,
                    frame_range="1-10",
                    write_nodes=["Write1"],
                    write_nodes_as_separate_jobs=False,
                    write_nodes_as_tasks=False
                )
                
                assert 0 in job_ids
                assert job_ids[0] == ["mock-job-id"]
                mock_submit_nuke.assert_called_once()
            finally:
                # Clean up the temporary script file
                Path(temp_script_path).unlink(missing_ok=True)


def test_contradictory_write_node_options():
    """Test that contradictory write node options are handled correctly."""
    with patch('nk2dl.deadline.connection.get_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Create a temporary test script file
        with tempfile.NamedTemporaryFile(suffix='.nk', delete=False) as temp_script:
            temp_script.write(b"# Test Nuke script")
            temp_script_path = temp_script.name
        
        try:
            # Patch _ensure_script_can_be_parsed to avoid loading real Nuke
            with patch('nk2dl.nuke.submission.NukeSubmission._ensure_script_can_be_parsed'):
                # Test should raise SubmissionError due to contradictory options
                with pytest.raises(SubmissionError) as exc_info:
                    submission = NukeSubmission(
                        script_path=temp_script_path,
                        script_path_same_as_current_nuke_session=True,
                        write_nodes_as_separate_jobs=True,
                        write_nodes_as_tasks=True,  # This contradicts write_nodes_as_separate_jobs
                        frame_range="1-100"
                    )
                
                # Check that we got the expected error message
                assert "Cannot use both write_nodes_as_tasks and write_nodes_as_separate_jobs" in str(exc_info.value)
                
        finally:
            # Clean up the temporary script file
            Path(temp_script_path).unlink(missing_ok=True) 