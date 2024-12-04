import os, sys
import json
import pandas as pd
from pprint import pprint
import collections
from typing import Dict, List, Set


def extract_id_from_href(href: str) -> str:
    return href.split('/')[-1]


def preprocess_data(persons_data: List[Dict], organisation_data: List[Dict]) -> Dict:
    # Create dictionaries for fast lookup
    persons = {p['id']: p for p in persons_data}
    organisations = {o['id']: o for o in organisation_data}

    # Create reverse mappings
    org_employees: Dict[str, Set[str]] = collections.defaultdict(set)
    org_pis: Dict[str, Set[str]] = collections.defaultdict(set)
    person_orgs: Dict[str, Set[str]] = collections.defaultdict(set)
    person_pi_projects: Dict[str, Set[str]] = collections.defaultdict(set)

    for person_id, person in persons.items():
        for link in person['links'].get('link', []):
            if link['rel'] == 'EMPLOYED':
                org_id = extract_id_from_href(link['href'])
                org_employees[org_id].add(person_id)
                person_orgs[person_id].add(org_id)
            elif link['rel'] == 'PI_PER':
                project_id = extract_id_from_href(link['href'])
                person_pi_projects[person_id].add(project_id)
                # We don't have direct project-to-org mapping, so we'll associate
                # the project with all orgs the person is employed by
                for org_id in person_orgs[person_id]:
                    org_pis[org_id].add(person_id)

    return {
        'persons': persons,
        'organisations': organisations,
        'org_employees': org_employees,
        'org_pis': org_pis,
        'person_orgs': person_orgs,
        'person_pi_projects': person_pi_projects
    }


def analyze_org_overlaps(data: Dict) -> Dict:
    org_pairs = collections.defaultdict(lambda: {'employee_overlap': set(), 'pi_overlap': set()})

    for org_id, employees in data['org_employees'].items():
        for other_org_id, other_employees in data['org_employees'].items():
            if org_id != other_org_id:
                pair = tuple(sorted([org_id, other_org_id]))
                org_pairs[pair]['employee_overlap'].update(employees & other_employees)

    for org_id, pis in data['org_pis'].items():
        for other_org_id, other_pis in data['org_pis'].items():
            if org_id != other_org_id:
                pair = tuple(sorted([org_id, other_org_id]))
                org_pairs[pair]['pi_overlap'].update(pis & other_pis)

    return org_pairs
