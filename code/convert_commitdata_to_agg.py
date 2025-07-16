import pandas as pd

# 读取你的 commit CSV 文件
df = pd.read_csv("data/commit_data2/tensorflow_tensorflow_commits.csv")

# 将 date 字段转为 datetime 类型
df["date"] = pd.to_datetime(df["date"])
df["weekday"] = df["date"].dt.weekday  # 0 = Monday, 6 = Sunday
df["msg_len"] = df["message"].fillna("").apply(len)

# Developer-level 聚合
dev_df = df.groupby("author").agg({
    "sha": "count",  # commit 总数
    "date": lambda x: x.dt.date.nunique(),  # 活跃天数
    "additions": "mean",  # 平均新增行数
    "deletions": "mean",  # 平均删除行数
    "total_changes": ["mean", "max"],  # 平均改动行数，最大改动行数
    "msg_len": "mean",  # 平均 message 长度
    "weekday": lambda x: (x >= 5).sum() / len(x)  # 周末提交比例
}).reset_index()

# 修复多层列名
dev_df.columns = [
    "author", "commit_count", "active_days", 
    "avg_additions", "avg_deletions", 
    "avg_total_changes", "max_total_changes", 
    "avg_msg_len", "weekend_commit_ratio"
]

# 保存结果
dev_df.to_csv("data/commit_data/tensorflow_tensorflow_developer_commit_profile.csv", index=False)
print("✅ Developer commit profile exported!")
