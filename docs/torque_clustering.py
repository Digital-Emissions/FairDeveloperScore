import numpy as np
import time
from typing import List, Tuple
from sklearn.cluster import KMeans, DBSCAN
from sklearn.datasets import make_blobs, make_moons, make_circles
from sklearn.metrics import adjusted_rand_score
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

def torque_clustering(X, initial_masses=None, distance_metric='euclidean'):
    """
    Perform Torque Clustering (TC) on dataset X to produce an autonomous clustering.
    
    If `initial_masses` is provided, use these as initial weights for each sample (enabling Weighted TC).
    Otherwise, each sample has an initial mass of 1.
    
    The algorithm follows the TC pseudocode:
      1. Start with each sample as its own cluster (mass = 1).
      2. For each cluster, find its 1-nearest neighboring cluster (by Euclidean distance by default).
      3. Connect (merge) cluster i into cluster j if mass(i) ≤ mass(j).
         - Compute merge properties: 
            M_i = mass(i) * mass(j),
            D_i = squared distance between centroids,
            τ_i = M_i * D_i.
      4. Merge clusters that are connected (forming connected components) and update centroids and masses.
      5. Repeat until only one cluster remains (the hierarchy is fully constructed).
      6. Sort all merge connections by descending τ (torque) values.
      7. Compute the Torque Gap (TGap) between adjacent τ values.
      8. Identify the largest TGap; remove all merges before this gap to obtain the final partition.
    
    Parameters:
        X : np.ndarray of shape (n_samples, n_features)
            Input data points.
        initial_masses : np.ndarray of shape (n_samples,), optional
            Initial weights for each sample (for weighted TC).
        distance_metric : str, optional
            Distance metric to use (default 'euclidean').
            
    Returns:
        labels : np.ndarray of shape (n_samples,)
            Cluster label assignment for each sample.
        cluster_centers : np.ndarray of shape (K, n_features)
            Centroids for the clusters.
        cluster_masses : np.ndarray of shape (K,)
            Mass (size) of each cluster.
    """
    X = np.asarray(X)
    n_samples, n_features = X.shape
    
    # Initialize each sample as its own cluster with mass 1 (or given mass).
    cluster_ids = list(range(n_samples))
    cluster_center = {i: X[i].copy() for i in cluster_ids}
    cluster_mass = {i: (1 if initial_masses is None else initial_masses[i]) for i in cluster_ids}
    
    # Record merge connections: (tau, cluster_i, cluster_j).
    connections = []
    
    # Hierarchical merging loop.
    while True:
        n_clusters = len(cluster_ids)
        if n_clusters <= 1:
            break
        
        # Compute pairwise distances between cluster centers.
        centers_array = np.vstack([cluster_center[c] for c in cluster_ids])
        diff = centers_array[:, None] - centers_array[None, :]
        dist_matrix = np.linalg.norm(diff, axis=2)
        np.fill_diagonal(dist_matrix, np.inf)
        
        # For each cluster, find the nearest neighbor.
        nearest_idx = np.argmin(dist_matrix, axis=1)
        
        # Create directed edges based on mass comparison.
        directed_edges = []
        for idx, cid in enumerate(cluster_ids):
            nbr_index = nearest_idx[idx]
            if nbr_index == idx:
                continue
            nbr_cid = cluster_ids[nbr_index]
            if cluster_mass[cid] <= cluster_mass[nbr_cid]:
                directed_edges.append((cid, nbr_cid))
        if not directed_edges:
            break
        
        # Use Union-Find to merge connected clusters.
        parent = {cid: cid for cid in cluster_ids}
        def find_set(a):
            if parent[a] != a:
                parent[a] = find_set(parent[a])
            return parent[a]
        def union_set(a, b):
            ra = find_set(a); rb = find_set(b)
            if ra != rb:
                if cluster_mass[ra] < cluster_mass[rb]:
                    parent[ra] = rb
                else:
                    parent[rb] = ra
        
        # Calculate τ values for each directed edge and prepare for merging.
        for cid, nid in directed_edges:
            M_val = cluster_mass[cid] * cluster_mass[nid]
            dist_sq = np.sum((cluster_center[cid] - cluster_center[nid])**2)
            tau_val = M_val * dist_sq
            connections.append((tau_val, cid, nid))
            union_set(cid, nid)
        

        # Update cluster centers and masses after merging.
        new_cluster_ids = {}
        new_center = {}
        new_mass = {}
        for cid in cluster_ids:
            root = find_set(cid)
            if root not in new_cluster_ids:
                new_cluster_ids[root] = root
                new_center[root] = np.zeros(n_features)
                new_mass[root] = 0
            new_center[root] += cluster_center[cid] * cluster_mass[cid]
            new_mass[root] += cluster_mass[cid]
        for root in new_center:
            new_center[root] /= new_mass[root]
        
        # Update cluster_ids, cluster_center, and cluster_mass.
        cluster_ids = list(new_cluster_ids.keys())
        cluster_center = new_center
        cluster_mass = new_mass
    
    # If no merges occurred, assign unique labels.
    if not connections:
        labels = np.arange(n_samples)
        return labels, X.copy(), np.ones(n_samples, dtype=int)
    
    # Determine optimal clustering via Torque Gap analysis.
    connections.sort(key=lambda x: x[0], reverse=True)
    tau_values = [conn[0] for conn in connections]
    tgap_values = []
    for j in range(len(tau_values) - 1):
        if tau_values[j+1] == 0:
            tgap = float('inf')
        else:
            ω_j = 1.0
            tgap = ω_j * (tau_values[j] / tau_values[j+1])
        tgap_values.append(tgap)
    if tgap_values:
        max_gap_index = int(np.argmax(tgap_values))
        optimal_clusters = max_gap_index + 2
    else:
        optimal_clusters = 1
    
    # Reconstruct final clustering using union-find.
    uf_parent = np.arange(n_samples)
    def uf_find(i):
        if uf_parent[i] != i:
            uf_parent[i] = uf_find(uf_parent[i])
        return uf_parent[i]
    def uf_union(i, j):
        ri = uf_find(i); rj = uf_find(j)
        if ri != rj:
            uf_parent[rj] = ri
    
    merges_to_remove = optimal_clusters - 1
    for k in range(merges_to_remove, len(connections)):
        _, cid_i, cid_j = connections[k]
        uf_union(cid_i, cid_j)
    labels = np.zeros(n_samples, dtype=int)
    cluster_map = {}
    next_label = 0
    for i in range(n_samples):
        root = uf_find(i)
        if root not in cluster_map:
            cluster_map[root] = next_label
            next_label += 1
        labels[i] = cluster_map[root]
    
    # Compute final centroids and cluster masses.
    K = next_label
    cluster_centers = np.zeros((K, n_features))
    cluster_masses = np.zeros(K, dtype=int)
    for i in range(n_samples):
        cid = labels[i]
        cluster_centers[cid] += X[i]
        cluster_masses[cid] += (1 if initial_masses is None else initial_masses[i])
    for cid in range(K):
        cluster_centers[cid] /= cluster_masses[cid]
    
    return labels, cluster_centers, cluster_masses

