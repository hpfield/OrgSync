import json
import os
import yaml
import hydra
from omegaconf import DictConfig
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

def check_all_datasets_parsed(datasets_to_parse, parsed_datasets):
    return all(dataset in parsed_datasets for dataset in datasets_to_parse)

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig):
    # Determine the directory where this script is located
    # script_directory = os.getcwd()
    script_directory = os.path.dirname(os.path.abspath(__file__)) 
    print(f"Running setup.py from {script_directory}")
    # load paths from config, modify in conf/config.yaml if needed
    input_path = os.path.join(script_directory, cfg.paths.input_path)
    output_file_path = os.path.join(script_directory, cfg.paths.output_file)
    cordis_files = cfg.paths.cordis_files
    gtr_file = os.path.join(input_path, cfg.paths.gtr_file)
    uktin_file = os.path.join(input_path, cfg.paths.uktin_file)
    
    # default datasets are "cordis" and "gtr". Modify in config.yaml or override to include "uktin"
    datasets_to_parse = cfg.datasets
    uk_data = []
    parsed_datasets = []

    if "cordis" in datasets_to_parse:
        # Iterate over the three cordis datasets to filter and append data to uk_data
        cordis_uk_data = []
        for file_path in cordis_files:
            full_path = os.path.join(input_path, file_path)
            data = load_json(full_path)
            # Filter the data where country is "UK". Unlike GtR, Cordis has non-UK entries
            uk_entries = [entry for entry in data if entry.get("country") == "UK"]
            cordis_uk_data.extend(uk_entries)
        cordis_uk_data = add_const_field_json(cordis_uk_data, "dataset", "cordis")
        # Save initial Cordis data with added dataset field
        save_json(cordis_uk_data, 'cordis_data.json', save_dir=os.path.dirname(output_file_path))
        # Remove fields not needed in final output, map names to standard format
        cordis_data = remove_fields(cordis_uk_data, cfg.fields.cordis_fields_to_keep)
        cordis_data = map_names_json(cordis_data, cfg.fields.map_names_cordis)
        uk_data.extend(cordis_data)
        parsed_datasets.append("cordis")

    if "gtr" in datasets_to_parse:
        # Load gtr dataset, apply processing functions from utils to transform to flat structure 
        raw_gtr_data = load_json(gtr_file)
        processed_gtr = process_gtr_data(raw_gtr_data)
        gtr_data = add_const_field_json(processed_gtr, "dataset", "gtr")
        # Save initial GtR data with added dataset field
        save_json(processed_gtr, 'gtr_data.json', save_dir=os.path.dirname(output_file_path))
        # Remove fields not needed in final output, map names to standard format
        gtr_data = remove_fields(gtr_data, cfg.fields.gtr_fields_to_keep)
        gtr_data = map_names_json(gtr_data, cfg.fields.map_names_gtr)
        uk_data.extend(gtr_data)
        parsed_datasets.append("gtr")

    if "uktin" in datasets_to_parse:
        # Load uktin dataset, apply processing functions from utils to transform to flat structure 
        raw_uktin_data = load_json(uktin_file)
        uktin_data = process_uktin_names_only(raw_uktin_data)
        uktin_data = add_const_field_json(uktin_data, "dataset", "uktin")
        # Save initial UKTIN data with added dataset field
        save_json(uktin_data, 'uktin_data.json', save_dir=os.path.dirname(output_file_path))
        uk_data.extend(uktin_data)
        parsed_datasets.append("uktin")
    
    if check_all_datasets_parsed(datasets_to_parse, parsed_datasets):
        # some unique ids and postcodes need to be converted from int to str for consistency
        convert_entries_to_str(uk_data, ["postcode", "unique_id"])
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(uk_data, output_file, indent=4)
        print(f"Filtered data for {datasets_to_parse} has been written to {output_file_path}")

if __name__ == "__main__":
    main()
    # for compatability with old configs in cfg\config.yaml, remove this block if not needed
    script_directory = os.path.dirname(os.path.abspath(__file__)) 
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