#!/usr/bin/env python3
"""
Direct Nuke test for storage functionality
Avoids import conflicts by testing core functionality directly
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Path setup for direct testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, nk2dl_path)

def test_config_system_in_nuke():
    """Test config system works in Nuke environment"""
    
    print("============================================================")
    print("DIRECT NUKE TEST: CONFIG SYSTEM")
    print("============================================================")
    
    try:
        # Direct import without relative imports
        from nk2dl.common.config import config
        
        # Test config access
        priority = config.get('submission.priority')
        pool = config.get('submission.pool')
        use_gpu = config.get('submission.use_gpu')
        
        print(f"Config priority: {priority}")
        print(f"Config pool: {pool}")
        print(f"Config use_gpu: {use_gpu}")
        
        assert priority is not None
        assert pool is not None
        assert use_gpu is not None
        
        print("✓ Config system works in Nuke")
        return True
        
    except Exception as e:
        print(f"✗ Config system failed: {e}")
        return False

def test_settings_schema_in_nuke():
    """Test SettingsSchema works in Nuke environment"""
    
    print("\n============================================================")
    print("DIRECT NUKE TEST: SETTINGS SCHEMA")
    print("============================================================")
    
    try:
        # Direct import
        from nk2dl.gui.panel.constants import SettingsSchema
        
        # Test schema access
        priority_type = SettingsSchema.get_parameter_type('priority')
        pool_type = SettingsSchema.get_parameter_type('pool')
        use_gpu_type = SettingsSchema.get_parameter_type('use_gpu')
        
        print(f"Priority type: {priority_type}")
        print(f"Pool type: {pool_type}")
        print(f"Use GPU type: {use_gpu_type}")
        
        assert priority_type == int
        assert pool_type == str
        assert use_gpu_type == bool
        
        # Test validation
        is_valid, error = SettingsSchema.validate_value('priority', 50)
        assert is_valid == True
        assert error == ""
        
        is_valid, error = SettingsSchema.validate_value('priority', 150)
        assert is_valid == False
        assert "greater than maximum" in error
        
        print("✓ Settings schema works in Nuke")
        return True
        
    except Exception as e:
        print(f"✗ Settings schema failed: {e}")
        return False

def test_pyside_imports_in_nuke():
    """Test PySide imports work correctly in Nuke"""
    
    print("\n============================================================")
    print("DIRECT NUKE TEST: PYSIDE IMPORTS")
    print("============================================================")
    
    try:
        import nuke
        
        # Test Nuke version detection
        print(f"Nuke version: {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
        
        # Test PySide imports based on Nuke version
        if nuke.NUKE_VERSION_MAJOR >= 16:
            from PySide6 import QtWidgets, QtCore, QtGui
            print("✓ PySide6 imported successfully")
        else:
            from PySide2 import QtWidgets, QtCore, QtGui
            print("✓ PySide2 imported successfully")
        
        # Test basic Qt functionality
        app = QtWidgets.QApplication.instance()
        if app is None:
            print("✗ Qt Application not available")
            return False
        else:
            print("✓ Qt Application available")
        
        return True
        
    except Exception as e:
        print(f"✗ PySide imports failed: {e}")
        return False

def test_storage_mock_in_nuke():
    """Test storage functionality with mocks in Nuke"""
    
    print("\n============================================================")
    print("DIRECT NUKE TEST: STORAGE MOCK")
    print("============================================================")
    
    try:
        # Mock nuke module to avoid import issues
        mock_nuke = Mock()
        mock_root = Mock()
        mock_knobs = {'nk2dl_settings': Mock()}
        mock_root.knobs.return_value = mock_knobs
        mock_root.__getitem__ = lambda self, key: mock_knobs[key]
        mock_nuke.root.return_value = mock_root
        
        # Test storage with mocks
        with patch('nk2dl.gui.panel.repositories.storage.nuke_module', return_value=mock_nuke):
            from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
            
            # Create storage instance
            storage = NodeSettingsStorage()
            
            # Test config default settings
            with patch('nk2dl.gui.panel.repositories.storage.config') as mock_config:
                mock_config.get.side_effect = lambda key: {
                    'submission.priority': 50,
                    'submission.pool': 'nuke',
                    'submission.use_gpu': False
                }.get(key)
                
                defaults = storage._get_config_default_settings()
                
                print(f"Config defaults: {defaults}")
                assert 'priority' in defaults
                assert 'pool' in defaults
                assert defaults['priority'] == 50
                assert defaults['pool'] == 'nuke'
        
        print("✓ Storage mock functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Storage mock failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_build_submission_args_in_nuke():
    """Test build_submission_args in Nuke environment"""
    
    print("\n============================================================")
    print("DIRECT NUKE TEST: BUILD SUBMISSION ARGS")
    print("============================================================")
    
    try:
        # Mock dependencies
        mock_nuke = Mock()
        mock_root = Mock()
        mock_knobs = {'nk2dl_settings': Mock()}
        mock_root.knobs.return_value = mock_knobs
        mock_root.__getitem__ = lambda self, key: mock_knobs[key]
        mock_nuke.root.return_value = mock_root
        
        with patch('nk2dl.gui.panel.repositories.storage.nuke_module', return_value=mock_nuke):
            from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
            
            # Create mock settings model
            settings_model = Mock()
            def mock_get_setting(param_name):
                test_values = {
                    'priority': 75,
                    'pool': 'test_pool',
                    'chunk_size': 5,
                    'use_gpu': True
                }
                return test_values.get(param_name, None)
            
            settings_model.get_setting = Mock(side_effect=mock_get_setting)
            
            # Create storage instance
            storage = NodeSettingsStorage()
            storage.settings_model = settings_model
            
            # Test basic submission args building
            script_path = "/path/to/test.nk"
            args = storage.build_submission_args(script_path)
            
            print(f"Submission args keys: {list(args.keys())}")
            print(f"Script path: {args.get('script_path')}")
            print(f"Priority: {args.get('priority')}")
            print(f"Pool: {args.get('pool')}")
            
            # Verify basic structure
            assert args['script_path'] == script_path
            assert args['script_is_open'] == True
            assert args['priority'] == 75
            assert args['pool'] == 'test_pool'
            
        print("✓ Build submission args works in Nuke")
        return True
        
    except Exception as e:
        print(f"✗ Build submission args failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all direct Nuke tests"""
    
    print("Starting direct Nuke tests...")
    
    # Keep track of results
    test_results = []
    
    # Run tests
    test_results.append(test_config_system_in_nuke())
    test_results.append(test_settings_schema_in_nuke())
    test_results.append(test_pyside_imports_in_nuke())
    test_results.append(test_storage_mock_in_nuke())
    test_results.append(test_build_submission_args_in_nuke())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n============================================================")
    print(f"DIRECT NUKE TEST SUMMARY")
    print(f"============================================================")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL DIRECT NUKE TESTS PASSED")
    else:
        print("❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Storage implementation validated in Nuke environment!")
    else:
        print("\n⚠️  Some issues found in Nuke environment") 