import json
import re
import logging

logger = logging.getLogger(__name__)

def stage1_load_and_preprocess_data(data=None):
    """
    Load and preprocess the merged data (or fallback to reading from disk).
    Convert 'name' + 'short_name' into a single 'combined_name' field.
    Preserve 'is_new' so that we can identify new entries later.
    """

    if data is None:
        # fallback to reading from disk -- if needed
        with open('/home/ubuntu/OrgSync/data/raw/uk_data.json', 'r') as file:
            data = json.load(file)

    def preprocess_name(name):
        name = name.lower()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[^\w\s]', '', name)
        return name.strip()

    def combine_entry(entry):
        combined_name = preprocess_name(
            ' '.join(filter(None, [entry.get('name', ''), entry.get('short_name', '')]))
        )
        return {
            "combined_name": combined_name,
            "dataset": entry.get("dataset", ""),
            "unique_id": entry.get("unique_id", ""),
            "postcode": entry.get("postcode", ""),
            # Carry over the is_new flag if present, else False
            "is_new": entry.get("is_new", False),
        }

    preprocessed_data = [combine_entry(entry) for entry in data]
    logger.info(f"Loaded and preprocessed {len(preprocessed_data)} entries.")
    return preprocessed_data
