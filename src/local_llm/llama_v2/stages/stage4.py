import logging
from tqdm import tqdm

from stages.utils import perform_web_search  # Import the web search utility

def stage4_perform_web_search(grouped_names, search_method='duckduckgo'):
    logger = logging.getLogger(__name__)
    logger.info("Performing web search on grouped names...")
    web_search_results = {}
    num_groups = len(grouped_names)
    with tqdm(total=num_groups, desc='Performing web search on grouped names') as pbar:
        for unique_name, matched_names in grouped_names.items():
            pbar.update(1)
            all_names = [unique_name] + matched_names
            # Perform web search on all names in the group
            results = perform_web_search(all_names, search_method=search_method)
            # Store results for each name
            web_search_results.update(results)
    logger.info(f"Completed web search for {num_groups} groups.")
    return web_search_results
