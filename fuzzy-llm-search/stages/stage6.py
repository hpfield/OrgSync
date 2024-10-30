# stages/stage6.py

import json
from tqdm import tqdm

from stages.utils import initialize_generator, UserMessage, SystemMessage

def stage6_process_combined_groups_with_llm(merged_groups):
    generator = initialize_generator()
    final_groups = []
    unsure_groups = []
    print("Processing combined groups with LLM...")
    with tqdm(total=len(merged_groups), desc='Processing combined groups with LLM') as pbar:
        for group_set in merged_groups:
            pbar.update(1)
            group_names = '\n'.join(group_set)
            response = process_combined_group_with_llm(group_names, generator)
            try:
                result = json.loads(response)
                selected_names = result.get('selected_names', [])
                representative_name = result.get('representative_name', '')
                certainty = result.get('certainty', '')
            except json.JSONDecodeError:
                print(f"\nError parsing LLM response for combined group. Response was: {response}")
                selected_names = []
                representative_name = ''
                certainty = ''
            except Exception as e:
                print(f"\nUnexpected error processing combined group: {e}")
                selected_names = []
                representative_name = ''
                certainty = ''
            if isinstance(selected_names, list):
                selected_names = [str(name) for name in selected_names if isinstance(name, str)]
            else:
                print(f"\nExpected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}")
                selected_names = []
            if certainty.lower() == 'sure':
                final_groups.append({
                    'selected_names': selected_names,
                    'representative_name': representative_name
                })
            else:
                unsure_groups.append({
                    'group_names': list(group_set),
                    'selected_names': selected_names,
                    'representative_name': representative_name,
                    'certainty': certainty
                })
    print(f"Number of final groups: {len(final_groups)}")
    print(f"Number of unsure groups: {len(unsure_groups)}")
    return final_groups, unsure_groups

def process_combined_group_with_llm(group_names, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in refining groups of organisation names to identify those that refer to the same organisation. You must output the results in the format specified by the user.")
    prompt = f"""Given the following group of organisation names:
{group_names}
Please select the names that belong to the same organisation, and output them as a JSON object with three keys:
"selected_names": an array of the names that belong to the same organisation,
"representative_name": the name that best represents that organisation,
"certainty": a string that is either "sure" or "unsure" indicating whether you are certain the names refer to the same organisation.

If you believe there is more than one organisation in this group, prioritise the predominantly represented organisation.

Ensure the output is only the JSON object, with no additional text.

Example:

Given the following group of organisation names:
Acme Corporation
Acme Corp
Acme Inc.
Acme Co.
Ace Corp

Your output should be:

{{
  "selected_names": ["Acme Corporation", "Acme Corp", "Acme Inc.", "Acme Co."],
  "representative_name": "Acme Corporation",
  "certainty": "sure"
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
