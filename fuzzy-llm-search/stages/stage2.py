import logging  # Import logging
from sklearn.feature_extraction.text import TfidfVectorizer

# Get the logger for this stage file
logger = logging.getLogger(__name__)

def stage2_vectorize_names(preprocessed_data):
    unique_combined_names = list(set(preprocessed_data))
    total_unique_names = len(unique_combined_names)
    vectorizer = TfidfVectorizer().fit(unique_combined_names)
    name_vectors = vectorizer.transform(unique_combined_names)
    logger.info(f"Vectorized {total_unique_names} unique combined names.")
    return vectorizer, name_vectors, unique_combined_names
