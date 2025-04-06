"""Tests for the Deadline connection module."""

import os
import pytest
from unittest.mock import MagicMock, patch

from nk2dl.common.config import Config
from nk2dl.common.errors import DeadlineError
from nk2dl.deadline.connection import DeadlineConnection

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('nk2dl.deadline.connection.config') as mock:
        mock.get.side_effect = lambda key, default=None: {
            'deadline.use_web_service': False,
            'deadline.host': 'testhost',
            'deadline.port': 8081,
            'deadline.ssl': False,
            'deadline.command_path': '/path/to/deadlinecommand'
        }.get(key, default)
        yield mock

def test_command_line_connection(mock_config):
    """Test command-line connection initialization."""
    with patch('os.path.exists') as mock_exists, \
         patch('subprocess.Popen') as mock_popen:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'/repo/path\n', b'')
        mock_popen.return_value = mock_process
        
        # Create connection
        conn = DeadlineConnection()
        assert not conn.use_web_service
        assert conn._command_path == '/path/to/deadlinecommand'
        
        # Initialize connection
        conn.ensure_connected()
        assert conn._repository_path == '/repo/path'

def test_web_service_connection(mock_config):
    """Test web service connection initialization."""
    with patch('nk2dl.deadline.connection.config') as mock_config, \
         patch.dict('sys.modules', {'Deadline': MagicMock(), 'Deadline.DeadlineConnect': MagicMock()}):
        
        # Setup mocks
        mock_config.get.side_effect = lambda key, default=None: {
            'deadline.use_web_service': True,
            'deadline.host': 'testhost',
            'deadline.port': 8081,
            'deadline.ssl': False
        }.get(key, default)
        
        mock_client = MagicMock()
        mock_client.Groups.GetGroupNames.return_value = ['group1', 'group2']
        
        with patch('Deadline.DeadlineConnect.DeadlineCon', return_value=mock_client):
            # Create connection
            conn = DeadlineConnection()
            assert conn.use_web_service
            assert conn._web_client is None  # Not initialized yet
            
            # Initialize connection
            conn.ensure_connected()
            assert conn._web_client is not None
            
            # Test group retrieval
            groups = conn.get_groups()
            assert groups == ['group1', 'group2']

