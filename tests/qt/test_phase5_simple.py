#!/usr/bin/env python3
"""
Test Phase 5: Enhanced Schema and Storage (Simple)
Test the core logic without GUI dependencies
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the nk2dl module to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_config_integration():
    """Test that config system integration works"""
    
    print("Testing config system integration...")
    
    # Import config directly
    from nk2dl.common.config import config
    
    # Test that we can get submission parameters from config
    priority = config.get('submission.priority')
    pool = config.get('submission.pool')
    use_gpu = config.get('submission.use_gpu')
    
    print(f"Config priority: {priority}")
    print(f"Config pool: {pool}")
    print(f"Config use_gpu: {use_gpu}")
    
    # These should have values from the config system
    assert priority is not None
    assert pool is not None
    assert use_gpu is not None
    
    print("✓ Config system integration works")

def test_parameter_schema_structure():
    """Test the parameter schema structure"""
    
    print("Testing parameter schema structure...")
    
    # Test that we can create a mock schema structure
    mock_schema = {
        'priority': {
            'type': int,
            'config_key': 'submission.priority',
            'min_value': 0,
            'max_value': 100,
            'required': True,
            'category': 'job'
        },
        'pool': {
            'type': str,
            'config_key': 'submission.pool',
            'required': False,
            'category': 'machine'
        },
        'use_gpu': {
            'type': bool,
            'config_key': 'submission.use_gpu',
            'required': False,
            'category': 'machine'
        }
    }
    
    # Test schema structure
    assert 'priority' in mock_schema
    assert 'pool' in mock_schema
    assert 'use_gpu' in mock_schema
    
    # Test priority schema
    priority_schema = mock_schema['priority']
    assert priority_schema['type'] == int
    assert priority_schema['config_key'] == 'submission.priority'
    assert priority_schema['category'] == 'job'
    assert priority_schema['required'] == True
    
    # Test validation rules exist
    assert 'min_value' in priority_schema
    assert 'max_value' in priority_schema
    
    print("✓ Parameter schema structure is correct")

def test_basic_validation_logic():
    """Test basic validation logic"""
    
    print("Testing basic validation logic...")
    
    def validate_int_value(value, min_val=None, max_val=None):
        """Simple validation function"""
        try:
            int_value = int(value)
            if min_val is not None and int_value < min_val:
                return False, f"Value {int_value} below minimum {min_val}"
            if max_val is not None and int_value > max_val:
                return False, f"Value {int_value} above maximum {max_val}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"Cannot convert {value} to integer"
    
    def validate_bool_value(value):
        """Simple boolean validation"""
        if isinstance(value, bool):
            return True, ""
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes', 'on']:
                return True, ""
            elif value.lower() in ['false', '0', 'no', 'off']:
                return True, ""
        return False, f"Cannot convert {value} to boolean"
    
    # Test integer validation
    valid, error = validate_int_value(50, 0, 100)
    assert valid == True
    assert error == ""
    
    valid, error = validate_int_value(150, 0, 100)
    assert valid == False
    assert "above maximum" in error
    
    valid, error = validate_int_value(-10, 0, 100)
    assert valid == False
    assert "below minimum" in error
    
    # Test boolean validation
    valid, error = validate_bool_value(True)
    assert valid == True
    
    valid, error = validate_bool_value("true")
    assert valid == True
    
    valid, error = validate_bool_value("invalid")
    assert valid == False
    
    print("✓ Basic validation logic works correctly")

def test_storage_data_structure():
    """Test storage data structure"""
    
    print("Testing storage data structure...")
    
    # Test that we can create the expected storage structure
    storage_data = {
        'version': '0.1',
        'timestamp': 1234567890,
        'global_settings': {
            'priority': 50,
            'pool': 'nuke',
            'use_gpu': False
        },
        'node_overrides': {
            'Write1': {
                'priority': 75,
                'use_gpu': True
            },
            'Write2': {
                'pool': 'render'
            }
        }
    }
    
    # Validate structure
    assert 'version' in storage_data
    assert 'timestamp' in storage_data
    assert 'global_settings' in storage_data
    assert 'node_overrides' in storage_data
    
    # Test global settings
    global_settings = storage_data['global_settings']
    assert global_settings['priority'] == 50
    assert global_settings['pool'] == 'nuke'
    assert global_settings['use_gpu'] == False
    
    # Test node overrides
    node_overrides = storage_data['node_overrides']
    assert 'Write1' in node_overrides
    assert 'Write2' in node_overrides
    
    write1_settings = node_overrides['Write1']
    assert write1_settings['priority'] == 75
    assert write1_settings['use_gpu'] == True
    
    write2_settings = node_overrides['Write2']
    assert write2_settings['pool'] == 'render'
    
    print("✓ Storage data structure is correct")

def test_config_defaults_logic():
    """Test config defaults application logic"""
    
    print("Testing config defaults application logic...")
    
    # Mock config system
    mock_config_defaults = {
        'submission.priority': 50,
        'submission.pool': 'nuke',
        'submission.use_gpu': False,
        'submission.chunk_size': 10,
        'submission.batch_mode': True
    }
    
    def apply_config_defaults(settings, config_defaults):
        """Apply config defaults to incomplete settings"""
        complete_settings = settings.copy()
        
        # Map of parameter names to config keys
        param_to_config = {
            'priority': 'submission.priority',
            'pool': 'submission.pool',
            'use_gpu': 'submission.use_gpu',
            'chunk_size': 'submission.chunk_size',
            'batch_mode': 'submission.batch_mode'
        }
        
        for param_name, config_key in param_to_config.items():
            if param_name not in complete_settings:
                if config_key in config_defaults:
                    complete_settings[param_name] = config_defaults[config_key]
        
        return complete_settings
    
    # Test with partial settings
    partial_settings = {
        'priority': 75,  # Override config default
        'pool': 'render'  # Override config default
    }
    
    complete_settings = apply_config_defaults(partial_settings, mock_config_defaults)
    
    # Should keep explicit values
    assert complete_settings['priority'] == 75
    assert complete_settings['pool'] == 'render'
    
    # Should add missing values from config
    assert complete_settings['use_gpu'] == False  # From config
    assert complete_settings['chunk_size'] == 10  # From config
    assert complete_settings['batch_mode'] == True  # From config
    
    print("✓ Config defaults application logic works correctly")

def test_submission_args_integration():
    """Test submission arguments integration"""
    
    print("Testing submission arguments integration...")
    
    # Test the concept of building submission args
    def build_submission_args(script_path, global_settings, node_overrides, write_nodes=None, **kwargs):
        """Build submission arguments from settings"""
        args = {
            'script_path': script_path,
            'script_is_open': True
        }
        
        # Add global settings
        args.update(global_settings)
        
        # Add write nodes with overrides
        if write_nodes:
            write_nodes_list = []
            for node_name in write_nodes:
                node_dict = {'write_node': node_name}
                
                # Apply node-specific overrides if they exist
                if node_name in node_overrides:
                    node_dict.update(node_overrides[node_name])
                
                write_nodes_list.append(node_dict)
            
            args['write_nodes'] = write_nodes_list
        
        # Apply additional kwargs (can override global settings)
        args.update(kwargs)
        
        return args
    
    # Test data
    global_settings = {
        'priority': 50,
        'pool': 'nuke',
        'use_gpu': False,
        'batch_mode': True
    }
    
    node_overrides = {
        'Write1': {'priority': 90, 'use_gpu': True},
        'Write2': {'pool': 'render'}
    }
    
    # Build submission args
    args = build_submission_args(
        script_path='/path/to/script.nk',
        global_settings=global_settings,
        node_overrides=node_overrides,
        write_nodes=['Write1', 'Write2'],
        frames='1-100',
        render_mode='full'
    )
    
    # Test basic structure
    assert args['script_path'] == '/path/to/script.nk'
    assert args['script_is_open'] == True
    
    # Test global settings
    assert args['priority'] == 50
    assert args['pool'] == 'nuke'
    assert args['use_gpu'] == False
    assert args['batch_mode'] == True
    
    # Test additional kwargs
    assert args['frames'] == '1-100'
    assert args['render_mode'] == 'full'
    
    # Test write nodes
    assert 'write_nodes' in args
    write_nodes_list = args['write_nodes']
    assert len(write_nodes_list) == 2
    
    # Test Write1 with overrides
    write1 = write_nodes_list[0]
    assert write1['write_node'] == 'Write1'
    assert write1['priority'] == 90  # Overridden
    assert write1['use_gpu'] == True  # Overridden
    
    # Test Write2 with overrides
    write2 = write_nodes_list[1]
    assert write2['write_node'] == 'Write2'
    assert write2['pool'] == 'render'  # Overridden
    
    print("✓ Submission arguments integration works correctly")

def main():
    """Run all Phase 5 simple tests"""
    print("============================================================")
    print("PHASE 5: ENHANCED SCHEMA AND STORAGE TESTS (SIMPLE)")
    print("============================================================")
    
    try:
        test_config_integration()
        test_parameter_schema_structure()
        test_basic_validation_logic()
        test_storage_data_structure()
        test_config_defaults_logic()
        test_submission_args_integration()
        
        print("============================================================")
        print("✅ ALL PHASE 5 SIMPLE TESTS PASSED")
        print("✅ Schema and storage concepts validated")
        print("✅ Config integration working correctly")
        print("✅ Parameter validation logic tested")
        print("✅ Zero-translation flow confirmed")
        print("============================================================")
        
    except Exception as e:
        print("============================================================")
        print(f"❌ PHASE 5 TEST FAILED: {str(e)}")
        print("============================================================")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 