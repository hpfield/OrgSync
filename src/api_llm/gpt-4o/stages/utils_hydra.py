import os
import sys
import logging
from pathlib import Path
import hydra
from omegaconf import DictConfig, OmegaConf
from hydra.utils import get_original_cwd

logger = logging.getLogger(__name__)

# Load Hydra configuration with a fallback to a local override file
@hydra.main(config_path="../../cfg/llm_utils", config_name="llm_utils", version_base=None)
def load_config(cfg: DictConfig):
    """
    Loads the base configuration from the global config file.
    If a local override file exists, it applies the overrides.
    """
    script_dir = Path(__file__).parent  # Directory where this script is located
    local_override_path = script_dir / "llm_utils_local.yaml"

    if local_override_path.exists():
        logger.info(f"Loading local override config from {local_override_path}")
        local_cfg = OmegaConf.load(local_override_path)
        cfg = OmegaConf.merge(cfg, local_cfg)  # Merge local overrides
    else:
        logger.info("No local override config found, using base config.")

    return cfg

# Load the final configuration with overrides
config = load_config()

# Determine the project root based on the location of this file
# utils.py is at: OrgSync/src/local_llm/llama_v3/stages/utils.py
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # Go up 4 levels

# Access model configurations
MODELS_DIR = PROJECT_ROOT / config.models_dir
DEFAULT_CKPT_DIR = config.default_ckpt_dir
TOKENIZER_PATH = MODELS_DIR / config.tokenizer_subpath

# Access LLM-specific parameters
MAX_SEQ_LEN = config.llm.max_seq_len
MAX_BATCH_SIZE = config.llm.max_batch_size
MODEL_PARALLEL_SIZE = config.llm.model_parallel_size

# Access web search settings
SEARCH_METHOD = config.search.default_method
NUM_RESULTS = config.search.num_results
MAX_RETRIES = config.search.max_retries
PAUSE_AFTER_N_SEARCHES = config.search.pause_after_n_searches
PAUSE_DURATION = config.search.pause_duration

# Access OpenAI API key (if used)
OPENAI_API_KEY = config.openai.api_key

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

def perform_web_search(names, num_results=3, max_retries=5, search_method='duckduckgo', api_key=None):
    if search_method == 'duckduckgo' and DDGS is None:
        logger.error("DuckDuckGo search module not available.")
        sys.exit(1)

    web_search_results = {}
    search_count = 0  # Counter to track the number of searches

    for name in names:
        search_count += 1  # Increment the search count
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
                time.sleep(64 * retries)
                
        if not success:
            logger.error(f"Failed to retrieve search results for '{name}' after {retries} retries.")
            web_search_results[name] = []
        else:
            web_search_results[name] = search_results

        # Pause for one minute if the search count is a multiple of 20
        if (search_count +1) % 20 == 0 and search_method=='duckduckgo':
            logger.info(f"Pausing for 1 minute after {search_count} searches...")
            time.sleep(60)

    return web_search_results
