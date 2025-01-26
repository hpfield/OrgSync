import logging
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

def stage3_vectorize_names(preprocessed_data):
    """
    Converts each dictionary entry to a frozenset so we only remove truly duplicate
    dictionaries. Then vectorizes the 'combined_name' field for similarity checks later.
    """
    # Make entire entry hashable -> remove exact duplicates
    unique_entries = list({frozenset(entry.items()): entry for entry in preprocessed_data}.values())

    # Extract the combined names for vectorization
    unique_combined_names = [entry['combined_name'] for entry in unique_entries]
    total_unique_entries = len(unique_entries)

    # Vectorize those combined names
    vectorizer = TfidfVectorizer().fit(unique_combined_names)
    name_vectors = vectorizer.transform(unique_combined_names)

    logger.info(f"Vectorized {total_unique_entries} unique entries based on full uniqueness.")
    return vectorizer, name_vectors, unique_entries
