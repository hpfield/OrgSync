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
from stages.stage4 import stage4_perform_web_search  # Updated stage
from stages.stage5 import stage5_process_groups_with_llm
from stages.stage6 import stage6_combine_overlapping_groups  # Ensure duplicates are removed
from stages.stage7 import stage7_determine_organisation_type  # New stage
from stages.stage8 import stage8_finalize_groups  # New final stage

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, default=1, help='Stage to start from (1-8)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], default='duckduckgo', help='Method for web searching in Stage 4')
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
        # Save unique_combined_names as JSON for review
        with open(os.path.join(output_dir, 'unique_combined_names_stage2.json'), 'w') as f:
            json.dump(unique_combined_names, f, indent=2)
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
        web_search_results = stage4_perform_web_search(grouped_names, search_method=args.search_method)
        with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'w') as f:
            json.dump(web_search_results, f, indent=2)
        logging.info("Stage 4 complete.")

    # Stage 5
    if stage <= 5:
        if stage == 5 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'grouped_names_stage3.json'), 'r') as f:
                grouped_names = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        refined_groups = stage5_process_groups_with_llm(grouped_names, web_search_results)
        with open(os.path.join(output_dir, 'refined_groups_stage5.json'), 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 5 complete.")

    # Stage 6
    if stage <= 6:
        if stage == 6 and input_files:
            with open(input_files[0], 'r') as f:
                refined_groups = json.load(f)
        else:
            with open(os.path.join(output_dir, 'refined_groups_stage5.json'), 'r') as f:
                refined_groups = json.load(f)
        merged_groups = stage6_combine_overlapping_groups(refined_groups)
        with open(os.path.join(output_dir, 'merged_groups_stage6.json'), 'w') as f:
            json.dump(merged_groups, f, indent=2)
        logging.info("Stage 6 complete.")

    # Stage 7
    if stage <= 7:
        if stage == 7 and input_files:
            with open(input_files[0], 'r') as f:
                merged_groups = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'merged_groups_stage6.json'), 'r') as f:
                merged_groups = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        groups_with_types = stage7_determine_organisation_type(merged_groups, web_search_results)
        with open(os.path.join(output_dir, 'groups_with_types_stage7.json'), 'w') as f:
            json.dump(groups_with_types, f, indent=2)
        logging.info("Stage 7 complete.")

    # Stage 8
    if stage <= 8:
        if stage == 8 and input_files:
            with open(input_files[0], 'r') as f:
                groups_with_types = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'groups_with_types_stage7.json'), 'r') as f:
                groups_with_types = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage4.json'), 'r') as f:
                web_search_results = json.load(f)
        final_groups = stage8_finalize_groups(groups_with_types, web_search_results)
        with open(os.path.join(output_dir, 'final_groups_stage8.json'), 'w') as f:
            json.dump(final_groups, f, indent=2)
        logging.info("Stage 8 complete.")

if __name__ == '__main__':
    main()
