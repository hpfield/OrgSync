import argparse
import json
import os
import sys
import pickle
import re
import time
import random
from collections import defaultdict
from pathlib import Path
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm

# Import the googlesearch module
try:
    from googlesearch import search
except ImportError:
    print("Please install the 'googlesearch-python' package: pip install googlesearch-python")
    sys.exit(1)

# -------------------------------
# Configuration Section
# -------------------------------

# Paths and environment variables setup
REPO_ROOT = Path("/home/ubuntu/OrgSync/llama-models")  # Adjust this if your structure is different
sys.path.append(str(REPO_ROOT))
TOKENIZER_PATH = str(REPO_ROOT / "models" / "llama3" / "api" / "tokenizer.model")
DEFAULT_CKPT_DIR = "/home/ubuntu/OrgSync/.llama/checkpoints/Meta-Llama3.1-8B-Instruct"  # <-- Replace with your actual path

# Set environment variables required by torch.distributed
os.environ['RANK'] = '0'
os.environ['WORLD_SIZE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '12355'  # You can choose any free port

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

# Set parameters for LLM
temperature = 0.0
top_p = 0.9
max_seq_len = 1024
max_batch_size = 4
max_gen_len = None
model_parallel_size = None

# Initialize the generator (LLM)
def initialize_generator():
    generator = Llama.build(
        ckpt_dir=DEFAULT_CKPT_DIR,
        tokenizer_path=TOKENIZER_PATH,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
        model_parallel_size=model_parallel_size,
    )
    return generator

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, required=True, help='Stage to start from (1-7)')
    parser.add_argument('--input', nargs='+', help='Input file(s) for the starting stage')
    parser.add_argument('--output', nargs='+', help='Output file(s) for the stages')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    return parser.parse_args()

# Main function
def main():
    args = parse_arguments()

    if args.stage == 1:
        preprocessed_data = stage1_load_and_preprocess_data()
        # Save output
        with open('preprocessed_data.pkl', 'wb') as f:
            pickle.dump(preprocessed_data, f)
        print("Stage 1 complete. Preprocessed data saved to 'preprocessed_data.pkl'.")
    elif args.stage == 2:
        if args.input:
            with open(args.input[0], 'rb') as f:
                preprocessed_data = pickle.load(f)
        else:
            print("Input file required for stage 2")
            sys.exit(1)
        vectorizer, name_vectors, unique_combined_names = stage2_vectorize_names(preprocessed_data)
        # Save outputs
        with open('vectorizer.pkl', 'wb') as f:
            pickle.dump(vectorizer, f)
        with open('name_vectors.pkl', 'wb') as f:
            pickle.dump(name_vectors, f)
        with open('unique_combined_names.pkl', 'wb') as f:
            pickle.dump(unique_combined_names, f)
        print("Stage 2 complete. Outputs saved to 'vectorizer.pkl', 'name_vectors.pkl', 'unique_combined_names.pkl'.")
    elif args.stage == 3:
        if args.input and len(args.input) >= 3:
            with open(args.input[0], 'rb') as f:
                vectorizer = pickle.load(f)
            with open(args.input[1], 'rb') as f:
                name_vectors = pickle.load(f)
            with open(args.input[2], 'rb') as f:
                unique_combined_names = pickle.load(f)
        else:
            print("Input files required for stage 3")
            sys.exit(1)
        grouped_names = stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=args.threshold)
        # Save output
        with open('grouped_names.json', 'w') as f:
            json.dump(grouped_names, f, indent=2)
        print("Stage 3 complete. Grouped names saved to 'grouped_names.json'.")
    elif args.stage == 4:
        if args.input:
            with open(args.input[0], 'r') as f:
                grouped_names = json.load(f)
        else:
            print("Input file required for stage 4")
            sys.exit(1)
        refined_groups = stage4_process_groups_with_llm(grouped_names)
        # Save output
        with open('refined_groups.json', 'w') as f:
            json.dump(refined_groups, f, indent=2)
        print("Stage 4 complete. Refined groups saved to 'refined_groups.json'.")
    elif args.stage == 5:
        if args.input:
            with open(args.input[0], 'r') as f:
                refined_groups = json.load(f)
        else:
            print("Input file required for stage 5")
            sys.exit(1)
        merged_groups = stage5_combine_overlapping_groups(refined_groups)
        # Save output
        with open('merged_groups.pkl', 'wb') as f:
            pickle.dump(merged_groups, f)
        print("Stage 5 complete. Merged groups saved to 'merged_groups.pkl'.")
    elif args.stage == 6:
        if args.input:
            with open(args.input[0], 'rb') as f:
                merged_groups = pickle.load(f)
        else:
            print("Input file required for stage 6")
            sys.exit(1)
        final_groups, unsure_groups = stage6_process_combined_groups_with_llm(merged_groups)
        # Save outputs
        with open('final_groups.json', 'w') as f:
            json.dump(final_groups, f, indent=2)
        with open('unsure_groups.json', 'w') as f:
            json.dump(unsure_groups, f, indent=2)
        print("Stage 6 complete. Outputs saved to 'final_groups.json' and 'unsure_groups.json'.")
    elif args.stage == 7:
        if args.input and len(args.input) >= 2:
            with open(args.input[0], 'r') as f:
                unsure_groups = json.load(f)
            with open(args.input[1], 'r') as f:
                final_groups = json.load(f)
        else:
            print("Input files required for stage 7")
            sys.exit(1)
        updated_final_groups = stage7_process_unsure_groups_with_llm(unsure_groups, final_groups)
        # Save output
        with open('updated_final_groups.json', 'w') as f:
            json.dump(updated_final_groups, f, indent=2)
        print("Stage 7 complete. Updated final groups saved to 'updated_final_groups.json'.")
    else:
        print("Invalid stage specified.")
        sys.exit(1)

