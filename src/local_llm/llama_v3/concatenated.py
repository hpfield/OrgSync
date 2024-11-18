# --- Start of main.py ---

import argparse
import sys
import os
import pickle
import json
import logging
from datetime import datetime

# Import stage functions
from stages.stage1 import stage1_load_and_preprocess_data
from stages.stage2 import stage2_vectorize_names
from stages.stage3 import stage3_group_similar_names
from stages.stage4 import stage4_perform_web_search  # Updated stage
from stages.stage5 import stage5_process_groups_with_llm
from stages.stage6 import stage6_combine_overlapping_groups  # Ensure duplicates are removed
from stages.stage7 import stage7_determine_organisation_type  # New stage
from stages.stage8 import stage8_finalize_groups  # New final stage

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, default=1, help='Stage to start from (1-8)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], default='duckduckgo', help='Method for web searching in Stage 4')
    parser.add_argument('--input', nargs='+', help='Input file(s) for the starting stage')
    parser.add_argument('--output-dir', type=str, default='outputs', help='Output directory to save results')
    return parser.parse_args()

# Define logging configuration
def setup_logging(stage):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"{timestamp}_stage{stage}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    args = parse_arguments()
    stage = args.stage
    input_files = args.input
    output_dir = args.output_dir
    setup_logging(stage)

    os.makedirs(output_dir, exist_ok=True)

    # Stage 1
    if stage <= 1:
        preprocessed_data = stage1_load_and_preprocess_data()
        with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'wb') as f:
            pickle.dump(preprocessed_data, f)
        logging.info("Stage 1 complete.")

    # Stage 2
    if stage <= 2:
        if stage == 2 and input_files:
            with open(input_files[0], 'rb') as f:
                preprocessed_data = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'rb') as f:
                preprocessed_data = pickle.load(f)
        vectorizer, name_vectors, unique_combined_names = stage2_vectorize_names(preprocessed_data)
        with open(os.path.join(output_dir, 'vectorizer_stage2.pkl'), 'wb') as f:
            pickle.dump(vectorizer, f)
        with open(os.path.join(output_dir, 'name_vectors_stage2.pkl'), 'wb') as f:
            pickle.dump(name_vectors, f)
        with open(os.path.join(output_dir, 'unique_combined_names_stage2.pkl'), 'wb') as f:
            pickle.dump(unique_combined_names, f)
        # Save unique_combined_names as JSON for review
        with open(os.path.join(output_dir, 'unique_combined_names_stage2.json'), 'w') as f:
            json.dump(unique_combined_names, f, indent=2)
        logging.info("Stage 2 complete.")

    # Stage 3
    if stage <= 3:
        if stage == 3 and input_files:
            with open(input_files[0], 'rb') as f:
                vectorizer = pickle.load(f)
            with open(input_files[1], 'rb') as f:
                name_vectors = pickle.load(f)
            with open(input_files[2], 'rb') as f:
                unique_combined_names = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'vectorizer_stage2.pkl'), 'rb') as f:
                vectorizer = pickle.load(f)
            with open(os.path.join(output_dir, 'name_vectors_stage2.pkl'), 'rb') as f:
                name_vectors = pickle.load(f)
            with open(os.path.join(output_dir, 'unique_combined_names_stage2.pkl'), 'rb') as f:
                unique_combined_names = pickle.load(f)
        grouped_names = stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=args.threshold)
        with open(os.path.join(output_dir, 'grouped_names_stage3.json'), 'w') as f:
            json.dump(grouped_names, f, indent=2)
        logging.info("Stage 3 complete.")

    # Stage 4
    if stage <= 4:
        if stage == 4 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
        else:
            with open(os.path.join(output_dir, 'grouped_names_stage3.json'), 'r') as f:
                grouped_names = json.load(f)
        web_search_results = stage4_perform_web_search(grouped_names, search_method=args.search_method)
        with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'w') as f:
            json.dump(web_search_results, f, indent=2)
        logging.info("Stage 4 complete.")

    # Stage 5
    if stage <= 5:
        if stage == 5 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'grouped_names_stage3.json'), 'r') as f:
                grouped_names = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        refined_groups = stage5_process_groups_with_llm(grouped_names, web_search_results)
        with open(os.path.join(output_dir, 'refined_groups_stage5.json'), 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 5 complete.")

    # Stage 6
    if stage <= 6:
        if stage == 6 and input_files:
            with open(input_files[0], 'r') as f:
                refined_groups = json.load(f)
        else:
            with open(os.path.join(output_dir, 'refined_groups_stage5.json'), 'r') as f:
                refined_groups = json.load(f)
        merged_groups = stage6_combine_overlapping_groups(refined_groups)
        with open(os.path.join(output_dir, 'merged_groups_stage6.json'), 'w') as f:
            json.dump(merged_groups, f, indent=2)
        logging.info("Stage 6 complete.")

    # Stage 7
    if stage <= 7:
        if stage == 7 and input_files:
            with open(input_files[0], 'r') as f:
                merged_groups = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'merged_groups_stage6.json'), 'r') as f:
                merged_groups = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        groups_with_types = stage7_determine_organisation_type(merged_groups, web_search_results)
        with open(os.path.join(output_dir, 'groups_with_types_stage7.json'), 'w') as f:
            json.dump(groups_with_types, f, indent=2)
        logging.info("Stage 7 complete.")

    # Stage 8
    if stage <= 8:
        if stage == 8 and input_files:
            with open(input_files[0], 'r') as f:
                groups_with_types = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'groups_with_types_stage7.json'), 'r') as f:
                groups_with_types = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        final_groups = stage8_finalize_groups(groups_with_types, web_search_results)
        with open(os.path.join(output_dir, 'final_groups_stage8.json'), 'w') as f:
            json.dump(final_groups, f, indent=2)
        logging.info("Stage 8 complete.")

