import json
import logging
import uuid
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_client

logger = logging.getLogger(__name__)

def stage9_finalize_groups(groups_with_types, web_search_results, all_names_and_items):
    """
    Produce the formatted groups as a dict of:
      { group_UUID: { "name": <chosen representative name>,
                      "items": [...],
                      "organisation_type": <type> }, ... }
    For each group, only include items found in the preprocessed database.
    Groups with one or no items after removal are skipped.
    Note: The redundant storage of group names is removed.
    """
    client = get_client()
    final_results = {}
    logger.info("Finalizing groups to produce the formatted groups with group UUIDs...")

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
            # Use candidate names from the group's original info.
            # Previously, group_info contained "group_names" but to avoid duplication we derive candidate names
            # from the items in the preprocessed database.
            organisation_type = group_info.get('organisation_type', '')
            
            # Derive candidate names from unique items associated with this group
            candidate_names_set = set()
            # If group_info has a "group_names" field, we could use it; otherwise, derive from items.
            if "group_names" in group_info:
                candidate_names_set.update(name.lower() for name in group_info["group_names"])
            else:
                for item in group_info.get("items", []):
                    candidate_names_set.add(item.get("org_name", "").lower())
            candidate_names = list(candidate_names_set)
            if not candidate_names:
                continue

            # Use the candidate names to choose a representative name via LLM
            representative_name = pick_representative_name_llm(candidate_names, organisation_type, web_search_results, client)

            # Build the items for this group by looking up from our preprocessed database.
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
    system_message = SystemMessage(content=(
        "You are an AI assistant that chooses the best representative name for a group "
        "of organisation names, given their organisation type and any web search results."
    ))
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
Based on the web results below, pick the single best 'representative name' in lowercase:
{web_results_str}

Only output the name itself, with no additional formatting.
"""
    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=chat_history
    )

    best_name = completion.choices[0].message
    if not best_name:
        best_name = candidate_names[0].lower()
    return best_name
    # result = client.chat_completion(
    #     chat_history, max_gen_len=None, temperature=0.0, top_p=0.9
    # )
    # best_name = result.generation.content.strip()
    # if not best_name:
    #     best_name = candidate_names[0].lower()
    # return best_name
