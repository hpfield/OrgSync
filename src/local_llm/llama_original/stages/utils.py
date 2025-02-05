import os
import sys
import time
import random
import logging
from pathlib import Path
import requests
import yaml

logger = logging.getLogger(__name__)

# Determine the project root based on the location of this file
# utils.py is at: OrgSync/src/local_llm/llama_v3/stages/utils.py
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # Go up 4 levels
CONFIG_PATH = PROJECT_ROOT / 'cfg' / 'config.yaml'

# Load the configuration
with open(CONFIG_PATH, 'r') as f:
    config_data = yaml.safe_load(f)

MODELS_DIR = Path(config_data['models_dir']).resolve()
DEFAULT_CKPT_DIR = config_data['default_ckpt_dir']
TOKENIZER_PATH = MODELS_DIR / config_data['tokenizer_subpath']

# Add the 'models' directory to sys.path
sys.path.append(str(MODELS_DIR.parent))

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
