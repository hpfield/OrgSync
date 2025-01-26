import json
import logging
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage6_process_groups_with_llm(grouped_names, web_search_results):
    generator = get_generator()
    refined_groups = {}
    num_groups = len(grouped_names)
    logger.info("Processing groups with LLM...")

    with tqdm(total=num_groups, desc='Processing groups with LLM') as pbar:
        for unique_name, matched_names in grouped_names.items():
            pbar.update(1)
            group_names = [unique_name] + matched_names
            # Gather search results for each name
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = process_group_with_llm(unique_name, matched_names, group_search_results, generator)

            try:
                parsed_response = json.loads(response)
                if isinstance(parsed_response, list):
                    selected_names = parsed_response
                else:
                    logger.warning(f"LLM response is not a list, skipping. Response: {response}")
                    selected_names = []
            except json.JSONDecodeError:
                logger.error(f"Error parsing LLM response for group '{unique_name}': {response}")
                selected_names = []
            except Exception as e:
                logger.exception(f"Unexpected error processing group '{unique_name}': {e}")
                selected_names = []

            # Ensure the original unique_name is present
            if unique_name not in selected_names:
                selected_names.append(unique_name)
            refined_groups[unique_name] = selected_names
            
    logger.info(f"Refined groups to {len(refined_groups)} groups after LLM processing.")
    return refined_groups

def process_group_with_llm(unique_name, matched_names, group_search_results, generator):
    system_message = SystemMessage(
        content=(
            "You are an AI assistant that helps identify whether organization names refer "
            "to the same UK research organization. You have access to web search results to assist. "
            "Output must be a JSON array of selected names in lowercase, no extra text."
        )
    )

    web_results_str = ""
    all_names = [unique_name] + matched_names
    for name in all_names:
        results = group_search_results.get(name, [])
        if results:
            result_strs = []
            for result in results:
                url = result.get('url', '')
                title = result.get('title', '')
                description = result.get('description', '')
                result_str = f"Title: {title}\nURL: {url}\nDescription: {description}"
                result_strs.append(result_str)
            combined = '\n\n'.join(result_strs)
            web_results_str += f"Search results for '{name}':\n{combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results currently available.\n\n"

    matched_names_str = '\n'.join(matched_names)
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

    result = generator.chat_completion(chat_history, max_gen_len=None, temperature=0.0, top_p=0.9)
    return result.generation.content.strip()
