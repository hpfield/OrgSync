# stages/stage5.py

def stage5_combine_overlapping_groups(refined_groups):
    print("Combining overlapping groups...")
    group_sets = []
    for names in refined_groups.values():
        if not isinstance(names, list):
            print(f"Expected names to be a list, but got {type(names)}")
            names = []
        else:
            names = [str(name) for name in names if isinstance(name, str)]
        try:
            group_sets.append(set(names))
        except TypeError as e:
            print(f"Error converting names to set: {e}")
            print(f"Names: {names}")
            continue

    merged_groups = merge_overlapping_groups(group_sets)
    print(f"Number of combined groups: {len(merged_groups)}")
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
