import json
import os
# import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from pprint import pprint

# Determine the directory where this script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the base path and the file paths to combine
input_path = os.path.join(script_directory, "data/raw/all_scraped/")

file_paths = {
    "organisations": os.path.join(input_path, "gtr/scraped/2024_07/organisations.json"),
    "projects": os.path.join(input_path, "gtr/scraped/2024_07/projects.json"),
    "persons": os.path.join(input_path, "gtr/scraped/2024_07/persons.json"),
}

schema_paths = {
    "organisations": os.path.join(input_path, "gtr/scraped/schemas/organisation.json"),
    "projects": os.path.join(input_path, "gtr/scraped/schemas/project.json"),
    "persons": os.path.join(input_path, "gtr/scraped/schemas/person.json"),
}


class SchemaProcessor:
    def __init__(self, schema_path: str):
        """Initialize processor with a schema file path."""
        self.schema = self._load_json(schema_path)
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

    @staticmethod
    def _load_json(filepath: str) -> Dict:
        """Load JSON data from file."""
        with open(filepath, 'r') as f:
            return json.load(f)

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

        # Process nested arrays - Removed for now but revisit. 
        # for path, properties in self.nested_arrays.items():
        #     parts = path.split(".")
        #     current_data = data
        #     for part in parts:
        #         current_data = current_data.get(part, {})
        #         if not current_data:
        #             break

        #     if current_data:
        #         if isinstance(current_data, list):
        #             processed[parts[-1]] = [
        #                 {k: item.get(k) for k in properties}
        #                 for item in current_data
        #             ]
        #         elif isinstance(current_data, dict):
        #             processed[parts[-1]] = [
        #                 {k: v.get(k) for k in properties}
        #                 for v in current_data.values()
        #                 if isinstance(v, dict)
        #             ]

        # Process links
        pprint(data["links"]["link"])
        #! currently manual but could be automated/ based on inputs/schema features
        #! could also come one level up on the links
        if "links" in data and "link" in data["links"]:
            processed["link"] = self._process_links(data["links"]["link"], entity_type)
    
        # if "addresses" in data and "address" in data["addresses"]:
        #     processed["address"] = self._process_nested_special(data, "addresses", "address", entity_type)
        #     processed.pop("address")
    
        return processed

    # def _process_nested_special(self, data, parent, child, entity_type: str):
    #     """
    #     Handle nested fields of form
    #         key: [{key: value, ..., key:value}]
    #     Where the list only contains one dictionary. 

    #     """
    #     fields_dict = {}
    #     if not 
    #     fields = data[parent][child][0].keys()
    



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

def process_dataset(schema_path: str, data_path: str, entity_type: str) -> List[Dict]:
    """Process an entire dataset using its schema."""
    processor = SchemaProcessor(schema_path)
    raw_data = processor._load_json(data_path)
    
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


if __name__ == "__main__":
    # Define schema and data paths
    schemas = {
        'organisations': schema_paths['organisations'],
        'projects': schema_paths['projects'],
        'persons': schema_paths['persons']
    }

    data_files = {
        'organisations': file_paths['organisations'],
        'projects': file_paths['projects'],
        'persons': file_paths['persons']
    }

    test_path = "organisations_cut.json"

    processed_data = {}
    processor = SchemaProcessor(schema_paths['organisations'])
    raw_data = processor._load_json(test_path)
    processed_data = [processor.process_data(item, "organisations") for item in raw_data]
    # processor.process_data(raw_data, 'organisations')
    # pprint(processed_data)
    # save
    with open("processed.json", "w") as f:
        json.dump(processed_data, f, indent=2)
