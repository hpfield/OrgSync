import json
import logging
import uuid
from tqdm import tqdm
from pydantic import BaseModel
from stages.utils import UserMessage, SystemMessage, get_client

logger = logging.getLogger(__name__)

class RepresentativeNameResponse(BaseModel):
    name: str

def stage9_finalize_groups(groups_with_types, web_search_results, all_names_and_items):
    client = get_client()
    final_results = {}
    logger.info("Finalizing groups to produce the formatted groups with group UUIDs...")
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)

    # Build lookup for unique entries by lower-case combined_name
    names_lookup = {}
    for entry in all_names_and_items:
        key = entry["combined_name"].lower()
        item = {
            "org_name": entry["combined_name"],
            "unique_id": entry["unique_id"],
            "dataset": entry["dataset"],
            "postcode": entry["postcode"]
        }
        names_lookup.setdefault(key, []).append(item)

    with tqdm(total=len(groups_with_types), desc='Finalizing groups') as pbar:
        for group_info in groups_with_types:
            pbar.update(1)
            organisation_type = group_info.get('organisation_type', '')
            # Derive candidate names either from provided "group_names" or from items.
            candidate_names_set = set()
            if "group_names" in group_info:
                candidate_names_set.update(name.lower() for name in group_info["group_names"])
            else:
                for item in group_info.get("items", []):
                    candidate_names_set.add(item.get("org_name", "").lower())
            candidate_names = list(candidate_names_set)
            if not candidate_names:
                continue

            representative_name = pick_representative_name_llm(candidate_names, organisation_type, web_search_results, client)

            items_for_this_group = []
            for name in candidate_names:
                normalized_name = name.lower()
                if normalized_name in names_lookup:
                    items_for_this_group.extend(names_lookup[normalized_name])
            if len(items_for_this_group) > 1:
                group_uuid = str(uuid.uuid4())
                final_results[group_uuid] = {
                    "name": representative_name,
                    "items": items_for_this_group,
                    "organisation_type": organisation_type
                }
            else:
                logger.info(
                    f"Skipping group '{representative_name}' due to insufficient items (found {len(items_for_this_group)})."
                )
    logger.info(f"Produced formatted groups with {len(final_results)} groups.")
    return final_results

def pick_representative_name_llm(candidate_names, organisation_type, web_search_results, client):
    system_message = "You are an AI assistant that chooses the best representative name for a group " \
        "of organisation names, given their organisation type and any web search results. " \
        "Output must be a JSON object with a single key 'name' containing the chosen representative name in lowercase."
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
            combined = '\n\n'.join(result_strs)
            web_results_str += f"Search results for '{name}':\n{combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results currently available.\n\n"

    prompt = f"""
Given these organisation names:
{', '.join(candidate_names)}

All are determined to be a/an {organisation_type}.
Based on the web results below, pick the single best 'representative name' in lowercase.
Output the result as JSON in the format: {{"name": "chosen name"}}.
Web search results:
{web_results_str}
"""
    chat_history = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=chat_history,
        response_format=RepresentativeNameResponse,
    )
    best_name = completion.choices[0].message.parsed.name
    if not best_name:
        best_name = candidate_names[0].lower()
    return best_name
