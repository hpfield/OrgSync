import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage4_process_groups_with_llm(grouped_names):
    generator = get_generator()
    refined_groups = {}
    num_groups = len(grouped_names)
    logger.info("Processing groups with LLM...")
    
    with tqdm(total=num_groups, desc='Processing groups with LLM') as pbar:
        for unique_name, matched_names in grouped_names.items():
            pbar.update(1)
            matched_names_str = '\n'.join(matched_names)
            response = process_group_with_llm(unique_name, matched_names_str, generator)
            try:
                parsed_response = json.loads(response)
                if isinstance(parsed_response, list):
                    selected_names = parsed_response
                else:
                    msg = f"Expected a list, but got {type(parsed_response)}. Response was: {response}"
                    tqdm.write(msg)  # Ensures tqdm progress bar is not disrupted
                    logger.warning(msg)
                    selected_names = []
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for group '{unique_name}'. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                selected_names = []
            except Exception as e:
                msg = f"Unexpected error processing group '{unique_name}': {e}"
                tqdm.write(msg)
                logger.exception(msg)
                selected_names = []
                
            if unique_name not in selected_names:
                selected_names.append(unique_name)
            refined_groups[unique_name] = selected_names
            
    logger.info(f"Refined groups to {len(refined_groups)} groups after LLM processing.")
    return refined_groups

def process_group_with_llm(unique_name, matched_names, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in identifying whether organization names refer to the same UK research organization. You must output the results in the format specified by the user.")
    prompt = f"""Given the organization name: "{unique_name}"
and the following list of similar names:
{matched_names}
Please select the names that belong to the same organization as "{unique_name}", and output them as a JSON array of selected names in lowercase.
Be strict, erring on the side of caution. Only include a name in your output if you're sure it belongs to the same research organization as {unique_name}. If it's ambiguous, leave it out! We want to preserve geographic separation for government institutions, but eliminate it for the private sector. 
Ensure the output is only the JSON array, with no additional text.

Do not include any keys or field names; only output the JSON array of names.

Correct Format Example:

["acme corporation", "acme inc", "acme co."]

Incorrect Format Examples:

{{"selected_names": ["acme corporation", "acme inc", "acme co."]}}

"Selected names are: ['acme corporation", "acme inc", "acme co.']"

Remember, only output the JSON array.

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
