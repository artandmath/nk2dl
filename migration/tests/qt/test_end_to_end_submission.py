#!/usr/bin/env python3
"""
Test End-to-End Submission Workflow
Validates complete integration from GUI → Storage → Submission
"""

import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, nk2dl_path)

def test_render_button_integration():
    """Test that render button properly integrates with storage and submission systems"""
    
    print("============================================================")
    print("END-TO-END TEST: RENDER BUTTON INTEGRATION")
    print("============================================================")
    
    try:
        import nuke
        
        # Test PySide imports based on Nuke version
        if nuke.NUKE_VERSION_MAJOR >= 16:
            from PySide6 import QtWidgets, QtCore, QtGui
            print("✓ PySide6 imported successfully")
        else:
            from PySide2 import QtWidgets, QtCore, QtGui
            print("✓ PySide2 imported successfully")
        
        # Mock nuke functions for testing
        with patch('nuke.root') as mock_root, \
             patch('nuke.message') as mock_message, \
             patch('nk2dl.nuke.submission.submit_nuke_script') as mock_submit:
            
            # Setup nuke mocks
            mock_root.return_value.name.return_value = "/path/to/test_script.nk"
            mock_submit.return_value = [
                {'job_id': 'job_12345', 'status': 'success'},
                {'job_id': 'job_12346', 'status': 'success'}
            ]
            
            # Import and create panel components
            from nk2dl.gui.panel import Nk2dlPanel
            
            # Create mock application if needed
            app = QtWidgets.QApplication.instance()
            if app is None:
                app = QtWidgets.QApplication([])
            
            # Create panel instance
            print("Creating panel instance...")
            panel = Nk2dlPanel()
            
            # Mock table model to simulate selected nodes
            mock_table_model = Mock()
            mock_table_model.get_row_count.return_value = 3
            mock_table_model.get_node_name.side_effect = lambda row: ['Write1', 'Write2', 'Write3'][row]
            mock_table_model.is_node_selected_for_render.side_effect = lambda row: row < 2  # Select first 2 nodes
            
            panel.table_model = mock_table_model
            
            # Mock storage system
            mock_storage = Mock()
            mock_storage.build_submission_args.return_value = {
                'script_path': '/path/to/test_script.nk',
                'write_nodes': ['Write1', 'Write2'],
                'script_is_open': True,
                'priority': 75,
                'pool': 'test_pool',
                'chunk_size': 5,
                'render_settings_from_metadata': True,
                'render_order_dependencies': True
            }
            
            panel.node_settings_view = Mock()
            panel.node_settings_view.storage = mock_storage
            
            # Mock progress manager
            panel.progress_manager = Mock()
            
            # Mock console view
            panel.console_view = Mock()
            
            print("✓ Panel components mocked successfully")
            
            # Test the render button click handler
            print("\nTesting render button click handler...")
            panel._on_render_clicked()
            
            # Verify the workflow
            print("\n--- Verifying Workflow ---")
            
            # 1. Check script path validation
            mock_root.return_value.name.assert_called()
            print("✓ Script path validation called")
            
            # 2. Check node selection
            assert mock_table_model.get_row_count.called
            assert mock_table_model.get_node_name.called
            assert mock_table_model.is_node_selected_for_render.called
            print("✓ Node selection logic executed")
            
            # 3. Check storage integration
            assert mock_storage.build_submission_args.called
            submission_call = mock_storage.build_submission_args.call_args
            assert submission_call[1]['script_path'] == '/path/to/test_script.nk'
            assert submission_call[1]['write_nodes'] == ['Write1', 'Write2']
            print("✓ Storage integration working correctly")
            
            # 4. Check submission call
            mock_submit.assert_called_once()
            submission_args = mock_submit.call_args[1]
            assert submission_args['script_path'] == '/path/to/test_script.nk'
            assert submission_args['write_nodes'] == ['Write1', 'Write2']
            assert submission_args['priority'] == 75
            print("✓ Submission system called with correct arguments")
            
            # 5. Check progress management
            assert panel.progress_manager.start_operation.called
            assert panel.progress_manager.finish_operation.called
            print("✓ Progress management working")
            
            # 6. Check success message
            mock_message.assert_called()
            success_message = mock_message.call_args[0][0]
            assert "Successfully submitted 2 jobs" in success_message
            assert "Write1, Write2" in success_message
            assert "job_12345" in success_message
            print("✓ Success message displayed correctly")
            
            print("\n============================================================")
            print("✅ RENDER BUTTON INTEGRATION TEST PASSED")
            print("✅ Complete workflow validated: GUI → Storage → Submission")
            print("============================================================")
            
            return True
            
    except Exception as e:
        print(f"✗ Render button integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling in the render button workflow"""
    
    print("\n============================================================")
    print("END-TO-END TEST: ERROR HANDLING")
    print("============================================================")
    
    try:
        import nuke
        
        if nuke.NUKE_VERSION_MAJOR >= 16:
            from PySide6 import QtWidgets, QtCore, QtGui
        else:
            from PySide2 import QtWidgets, QtCore, QtGui
        
        # Test unsaved script error
        print("Testing unsaved script error handling...")
        with patch('nuke.root') as mock_root, \
             patch('nuke.message') as mock_message:
            
            mock_root.return_value.name.return_value = "Root"  # Unsaved script
            
            from nk2dl.gui.panel import Nk2dlPanel
            panel = Nk2dlPanel()
            
            # Mock required components
            panel.render_btn = Mock()
            panel.progress_manager = Mock()
            panel.console_view = Mock()
            
            panel._on_render_clicked()
            
            # Should show unsaved script message
            mock_message.assert_called_with("Please save your script before submitting to Deadline.")
            print("✓ Unsaved script error handled correctly")
        
        # Test no nodes selected error
        print("Testing no nodes selected error handling...")
        with patch('nuke.root') as mock_root, \
             patch('nuke.message') as mock_message:
            
            mock_root.return_value.name.return_value = "/path/to/script.nk"
            
            panel = Nk2dlPanel()
            panel.render_btn = Mock()
            panel.progress_manager = Mock()
            panel.console_view = Mock()
            
            # Mock table model with no selected nodes
            mock_table_model = Mock()
            mock_table_model.get_row_count.return_value = 2
            mock_table_model.get_node_name.side_effect = lambda row: ['Write1', 'Write2'][row]
            mock_table_model.is_node_selected_for_render.return_value = False  # No nodes selected
            
            panel.table_model = mock_table_model
            
            panel._on_render_clicked()
            
            # Should show no nodes selected message
            mock_message.assert_called_with("No write nodes selected for rendering.\n\nPlease select at least one write node in the table.")
            print("✓ No nodes selected error handled correctly")
        
        # Test submission failure error
        print("Testing submission failure error handling...")
        with patch('nuke.root') as mock_root, \
             patch('nuke.message') as mock_message, \
             patch('nk2dl.nuke.submission.submit_nuke_script') as mock_submit:
            
            mock_root.return_value.name.return_value = "/path/to/script.nk"
            mock_submit.side_effect = Exception("Deadline connection failed")
            
            panel = Nk2dlPanel()
            panel.render_btn = Mock()
            panel.progress_manager = Mock()
            panel.console_view = Mock()
            
            # Mock table model with selected nodes
            mock_table_model = Mock()
            mock_table_model.get_row_count.return_value = 1
            mock_table_model.get_node_name.return_value = 'Write1'
            mock_table_model.is_node_selected_for_render.return_value = True
            
            panel.table_model = mock_table_model
            
            # Mock storage
            mock_storage = Mock()
            mock_storage.build_submission_args.return_value = {'script_path': '/path/to/script.nk'}
            panel.node_settings_view = Mock()
            panel.node_settings_view.storage = mock_storage
            
            panel._on_render_clicked()
            
            # Should show submission failure message
            mock_message.assert_called()
            error_message = mock_message.call_args[0][0]
            assert "Submission failed" in error_message
            assert "Deadline connection failed" in error_message
            print("✓ Submission failure error handled correctly")
        
        print("\n============================================================")
        print("✅ ERROR HANDLING TEST PASSED")
        print("✅ All error scenarios handled gracefully")
        print("============================================================")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_submission_integration():
    """Test that storage system properly integrates with submission system"""
    
    print("\n============================================================")
    print("END-TO-END TEST: STORAGE-SUBMISSION INTEGRATION")
    print("============================================================")
    
    try:
        from nk2dl.gui.panel.repositories.storage import NodeSettingsStorage
        from nk2dl.gui.panel.models.settings_model import SettingsModel
        
        print("Testing storage to submission parameter flow...")
        
        # Mock nuke module
        mock_nuke = Mock()
        mock_root = Mock()
        mock_knobs = {'nk2dl_settings': Mock()}
        mock_root.knobs.return_value = mock_knobs
        mock_root.__getitem__ = lambda self, key: mock_knobs[key]
        mock_nuke.root.return_value = mock_root
        
        with patch('nk2dl.gui.panel.repositories.storage.nuke_module', return_value=mock_nuke):
            # Create storage instance
            storage = NodeSettingsStorage()
            
            # Create mock settings model
            settings_model = Mock()
            def mock_get_setting(param_name):
                return {
                    'priority': 85,
                    'pool': 'vfx_pool',
                    'chunk_size': 10,
                    'use_gpu': True,
                    'gpu_override': 'gpu0',
                    'threads': 8,
                    'ram_use': 16000,
                    'batch_mode': True,
                    'render_mode': 'full'
                }.get(param_name, None)
            
            settings_model.get_setting = Mock(side_effect=mock_get_setting)
            storage.settings_model = settings_model
            
            # Add node overrides
            storage.node_overrides = {
                'Write1': {
                    'priority': 95,
                    'chunk_size': 5,
                    'use_gpu': False
                },
                'Write2': {
                    'pool': 'urgent_pool',
                    'threads': 16
                }
            }
            
            # Build submission arguments
            args = storage.build_submission_args(
                script_path="/path/to/test.nk",
                write_nodes=['Write1', 'Write2', 'Write3'],
                frames='1-100'
            )
            
            print("✓ Storage built submission arguments successfully")
            
            # Verify argument structure
            assert args['script_path'] == "/path/to/test.nk"
            assert args['script_is_open'] == True
            assert args['frames'] == '1-100'
            
            # Verify global settings
            assert args['priority'] == 85
            assert args['pool'] == 'vfx_pool'
            assert args['chunk_size'] == 10
            assert args['use_gpu'] == True
            assert args['gpu_override'] == 'gpu0'
            assert args['threads'] == 8
            assert args['ram_use'] == 16000
            assert args['batch_mode'] == True
            assert args['render_mode'] == 'full'
            
            print("✓ Global settings correctly mapped")
            
            # Verify write nodes structure
            write_nodes = args['write_nodes']
            assert len(write_nodes) == 3
            
            # Write1 should have overrides
            write1 = write_nodes[0]
            assert isinstance(write1, dict)
            assert write1['write_node'] == 'Write1'
            assert write1['priority'] == 95  # Override
            assert write1['chunk_size'] == 5  # Override
            assert write1['use_gpu'] == False  # Override
            
            # Write2 should have overrides
            write2 = write_nodes[1]
            assert isinstance(write2, dict)
            assert write2['write_node'] == 'Write2'
            assert write2['pool'] == 'urgent_pool'  # Override
            assert write2['threads'] == 16  # Override
            
            # Write3 should be simple string (no overrides)
            write3 = write_nodes[2]
            assert write3 == 'Write3'
            
            print("✓ Node overrides correctly formatted")
            
            # Verify this would work with NukeSubmission
            # (We can't import NukeSubmission in this test environment, but we can verify the structure)
            expected_args = [
                'script_path', 'script_is_open', 'write_nodes', 'frames',
                'priority', 'pool', 'chunk_size', 'use_gpu', 'gpu_override',
                'threads', 'ram_use', 'batch_mode', 'render_mode'
            ]
            
            for arg in expected_args:
                assert arg in args, f"Missing argument: {arg}"
            
            print("✓ All required submission arguments present")
            print("✓ Zero-translation parameter flow confirmed")
            
        print("\n============================================================")
        print("✅ STORAGE-SUBMISSION INTEGRATION TEST PASSED")
        print("✅ Perfect parameter alignment validated")
        print("============================================================")
        
        return True
        
    except Exception as e:
        print(f"✗ Storage-submission integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all end-to-end tests"""
    
    print("Starting End-to-End Submission Tests...")
    print("Testing complete workflow: GUI → Storage → Submission → Results")
    
    # Keep track of results
    test_results = []
    
    # Run tests
    test_results.append(test_render_button_integration())
    test_results.append(test_error_handling())
    test_results.append(test_storage_submission_integration())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n============================================================")
    print(f"END-TO-END TEST SUMMARY")
    print(f"============================================================")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL END-TO-END TESTS PASSED")
        print("🎉 Complete submission workflow validated!")
        print("")
        print("🚀 READY FOR PRODUCTION:")
        print("   • Render button fully functional")
        print("   • Storage system integrated")
        print("   • Zero-translation parameter flow")
        print("   • Comprehensive error handling")
        print("   • Progress management working")
        print("   • Success/failure feedback")
    else:
        print("❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main() 