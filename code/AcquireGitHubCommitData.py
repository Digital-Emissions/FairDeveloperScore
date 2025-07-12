"""
GitHub Commit Collector (Last 300 Commits per Repo)

This script asynchronously collects the most recent ~300 commits for each repository 
listed in top_500_repos.txt. For each commit, it retrieves:
- Commit SHA
- Author name
- Commit date
- Commit message
- Lines added, deleted, and total changes

Each repo’s data is saved immediately into a separate CSV file under 'data/commit_data/'.
If GitHub API tokens are exhausted, processed repo names are saved to completed_repos.txt
to ensure resumability after restart.

Requirements:
- top_500_repos.txt (one line per repo: owner/repo)
- GitHub personal access tokens with repo read access
"""

import asyncio
import httpx
import csv
import time
import os
from datetime import datetime

# 🔐 Your GitHub PATs (rotate for rate limiting)
GITHUB_TOKENS = [
    "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",
    "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",
    "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"
]

# 📄 Load repositories
with open("top_500_repos.txt", "r") as f:
    REPO_LIST = [line.strip() for line in f if line.strip()]

# 🔁 Token rate limit tracking
token_states = {token: {"remaining": 5000, "reset": 0} for token in GITHUB_TOKENS}

def get_valid_token():
    now = int(time.time())
    for token in GITHUB_TOKENS:
        state = token_states[token]
        if state["remaining"] > 1 or now >= state["reset"]:
            return token
    return None

async def update_token_state(token, client):
    url = "https://api.github.com/rate_limit"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    try:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            core = data.get("rate", {})
            token_states[token]["remaining"] = core.get("remaining", 0)
            token_states[token]["reset"] = core.get("reset", int(time.time()) + 60)
    except Exception as e:
        print(f"⚠️ Failed to update token state: {e}")

# 🌐 Safe GET with token rotation and retry
async def safe_get(client, url, retries=3, delay=1.5):
    for attempt in range(retries):
        token = get_valid_token()
        if not token:
            reset_times = [state["reset"] for state in token_states.values()]
            wait_time = min(reset_times) - int(time.time())
            wait_time = max(wait_time, 5)
            print(f"⏳ All tokens exhausted. Waiting {wait_time} seconds for reset...")
            await asyncio.sleep(wait_time)
            continue

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            resp = await client.get(url, headers=headers)
            await update_token_state(token, client)

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                print(f"🚫 403 Forbidden from {url}")
            else:
                print(f"⚠️ Status {resp.status_code} on attempt {attempt+1} for {url}")
        except Exception as e:
            print(f"❌ Attempt {attempt+1} failed for {url}: {e}")

        await asyncio.sleep(delay * (attempt + 1))
    return None

# 🔍 Get stats (additions/deletions) for a single commit
async def fetch_commit_detail(repo, sha, client):
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    data = await safe_get(client, url)
    if data and "stats" in data:
        stats = data["stats"]
        return stats.get("additions", 0), stats.get("deletions", 0), stats.get("total", 0)
    return 0, 0, 0

# 📦 Collect up to ~300 recent commits for a repo
async def fetch_commits_with_stats(repo, client):
    all_commits = []
    for page in range(1, 11):  # 10 pages × 30 commits = ~300
        url = f"https://api.github.com/repos/{repo}/commits?per_page=30&page={page}"
        data = await safe_get(client, url)
        if not data or len(data) == 0:
            break

        for commit in data:
            if "commit" in commit:
                info = commit["commit"]
                sha = commit.get("sha")
                additions, deletions, total = await fetch_commit_detail(repo, sha, client)
                all_commits.append({
                    "repo": repo,
                    "sha": sha,
                    "author": info["author"].get("name") if info.get("author") else "",
                    "date": info["author"].get("date") if info.get("author") else "",
                    "message": info.get("message", "").replace("\n", " "),
                    "additions": additions,
                    "deletions": deletions,
                    "total_changes": total
                })

    print(f"📦 {repo}: {len(all_commits)} commits fetched")
    return all_commits

# ✅ Save completed repo name to log file
def log_completed_repo(repo_name):
    with open("completed_repos.txt", "a") as f:
        f.write(repo_name + "\n")

# 🚀 Main async entry
async def main():
    SAVE_DIR = "data/commit_data"
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Load previously completed repos
    completed = set()
    if os.path.exists("completed_repos.txt"):
        with open("completed_repos.txt", "r") as f:
            completed = set(line.strip() for line in f)

    pending_repos = [r for r in REPO_LIST if r not in completed]

    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    async with httpx.AsyncClient(timeout=30, http2=False, limits=limits) as client:
        await asyncio.gather(*[update_token_state(t, client) for t in GITHUB_TOKENS])

        semaphore = asyncio.Semaphore(5)

        async def limited_fetch_and_save(repo):
            async with semaphore:
                print(f"\n🔍 Processing {repo}")
                commits = await fetch_commits_with_stats(repo, client)
                if commits:
                    filename = repo.replace("/", "_") + "_commits.csv"
                    path = os.path.join(SAVE_DIR, filename)
                    with open(path, mode="w", newline="", encoding="utf-8") as f:
                        fieldnames = ["repo", "sha", "author", "date", "message", "additions", "deletions", "total_changes"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(commits)
                    print(f"✅ Saved CSV for {repo}")
                    log_completed_repo(repo)

        tasks = [limited_fetch_and_save(repo) for repo in pending_repos]
        await asyncio.gather(*tasks)

    print("\n✅ All available repos processed. Results saved in data/commit_data/")

if __name__ == "__main__":
    asyncio.run(main())
