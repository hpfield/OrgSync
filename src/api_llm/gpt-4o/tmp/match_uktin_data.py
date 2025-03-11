#!/usr/bin/env python3
import json
import random
from tqdm import tqdm  # for progress bars

def main():
    # File paths
    projects_file = '/home/ubuntu/OrgSync/data/raw/all_scraped/uktin/projects.json'
    groups_file = '/home/ubuntu/OrgSync/src/api_llm/gpt-4o/outputs/output_groups.json'
    output_file = '/home/ubuntu/OrgSync/src/api_llm/gpt-4o/outputs/GTR_CORDIS_UKTIN_output_groups.json'
    
    # Load the projects data
    print(f"Loading projects data from: {projects_file}")
    with open(projects_file, 'r') as f:
        projects = json.load(f)
    
    # Extract partner items from projects data.
    print("Extracting partner items from projects data...")
    partner_items = {}  # mapping: partner name (lowercase) -> list of items
    for project_url, project_data in tqdm(projects.items(), desc="Processing projects", total=len(projects)):
        partners = project_data.get("partners", [])
        for partner in partners:
            partner_lower = partner.lower()
            item = {
                "org_name": partner_lower,
                "unique_id": project_url,
                "dataset": "uktin",
                "postcode": ""
            }
            partner_items.setdefault(partner_lower, []).append(item)
    
    # Load the existing groupings data
    print(f"\nLoading existing groups data from: {groups_file}")
    with open(groups_file, 'r') as f:
        groups = json.load(f)
    
    # Build a mapping from each group ID to the set of names in that group.
    print("Building group names mapping for matching...")
    group_names_mapping = {}
    for group_id, group_data in tqdm(groups.items(), desc="Mapping groups", total=len(groups)):
        names_set = set()
        group_name = group_data.get("name", "").lower()
        if group_name:
            names_set.add(group_name)
        for item in group_data.get("items", []):
            org_name = item.get("org_name", "").lower()
            if org_name:
                names_set.add(org_name)
        group_names_mapping[group_id] = names_set
    
    # Counters for summary
    total_names = len(partner_items)
    mapped_count = 0

    # Process each partner from the projects data and update groups if a match is found.
    print("Updating groups with new partner items...")
    for partner_lower, items in tqdm(partner_items.items(), desc="Processing partners", total=total_names):
        matching_group_ids = []
        for group_id, names_set in group_names_mapping.items():
            if partner_lower in names_set:
                matching_group_ids.append(group_id)
        
        if matching_group_ids:
            chosen_group_id = random.choice(matching_group_ids)
            print(f"Match found for '{partner_lower}' in group {chosen_group_id}. Adding {len(items)} item(s).")
            groups[chosen_group_id]["items"].extend(items)
            # Update the names mapping for the chosen group
            group_names_mapping[chosen_group_id].add(partner_lower)
            mapped_count += 1
    
    # Write the updated groups to the output file
    print(f"\nWriting updated groups data to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(groups, f, indent=2)
    
    print(f"\nProcessing complete. {mapped_count} out of {total_names} partner names were mapped.")

if __name__ == "__main__":
    main()
