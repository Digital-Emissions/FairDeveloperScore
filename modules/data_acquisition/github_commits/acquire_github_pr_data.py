"""
GitHub PR Review Pass Rate Analyzer (Async Version)

This script analyzes the "pass rate" of pull requests across a list of top GitHub repositories.
The pass rate is defined as the percentage of merged PRs that did not receive a "CHANGES_REQUESTED" state in code reviews.
It uses multiple GitHub tokens to manage rate limits and sends asynchronous API requests to maximize efficiency.

Key Features:
- Asynchronous HTTP requests using httpx and asyncio
- GitHub token rotation and rate limit awareness
- Supports analyzing hundreds of repositories in parallel
- Outputs results to a CSV file including pass rate per repository

Required:
- A `top_500_repos.txt` file with one repository (e.g., "owner/repo") per line
- At least one valid GitHub personal access token with repo read permissions
"""

import asyncio
import httpx
import csv
import time
from datetime import datetime

# Remeber to replace Your GitHub Personal Access Tokens (PATs) here
GITHUB_TOKENS = [
    
]

# Load repository list (top_500_repos.txt)
with open("top_500_repos.txt", "r") as f:
    REPO_LIST = [line.strip() for line in f if line.strip()]

MAX_PR_PER_REPO = 30  # Limit the number of PRs analyzed per repo

# ====== Token rate limit state tracking ======
token_states = {token: {"remaining": 5000, "reset": 0} for token in GITHUB_TOKENS}

def get_valid_token():
    """Returns a valid token that still has available quota or has reset."""
    now = int(time.time())
    for token in GITHUB_TOKENS:
        state = token_states[token]
        if state["remaining"] > 1 or now >= state["reset"]:
            return token
    return None

async def update_token_state(token, client):
    """Fetches and updates the current rate limit info for a token."""
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

# ====== Safe GET wrapper with retries and token switching ======
async def safe_get(client, url, retries=3, delay=1.5):
    """Sends a GET request with retry logic and token management."""
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
                print(f"🚫 403 Forbidden from {url} — likely token limit hit.")
            else:
                print(f"⚠️ Status {resp.status_code} on attempt {attempt+1} from {url}")
        except Exception as e:
            print(f"❌ Attempt {attempt+1} failed for {url}: {e}")

        await asyncio.sleep(delay * (attempt + 1))
    return None

# ====== Pull request and review fetching ======
async def fetch_prs(repo, client):
    """Fetch merged PR numbers for a repo."""
    url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page={MAX_PR_PER_REPO}&sort=updated&direction=desc"
    data = await safe_get(client, url)
    if not data:
        return []
    return [pr["number"] for pr in data if pr.get("merged_at")]

async def fetch_reviews(repo, pr_number, client):
    """Fetch review states for a specific PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    data = await safe_get(client, url)
    if not data:
        return []
    return [r["state"] for r in data]

# ====== Analyze each repo for PR review pass rate ======
async def analyze_repo(repo, client):
    print(f"\n🔍 Analyzing {repo}")
    pr_numbers = await fetch_prs(repo, client)
    total = 0
    passed = 0

    for pr_number in pr_numbers:
        states = await fetch_reviews(repo, pr_number, client)
        total += 1
        if "CHANGES_REQUESTED" not in states:
            passed += 1

    rate = round((passed / total) * 100, 2) if total else 0.0
    print(f"✅ {repo}: {passed}/{total} passed, rate={rate}%")
    return {
        "repo": repo,
        "total_merged_prs": total,
        "passed_first_try": passed,
        "pass_rate": rate
    }

# ====== Main async entry point ======
async def main():
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    async with httpx.AsyncClient(timeout=30, http2=False, limits=limits) as client:
        # Initialize token states
        await asyncio.gather(*[update_token_state(t, client) for t in GITHUB_TOKENS])

        semaphore = asyncio.Semaphore(5)  # Limit concurrent tasks

        async def limited_analyze(repo):
            async with semaphore:
                return await analyze_repo(repo, client)

        tasks = [limited_analyze(repo) for repo in REPO_LIST]
        results = await asyncio.gather(*tasks)

    # Save results to CSV
    with open("pr_pass_rate_top500.csv", mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\n✅ Done. Results saved to pr_pass_rate_top500.csv")

if __name__ == "__main__":
    asyncio.run(main())
