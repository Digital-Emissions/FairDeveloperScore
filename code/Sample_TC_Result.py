from doc.torque_clustering import torque_clustering

import pandas as pd

# 假设你的 CSV 文件名为 "your_data.csv"
df = pd.read_csv('Kevin_project_commits.csv')
X = df.select_dtypes(include='number').values

# 使用 torque_clustering 函数
torque_clustering(X, initial_masses=None, distance_metric='euclidean')

labels, centers, masses = torque_clustering(X)


print("Labels:", labels)
print("Cluster Centers:", centers)
print("Cluster Masses:", masses)






