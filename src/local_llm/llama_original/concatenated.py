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
from stages.stage4 import stage4_process_groups_with_llm
from stages.stage5 import stage5_combine_overlapping_groups
from stages.stage6 import stage6_process_combined_groups_with_llm
from stages.stage7 import stage7_process_unsure_groups_with_llm

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, default=1, help='Stage to start from (1-7)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], default='duckduckgo', help='Method for web searching in Stage 7')
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
        refined_groups = stage4_process_groups_with_llm(grouped_names)
        with open(os.path.join(output_dir, 'refined_groups_stage4.json'), 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 4 complete.")

    # Stage 5
    if stage <= 5:
        if stage == 5 and input_files:
            with open(input_files[0], 'r') as f:
                refined_groups = json.load(f)
        else:
            with open(os.path.join(output_dir, 'refined_groups_stage4.json'), 'r') as f:
                refined_groups = json.load(f)
        merged_groups = stage5_combine_overlapping_groups(refined_groups)
        with open(os.path.join(output_dir, 'merged_groups_stage5.pkl'), 'wb') as f:
            pickle.dump(merged_groups, f)
        logging.info("Stage 5 complete.")

    # Stage 6
    if stage <= 6:
        if stage == 6 and input_files:
            with open(input_files[0], 'rb') as f:
                merged_groups = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'merged_groups_stage5.pkl'), 'rb') as f:
                merged_groups = pickle.load(f)
        final_groups, unsure_groups = stage6_process_combined_groups_with_llm(merged_groups)
        with open(os.path.join(output_dir, 'final_groups_stage6.json'), 'w') as f:
            json.dump(final_groups, f, indent=2)
        with open(os.path.join(output_dir, 'unsure_groups_stage6.json'), 'w') as f:
            json.dump(unsure_groups, f, indent=2)
        logging.info("Stage 6 complete.")

    # Stage 7
    if stage <= 7:
        if not hasattr(args, 'search_method'):
            logging.error("Error: --search-method is required for Stage 7.")
            sys.exit(1)
        if stage == 7 and input_files:
            with open(input_files[0], 'r') as f:
                final_groups = json.load(f)
            with open(input_files[1], 'r') as f:
                unsure_groups = json.load(f)
        else:
            with open(os.path.join(output_dir, 'final_groups_stage6.json'), 'r') as f:
                final_groups = json.load(f)
            with open(os.path.join(output_dir, 'unsure_groups_stage6.json'), 'r') as f:
                unsure_groups = json.load(f)
        updated_final_groups = stage7_process_unsure_groups_with_llm(unsure_groups, final_groups, args.search_method)
        with open(os.path.join(output_dir, 'updated_final_groups_stage7.json'), 'w') as f:
            json.dump(updated_final_groups, f, indent=2)
        logging.info("Stage 7 complete.")

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

import logging  # Import logging
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

# Get the logger for this stage file
logger = logging.getLogger(__name__)

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
    logger.info(f"Grouped names into {len(grouped_names)} groups.")
    return grouped_names


# --- End of stages/stage3.py ---

# --- Start of stages/stage4.py ---

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


# --- End of stages/stage4.py ---

# --- Start of stages/stage5.py ---

import logging  # Import logging

# Initialize logger
logger = logging.getLogger(__name__)

def stage5_combine_overlapping_groups(refined_groups):
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


# --- End of stages/stage5.py ---

# --- Start of stages/stage6.py ---

import json
import logging
from tqdm import tqdm

from stages.utils import UserMessage, SystemMessage, get_generator

# Initialize logger
logger = logging.getLogger(__name__)

