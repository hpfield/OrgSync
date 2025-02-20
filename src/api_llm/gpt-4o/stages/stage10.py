import json
import logging
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage10_refine_groups_with_llm(formatted_groups, web_search_results, unique_entries):
    """
    Refine the groups produced in stage 9 using LLM to validate membership.
    For each group, using the representative name from stage 9 and candidate names derived from the group's items,
    re-assess the group membership via LLM and then re-validate against unique_entries.
    Returns refined groups in the final output format, reusing the same UUID as stage 9:
      { group_UUID: { "name": representative_name, "items": refined_items } }.
    """
    generator = get_generator()
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
    
    logger.info("Refining formatted groups with LLM...")
    for group_id, group_info in tqdm(formatted_groups.items(), desc="Refining groups"):
        rep_name = group_info.get("name", "").lower()
        organisation_type = group_info.get("organisation_type", "")
        
        # Derive candidate names from the group's items (using the canonical 'org_name' field)
        candidate_names_set = set()
        for item in group_info.get("items", []):
            if "org_name" in item:
                candidate_names_set.add(item["org_name"].lower())
        candidate_names = list(candidate_names_set)
        
        if not candidate_names:
            logger.info(f"Skipping group {rep_name} due to no candidate names found.")
            continue
        
        # Build web search results context for each candidate name
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
        
        # Build prompt using the candidate names and the representative name from stage 9
        prompt = f"""Given the following candidate organization names:
{', '.join(candidate_names)}

The chosen representative name is "{rep_name}".
All are determined to be a/an {organisation_type}.
Based on the web search results below, please select the names that truly belong to the same organization as "{rep_name}", 
and output them as a JSON array in lowercase. Exclude any ambiguous names. No extra text, just JSON array (e.g. ["acme corp", "acme inc"]).
Web search results:
{web_results_str}
"""
        system_message = SystemMessage(
            content="You are an AI assistant that refines organization groups based on provided candidate names, organisation type, and web search results. Output must be a JSON array of valid names in lowercase, with no additional text."
        )
        user_message = UserMessage(content=prompt)
        chat_history = [system_message, user_message]
        try:
            result = generator.chat_completion(chat_history, max_gen_len=None, temperature=0.0, top_p=0.9)
            response = result.generation.content.strip()
            refined_names = json.loads(response) if response else []
            if not isinstance(refined_names, list):
                logger.warning(f"LLM response is not a list for group {rep_name}. Response: {response}")
                refined_names = []
        except Exception as e:
            logger.error(f"Error processing group {rep_name} with LLM: {e}")
            refined_names = []
        
        # Ensure the representative name is included
        if rep_name not in refined_names:
            refined_names.append(rep_name)
        
        # Build refined items for the group from unique_entries lookup using refined names
        items_for_group = []
        for name in refined_names:
            normalized_name = name.lower()
            if normalized_name in names_lookup:
                items_for_group.extend(names_lookup[normalized_name])
        
        if len(items_for_group) > 1:
            # Reuse the same group_id from stage 9 (no new UUID is generated)
            refined_results[group_id] = {
                "name": group_info["name"],  # Keep the representative name from stage 9
                "items": items_for_group
            }
        else:
            logger.info(f"Skipping group {rep_name} due to insufficient items after LLM refinement.")
    logger.info(f"Refined groups count: {len(refined_results)}")
    return refined_results
