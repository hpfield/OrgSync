import logging
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger(__name__)

def stage4_group_similar_names(vectorizer, name_vectors, unique_entries, threshold=0.5):
    """
    Groups 'unique_entries' whose 'combined_name' fields are similar
    based on the TF-IDF vectors and a cosine distance threshold.
    
    Returns a dict of the form:
    {
       <representative_name>: {
          "matched_names": [other similar names],
          "items": [the full item dicts (representative + matched)]
       },
       ...
    }
    """

    # We'll need quick access from combined_name -> item dicts
    name_to_itemlist = defaultdict(list)
    for entry in unique_entries:
        nm = entry["combined_name"]
        name_to_itemlist[nm].append(entry)

    all_names = [entry["combined_name"] for entry in unique_entries]
    nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
    distances, indices = nbrs.kneighbors(name_vectors)

    grouped_names = {}
    used_names = set()

    for i, name in enumerate(all_names):
        if name in used_names:
            continue

        similar_names = []
        for j, idx in enumerate(indices[i]):
            if distances[i][j] <= threshold and idx != i:
                neighbor_name = all_names[idx]
                if neighbor_name not in used_names:
                    similar_names.append(neighbor_name)

        all_group_names = [name] + similar_names
        if len(all_group_names) > 1:
            # Mark them as 'used'
            for gnm in all_group_names:
                used_names.add(gnm)

            grouped_names[name] = {
                "matched_names": similar_names,
                # Gather all the item dicts from each group name
                "items": [
                    item
                    for gnm in all_group_names
                    for item in name_to_itemlist[gnm]
                ],
            }
        else:
            # No match found under threshold, skip adding a group for size=1
            # (or handle singletons if you want them)
            continue

    logger.info(f"Grouped names into {len(grouped_names)} groups (size >= 2).")
    return grouped_names
