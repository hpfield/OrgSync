import os, sys
import json
import pandas as pd
from pprint import pprint
import collections
from typing import Dict, List, Set

def get_data(file_path: str) -> Dict:
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def extract_id_from_href(href: str) -> str:
    return href.split('/')[-1]

def extract_domain_from_href(href: str) -> str:
    return href.split('/')[-2]

def get_hrefs_as_dict_of_lists(entry, rels):
    link_dicts = entry["links"]["link"]
    # populate with {rel: [list]}
    rel_lists = {rel: [] for rel in rels}
    for link_item in link_dicts:        
        if link_item["rel"] in rels:
            rel_lists[link_item["rel"]].append(link_item["href"])
            rel_lists[link_item["rel"]+"_ids"] = [extract_id_from_href(href) for href in rel_lists[link_item["rel"]]]
    return rel_lists

def transform_data(data: List[Dict], keys: Dict, rels: List)  -> List[Dict]:
    transformed = []
    for entry in data:
        data_transformed = {}
        for key, value in keys.items():
            data_transformed[key] = entry[value]
            href_dict = get_hrefs_as_dict_of_lists(entry, rels)
            # merge the transformed person with the hrefs
            data_transformed = {**data_transformed, **href_dict}
        transformed.append(data_transformed)
    return transformed


if __name__ == "__main__":
    base_path = os.path.join("data", "raw")
    gtr_base = os.path.join(base_path, "all_scraped", "gtr", "scraped")
    gtr_persons_json = os.path.join(gtr_base, "2024_07", "persons.json")
    gtr_projects_json = os.path.join(gtr_base, "2024_07", "projects.json")
    gtr_organisations_json = os.path.join(gtr_base, "2024_07", "organisations.json")

    person_keys = {
    "person_id": "id",
    "firstName": "firstName",
    "surname": "surname",
    "otherNames": "otherNames",
    "email": "email",
    "orcidId": "orcidId",
    "created": "created",
}

    # rels is a list of the `rel` fields in the nested list of dictionaries in the json file
    # Each returns an href to another json file that contins information about projects, organisations etc. 
    person_rels = ["EMPLOYED", "PI_PER", "COI_PER"]

    persons = get_data(gtr_persons_json)
    persons_transformed = transform_data(persons, person_keys, person_rels)
    # pprint(persons_transformed)
    # create folder if doesn't exist
    os.makedirs("data/transformed", exist_ok=True)
    # save persons transformed and organisations transformed to csv
    persons_df = pd.DataFrame(persons_transformed)
    persons_df.to_csv("data/transformed/persons.csv", index=False)

    organisation_keys = {
    "name": "name",
    "organisation_id": "id",
    "website": "website",
    "created": "created"
    # ignore postcode/ location for now.
    # ad "created" back in at some point could be helpful, same with projects and persons.
    }

    organisation_rels = ["EMPLOYEE", "PROJECT"]

    organisations = get_data(gtr_organisations_json)
    organisations_transformed = transform_data(organisations, organisation_keys, organisation_rels)
    # pprint(organisations_transformed)


    organisations_df = pd.DataFrame(organisations_transformed)
    organisations_df.to_csv("data/transformed/organisations.csv", index=False)

    ## ADD PROJECT TRANSFORM HERE ##