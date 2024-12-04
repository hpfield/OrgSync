import os, sys
import json
import pandas as pd
from pprint import pprint
import collections
from typing import Dict, List, Set

# move to route directory of repo
os.chdir(os.path.join(os.getcwd(), 'OrgSync'))

base_path = os.path.join("data", "raw")
gtr_base = os.path.join(base_path, "all_scraped", "gtr", "scraped")
gtr_persons_json = os.path.join(gtr_base, "2024_07", "persons.json")
gtr_projects_json = os.path.join(gtr_base, "2024_07", "projects.json")
gtr_organisations_json = os.path.join(gtr_base, "2024_07", "organisations.json")

person_keys = {
    "person_id": "id",
    "first_name": "firstName",
    "last_name": "surname",
    "other_names": "otherNames",
    "email": "email",
    "orchic_id": "orchidId",
}

person_rels = ["EMPLOYED", "PI_PER", "COI_PER"]

def extract_id_from_href(href: str) -> str:
    return href.split('/')[-1]

def extract_domain_from_href(href: str) -> str:
    return href.split('/')[2]

def get_links_as_list(entry, rels):
    link_dicts = entry["links"]["link"]

    links = {} #! convert to list, not dict...
    for link_item in link_dicts:
        if link_item["rel"] in rels:
            links[link_item["rel"]] = link_item["href"]
            links["domain"] = extract_domain_from_href(link_item["href"])
        # links["href_id"] = extract_id_from_href(link_item["href"])
    return links





def transform_persons(persons_path, keys):
    """
    persons opened from json will be a list of dictionaries.
    """
    with open(persons_path, "r") as f:
        persons = json.load(f)

     

