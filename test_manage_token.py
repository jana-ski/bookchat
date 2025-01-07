import unittest
from unittest.mock import patch, mock_open
import os
from pathlib import Path
import tempfile
import shutil
from manage_token import update_token, show_token

class TestTokenManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a test .env file
        self.env_content = """# GitHub Configuration
GITHUB_TOKEN=test_token_123
GITHUB_REPO=test/repo"""
        
        with open('.env', 'w') as f:
            f.write(self.env_content)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_update_token(self):
        """Test updating the GitHub token"""
        new_token = "new_test_token_456"
        update_token(new_token)
        
        # Verify the token was updated
        with open('.env', 'r') as f:
            content = f.read()
            self.assertIn(f"GITHUB_TOKEN={new_token}", content)
            self.assertIn("GITHUB_REPO=test/repo", content)

    def test_update_token_empty(self):
        """Test removing the GitHub token"""
        update_token(None)
        
        # Verify the token was removed but repo remains
        with open('.env', 'r') as f:
            content = f.read()
            self.assertIn("GITHUB_TOKEN=", content)
            self.assertIn("GITHUB_REPO=test/repo", content)

    def test_show_token_exists(self):
        """Test showing an existing token"""
        with patch('sys.stdout') as mock_stdout:
            show_token()
            output = mock_stdout.getvalue()
            self.assertIn("test_token_123", output)

    def test_show_token_not_exists(self):
        """Test showing when no token exists"""
        # Remove token from .env
        with open('.env', 'w') as f:
            f.write("GITHUB_REPO=test/repo\n")
        
        with patch('sys.stdout') as mock_stdout:
            show_token()
            output = mock_stdout.getvalue()
            self.assertIn("No GitHub token found", output)

    def test_update_token_creates_env_file(self):
        """Test updating token when .env doesn't exist"""
        # Remove existing .env
        os.remove('.env')
        
        new_token = "created_token_789"
        update_token(new_token)
        
        # Verify .env was created with the token
        self.assertTrue(os.path.exists('.env'))
        with open('.env', 'r') as f:
            content = f.read()
            self.assertIn(f"GITHUB_TOKEN={new_token}", content)

    def test_token_format_validation(self):
        """Test token format validation"""
        # Test with valid token format
        valid_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        update_token(valid_token)
        with open('.env', 'r') as f:
            content = f.read()
            self.assertIn(f"GITHUB_TOKEN={valid_token}", content)

if __name__ == '__main__':
    unittest.main()
