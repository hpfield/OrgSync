# stages/stage4.py

import json
from tqdm import tqdm

from stages.utils import initialize_generator, UserMessage, SystemMessage

def stage4_process_groups_with_llm(grouped_names):
    generator = initialize_generator()
    refined_groups = {}
    num_groups = len(grouped_names)
    print("Processing groups with LLM...")
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
                    print(f"\nExpected a list, but got {type(parsed_response)}. Response was: {response}")
                    selected_names = []
            except json.JSONDecodeError:
                print(f"\nError parsing LLM response for group '{unique_name}'. Response was: {response}")
                selected_names = []
            except Exception as e:
                print(f"\nUnexpected error processing group '{unique_name}': {e}")
                selected_names = []
            if unique_name not in selected_names:
                selected_names.append(unique_name)
            refined_groups[unique_name] = selected_names
    print(f"Refined groups to {len(refined_groups)} groups after LLM processing.")
    return refined_groups

def process_group_with_llm(unique_name, matched_names, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in identifying whether organization names refer to the same UK research organization. You must output the results in the format specified by the user.")
    prompt = f"""Given the organization name: "{unique_name}"
and the following list of similar names:
{matched_names}
Please select the names that belong to the same organization as "{unique_name}", and output them as a JSON array of selected names.
Be strict, erring on the side of caution. Only include a name in your output if you're sure it belongs to the same research organization as {unique_name}. If it's ambiguous, leave it out! We want to preserve geographic separation for government institutions, but eliminate it for the private sector. 
Ensure the output is only the JSON array, with no additional text.

Do not include any keys or field names; only output the JSON array of names.

Correct Format Example:

["Acme Corporation", "Acme Inc", "Acme Co."]

Incorrect Format Examples:

{{"selected_names": ["Acme Corporation", "Acme Inc", "Acme Co."]}}

"Selected names are: ['Acme Corporation', 'Acme Inc', 'Acme Co.']"

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
