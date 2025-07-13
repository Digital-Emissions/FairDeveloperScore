import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

TOP_N = 500  # 300 is the number of most starred repos that We want to get on Github，can be changed to any number
PER_PAGE = 100 
repo_list = []

for page in range(1, (TOP_N // PER_PAGE) + 1):
    print(f"Fetching page {page}...")
    response = requests.get(
        f"https://api.github.com/search/repositories",
        headers=headers,
        params={
            "q": "stars:>10000",
            "sort": "stars",
            "order": "desc",
            "per_page": PER_PAGE,
            "page": page
        }
    )

    if response.status_code != 200:
        print("❌ Failed:", response.status_code, response.text)
        break

    data = response.json()
    for item in data["items"]:
        full_name = item["full_name"]  # like 'torvalds/linux'
        repo_list.append(full_name)

# save to local txt file
with open("top_500_repos.txt", "w") as f:
    for repo in repo_list:
        f.write(repo + "\n")

print(f"✅ Fetched {len(repo_list)} top starred repos")
