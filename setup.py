import json
import os
import yaml
import argparse
from src.util_funcs import (
    SchemaProcessor, 
    normalize_json_fields, 
    read_json, 
    save_json,
    add_const_field_json,
    remove_fields,
    map_names_json,
    convert_entries_to_str
)

# Allow testing only on Cordis data only
parser = argparse.ArgumentParser()
parser.add_argument(
    "--all_data", 
    default = True, 
    type = bool, 
    help="Create separate json for GtR data")

# Determine the directory where this script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the base path and the file paths to combine
input_path = os.path.join(script_directory, "data/raw/all_scraped/")
file_paths = [
    "cordis/2024_07/FP7/organization.json",
    "cordis/2024_07/Horizon 2020/organization.json",
    "cordis/2024_07/Horizon Europe/organization.json",
]

# Initialize an empty list to store combined data
uk_data = []

# Iterate over the file paths, read, filter and append data to uk_data
for file_path in file_paths:
    full_path = os.path.join(input_path, file_path)
    with open(full_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        # Filter the data where country is "UK"
        uk_entries = [entry for entry in data if entry.get("country") == "UK"]
        uk_data.extend(uk_entries)

# Specify the output file path
output_file_path = os.path.join(script_directory, "data", "raw", "uk_data.json")

# Write the filtered UK data to the output file
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(uk_data, output_file, indent=4)

print(f"Filtered Cordis data has been written to {output_file_path}")


if parser.parse_args().all_data:
    # process gtr data
    cordis_data = add_const_field_json(uk_data, "dataset", "cordis")
    save_json(cordis_data, os.path.join(script_directory, 'data/raw/cordis_data.json'))
    print(f"Filtered Cordis data has been written to {os.path.join(script_directory, 'data/raw/cordis_data.json')}")
    
    base_dir = os.path.join("data", "raw", "all_scraped")
    file_path = os.path.join(base_dir,"gtr", "scraped", "2024_07", "organisations.json")
    schema_path = os.path.join(base_dir, "gtr", "scraped", "schemas", "organisation.json")

    raw_data = read_json(file_path)
    schema = read_json(schema_path)
    processor = SchemaProcessor(raw_data, schema)
    processed_data = [processor.process_data(item, "organisations") for item in raw_data]
    normalised_data = normalize_json_fields(processed_data)
    gtr_data = add_const_field_json(normalised_data, "dataset", "gtr")
    save_dir = os.path.join(script_directory, "data/raw/")
    save_json(gtr_data, os.path.join(save_dir, 'gtr_data.json'))
    print(f"Normalised GtR data has been written to {os.path.join(save_dir, 'gtr_data.json')}")

    # combine datasets including only fields of interest
    gtr_fields_to_keep = [
        "dataset",
        "name",
        "id",
        # "address.type",
        "address.postCode",
        # "address.region",
    ]

    cordis_fields_to_keep = [
        "dataset",
        "name",
        "shortName",
        # "projectAcronym",
        "organisationID",
        # "city", 
        # "geolocation",
        "postCode",
        # "street",
        # "nutsCode",
        # "rcn",
        # "organisationURL",
    ]

    map_names_gtr = {
        "id": "unique_id",
        "address.postCode": "postcode"
    }
    map_names_cordis = {
        "organisationID": "unique_id",
        "postCode": "postcode"
    }

    gtr_data = remove_fields(gtr_data, gtr_fields_to_keep)
    gtr_data = map_names_json(gtr_data, map_names_gtr)

    cordis_data = remove_fields(cordis_data, cordis_fields_to_keep)
    cordis_data = map_names_json(cordis_data, map_names_cordis)
    
    uk_data = cordis_data + gtr_data
    convert_entries_to_str(uk_data, ["postcode", "unique_id"])
    save_json(uk_data, os.path.join(script_directory, 'data/raw/uk_data.json'))



# Path to the config file
config_file_path = os.path.join(script_directory, "cfg/config.yaml")

# Append the project root to the config file
project_root_key = "project_root"
project_root_value = script_directory

# Load existing config if it exists, or create a new dict
if os.path.exists(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as config_file:
        config_data = yaml.safe_load(config_file) or {}
else:
    config_data = {}

# Update the config with the project root path
config_data[project_root_key] = project_root_value

# Write the updated config back to the config file
with open(config_file_path, 'w', encoding='utf-8') as config_file:
    yaml.safe_dump(config_data, config_file)

print(f"Project root has been set to {project_root_value} in {config_file_path}")
