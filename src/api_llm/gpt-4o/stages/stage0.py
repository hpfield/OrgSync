import json
import os
import logging

logger = logging.getLogger(__name__)

def stage0_check_new_data(new_data_path, old_data_path, merged_data_path, new_entries_path):
    """
    - Loads old_data if it exists,
    - Loads new_data,
    - Finds the 'new entries' that exist in new_data but not in old_data,
    - Writes out:
        1) A merged dataset (old + new) to `merged_data_path`
        2) The list of truly new entries to `new_entries_path`.

    Returns the merged_data (list of dicts) so it can be passed to subsequent stages.
    """

    # Load new data
    with open(new_data_path, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    # Attempt to load old data
    if os.path.exists(old_data_path):
        with open(old_data_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        logger.info(f"Loaded old database with {len(old_data)} entries from {old_data_path}")
    else:
        old_data = []
        logger.info(f"No old database found at {old_data_path}; starting fresh.")

    # Convert each record to a frozenset of items so we can deduplicate
    old_data_set = {frozenset(d.items()) for d in old_data}
    new_data_set = {frozenset(d.items()) for d in new_data}

    # Identify truly new entries
    truly_new_entries_set = new_data_set - old_data_set
    truly_new_entries = [dict(fs) for fs in truly_new_entries_set]

    # Merge old + new
    merged_data_set = old_data_set | new_data_set
    merged_data = [dict(fs) for fs in merged_data_set]

    logger.info(f"Merged dataset has {len(merged_data)} total entries.")
    logger.info(f"Found {len(truly_new_entries)} new entries not in the old database.")

    # Mark is_new=True on truly new, else False
    for item in merged_data:
        if frozenset(item.items()) in truly_new_entries_set:
            item["is_new"] = True
        else:
            item["is_new"] = False

    # Save the merged dataset
    with open(merged_data_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4)
    logger.info(f"Merged data written to {merged_data_path}")

    # Save new entries (if you want to track them separately)
    with open(new_entries_path, 'w', encoding='utf-8') as f:
        json.dump(truly_new_entries, f, indent=4)
    logger.info(f"New entries written to {new_entries_path}")

    return merged_data
