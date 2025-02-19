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
    """
    generator = get_generator()
    capitalised_groups = {}
    logger.info("Applying capitalisation to group names via LLM...")
    for group_id, group_info in tqdm(groups.items(), desc="Capitalising group names"):
        current_name = group_info["name"]
        prompt = f"""Please provide the correct capitalisation for the organization name below, without altering any other text:
"{current_name}"
Output only the capitalised name."""
        system_message = SystemMessage(content="You are an AI assistant that only corrects the capitalisation of organization names.")
        user_message = UserMessage(content=prompt)
        chat_history = [system_message, user_message]
        try:
            result = generator.chat_completion(chat_history, max_gen_len=100, temperature=0.0, top_p=0.9)
            capitalised_name = result.generation.content.strip()
            if not capitalised_name:
                capitalised_name = current_name
        except Exception as e:
            logger.error(f"Error in capitalisation for group {group_id}: {e}")
            capitalised_name = current_name
        # Create final group output with only "name" and "items"
        capitalised_groups[group_id] = {
            "name": capitalised_name,
            "items": group_info["items"]
        }
    logger.info("Capitalisation stage complete.")
    return capitalised_groups
