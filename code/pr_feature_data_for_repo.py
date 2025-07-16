from github import Github
from collections import defaultdict
import time
import csv


GITHUB_TOKEN = "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"
REPO_NAME = "tensorflow/tensorflow"
OUTPUT_CSV = "data/pr_data/tensorflow_tensorflow_pr_stats.csv"
SLEEP_TIME = 0.3  # 防止 API rate limit

# ========== INIT ==========
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

# stats structure: {user: {total, merged, reverted}}
stats = defaultdict(lambda: {"total": 0, "merged": 0, "reverted": 0})

print("⏳ Collecting PR stats from torvalds/linux...")

MAX_PRS = 400  # set the maximum number of PRs you want to collect
counter = 0

# ========== MAIN LOOP ==========
for pr in pulls:
    if counter >= MAX_PRS:
        break  # exit early if we've reached the maximum number of PRs

    if pr.user is None:
        continue

    author = pr.user.login
    stats[author]["total"] += 1

    if pr.is_merged():
        stats[author]["merged"] += 1

    counter += 1
    time.sleep(SLEEP_TIME)

# ========== EXPORT TO CSV ==========
print("💾 Writing results to CSV...")

with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Developer", "Total PRs", "Merged PRs", "Reverted PRs", "Acceptance Rate"])

    for dev, s in sorted(stats.items(), key=lambda x: -x[1]["total"]):
        total = s["total"]
        merged = s["merged"]
        reverted = s["reverted"]
        acceptance_rate = round(merged / total, 4) if total > 0 else 0.0
        writer.writerow([dev, total, merged, reverted, acceptance_rate])

print(f"✅ Done. Output saved to {OUTPUT_CSV}")