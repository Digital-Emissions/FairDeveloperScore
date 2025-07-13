import os
from dotenv import load_dotenv
from github import Github

# Load environment variables from .env file
load_dotenv()

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Use the token to create a Github instance
g = Github(GITHUB_TOKEN)

# ... rest of your script 