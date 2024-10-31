import json
import re
import logging  # Import logging

# Get the logger for this stage file
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

    def combine_names(entry):
        combined_name = ' '.join(filter(None, [entry.get('name', ''), entry.get('short_name', '')]))
        return preprocess_name(combined_name)

    preprocessed_data = [combine_names(entry) for entry in uk_data]
    logger.info(f"Loaded and preprocessed {len(preprocessed_data)} names.")
    return preprocessed_data
