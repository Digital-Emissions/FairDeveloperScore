from github import Github
from collections import defaultdict
import csv
import time

# ========== CONFIG ==========
GITHUB_TOKEN = "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"
REPO_NAME = "tensorflow/tensorflow"
OUTPUT_CSV = "data/pr_data/tensorflow_tensorflow_pr_contributors.csv"
MAX_PRS = 400  # set the maximum number of PRs you want to collect
SLEEP_TIME = 0.4

# ========== INIT ==========
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

# ========== COLLECTOR ==========
contributor_stats = defaultdict(lambda: {"pr_count": 0, "merged_count": 0})

print(f"🔍 Scanning {MAX_PRS} PRs from {REPO_NAME}...")

for i, pr in enumerate(pulls):
    if i >= MAX_PRS:
        break

    if not pr.is_merged():
        continue

    try:
        commits = pr.get_commits()
        for commit in commits:
            author = None
            if commit.author:  
                author = commit.author.login
            elif commit.commit and commit.commit.author:
                author = commit.commit.author.name 
            
            if author:
                contributor_stats[author]["pr_count"] += 1
                contributor_stats[author]["merged_count"] += 1

        time.sleep(SLEEP_TIME)

    except Exception as e:
        print(f"⚠️ Error on PR #{pr.number}: {e}")
        continue

# ========== SAVE ==========
print(f"💾 Writing contributor stats to {OUTPUT_CSV}...")

with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Developer", "PRs Contributed", "Merged PRs"])
    for dev, stats in sorted(contributor_stats.items(), key=lambda x: -x[1]["pr_count"]):
        writer.writerow([dev, stats["pr_count"], stats["merged_count"]])

print("✅ Done.")
