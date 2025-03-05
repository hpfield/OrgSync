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
    convert_entries_to_str,
    process_uktin_names_only
)
# Any fields not named in fields to keep will be excluded from final uk_data.json
GTR_FIELDS_TO_KEEP = [
    "dataset",
    "name",
    "id",
    "address.postCode",
]
CORDIS_FIELDS_TO_KEEP = [
    "dataset",
    "name",
    "shortName",
    "organisationID",
    "postCode",
]

# Remap names as postcode and unique id have different names in gtr and cordis
MAP_NAMES_GTR = {
    "id": "unique_id",
    "address.postCode": "postcode"
}
MAP_NAMES_CORDIS = {
    "organisationID": "unique_id",
    "postCode": "postcode"
}
    
def check_all_datasets_parsed(datasets_to_parse, parsed_datasets):
    return all(dataset in parsed_datasets for dataset in datasets_to_parse)

if __name__ == "__main__":
    # Set up argument parser to allow testing only on Cordis data only
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--datasets",
        help="list all datasets (uktin, gtr, cordis) to be processed using --datasets dataset1 dataset2 ...",
        nargs="+",
        default=["cordis", "gtr", "uktin"],
    )
    parser.add_argument(
        "--which_version",
        help="specify which version of the data to use (old or new)",
        default="new",
    )
    datasets_to_parse = parser.parse_args().datasets
    which_version = parser.parse_args().which_version

    # Get the script directory for relative data imports
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the base path for raw data, modify if this changes
    if which_version == "new":
        input_path = os.path.join(script_directory, "data", "raw")
    else:
        input_path = os.path.join(script_directory, "data", "raw", "all_scraped")

    cordis_files = [
            "cordis/FP7/organization.json",
            "cordis/Horizon 2020/organization.json",
            "cordis/Horizon Europe/organization.json",
    ]
    gtr_file = "gtr/organisations.json"

    uktin_file = "uktin/projects.json"

    # Combine and filter Cordis data
    uk_data = []
    parsed_datasets = []
    # Specify the output file path
    if which_version == "old":
        output_file_path = os.path.join(script_directory, "data", "raw", "uk_data_old.json")
    else: 
        output_file_path = os.path.join(script_directory, "data", "raw", "uk_data.json")

    if "cordis" in datasets_to_parse:
        # Iterate over the file paths, read, filter and append data to uk_data
        cordis_uk_data = []
        for file_path in cordis_files:
            full_path = os.path.join(input_path, file_path)
            data = load_json(full_path)
            # Filter the data where country is "UK". Unlike GtR, Cordis has non-UK entries
            uk_entries = [entry for entry in data if entry.get("country") == "UK"]
            cordis_uk_data.extend(uk_entries)
        cordis_uk_data = add_const_field_json(cordis_uk_data, "dataset", "cordis")
        # Save initial Cordis data with added dataset field
        save_json(
            cordis_uk_data, 
            'cordis_data.json', 
            save_dir=os.path.join(script_directory, 'data/raw/')
        )
        cordis_data = remove_fields(cordis_uk_data, CORDIS_FIELDS_TO_KEEP)
        cordis_data = map_names_json(cordis_data, MAP_NAMES_CORDIS)
        uk_data.extend(cordis_data)
        parsed_datasets.append("cordis")
    
    if "gtr" in datasets_to_parse:
        # load and apply processing function for gtr data to transform to flat structure
        gtr_file = os.path.join(input_path, gtr_file)
        raw_gtr_data = load_json(gtr_file)
        processed_gtr = process_gtr_data(raw_gtr_data)
        gtr_data = add_const_field_json(processed_gtr, "dataset", "gtr")
        
        save_json(
            processed_gtr, 
            'gtr_data.json', 
            save_dir=os.path.join(script_directory, 'data/raw/')
        )
        gtr_data = remove_fields(gtr_data, GTR_FIELDS_TO_KEEP)
        gtr_data = map_names_json(gtr_data, MAP_NAMES_GTR)
        uk_data.extend(gtr_data)
        parsed_datasets.append("gtr")
        # Apply transformations to both datasets
        
    if "uktin" in datasets_to_parse:
        # Load and apply processing function for uktin data to transform to flat structure
        uktin_file = os.path.join(input_path, uktin_file)
        raw_uktin_data = load_json(uktin_file)
        uktin_data = process_uktin_names_only(raw_uktin_data)
        uktin_data = add_const_field_json(uktin_data, "dataset", "uktin")
        uk_data.extend(uktin_data)
        parsed_datasets.append("uktin")
        # Save initial UKTIN data with added dataset field
        save_json(
            uktin_data, 
            'uktin_data.json', 
            save_dir=os.path.join(script_directory, 'data/raw/')
        )
    
    if check_all_datasets_parsed(datasets_to_parse, parsed_datasets):
        # some unique ids and postcodes need to be converted from int to str for consistency
        convert_entries_to_str(uk_data, ["postcode", "unique_id"])
        print(f"Combined Cordis and GtR data has been written to {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(uk_data, output_file, indent=4)
        print(f"Filtered data for {datasets_to_parse} has been written to {output_file_path}")
        
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