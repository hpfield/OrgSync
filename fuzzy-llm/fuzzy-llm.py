import json
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from collections import defaultdict

import os
import sys
from pathlib import Path
from typing import Optional

from tqdm import tqdm

# -------------------------------
# Configuration Section
# -------------------------------

print("Starting")

# Dynamically determine the repository root based on the script's location
THIS_DIR = Path(__file__).parent.resolve()
REPO_ROOT = Path("/home/ubuntu/OrgSync/llama-models")  # Adjust this if your structure is different

# Add the repository root to sys.path for imports
sys.path.append(str(REPO_ROOT))

# Absolute path to the tokenizer model
TOKENIZER_PATH = str(REPO_ROOT / "models" / "llama3" / "api" / "tokenizer.model")

# Absolute path to the checkpoint directory
DEFAULT_CKPT_DIR = "/home/ubuntu/OrgSync/.llama/checkpoints/Meta-Llama3.1-8B-Instruct"  # <-- Replace with your actual path
# DEFAULT_CKPT_DIR = "/root/.llama/checkpoints/Llama3.1-70B-Instruct/"

# Set environment variables required by torch.distributed
os.environ['RANK'] = '0'
os.environ['WORLD_SIZE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '12356'  # You can choose any free port

# -------------------------------
# End of Configuration
# -------------------------------

try:
    from models.llama3.api.datatypes import (
        UserMessage,
        SystemMessage,
        CompletionMessage,
        StopReason
    )
    from models.llama3.reference_impl.generation import Llama
except ModuleNotFoundError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure that the 'models' package is correctly added to sys.path and contains __init__.py files.")
    sys.exit(1)

print("Loaded model libs")

# Set parameters for LLM
temperature = 0.0
top_p = 0.9
max_seq_len = 1024
max_batch_size = 4
max_gen_len = None
model_parallel_size = 1

# Build the generator
generator = Llama.build(
    ckpt_dir=DEFAULT_CKPT_DIR,
    tokenizer_path=TOKENIZER_PATH,
    max_seq_len=max_seq_len,
    max_batch_size=max_batch_size,
    model_parallel_size=model_parallel_size,
)
print("Built generator")

# Load the UK names data
with open('/home/ubuntu/OrgSync/data/raw/uk_data.json', 'r') as file:
    uk_data = json.load(file)

# Function to preprocess the names
def preprocess_name(name):
    name = name.lower()  # Convert to lowercase
    name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with a single space
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    return name.strip()  # Strip leading and trailing whitespace

# Combine the name, short_name, and standardized_name fields
def combine_names(entry):
    combined_name = ' '.join(filter(None, [entry.get('name', ''), entry.get('short_name', ''), entry.get('standardized_name', '')]))
    return preprocess_name(combined_name)

# Create a list of combined names
combined_names = [combine_names(entry) for entry in uk_data]

# Remove exact duplicates to keep only unique combined names
unique_combined_names = list(set(combined_names))
total_unique_names = len(unique_combined_names)

# Vectorize the unique combined names using TF-IDF
vectorizer = TfidfVectorizer().fit(unique_combined_names)
name_vectors = vectorizer.transform(unique_combined_names)

# Use Nearest Neighbors to find similar names
nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
distances, indices = nbrs.kneighbors(name_vectors)

# Group similar names based on the specified threshold
def group_similar_names(threshold=0.3):
    grouped_names = defaultdict(list)
    used_names = set()

    for i, name in enumerate(unique_combined_names):
        if name in used_names:
            continue

        # Get similar names based on the cosine similarity
        similar_names = [unique_combined_names[idx] for j, idx in enumerate(indices[i]) if distances[i][j] <= threshold and idx != i]

        if similar_names:  # Only consider if there are matches
            # Add to the group and mark as used
            grouped_names[name].extend(similar_names)
            used_names.add(name)
            used_names.update(similar_names)

    return grouped_names

# Group the names
grouped_names = group_similar_names(threshold=0.5)

# Save grouped names to file
with open('grouped_names.json', 'w') as f:
    json.dump(grouped_names, f, indent=2)

print(f"Total unique combined names: {total_unique_names}")
print(f"Number of groups found: {len(grouped_names)}")

# Now, process each group with LLM
def process_group_with_llm(unique_name, matched_names, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in identifying whether organization names refer to the same UK research organization. You must output the results in the format specified by the user.")
    prompt = f"""Given the organization name: "{unique_name}"
and the following list of similar names:
{matched_names}
Please select the names that belong to the same research organization as "{unique_name}", and output them as a JSON array of selected names.
Be strict, erring on the side of caution. Only include a name in your output if you're sure it belongs to the same research organization as {unique_name}. If it's ambiguous, leave it out! We want to preserve geographic separation for government institutions, but eliminate it for the private. 
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

    # Generate the model's response
    result = generator.chat_completion(
        chat_history,
        max_gen_len=max_gen_len,
        temperature=temperature,
        top_p=top_p,
    )

    # Get the model's response
    out_message = result.generation
    response = out_message.content.strip()

    return response

refined_groups = {}  # key: unique_name, value: list of selected names

group_sizes = []
num_groups = len(grouped_names)

print("Processing groups with LLM...")
with tqdm(total=num_groups, desc='Processing groups with LLM') as pbar:
    for unique_name, matched_names in grouped_names.items():
        # For progress bar
        pbar.update(1)

        # matched_names is a list of names
        # Convert it to a string for the prompt
        matched_names_str = '\n'.join(matched_names)

        # Process with LLM
        response = process_group_with_llm(unique_name, matched_names_str, generator)

        # Parse the LLM response
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

        # Ensure selected_names is a list of strings
        if isinstance(selected_names, list):
            # Ensure all elements are strings
            selected_names = [str(name) for name in selected_names if isinstance(name, str)]
        else:
            selected_names = []

        # Add the unique_name to selected_names if not already present
        if unique_name not in selected_names:
            selected_names.append(unique_name)

        # Store the refined group
        refined_groups[unique_name] = selected_names

        group_sizes.append(len(selected_names))

# After processing all groups, print stats
average_group_size = sum(group_sizes) / len(group_sizes) if group_sizes else 0

print(f"Number of groups after LLM processing: {len(refined_groups)}")
print(f"Average group size: {average_group_size:.2f}")

# Save refined groups to file
with open('refined_groups.json', 'w') as f:
    json.dump(refined_groups, f, indent=2)

# Now, check for overlaps among the refined groups and combine overlapping groups
print("Combining overlapping groups...")

# Prepare list of sets from refined_groups
group_sets = []
for names in refined_groups.values():
    # Ensure names is a list of strings
    if not isinstance(names, list):
        print(f"Expected names to be a list, but got {type(names)}")
        names = []
    else:
        # Filter out any elements that are not strings
        names = [str(name) for name in names if isinstance(name, str)]
    try:
        group_sets.append(set(names))
    except TypeError as e:
        print(f"Error converting names to set: {e}")
        print(f"Names: {names}")
        continue

def merge_overlapping_groups(group_sets):
    merged = []
    for group in group_sets:
        found = False
        for mgroup in merged:
            if group & mgroup:
                mgroup |= group  # Merge
                found = True
                break
        if not found:
            merged.append(set(group))
    # Now, repeat until no further merging can be done
    merging = True
    while merging:
        merging = False
        for i in range(len(merged)):
            for j in range(i+1, len(merged)):
                if merged[i] & merged[j]:
                    merged[i] |= merged[j]
                    del merged[j]
                    merging = True
                    break
            if merging:
                break
    return merged

merged_groups = merge_overlapping_groups(group_sets)

number_of_combined_groups = len(merged_groups)
average_combined_group_size = sum(len(g) for g in merged_groups) / number_of_combined_groups

print(f"Number of combined groups: {number_of_combined_groups}")
print(f"Average combined group size: {average_combined_group_size:.2f}")

# Now, process each combined group with LLM
def process_combined_group_with_llm(group_names, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in refining groups of organisation names to identify those that refer to the same organisation. You must output the results in the format specified by the user.")
    prompt = f"""Given the following group of organisation names:
{group_names}
Please select the names that belong to the same organisation, and output them as a JSON object with two keys:
"selected_names": an array of the names that belong to the same organisation,
"representative_name": the name that best represents that organisation.
If you believe there is more than one organisation in this group, prioritise the predominantly represented organisation.
Be strict, erring on the side of caution. Only include a name in your output if you're sure it belongs to the same research organization. If it's ambiguous, leave it out! We want to preserve geographic separation for government institutions, but eliminate it for the private. 
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
  "representative_name": "Acme Corporation"
}}

