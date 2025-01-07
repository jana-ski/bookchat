import sqlite3
from datetime import datetime
from typing import List, Optional

class Database:
    def __init__(self, db_path: str = 'chat.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    name TEXT NOT NULL,
                    last_sync TIMESTAMP,
                    UNIQUE(owner, name)
                )
            """)
            
            # Create messages table with repository reference
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    github_url TEXT,
                    commit_sha TEXT,
                    author TEXT,
                    FOREIGN KEY (repository_id) REFERENCES repositories(id)
                )
            """)
            
            conn.commit()

    def add_repository(self, owner: str, name: str) -> int:
        """Add a new repository to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO repositories (owner, name) VALUES (?, ?)",
                (owner, name)
            )
            conn.commit()
            
            # Get the repository ID
            cursor.execute(
                "SELECT id FROM repositories WHERE owner = ? AND name = ?",
                (owner, name)
            )
            return cursor.fetchone()[0]

    def save_message(self, message: str, repository_id: int, github_url: Optional[str] = None,
                    commit_sha: Optional[str] = None, author: Optional[str] = None) -> int:
        """Save a message with repository information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages 
                (message, repository_id, github_url, commit_sha, author)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message, repository_id, github_url, commit_sha, author)
            )
            conn.commit()
            return cursor.lastrowid

    def get_messages(self, limit: int = 100, repository_id: Optional[int] = None) -> List[dict]:
        """Get messages with optional repository filter"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT m.*, r.owner, r.name
                FROM messages m
                JOIN repositories r ON m.repository_id = r.id
            """
            
            params = []
            if repository_id is not None:
                query += " WHERE m.repository_id = ?"
                params.append(repository_id)
            
            query += " ORDER BY m.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'message': row['message'],
                    'timestamp': row['timestamp'],
                    'github_url': row['github_url'],
                    'repository': f"{row['owner']}/{row['name']}",
                    'author': row['author'],
                    'commit_sha': row['commit_sha']
                })
            
            return messages

    def update_repository_sync(self, repository_id: int):
        """Update the last sync time for a repository"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE repositories SET last_sync = ? WHERE id = ?",
                (datetime.now().isoformat(), repository_id)
            )
            conn.commit()

    def get_repository_id(self, owner: str, name: str) -> Optional[int]:
        """Get repository ID by owner and name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM repositories WHERE owner = ? AND name = ?",
                (owner, name)
            )
            result = cursor.fetchone()
            return result[0] if result else None
