import pickle
import os
import argparse
import logging
import json
from tqdm import tqdm

def setup_logging():
    """Set up the logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_pickle_file(file_path):
    """
    Load a pickle file and return its contents.

    Parameters:
        file_path (str): The path to the pickle file.

    Returns:
        dict or list: The deserialized contents of the pickle file.
    """
    if not os.path.exists(file_path):
        logging.error(f"The file '{file_path}' does not exist.")
        return None

    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            logging.info(f"Successfully loaded data from '{file_path}'.")
            return data
    except Exception as e:
        logging.error(f"An error occurred while loading the pickle file: {e}")
        return None

def save_to_json(data, output_path):
    """
    Save data to a JSON file.

    Parameters:
        data (dict or list): The data to be saved.
        output_path (str): The path where the JSON file will be saved.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logging.info(f"Data successfully saved to JSON file at '{output_path}'.")
    except Exception as e:
        logging.error(f"An error occurred while saving to JSON file: {e}")

def count_no_results(web_search_results):
    """
    Count how many names returned no results.

    Parameters:
        web_search_results (dict): The dictionary containing web search results.

    Returns:
        int: The count of names with no results.
    """
    no_result_count = 0
    total_names = 0

    for unique_name, results in tqdm(web_search_results.items(), desc="Counting no results"):
        if isinstance(results, dict):
            # If results are in a dictionary format
            for name, result in results.items():
                total_names += 1
                if not result:
                    no_result_count += 1
        elif isinstance(results, list):
            # If results are in a list format
            for result in results:
                total_names += 1
                if not result:
                    no_result_count += 1
        else:
            logging.warning(f"Unexpected data type for '{unique_name}': {type(results)}")

    return no_result_count, total_names

def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Read a web_search_results_stage4.pkl file, output its contents to a JSON file, and report how many names returned no results.'
    )
    parser.add_argument(
        'pkl_file',
        type=str,
        help='Path to the web_search_results_stage4.pkl file.'
    )
    parser.add_argument(
        '--output_json',
        type=str,
        default='web_search_results_stage4.json',
        help='Path for the output JSON file. Defaults to "web_search_results_stage4.json" in the current directory.'
    )
    return parser.parse_args()

def main():
    """Main function to execute the script."""
    setup_logging()
    args = parse_arguments()
    pkl_file_path = args.pkl_file
    output_json_path = args.output_json

    logging.info(f"Attempting to load pickle file: {pkl_file_path}")
    web_search_results = load_pickle_file(pkl_file_path)

    if web_search_results is not None:
        logging.info("Saving web search results to JSON file.")
        save_to_json(web_search_results, output_json_path)

        logging.info("Counting how many names returned no results.")
        no_results, total_names = count_no_results(web_search_results)
        logging.info(f"Total names processed: {total_names}")
        logging.info(f"Number of names with no results: {no_results}")
        print(f"\nSummary:\nTotal names processed: {total_names}\nNumber of names with no results: {no_results}\n")
    else:
        logging.error("Failed to load web search results. Exiting.")

if __name__ == "__main__":
    main()
