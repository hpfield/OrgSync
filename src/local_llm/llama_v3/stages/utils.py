import os
import sys
import time
import random
import logging
from pathlib import Path
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

def configure_environment():
    sys.path.append(str(MODELS_DIR.parent))
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'

# Try importing search modules and model
try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None
    logger.warning("Google search module not available.")

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

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    logger.warning("DuckDuckGo search module not available.")

logger.info("Initializing the Llama generator.")
generator = Llama.build(
    ckpt_dir=str(DEFAULT_CKPT_DIR),
    tokenizer_path=str(TOKENIZER_PATH),
    max_seq_len=8192,
    max_batch_size=4,
    model_parallel_size=None,
)

def get_generator():
    return generator

def perform_web_search(names, num_results=5, max_retries=7, search_method='duckduckgo', api_key=None):
    if search_method == 'duckduckgo' and DDGS is None:
        logger.error("DuckDuckGo search module not available.")
        sys.exit(1)
    
    web_search_results = {}
    for name in names:
        retries = 0
        success = False
        while retries < max_retries and not success:
            try:
                query = f'"{name}"'
                search_results = []
                ddgs = DDGS()
                results = ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=num_results)
                
                if results:
                    for res in results:
                        search_results.append({
                            'url': res.get('href', ''),
                            'title': res.get('title', ''),
                            'description': res.get('body', '')
                        })
                
                success = True
                
            except Exception as e:
                retries += 1
                logger.error(f"Error during web search for '{name}': {e}. Retrying ({retries}/{max_retries})...")
                time.sleep(2 ** retries)
                
        if not success:
            logger.error(f"Failed to retrieve search results for '{name}' after {retries} retries.")
            web_search_results[name] = []
        else:
            web_search_results[name] = search_results

    return web_search_results
