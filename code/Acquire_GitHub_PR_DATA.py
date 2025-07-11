from github import Github
import datetime, pandas as pd

# Option 2: With token (5000 requests/hour)
g = Github("")

repo = g.get_repo("torvalds/linux")

# Define time window: last 30 days
since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
print(f"Fetching pull requests since {since.isoformat()}...")

# GitHub's get_pulls does not support 'since', so we manually filter
all_pulls = repo.get_pulls(state='all', sort='created', direction='desc')
pull_data = []

print("Collecting detailed pull request data...")
count = 0
for pr in all_pulls:
    # Stop if PR was created before our target window
    if pr.created_at < since:
        break  # pull requests are returned in descending order

    try:
        pull_data.append({
            "number": pr.number,
            "title": pr.title,
            "user": pr.user.login if pr.user else None,
            "created_at": pr.created_at,
            "merged_at": pr.merged_at,
            "closed_at": pr.closed_at,
            "state": pr.state,
            "comments": pr.comments,  # general PR comments (not code review)
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "mergeable_state": pr.mergeable_state,
            "is_merged": pr.is_merged()
        })
        count += 1
        if count % 20 == 0:
            print(f"Processed {count} pull requests...")
    except Exception as e:
        print(f"Error processing PR #{pr.number}: {e}")
        continue

# Save results to CSV
print(f"Saving {len(pull_data)} pull requests to CSV...")
pd.DataFrame(pull_data).to_csv("linux_pull_requests.csv", index=False)
print("Data saved to linux_pull_requests.csv")
