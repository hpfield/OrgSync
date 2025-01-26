import json
import logging
import uuid
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage9_finalize_groups(groups_with_types, web_search_results, identical_name_groups):
    """
    Produce the final output as:
    {
      "{group_UUID}": {
        "name": "{organisation_name_of_group}",
        "items": [
          {"org_name": "...", "unique_id": "...", "dataset": "...", "postcode": "..."},
          ...
        ]
      },
      ...
    }

    The "name" (organisation_name_of_group) can come from an LLM prompt (representative_name)
    or simply from the group itself.
    We'll also ensure that if a 'perfect match' group from identical_name_groups was never
    merged with other names, it still appears here in a distinct group.
    """
    generator = get_generator()
    final_results = {}
    logger.info("Finalizing groups to produce the final JSON with group UUIDs...")

    # Stage 9 re-check: we can refine each group further if needed
    with tqdm(total=len(groups_with_types), desc='Finalizing groups') as pbar:
        for group_info in groups_with_types:
            pbar.update(1)
            group_names = group_info['group_names']
            organisation_type = group_info.get('organisation_type', '')
            
            # We can optionally call LLM to pick a best "representative_name"
            # or just pick the first of group_names or something. We'll do a short prompt:
            representative_name = pick_representative_name_llm(group_names, organisation_type, web_search_results, generator)

            # Now build the final items array
            # For each name in group_names, gather all possible identical entries from Stage 2
            # (some might appear multiple times if they have identical combined_name but different fields).
            items_for_this_group = []
            for name in group_names:
                # If that 'name' exists in identical_name_groups, gather all entries
                if name in identical_name_groups:
                    for entry in identical_name_groups[name]:
                        items_for_this_group.append({
                            "org_name": entry["combined_name"],
                            "unique_id": entry["unique_id"],
                            "dataset": entry["dataset"],
                            "postcode": entry["postcode"]
                        })
                else:
                    # It's possible the name is not in identical_name_groups
                    # (e.g. it was unique from the start)
                    items_for_this_group.append({
                        "org_name": name,
                        "unique_id": "",
                        "dataset": "",
                        "postcode": ""
                    })

            # Create a unique UUID for this group
            group_uuid = str(uuid.uuid4())

            final_results[group_uuid] = {
                "name": representative_name,
                "items": items_for_this_group
            }

    logger.info(f"Produced final results with {len(final_results)} groups.")
    return final_results

def pick_representative_name_llm(group_names, organisation_type, web_search_results, generator):
    """
    Example function to let the LLM choose a final 'best' organization name
    from the group. You could also do a simpler approach (like group_names[0])
    if you prefer. 
    """
    system_message = SystemMessage(content=(
        "You are an AI assistant that chooses the best representative name for a group "
        "of organisation names, given their organisation type and any web search results."
    ))

    # Build a small string of results
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

Only output the name (string) itself, no additional formatting.
"""

    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]
    result = generator.chat_completion(
        chat_history, max_gen_len=None, temperature=0.0, top_p=0.9
    )

    best_name = result.generation.content.strip()
    # If the LLM outputs JSON or extra text, you might parse/clean it. For now, assume it's just a string.
    if not best_name:
        # Fallback to the first name
        best_name = group_names[0].lower()

    return best_name
