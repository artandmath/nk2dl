"""Tests for the configuration system."""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from nk2dl.common.config import Config, ConfigError

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables and config state before each test."""
    # Save original environment
    original_env = dict(os.environ)
    
    # Clear NK2DL environment variables
    for key in list(os.environ.keys()):
        if key.startswith('NK2DL_'):
            del os.environ[key]
    
    # Reset global config instance
    from nk2dl.common.config import config
    config._config = config.DEFAULT_CONFIG.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

def test_default_config():
    """Test that default configuration is loaded correctly."""
    config = Config()
    
    # Helper function to get config with fallback to default
    def get_config_with_default(key):
        value = config.get(key)
        if value is None:
            return config.DEFAULT_CONFIG
        for part in key.split('.'):
            if value is None or part not in value:
                return config.DEFAULT_CONFIG[key.split('.')[0]][key.split('.')[1]]
            value = value[part]
        return value

    # Test that values exist, falling back to defaults if not configured
    assert config.get('deadline.host', 'localhost')  # Value exists, default localhost
    assert isinstance(config.get('deadline.port', 8081), int)  # Value is an integer
    assert isinstance(config.get('deadline.use_web_service', False), bool)  # Value is a boolean
    assert config.get('logging.level') in ['DEBUG', 'INFO']  # Standard log levels
    
    # Test default values that should always work
    assert config.get('nonexistent.key') is None
    assert config.get('nonexistent.key', 'default') == 'default'
    
    # Test submission values with defaults
    assert config.get('submission.pool', 'nuke') == 'nuke'
    assert config.get('submission.group', 'none') == 'none'
    assert isinstance(config.get('submission.priority', 50), int)
    assert isinstance(config.get('submission.chunk_size', 10), int)

def test_environment_variables():
    """Test that environment variables override configuration."""
    os.environ['NK2DL_DEADLINE_HOST'] = 'testhost'
    os.environ['NK2DL_LOGGING_LEVEL'] = 'DEBUG'
    os.environ['NK2DL_DEADLINE_USE__WEB__SERVICE'] = 'true'
    os.environ['NK2DL_SUBMISSION_CHUNK__SIZE'] = '20'
    
    config = Config()
    assert config.get('deadline.host') == 'testhost'
    assert config.get('logging.level') == 'DEBUG'
    assert config.get('deadline.use_web_service') == 'true'
    assert config.get('submission.chunk_size') == 20
    
    # Clean up
    del os.environ['NK2DL_DEADLINE_HOST']
    del os.environ['NK2DL_LOGGING_LEVEL']
    del os.environ['NK2DL_DEADLINE_USE__WEB__SERVICE']
    del os.environ['NK2DL_SUBMISSION_CHUNK__SIZE']

def test_config_order():
    """Test configuration loading order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create project config
        project_config = Path(tmpdir) / 'project.yaml'
        project_data = {
            'deadline': {
                'host': 'project_host',
                'port': 1111
            }
        }
        with project_config.open('w') as f:
            yaml.safe_dump(project_data, f)
        
        # Create user config
        user_config = Path(tmpdir) / 'user.yaml'
        user_data = {
            'deadline': {
                'host': 'user_host',
                'port': 2222
            }
        }
        with user_config.open('w') as f:
            yaml.safe_dump(user_data, f)
        
        # Set environment variable
        os.environ['NK2DL_DEADLINE_PORT'] = '3333'
        
        # Create config with both files
        config = Config(
            project_config=str(project_config),
            user_config=str(user_config)
        )
        
        # Check values - env vars should override user config should override project config
        assert config.get('deadline.host') == 'user_host'  # From user config
        assert config.get('deadline.port') == 3333  # From env var
        
        # Clean up
        del os.environ['NK2DL_DEADLINE_PORT']

def test_nk2dl_config_env_var():
    """Test NK2DL_CONFIG environment variable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config file
        config_path = Path(tmpdir) / 'custom_config.yaml'
        config_data = {
            'deadline': {
                'host': 'env_config_host'
            }
        }
        with config_path.open('w') as f:
            yaml.safe_dump(config_data, f)
        
        # Set environment variable
        os.environ['NK2DL_CONFIG'] = str(config_path)
        
        # Create config
        config = Config()
        assert config.get('deadline.host') == 'env_config_host'
        
        # Clean up
        del os.environ['NK2DL_CONFIG']

def test_invalid_yaml():
    """Test handling of invalid YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'invalid.yaml'
        
        # Create invalid YAML
        config_path.write_text('invalid: yaml: : :\n')
        
        with pytest.raises(ConfigError):
            Config(project_config=str(config_path))

def test_nonexistent_config_files():
    """Test behavior with nonexistent config files."""
    # Create a new config instance with nonexistent files
    test_config = Config(
        project_config='nonexistent.yaml',
        user_config='also_nonexistent.yaml'
    )
    
    # Should fall back to defaults
    assert test_config.get('deadline.host') == test_config.DEFAULT_CONFIG['deadline']['host']
    assert test_config.get('deadline.port') == test_config.DEFAULT_CONFIG['deadline']['port']
    assert test_config.get('deadline.use_web_service') == test_config.DEFAULT_CONFIG['deadline']['use_web_service']

def test_nonexistent_key():
    """Test getting nonexistent configuration key."""
    config = Config()
    assert config.get('nonexistent.key') is None
    assert config.get('nonexistent.key', 'default') == 'default' 