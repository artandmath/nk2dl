#!/usr/bin/env python3
"""
Test Phase 5: Enhanced Schema and Storage
Test the SettingsSchema class and enhanced NodeSettingsStorage methods
"""

import sys
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add the nk2dl module to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_settings_schema_basic():
    """Test basic SettingsSchema functionality"""
    
    print("Testing SettingsSchema basic functionality...")
    
    # Import after path setup
    from nk2dl.gui.panel.constants import SettingsSchema
    
    # Test getting parameter schema
    priority_schema = SettingsSchema.get_parameter_schema('priority')
    assert priority_schema['type'] == SettingsSchema.TYPE_INT
    assert priority_schema['config_key'] == 'submission.priority'
    assert priority_schema['category'] == 'job'
    assert priority_schema['required'] == True
    
    # Test getting parameter type
    assert SettingsSchema.get_parameter_type('priority') == int
    assert SettingsSchema.get_parameter_type('pool') == str
    assert SettingsSchema.get_parameter_type('use_gpu') == bool
    
    # Test getting config key
    assert SettingsSchema.get_config_key('priority') == 'submission.priority'
    assert SettingsSchema.get_config_key('pool') == 'submission.pool'
    assert SettingsSchema.get_config_key('frames') is None  # Not in config
    
    # Test validation rules
    rules = SettingsSchema.get_validation_rules('priority')
    assert 'min_value' in rules
    assert 'max_value' in rules
    assert rules['required'] == True
    
    # Test category grouping
    job_params = SettingsSchema.get_parameters_by_category('job')
    machine_params = SettingsSchema.get_parameters_by_category('machine')
    extra_params = SettingsSchema.get_parameters_by_category('extra')
    
    assert 'priority' in job_params
    assert 'pool' in machine_params
    assert 'department' in extra_params
    
    print("✓ SettingsSchema basic functionality works correctly")

def test_settings_schema_validation():
    """Test SettingsSchema validation functionality"""
    
    print("Testing SettingsSchema validation...")
    
    from nk2dl.gui.panel.constants import SettingsSchema
    
    # Test valid values
    is_valid, error = SettingsSchema.validate_value('priority', 50)
    assert is_valid == True
    assert error == ""
    
    # Test type conversion
    is_valid, error = SettingsSchema.validate_value('priority', "75")
    assert is_valid == True  # Should convert string to int
    
    # Test range validation
    is_valid, error = SettingsSchema.validate_value('priority', 150)
    assert is_valid == False  # Above max value
    assert "greater than maximum" in error
    
    is_valid, error = SettingsSchema.validate_value('priority', -10)
    assert is_valid == False  # Below min value
    assert "less than minimum" in error
    
    # Test boolean validation
    is_valid, error = SettingsSchema.validate_value('use_gpu', True)
    assert is_valid == True
    
    is_valid, error = SettingsSchema.validate_value('use_gpu', "yes")
    assert is_valid == True  # Should convert to bool
    
    # Test options validation
    is_valid, error = SettingsSchema.validate_value('render_mode', 'full')
    assert is_valid == True
    
    is_valid, error = SettingsSchema.validate_value('render_mode', 'invalid_mode')
    assert is_valid == False
    assert "not in allowed options" in error
    
    # Test required field validation
    is_valid, error = SettingsSchema.validate_value('priority', None)
    assert is_valid == False
    assert "Parameter priority is required" in error
    
    print("✓ SettingsSchema validation works correctly")

def test_helper_functions():
    """Test the helper functions for config integration"""
    
    print("Testing helper functions...")
    
    from nk2dl.gui.panel.constants import (
        get_default_value, get_schema_default, 
        validate_settings, convert_and_validate_setting
    )
    
    # Test get_default_value (mock config)
    with patch('nk2dl.common.config.config') as mock_config:
        mock_config.get.return_value = 50
        value = get_default_value('submission.priority')
        assert value == 50
        mock_config.get.assert_called_with('submission.priority')
    
    # Test get_schema_default
    with patch('nk2dl.common.config.config') as mock_config:
        mock_config.get.return_value = 'nuke'
        value = get_schema_default('machine', 'pool')
        assert value == 'nuke'
    
    # Test validate_settings
    test_settings = {
        'priority': 50,
        'pool': 'nuke',
        'use_gpu': True
    }
    is_valid, errors = validate_settings(test_settings)
    assert is_valid == True
    assert len(errors) == 0
    
    # Test with invalid settings
    invalid_settings = {
        'priority': 150,  # Above max
        'render_mode': 'invalid'  # Not in options
    }
    is_valid, errors = validate_settings(invalid_settings)
    assert is_valid == False
    assert len(errors) > 0
    
    # Test convert_and_validate_setting
    converted, is_valid, error = convert_and_validate_setting('priority', "75")
    assert converted == 75
    assert is_valid == True
    assert error == ""
    
    # Test boolean conversion
    converted, is_valid, error = convert_and_validate_setting('use_gpu', "true")
    assert converted == True
    assert is_valid == True
    
    print("✓ Helper functions work correctly")

