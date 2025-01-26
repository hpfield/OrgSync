import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def stage2_identify_identical_names(preprocessed_data):
    """
    Identify groups of entries that share the exact same 'combined_name'.
    Return a dict: { <combined_name>: [list_of_entries_with_that_name], ... }
    excluding any groups of size 1.
    """
    name_groups = defaultdict(list)
    for entry in preprocessed_data:
        name_groups[entry["combined_name"]].append(entry)

    # Filter out single-entry groups
    multi_name_groups = {name: entries for name, entries in name_groups.items() if len(entries) > 1}

    logger.info(f"Found {len(multi_name_groups)} identical-name groups with more than 1 entry.")
    return multi_name_groups
