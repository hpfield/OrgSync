import json
import re
import logging  # Import logging

logger = logging.getLogger(__name__)

def stage1_load_and_preprocess_data():
    # Load the UK names data
    with open('/home/ubuntu/OrgSync/data/raw/uk_data.json', 'r') as file:
        uk_data = json.load(file)

    # Preprocess the data
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
            "postcode": entry.get("postcode", "")
        }

    # Combine names and include other fields
    preprocessed_data = [combine_entry(entry) for entry in uk_data]
    logger.info(f"Loaded and preprocessed {len(preprocessed_data)} entries.")
    return preprocessed_data
