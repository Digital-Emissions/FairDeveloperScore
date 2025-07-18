from utils.custom_torque_clustering import compute_productivity_score, torque_clustering_custom
import pandas as pd

# 1. 读取数据
df = pd.read_csv("data/developer_profile_total/merged_developer_profile_cleaned.csv")

# 2. 计算生产力分数
df = compute_productivity_score(df)

# 3. 选取用于聚类的特征
features = df[['commit_count', 'avg_total_changes', 'pr_acceptance_rate', 'weekend_commit_ratio', 'productivity_score']].values
feature_weights = [1.0, 0.8, 1.2, 0.8, 1.5]  # 自定义特征权重

# 4. 执行改造后的 Torque Clustering
labels = torque_clustering_custom(features, feature_weights=feature_weights, alpha=0.2)

# 5. 将聚类结果添加回 DataFrame
df['cluster'] = labels

# 6. 查看分出了多少个 cluster
num_clusters = len(df['cluster'].unique())
print(f"总共分出了 {num_clusters} 个 cluster")

# 7. 按 productivity_score 降序排列
df_sorted = df.sort_values(by='productivity_score', ascending=False)

# 8. 保存结果
output_path = "developer_clusters_sorted.csv"
df_sorted.to_csv(output_path, index=False)
print(f"结果已按 productivity_score 降序排列并保存到 {output_path}")
