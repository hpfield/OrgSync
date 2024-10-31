import logging  # Import logging
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

# Get the logger for this stage file
logger = logging.getLogger(__name__)

def stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=0.5):
    nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
    distances, indices = nbrs.kneighbors(name_vectors)
    grouped_names = defaultdict(list)
    used_names = set()
    for i, name in enumerate(unique_combined_names):
        if name in used_names:
            continue
        similar_names = [unique_combined_names[idx] for j, idx in enumerate(indices[i]) if distances[i][j] <= threshold and idx != i]
        if similar_names:
            grouped_names[name].extend(similar_names)
            used_names.add(name)
            used_names.update(similar_names)
    logger.info(f"Grouped names into {len(grouped_names)} groups.")
    return grouped_names
