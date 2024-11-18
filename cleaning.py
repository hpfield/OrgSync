import json
import os
# import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from pprint import pprint
import pandas as pd


pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_colwidth', 199)
pd.set_option('display.width', 200)
pd.set_option('display.expand_frame_repr', True)

#! if running from repo root...
# Determine the directory where this script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

## data & Globals
base_path = os.path.join(script_directory, "data", "raw")
file_paths = {
    "gtr": os.path.join(base_path, "gtr_data.json"),
    "cordis": os.path.join(base_path, "uk_data.json"),
}

# testing on smaller datasets first.
base_test_dir = os.path.join(script_directory, "data", "test")
test_paths = {
    "gtr": os.path.join("data", "test", "gtr_organisations_processed.json"),
    "cordis": os.path.join("data", "test", "uk_data.json"),
}

# Initial fields of interest for each dataset
gtr_fields_to_keep = [
    "name",
    "id", # kept as unique identifier but not used for matching
    # "address.country", # exclude as all UK at this point
    "address.type",
    "address.postCode",
    "address.region",
    "link.EMPLOYEE" # kept as only contains one person per org so suitable to splink without array matching
    # "created", # include to match with contentUpdateDate not implemented
]

cordis_fields_to_keep = [
    "name",
    "shortName",
    # "projectAcronym",
    "organisationID",
    "city", 
    # "country", # exclude as all UK at this point
    "geolocation",
    "postCode",
    "street",
    "nutsCode",
    "rcn",
    "organisationURL",
    # "contentUpdateDate" # not implemented
]

def remove_fields(data: List[Dict[str, Any]], fields_to_keep: List[str]) -> List[Dict[str, Any]]:
    """
    Removes fields from a list of dictionaries
    """
    for entry in data:
        for key in list(entry.keys()):
            if key not in fields_to_keep:
                del entry[key]
    return data

def preprocess_name(name):
    name = name.lower()  # Convert to lowercase
    name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with a single space
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    return name.strip()  # Strip leading and trailing whitespace

# Combine fields representing same information

# Search for urls for entries, create new field

# process fields for splink

# set up blocking and matching rules

# run splink

if __name__ == "__main__":
    # load data
    output_dir = os.path.join(base_path, "processed")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    test_paths = file_paths
    full_path = test_paths["gtr"]
    with open(full_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for entry in data:
        entry["name"]
    gtr_data = remove_fields(data, gtr_fields_to_keep)
    # save json
    with open(os.path.join(output_dir, "gtr_data.json"), 'w', encoding='utf-8') as file:
        json.dump(gtr_data, file, indent=4)

    full_path= test_paths["cordis"]
    with open(full_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    cordis_data = remove_fields(data, cordis_fields_to_keep)
    # save json
    with open(os.path.join(output_dir, "cordis_data.json"), 'w', encoding='utf-8') as file:
        json.dump(cordis_data, file, indent=4)


    output_dir = os.path.join("base_path")

    print("Done")





