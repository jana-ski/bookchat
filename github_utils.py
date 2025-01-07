import os
import subprocess
from datetime import datetime
from github import Github
from pathlib import Path

class GitHubManager:
    def __init__(self, token=None, repo_name=None):
        self.token = token
        self.repo_name = repo_name
        self.g = Github(token) if token else None
        
    def clone_repository(self, repo_url, local_path):
        """Clone a repository to local path"""
        try:
            subprocess.run(['git', 'clone', repo_url, local_path], 
                         check=True, capture_output=True, text=True)
            print(f"Successfully cloned repository to {local_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            return False

    def push_file(self, file_path, commit_message, branch='main'):
        """Push a file to GitHub repository using git commands"""
        try:
            repo_path = str(Path(file_path).parent)
            file_name = Path(file_path).name
            
            # Add the file
            subprocess.run(['git', 'add', file_name], 
                         cwd=repo_path, check=True, capture_output=True, text=True)
            
            # Commit the changes
            subprocess.run(['git', 'commit', '-m', commit_message],
                         cwd=repo_path, check=True, capture_output=True, text=True)
            
            # Push to remote
            subprocess.run(['git', 'push', 'origin', branch],
                         cwd=repo_path, check=True, capture_output=True, text=True)
            
            print(f"Successfully pushed {file_name} to repository")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing file: {e.stderr}")
            return False

    def create_message_file(self, message, repo_path):
        """Create a file with a message and timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"message_{timestamp}.txt"
        file_path = os.path.join(repo_path, file_name)
        
        with open(file_path, 'w') as f:
            f.write(f"Message created at {timestamp}:\n\n{message}")
        
        return file_path

def main():
    # Replace these with your actual values
    GITHUB_TOKEN = "your_github_token"  # Don't hardcode in production
    REPO_NAME = "your_username/your_repo"
    REPO_URL = f"https://github.com/{REPO_NAME}.git"
    LOCAL_PATH = "local_repo"
    
    # Create GitHubManager instance
    gh_manager = GitHubManager(GITHUB_TOKEN, REPO_NAME)
    
    # Example usage
    if not os.path.exists(LOCAL_PATH):
        # Clone repository if it doesn't exist locally
        success = gh_manager.clone_repository(REPO_URL, LOCAL_PATH)
        if not success:
            print("Failed to clone repository")
            return
    
    # Create a message file
    message = "Hello from BookChat!"
    file_path = gh_manager.create_message_file(message, LOCAL_PATH)
    
    # Push the file
    commit_message = "Add new message file"
    success = gh_manager.push_file(file_path, commit_message)
    
    if success:
        print("Message successfully pushed to GitHub!")
    else:
        print("Failed to push message to GitHub")

if __name__ == "__main__":
    main()
