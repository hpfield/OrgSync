import json
import os
# import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from pprint import pprint

def map_names_json(data: List[Dict[str, Any]], map_names: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Rename fields in a list of dictionaries.

    Args:
        data: List of dictionaries to process
        map_names: Dictionary mapping old field names to new field names

    Returns:
        List of dictionaries with renamed fields
    """
    for entry in data:
        for key, value in map_names.items():
            if key in entry:
                entry[value] = entry[key]
                del entry[key]
    return data

# def map_names_json(data, map_names):
#         """
#         Changes the name of a field using a mapping dictionary, removing the old field name
#         """
#         for entry in data:
#             for key, value in map_names.items():
#                 entry[value] = entry.pop(key)
#         return data

def convert_entries_to_str(data: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
    """
    Convert fields in a list of dictionaries to strings.

    Args:
        data: List of dictionaries to process
        fields: List of fields to convert to strings

    Returns:
        List of dictionaries with specified fields converted to strings
    """
    for entry in data:
        for field in fields:
            if field in entry:
                if not isinstance(entry[field], str):
                    entry[field] = str(entry[field])
    return data

def remove_fields(data: List[Dict[str, Any]], fields_to_keep: List[str]) -> List[Dict[str, Any]]:
    """
    Removes fields from dictionaries in a list of dictionaries.

    Args:
        data: List of dictionaries to process
        fields_to_keep: List of fields to keep in each dictionary

    Returns:
        List of dictionaries with only the specified fields 
    """
    for entry in data:
        for key in list(entry.keys()):
            if key not in fields_to_keep:
                del entry[key]
    return data

def add_const_field_json(data: List[Dict[str, Any]], field_name: str, field_value: Any) -> List[Dict[str, Any]]:
    """Add a constant field to all dictionaries in a list."""
    return [{**item, field_name: field_value} for item in data]

def save_json(data: Any, filename:str, save_dir: str|None = None, encoding="utf-8") -> None:
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
        json.dump(data, f, indent=2)
    print(f"Data saved to {save_path}")
    


def read_json(filepath: str, encoding="utf-8") -> Dict:
    """Load JSON data from file."""
    with open(filepath, 'r', encoding=encoding) as f:
        return json.load(f)

def normalize_json_fields(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of dictionaries by ensuring all dictionaries have the same fields.
    Missing fields are populated with None.
    
    Args:
        data: List of dictionaries to normalize
        
    Returns:
        List of normalized dictionaries with consistent fields
    """
    # First pass: collect all possible fields
    all_fields = set()
    for item in data:
        all_fields.update(item.keys())
    
    # Second pass: normalize all dictionaries
    normalized_data = []
    for item in data:
        normalized_item = {field: item.get(field, None) for field in all_fields}
        normalized_data.append(normalized_item)
    
    return normalized_data

def normalize_json_file(input_path: str, output_path: str) -> None:
    """
    Read JSON file, normalize all dictionaries, and write back to new file.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to write normalized JSON file
    """
    # Read input file
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Normalize data
    normalized_data = normalize_json_fields(data)
    
    # Write normalized data
    with open(output_path, 'w') as f:
        json.dump(normalized_data, f, indent=2)
        
def analyze_field_coverage(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Analyze what percentage of records have each field.
    
    Args:
        data: List of dictionaries to analyze
        
    Returns:
        Dictionary mapping field names to their coverage percentage
    """
    total_records = len(data)
    field_counts = defaultdict(int)
    
    for item in data:
        for field in item.keys():
            field_counts[field] += 1
    
    coverage = {
        field: (count / total_records) * 100 
        for field, count in field_counts.items()
    }
    
    return coverage


class SchemaProcessor:
    """
    Process GtR data according to it's schema to remove explode nested fields into
    individual fields with single values per entry, and array fields containing multiple values. 
    """
    def __init__(self, data_json, schema):
        """Initialize processor with a schema file path."""
        self.data_json = data_json
        self.schema = schema
        self.processed_fields = set()
        self.nested_arrays = {}
        self.links = {}
        self.lookup_parent = {}
        self._analyze_schema(self.schema)
        self._convert_nested_fields()
        # pprint(self.processed_fields)
        # pprint(self.nested_arrays)
        # pprint(self.links)
        # pprint(self.lookup_parent)

    # @staticmethod
    # def load_json(filepath: str) -> Dict:
    #     """Load JSON data from file."""
    #     with open(filepath, 'r') as f:
    #         return json.load(f)

    def _analyze_schema(self, schema: Dict, parent_path: str = "") -> None:
        """Recursively analyze schema to identify nested structures and links."""
        if not isinstance(schema, dict):
            return

        # Handle items in arrays
        if "items" in schema:
            self._analyze_schema(schema["items"], parent_path)
            return

        # Process properties
        properties = schema.get("properties", {})
        for field, details in properties.items(): #! if one one field and that field is object, then current_path = something else?
            current_path = f"{parent_path}.{field}" if parent_path else field
            
            if details.get("type") == "array":
                array_items = details.get("items", {})
                if array_items.get("type") == "object":
                    self.nested_arrays[current_path] = array_items.get("properties", {})
            
            elif details.get("type") == "object":
                self._analyze_schema(details, current_path)

            # Track fields that are required
            if field in schema.get("required", []):
                self.processed_fields.add(field)

            # # Special handling for links
            # if field == "links":
            #     self.links[current_path] = details
    
    def _convert_nested_fields(self):
        for key in self.nested_arrays:
            parts = key.split(".")
            parent = parts[0]
            child = parts[1]
            self.lookup_parent[child] = parent
            
    def process_data(self, data: Dict, entity_type: str) -> Dict:
        """Process a single data entry according to schema."""
        processed = {}
        skip_fields = []
        # Basic fields
        for field in self.processed_fields:
            # this will not catch nested fields deeper than 1 level
            # field only in data if field is top level key
            if not field in data:
                if not field in self.lookup_parent:
                    continue
                parent = self.lookup_parent[field]
                if not parent in data:
                    continue
                if not field in data[parent]:
                    continue
                processed[field] = data[parent][field]
                skip_fields.append(parent)
                skip_fields.append(field)

        non_nested_fields = [field for field in self.processed_fields if field not in skip_fields]
        for field in non_nested_fields:
            if field in data:
                # pprint(data[field])
                processed[field] = data[field]
                continue
        
        # Some fields contain lists of dictionaries with the same keys, corresponding with different
        # entities, so we want to explode these out into separate fields. 
        # Current method is specific to the "links" column but could be generalised. 
        if "links" in data and "link" in data["links"]:
            #Using "link" to replace existing link dict. Could rename and manually drop the old link dicts. 
            processed["link"] = self._process_links(data["links"]["link"], entity_type)
    
        # Handle nested fields by specifying which fields to keep 
        chosen_children_of_parent = {
            "address": ["postCode", "region", "country", "type"],
            "link": []
        } 

        for k, v in chosen_children_of_parent.items():
            parent = k
            child_fields_to_keep = v
            if not parent in processed:
                raise ValueError(f"Parent {parent} not in processed data.") 
    
            processed_children = self._process_nested_special(processed, parent, child_fields_to_keep)
            processed.pop(parent)
            if not processed_children:
                continue
            for key, value in processed_children.items():
                processed[f"{parent}.{key}"] = value

        return processed

    def _process_nested_special(self, processed_data: dict, parent_key: str, child_fields_to_keep: List[str]):
        """
        Handle nested fields of form
            key: [{key: value, ..., key:value}]
        Where the list only contains one dictionary. 


        Parameters
        ----------
        processed_data : dict
            The full processed entity dictionary.
    
        parent_key : str
            The key of the nested data.
        
        child_fields_to_keep : List[str]
            The fields to keep from the nested data. If empty, all fields are kept.

        Returns
        -------
        relationships : dict
            The processed nested data keys and value. 
        """
        relationships = {}
        parent = processed_data[parent_key]
        if isinstance(parent, dict):
            parent_dict = parent

        elif isinstance(processed_data[parent_key], list):
            # Currently assuming multiple dictionaries in list would have same fields
            # meaning if we explode them out, they would replace oneanother.
            if len(parent) > 1:
                raise ValueError("Error: List contains multiple dictionaries")
            # Some lists can be empty, in which case we return None so that it can be handled later.
            if len(parent) == 0:
                return None
            parent_dict = parent[0]
            
        else:
            raise ValueError("Nested data is not a list or dict.")

        if len(child_fields_to_keep) == 0:
            child_fields_to_keep = list(parent_dict.keys())
        
        for child_field in child_fields_to_keep:
            assert child_field in parent_dict, f"Field {child_field} not in nested data."
            data = parent_dict.get(child_field)
            relationships[child_field] = data
        return relationships
        
        # # child_fields = nested_data[parent_key][0].keys()
        # if len(child_fields_to_keep) == 0:
        #     child_fields_to_keep = processed_data[parent_key][0].keys()


        # for child_field in child_fields_to_keep:
        #     # data = processed_data[parent_key][0][child_field]
        #     # assert data is not None, f"Data for {child_field} is None."
        #     assert child_field in processed_data[parent_key][0], f"Field {child_field} not in nested data."
        #     data = processed_data[parent_key][0].get(child_field)
        #     relationships[child_field] = data
        # return relationships


            

        # if not nested_data[parent][child]:
        # fields_dict = {}
        # if not 
        # fields = nested_data[parent][child][0].keys()
    


    #! Handles transforming of list of dicts, to separate fields based on keys from the dicts. 
    def _process_links(self, links: List[Dict], entity_type: str) -> Dict[str, List[str]]:
        """Process links into categorized relationships."""
        relationships = defaultdict(list)
        
        for link in links:
            rel_type = link.get("rel", "")#.lower()
            href = link.get("href", "")
            if href:
                entity_id = href.split("/")[-1]
                relationships[rel_type].append(
                    entity_id, #! specific to GTR schema
                    )
                # relationships[rel_type].append({
                #     "id": entity_id, #! specific to GTR schema
                #     "type": rel_type, #! specific to GTR schema
                # })
        return dict(relationships)

def process_dataset(data_json, schema, entity_type: str) -> List[Dict]:
    """Process an entire dataset using its schema."""
    processor = SchemaProcessor(data_json, schema)
    raw_data = processor.data_json
    
    # Handle both single objects and arrays
    if isinstance(raw_data, list):
        return [processor.process_data(item, entity_type) for item in raw_data]
    return [processor.process_data(raw_data, entity_type)]

def combine_datasets(processed_data: Dict[str, List[Dict]]) -> List[Dict]:
    """Combine processed datasets into a single coherent structure."""
    combined = []
    
    # Start with organizations
    for org in processed_data['organizations']:
        org_record = {
            'organization': {
                'id': org.get('id'),
                'name': org.get('name'),
                'created': org.get('created')
            },
            'relationships': org.get('relationships', {}),
            'projects': [],
            'persons': []
        }
        
        # Add related projects
        project_refs = {
            rel['id'] for rel in org.get('relationships', {}).get('project', [])
        }
        org_record['projects'] = [
            proj for proj in processed_data['projects']
            if proj.get('id') in project_refs
        ]
        
        # Add related persons
        person_refs = {
            rel['id'] for rel in org.get('relationships', {}).get('employee', [])
        }
        org_record['persons'] = [
            person for person in processed_data['persons']
            if person.get('id') in person_refs
        ]
        
        combined.append(org_record)
    
    return combined


# if __name__ == "__main__":
#     # Define schema and data paths
#     schemas = {
#         'organisations': schema_paths['organisations'],
#         'projects': schema_paths['projects'],
#         'persons': schema_paths['persons']
#     }

#     data_files = {
#         'organisations': file_paths['organisations'],
#         'projects': file_paths['projects'],
#         'persons': file_paths['persons']
#     }

#     # process orgs only as not using linked fields for splink matching
#     processor = SchemaProcessor(schema_paths['organisations'])
#     raw_data = processor.load_json(data_files['organisations'])
#     processed_data = [processor.process_data(item, "organisations") for item in raw_data]
#     # processor.process_data(raw_data, 'organisations')
#     # pprint(processed_data)
#     # save
#     normalised_data = normalize_json_fields(processed_data)

#     save_path = os.path.join(script_directory, "data/raw/")
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)
#     save_as = "gtr_data.json"
#     with open(os.path.join(save_path, save_as), "w") as f:
#         json.dump(normalised_data, f, indent=2)
#     print(f"Data saved to {os.path.join(save_path, save_as)}")
