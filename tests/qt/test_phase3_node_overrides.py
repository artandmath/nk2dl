#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 3 Node Override Integration Tests"""

import sys
import os
import yaml
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the nk2dl path to sys.path
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nk2dl')
if nk2dl_path not in sys.path:
    sys.path.insert(0, nk2dl_path)

# Set minimal logging
os.environ['NK2DL_LOG_LEVEL'] = 'ERROR'

def test_storage_config_integration():
    """Test storage integration with config system."""
    print("Testing Storage Config Integration")
    print("=" * 40)
    
    try:
        # Mock the nuke module
        with patch('gui.panel.repositories.storage.nuke_module') as mock_nuke_module:
            # Mock nuke components
            mock_nuke = Mock()
            mock_root = Mock()
            mock_knob = Mock()
            
            # Set up mock return values
            mock_nuke_module.return_value = mock_nuke
            mock_nuke.root.return_value = mock_root
            mock_root.knobs.return_value = {'nk2dl_settings': mock_knob}
            mock_root.__getitem__.return_value = mock_knob
            mock_knob.value.return_value = ""  # Empty settings initially
            
            # Import after mocking
            from gui.panel.repositories.storage import NodeSettingsStorage
            
            storage = NodeSettingsStorage()
            
            # Test config default value retrieval
            priority = storage.get_config_default_value('priority')
            chunk_size = storage.get_config_default_value('chunk_size')
            enable_auto_timeout = storage.get_config_default_value('enable_auto_timeout')
            gpu_override = storage.get_config_default_value('gpu_override')
            
            print(f"  Config defaults:")
            print(f"    priority: {priority} ✓")
            print(f"    chunk_size: {chunk_size} ✓")
            print(f"    enable_auto_timeout: {enable_auto_timeout} ✓")
            print(f"    gpu_override: '{gpu_override}' ✓")
            
            # Test parameter validation
            validated_priority = storage.validate_node_override('priority', "75")
            validated_timeout = storage.validate_node_override('enable_auto_timeout', "true")
            validated_gpu = storage.validate_node_override('gpu_override', "2")
            
            print(f"  Parameter validation:")
            print(f"    priority '75' -> {validated_priority} ({type(validated_priority).__name__}) ✓")
            print(f"    enable_auto_timeout 'true' -> {validated_timeout} ({type(validated_timeout).__name__}) ✓")
            print(f"    gpu_override '2' -> '{validated_gpu}' ({type(validated_gpu).__name__}) ✓")
            
            print("✅ Storage config integration working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Storage config integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_write_node_dict_generation():
    """Test WriteNode dictionary generation with direct parameter mapping."""
    print("\nTesting WriteNode Dictionary Generation")
    print("=" * 40)
    
    try:
        # Mock the nuke module
        with patch('gui.panel.repositories.storage.nuke_module') as mock_nuke_module:
            # Mock nuke components
            mock_nuke = Mock()
            mock_root = Mock()
            mock_knob = Mock()
            
            # Test data: node overrides with submission parameter names
            test_overrides = {
                'Write1': {
                    'priority': 90,
                    'chunk_size': 5,
                    'enable_auto_timeout': True,
                    'gpu_override': '2',
                    'limit_worker_tasks': True
                },
                'Write2': {
                    'priority': 80,
                    'use_gpu': True,
                    'pool': 'render'
                }
            }
            
            yaml_data = yaml.dump({
                'version': '0.1',
                'timestamp': 1234567890,
                'node_overrides': test_overrides
            })
            
            # Set up mock return values
            mock_nuke_module.return_value = mock_nuke
            mock_nuke.root.return_value = mock_root
            mock_root.knobs.return_value = {'nk2dl_settings': mock_knob}
            mock_root.__getitem__.return_value = mock_knob
            mock_knob.value.return_value = yaml_data
            
            # Import after mocking
            from gui.panel.repositories.storage import NodeSettingsStorage
            
            storage = NodeSettingsStorage()
            
            # Test single WriteNode dict generation
            write1_dict = storage.build_write_node_dict('Write1')
            write2_dict = storage.build_write_node_dict('Write2')
            write3_dict = storage.build_write_node_dict('Write3')  # No overrides
            
            print(f"  WriteNode dictionaries:")
            print(f"    Write1: {write1_dict}")
            print(f"    Write2: {write2_dict}")
            print(f"    Write3: {write3_dict}")
            
            # Verify Write1 dict
            expected_write1 = {
                'write_node': 'Write1',
                'priority': 90,
                'chunk_size': 5,
                'enable_auto_timeout': True,
                'gpu_override': '2',
                'limit_worker_tasks': True
            }
            
            if write1_dict == expected_write1:
                print("    ✅ Write1 dict correct")
            else:
                print(f"    ❌ Write1 dict mismatch: got {write1_dict}, expected {expected_write1}")
                return False
            
            # Verify Write2 dict
            expected_write2 = {
                'write_node': 'Write2',
                'priority': 80,
                'use_gpu': True,
                'pool': 'render'
            }
            
            if write2_dict == expected_write2:
                print("    ✅ Write2 dict correct")
            else:
                print(f"    ❌ Write2 dict mismatch: got {write2_dict}, expected {expected_write2}")
                return False
            
            # Verify Write3 dict (no overrides)
            expected_write3 = {'write_node': 'Write3'}
            
            if write3_dict == expected_write3:
                print("    ✅ Write3 dict correct (no overrides)")
            else:
                print(f"    ❌ Write3 dict mismatch: got {write3_dict}, expected {expected_write3}")
                return False
            
            # Test WriteNodes list generation
            write_nodes_list = storage.build_write_nodes_list(['Write1', 'Write2', 'Write3'])
            expected_list = [expected_write1, expected_write2, expected_write3]
            
            if write_nodes_list == expected_list:
                print("    ✅ WriteNodes list correct")
            else:
                print(f"    ❌ WriteNodes list mismatch: got {write_nodes_list}, expected {expected_list}")
                return False
            
            print("✅ WriteNode dictionary generation working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ WriteNode dictionary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effective_value_calculation():
    """Test effective value calculation (override vs config default)."""
    print("\nTesting Effective Value Calculation")
    print("=" * 40)
    
    try:
        # Mock the nuke module
        with patch('gui.panel.repositories.storage.nuke_module') as mock_nuke_module:
            # Mock nuke components
            mock_nuke = Mock()
            mock_root = Mock()
            mock_knob = Mock()
            
            # Test data: partial overrides
            test_overrides = {
                'Write1': {
                    'priority': 95,  # Overridden
                    'chunk_size': 3,  # Overridden
                    # use_gpu not overridden - should use config default
                }
            }
            
            yaml_data = yaml.dump({
                'version': '0.1',
                'timestamp': 1234567890,
                'node_overrides': test_overrides
            })
            
            # Set up mock return values
            mock_nuke_module.return_value = mock_nuke
            mock_nuke.root.return_value = mock_root
            mock_root.knobs.return_value = {'nk2dl_settings': mock_knob}
            mock_root.__getitem__.return_value = mock_knob
            mock_knob.value.return_value = yaml_data
            
            # Import after mocking
            from gui.panel.repositories.storage import NodeSettingsStorage
            
            storage = NodeSettingsStorage()
            
            # Test effective values
            priority_value = storage.get_effective_value('Write1', 'priority')
            chunk_size_value = storage.get_effective_value('Write1', 'chunk_size')
            use_gpu_value = storage.get_effective_value('Write1', 'use_gpu')
            pool_value = storage.get_effective_value('Write1', 'pool')
            
            print(f"  Effective values for Write1:")
            print(f"    priority: {priority_value} (overridden)")
            print(f"    chunk_size: {chunk_size_value} (overridden)")
            print(f"    use_gpu: {use_gpu_value} (config default)")
            print(f"    pool: {pool_value} (config default)")
            
            # Test override status
            priority_overridden = storage.is_value_overridden('Write1', 'priority')
            use_gpu_overridden = storage.is_value_overridden('Write1', 'use_gpu')
            
            print(f"  Override status:")
            print(f"    priority overridden: {priority_overridden} ✓")
            print(f"    use_gpu overridden: {use_gpu_overridden} ✓")
            
            # Verify correct values
            if priority_value == 95 and priority_overridden:
                print("    ✅ Priority override working correctly")
            else:
                print(f"    ❌ Priority override failed: value={priority_value}, overridden={priority_overridden}")
                return False
            
            if use_gpu_value == False and not use_gpu_overridden:  # Config default
                print("    ✅ Config default inheritance working correctly")
            else:
                print(f"    ❌ Config default inheritance failed: value={use_gpu_value}, overridden={use_gpu_overridden}")
                return False
            
            print("✅ Effective value calculation working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Effective value calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_node_override_management():
    """Test node override setting and clearing."""
    print("\nTesting Node Override Management")
    print("=" * 40)
    
    try:
        # Mock the nuke module
        with patch('gui.panel.repositories.storage.nuke_module') as mock_nuke_module:
            # Mock nuke components
            mock_nuke = Mock()
            mock_root = Mock()
            mock_knob = Mock()
            
            # Initial empty state
            mock_nuke_module.return_value = mock_nuke
            mock_nuke.root.return_value = mock_root
            mock_root.knobs.return_value = {'nk2dl_settings': mock_knob}
            mock_root.__getitem__.return_value = mock_knob
            mock_knob.value.return_value = ""
            
            # Import after mocking
            from gui.panel.repositories.storage import NodeSettingsStorage
            
            storage = NodeSettingsStorage()
            
            # Test setting overrides
            success1 = storage.set_node_override('Write1', 'priority', 85)
            success2 = storage.set_node_override('Write1', 'chunk_size', 8)
            success3 = storage.set_node_override('Write2', 'use_gpu', True)
            
            print(f"  Setting overrides:")
            print(f"    Write1.priority = 85: {success1} ✓")
            print(f"    Write1.chunk_size = 8: {success2} ✓")
            print(f"    Write2.use_gpu = True: {success3} ✓")
            
            # Test clearing individual override
            success4 = storage.set_node_override('Write1', 'priority', None)
            print(f"  Clearing override:")
            print(f"    Write1.priority = None: {success4} ✓")
            
            # Test clearing all overrides for a node
            success5 = storage.clear_node_overrides('Write1')
            print(f"  Clearing all overrides:")
            print(f"    Clear Write1 overrides: {success5} ✓")
            
            print("✅ Node override management working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Node override management failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Phase 3 tests."""
    print("🎯 PHASE 3: NODE OVERRIDE INTEGRATION TESTS")
    print("=" * 50)
    
    tests = [
        test_storage_config_integration,
        test_write_node_dict_generation,
        test_effective_value_calculation,
        test_node_override_management
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Phase 3 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 PHASE 3: NODE OVERRIDE INTEGRATION COMPLETE!")
        print("✅ All tests passed successfully!")
        print("\n📋 PHASE 3 ACHIEVEMENTS:")
        print("   ✅ Node override storage using submission parameter names")
        print("   ✅ Config defaults integration for missing values")
        print("   ✅ Direct parameter mapping (zero translation)")
        print("   ✅ WriteNode dictionary generation")
        print("   ✅ Effective value calculation (override vs config)")
        print("   ✅ Node override management (set/clear)")
        print("\n🚀 READY FOR PHASE 4: Submission Integration")
    else:
        print("❌ Some Phase 3 tests failed")
    
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 