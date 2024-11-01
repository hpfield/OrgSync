import logging
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

# Initialize logger
logger = logging.getLogger(__name__)

def stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=0.5):
    nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
    distances, indices = nbrs.kneighbors(name_vectors)

    grouped_names = {}
    used_names = set()

    for i, name in enumerate(unique_combined_names):
        if name in used_names:
            continue
        similar_names = [
            unique_combined_names[idx]
            for j, idx in enumerate(indices[i])
            if distances[i][j] <= threshold and idx != i and unique_combined_names[idx] not in used_names
        ]
        all_group_names = [name] + similar_names
        if len(all_group_names) > 1:
            grouped_names[name] = similar_names
            used_names.update(all_group_names)
        else:
            # No similar names found, skip adding this group
            continue

    logger.info(f"Grouped names into {len(grouped_names)} groups after removing groups of size 1.")
    return grouped_names