if __name__ == '__main__':
    main()


# --- End of main.py ---

# --- Start of stages/stage1.py ---

import json
import re
import logging  # Import logging

# Get the logger for this stage file
logger = logging.getLogger(__name__)

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
        combined_name = ' '.join(filter(None, [entry.get('name', ''), entry.get('short_name', '')]))
        return preprocess_name(combined_name)

    preprocessed_data = [combine_names(entry) for entry in uk_data]
    logger.info(f"Loaded and preprocessed {len(preprocessed_data)} names.")
    return preprocessed_data


# --- End of stages/stage1.py ---

# --- Start of stages/stage2.py ---

import logging  # Import logging
from sklearn.feature_extraction.text import TfidfVectorizer

# Get the logger for this stage file
logger = logging.getLogger(__name__)

def stage2_vectorize_names(preprocessed_data):
    unique_combined_names = list(set(preprocessed_data))
    total_unique_names = len(unique_combined_names)
    vectorizer = TfidfVectorizer().fit(unique_combined_names)
    name_vectors = vectorizer.transform(unique_combined_names)
    logger.info(f"Vectorized {total_unique_names} unique combined names.")
    return vectorizer, name_vectors, unique_combined_names


# --- End of stages/stage2.py ---

# --- Start of stages/stage3.py ---

import logging
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

# Initialize logger
logger = logging.getLogger(__name__)

def stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=0.5):
    nbrs = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute').fit(name_vectors)
    distances, indices = nbrs.kneighbors(name_vectors)

    grouped_names = {}
    used_names = set()

    for i, name in enumerate(unique_combined_names):
        if name in used_names:
            continue
        similar_names = [
            unique_combined_names[idx]
            for j, idx in enumerate(indices[i])
            if distances[i][j] <= threshold and idx != i and unique_combined_names[idx] not in used_names
        ]
        all_group_names = [name] + similar_names
        if len(all_group_names) > 1:
            grouped_names[name] = similar_names
            used_names.update(all_group_names)
        else:
            # No similar names found, skip adding this group
            continue

    logger.info(f"Grouped names into {len(grouped_names)} groups after removing groups of size 1.")
    return grouped_names


# --- End of stages/stage3.py ---

# --- Start of stages/stage4.py ---

import logging
from tqdm import tqdm

from stages.utils import perform_web_search  # Import the web search utility

def stage4_perform_web_search(grouped_names, search_method='duckduckgo'):
    logger = logging.getLogger(__name__)
    logger.info("Extracting unique names from grouped names for web search...")
    
    # Extract all unique names from the grouped names
    unique_names = set()
    for unique_name, matched_names in grouped_names.items():
        unique_names.add(unique_name)
        unique_names.update(matched_names)
    
    unique_names = sorted(unique_names)
    num_names = len(unique_names)
    
    # Perform web search on each unique name
    web_search_results = {}
    with tqdm(total=num_names, desc='Performing web search on unique names') as pbar:
        for name in unique_names:
            pbar.update(1)
            # Perform web search on the name
            results = perform_web_search([name], search_method=search_method)
            # Store results for the name
            web_search_results[name] = results.get(name, [])
    logger.info(f"Completed web search for {num_names} unique names.")
    return web_search_results


# --- End of stages/stage4.py ---

# --- Start of stages/stage5.py ---