"""

    user_message = UserMessage(content=prompt)
    chat_history = [system_message, user_message]

    # Generate the model's response
    result = generator.chat_completion(
        chat_history,
        max_gen_len=max_gen_len,
        temperature=temperature,
        top_p=top_p,
    )

    # Get the model's response
    out_message = result.generation
    response = out_message.content.strip()

    return response

final_groups = []
print("Processing combined groups with LLM...")
with tqdm(total=len(merged_groups), desc='Processing combined groups with LLM') as pbar:
    for group_set in merged_groups:
        pbar.update(1)
        group_names = '\n'.join(group_set)

        response = process_combined_group_with_llm(group_names, generator)

        # Parse the LLM response
        try:
            result = json.loads(response)
            selected_names = result.get('selected_names', [])
            representative_name = result.get('representative_name', '')
        except json.JSONDecodeError:
            print(f"\nError parsing LLM response for combined group. Response was: {response}")
            selected_names = []
            representative_name = ''
        except Exception as e:
            print(f"\nUnexpected error processing combined group: {e}")
            selected_names = []
            representative_name = ''

        # Ensure selected_names is a list of strings
        if isinstance(selected_names, list):
            selected_names = [str(name) for name in selected_names if isinstance(name, str)]
        else:
            print(f"\nExpected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}")
            selected_names = []

        final_groups.append({
            'selected_names': selected_names,
            'representative_name': representative_name
        })

final_group_sizes = [len(group['selected_names']) for group in final_groups]
average_final_group_size = sum(final_group_sizes) / len(final_groups) if final_groups else 0

print(f"Number of final groups: {len(final_groups)}")
print(f"Average final group size: {average_final_group_size:.2f}")

# Save final groups to file
with open('final_groups.json', 'w') as f:
    json.dump(final_groups, f, indent=2)

print("Processing complete.")
