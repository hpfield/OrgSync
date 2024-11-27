from uk_postcodes_parsing import ukpostcode
import pandas as pd
import json
import numpy as np
import re, os, sys
from pprint import pprint
#! NOTE: SOME OF THIS CODE SHOULD BE MOVED TO THE PROCESSING/ CLEANING STAGE

### Load full gtr and cordis datasets (update the cleaning code...)
# data_dir = os.path.join("data", "raw")
# gtr_path = os.path.join(data_dir, "gtr_data.json")
# cordis_path = os.path.join(data_dir, "uk_data.json")

# with open(gtr_path, "r") as f:
#     gtr_data = json.load(f)

# with open(cordis_path, "r") as f:
#     cordis_data = json.load(f)

def rename_fields(data, field_renaming):
    for record in data:
        for old_field, new_field in field_renaming.items():
            record[new_field] = record.pop(old_field)
    return data

def keep_fields(original_data, fields_to_keep, inplace=False):
    # avoid modifying original json by accident!
    if not inplace:
        data = original_data.copy()
    else:
        data = original_data
    for record in data:
        for field in list(record.keys()):
            if field not in fields_to_keep:
                record.pop(field)
    return data

def parse_postcode(postcode):
    parsed = ukpostcode.parse_from_corpus(postcode)
    # parsed is an empty list if the postcode is invalid
    if len(parsed) == 0:
        return None
    return parsed[0].__dict__

def create_single_valued_field(data, field_name, value):
    for record in data:
        record[field_name] = value
    return data


def convert_field_to_str(data, field):
    """
    convert all values in a field to strings
    """
    for record in data:
        print(record[field])
        print(type(record[field]))
        record[field] = str(record[field])
        print(record[field])
    return data

data_path = os.path.join("data","splink","all_data.json")
with open(data_path, "r") as f:
    data = json.load(f)

postcodes = keep_fields(data, ["dataset", "unique_id", "postcode"])


def create_parsed_postcodes_fields(data):
    """
    Takes in json of records with fields "unique_id" and "postcode". Parses postcodes with
    ukpostcode library and adds parsed postcode fields to each record.

    If len(parse_postcode) == 0, then the postcode is not valid, and the record should be 
    populated with None values.
    
    e.g.
    parse_postcode("SW1A 1AA") ->
        {'original': 'SW1A 1AA',
        'postcode': 'SW1A 1AA',
        'incode': '1AA',
        'outcode': 'SW1A',
        'area': 'SW',
        'district': 'SW1',
        'sub_district': 'SW1A',
        'sector': 'SW1A 1',
        'unit': 'AA',
        'fix_distance': 0,
        'is_in_ons_postcode_directory': True} 
    """
    empty_fields = {
            "original": None,  
            "postcode": None,
            "incode": None,
            "outcode": None,
            "area": None,
            "district": None,
            "sub_district": None,
            "sector": None,
            "unit": None,
            "fix_distance": None,
            "is_in_ons_postcode_directory": None
    }

    for record in data:
        if not record["postcode"]:
            record.update(empty_fields)
            continue
        parsed = parse_postcode(record["postcode"])
        if not parsed:
            record.update(empty_fields)
            continue
        record.update(parsed)

    # for all fields other than unique_id and dataset, modify to "parsed." + field
    for record in data:
        for field in list(record.keys()):
            if field not in ["unique_id", "dataset"]:
                record["parsed." + field] = record.pop(field)
    return data

all_postcodes = create_parsed_postcodes_fields(postcodes)
all_postcodes
# save to json
save_path = os.path.join("data", "splink", "parsed_postcodes.json")
# check if path exists, else create
if not os.path.exists(os.path.dirname(save_path)):
    os.makedirs(os.path.dirname(save_path))
with open(save_path, "w") as f:
    json.dump(all_postcodes, f, indent=2)



#! Move to cleaning script
# gtr_field_renaming = {
#     "id": "unique_id",
#     "postCode": "postcode",
# }

# cordis_field_renaming = {
#     "organisationID": "unique_id",
#     # "postCode": "postcode",
# }

# gtr_data = rename_fields(gtr_data, gtr_field_renaming)
# cordis_data = rename_fields(cordis_data, cordis_field_renaming)

# create_single_valued_field(gtr_data, "dataset", "gtr")
# create_single_valued_field(cordis_data, "dataset", "cordis")


# fields_to_keep = ["dataset","unique_id", "postcode"]

# # isolate poctcodes, keeping ids to link back to original data
# cordis_postcodes = keep_fields(cordis_data, fields_to_keep)
# gtr_postcodes = keep_fields(gtr_data, fields_to_keep)

# # combine
# all_postcodes = cordis_postcodes + gtr_postcodes

# df = pd.DataFrame(all_postcodes)
# df.tail()
