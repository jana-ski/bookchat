#!/usr/bin/env python3
import os
import sys
from github import Github
from dotenv import load_dotenv
import subprocess
from pathlib import Path
import argparse

def load_repositories():
    """Load repository configurations from .env file"""
    repos = []
    for key, value in os.environ.items():
        if key.startswith('GITHUB_REPO_'):
            try:
                repo_info = value.split(':')
                if len(repo_info) != 2:
                    continue
                owner_repo, token = repo_info
                repos.append((owner_repo, token))
            except ValueError:
                continue
    return repos

def git_command(cmd, cwd=None):
    """Run a git command and return its output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e.stderr}")
        return None

def push_repository(repo_path, remote_url, token, branch='main'):
    """Push repository to GitHub"""
    # Check if git is initialized
    git_dir = Path(repo_path) / '.git'
    if not git_dir.exists():
        print(f"Initializing git repository in {repo_path}")
        git_command(['git', 'init'], repo_path)

    # Configure remote
    remote_with_token = f"https://x-access-token:{token}@github.com/{remote_url}.git"
    
    # Check if remote exists
    remotes = git_command(['git', 'remote'], repo_path)
    if 'origin' not in (remotes or ''):
        print("Adding remote origin")
        git_command(['git', 'remote', 'add', 'origin', remote_with_token], repo_path)
    else:
        print("Updating remote origin")
        git_command(['git', 'remote', 'set-url', 'origin', remote_with_token], repo_path)

    # Add all files
    print("Adding files...")
    git_command(['git', 'add', '.'], repo_path)

    # Commit if there are changes
    status = git_command(['git', 'status', '--porcelain'], repo_path)
    if status:
        print("Committing changes...")
        git_command(['git', 'commit', '-m', 'Update chat messages and configuration'], repo_path)

    # Push to GitHub
    print(f"Pushing to {remote_url}...")
    result = git_command(['git', 'push', '-u', 'origin', branch], repo_path)
    
    if result is not None:
        print(f"Successfully pushed to {remote_url}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Push BookChat repositories to GitHub')
    parser.add_argument('--repo-path', default=os.getcwd(),
                      help='Path to the repository (default: current directory)')
    parser.add_argument('--branch', default='main',
                      help='Branch to push (default: main)')
    args = parser.parse_args()

    # Load environment variables
    env_path = Path(args.repo_path) / '.env'
    if not env_path.exists():
        print("Error: .env file not found. Please create one from .env.example")
        sys.exit(1)

    load_dotenv(env_path)
    
    # Get repository configurations
    repos = load_repositories()
    if not repos:
        print("Error: No repositories configured in .env file")
        sys.exit(1)

    # Push to each configured repository
    success = True
    for remote_url, token in repos:
        print(f"\nPushing to {remote_url}...")
        if not push_repository(args.repo_path, remote_url, token, args.branch):
            print(f"Failed to push to {remote_url}")
            success = False

    if success:
        print("\nSuccessfully pushed to all repositories!")
    else:
        print("\nSome repositories failed to push. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
