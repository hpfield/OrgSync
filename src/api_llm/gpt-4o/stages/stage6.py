import json
import logging
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_client, get_generator

logger = logging.getLogger(__name__)

def stage6_process_groups_with_llm(grouped_names, web_search_results):
    """
    Receives `grouped_names` in the format:
    {
      "<representative_name>": {
        "matched_names": [...],
        "items": [...]
      },
      ...
    }
    along with a web_search_results dict mapping each name -> list of search hits.

    We call the LLM to decide which of the 'matched_names' actually belong to the same
    organization as 'unique_name'. We store the result in `refined_groups` as:
      refined_groups[unique_name] = [list_of_selected_names]
    """
    
    client = get_client()

    # client = get_generator()
    refined_groups = {}
    num_groups = len(grouped_names)

    logger.info("Processing groups with LLM...")

    with tqdm(total=num_groups, desc='Processing groups with LLM') as pbar:
        for unique_name, info in grouped_names.items():
            pbar.update(1)
            # info is a dict with at least "matched_names" and "items"
            matched_names_list = info.get("matched_names", [])

            # Combine unique_name and matched_names into a single list for the LLM check
            group_names = [unique_name] + matched_names_list

            # Gather search results for each name in this group
            group_search_results = {
                name: web_search_results.get(name, [])
                for name in group_names
            }

            # Call our helper that prompts the LLM
            response = process_group_with_llm(
                unique_name,
                matched_names_list,
                group_search_results,
                client
            )

            # Attempt to parse the JSON response
            try:
                parsed_response = json.loads(response)
                if isinstance(parsed_response, list):
                    selected_names = parsed_response
                else:
                    logger.warning(
                        f"LLM response for group '{unique_name}' is not a list. "
                        f"Response was: {response}"
                    )
                    selected_names = []
            except json.JSONDecodeError:
                logger.error(
                    f"Error parsing LLM response for group '{unique_name}': {response}"
                )
                selected_names = []
            except Exception as e:
                logger.exception(
                    f"Unexpected error processing group '{unique_name}': {e}"
                )
                selected_names = []

            # Ensure the original unique_name is present
            if unique_name not in selected_names:
                selected_names.append(unique_name)

            # Save the refined list of names for this group
            refined_groups[unique_name] = selected_names

    logger.info(f"Refined groups to {len(refined_groups)} groups after LLM processing.")
    return refined_groups

def process_group_with_llm(unique_name, matched_names_list, group_search_results, client):
    """
    Sends a prompt to the LLM:
      - unique_name is the 'primary' name
      - matched_names_list are possible duplicates
      - group_search_results is a dict {org_name -> list_of_search_hits}
      - client is the local LLM client object

    We expect the LLM to return a JSON array of chosen names (in lowercase).
    """
    system_message = SystemMessage(
        content=(
            "You are an AI assistant that helps identify whether organization names refer "
            "to the same UK research organization. You have access to web search results to assist. "
            "Output must be a JSON array of selected names in lowercase, no extra text."
        )
    )

    # Build a text block summarizing all search results
    web_results_str = ""
    all_names = [unique_name] + matched_names_list
    for name in all_names:
        results = group_search_results.get(name, [])
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

    matched_names_str = '\n'.join(matched_names_list)
    prompt = f"""Given the organization name: "{unique_name}"
and the following list of similar names:
{matched_names_str}

Here are web search results for each name:
{web_results_str}

Please select the names that belong to the same organization as "{unique_name}", 
and output them as a JSON array in lowercase. If ambiguous, exclude the name.
No extra text, just JSON array (e.g. ["acme corp", "acme inc"])."""

    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=chat_history
    )

    return completion.choices[0].message

    # result = client.chat_completion(chat_history, max_gen_len=None, temperature=0.0, top_p=0.9)
    # return result.generation.content.strip()
    
