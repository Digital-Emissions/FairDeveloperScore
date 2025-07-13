import os
from dotenv import load_dotenv
load_dotenv()
# Replace the hardcoded secret with an environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') 