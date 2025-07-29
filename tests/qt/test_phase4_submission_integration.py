#!/usr/bin/env python3
"""
Test Phase 4: Submission Integration
Test zero-translation parameter flow from storage to NukeSubmission
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add the nk2dl module to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Test direct logic without Qt/Nuke dependencies
def test_build_submission_args_basic():
    """Test basic build_submission_args functionality"""
    
    # Import after path setup
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    from nk2dl.common.config import config
    
    print("Testing basic build_submission_args functionality...")
    
    # Create mock settings model
    settings_model = Mock()
    
    # Configure mock to return specific values
    def mock_get_setting(param_name):
        test_values = {
            'priority': 75,
            'pool': 'test_pool',
            'chunk_size': 5,
            'use_gpu': True,
            'gpu_override': 'gpu1',
            'batch_mode': False,
            'ram_use': 8000
        }
        return test_values.get(param_name, None)
    
    settings_model.get_setting = Mock(side_effect=mock_get_setting)
    
    # Create storage instance
    storage = NodeSettingsStorage()
    storage.settings_model = settings_model
    
    # Test basic submission args building
    script_path = "/path/to/test.nk"
    args = storage.build_submission_args(script_path)
    
    # Verify basic structure
    assert args['script_path'] == script_path
    assert args['script_is_open'] == True
    
    # Verify settings were included
    assert args['priority'] == 75
    assert args['pool'] == 'test_pool'
    assert args['chunk_size'] == 5
    assert args['use_gpu'] == True
    assert args['gpu_override'] == 'gpu1'
    assert args['batch_mode'] == False
    assert args['ram_use'] == 8000
    
    print("✓ Basic submission args building works correctly")

def test_build_submission_args_with_node_overrides():
    """Test build_submission_args with node-specific overrides"""
    
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    
    print("Testing build_submission_args with node overrides...")
    
    # Create mock settings model
    settings_model = Mock()
    
    def mock_get_setting(param_name):
        global_values = {
            'priority': 50,
            'pool': 'default_pool',
            'chunk_size': 10,
            'use_gpu': False
        }
        return global_values.get(param_name, None)
    
    settings_model.get_setting = Mock(side_effect=mock_get_setting)
    
    # Create storage instance with node overrides
    storage = NodeSettingsStorage()
    storage.settings_model = settings_model
    
    # Add node overrides
    storage.node_overrides = {
        'Write1': {
            'priority': 90,
            'chunk_size': 5,
            'use_gpu': True
        },
        'Write2': {
            'priority': 75,
            'gpu_override': 'gpu2'
        }
    }
    
    # Test with write nodes
    script_path = "/path/to/test.nk"
    write_nodes = ['Write1', 'Write2', 'Write3']
    
    args = storage.build_submission_args(script_path, write_nodes=write_nodes)
    
    # Verify basic structure
    assert args['script_path'] == script_path
    assert args['script_is_open'] == True
    
    # Verify global settings
    assert args['priority'] == 50  # Global default
    assert args['pool'] == 'default_pool'
    assert args['chunk_size'] == 10
    assert args['use_gpu'] == False
    
    # Verify write_nodes structure
    assert 'write_nodes' in args
    write_nodes_result = args['write_nodes']
    assert len(write_nodes_result) == 3
    
    # Write1 should have overrides
    write1 = write_nodes_result[0]
    assert isinstance(write1, dict)
    assert write1['write_node'] == 'Write1'
    assert write1['priority'] == 90
    assert write1['chunk_size'] == 5
    assert write1['use_gpu'] == True
    
    # Write2 should have overrides
    write2 = write_nodes_result[1]
    assert isinstance(write2, dict)
    assert write2['write_node'] == 'Write2'
    assert write2['priority'] == 75
    assert write2['gpu_override'] == 'gpu2'
    
    # Write3 should be a simple string (no overrides)
    write3 = write_nodes_result[2]
    assert write3 == 'Write3'
    
    print("✓ Node overrides handled correctly")

def test_build_submission_args_with_additional_kwargs():
    """Test build_submission_args with additional keyword arguments"""
    
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    
    print("Testing build_submission_args with additional kwargs...")
    
    # Create mock settings model
    settings_model = Mock()
    
    def mock_get_setting(param_name):
        return {'priority': 50, 'pool': 'default'}.get(param_name, None)
    
    settings_model.get_setting = Mock(side_effect=mock_get_setting)
    
    # Create storage instance
    storage = NodeSettingsStorage()
    storage.settings_model = settings_model
    
    # Test with additional kwargs
    script_path = "/path/to/test.nk"
    additional_kwargs = {
        'frames': '1-100',
        'priority': 99,  # Should override global setting
        'render_mode': 'proxy',
        'write_nodes_as_separate_jobs': True,
        'custom_param': 'custom_value'
    }
    
    args = storage.build_submission_args(script_path, **additional_kwargs)
    
    # Verify basic structure
    assert args['script_path'] == script_path
    assert args['script_is_open'] == True
    
    # Verify global settings
    assert args['pool'] == 'default'  # From settings model
    
    # Verify additional kwargs override and extend
    assert args['frames'] == '1-100'
    assert args['priority'] == 99  # Should override global setting
    assert args['render_mode'] == 'proxy'
    assert args['write_nodes_as_separate_jobs'] == True
    assert args['custom_param'] == 'custom_value'
    
    print("✓ Additional kwargs handled correctly")

def test_parameter_name_mapping():
    """Test that parameter names in HeaderSettingsMapping are correctly used"""
    
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    from nk2dl.gui.panel.constants import HeaderSettingsMapping
    
    print("Testing parameter name mapping...")
    
    # Create mock settings model
    settings_model = Mock()
    
    # Create test values for all parameters in HeaderSettingsMapping
    test_values = {}
    for display_name, param_name in HeaderSettingsMapping.ALL_MAPPINGS.items():
        if param_name == 'priority':
            test_values[param_name] = 75
        elif param_name == 'pool':
            test_values[param_name] = 'test_pool'
        elif param_name == 'chunk_size':
            test_values[param_name] = 8
        elif param_name == 'use_gpu':
            test_values[param_name] = True
        elif param_name == 'batch_mode':
            test_values[param_name] = False
        elif param_name == 'enable_auto_timeout':
            test_values[param_name] = True
        elif param_name == 'use_nuke_x':
            test_values[param_name] = True
        else:
            test_values[param_name] = f"test_{param_name}"
    
    def mock_get_setting(param_name):
        return test_values.get(param_name, None)
    
    settings_model.get_setting = Mock(side_effect=mock_get_setting)
    
    # Create storage instance
    storage = NodeSettingsStorage()
    storage.settings_model = settings_model
    
    # Build submission args
    script_path = "/path/to/test.nk"
    args = storage.build_submission_args(script_path)
    
    # Verify all parameter names were correctly mapped
    for display_name, param_name in HeaderSettingsMapping.ALL_MAPPINGS.items():
        assert param_name in args, f"Parameter {param_name} not found in args"
        assert args[param_name] == test_values[param_name], f"Parameter {param_name} value mismatch"
    
    print("✓ Parameter name mapping works correctly")

def test_zero_translation_compatibility():
    """Test that built args are compatible with NukeSubmission constructor"""
    
    from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
    from nk2dl.gui.panel.models.settings_model import SettingsModel
    
    print("Testing zero-translation compatibility...")
    
    # Create mock settings model
    settings_model = Mock()
    
    def mock_get_setting(param_name):
        # Return realistic values for key parameters
        realistic_values = {
            'priority': 50,
            'pool': 'nuke',
            'group': 'none',
            'chunk_size': 10,
            'use_nuke_x': False,
            'batch_mode': True,
            'use_gpu': False,
            'enforce_render_order': True,
            'continue_on_error': False,
            'reload_plugins': False,
            'performance_profiler': False,
            'enable_auto_timeout': False,
            'limit_worker_tasks': False,
            'use_node_frame_list': False
        }
        return realistic_values.get(param_name, None)
    
    settings_model.get_setting = Mock(side_effect=mock_get_setting)
    
    # Create storage instance
    storage = NodeSettingsStorage()
    storage.settings_model = settings_model
    
    # Add some node overrides
    storage.node_overrides = {
        'Write1': {
            'priority': 90,
            'use_gpu': True
        }
    }
    
    # Build submission args
    script_path = "/path/to/test.nk"
    write_nodes = ['Write1']
    
    args = storage.build_submission_args(
        script_path, 
        write_nodes=write_nodes,
        frames='1-100',
        render_mode='full'
    )
    
    # Verify the args structure is compatible with NukeSubmission
    # All parameters should be using the exact names from submission.py
    
    # Check required parameters are present
    assert 'script_path' in args
    assert 'script_is_open' in args
    
    # Check submission parameters use correct names
    assert 'priority' in args  # Not 'Priority'
    assert 'pool' in args      # Not 'Pool'
    assert 'chunk_size' in args  # Not 'ChunkSize'
    assert 'use_gpu' in args   # Not 'UseGpu'
    assert 'batch_mode' in args  # Not 'BatchMode'
    assert 'use_nuke_x' in args  # Not 'UseNukeX'
    assert 'enable_auto_timeout' in args  # Not 'EnableAutoTimeout'
    assert 'limit_worker_tasks' in args   # Not 'LimitConcurrentTasks'
    
    # Check write_nodes format
    assert 'write_nodes' in args
    assert isinstance(args['write_nodes'], list)
    assert len(args['write_nodes']) == 1
    
    write_node = args['write_nodes'][0]
    assert isinstance(write_node, dict)
    assert write_node['write_node'] == 'Write1'
    assert write_node['priority'] == 90
    assert write_node['use_gpu'] == True
    
    print("✓ Zero-translation compatibility verified")

def main():
    """Run all Phase 4 tests"""
    print("=" * 60)
    print("PHASE 4: SUBMISSION INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_build_submission_args_basic()
        test_build_submission_args_with_node_overrides()
        test_build_submission_args_with_additional_kwargs()
        test_parameter_name_mapping()
        test_zero_translation_compatibility()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 4 TESTS PASSED")
        print("✅ Zero-translation parameter flow working correctly")
        print("✅ Storage → NukeSubmission integration ready")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 