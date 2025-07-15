from doc.torque_clustering import torque_clustering

import pandas as pd

# Assume your CSV file is named "your_data.csv"
df = pd.read_csv('kevin_project_commits.csv')
X = df.select_dtypes(include='number').values

# Use torque_clustering function
torque_clustering(X, initial_masses=None, distance_metric='euclidean')

labels, centers, masses = torque_clustering(X)


print("Labels:", labels)
print("Cluster Centers:", centers)
print("Cluster Masses:", masses)






