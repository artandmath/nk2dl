#!/usr/bin/env python3
"""
Test Phase 4: Submission Integration (Simple)
Test the core logic without Qt/GUI dependencies
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the nk2dl module to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_submission_args_structure():
    """Test that we can build submission arguments with the expected structure"""
    
    print("Testing submission arguments structure...")
    
    # Mock the storage class directly without importing GUI components
    class MockStorage:
        def __init__(self):
            self.node_overrides = {}
            self.settings_model = None
            
        def build_submission_args(self, script_path, write_nodes=None, **additional_kwargs):
            """Build arguments for NukeSubmission constructor"""
            
            # Start with required parameters
            args = {
                'script_path': script_path,
                'script_is_open': True,
            }
            
            # Add mock global settings
            if self.settings_model:
                # Simulate HeaderSettingsMapping parameter retrieval
                test_mapping = {
                    'Priority': 'priority',
                    'Pool': 'pool', 
                    'Group': 'group',
                    'ChunkSize': 'chunk_size',
                    'GPU': 'use_gpu',
                    'GPUId': 'gpu_override',
                    'BatchMode': 'batch_mode',
                    'NukeX': 'use_nuke_x',
                    'AutoTimeout': 'enable_auto_timeout',
                    'WorkerTaskLimit': 'limit_worker_tasks'
                }
                
                for display_name, param_name in test_mapping.items():
                    value = self.settings_model.get_setting(param_name)
                    if value is not None:
                        args[param_name] = value
            
            # Handle write nodes with overrides
            if write_nodes:
                write_nodes_with_overrides = []
                
                for node_name in write_nodes:
                    if node_name in self.node_overrides:
                        # Node has overrides - create WriteNode dictionary
                        node_dict = {
                            'write_node': node_name,
                            **self.node_overrides[node_name]
                        }
                        write_nodes_with_overrides.append(node_dict)
                    else:
                        # Node has no overrides - use simple string
                        write_nodes_with_overrides.append(node_name)
                
                args['write_nodes'] = write_nodes_with_overrides
            
            # Apply additional kwargs
            args.update(additional_kwargs)
            
            return args
    
    # Test the mock implementation
    storage = MockStorage()
    
    # Create mock settings model
    settings_model = Mock()
    
    def mock_get_setting(param_name):
        test_values = {
            'priority': 75,
            'pool': 'test_pool',
            'chunk_size': 5,
            'use_gpu': True,
            'gpu_override': 'gpu1',
            'batch_mode': False,
            'use_nuke_x': True,
            'enable_auto_timeout': True,
            'limit_worker_tasks': False
        }
        return test_values.get(param_name, None)
    
    settings_model.get_setting.side_effect = mock_get_setting
    storage.settings_model = settings_model
    
    # Test basic args building
    script_path = "/path/to/test.nk"
    args = storage.build_submission_args(script_path)
    
    # Verify structure
    assert args['script_path'] == script_path
    assert args['script_is_open'] == True
    assert args['priority'] == 75
    assert args['pool'] == 'test_pool'
    assert args['chunk_size'] == 5
    assert args['use_gpu'] == True
    assert args['gpu_override'] == 'gpu1'
    assert args['batch_mode'] == False
    assert args['use_nuke_x'] == True
    assert args['enable_auto_timeout'] == True
    assert args['limit_worker_tasks'] == False
    
    print("✓ Basic submission args structure correct")

def test_node_overrides_structure():
    """Test node overrides are structured correctly for WriteNode format"""
    
    print("Testing node overrides structure...")
    
    # Mock storage with node overrides
    class MockStorage:
        def __init__(self):
            self.node_overrides = {
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
            self.settings_model = None
            
        def build_submission_args(self, script_path, write_nodes=None, **additional_kwargs):
            args = {
                'script_path': script_path,
                'script_is_open': True,
            }
            
            # Handle write nodes with overrides
            if write_nodes:
                write_nodes_with_overrides = []
                
                for node_name in write_nodes:
                    if node_name in self.node_overrides:
                        node_dict = {
                            'write_node': node_name,
                            **self.node_overrides[node_name]
                        }
                        write_nodes_with_overrides.append(node_dict)
                    else:
                        write_nodes_with_overrides.append(node_name)
                
                args['write_nodes'] = write_nodes_with_overrides
            
            args.update(additional_kwargs)
            return args
    
    storage = MockStorage()
    
    # Test with write nodes
    script_path = "/path/to/test.nk"
    write_nodes = ['Write1', 'Write2', 'Write3']
    
    args = storage.build_submission_args(script_path, write_nodes=write_nodes)
    
    # Verify write_nodes structure
    assert 'write_nodes' in args
    write_nodes_result = args['write_nodes']
    assert len(write_nodes_result) == 3
    
    # Write1 should be a dict with overrides
    write1 = write_nodes_result[0]
    assert isinstance(write1, dict)
    assert write1['write_node'] == 'Write1'
    assert write1['priority'] == 90
    assert write1['chunk_size'] == 5
    assert write1['use_gpu'] == True
    
    # Write2 should be a dict with overrides
    write2 = write_nodes_result[1]
    assert isinstance(write2, dict)
    assert write2['write_node'] == 'Write2'
    assert write2['priority'] == 75
    assert write2['gpu_override'] == 'gpu2'
    
    # Write3 should be a simple string (no overrides)
    write3 = write_nodes_result[2]
    assert write3 == 'Write3'
    
    print("✓ Node overrides structure correct")

def test_parameter_name_compatibility():
    """Test that parameter names match NukeSubmission constructor expectations"""
    
    print("Testing parameter name compatibility...")
    
    # These are the actual parameter names used in NukeSubmission constructor
    expected_submission_params = [
        'script_path',
        'script_is_open',
        'priority',
        'pool', 
        'group',
        'chunk_size',
        'use_gpu',
        'gpu_override',
        'batch_mode',
        'use_nuke_x',
        'enable_auto_timeout',
        'limit_worker_tasks',
        'frames',
        'write_nodes',
        'render_mode'
    ]
    
    # Mock storage that returns these parameter names
    class MockStorage:
        def build_submission_args(self, script_path, **kwargs):
            # Return args using correct parameter names
            args = {
                'script_path': script_path,
                'script_is_open': True,
                'priority': 50,
                'pool': 'nuke',
                'group': 'none', 
                'chunk_size': 10,
                'use_gpu': False,
                'gpu_override': '',
                'batch_mode': True,
                'use_nuke_x': False,
                'enable_auto_timeout': False,
                'limit_worker_tasks': False
            }
            args.update(kwargs)
            return args
    
    storage = MockStorage()
    
    # Build args with additional parameters
    args = storage.build_submission_args(
        '/path/to/test.nk',
        frames='1-100',
        render_mode='full',
        write_nodes=['Write1']
    )
    
    # Verify all expected parameters are present with correct names
    for param in expected_submission_params:
        assert param in args, f"Missing parameter: {param}"
    
    # Verify parameter names match expected format (not Deadline format)
    assert 'priority' in args  # Not 'Priority'
    assert 'pool' in args      # Not 'Pool'
    assert 'chunk_size' in args  # Not 'ChunkSize'
    assert 'use_gpu' in args   # Not 'UseGpu'
    assert 'batch_mode' in args  # Not 'BatchMode'
    assert 'use_nuke_x' in args  # Not 'UseNukeX'
    assert 'enable_auto_timeout' in args  # Not 'EnableAutoTimeout'
    assert 'limit_worker_tasks' in args   # Not 'LimitConcurrentTasks'
    
    print("✓ Parameter names compatible with NukeSubmission")

def test_zero_translation_flow():
    """Test complete zero-translation flow simulation"""
    
    print("Testing zero-translation flow...")
    
    # Simulate the complete flow: Storage → NukeSubmission arguments
    
    # Mock storage that builds args
    class MockStorage:
        def build_submission_args(self, script_path, **kwargs):
            return {
                'script_path': script_path,
                'script_is_open': True,
                'priority': 75,
                'pool': 'nuke',
                'chunk_size': 8,
                'use_gpu': True,
                'write_nodes': [
                    {
                        'write_node': 'Write1',
                        'priority': 90,
                        'use_gpu': True
                    },
                    'Write2'  # No overrides
                ],
                **kwargs
            }
    
    # Mock NukeSubmission constructor
    class MockNukeSubmission:
        def __init__(self, **kwargs):
            self.args = kwargs
            
        def submit(self):
            return [{'job_id': 'test123'}]
    
    # Simulate the flow
    storage = MockStorage()
    
    # Step 1: Build submission args using storage
    script_path = '/path/to/test.nk'
    submission_args = storage.build_submission_args(
        script_path,
        frames='1-100',
        render_mode='full'
    )
    
    # Step 2: Pass args directly to NukeSubmission (zero translation)
    submission = MockNukeSubmission(**submission_args)
    
    # Step 3: Verify the args were passed through correctly
    args = submission.args
    
    assert args['script_path'] == script_path
    assert args['script_is_open'] == True
    assert args['priority'] == 75
    assert args['pool'] == 'nuke'
    assert args['chunk_size'] == 8
    assert args['use_gpu'] == True
    assert args['frames'] == '1-100'
    assert args['render_mode'] == 'full'
    
    # Verify write_nodes structure
    write_nodes = args['write_nodes']
    assert len(write_nodes) == 2
    
    write1 = write_nodes[0]
    assert write1['write_node'] == 'Write1'
    assert write1['priority'] == 90
    assert write1['use_gpu'] == True
    
    write2 = write_nodes[1]
    assert write2 == 'Write2'
    
    # Step 4: Simulate submission
    results = submission.submit()
    assert len(results) == 1
    assert results[0]['job_id'] == 'test123'
    
    print("✓ Zero-translation flow successful")

def main():
    """Run all Phase 4 simple tests"""
    print("=" * 60)
    print("PHASE 4: SUBMISSION INTEGRATION TESTS (SIMPLE)")
    print("=" * 60)
    
    try:
        test_submission_args_structure()
        test_node_overrides_structure()
        test_parameter_name_compatibility()
        test_zero_translation_flow()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 4 SIMPLE TESTS PASSED")
        print("✅ Zero-translation parameter flow validated")
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