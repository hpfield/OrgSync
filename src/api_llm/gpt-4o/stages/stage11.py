import json
import logging
from tqdm import tqdm
from pydantic import BaseModel
from stages.utils import UserMessage, SystemMessage, get_client

logger = logging.getLogger(__name__)

class CapitalisedNameResponse(BaseModel):
    capitalised_name: str

def stage11_capitalize_group_names(groups, web_search_results):
    client = get_client()
    capitalised_groups = {}
    logger.info("Applying capitalisation to group names via LLM...")
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)

    for group_id, group_info in tqdm(groups.items(), desc="Capitalising group names"):
        current_name = group_info["name"]

        # Gather web search results context for the current representative name.
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

Output the result as JSON in the format: {{"capitalised_name": "Proper Capitalisation"}} with no additional text.
"""
        system_message = "You are an AI assistant that only corrects the capitalisation of organization names based on provided context, without changing the spelling."
        chat_history = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=chat_history,
                response_format=CapitalisedNameResponse,
            )
            capitalised_name = result.choices[0].message.parsed.capitalised_name
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
