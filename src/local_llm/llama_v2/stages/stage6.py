import logging

# Initialize logger
logger = logging.getLogger(__name__)

def stage6_combine_overlapping_groups(refined_groups):
    logger.info("Combining overlapping groups...")
    group_sets = []
    for names in refined_groups.values():
        if not isinstance(names, list):
            logger.warning(f"Expected names to be a list, but got {type(names)}. Setting names to an empty list.")
            names = []
        else:
            names = [str(name) for name in names if isinstance(name, str)]
        try:
            group_sets.append(set(names))
        except TypeError as e:
            logger.error(f"Error converting names to set: {e}. Names: {names}")
            continue

    merged_groups = merge_overlapping_groups(group_sets)
    logger.info(f"Number of combined groups: {len(merged_groups)}")
    return merged_groups

def merge_overlapping_groups(group_sets):
    merged = []
    for group in group_sets:
        found = False
        for mgroup in merged:
            if group & mgroup:
                mgroup |= group
                found = True
                break
        if not found:
            merged.append(set(group))
    merging = True
    while merging:
        merging = False
        for i in range(len(merged)):
            for j in range(i+1, len(merged)):
                if merged[i] & merged[j]:
                    merged[i] |= merged[j]
                    del merged[j]
                    merging = True
                    break
            if merging:
                break
    return merged
