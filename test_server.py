import unittest
import json
import tempfile
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
import http.server
import threading
import requests
import time
from server import ChatRequestHandler, PORT
from database import Database
import socketserver

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up a test server in a separate thread"""
        # Create a temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.test_dir, 'test.db')
        
        # Mock the database and GitHub manager
        cls.mock_db = MagicMock(spec=Database)
        cls.mock_github = MagicMock()
        
        # Patch the database and GitHub manager in the server
        cls.db_patcher = patch('server.db', cls.mock_db)
        cls.github_patcher = patch('server.github_manager', cls.mock_github)
        cls.db_patcher.start()
        cls.github_patcher.start()
        
        # Start the server in a separate thread
        cls.server = socketserver.TCPServer(("", PORT), ChatRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Stop the server
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()
        
        # Stop the patches
        cls.db_patcher.stop()
        cls.github_patcher.stop()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Reset mock objects before each test"""
        self.mock_db.reset_mock()
        self.mock_github.reset_mock()
        
        # Set up mock returns
        self.mock_db.save_message.return_value = 1
        self.mock_github.create_message_file.return_value = "test_message.txt"
        self.mock_github.push_file.return_value = True
        self.mock_github.repo_name = "test/repo"

    def test_post_message_success(self):
        """Test successful message posting"""
        test_message = "Hello, this is a test message!"
        response = requests.post(
            f"http://localhost:{PORT}/chat",
            json={"message": test_message}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("github_url", data)
        
        # Verify database calls
        self.mock_db.save_message.assert_called_once_with(test_message)
        self.mock_db.update_github_url.assert_called_once()
        
        # Verify GitHub operations
        self.mock_github.create_message_file.assert_called_once()
        self.mock_github.push_file.assert_called_once()

    def test_post_message_no_message(self):
        """Test posting with empty message"""
        response = requests.post(
            f"http://localhost:{PORT}/chat",
            json={}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.mock_db.save_message.assert_called_once_with("")

    def test_post_message_github_failure(self):
        """Test handling of GitHub push failure"""
        # Set up mock to simulate GitHub failure
        self.mock_github.push_file.return_value = False
        
        test_message = "Test message with GitHub failure"
        response = requests.post(
            f"http://localhost:{PORT}/chat",
            json={"message": test_message}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "partial")
        self.assertIn("GitHub push failed", data["message"])
        
        # Verify database was still called
        self.mock_db.save_message.assert_called_once_with(test_message)

    def test_post_message_database_error(self):
        """Test handling of database error"""
        # Set up mock to simulate database error
        self.mock_db.save_message.side_effect = Exception("Database error")
        
        test_message = "Test message with database error"
        response = requests.post(
            f"http://localhost:{PORT}/chat",
            json={"message": test_message}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Database error", data["message"])

    def test_get_messages(self):
        """Test getting message history"""
        # Set up mock messages
        mock_messages = [
            (1, "Test message 1", "2025-01-07T16:13:39", "https://github.com/test/1"),
            (2, "Test message 2", "2025-01-07T16:13:40", "https://github.com/test/2")
        ]
        self.mock_db.get_messages.return_value = mock_messages
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 2)
        self.assertEqual(data["messages"][0]["message"], "Test message 1")
        
        # Verify database call
        self.mock_db.get_messages.assert_called_once()

    def test_get_messages_empty(self):
        """Test getting messages when database is empty"""
        # Set up mock to return empty list
        self.mock_db.get_messages.return_value = []
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 0)
        self.assertEqual(data["messages"], [])
        
        # Verify database call
        self.mock_db.get_messages.assert_called_once()

    def test_get_messages_multiple(self):
        """Test getting multiple messages"""
        # Set up mock messages with different timestamps and GitHub URLs
        mock_messages = [
            (1, "First message", "2025-01-07T16:15:39", "https://github.com/test/1"),
            (2, "Second message", "2025-01-07T16:15:40", "https://github.com/test/2"),
            (3, "Third message", "2025-01-07T16:15:41", "https://github.com/test/3")
        ]
        self.mock_db.get_messages.return_value = mock_messages
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify number of messages
        self.assertEqual(len(data["messages"]), 3)
        
        # Verify message order (should be in same order as mock data)
        self.assertEqual(data["messages"][0]["id"], 1)
        self.assertEqual(data["messages"][1]["id"], 2)
        self.assertEqual(data["messages"][2]["id"], 3)
        
        # Verify message content
        for i, msg in enumerate(data["messages"]):
            self.assertEqual(msg["id"], mock_messages[i][0])
            self.assertEqual(msg["message"], mock_messages[i][1])
            self.assertEqual(msg["timestamp"], mock_messages[i][2])
            self.assertEqual(msg["github_url"], mock_messages[i][3])

    def test_get_messages_with_null_github_urls(self):
        """Test getting messages with null GitHub URLs"""
        # Set up mock messages with some null GitHub URLs
        mock_messages = [
            (1, "Message with URL", "2025-01-07T16:15:39", "https://github.com/test/1"),
            (2, "Message without URL", "2025-01-07T16:15:40", None),
            (3, "Another with URL", "2025-01-07T16:15:41", "https://github.com/test/3")
        ]
        self.mock_db.get_messages.return_value = mock_messages
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify handling of null GitHub URLs
        self.assertIsNone(data["messages"][1]["github_url"])
        self.assertIsNotNone(data["messages"][0]["github_url"])
        self.assertIsNotNone(data["messages"][2]["github_url"])

    def test_get_messages_database_error(self):
        """Test handling of database errors during message retrieval"""
        # Set up mock to simulate database error
        self.mock_db.get_messages.side_effect = Exception("Database error")
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Database error", str(data["error"]))

    def test_get_messages_content_type(self):
        """Test that the response has the correct content type"""
        self.mock_db.get_messages.return_value = []
        
        response = requests.get(f"http://localhost:{PORT}/messages")
        
        # Check content type header
        self.assertEqual(response.headers['Content-Type'], 'application/json')

if __name__ == '__main__':
    unittest.main()
