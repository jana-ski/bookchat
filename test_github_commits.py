import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from github_commits import GitHubCommitFetcher, CommitInfo

class TestGitHubCommitFetcher(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.token = "test_token"
        self.repo_name = "test/repo"
        
        # Create mock commit data
        self.mock_commit = MagicMock()
        self.mock_commit.sha = "abc123"
        self.mock_commit.commit.message = "Test commit"
        self.mock_commit.commit.author.name = "Test Author"
        self.mock_commit.commit.author.email = "test@example.com"
        self.mock_commit.commit.author.date = datetime(2025, 1, 7, 16, 16, 35, tzinfo=timezone.utc)
        self.mock_commit.html_url = "https://github.com/test/repo/commit/abc123"
        
        # Mock file changes
        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.additions = 10
        mock_file.deletions = 5
        self.mock_commit.files = [mock_file]

    def test_init_with_params(self):
        """Test initialization with explicit parameters"""
        fetcher = GitHubCommitFetcher(token=self.token, repo_name=self.repo_name)
        self.assertEqual(fetcher.token, self.token)
        self.assertEqual(fetcher.repo_name, self.repo_name)

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token', 'GITHUB_REPO': 'env/repo'})
    def test_init_with_env_vars(self):
        """Test initialization using environment variables"""
        fetcher = GitHubCommitFetcher()
        self.assertEqual(fetcher.token, 'env_token')
        self.assertEqual(fetcher.repo_name, 'env/repo')

    def test_init_without_token(self):
        """Test initialization without token raises error"""
        with self.assertRaises(ValueError):
            GitHubCommitFetcher(repo_name=self.repo_name)

    @patch('github.Github')
    def test_get_commits(self, mock_github):
        """Test fetching commits"""
        # Set up mock
        mock_repo = MagicMock()
        mock_repo.get_commits.return_value = [self.mock_commit]
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Create fetcher and get commits
        fetcher = GitHubCommitFetcher(self.token, self.repo_name)
        commits = fetcher.get_commits(max_count=1)
        
        # Verify results
        self.assertEqual(len(commits), 1)
        commit = commits[0]
        self.assertEqual(commit.sha, "abc123")
        self.assertEqual(commit.message, "Test commit")
        self.assertEqual(commit.author_name, "Test Author")
        self.assertEqual(commit.author_email, "test@example.com")
        self.assertEqual(commit.url, "https://github.com/test/repo/commit/abc123")
        self.assertEqual(commit.changes["test.py"]["additions"], 10)
        self.assertEqual(commit.changes["test.py"]["deletions"], 5)

    @patch('github.Github')
    def test_get_commits_with_filters(self, mock_github):
        """Test fetching commits with filters"""
        # Set up mock
        mock_repo = MagicMock()
        mock_repo.get_commits.return_value = [self.mock_commit]
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Create fetcher
        fetcher = GitHubCommitFetcher(self.token, self.repo_name)
        
        # Test with filters
        since = datetime(2025, 1, 1)
        until = datetime(2025, 1, 7)
        path = "src"
        
        commits = fetcher.get_commits(
            branch="dev",
            since=since,
            until=until,
            path=path
        )
        
        # Verify that filters were passed to GitHub API
        mock_repo.get_commits.assert_called_with(
            sha="dev",
            since=since,
            until=until,
            path=path
        )

    def test_get_commit_stats(self):
        """Test generating commit statistics"""
        fetcher = GitHubCommitFetcher(self.token, self.repo_name)
        
        # Create test commit data
        commit1 = CommitInfo(
            sha="abc123",
            message="Test commit 1",
            author_name="Alice",
            author_email="alice@example.com",
            timestamp=datetime(2025, 1, 7, 14, 0),
            url="https://github.com/test/1",
            changes={"file1.py": {"additions": 10, "deletions": 5}}
        )
        
        commit2 = CommitInfo(
            sha="def456",
            message="Test commit 2",
            author_name="Bob",
            author_email="bob@example.com",
            timestamp=datetime(2025, 1, 7, 15, 0),
            url="https://github.com/test/2",
            changes={"file2.py": {"additions": 20, "deletions": 8}}
        )
        
        # Generate stats
        stats = fetcher.get_commit_stats([commit1, commit2])
        
        # Verify statistics
        self.assertEqual(stats['total_commits'], 2)
        self.assertEqual(len(stats['authors']), 2)
        self.assertEqual(stats['authors']['Alice'], 1)
        self.assertEqual(stats['authors']['Bob'], 1)
        self.assertEqual(len(stats['files_changed']), 2)
        self.assertIn('file1.py', stats['files_changed'])
        self.assertIn('file2.py', stats['files_changed'])
        
        # Verify time stats
        self.assertEqual(stats['commit_times']['hour'][14], 1)
        self.assertEqual(stats['commit_times']['hour'][15], 1)

if __name__ == '__main__':
    unittest.main()
