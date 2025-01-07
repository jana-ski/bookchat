import http.server
import socketserver
import json
from pathlib import Path
from database import Database
from repository_manager import RepositoryManager
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure the server
PORT = 8000
DIRECTORY = Path(__file__).parent

# Initialize managers
db = Database()
repo_manager = RepositoryManager()

# Cache for repository messages
message_cache = {}
last_cache_update = datetime.now()
CACHE_DURATION = timedelta(minutes=5)

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/messages':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get messages from all repositories
            messages = self._get_all_messages()
            self.wfile.write(json.dumps({'messages': messages}).encode())
            return
            
        return super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            try:
                message = data.get('message')
                if not message:
                    raise ValueError("Message cannot be empty")
                
                # Save message to all configured repositories
                responses = []
                for repo in repo_manager.get_all_repositories():
                    try:
                        # Save to database first
                        repo_id = db.get_repository_id(repo.owner, repo.name)
                        if not repo_id:
                            repo_id = db.add_repository(repo.owner, repo.name)
                        
                        message_id = db.save_message(
                            message=message,
                            repository_id=repo_id
                        )
                        
                        # Create commit in GitHub
                        g = Github(repo.token)
                        github_repo = g.get_repo(repo.full_name)
                        
                        # Create file with message content
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        file_path = f"messages/{timestamp}.txt"
                        
                        commit = github_repo.create_file(
                            path=file_path,
                            message=message,
                            content=message.encode('utf-8')
                        )
                        
                        # Update database with commit URL
                        db.save_message(
                            message=message,
                            repository_id=repo_id,
                            github_url=commit['commit'].html_url,
                            commit_sha=commit['commit'].sha,
                            author=commit['commit'].author.name
                        )
                        
                        responses.append({
                            'repository': repo.full_name,
                            'status': 'success',
                            'github_url': commit['commit'].html_url
                        })
                        
                    except Exception as e:
                        responses.append({
                            'repository': repo.full_name,
                            'status': 'error',
                            'error': str(e)
                        })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'responses': responses
                }).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': str(e)
                }).encode())
            
            return
            
        return self.send_error(404)

    def _get_all_messages(self):
        """Get messages from all repositories with caching"""
        global last_cache_update, message_cache
        
        current_time = datetime.now()
        if (current_time - last_cache_update) < CACHE_DURATION and message_cache:
            return message_cache
        
        # Get messages from database
        messages = []
        for repo in repo_manager.get_all_repositories():
            repo_id = db.get_repository_id(repo.owner, repo.name)
            if repo_id:
                repo_messages = db.get_messages(repository_id=repo_id)
                messages.extend(repo_messages)
        
        # Sort all messages by timestamp
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Update cache
        message_cache = messages
        last_cache_update = current_time
        
        return messages

def run_server():
    """Run the HTTP server"""
    with socketserver.TCPServer(("", PORT), ChatRequestHandler) as httpd:
        print(f"Server running on port {PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()
