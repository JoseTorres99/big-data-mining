import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("USArrests.csv")

# Save state names separately
states = df.iloc[:, 0]
data = df.iloc[:, 1:].values


# Standardize data (mean = 0, std = 1)
def standardize(X):
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    return (X - mean) / std


X = standardize(data)


# Euclidean distance
def euclidean_distance(a, b):
    return np.sqrt(np.sum((a - b) ** 2))


# K-means clustering
def kmeans(X, K=4, max_iters=100):
    n_samples, n_features = X.shape

    # Randomly choose initial centroids
    indices = np.random.choice(n_samples, K, replace=False)
    centroids = X[indices]

    for _ in range(max_iters):
        clusters = [[] for _ in range(K)]

        # Assign points to closest centroid
        for i, point in enumerate(X):
            distances = [euclidean_distance(point, c) for c in centroids]
            cluster_index = np.argmin(distances)
            clusters[cluster_index].append(i)

        # Compute new centroids
        new_centroids = []
        for cluster in clusters:
            if len(cluster) > 0:
                new_centroids.append(np.mean(X[cluster], axis=0))
            else:
                new_centroids.append(centroids[len(new_centroids)])

        new_centroids = np.array(new_centroids)

        # Stop if centroids do not change
        if np.allclose(centroids, new_centroids):
            break

        centroids = new_centroids

    return clusters, centroids


# Run K-means
clusters, centroids = kmeans(X, K=4)

print("\n===== K-MEANS CLUSTERING RESULTS =====")
for i, cluster in enumerate(clusters):
    print(f"\nCluster {i+1}:")
    for index in cluster:
        print(states.iloc[index])


# Distance between two clusters
def cluster_distance(c1, c2, X, method="min"):
    distances = []

    for i in c1:
        for j in c2:
            distances.append(euclidean_distance(X[i], X[j]))

    if method == "min":
        return min(distances)
    elif method == "max":
        return max(distances)
    elif method == "average":
        return np.mean(distances)


# Hierarchical clustering
def hierarchical_clustering(X, method="min"):
    clusters = [[i] for i in range(len(X))]
    merge_steps = []

    while len(clusters) > 1:
        min_dist = float("inf")
        to_merge = (0, 1)

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                dist = cluster_distance(clusters[i], clusters[j], X, method)

                if dist < min_dist:
                    min_dist = dist
                    to_merge = (i, j)

        i, j = to_merge

        new_cluster = clusters[i] + clusters[j]
        merge_steps.append((clusters[i], clusters[j], min_dist))

        # Remove higher index first
        clusters.pop(j)
        clusters.pop(i)
        clusters.append(new_cluster)

    return merge_steps


# Run hierarchical clustering for all 3 linkage methods
print("\n===== HIERARCHICAL CLUSTERING: MIN LINKAGE =====")
min_steps = hierarchical_clustering(X, method="min")
for step in min_steps[:10]:
    print(step)

print("\n===== HIERARCHICAL CLUSTERING: MAX LINKAGE =====")
max_steps = hierarchical_clustering(X, method="max")
for step in max_steps[:10]:
    print(step)

print("\n===== HIERARCHICAL CLUSTERING: AVERAGE LINKAGE =====")
avg_steps = hierarchical_clustering(X, method="average")
for step in avg_steps[:10]:
    print(step)