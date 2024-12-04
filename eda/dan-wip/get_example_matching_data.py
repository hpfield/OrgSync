import os, sys
import json
import pandas as pd
from pprint import pprint

# cd to repo base
# print wd
print(os.getcwd())

print(os.getcwd())


base_path = os.path.join("data", "raw")
gtr_base = os.path.join(base_path, "all_scraped", "gtr", "scraped")
gtr_persons_json = os.path.join(gtr_base, "2024_07", "persons.json")
gtr_projects_json = os.path.join(gtr_base, "2024_07", "projects.json")
gtr_organisations_json = os.path.join(gtr_base, "2024_07", "organisations.json")


with open(gtr_projects_json, "r") as f:
    projects_data = json.load(f)

pprint(projects_data[0])


with open(gtr_organisations_json, "r") as f:
    organisations_data = json.load(f)

pprint(projects_data[0])


with open(gtr_persons_json, "r") as f:
    persons_data = json.load(f)

pprint(persons_data[0])


# save first 100 entries of each data set to .json

example_data_path = os.path.join(base_path, "example_data")
os.makedirs(example_data_path, exist_ok=True)

with open(os.path.join(base_path, "example_data", "persons.json"), "w") as f:
    json.dump(persons_data[:100], f)

with open(os.path.join(base_path, "example_data", "projects.json"), "w") as f:
    json.dump(projects_data[:100], f)

with open(os.path.join(base_path, "example_data", "organisations.json"), "w") as f:
    json.dump(organisations_data[:100], f)

