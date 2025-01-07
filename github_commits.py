from github import Github
from datetime import datetime
from typing import List, Dict, Optional
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommitInfo:
    """Structured information about a commit"""
    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: datetime
    url: str
    changes: Dict[str, int]  # Number of additions/deletions per file

class GitHubCommitFetcher:
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """Initialize the GitHub commit fetcher
        
        Args:
            token: GitHub personal access token. If None, uses GITHUB_TOKEN env var
            repo_name: Repository name in format 'owner/repo'. If None, uses GITHUB_REPO env var
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN env var not set")
            
        self.repo_name = repo_name or os.getenv('GITHUB_REPO')
        if not self.repo_name:
            raise ValueError("Repository name not provided and GITHUB_REPO env var not set")
            
        self.github = Github(self.token)
        
    def get_commits(self, 
                   branch: str = "main", 
                   since: Optional[datetime] = None,
                   until: Optional[datetime] = None,
                   path: Optional[str] = None,
                   max_count: int = 100) -> List[CommitInfo]:
        """Fetch commits from the repository
        
        Args:
            branch: Branch name to fetch commits from
            since: Only show commits after this timestamp
            until: Only show commits before this timestamp
            path: Only show commits touching this file/directory
            max_count: Maximum number of commits to fetch
            
        Returns:
            List of CommitInfo objects containing structured commit data
        """
        try:
            repo = self.github.get_repo(self.repo_name)
            commits = repo.get_commits(sha=branch, 
                                    since=since,
                                    until=until,
                                    path=path)
            
            result = []
            for commit in commits[:max_count]:
                # Get detailed commit info
                files_changed = {
                    file.filename: {
                        'additions': file.additions,
                        'deletions': file.deletions
                    }
                    for file in commit.files
                }
                
                # Create structured commit info
                commit_info = CommitInfo(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author_name=commit.commit.author.name,
                    author_email=commit.commit.author.email,
                    timestamp=commit.commit.author.date,
                    url=commit.html_url,
                    changes=files_changed
                )
                result.append(commit_info)
                
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching commits: {str(e)}")
            
    def get_commit_stats(self, commits: List[CommitInfo]) -> Dict:
        """Generate statistics about the commits
        
        Args:
            commits: List of CommitInfo objects
            
        Returns:
            Dictionary containing commit statistics
        """
        stats = {
            'total_commits': len(commits),
            'authors': {},
            'files_changed': set(),
            'commit_times': {
                'hour': {},
                'day': {},
                'month': {}
            }
        }
        
        for commit in commits:
            # Author stats
            if commit.author_name not in stats['authors']:
                stats['authors'][commit.author_name] = 0
            stats['authors'][commit.author_name] += 1
            
            # Files changed
            stats['files_changed'].update(commit.changes.keys())
            
            # Time stats
            hour = commit.timestamp.hour
            day = commit.timestamp.strftime('%A')
            month = commit.timestamp.strftime('%B')
            
            if hour not in stats['commit_times']['hour']:
                stats['commit_times']['hour'][hour] = 0
            stats['commit_times']['hour'][hour] += 1
            
            if day not in stats['commit_times']['day']:
                stats['commit_times']['day'][day] = 0
            stats['commit_times']['day'][day] += 1
            
            if month not in stats['commit_times']['month']:
                stats['commit_times']['month'][month] = 0
            stats['commit_times']['month'][month] += 1
        
        # Convert files_changed to list for JSON serialization
        stats['files_changed'] = list(stats['files_changed'])
        
        return stats

def main():
    """Example usage of the GitHubCommitFetcher"""
    # Initialize fetcher using environment variables
    fetcher = GitHubCommitFetcher()
    
    # Get commits from the last month
    from datetime import timedelta
    since_date = datetime.now() - timedelta(days=30)
    
    commits = fetcher.get_commits(since=since_date)
    
    # Print commit messages
    print("\nRecent commits:")
    for commit in commits:
        print(f"\nCommit: {commit.sha[:8]}")
        print(f"Author: {commit.author_name}")
        print(f"Date: {commit.timestamp}")
        print(f"Message: {commit.message}")
        print(f"URL: {commit.url}")
        print("Files changed:")
        for file, changes in commit.changes.items():
            print(f"  - {file}: +{changes['additions']}, -{changes['deletions']}")
    
    # Generate and print statistics
    stats = fetcher.get_commit_stats(commits)
    
    print("\nCommit Statistics:")
    print(f"Total commits: {stats['total_commits']}")
    print("\nTop contributors:")
    for author, count in sorted(stats['authors'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {author}: {count} commits")
    
    print("\nMost active hours:")
    for hour, count in sorted(stats['commit_times']['hour'].items()):
        print(f"  {hour:02d}:00 - {count} commits")

if __name__ == "__main__":
    main()
