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

def perform_web_search(names, num_results=3, max_retries=5, search_method='duckduckgo', api_key=None):
    if search_method == 'duckduckgo' and DDGS is None:
        logger.error("DuckDuckGo search module not available. Please install 'duckduckgo-search' or choose another search method.")
        sys.exit(1)
    
    web_search_results = {}
    for name in names:
        retries = 0
        success = False
        while retries < max_retries and not success:
            original_level = logging.getLogger().level  # Get original level at the start
            try:
                query = f'"{name}"'
                search_results = []
                
                # Temporarily suppress logs
                logging.getLogger().setLevel(logging.CRITICAL)
                
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
                
            finally:
                # Restore logging level no matter what
                logging.getLogger().setLevel(original_level)
                
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