def stage6_process_combined_groups_with_llm(merged_groups):
    generator = get_generator()
    final_groups = []
    unsure_groups = []
    logger.info("Processing combined groups with LLM...")
    
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
                msg = f"Error parsing LLM response for combined group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                selected_names = []
                representative_name = ''
                certainty = ''
            except Exception as e:
                msg = f"Unexpected error processing combined group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                selected_names = []
                representative_name = ''
                certainty = ''
                
            if isinstance(selected_names, list):
                selected_names = [str(name) for name in selected_names if isinstance(name, str)]
            else:
                msg = f"Expected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}"
                tqdm.write(msg)
                logger.warning(msg)
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
    
    logger.info(f"Number of final groups: {len(final_groups)}")
    logger.info(f"Number of unsure groups: {len(unsure_groups)}")
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

            Ensure the output is only the JSON object, with no additional text. Ensure all names are in lowercase.

            Example:

            Given the following group of organisation names:
            acme corporation
            acme corp
            acme inc.
            acme co.
            ace corp

            Your output should be:

            {{
            "selected_names": ["acme corporation", "acme corp", "acme inc.", "acme co."],
            "representative_name": "acme corporation",
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


# --- End of stages/stage6.py ---

# --- Start of stages/stage7.py ---

import json
import logging
from tqdm import tqdm

from stages.utils import get_generator, UserMessage, SystemMessage, perform_web_search

# Initialize logger
logger = logging.getLogger(__name__)

def stage7_process_unsure_groups_with_llm(unsure_groups, final_groups, search_method):
    generator = get_generator()
    logger.info(f"Processing unsure groups with LLM using {search_method} search...")
    
    with tqdm(total=len(unsure_groups), desc=f'Processing unsure groups with LLM using {search_method} search') as pbar:
        for group in unsure_groups:
            pbar.update(1)
            group_names = group['group_names']
            web_search_results = perform_web_search(group_names, search_method=search_method)
            response = process_unsure_group_with_llm(group_names, web_search_results, generator)
            
            try:
                result = json.loads(response)
                selected_names = result.get('selected_names', [])
                representative_name = result.get('representative_name', '')
            except json.JSONDecodeError:
                msg = f"Error parsing LLM response for unsure group. Response was: {response}"
                tqdm.write(msg)
                logger.error(msg)
                selected_names = []
                representative_name = ''
            except Exception as e:
                msg = f"Unexpected error processing unsure group: {e}"
                tqdm.write(msg)
                logger.exception(msg)
                selected_names = []
                representative_name = ''
            
            if isinstance(selected_names, list):
                selected_names = [str(name) for name in selected_names if isinstance(name, str)]
            else:
                msg = f"Expected 'selected_names' to be a list, but got {type(selected_names)}. Response was: {response}"
                tqdm.write(msg)
                logger.warning(msg)
                selected_names = []
                
            final_groups.append({
                'selected_names': selected_names,
                'representative_name': representative_name
            })
    pbar.close()
    
    logger.info(f"Total number of final groups after processing unsure groups: {len(final_groups)}")
    return final_groups

def process_unsure_group_with_llm(group_names, web_search_results, generator):
    system_message = SystemMessage(content="You are an AI assistant that helps refine groups of organization names to identify those that refer to the same organization. You have access to web search results to assist in your decision. You must output the results in the format specified by the user.")
    web_results_str = ""
    for name in group_names:
        results = web_search_results.get(name, [])
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

    Please select the names that belong to the same organization, and output them as a JSON object with two keys:
    "selected_names": an array of the names that belong to the same organization,
    "representative_name": the name that best represents that organization.

    Ensure the output is only the JSON object, with no additional text. All names should be lowercase.

    Example:

    Given the following group of organization names:
    acme corporation, acme corp, acme inc., acme co., ace corp

    And the following web search results:
    Search results for 'acme corporation':
    Title: Acme Corporation - Official Site
    URL: http://www.acmecorp.com
    Description: Welcome to Acme Corporation, the leading provider of...

    Title: Acme Corporation - Wikipedia
    URL: http://en.wikipedia.org/wiki/Acme_Corporation
    Description: Acme Corporation is a fictional company featured in...

    Search results for 'Ace Corp':
    Title: Ace Corp - Home
    URL: http://www.acecorp.com
    Description: Ace Corp specializes in...

    Your output should be:

    {{
    "selected_names": ["acme corporation", "acme corp", "acme inc.", "acme co."],
    "representative_name": "acme corporation"
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

def perform_web_search(names, num_results=3, max_retries=5, search_method='duckduckgo', api_key=None):
    if search_method == 'duckduckgo' and DDGS is None:
        logger.error("DuckDuckGo search module not available. Please install 'duckduckgo-search' or choose another search method.")
        sys.exit(1)
    
    web_search_results = {}
    for name in names:
        retries = 0
        success = False
        while retries < max_retries and not success:
            try:
                query = f'"{name}"'
                search_results = []
                if search_method == 'duckduckgo':
                    # logger.info(f"Performing DuckDuckGo search for query: {query}")
                    # Alter logging level to silence unwanted logs during search
                    original_level = logging.getLogger().level
                    logging.getLogger().setLevel(logging.CRITICAL)
                    ddgs = DDGS()
                    results = ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=num_results)
                    logging.getLogger().setLevel(original_level)
                    if results:
                        for res in results:
                            search_results.append({
                                'url': res.get('href', ''),
                                'title': res.get('title', ''),
                                'description': res.get('body', '')
                            })
                    # else:
                    #     logger.warning(f"No results found for '{name}' using DuckDuckGo.")
                else:
                    logger.error(f"Unknown search method: {search_method}")
                    sys.exit(1)
                
                web_search_results[name] = search_results
                # logger.info(f"Received {len(search_results)} results from {search_method.capitalize()} for '{name}'.")
                time.sleep(random.uniform(1, 3))  # Adjust delay as needed
                success = True
            except Exception as e:
                retries += 1
                # logger.error(f"Error during web search for '{name}': {e}. Retrying ({retries}/{max_retries})...")
                time.sleep(2 ** retries)  # Exponential backoff
        if not success:
            logger.error(f"Failed to retrieve search results for '{name}' after {max_retries} retries.")
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