def test_command_line_not_found(mock_config):
    """Test error when deadlinecommand is not found."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        
        with pytest.raises(DeadlineError) as exc_info:
            DeadlineConnection()
        
        assert "Could not find deadlinecommand" in str(exc_info.value)

def test_web_service_import_error(mock_config):
    """Test error when Deadline web service module cannot be imported."""
    with patch('nk2dl.deadline.connection.config') as mock_config:
        mock_config.get.side_effect = lambda key, default=None: {
            'deadline.use_web_service': True
        }.get(key, default)
        
        with pytest.raises(DeadlineError) as exc_info:
            DeadlineConnection()
        
        assert "Failed to import Deadline Web Service API" in str(exc_info.value)

def test_get_groups_command_line(mock_config):
    """Test getting groups via command-line."""
    with patch('os.path.exists') as mock_exists, \
         patch('subprocess.Popen') as mock_popen:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.communicate.side_effect = [
            (b'/repo/path\n', b''),  # For init
            (b'group1\ngroup2\n', b'')  # For get_groups
        ]
        mock_popen.return_value = mock_process
        
        # Create connection and test
        conn = DeadlineConnection()
        groups = conn.get_groups()
        assert groups == ['group1', 'group2']

def test_submit_job_command_line(mock_config):
    """Test job submission via command line."""
    with patch('os.path.exists') as mock_exists, \
         patch('subprocess.Popen') as mock_popen, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'JobID=12345\nSuccess\n', b'')
        mock_popen.return_value = mock_process
        
        # Mock temp files
        mock_job_file = MagicMock()
        mock_job_file.__enter__.return_value = mock_job_file
        mock_job_file.name = '/tmp/job_info.job'
        
        mock_plugin_file = MagicMock()
        mock_plugin_file.__enter__.return_value = mock_plugin_file
        mock_plugin_file.name = '/tmp/plugin_info.job'
        
        mock_temp.side_effect = [mock_job_file, mock_plugin_file]
        
        # Create connection and submit job
        conn = DeadlineConnection()
        job_info = {
            'Plugin': 'Nuke',
            'Name': 'Test Job',
            'Frames': '1-10'
        }
        plugin_info = {
            'Version': '13.0',
            'SceneFile': '/path/to/scene.nk'
        }
        
        job_id = conn.submit_job(job_info, plugin_info)
        assert job_id == '12345'
        
        # Verify temp files were written correctly
        mock_job_file.write.assert_any_call('Plugin=Nuke\n')
        mock_job_file.write.assert_any_call('Name=Test Job\n')
        mock_job_file.write.assert_any_call('Frames=1-10\n')
        
        mock_plugin_file.write.assert_any_call('Version=13.0\n')
        mock_plugin_file.write.assert_any_call('SceneFile=/path/to/scene.nk\n')

def test_submit_job_web_service(mock_config):
    """Test job submission via web service."""
    with patch('nk2dl.deadline.connection.config') as mock_config, \
         patch.dict('sys.modules', {'Deadline': MagicMock(), 'Deadline.DeadlineConnect': MagicMock()}), \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        # Setup mocks
        mock_config.get.side_effect = lambda key, default=None: {
            'deadline.use_web_service': True,
            'deadline.host': 'testhost',
            'deadline.port': 8081,
            'deadline.ssl': False
        }.get(key, default)
        
        mock_client = MagicMock()
        mock_client.Jobs.SubmitJob.return_value = '12345'
        
        # Mock temp files
        mock_job_file = MagicMock()
        mock_job_file.__enter__.return_value = mock_job_file
        mock_job_file.name = '/tmp/job_info.job'
        
        mock_plugin_file = MagicMock()
        mock_plugin_file.__enter__.return_value = mock_plugin_file
        mock_plugin_file.name = '/tmp/plugin_info.job'
        
        mock_temp.side_effect = [mock_job_file, mock_plugin_file]
        
        with patch('Deadline.DeadlineConnect.DeadlineCon', return_value=mock_client):
            # Create connection and submit job
            conn = DeadlineConnection()
            conn.ensure_connected()
            
            job_info = {
                'Plugin': 'Nuke',
                'Name': 'Test Job',
                'Frames': '1-10'
            }
            plugin_info = {
                'Version': '13.0',
                'SceneFile': '/path/to/scene.nk'
            }
            
            job_id = conn.submit_job(job_info, plugin_info)
            assert job_id == '12345'
            
            # Verify temp files were written correctly
            mock_job_file.write.assert_any_call('Plugin=Nuke\n')
            mock_job_file.write.assert_any_call('Name=Test Job\n')
            mock_job_file.write.assert_any_call('Frames=1-10\n')
            
            mock_plugin_file.write.assert_any_call('Version=13.0\n')
            mock_plugin_file.write.assert_any_call('SceneFile=/path/to/scene.nk\n')
            
            # Verify web service was called correctly
            mock_client.Jobs.SubmitJob.assert_called_once_with('/tmp/job_info.job', '/tmp/plugin_info.job')

def test_submit_job_command_line_error(mock_config):
    """Test error handling for command line job submission."""
    with patch('os.path.exists') as mock_exists, \
         patch('subprocess.Popen') as mock_popen, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'Error: Failed to submit job\n', b'')
        mock_popen.return_value = mock_process
        
        # Mock temp files
        mock_job_file = MagicMock()
        mock_job_file.__enter__.return_value = mock_job_file
        mock_job_file.name = '/tmp/job_info.job'
        
        mock_plugin_file = MagicMock()
        mock_plugin_file.__enter__.return_value = mock_plugin_file
        mock_plugin_file.name = '/tmp/plugin_info.job'
        
        mock_temp.side_effect = [mock_job_file, mock_plugin_file]
        
        # Create connection and attempt to submit job
        conn = DeadlineConnection()
        job_info = {'Plugin': 'Nuke', 'Name': 'Test Job'}
        plugin_info = {'Version': '13.0'}
        
        with pytest.raises(DeadlineError) as exc_info:
            conn.submit_job(job_info, plugin_info)
        assert "No job ID found in submission output" in str(exc_info.value)

def test_submit_job_web_service_error(mock_config):
    """Test error handling for web service job submission."""
    with patch('nk2dl.deadline.connection.config') as mock_config, \
         patch.dict('sys.modules', {'Deadline': MagicMock(), 'Deadline.DeadlineConnect': MagicMock()}), \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        # Setup mocks
        mock_config.get.side_effect = lambda key, default=None: {
            'deadline.use_web_service': True,
            'deadline.host': 'testhost',
            'deadline.port': 8081,
            'deadline.ssl': False
        }.get(key, default)
        
        mock_client = MagicMock()
        mock_client.Jobs.SubmitJob.side_effect = Exception("Failed to submit job")
        
        # Mock temp files
        mock_job_file = MagicMock()
        mock_job_file.__enter__.return_value = mock_job_file
        mock_job_file.name = '/tmp/job_info.job'
        
        mock_plugin_file = MagicMock()
        mock_plugin_file.__enter__.return_value = mock_plugin_file
        mock_plugin_file.name = '/tmp/plugin_info.job'
        
        mock_temp.side_effect = [mock_job_file, mock_plugin_file]
        
        with patch('Deadline.DeadlineConnect.DeadlineCon', return_value=mock_client):
            # Create connection and attempt to submit job
            conn = DeadlineConnection()
            conn.ensure_connected()
            
            job_info = {'Plugin': 'Nuke', 'Name': 'Test Job'}
            plugin_info = {'Version': '13.0'}
            
            with pytest.raises(DeadlineError) as exc_info:
                conn.submit_job(job_info, plugin_info)
            assert "Failed to submit job via web service" in str(exc_info.value) 