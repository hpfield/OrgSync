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

file_paths = {
    "gtr": os.path.join(script_directory, "data", "processed" "gtr_organisations_processed.csv"),
    "cordis": os.path.join(script_directory, "data", "raw", "uk_data.json"),
}

test_paths = {
    "gtr": os.path.join("data", "test", "gtr_organisations_processed.csv"),
    "cordis": os.path.join("data", "test", "uk_data.json"),
}

# Initial fields of interest for each dataset
gtr_fields_to_keep = [
    "name",
    "id",
    # "address.country", # exclude as all UK at this point
    "address.type",
    "address.postCode",
    "address.region",
    "link.EMPLOYEE" # kept as only contains one person per org so suitable to splink without array matching
    # "created", # include to match with contentUpdateDate not implemented
]

coris_fields_to_keep = [
    "name",
    "shortName",
    "projectAcronym",
    "city", 
    # "country", # exclude as all UK at this point
    "geolocation",
    "postCode",
    "street",
    "nutsCode",
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

# Combine fields representing same information

# Search for urls for entries, create new field

# process fields for splink

# set up blocking and matching rules

# run splink

if __name__ == "__main__":
    # load data
    gtr_data = pd.read_csv(test_paths["gtr"])
    cordis_data = pd.read_json(test_paths["cordis"])

    # remove fields
    gtr_data = remove_fields(gtr_data, gtr_fields_to_keep)
    cordis_data = remove_fields(cordis_data, coris_fields_to_keep)

    # save to test dir
    base = os.path.join(script_directory, "data", "test")
    gtr_data.to_csv(os.path.join(base, "gtr_test.csv"), index=False)
    cordis_data.to_json(os.path.join(base, "cordis_test.json"), orient="records")