import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage5_process_groups_with_llm(grouped_names, web_search_results):
    generator = get_generator()
    refined_groups = {}
    num_groups = len(grouped_names)
    logger.info("Processing groups with LLM...")

    with tqdm(total=num_groups, desc='Processing groups with LLM') as pbar:
        for unique_name, matched_names in grouped_names.items():
            pbar.update(1)
            group_names = [unique_name] + matched_names
            # Retrieve web search results for each name in the group
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = process_group_with_llm(unique_name, matched_names, group_search_results, generator)
            try:
                parsed_response = json.loads(response)
                if isinstance(parsed_response, list):
                    selected_names = parsed_response
                else:
                    msg = f"Expected a list, but got {type(parsed_response)}. Response was: {response}"
                    tqdm.write(msg)
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

def process_group_with_llm(unique_name, matched_names, group_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps in identifying whether organization names refer to the same UK research organization. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")

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
            results_combined = '\n\n'.join(result_strs)
            web_results_str += f"Search results for '{name}':\n{results_combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results found.\n\n"

    matched_names_str = '\n'.join(matched_names)
    prompt = f"""Given the organization name: "{unique_name}"
and the following list of similar names:
{matched_names_str}
And the following web search results:
{web_results_str}
Please select the names that belong to the same organization as "{unique_name}", and output them as a JSON array of selected names in lowercase.
Be strict, erring on the side of caution. Only include a name in your output if you're sure it belongs to the same research organization as "{unique_name}". If it's ambiguous, leave it out! We want to preserve geographic separation for government institutions, but eliminate it for the private sector.
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


# --- End of stages/stage5.py ---

# --- Start of stages/stage6.py ---

import logging

# Initialize logger
logger = logging.getLogger(__name__)

def stage6_combine_overlapping_groups(refined_groups):
    logger.info("Combining overlapping groups...")
    group_sets = []
    for names in refined_groups.values():
        if not isinstance(names, list):
            logger.warning(f"Expected names to be a list, but got {type(names)}. Setting names to an empty list.")
            names = []
        else:
            names = [str(name) for name in names if isinstance(name, str)]
        try:
            group_sets.append(set(names))
        except TypeError as e:
            logger.error(f"Error converting names to set: {e}. Names: {names}")
            continue

    merged_groups = merge_overlapping_groups(group_sets)
    # Remove duplicates within each merged group (already sets)
    merged_groups = [sorted(list(group)) for group in merged_groups]  # Convert sets to sorted lists
    logger.info(f"Number of combined groups: {len(merged_groups)}")
    return merged_groups

def merge_overlapping_groups(group_sets):
    merged = []
    for group in group_sets:
        found = False
        for mgroup in merged:
            if group & mgroup:
                mgroup |= group
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


# --- End of stages/stage6.py ---

# --- Start of stages/stage7.py ---

import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage7_determine_organisation_type(merged_groups, web_search_results):
    generator = get_generator()
    groups_with_types = []
    logger.info("Determining organisation types for groups...")

    with tqdm(total=len(merged_groups), desc='Determining organisation types') as pbar:
        for group_names in merged_groups:
            pbar.update(1)
            # Retrieve web search results for each name in the group
            group_search_results = {name: web_search_results.get(name, []) for name in group_names}
            response = determine_organisation_type_with_llm(group_names, group_search_results, generator)
            try:
                result = json.loads(response)
                organisation_type = result.get('organisation_type', '')
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                organisation_type = ''
            except Exception as e:
                msg = f"Unexpected error processing group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                organisation_type = ''
            
            groups_with_types.append({
                'group_names': group_names,
                'organisation_type': organisation_type
            })

    logger.info(f"Completed determining organisation types for {len(groups_with_types)} groups.")
    return groups_with_types

def determine_organisation_type_with_llm(group_names, group_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps identify the type of organisation that a group of names refer to. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")

    web_results_str = ""
    for name in group_names:
        results = group_search_results.get(name, [])
        if results:
            result_strs = []
            for result in results:
                url = result.get('url', '')
                title = result.get('title', '')
                description = result.get('description', '')
                result_str = f"Title: {title}\nURL: {url}\nDescription: {description}"
                result_strs.append(result_str)
            results_combined = '\n\n'.join(result_strs)
            web_results_str += f"Search results for '{name}':\n{results_combined}\n\n"
        else:
            web_results_str += f"Search results for '{name}':\nNo results found.\n\n"

    prompt = f"""Given the following group of organization names:
{', '.join(group_names)}

And the following web search results:
{web_results_str}

Please determine the type of organization these names refer to. Examples of organization types include, but are not limited to: 'company', 'university', 'government organization', 'non-profit', 'research institute', etc.

Output your answer as a JSON object with one key:
"organisation_type": the type of organization these names refer to.

Ensure the output is only the JSON object, with no additional text.

Example:

{{
"organisation_type": "university"
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


# --- End of stages/stage7.py ---

# --- Start of stages/utils.py ---

import os
import sys
import time
import random
import logging
from pathlib import Path

# Initialize logger
logger = logging.getLogger(__name__)

# -------------------------------
# Configuration Section
# -------------------------------

# Determine the absolute path to the project root (where main.py is located)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Assuming the 'models' directory is at '/home/ubuntu/OrgSync/llama-models/models'
# You can adjust this path if 'models' is located differently
MODELS_DIR = Path("/home/ubuntu/OrgSync/llama-models/models")

# Add the 'models' directory to sys.path
sys.path.append(str(MODELS_DIR.parent))

# Absolute path to the tokenizer model
TOKENIZER_PATH = str(MODELS_DIR / "llama3" / "api" / "tokenizer.model")

# Absolute path to the checkpoint directory
DEFAULT_CKPT_DIR = "/home/ubuntu/OrgSync/.llama/checkpoints/Meta-Llama3.1-8B-Instruct"  # Replace with your actual path

# Set environment variables required by torch.distributed
os.environ['RANK'] = '0'
os.environ['WORLD_SIZE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '12355'  # You can choose any free port

# Allow environemnt variables to be reset to persist through pipeline
def configure_environment():
    # Add the 'models' directory to sys.path
    sys.path.append(str(MODELS_DIR.parent))

    # Set environment variables required by torch.distributed
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'  # You can choose any free port

# -------------------------------
# End of Configuration
# -------------------------------

# Import the googlesearch module
try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None
    logger.warning("Google search module not available. Install it to enable Google search functionality.")

# Import necessary classes from the models package
try:
    from models.llama3.reference_impl.generation import Llama
    from models.llama3.api.datatypes import (
        UserMessage,
        SystemMessage,
        CompletionMessage,
        StopReason
    )
except ModuleNotFoundError as e:
    logger.critical(f"Error importing Llama model modules: {e}")
    sys.exit(1)

# Import DuckDuckGo search function
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    logger.warning("DuckDuckGo search module not available. Install it to enable DuckDuckGo search functionality.")

logger.info("Initializing the Llama generator.")
generator = Llama.build(
    ckpt_dir=DEFAULT_CKPT_DIR,
    tokenizer_path=TOKENIZER_PATH,
    max_seq_len=8192,
    max_batch_size=4,
    model_parallel_size=None,
)

def get_generator():
    return generator

import logging
import time
import random
import sys
# Assume DDGS is already imported and available

def perform_web_search(names, num_results=3, max_retries=7, search_method='duckduckgo', api_key=None):
    if search_method == 'duckduckgo' and DDGS is None:
        logger.error("DuckDuckGo search module not available. Please install 'duckduckgo-search' or choose another search method.")
        sys.exit(1)
    
    web_search_results = {}
    for name in names:
        retries = 0
        success = False
        while retries < max_retries and not success:
            # original_level = logging.getLogger().level  # Get original level at the start
            try:
                query = f'"{name}"'
                search_results = []
                
                # Temporarily suppress logs
                # logging.getLogger().setLevel(logging.CRITICAL)
                
                # Perform search
                ddgs = DDGS()
                results = ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=num_results)
                
                if results:
                    for res in results:
                        search_results.append({
                            'url': res.get('href', ''),
                            'title': res.get('title', ''),
                            'description': res.get('body', '')
                        })
                
                # Restore original logging level in `finally`
                success = True
                
            except Exception as e:
                retries += 1
                logger.error(f"Error during web search for '{name}': {e}. Retrying ({retries}/{max_retries})...")
                time.sleep(2 ** retries)  # Exponential backoff
                
            # finally:
                # Restore logging level no matter what
                # logging.getLogger().setLevel(original_level)
                
        if not success:
            logger.error(f"Failed to retrieve search results for '{name}' after {retries} retries.")
            web_search_results[name] = []
            
    return web_search_results



#! Not currently using
def duckduckgo_search(query, num_results):
    """Perform a search using the DuckDuckGo API."""
    logger.info(f"Performing DuckDuckGo search for query: {query}")
    params = {
        'q': query,
        'format': 'json',
        'no_html': 1,
        'skip_disambig': 1,
        'pretty': 1,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get('https://api.duckduckgo.com/', params=params, headers=headers)
    data = response.json()

    results = []
    related_topics = data.get('RelatedTopics', [])
    for topic in related_topics:
        if 'FirstURL' in topic:
            results.append(topic['FirstURL'])
        elif 'Topics' in topic:
            for subtopic in topic['Topics']:
                if 'FirstURL' in subtopic:
                    results.append(subtopic['FirstURL'])
        if len(results) >= num_results:
            break
    logger.info(f"Received URLs from DuckDuckGo for query '{query}'.")
    return results[:num_results]


# --- End of stages/utils.py ---

