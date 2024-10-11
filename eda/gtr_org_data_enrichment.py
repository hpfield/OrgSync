import httpx 
import pandas as pd
from typing import List, Dict, Any
import asyncio
import os
import json


BASE_URL = "https://gtr.ukri.org/gtr/api"
HEADERS = {
    "Accept": "application/vnd.rcuk.gtr.json-v7"
}

def split_link(link):
    """
    Split link of form `http://gtr.ukri.org/gtr/api/<domain>/<id>` into domain and id.
    """
    base = "https://gtr.ukri.org/gtr/api"
    tail = link[len(base):]
    print(tail)
    domain, identifier = tail.split("/")
    print(domain, identifier)
    return domain, identifier

def create_async_client():
    client = httpx.AsyncClient(
        headers=HEADERS,
        base_url=BASE_URL,
        follow_redirects=True,
        timeout=20
    )   
    return client

async def fetch_data(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    """Fetch data from the GtR API."""
    response = await client.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

async def get_organization_details(client: httpx.AsyncClient, org_id: str) -> Dict[str, Any]:
    """Fetch detailed information about an organization."""
    url = f"{BASE_URL}/organisations/{org_id}"
    return await fetch_data(client, url)

async def get_project_details(client: httpx.AsyncClient, project_id: str) -> Dict[str, Any]:
    """Fetch detailed information about a project."""
    url = f"{BASE_URL}/projects/{project_id}"
    return await fetch_data(client, url)

async def get_person_details(client: httpx.AsyncClient, person_id: str) -> Dict[str, Any]:
    """Fetch detailed information about a person."""
    url = f"{BASE_URL}/persons/{person_id}"
    return await fetch_data(client, url)

async def enrich_organization_data(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich the organization data with additional information from the GtR API."""
    async with httpx.AsyncClient() as client:
        enriched_data = []
        for _, row in df.iterrows():
            org_id = row['id']
            org_details = await get_organization_details(client, org_id)
            
            # Fetch associated projects
            projects = []
            for link in org_details.get('links', []):
                if link['rel'] == 'PROJECT':
                    project_id = link['href'].split('/')[-1]
                    project_details = await get_project_details(client, project_id)
                    projects.append(project_details)
            
            # Fetch employee details
            employees = []
            for link in org_details.get('links', []):
                if link['rel'] == 'EMPLOYEE':
                    person_id = link['href'].split('/')[-1]
                    person_details = await get_person_details(client, person_id)
                    employees.append(person_details)
            
            enriched_data.append({
                'org_id': org_id,
                'org_name': org_details.get('name'),
                'org_address': org_details.get('address', {}).get('postCode'),
                'projects': projects,
                'employees': employees
            })
        
    return pd.DataFrame(enriched_data)

# Main function to run the enrichment process
async def main():
    # open processed gtr organisation data with links
    data = os.path.join("data", "processed", "gtr_links_expanded.csv")
    df = pd.read_csv(data)
    
    enriched_df = await enrich_organization_data(df)
    
    # Save the enriched DataFrame
    enriched_df.to_csv('enriched_organization_data.csv', index=False)
    print("Data enrichment completed. Results saved to 'enriched_organization_data.csv'")

if __name__ == "__main__":
    asyncio.run(main())