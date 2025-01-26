import logging
from tqdm import tqdm
from stages.utils import perform_web_search

logger = logging.getLogger(__name__)

def stage5_perform_web_search(grouped_names, search_method='duckduckgo'):
    logger.info("Extracting unique names from grouped names for web search...")

    # Collect all unique names from the groups
    unique_names = set()
    for unique_name, matched_names in grouped_names.items():
        unique_names.add(unique_name)
        unique_names.update(matched_names)

    unique_names = sorted(unique_names)
    num_names = len(unique_names)

    # Log the number of web searches needed
    logger.info(f"Number of web searches needed: {num_names}")

    # Perform web search on each unique name
    web_search_results = {}
    with tqdm(total=num_names, desc='Performing web search') as pbar:
        for name in unique_names:
            pbar.update(1)
            results = perform_web_search([name], search_method=search_method)
            web_search_results[name] = results.get(name, [])

    logger.info(f"Completed web search for {num_names} unique names.")
    return web_search_results
