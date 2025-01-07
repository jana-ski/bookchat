import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from pathlib import Path
from github_utils import GitHubManager

class TestGitHubManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.gh_manager = GitHubManager(token="dummy_token", repo_name="test/repo")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_clone_repository(self, mock_run):
        # Setup mock
        mock_run.return_value.returncode = 0
        
        # Test successful clone
        result = self.gh_manager.clone_repository(
            "https://github.com/test/repo.git",
            self.test_dir
        )
        
        # Assertions
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ['git', 'clone', 'https://github.com/test/repo.git', self.test_dir],
            check=True, capture_output=True, text=True
        )

    @patch('subprocess.run')
    def test_push_file(self, mock_run):
        # Create a test file
        test_file = Path(self.test_dir) / "test_message.txt"
        test_file.write_text("Test message")
        
        # Setup mock
        mock_run.return_value.returncode = 0
        
        # Test successful push
        result = self.gh_manager.push_file(
            str(test_file),
            "Test commit message"
        )
        
        # Assertions
        self.assertTrue(result)
        expected_calls = [
            unittest.mock.call(['git', 'add', 'test_message.txt'],
                             cwd=self.test_dir, check=True, capture_output=True, text=True),
            unittest.mock.call(['git', 'commit', '-m', 'Test commit message'],
                             cwd=self.test_dir, check=True, capture_output=True, text=True),
            unittest.mock.call(['git', 'push', 'origin', 'main'],
                             cwd=self.test_dir, check=True, capture_output=True, text=True)
        ]
        self.assertEqual(mock_run.call_count, 3)
        mock_run.assert_has_calls(expected_calls)

    def test_create_message_file(self):
        # Test file creation
        message = "Test message content"
        file_path = self.gh_manager.create_message_file(message, self.test_dir)
        
        # Assertions
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn("Test message content", content)
            self.assertIn("Message created at", content)

    @patch('subprocess.run')
    def test_failed_clone(self, mock_run):
        # Setup mock to simulate failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git clone', stderr="Error: repository not found"
        )
        
        # Test failed clone
        result = self.gh_manager.clone_repository(
            "https://github.com/nonexistent/repo.git",
            self.test_dir
        )
        
        # Assertions
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_failed_push(self, mock_run):
        # Create a test file
        test_file = Path(self.test_dir) / "test_message.txt"
        test_file.write_text("Test message")
        
        # Setup mock to simulate failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git push', stderr="Error: push failed"
        )
        
        # Test failed push
        result = self.gh_manager.push_file(
            str(test_file),
            "Test commit message"
        )
        
        # Assertions
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
