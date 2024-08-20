"""
Establish the project root filepath, wrangle the raw data files and setup any other initial params
"""

import json
import os
import yaml

# Determine the directory where this script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the base path and the file paths to combine
input_path = os.path.join(script_directory, "data/raw/all_scraped/")
file_paths = [
    "cordis/2024_07/FP7/organization.json",
    "cordis/2024_07/Horizon 2020/organization.json",
    "cordis/2024_07/Horizon Europe/organization.json",
    "gtr/scraped/2024_07/organisations.json"
]

# Initialize an empty list to store combined data
combined_data = []

# Iterate over the file paths, read and append data to combined_data
for file_path in file_paths:
    full_path = os.path.join(input_path, file_path)
    with open(full_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        combined_data.extend(data)

# Specify the output file path
output_file_path = os.path.join(script_directory, "data", "raw", "combined_organizations.json")

# Write the combined data to the output file
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(combined_data, output_file, indent=4)

print(f"Combined data has been written to {output_file_path}")

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