def distributed_torque_clustering(data_sites: List[np.ndarray], distance_metric='euclidean') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform Distributed Torque Clustering (DTC) on data partitioned across multiple sites.
    
    Parameters:
        data_sites : list of np.ndarray
            List of datasets from different sites (each array of shape (n_k, n_features)).
        distance_metric : str, optional
            Distance metric for TC/WTC (default 'euclidean').
    
    Returns:
        global_labels : np.ndarray of shape (N_total,)
            Cluster labels for each original data sample.
        global_centers : np.ndarray of shape (K_total, n_features)
            Centroids of the final global clusters.
        global_masses : np.ndarray of shape (K_total,)
            Masses (sizes) of the final global clusters.
    """
    representatives = []
    rep_weights = []
    sample_to_rep_index = []

    def process_site(X_k):
        labels_k, centers_k, masses_k = torque_clustering(X_k, distance_metric=distance_metric)
        return labels_k, centers_k, masses_k

    # Process each site in parallel
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_site, data_sites))

    offset = 0
    for labels_k, centers_k, masses_k in results:
        r_k = centers_k.shape[0]
        representatives.append(centers_k)
        rep_weights.append(masses_k)
        sample_to_rep_index.append(offset + labels_k)
        offset += r_k

    if representatives:
        representatives = np.vstack(representatives)
        rep_weights = np.concatenate(rep_weights).astype(int)
    else:
        return np.array([], dtype=int), np.array([]), np.array([])

    # Global clustering with Weighted TC.
    rep_labels, rep_cluster_centers, rep_cluster_masses = torque_clustering(representatives, initial_masses=rep_weights, distance_metric=distance_metric)

    # Propagate labels to original samples.
    total_samples = sum(len(X_k) for X_k in data_sites)
    global_labels = np.empty(total_samples, dtype=int)
    current_index = 0
    for k, X_k in enumerate(data_sites):
        n_k = len(X_k)
        rep_indices = sample_to_rep_index[k]
        global_labels[current_index: current_index + n_k] = rep_labels[rep_indices]
        current_index += n_k

    # Compute final global centroids and masses.
    K_total = len(np.unique(global_labels))
    n_features = data_sites[0].shape[1] if total_samples > 0 else 0
    global_centers = np.zeros((K_total, n_features))
    global_masses = np.zeros(K_total, dtype=int)
    current_index = 0
    for k, X_k in enumerate(data_sites):
        for i in range(len(X_k)):
            cid = global_labels[current_index + i]
            global_centers[cid] += X_k[i]
            global_masses[cid] += 1
        current_index += len(X_k)
    for cid in range(K_total):
        if global_masses[cid] > 0:
            global_centers[cid] /= global_masses[cid]

    return global_labels, global_centers, global_masses

# --- Demonstration and Comparison ---
if __name__ == "__main__":

    # Compile all ARI results into a table and compute percentage improvement for DTC/TC over KMeans/DBSCAN
    scenarios = [
        "Varying Densities",
        "Nested Clusters",
        "Unequal Cluster Sizes",
        "Non-convex (Moons + Blob)",
        "Clusters with Outliers",
        "Anisotropic Clusters",
        "Varying Feature Scales"
    ]
    results = []
    datasets = []
    y_trues = []

    # Prepare all datasets and ground truths
    # Scenario 1: Varying Densities
    X1, _ = make_blobs(n_samples=50, centers=[[0, 0]], cluster_std=0.3, random_state=1)
    X2, _ = make_blobs(n_samples=50, centers=[[5, 5]], cluster_std=0.3, random_state=2)
    X3, _ = make_blobs(n_samples=200, centers=[[2.5, 2.5]], cluster_std=2.0, random_state=3)
    datasets.append(np.vstack([X1, X2, X3]))
    y_trues.append(np.array([0]*50 + [1]*50 + [2]*200))
    # Scenario 2: Nested Clusters
    X_inner, _ = make_blobs(n_samples=60, centers=[[0, 0]], cluster_std=0.2, random_state=4)
    X_outer, _ = make_blobs(n_samples=240, centers=[[0, 0]], cluster_std=1.5, random_state=5)
    datasets.append(np.vstack([X_inner, X_outer]))
    y_trues.append(np.array([0]*60 + [1]*240))
    # Scenario 3: Unequal Cluster Sizes
    X1, _ = make_blobs(n_samples=10, centers=[[0, 0]], cluster_std=0.3, random_state=6)
    X2, _ = make_blobs(n_samples=10, centers=[[5, 5]], cluster_std=0.3, random_state=7)
    X3, _ = make_blobs(n_samples=280, centers=[[2.5, 2.5]], cluster_std=1.0, random_state=8)
    datasets.append(np.vstack([X1, X2, X3]))
    y_trues.append(np.array([0]*10 + [1]*10 + [2]*280))
    # Scenario 4: Non-convex (Moons + Blob)
    X_moons, y_moons = make_moons(n_samples=200, noise=0.05, random_state=10)
    X_blob, _ = make_blobs(n_samples=50, centers=[[8, 8]], cluster_std=0.3, random_state=20)
    X_moons[:, 0] += 2
    datasets.append(np.vstack([X_moons, X_blob]))
    y_trues.append(np.concatenate([y_moons, np.full(50, 2)]))
    # Scenario 5: Clusters with Outliers
    X_clusters, y_clusters = make_blobs(n_samples=270, centers=[[0, 0], [5, 5], [0, 10]], cluster_std=0.5, random_state=30)
    X_outliers = np.random.uniform(low=-10, high=15, size=(30, 2))
    datasets.append(np.vstack([X_clusters, X_outliers]))
    y_trues.append(np.concatenate([y_clusters, np.full(30, 3)]))
    # Scenario 6: Anisotropic Clusters
    X, y_true = make_blobs(n_samples=300, centers=3, random_state=40)
    transformation = [[0.6, -0.6], [-0.4, 0.8]]
    datasets.append(np.dot(X, transformation))
    y_trues.append(y_true)
    # Scenario 7: Varying Feature Scales
    X, y_true = make_blobs(n_samples=300, centers=3, random_state=50)
    X[:, 0] *= 10
    datasets.append(X)
    y_trues.append(y_true)

    for i, (X, y_true) in enumerate(zip(datasets, y_trues)):
        sites = np.array_split(X, 3)
        labels_dtc, _, _ = distributed_torque_clustering(sites)
        labels_tc, _, _ = torque_clustering(X)
        kmeans = KMeans(n_clusters=len(np.unique(y_true)), n_init='auto', random_state=0).fit(X)
        labels_km = kmeans.labels_
        dbscan = DBSCAN(eps=1.0, min_samples=5).fit(X)
        labels_db = dbscan.labels_
        # ARI
        ari_dtc = adjusted_rand_score(y_true, labels_dtc)
        ari_tc = adjusted_rand_score(y_true, labels_tc)
        ari_km = adjusted_rand_score(y_true, labels_km)
        ari_db = adjusted_rand_score(y_true, labels_db)
        results.append({
            'Scenario': scenarios[i],
            'DTC': ari_dtc,
            'TC': ari_tc,
            'KMeans': ari_km,
            'DBSCAN': ari_db
        })

    df = pd.DataFrame(results)
    # Calculate percentage increase
    df['DTC_vs_KMeans_%'] = 100 * (df['DTC'] - df['KMeans']) / (df['KMeans'] + 1e-8).round(2)
    df['DTC_vs_DBSCAN_%'] = 100 * (df['DTC'] - df['DBSCAN']) / (np.abs(df['DBSCAN']) + 1e-8).round(2)
    df['TC_vs_KMeans_%'] = 100 * (df['TC'] - df['KMeans']) / (df['KMeans'] + 1e-8).round(2)
    df['TC_vs_DBSCAN_%'] = 100 * (df['TC'] - df['DBSCAN']) / (np.abs(df['DBSCAN']) + 1e-8).round(2)
    print("\nClustering ARI Results and Percentage Increase:")
    print(df.to_string(index=False))