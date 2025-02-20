import json
import logging
from tqdm import tqdm
from stages.utils import UserMessage, SystemMessage, get_generator

logger = logging.getLogger(__name__)

def stage11_capitalize_group_names(groups, web_search_results):
    """
    Applies appropriate capitalisation to the representative names of groups using LLM.
    Only the overall group name is changed; the items remain unmodified.
    The final output will have the format: { group_UUID: { "name": <capitalised_name>, "items": [...] } }
    
    The LLM is provided with web search results context to help determine proper capitalisation.
    It is highly unlikely that the company name should be in all caps, and any full caps from Companies House
    should be ignored. The LLM should not change the spelling of the representative name, only provide the correct
    capitalisation.
    """
    generator = get_generator()
    capitalised_groups = {}
    logger.info("Applying capitalisation to group names via LLM...")

    for group_id, group_info in tqdm(groups.items(), desc="Capitalising group names"):
        current_name = group_info["name"]

        # Gather web search results context for the current representative name
        web_results = web_search_results.get(current_name.lower(), [])
        web_context = ""
        if web_results:
            result_strs = []
            for result in web_results:
                url = result.get('url', '')
                title = result.get('title', '')
                description = result.get('description', '')
                result_strs.append(f"Title: {title}\nURL: {url}\nDescription: {description}")
            web_context = "\n\n".join(result_strs)
        
        prompt = f"""Please provide the correct capitalisation for the organization name below, without altering its spelling:
"{current_name}"

Here is some context from web search results:
{web_context}

Note:
- It is highly unlikely that the company name should be in all caps.
- Ignore any instances of full caps as provided by Companies House.
- Do not change the spelling of the representative name; only adjust the capitalisation.

Output only the correctly capitalised name, with no additional text."""
        
        system_message = SystemMessage(content="You are an AI assistant that only corrects the capitalisation of organization names based on provided context, without changing the spelling.")
        user_message = UserMessage(content=prompt)
        chat_history = [system_message, user_message]
        
        try:
            result = generator.chat_completion(chat_history, max_gen_len=50, temperature=0.0, top_p=0.9)
            capitalised_name = result.generation.content.strip()
            if not capitalised_name:
                capitalised_name = current_name
        except Exception as e:
            logger.error(f"Error in capitalisation for group {group_id}: {e}")
            capitalised_name = current_name
        
        capitalised_groups[group_id] = {
            "name": capitalised_name,
            "items": group_info["items"]
        }
    logger.info("Capitalisation stage complete.")
    return capitalised_groups