# Stage 1: Load and preprocess data
def stage1_load_and_preprocess_data():
    # Load the UK names data
    with open('/home/ubuntu/OrgSync/data/raw/uk_data.json', 'r') as file:
        uk_data = json.load(file)
    # Preprocess the data
    def preprocess_name(name):
        name = name.lower()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[^\w\s]', '', name)
        return name.strip()
    def combine_names(entry):
        combined_name = ' '.join(filter(None, [entry.get('name', ''), entry.get('short_name', ''), entry.get('standardized_name', '')]))
        return preprocess_name(combined_name)
    preprocessed_data = [combine_names(entry) for entry in uk_data]
    print(f"Loaded and preprocessed {len(preprocessed_data)} names.")
    return preprocessed_data

# Stage 2: Vectorize names and find similar names
def stage2_vectorize_names(preprocessed_data):
    unique_combined_names = list(set(preprocessed_data))
    total_unique_names = len(unique_combined_names)
    vectorizer = TfidfVectorizer().fit(unique_combined_names)
    name_vectors = vectorizer.transform(unique_combined_names)
    print(f"Vectorized {total_unique_names} unique combined names.")
    return vectorizer, name_vectors, unique_combined_names

# Stage 3: Group similar names based on threshold
def stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=0.5):
    nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
    distances, indices = nbrs.kneighbors(name_vectors)
    grouped_names = defaultdict(list)
    used_names = set()
    for i, name in enumerate(unique_combined_names):
        if name in used_names:
            continue
        similar_names = [unique_combined_names[idx] for j, idx in enumerate(indices[i]) if distances[i][j] <= threshold and idx != i]
        if similar_names:
            grouped_names[name].extend(similar_names)
            used_names.add(name)
            used_names.update(similar_names)
    print(f"Grouped names into {len(grouped_names)} groups.")
    return grouped_names

# Stage 4: Process each group with LLM to refine groups
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

# Helper function for LLM processing in stage 4
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

