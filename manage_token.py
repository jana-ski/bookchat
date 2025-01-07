#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
import argparse

def update_token(token: str = None):
    """Update the GitHub token in the .env file"""
    env_path = Path('.env')
    
    # Load existing environment variables
    load_dotenv()
    current_repo = os.getenv('GITHUB_REPO', 'jana-ski/bookchat')
    
    # Create or update .env file
    with open(env_path, 'w') as f:
        f.write(f"# GitHub Configuration\n")
        f.write(f"GITHUB_TOKEN={token or ''}\n")
        f.write(f"GITHUB_REPO={current_repo}\n")
    
    print(f"GitHub token {'updated' if token else 'removed'} successfully.")

def show_token():
    """Display the current GitHub token"""
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    if token:
        print(f"Current GitHub token: {token[:4]}...{token[-4:]}")
    else:
        print("No GitHub token found.")

def main():
    parser = argparse.ArgumentParser(description='Manage GitHub API token')
    parser.add_argument('--update', help='Update GitHub token')
    parser.add_argument('--show', action='store_true', help='Show current token')
    parser.add_argument('--remove', action='store_true', help='Remove current token')
    
    args = parser.parse_args()
    
    if args.update:
        update_token(args.update)
    elif args.show:
        show_token()
    elif args.remove:
        update_token()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