def test_enhanced_storage_methods():
    """Test the enhanced NodeSettingsStorage methods"""
    
    print("Testing enhanced NodeSettingsStorage methods...")
    
    # Mock nuke module
    mock_nuke = Mock()
    mock_root = Mock()
    mock_knobs = {'nk2dl_settings': Mock()}
    mock_root.knobs.return_value = mock_knobs
    mock_root.__getitem__ = lambda self, key: mock_knobs[key]
    mock_nuke.root.return_value = mock_root
    
    with patch('nk2dl.gui.panel.repositories.storage.nuke_module', return_value=mock_nuke):
        from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
        
        # Create storage instance
        storage = NodeSettingsStorage()
        
        # Test _get_config_default_settings
        with patch('nk2dl.gui.panel.repositories.storage.config') as mock_config:
            mock_config.get.side_effect = lambda key: {
                'submission.priority': 50,
                'submission.pool': 'nuke',
                'submission.use_gpu': False
            }.get(key)
            
            defaults = storage._get_config_default_settings()
            assert 'priority' in defaults
            assert 'pool' in defaults
            assert 'use_gpu' in defaults
            assert defaults['priority'] == 50
            assert defaults['pool'] == 'nuke'
        
        # Test _apply_config_defaults
        with patch('nk2dl.gui.panel.repositories.storage.config') as mock_config:
            mock_config.get.side_effect = lambda key: {
                'submission.priority': 50,
                'submission.pool': 'nuke'
            }.get(key)
            
            partial_settings = {'priority': 75}  # Only has priority
            complete_settings = storage._apply_config_defaults(partial_settings)
            assert complete_settings['priority'] == 75  # Keeps existing
            assert 'pool' in complete_settings  # Adds missing from config
        
        # Test _validate_settings
        global_settings = {'priority': 50, 'pool': 'nuke'}
        node_overrides = {
            'Write1': {'priority': 75, 'use_gpu': True}
        }
        
        is_valid, errors = storage._validate_settings(global_settings, node_overrides)
        assert is_valid == True
        assert len(errors) == 0
        
        # Test _convert_and_validate
        converted, is_valid, error = storage._convert_and_validate('priority', "80")
        assert converted == 80
        assert is_valid == True
        assert error == ""
        
        print("✓ Enhanced NodeSettingsStorage methods work correctly")

def test_save_load_all_settings():
    """Test save_all_settings and load_all_settings methods"""
    
    print("Testing save_all_settings and load_all_settings...")
    
    # Mock nuke module and storage
    mock_nuke = Mock()
    mock_root = Mock()
    mock_settings_knob = Mock()
    mock_knobs = {'nk2dl_settings': mock_settings_knob}
    
    mock_root.knobs.return_value = mock_knobs
    mock_root.__getitem__ = lambda self, key: mock_knobs[key]
    mock_root.__contains__ = lambda self, key: key in mock_knobs
    mock_nuke.root.return_value = mock_root
    
    # Storage for the YAML data
    stored_yaml = ""
    
    def mock_set_value(value):
        nonlocal stored_yaml
        stored_yaml = value
    
    def mock_get_value():
        return stored_yaml
    
    mock_settings_knob.setValue = mock_set_value
    mock_settings_knob.value = mock_get_value
    
    with patch('nk2dl.gui.panel.repositories.storage.nuke_module', return_value=mock_nuke):
        from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
        
        # Create storage instance
        storage = NodeSettingsStorage()
        
        # Mock config for validation
        with patch('nk2dl.gui.panel.repositories.storage.config') as mock_config:
            mock_config.get.side_effect = lambda key: {
                'submission.priority': 50,
                'submission.pool': 'nuke',
                'submission.use_gpu': False
            }.get(key)
            
            # Test data
            global_settings = {
                'priority': 75,
                'pool': 'render',
                'use_gpu': True
            }
            
            node_overrides = {
                'Write1': {'priority': 90, 'use_gpu': False},
                'Write2': {'pool': 'fx'}
            }
            
            # Test save_all_settings
            success = storage.save_all_settings(global_settings, node_overrides)
            assert success == True
            assert stored_yaml != ""  # Something was saved
            
            # Test load_all_settings
            loaded_data = storage.load_all_settings()
            assert 'global_settings' in loaded_data
            assert 'node_overrides' in loaded_data
            
            loaded_global = loaded_data['global_settings']
            loaded_nodes = loaded_data['node_overrides']
            
            # Verify the data
            assert loaded_global['priority'] == 75
            assert loaded_global['pool'] == 'render'
            assert loaded_global['use_gpu'] == True
            
            assert 'Write1' in loaded_nodes
            assert 'Write2' in loaded_nodes
            assert loaded_nodes['Write1']['priority'] == 90
            assert loaded_nodes['Write2']['pool'] == 'fx'
    
    print("✓ save_all_settings and load_all_settings work correctly")

def main():
    """Run all Phase 5 tests"""
    print("============================================================")
    print("PHASE 5: ENHANCED SCHEMA AND STORAGE TESTS")
    print("============================================================")
    
    try:
        test_settings_schema_basic()
        test_settings_schema_validation()
        test_helper_functions()
        test_enhanced_storage_methods()
        test_save_load_all_settings()
        
        print("============================================================")
        print("✅ ALL PHASE 5 TESTS PASSED")
        print("✅ SettingsSchema integration working correctly")
        print("✅ Enhanced NodeSettingsStorage ready")
        print("============================================================")
        
    except Exception as e:
        print("============================================================")
        print(f"❌ PHASE 5 TEST FAILED: {str(e)}")
        print("============================================================")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 