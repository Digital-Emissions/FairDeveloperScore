import numpy as np

def auto_feature_weights(X):
    """
    Automatically compute feature weights as inverse of variance.
    This prevents high-variance features from dominating the distance.
    """
    variances = np.var(X, axis=0)
    return 1 / (variances + 1e-8)

def custom_distance_matrix(X, feature_weights):
    """
    Compute pairwise weighted Euclidean distance.
    D_ij = sqrt( sum_k (w_k * (x_ik - x_jk))^2 )
    """
    Xw = X * feature_weights
    diff = Xw[:, None, :] - Xw[None, :, :]
    dist_matrix = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dist_matrix, np.inf)
    return dist_matrix

def torque_clustering(X, feature_weights=None):
    """
    Torque Clustering (TC) with optional feature weighting.

    Parameters
    ----------
    X : np.ndarray, shape (n_samples, n_features)
        Input dataset.
    feature_weights : list or np.ndarray, optional
        Custom weights for each feature. If None, weights are computed automatically.

    Returns
    -------
    labels : np.ndarray, shape (n_samples,)
        Cluster label assignment for each sample.
    """
    X = np.asarray(X)
    n_samples, n_features = X.shape

    # Compute feature weights if not provided
    if feature_weights is None:
        feature_weights = auto_feature_weights(X)
    else:
        feature_weights = np.array(feature_weights)
        if feature_weights.shape[0] != n_features:
            raise ValueError("Length of feature_weights must match the number of features.")

    # Initialize clusters
    cluster_ids = list(range(n_samples))
    cluster_center = {i: X[i].copy() for i in cluster_ids}
    cluster_mass = {i: 1 for i in cluster_ids}
    connections = []

    # Hierarchical merging
    while True:
        n_clusters = len(cluster_ids)
        if n_clusters <= 1:
            break

        centers_array = np.vstack([cluster_center[c] for c in cluster_ids])
        dist_matrix = custom_distance_matrix(centers_array, feature_weights)

        nearest_idx = np.argmin(dist_matrix, axis=1)
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

        # Union-Find
        parent = {cid: cid for cid in cluster_ids}
        def find_set(a):
            if parent[a] != a:
                parent[a] = find_set(parent[a])
            return parent[a]
        def union_set(a, b):
            ra = find_set(a)
            rb = find_set(b)
            if ra != rb:
                if cluster_mass[ra] < cluster_mass[rb]:
                    parent[ra] = rb
                else:
                    parent[rb] = ra

        for cid, nid in directed_edges:
            M_val = cluster_mass[cid] * cluster_mass[nid]
            dist_sq = np.sum(((cluster_center[cid] - cluster_center[nid]) * feature_weights)**2)
            tau_val = M_val * dist_sq
            connections.append((tau_val, cid, nid))
            union_set(cid, nid)

        new_center = {}
        new_mass = {}
        for cid in cluster_ids:
            root = find_set(cid)
            if root not in new_center:
                new_center[root] = np.zeros(n_features)
                new_mass[root] = 0
            new_center[root] += cluster_center[cid] * cluster_mass[cid]
            new_mass[root] += cluster_mass[cid]
        for root in new_center:
            new_center[root] /= new_mass[root]
        cluster_ids = list(new_center.keys())
        cluster_center = new_center
        cluster_mass = new_mass

    # Assign labels
    if not connections:
        return np.arange(n_samples)

    connections.sort(key=lambda x: x[0], reverse=True)
    tau_values = [conn[0] for conn in connections]
    tgap_values = [tau_values[j] / tau_values[j + 1] if tau_values[j + 1] != 0 else float('inf')
                   for j in range(len(tau_values) - 1)]
    max_gap_index = int(np.argmax(tgap_values)) if tgap_values else 0
    optimal_clusters = max_gap_index + 2

    uf_parent = np.arange(n_samples)
    def uf_find(i):
        if uf_parent[i] != i:
            uf_parent[i] = uf_find(uf_parent[i])
        return uf_parent[i]
    def uf_union(i, j):
        ri = uf_find(i)
        rj = uf_find(j)
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

    return labels
