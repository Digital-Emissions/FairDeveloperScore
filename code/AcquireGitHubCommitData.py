from github import Github
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import time
import csv
import os

# ========== CONFIG ==========
GITHUB_TOKENS = [
    "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",
    "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",
    "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"
]
REPO_NAME = "microsoft/vscode"
NUM_COMMITS = 300
CSV_NAME = f"{REPO_NAME.replace('/', '_')}_commit_only.csv"
FINAL_CSV = f"{REPO_NAME.replace('/', '_')}_commit_with_pr_stats_2.csv"

# ========== TOKEN ROTATOR ==========
class TokenRotator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.g = Github(self.tokens[self.index])

    def get_client(self):
        rate_limit = self.g.get_rate_limit().core
        if rate_limit.remaining == 0:
            print(f"⚠️ Token {self.index + 1} exhausted. Switching to next token...")
            self.index += 1
            if self.index >= len(self.tokens):
                print("❌ All tokens exhausted. Waiting 60 seconds...")
                time.sleep(60)
                self.index = 0
            self.g = Github(self.tokens[self.index])
        return self.g

# ========== SETUP ==========
token_rotator = TokenRotator(GITHUB_TOKENS)
g = token_rotator.get_client()
repo = g.get_repo(REPO_NAME)

# ========== INIT CSV IF NOT EXIST ==========
if not os.path.exists(CSV_NAME):
    with open(CSV_NAME, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "sha", "author_login", "date", "message", "additions", "deletions", "total_changes"
        ])

# ========== COMMIT STAGE ==========
print("🔍 Fetching commits...")
commit_counts = defaultdict(int)
authors_seen = set()
commits = repo.get_commits()

with open(CSV_NAME, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for i, commit in enumerate(tqdm(commits, total=NUM_COMMITS)):
        g = token_rotator.get_client()
        if i >= NUM_COMMITS:
            break
        if commit.author is None or commit.author.login is None:
            continue

        author_login = commit.author.login
        sha = commit.sha
        date = commit.commit.author.date
        message = commit.commit.message
        stats = commit.stats

        additions = stats.additions
        deletions = stats.deletions
        total_changes = stats.total

        commit_counts[author_login] += 1
        authors_seen.add(author_login)

        writer.writerow([
            sha, author_login, date, message, additions, deletions, total_changes
        ])

# ========== PR STAGE ==========
print("📦 Fetching PR stats per author...")
pr_stats_rows = []

for login in tqdm(authors_seen):
    g = token_rotator.get_client()
    total_pr = 0
    merged_pr = 0

    try:
        query = f'repo:{REPO_NAME} is:pr author:{login}'
        pr_results = g.search_issues(query=query, sort='created', order='desc')
        for pr_issue in pr_results:
            if pr_issue.pull_request:
                pr = repo.get_pull(pr_issue.number)
                total_pr += 1
                if pr.is_merged():
                    merged_pr += 1
    except Exception as e:
        print(f"❌ Failed to fetch PRs for {login}: {e}")
        total_pr = 0
        merged_pr = 0

    pr_stats_rows.append({
        "author_login": login,
        "commit_count": commit_counts[login],
        "total_prs": total_pr,
        "merged_prs": merged_pr,
        "pr_acceptance_rate": round(merged_pr / total_pr, 2) if total_pr > 0 else None
    })

# ========== MERGE AND SAVE ==========
print("🧩 Merging commit + PR data...")
commit_df = pd.read_csv(CSV_NAME)
pr_df = pd.DataFrame(pr_stats_rows)

final_df = commit_df.merge(pr_df, on="author_login", how="left")
final_df.to_csv(FINAL_CSV, index=False)

print(f"✅ Final dataset saved as {FINAL_CSV}")