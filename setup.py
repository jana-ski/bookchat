#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse
from typing import Dict, Optional
import re
from dotenv import load_dotenv

class EnvManager:
    def __init__(self, env_path: str = '.env'):
        self.env_path = Path(env_path)
        self.env_example_path = Path(str(env_path) + '.example')
        self._load_env()

    def _load_env(self):
        """Load current environment variables"""
        self.current_vars = {}
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            self.current_vars[key.strip()] = value.strip()
                        except ValueError:
                            continue

    def _load_example_vars(self) -> Dict[str, str]:
        """Load variables from .env.example with comments"""
        example_vars = {}
        if not self.env_example_path.exists():
            return example_vars

        current_comment = []
        with open(self.env_example_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                if line.startswith('#'):
                    current_comment.append(line)
                elif line:
                    try:
                        key, value = line.split('=', 1)
                        example_vars[key.strip()] = {
                            'value': value.strip(),
                            'comments': current_comment.copy()
                        }
                        current_comment = []
                    except ValueError:
                        continue
                else:
                    current_comment = []
        return example_vars

    def list_vars(self, show_values: bool = False):
        """List all environment variables"""
        example_vars = self._load_example_vars()
        
        print("\nEnvironment Variables:")
        print("=====================")
        
        # First, show repository variables
        repo_vars = {k: v for k, v in self.current_vars.items() if k.startswith('GITHUB_REPO_')}
        if repo_vars:
            print("\nConfigured Repositories:")
            for key, value in sorted(repo_vars.items()):
                if show_values:
                    print(f"{key} = {value}")
                else:
                    repo_info = value.split(':')[0] if ':' in value else value
                    print(f"{key} = {repo_info}:****")

        # Then show other variables
        other_vars = {k: v for k, v in self.current_vars.items() if not k.startswith('GITHUB_REPO_')}
        if other_vars:
            print("\nOther Settings:")
            for key, value in sorted(other_vars.items()):
                if key in example_vars:
                    for comment in example_vars[key]['comments']:
                        print(comment)
                print(f"{key} = {value}")

        # Show unconfigured example variables
        unconfigured = {k: v for k, v in example_vars.items() if k not in self.current_vars}
        if unconfigured:
            print("\nUnconfigured Variables:")
            for key, data in unconfigured.items():
                for comment in data['comments']:
                    print(comment)
                print(f"{key} (example: {data['value']})")

    def get_var(self, key: str) -> Optional[str]:
        """Get a specific environment variable"""
        return self.current_vars.get(key)

    def set_var(self, key: str, value: str):
        """Set a specific environment variable"""
        self.current_vars[key] = value
        self._save_env()

    def remove_var(self, key: str):
        """Remove a specific environment variable"""
        if key in self.current_vars:
            del self.current_vars[key]
            self._save_env()

    def _save_env(self):
        """Save current variables to .env file"""
        example_vars = self._load_example_vars()
        
        with open(self.env_path, 'w') as f:
            # Write repositories first
            repo_vars = {k: v for k, v in self.current_vars.items() if k.startswith('GITHUB_REPO_')}
            if repo_vars:
                f.write("# GitHub Repository Configuration\n")
                for key, value in sorted(repo_vars.items()):
                    f.write(f"{key}={value}\n")
                f.write("\n")

            # Write other variables
            other_vars = {k: v for k, v in self.current_vars.items() if not k.startswith('GITHUB_REPO_')}
            if other_vars:
                f.write("# Other Settings\n")
                for key, value in sorted(other_vars.items()):
                    if key in example_vars:
                        for comment in example_vars[key]['comments']:
                            f.write(f"{comment}\n")
                    f.write(f"{key}={value}\n")

    def add_repository(self, owner: str, name: str, token: str):
        """Add a new GitHub repository"""
        # Find the next available repository number
        repo_nums = [int(k.split('_')[2]) for k in self.current_vars.keys()
                    if k.startswith('GITHUB_REPO_') and k.split('_')[2].isdigit()]
        next_num = max(repo_nums, default=0) + 1
        
        key = f"GITHUB_REPO_{next_num}"
        value = f"{owner}/{name}:{token}"
        self.set_var(key, value)
        print(f"Added repository: {owner}/{name}")

def main():
    parser = argparse.ArgumentParser(description='Manage BookChat environment variables')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List all environment variables')
    list_parser.add_argument('--show-values', action='store_true', 
                            help='Show actual values (including tokens)')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get a specific variable')
    get_parser.add_argument('key', help='Variable name')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set a specific variable')
    set_parser.add_argument('key', help='Variable name')
    set_parser.add_argument('value', help='Variable value')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a specific variable')
    remove_parser.add_argument('key', help='Variable name')

    # Add repository command
    repo_parser = subparsers.add_parser('add-repo', help='Add a GitHub repository')
    repo_parser.add_argument('owner', help='Repository owner')
    repo_parser.add_argument('name', help='Repository name')
    repo_parser.add_argument('token', help='GitHub token')

    args = parser.parse_args()

    env_manager = EnvManager()

    if args.command == 'list':
        env_manager.list_vars(args.show_values)
    elif args.command == 'get':
        value = env_manager.get_var(args.key)
        if value:
            print(f"{args.key} = {value}")
        else:
            print(f"Variable {args.key} not found")
    elif args.command == 'set':
        env_manager.set_var(args.key, args.value)
        print(f"Set {args.key} = {args.value}")
    elif args.command == 'remove':
        env_manager.remove_var(args.key)
        print(f"Removed {args.key}")
    elif args.command == 'add-repo':
        env_manager.add_repository(args.owner, args.name, args.token)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
