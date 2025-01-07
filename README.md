# BookChat

A real-time chat application that saves messages to multiple GitHub repositories.

## Features

- Real-time message updates
- Multi-repository support
- Message persistence in SQLite database
- GitHub integration with commit history
- Modern, responsive UI
- Message caching for performance

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/bookchat.git
cd bookchat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your GitHub configuration:
     ```
     # Primary repository
     GITHUB_REPO_1=owner/repository:your_github_token_here
     
     # Additional repositories (optional)
     GITHUB_REPO_2=another-owner/another-repo:another_token_here
     ```

4. GitHub Token Setup:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Create a new token with these permissions:
     - `repo` (Full control of private repositories)
     - `workflow` (Optional: if you want to trigger GitHub Actions)
   - Copy the token and add it to your `.env` file

5. Create the database:
   - The database will be automatically created when you first run the server
   - Default location: `chat.db` in the project root

## Environment Setup

BookChat provides a command-line utility to manage your environment variables:

```bash
# List all variables (hiding sensitive values)
./setup.py list

# List all variables (showing all values)
./setup.py list --show-values

# Get a specific variable
./setup.py get GITHUB_REPO_1

# Set a variable
./setup.py set PORT 8080

# Remove a variable
./setup.py remove GITHUB_REPO_2

# Add a new repository
./setup.py add-repo owner repo-name github_token
```

The setup utility will:
- Preserve comments and formatting
- Keep variables organized by category
- Hide sensitive values by default
- Validate repository configurations
- Maintain multiple repository entries

## Running the Application

1. Start the server:
```bash
python server.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Pushing to GitHub

You can push your changes to all configured repositories using the push command:

```bash
# Push from current directory
./push.py

# Push from specific directory
./push.py --repo-path /path/to/repo

# Push to specific branch
./push.py --branch develop
```

The push command will:
1. Initialize git repository if needed
2. Configure remotes for all repositories in .env
3. Add and commit any changes
4. Push to all configured repositories

## Environment Variables

- `GITHUB_REPO_[NUMBER]`: Repository configuration in format `owner/repo:token`
  - Example: `GITHUB_REPO_1=octocat/Hello-World:ghp_xxxxxxxxxxxxxxxxxxxx`
  - You can add multiple repositories by incrementing the number
- `PORT`: Server port (default: 8000)
- `CACHE_DURATION`: Message cache duration in minutes (default: 5)

## Repository Structure

- `server.py`: Main server implementation
- `database.py`: SQLite database management
- `repository_manager.py`: GitHub repository management
- `static/js/chat.js`: Frontend JavaScript
- `index.html`: Main web interface
- `test_*.py`: Test files

## Testing

Run the test suite:
```bash
python -m unittest discover -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
