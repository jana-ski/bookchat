import unittest
import sqlite3
import os
import tempfile
from datetime import datetime
from database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        # Create a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = Database(self.db_path)

    def tearDown(self):
        """Clean up test database"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init_db(self):
        """Test database initialization"""
        # Verify the messages table exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='messages'
            """)
            self.assertIsNotNone(cursor.fetchone())

    def test_save_message(self):
        """Test saving a message"""
        message = "Test message"
        message_id = self.db.save_message(message)
        
        # Verify message was saved
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM messages WHERE id = ?", (message_id,))
            saved_message = cursor.fetchone()[0]
            self.assertEqual(saved_message, message)

    def test_save_message_with_github_url(self):
        """Test saving a message with GitHub URL"""
        message = "Test message with URL"
        github_url = "https://github.com/test/repo/commit/123"
        message_id = self.db.save_message(message)
        self.db.update_github_url(message_id, github_url)
        
        # Verify message and URL were saved
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message, github_url FROM messages WHERE id = ?", 
                (message_id,)
            )
            saved_message, saved_url = cursor.fetchone()
            self.assertEqual(saved_message, message)
            self.assertEqual(saved_url, github_url)

    def test_get_messages(self):
        """Test retrieving messages"""
        # Add multiple messages
        messages = [
            "First test message",
            "Second test message",
            "Third test message"
        ]
        for msg in messages:
            self.db.save_message(msg)
        
        # Retrieve and verify messages
        saved_messages = self.db.get_messages()
        self.assertEqual(len(saved_messages), 3)
        
        # Verify messages are in reverse chronological order
        self.assertEqual(saved_messages[0][1], messages[2])
        self.assertEqual(saved_messages[1][1], messages[1])
        self.assertEqual(saved_messages[2][1], messages[0])

    def test_get_messages_limit(self):
        """Test message retrieval limit"""
        # Add more messages than the default limit
        for i in range(150):
            self.db.save_message(f"Message {i}")
        
        # Verify limit works
        messages = self.db.get_messages(limit=50)
        self.assertEqual(len(messages), 50)

    def test_message_timestamp(self):
        """Test message timestamps"""
        message = "Test message with timestamp"
        message_id = self.db.save_message(message)
        
        # Verify timestamp format
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM messages WHERE id = ?", (message_id,))
            timestamp_str = cursor.fetchone()[0]
            
            # Verify it's a valid ISO format timestamp
            timestamp = datetime.fromisoformat(timestamp_str)
            self.assertIsInstance(timestamp, datetime)

    def test_update_nonexistent_message(self):
        """Test updating GitHub URL for non-existent message"""
        with self.assertRaises(sqlite3.Error):
            self.db.update_github_url(999, "https://github.com/test/repo")

    def test_message_sanitization(self):
        """Test message content sanitization"""
        # Test with potentially problematic characters
        message = "Test message with 'quotes' and \"double quotes\" and -- dashes"
        message_id = self.db.save_message(message)
        
        # Verify message was saved correctly
        saved_messages = self.db.get_messages()
        saved_message = next(msg for msg in saved_messages if msg[0] == message_id)
        self.assertEqual(saved_message[1], message)

    def test_concurrent_access(self):
        """Test concurrent database access"""
        import threading
        
        def save_messages(count):
            for i in range(count):
                self.db.save_message(f"Thread message {i}")
        
        # Create multiple threads to save messages
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_messages, args=(10,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify all messages were saved
        messages = self.db.get_messages()
        self.assertEqual(len(messages), 50)  # 5 threads * 10 messages each

if __name__ == '__main__':
    unittest.main()
