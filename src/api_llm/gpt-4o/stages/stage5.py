import logging
import json
import os
from tqdm import tqdm
from stages.utils import perform_web_search

logger = logging.getLogger(__name__)

def stage5_perform_web_search(grouped_names, all_names_and_items, search_method='duckduckgo', num_results=3, output_dir='outputs'):
    """
    - Maintains a rolling database of all web searches in 'all_web_search_results.json'.
    - For the given search_method, only fetch new results if we have < num_results for that name (or it's absent).
    - Returns the entire dictionary, but the pipeline typically uses only the sub-dict for the active method.
    
    Modification:
      - Use the postcode from all_names_and_items to form the search query as '{name} {postcode}'
    """

    if search_method == 'duckduckgo':
        logger.info(f"Due to rate limits, the program will wait for 60 seconds every 20 searches.")

    # Path to the rolling DB
    rolling_db_path = os.path.join(output_dir, 'all_web_search_results.json')

    # Load existing DB if it exists; else initialize
    if os.path.exists(rolling_db_path):
        with open(rolling_db_path, 'r') as f:
            all_web_search_results = json.load(f)
        logger.info(f"Loaded existing web search DB from {rolling_db_path}")
    else:
        all_web_search_results = {}
        logger.info("Initializing new web search DB.")

    # Ensure we have a sub-dict for this search method
    if search_method not in all_web_search_results:
        logger.info(f"Couldn't find any previous search results using {search_method}")
        all_web_search_results[search_method] = {}

    # Pre-process all_names_and_items to build a lookup of normalized name -> postcode
    postcode_lookup = {}
    for entry in all_names_and_items:
        key = entry["combined_name"].lower()
        # Use the first postcode encountered for this name
        if key not in postcode_lookup:
            postcode_lookup[key] = entry["postcode"]

    # Extract all names from grouped_names
    unique_names = set()
    for rep_name, info in grouped_names.items():
        unique_names.add(rep_name)
        for nm in info["matched_names"]:
            unique_names.add(nm)

    # We'll gather a list of names that need searching
    names_to_search = []
    for name in unique_names:
        existing_results = all_web_search_results[search_method].get(name, [])
        # If we have fewer than num_results, we do a fresh search
        if len(existing_results) < num_results:
            names_to_search.append(name)

    logger.info(f"{len(names_to_search)} out of {len(unique_names)} names need new web searches.")

    # Perform the new/updated searches
    for name in tqdm(names_to_search, desc='Performing new web searches'):
        # Look up the postcode for the name (using a case-insensitive key)
        normalized_name = name.lower()
        postcode = postcode_lookup.get(normalized_name, "").strip()
        # Build the query with the postcode if available
        if postcode:
            query = f"{name} {postcode}"
        else:
            query = name

        try:
            # Perform search with the constructed query
            new_results_dict = perform_web_search([query], num_results=num_results, search_method=search_method)
            # The results are expected to be in the dict with the key as our query
            found = new_results_dict.get(query, [])
            # Update the DB entry using the original name as the key
            all_web_search_results[search_method][name] = found
        except Exception as e:
            logger.error(f"Error searching for '{name}': {e}")
            # Keep old results if something fails

    # Save the updated rolling DB
    with open(rolling_db_path, 'w') as f:
        json.dump(all_web_search_results, f, indent=2)
    logger.info(f"Updated rolling DB saved to {rolling_db_path}")

    return all_web_search_results
