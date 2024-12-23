import json
import os
import yaml
import argparse
from src.setup_utils import (
    process_gtr_data,
    load_json,
    save_json,
    add_const_field_json,
    remove_fields,
    map_names_json,
    convert_entries_to_str
)

if __name__ == "__main__":
    # Set up argument parser to allow testing only on Cordis data only
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cordis_only",
        default=False,
        action = "store_true",
        help="Process Cordis data only"
    )
    args = parser.parse_args()
    if args.cordis_only:
        print("Processing Cordis data only")
    else:
        print("Processing Cordis and GtR data")
    

    # Determine the directory where this script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the base path for raw data
    input_path = os.path.join(script_directory, "data/raw/all_scraped/")
    # Define the file paths to combine for Cordis data
    cordis_files = [
        "cordis/2024_07/FP7/organization.json",
        "cordis/2024_07/Horizon 2020/organization.json",
        "cordis/2024_07/Horizon Europe/organization.json",
    ]
    gtr_file = "gtr/scraped/2024_07/organisations.json"

    # Combine and filter Cordis data
    uk_data = []

    # Iterate over the file paths, read, filter and append data to uk_data
    for file_path in cordis_files:
        full_path = os.path.join(input_path, file_path)
        data = load_json(full_path)
        # Filter the data where country is "UK". Unlike GtR, Cordis has non-UK entries
        uk_entries = [entry for entry in data if entry.get("country") == "UK"]
        uk_data.extend(uk_entries)

    # Specify the output file path
    output_file_path = os.path.join(script_directory, "data", "raw", "uk_data.json")

    # Write the filtered UK data to the output file
    if args.cordis_only:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(uk_data, output_file, indent=4)
        print(f"Filtered Cordis data has been written to {output_file_path}")

    else:
        # Save initial Cordis data with added dataset field
        cordis_data = add_const_field_json(uk_data, "dataset", "cordis")
        save_json(
            cordis_data, 
            'cordis_data.json', 
            save_dir=os.path.join(script_directory, 'data/raw/')
        )
        # load and apply processing function for gtr data to transform to flat structure
        gtr_file = os.path.join(input_path, gtr_file)
        raw_gtr_data = load_json(gtr_file)
        processed_gtr = process_gtr_data(raw_gtr_data)
        save_json(
            processed_gtr, 
            'gtr_data.json', 
            save_dir=os.path.join(script_directory, 'data/raw/')
        )
        # Any fields not named in fields to keep will be excluded from final uk_data.json
        gtr_fields_to_keep = [
            "dataset",
            "name",
            "id",
            "address.postCode",
        ]
        cordis_fields_to_keep = [
            "dataset",
            "name",
            "shortName",
            "organisationID",
            "postCode",
        ]
        # Remap names as postcode and unique id have different names in gtr and cordis
        map_names_gtr = {
            "id": "unique_id",
            "address.postCode": "postcode"
        }
        map_names_cordis = {
            "organisationID": "unique_id",
            "postCode": "postcode"
        }

        # Add dataset field to processed GTR data
        gtr_data = add_const_field_json(processed_gtr, "dataset", "gtr")
        # Apply transformations to both datasets
        gtr_data = remove_fields(gtr_data, gtr_fields_to_keep)
        gtr_data = map_names_json(gtr_data, map_names_gtr)
        cordis_data = remove_fields(cordis_data, cordis_fields_to_keep)
        cordis_data = map_names_json(cordis_data, map_names_cordis)
        # Combine and save final dataset
        uk_data = cordis_data + gtr_data
        # some unique ids and postcodes need to be converted from int
        convert_entries_to_str(uk_data, ["postcode", "unique_id"])
        output_file_path = os.path.join(script_directory, "data", "raw", "uk_data.json")
        with open (output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(uk_data, output_file, indent=4)
        print(f"Combined Cordis and GtR data has been written to {output_file_path}")
        
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