import json
import logging
import uuid
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage9_finalize_groups(groups_with_types, web_search_results, identical_name_groups):
    """
    Produce the final output as a dict of:
      { group_UUID: { "name": <chosen representative name>, "items": [...] }, ... }
    
    Then we also merge with `output_groups.json` if it exists (the rolling final output).
    """

    generator = get_generator()
    final_results = {}
    logger.info("Finalizing groups to produce the final JSON with group UUIDs...")

    # We'll do a short pass to handle each group
    with tqdm(total=len(groups_with_types), desc='Finalizing groups') as pbar:
        for group_info in groups_with_types:
            pbar.update(1)
            group_names = group_info['group_names']
            organisation_type = group_info.get('organisation_type', '')

            representative_name = pick_representative_name_llm(
                group_names, organisation_type, web_search_results, generator
            )

            # Build the items for this group
            # We'll gather from identical_name_groups if possible
            items_for_this_group = []
            for name in group_names:
                if name in identical_name_groups:
                    # If name is a "key" from stage2, that means
                    # each entry in identical_name_groups[name] has the full original data
                    for entry in identical_name_groups[name]:
                        items_for_this_group.append({
                            "org_name": entry["combined_name"],
                            "unique_id": entry["unique_id"],
                            "dataset": entry["dataset"],
                            "postcode": entry["postcode"]
                        })
                else:
                    # It's possible the name was unique, so we only have that string
                    items_for_this_group.append({
                        "org_name": name,
                        "unique_id": "",
                        "dataset": "",
                        "postcode": ""
                    })

            group_uuid = str(uuid.uuid4())
            final_results[group_uuid] = {
                "name": representative_name,
                "items": items_for_this_group
            }

    logger.info(f"Produced final results with {len(final_results)} groups.")
    return final_results

def pick_representative_name_llm(group_names, organisation_type, web_search_results, generator):
    system_message = SystemMessage(content=(
        "You are an AI assistant that chooses the best representative name for a group "
        "of organisation names, given their organisation type and any web search results."
    ))

    web_results_str = ""
    for name in group_names:
        results = web_search_results.get(name, [])
        if results:
            descs = []
            for r in results:
                title = r.get("title", "")
                desc = r.get("description", "")
                descs.append(f"Title: {title}\nDescription: {desc}")
            joined = "\n\n".join(descs)
            web_results_str += f"Name: {name}\n{joined}\n\n"

    prompt = f"""
Given these organisation names:
{', '.join(group_names)}

All are determined to be a/an {organisation_type}.
Based on the web results below, pick the single best 'representative name' in lowercase:
{web_results_str}

Only output the name itself, with no additional formatting.
"""

    from stages.utils import UserMessage
    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]
    result = generator.chat_completion(
        chat_history, max_gen_len=None, temperature=0.0, top_p=0.9
    )

    best_name = result.generation.content.strip()
    if not best_name:
        best_name = group_names[0].lower()
    return best_name
