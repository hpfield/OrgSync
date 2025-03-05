import json
import logging
from tqdm import tqdm
from pydantic import BaseModel
from stages.utils import UserMessage, SystemMessage, get_client

logger = logging.getLogger(__name__)

class RefineGroupResponse(BaseModel):
    selected_names: list[str]

def stage10_refine_groups_with_llm(formatted_groups, web_search_results, unique_entries):
    client = get_client()
    refined_results = {}
    
    # Build lookup for unique entries by lower-case combined_name
    names_lookup = {}
    for entry in unique_entries:
        key = entry["combined_name"].lower()
        item = {
            "org_name": entry["combined_name"],
            "unique_id": entry["unique_id"],
            "dataset": entry["dataset"],
            "postcode": entry["postcode"]
        }
        names_lookup.setdefault(key, []).append(item)
    
    logger.info("Refining formatted groups with LLM...")#
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    for group_id, group_info in tqdm(formatted_groups.items(), desc="Refining groups"):
        rep_name = group_info.get("name", "").lower()
        organisation_type = group_info.get("organisation_type", "")
        
        # Derive candidate names from the group's items using the canonical 'org_name' field.
        candidate_names_set = set()
        for item in group_info.get("items", []):
            if "org_name" in item:
                candidate_names_set.add(item["org_name"].lower())
        candidate_names = list(candidate_names_set)
        
        if not candidate_names:
            logger.info(f"Skipping group {rep_name} due to no candidate names found.")
            continue
        
        # Build web search results context for each candidate name.
        web_results_str = ""
        for name in candidate_names:
            results = web_search_results.get(name, [])
            if results:
                result_strs = []
                for result in results:
                    url = result.get('url', '')
                    title = result.get('title', '')
                    description = result.get('description', '')
                    result_strs.append(f"Title: {title}\nURL: {url}\nDescription: {description}")
                combined = "\n\n".join(result_strs)
                web_results_str += f"Search results for '{name}':\n{combined}\n\n"
            else:
                web_results_str += f"Search results for '{name}':\nNo results available.\n\n"
        
        prompt = f"""Given the following candidate organization names:
{', '.join(candidate_names)}

The chosen representative name is "{rep_name}".
All are determined to be a/an {organisation_type}.
Based on the web search results below, please select the names that truly belong to the same organization as "{rep_name}", 
and output them as a JSON object with a key "selected_names" that is an array of names in lowercase.
Exclude any ambiguous names. No extra text, just JSON.
Web search results:
{web_results_str}
"""
        system_message = "You are an AI assistant that refines organization groups based on provided candidate names, organisation type, and web search results. Output must be a JSON object with a key 'selected_names' containing a list of valid names in lowercase, with no additional text."
        chat_history = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        try:
            result = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=chat_history,
                response_format=RefineGroupResponse,
            )
            refined_names = result.choices[0].message.parsed.selected_names
            if not isinstance(refined_names, list):
                logger.warning(f"LLM response is not a list for group {rep_name}.")
                refined_names = []
        except Exception as e:
            logger.error(f"Error processing group {rep_name} with LLM: {e}")
            refined_names = []
        
        # Ensure the representative name is included.
        if rep_name not in refined_names:
            refined_names.append(rep_name)
        
        # Build refined items for the group from the preprocessed lookup.
        items_for_group = []
        for name in refined_names:
            normalized_name = name.lower()
            if normalized_name in names_lookup:
                items_for_group.extend(names_lookup[normalized_name])
        
        if len(items_for_group) > 1:
            refined_results[group_id] = {
                "name": group_info["name"],
                "items": items_for_group
            }
        else:
            logger.info(f"Skipping group {rep_name} due to insufficient items after LLM refinement.")
    logger.info(f"Refined groups count: {len(refined_results)}")
    return refined_results
