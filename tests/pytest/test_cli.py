"""Tests for the CLI parser."""

import sys
import unittest
from unittest.mock import patch

from nk2dl.cli.parser import parse_args, create_parser


class TestCLIParser(unittest.TestCase):
    """Tests for the CLI argument parser."""
    
    def test_create_parser(self):
        """Test creating the parser."""
        parser = create_parser()
        self.assertIsNotNone(parser)
        
    def test_submit_command(self):
        """Test parsing submit command arguments."""
        with patch.object(sys, 'argv', ['nk2dl', 'submit', 'test.nk']):
            args = parse_args(['submit', 'test.nk'])
            self.assertEqual(args.command, 'submit')
            self.assertEqual(args.script_path, 'test.nk')
            
    def test_config_list_command(self):
        """Test parsing config list command arguments."""
        with patch.object(sys, 'argv', ['nk2dl', 'config', 'list']):
            args = parse_args(['config', 'list'])
            self.assertEqual(args.command, 'config')
            self.assertEqual(args.config_command, 'list')
            
    def test_submit_with_options(self):
        """Test parsing submit command with options."""
        with patch.object(sys, 'argv', [
            'nk2dl', 'submit', 'test.nk',
            '--Priority', '75',
            '--Pool', 'comp',
            '--Frames', '1-100',
            '--FramesPerTask', '10',
            '--UseNukeX'
        ]):
            args = parse_args([
                'submit', 'test.nk',
                '--Priority', '75',
                '--Pool', 'comp',
                '--Frames', '1-100',
                '--FramesPerTask', '10',
                '--UseNukeX'
            ])
            self.assertEqual(args.command, 'submit')
            self.assertEqual(args.script_path, 'test.nk')
            self.assertEqual(args.Priority, 75)
            self.assertEqual(args.Pool, 'comp')
            self.assertEqual(args.Frames, '1-100')
            self.assertEqual(args.FramesPerTask, 10)
            self.assertTrue(args.UseNukeX)


if __name__ == '__main__':
    unittest.main() 