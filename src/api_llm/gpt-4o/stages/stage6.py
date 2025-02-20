import json
import logging
from tqdm import tqdm  # synchronous progress bar
from stages.utils import get_client
from stages.utils import GroupResponse

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

    Calls the LLM synchronously to decide which of the 'matched_names' belong to the same
    organization as the unique name. The result is stored in `refined_groups` as:
      refined_groups[unique_name] = [list_of_selected_names]
    """
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    original_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    client = get_client()  # Assumed now to support synchronous calls

    refined_groups = {}
    num_groups = len(grouped_names)

    logger.info("Processing groups with LLM synchronously...")

    pbar = tqdm(total=num_groups, desc='Processing groups with LLM')
    for unique_name, info in grouped_names.items():
        matched_names_list = info.get("matched_names", [])
        # Build a dict mapping each name in the group to its search results.
        group_names = [unique_name] + matched_names_list
        group_search_results = {
            name: web_search_results.get(name, [])
            for name in group_names
        }
        try:
            unique_name, response = process_group_with_llm(unique_name, matched_names_list, group_search_results, client)
        except Exception as e:
            logger.exception(f"Processing group '{unique_name}' raised an exception: {e}")
            continue

        pbar.update(1)

        # Parse the response (expected to be a JSON array string)
        try:
            if isinstance(response, list):
                selected_names = response
            else:
                logger.warning(f"LLM response for group '{unique_name}' is not a list. Response was: {response}")
                selected_names = []
        except json.JSONDecodeError:
            logger.error(f"Error parsing LLM response for group '{unique_name}': {response}")
            selected_names = []
        except Exception as e:
            logger.exception(f"Unexpected error processing group '{unique_name}': {e}")
            selected_names = []

        # Ensure the original unique_name is included
        if unique_name not in selected_names:
            selected_names.append(unique_name)

        refined_groups[unique_name] = selected_names

    pbar.close()

    logger.setLevel(original_level)
    logger.info(f"Refined groups to {len(refined_groups)} groups after LLM processing.")
    return refined_groups

def process_group_with_llm(unique_name, matched_names_list, group_search_results, client):
    """
    Synchronously sends a prompt to the LLM:
      - unique_name is the 'primary' name.
      - matched_names_list are possible duplicates.
      - group_search_results is a dict {org_name -> list_of_search_hits}.
      - client is the local LLM client object.

    Expects the LLM to return a JSON array (as a string) of selected names in lowercase.
    Returns a tuple (unique_name, response).
    """
    system_message = (
        "You are an AI assistant that helps identify whether organization names refer "
        "to the same UK research organization. You have access to web search results to assist. "
        "Output must be a JSON array of selected names in lowercase, no extra text."
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

    chat_history = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    # Synchronously call the API using the blocking method.
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=chat_history,
        response_format=GroupResponse, 
    )

    # Extract and return the response from the first choice.
    response = completion.choices[0].message.parsed
    return unique_name, response.selected_names
