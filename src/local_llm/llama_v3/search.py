import os
import json
import logging
import time
from tqdm import tqdm
import logging
from datetime import datetime
import sys

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join(log_dir, f"{timestamp}_search.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    logger.warning("DuckDuckGo search module not available. Install it to enable DuckDuckGo search functionality.")

# Import your existing functions and configurations
# Ensure that DDGS (DuckDuckGo Search) and perform_web_search are properly imported
# For example:
# from your_module import perform_web_search, DDGS

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def stage4_update_empty_search_results(web_search_results_file, output_file, search_method='duckduckgo'):
    logger.info(f"Reading existing web search results from {web_search_results_file}...")
    
    # Read in existing results
    with open(web_search_results_file, 'r') as f:
        web_search_results = json.load(f)
    
    # Find terms with empty results
    terms_to_update = [term for term, results in web_search_results.items() if not results]
    num_terms = len(terms_to_update)
    logger.info(f"Found {num_terms} terms with empty search results.")
    
    if num_terms == 0:
        logger.info("No terms with empty results found. Exiting.")
        return
    
    # Perform web searches for terms with empty results
    logger.info("Performing web searches for terms with empty results...")
    with tqdm(total=num_terms, desc='Performing web search on empty-result terms') as pbar:
        for term in terms_to_update:
            pbar.update(1)
            # Perform web search on the term
            result = perform_web_search([term], search_method=search_method, max_retries=20)
            # Update the web_search_results dictionary
            web_search_results[term] = result.get(term, [])
    
    # Write the updated results back to a JSON file
    with open(output_file, 'w') as f:
        json.dump(web_search_results, f, indent=2)
    logger.info(f"Updated web search results written to {output_file}.")

# Update your perform_web_search function to ensure it stores the results
def perform_web_search(names, num_results=3, max_retries=10, search_method='duckduckgo', api_key=None):
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
                
                # Perform search
                with DDGS() as ddgs:
                    results = ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=num_results)
                    results = list(results)  # Convert generator to list
                
                if results:
                    for res in results:
                        search_results.append({
                            'url': res.get('href', ''),
                            'title': res.get('title', ''),
                            'description': res.get('body', '')
                        })
                
                if search_results:
                    success = True
                    web_search_results[name] = search_results
                else:
                    logger.error(f"No results found for '{name}'. Retrying ({retries}/{max_retries})...")
                    continue
                    # time.sleep(2 ** retries)
            except Exception as e:
                retries += 1
                logger.error(f"Error during web search for '{name}': {e}. Retrying ({retries}/{max_retries})...")
                time.sleep(2 ** retries)  # Exponential backoff
        if not success:
            logger.error(f"Failed to retrieve search results for '{name}' after {retries} retries.")
            web_search_results[name] = []
    return web_search_results

# Example usage:
if __name__ == "__main__":
    # Replace 'web_search_results_stage4.json' with the path to your existing JSON file
    existing_results_file = 'results.json'
    # Specify the output file where updated results will be saved
    output_file = 'outputs/full_web_search_results.json'
    # Call the function to update empty search results
    stage4_update_empty_search_results(existing_results_file, output_file, search_method='duckduckgo')
