import json
import logging
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage8_determine_organisation_type(merged_groups, web_search_results):
    generator = get_generator()
    groups_with_types = []
    logger.info("Determining organisation types for groups...")

    with tqdm(total=len(merged_groups), desc='Determining org types') as pbar:
        for group_names in merged_groups:
            pbar.update(1)
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = determine_organisation_type_with_llm(group_names, group_search_results, generator)
            try:
                result = json.loads(response)
                organisation_type = result.get('organisation_type', '')
            except json.JSONDecodeError:
                logger.error(f"Error parsing LLM response. Response was: {response}")
                organisation_type = ''
            except Exception as e:
                logger.exception(f"Unexpected error processing group: {e}")
                organisation_type = ''

            groups_with_types.append({
                'group_names': group_names,
                'organisation_type': organisation_type
            })

    logger.info(f"Completed organisation type detection for {len(groups_with_types)} groups.")
    return groups_with_types

def determine_organisation_type_with_llm(group_names, group_search_results, generator):
    system_message = SystemMessage(
        content=(
            "You are an AI assistant that helps identify the type of organisation "
            "these group names refer to. Output must be JSON with a single key 'organisation_type'."
        )
    )

    web_results_str = ""
    for name in group_names:
        results = group_search_results.get(name, [])
        if results:
            entries = []
            for res in results:
                url = res.get('url', '')
                title = res.get('title', '')
                desc = res.get('description', '')
                entries.append(f"Title: {title}\nURL: {url}\nDescription: {desc}")
            combined = "\n\n".join(entries)
            web_results_str += f"Search results for '{name}':\n{combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results found.\n\n"

    prompt = f"""
Given this group of organisation names:
{', '.join(group_names)}

And the following web search results:
{web_results_str}

Classify the type of organisation (e.g. 'company', 'university', 'government', 'non-profit', etc.).
Output JSON of the form:

{{"organisation_type": "some type"}}
"""

    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]

    result = generator.chat_completion(chat_history, max_gen_len=None, temperature=0.0, top_p=0.9)
    return result.generation.content.strip()
