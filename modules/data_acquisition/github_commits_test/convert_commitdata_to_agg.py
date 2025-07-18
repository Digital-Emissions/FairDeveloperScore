import pandas as pd

# === Load enriched CSV ===
df = pd.read_csv("data/Commit_PR_data/torvalds_linux_commit_with_pr_stats_2.csv")

# === preprocess ===
df["date"] = pd.to_datetime(df["date"])
df["weekday"] = df["date"].dt.weekday  # 0 = Monday, 6 = Sunday
df["msg_len"] = df["message"].fillna("").apply(len)

# === Developer-level aggregation ===
dev_df = df.groupby("author_login").agg({
    "sha": "count",  # total commits
    "date": lambda x: x.dt.date.nunique(),  # active days
    "additions": "mean",
    "deletions": "mean",
    "total_changes": ["mean", "max"],
    "msg_len": "mean",
    "weekday": lambda x: (x >= 5).sum() / len(x),  # weekend commit ratio
    "total_prs": "first",  # one row per dev, so total_prs stays the same
    "merged_prs": "first",
    "pr_acceptance_rate": "first",
    "commit_count": "first"  # already counted at row level
}).reset_index()

# === Fix multi-index columns ===
dev_df.columns = [
    "author_login", "commit_count_raw", "active_days",
    "avg_additions", "avg_deletions",
    "avg_total_changes", "max_total_changes",
    "avg_msg_len", "weekend_commit_ratio",
    "total_prs", "merged_prs", "pr_acceptance_rate", "commit_count"
]

# === Save developer profile ===
dev_df.to_csv("data/developer_profile/torvalds_linux_developer_commit_pr_profile.csv", index=False)
print("✅ Developer commit + PR profile exported!")
