import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage8_finalize_groups(groups_with_types, web_search_results):
    generator = get_generator()
    final_groups = []
    logger.info("Finalizing groups based on organisation types...")

    with tqdm(total=len(groups_with_types), desc='Finalizing groups') as pbar:
        for group in groups_with_types:
            pbar.update(1)
            group_names = group['group_names']
            organisation_type = group['organisation_type']
            # Retrieve web search results for each name in the group
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = finalize_group_with_llm(group_names, organisation_type, group_search_results, generator)
            try:
                result = json.loads(response)
                selected_names = result.get('selected_names', [])
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                selected_names = []
            except Exception as e:
                msg = f"Unexpected error processing group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                selected_names = []

            final_groups.append({
                'selected_names': selected_names,
                'organisation_type': organisation_type
            })

    logger.info(f"Completed finalizing {len(final_groups)} groups.")
    return final_groups

def finalize_group_with_llm(group_names, organisation_type, group_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps refine groups of organization names to identify those that refer to the same organization of a specific type. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")

    web_results_str = ""
    for name in group_names:
        results = group_search_results.get(name, [])
        if results:
            result_strs = []
            for result in results:
                url = result.get('url', '')
                title = result.get('title', '')
                description = result.get('description', '')
                result_str = f"Title: {title}\nURL: {url}\nDescription: {description}"
                result_strs.append(result_str)
            results_combined = '\n\n'.join(result_strs)
            web_results_str += f"Search results for '{name}':\n{results_combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results found.\n\n"

    prompt = f"""Given the following group of organization names:
{', '.join(group_names)}

And the following web search results:
{web_results_str}

Please select the names that belong to the same {organisation_type}, and output them as a JSON object with one key:
"selected_names": an array of the names that belong to the same {organisation_type}.
"representative_name": the name that best represents that {organisation_type}.


Ensure the output is only the JSON object, with no additional text. All names should be lowercase.

Example:

{{
"selected_names": ["acme corporation", "acme corp", "acme inc.", "acme co."],
"representative_name": "acme corporation"
}}

Remember, only output the JSON object.
"""

    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]

    result = generator.chat_completion(
        chat_history,
        max_gen_len=None,
        temperature=0.0,
        top_p=0.9,
    )

    out_message = result.generation
    response = out_message.content.strip()

    return response
