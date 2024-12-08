# imports
import json
import os
from typing import Dict, List, Any

def load_json(filepath: str, encoding="utf-8") -> Dict:
    """Load JSON data from file."""
    with open(filepath, 'r', encoding=encoding) as f:
        return json.load(f)

def save_json(data: Any, filename: str, save_dir: str|None = None, encoding="utf-8") -> None:
    """Save JSON data to file."""
    if not filename.endswith(".json"):
        filename += ".json"

    if save_dir:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_path = os.path.join(save_dir, filename)
    else:
        save_path = filename

    with open(save_path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {save_path}")

def process_gtr_data(raw_data):
    """
    Transform GTR organization data from nested to flat structure.
    
    Args:
        raw_data: List of dictionaries containing raw GTR organization data
        
    Returns:
        List of transformed organization dictionaries
    """
    processed_data = []
    
    for org in raw_data:
        # Initialize the transformed organization record
        transformed_org = {
            'name': org['name'],
            'id': org['id'],
            'created': org['created'],
            'href': org['href'],
            # 'dataset': 'gtr' # can add const field but currently handled in setup.py for dataset
        }
        
        # Process address information
        if org.get('addresses') and org['addresses'].get('address'):
            address = org['addresses']['address'][0]  # Taking first address since data shows only one exists
            transformed_org.update({
                'address.postCode': address.get('postCode'),
                'address.region': address.get('region'),
                'address.country': address.get('country'),
                'address.type': address.get('type')
            })
            
        # Process links - group by relationship type
        if org.get('links') and org['links'].get('link'):
            link_groups = {}
            
            for link in org['links']['link']:
                rel_type = link.get('rel')
                if rel_type:
                    # Extract ID from href
                    entity_id = link['href'].split('/')[-1]
                    
                    # Initialize list for this relationship type if it doesn't exist
                    if f'link.{rel_type}' not in link_groups:
                        link_groups[f'link.{rel_type}'] = []
                        
                    link_groups[f'link.{rel_type}'].append(entity_id)
            
            # Add all link groups to transformed organization
            transformed_org.update(link_groups)
        
        processed_data.append(transformed_org)
    
    return processed_data

def add_const_field_json(data: List[Dict[str, Any]], field_name: str, field_value: Any) -> List[Dict[str, Any]]:
    """Add a constant field to all dictionaries in a list."""
    return [{**item, field_name: field_value} for item in data]

def remove_fields(data: List[Dict[str, Any]], fields_to_keep: List[str]) -> List[Dict[str, Any]]:
    """Keep only specified fields in each dictionary."""
    return [{k: v for k, v in entry.items() if k in fields_to_keep} for entry in data]

def map_names_json(data: List[Dict[str, Any]], map_names: Dict[str, str]) -> List[Dict[str, Any]]:
    """Rename fields in dictionaries according to mapping."""
    for entry in data:
        for old_name, new_name in map_names.items():
            if old_name in entry:
                entry[new_name] = entry.pop(old_name)
    return data

def convert_entries_to_str(data: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
    """Convert specified fields to strings in all dictionaries."""
    for entry in data:
        for field in fields:
            if field in entry and not isinstance(entry[field], str):
                entry[field] = str(entry[field])
    return data

# Example usage:
if __name__ == "__main__":
    import json
    
    # Read input data
    with open('organisations.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Process the data
    processed = process_gtr_data(raw_data)
    
    # Save processed data
    with open('processed_organisations.json', 'w', encoding='utf-8') as f:
        json.dump(processed, f, indent=2)