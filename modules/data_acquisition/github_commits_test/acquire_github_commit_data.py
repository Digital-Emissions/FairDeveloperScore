from github import Github
import datetime, pandas as pd

# Option 1: No token (60 requests/hour)
# g = Github()

# Option 2: With token (5000 requests/hour) - add your token here
g = Github("YOUR_GITHUB_TOKEN_HERE")

repo = g.get_repo("torvalds/linux")

since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
main_commits = repo.get_commits(sha="master", since=since)

dates = [c.commit.author.date.date() for c in main_commits]
df = pd.Series(dates).value_counts().sort_index()
deployment_frequency = df.mean() 
print("deployment_frequency_in_30_days:", deployment_frequency)
print("total_commits_in_30_days:", len(dates))
print("unique_days_with_commits:", len(df))

# full commit data
detail = []
print("Collecting detailed commit data...")
for i, c in enumerate(main_commits):
    if i % 50 == 0:
        print(f"Processed {i} commits...")
    try:
        s = c.stats
        detail.append({
            "sha": c.sha,
            "author": c.author.login if c.author else None,
            "time": c.commit.author.date,
            "add": s.additions, "del": s.deletions, "total": s.total,
            "msg": c.commit.message.splitlines()[0]
        })
    except Exception as e:
        print(f"Error processing commit {c.sha}: {e}")
        continue

print(f"Saving {len(detail)} commits to CSV...")
pd.DataFrame(detail).to_csv("linux_commits.csv", index=False)
print("Data saved to linux_commits.csv")
