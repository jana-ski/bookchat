from dataclasses import dataclass
from typing import List, Optional
import os
from github import Github
from datetime import datetime

@dataclass
class Repository:
    owner: str
    name: str
    token: str
    last_sync: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

class RepositoryManager:
    def __init__(self):
        self.repositories: List[Repository] = []
        self._load_repositories_from_env()

    def _load_repositories_from_env(self):
        """Load repository configurations from environment variables"""
        # Format: GITHUB_REPO_1=owner/name:token
        #         GITHUB_REPO_2=owner/name:token
        for key, value in os.environ.items():
            if key.startswith('GITHUB_REPO_'):
                try:
                    repo_info = value.split(':')
                    if len(repo_info) != 2:
                        continue
                    
                    owner_repo, token = repo_info
                    owner, name = owner_repo.split('/')
                    
                    self.add_repository(owner, name, token)
                except ValueError:
                    continue

    def add_repository(self, owner: str, name: str, token: str) -> Repository:
        """Add a new repository to track"""
        repo = Repository(owner=owner, name=name, token=token)
        self.repositories.append(repo)
        return repo

    def remove_repository(self, owner: str, name: str):
        """Remove a repository from tracking"""
        self.repositories = [
            repo for repo in self.repositories 
            if not (repo.owner == owner and repo.name == name)
        ]

    def get_all_repositories(self) -> List[Repository]:
        """Get all tracked repositories"""
        return self.repositories

    def get_repository(self, owner: str, name: str) -> Optional[Repository]:
        """Get a specific repository by owner and name"""
        for repo in self.repositories:
            if repo.owner == owner and repo.name == name:
                return repo
        return None

    async def fetch_messages_from_all(self) -> List[dict]:
        """Fetch messages from all repositories"""
        all_messages = []
        
        for repo in self.repositories:
            try:
                g = Github(repo.token)
                github_repo = g.get_repo(repo.full_name)
                
                # Get commits from the repository
                commits = github_repo.get_commits()
                
                for commit in commits:
                    message = {
                        'repository': repo.full_name,
                        'message': commit.commit.message,
                        'timestamp': commit.commit.author.date.isoformat(),
                        'author': commit.commit.author.name,
                        'github_url': commit.html_url,
                        'sha': commit.sha
                    }
                    all_messages.append(message)
                
                # Update last sync time
                repo.last_sync = datetime.now()
                
            except Exception as e:
                print(f"Error fetching from {repo.full_name}: {str(e)}")
                continue
        
        # Sort all messages by timestamp
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_messages
