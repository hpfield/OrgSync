import logging

logger = logging.getLogger(__name__)

def stage7_combine_overlapping_groups(refined_groups):
    logger.info("Combining overlapping groups...")
    group_sets = []
    for names in refined_groups.values():
        # Ensure each group is a set of strings
        if not isinstance(names, list):
            logger.warning(f"Expected a list, got {type(names)}. Converting to empty list.")
            names = []
        else:
            names = [str(name).strip() for name in names]
        group_sets.append(set(names))

    merged_groups = merge_overlapping_groups(group_sets)
    # Convert each set to a sorted list
    merged_groups = [sorted(list(g)) for g in merged_groups]
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

    # Repeatedly merge if new overlaps are introduced
    merging = True
    while merging:
        merging = False
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                if merged[i] & merged[j]:
                    merged[i] |= merged[j]
                    del merged[j]
                    merging = True
                    break
            if merging:
                break
    return merged
