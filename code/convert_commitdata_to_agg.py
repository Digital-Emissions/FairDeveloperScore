import pandas as pd


df = pd.read_csv("data/commit_data2/tensorflow_tensorflow_commits.csv")


df["date"] = pd.to_datetime(df["date"])
df["weekday"] = df["date"].dt.weekday  # 0 = Monday, 6 = Sunday
df["msg_len"] = df["message"].fillna("").apply(len)

# Developer-level aggregation
dev_df = df.groupby("author").agg({
    "sha": "count",  # total amount of commits
    "date": lambda x: x.dt.date.nunique(),  # active days
    "additions": "mean",  # average additions
    "deletions": "mean",  # average deletions
    "total_changes": ["mean", "max"],  # average total changes, max total changes
    "msg_len": "mean",  # average message length
    "weekday": lambda x: (x >= 5).sum() / len(x)  # weekend commit ratio
}).reset_index()

# fix multi-level column names
dev_df.columns = [
    "author", "commit_count", "active_days", 
    "avg_additions", "avg_deletions", 
    "avg_total_changes", "max_total_changes", 
    "avg_msg_len", "weekend_commit_ratio"
]


dev_df.to_csv("data/commit_data/tensorflow_tensorflow_developer_commit_profile.csv", index=False)
print("✅ Developer commit profile exported!")
