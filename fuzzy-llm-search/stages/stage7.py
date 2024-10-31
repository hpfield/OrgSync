import json
import logging
from tqdm import tqdm

from stages.utils import get_generator, UserMessage, SystemMessage, perform_web_search

# Initialize logger
logger = logging.getLogger(__name__)

def stage7_process_unsure_groups_with_llm(unsure_groups, final_groups, search_method):
    generator = get_generator()
    logger.info(f"Processing unsure groups with LLM using {search_method} search...")
    
    with tqdm(total=len(unsure_groups), desc=f'Processing unsure groups with LLM using {search_method} search') as pbar:
        for group in unsure_groups:
            pbar.update(1)
            group_names = group['group_names']
            web_search_results = perform_web_search(group_names, search_method=search_method)
            response = process_unsure_group_with_llm(group_names, web_search_results, generator)
            
            try:
                result = json.loads(response)
                selected_names = result.get('selected_names', [])
                representative_name = result.get('representative_name', '')
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for unsure group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                selected_names = []
                representative_name = ''
            except Exception as e:
                msg = f"Unexpected error processing unsure group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                selected_names = []
                representative_name = ''
            
            if isinstance(selected_names, list):
                selected_names = [str(name) for name in selected_names if isinstance(name, str)]
            else:
                msg = f"Expected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}"
                tqdm.write(msg)
                logger.warning(msg)
                selected_names = []
                
            final_groups.append({
                'selected_names': selected_names,
                'representative_name': representative_name
            })
    pbar.close()
    
    logger.info(f"Total number of final groups after processing unsure groups: {len(final_groups)}")
    return final_groups

def process_unsure_group_with_llm(group_names, web_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps refine groups of organization names to identify those that refer to the same organization. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")
    web_results_str = ""
    for name in group_names:
        results = web_search_results.get(name, [])
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

    Please select the names that belong to the same organization, and output them as a JSON object with two keys:
    "selected_names": an array of the names that belong to the same organization,
    "representative_name": the name that best represents that organization.

    Ensure the output is only the JSON object, with no additional text. All names should be lowercase.

    Example:

    Given the following group of organization names:
    acme corporation, acme corp, acme inc., acme co., ace corp

    And the following web search results:
    Search results for 'acme corporation':
    Title: Acme Corporation - Official Site
    URL: http://www.acmecorp.com
    Description: Welcome to Acme Corporation, the leading provider of...

    Title: Acme Corporation - Wikipedia
    URL: http://en.wikipedia.org/wiki/Acme_Corporation
    Description: Acme Corporation is a fictional company featured in...

    Search results for 'Ace Corp':
    Title: Ace Corp - Home
    URL: http://www.acecorp.com
    Description: Ace Corp specializes in...

    Your output should be:

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
