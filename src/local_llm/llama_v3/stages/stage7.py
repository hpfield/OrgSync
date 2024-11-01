import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage7_determine_organisation_type(merged_groups, web_search_results):
    generator = get_generator()
    groups_with_types = []
    logger.info("Determining organisation types for groups...")

    with tqdm(total=len(merged_groups), desc='Determining organisation types') as pbar:
        for group_names in merged_groups:
            pbar.update(1)
            # Retrieve web search results for each name in the group
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = determine_organisation_type_with_llm(group_names, group_search_results, generator)
            try:
                result = json.loads(response)
                organisation_type = result.get('organisation_type', '')
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                organisation_type = ''
            except Exception as e:
                msg = f"Unexpected error processing group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                organisation_type = ''
            
            groups_with_types.append({
                'group_names': group_names,
                'organisation_type': organisation_type
            })

    logger.info(f"Completed determining organisation types for {len(groups_with_types)} groups.")
    return groups_with_types

def determine_organisation_type_with_llm(group_names, group_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps identify the type of organisation that a group of names refer to. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")

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

Please determine the type of organization these names refer to. Examples of organization types include, but are not limited to: 'company', 'university', 'government organization', 'non-profit', 'research institute', etc.

Output your answer as a JSON object with one key:
"organisation_type": the type of organization these names refer to.

Ensure the output is only the JSON object, with no additional text.

Example:

{{
"organisation_type": "university"
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