# Stage 5: Combine overlapping groups
def stage5_combine_overlapping_groups(refined_groups):
    print("Combining overlapping groups...")
    group_sets = []
    for names in refined_groups.values():
        if not isinstance(names, list):
            print(f"Expected names to be a list, but got {type(names)}")
            names = []
        else:
            names = [str(name) for name in names if isinstance(name, str)]
        try:
            group_sets.append(set(names))
        except TypeError as e:
            print(f"Error converting names to set: {e}")
            print(f"Names: {names}")
            continue

    merged_groups = merge_overlapping_groups(group_sets)
    print(f"Number of combined groups: {len(merged_groups)}")
    return merged_groups

# Helper function for merging groups in stage 5
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

# Stage 6: Process combined groups with LLM to finalize groups
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

# Helper function for LLM processing in stage 6
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

# Stage 7: Process unsure groups with LLM using web search
def stage7_process_unsure_groups_with_llm(unsure_groups, final_groups):
    generator = initialize_generator()
    print("Processing unsure groups with LLM using web search...")
    with tqdm(total=len(unsure_groups), desc='Processing unsure groups with LLM using web search') as pbar:
        for group in unsure_groups:
            pbar.update(1)
            group_names = group['group_names']
            web_search_results = perform_web_search(group_names)
            response = process_unsure_group_with_llm(group_names, web_search_results, generator)
            try:
                result = json.loads(response)
                selected_names = result.get('selected_names', [])
                representative_name = result.get('representative_name', '')
            except json.JSONDecodeError:
                print(f"\nError parsing LLM response for unsure group. Response was: {response}")
                selected_names = []
                representative_name = ''
            except Exception as e:
                print(f"\nUnexpected error processing unsure group: {e}")
                selected_names = []
                representative_name = ''
            if isinstance(selected_names, list):
                selected_names = [str(name) for name in selected_names if isinstance(name, str)]
            else:
                print(f"\nExpected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}")
                selected_names = []
            final_groups.append({
                'selected_names': selected_names,
                'representative_name': representative_name
            })
    print(f"Total number of final groups after processing unsure groups: {len(final_groups)}")
    return final_groups

# Helper functions for web search and LLM processing in stage 7
def perform_web_search(names, num_results=3, max_retries=3):
    web_search_results = {}
    for name in names:
        retries = 0
        while retries < max_retries:
            try:
                query = f'"{name}"'
                search_results = []
                for url in search(query, num_results=num_results, lang='en'):
                    search_results.append(url)
                web_search_results[name] = search_results
                time.sleep(random.uniform(5, 15))
                break
            except Exception as e:
                if "Too Many Requests" in str(e):
                    retries += 1
                    print(f"Too many requests. Retrying {retries}/{max_retries}...")
                    time.sleep(60 * retries)
                else:
                    print(f"Error during web search for '{name}': {e}")
                    web_search_results[name] = []
                    break
    return web_search_results

def process_unsure_group_with_llm(group_names, web_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in refining groups of organisation names to identify those that refer to the same organisation. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")
    web_results_str = ""
    for name in group_names:
        urls = web_search_results.get(name, [])
        urls_str = '\n'.join(urls)
        web_results_str += f"Search results for '{name}':\n{urls_str}\n\n"

    prompt = f"""Given the following group of organisation names:
{', '.join(group_names)}

And the following web search results:
{web_results_str}

Please select the names that belong to the same organisation, and output them as a JSON object with two keys:
"selected_names": an array of the names that belong to the same organisation,
"representative_name": the name that best represents that organisation.

Ensure the output is only the JSON object, with no additional text.

Example:

Given the following group of organisation names:
Acme Corporation, Acme Corp, Acme Inc., Acme Co., Ace Corp

And the following web search results:
Search results for 'Acme Corporation':
http://www.acmecorp.com
http://en.wikipedia.org/wiki/Acme_Corporation

Search results for 'Ace Corp':
http://www.acecorp.com

Your output should be:

{{
  "selected_names": ["Acme Corporation", "Acme Corp", "Acme Inc.", "Acme Co."],
  "representative_name": "Acme Corporation"
}}

Remember, only output the JSON object.
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

if __name__ == '__main__':
    main()
