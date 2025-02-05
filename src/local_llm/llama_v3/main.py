import argparse
import sys
import os
import pickle
import json
import logging
from datetime import datetime

# Import stage functions
from stages.stage1 import stage1_load_and_preprocess_data
from stages.stage2 import stage2_identify_identical_names
from stages.stage3 import stage3_vectorize_names
from stages.stage4 import stage4_group_similar_names
from stages.stage5 import stage5_perform_web_search
from stages.stage6 import stage6_process_groups_with_llm
from stages.stage7 import stage7_combine_overlapping_groups
from stages.stage8 import stage8_determine_organisation_type
from stages.stage9 import stage9_finalize_groups

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, default=1, help='Stage to start from (1-9)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], default='duckduckgo',
                        help='Method for web searching in Stage 5')
    parser.add_argument('--input', nargs='+', help='Input file(s) for the starting stage')
    parser.add_argument('--output-dir', type=str, default='outputs', help='Output directory to save results')
    return parser.parse_args()

def setup_logging(stage):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    from datetime import datetime
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

    # ---------------------------
    # Stage 1: Load and preprocess
    # ---------------------------
    if stage <= 1:
        preprocessed_data = stage1_load_and_preprocess_data()
        #! for testing
        preprocessed_data = [x for x in preprocessed_data if x['dataset'] == 'cordis'][:50] + [x for x in preprocessed_data if x['dataset'] == 'gtr'][:50]
        with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'wb') as f:
            pickle.dump(preprocessed_data, f)
        logging.info("Stage 1 complete.")

    # ---------------------------
    # Stage 2: Identify identical names
    # ---------------------------
    if stage <= 2:
        if stage == 2 and input_files:
            with open(input_files[0], 'rb') as f:
                preprocessed_data = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'rb') as f:
                preprocessed_data = pickle.load(f)
        # Identify identical names
        identical_name_groups = stage2_identify_identical_names(preprocessed_data)
        # Save them for later assimilation
        with open(os.path.join(output_dir, 'identical_name_groups_stage2.json'), 'w') as f:
            json.dump(identical_name_groups, f, indent=2)
        logging.info("Stage 2 complete.")

    # ---------------------------
    # Stage 3: Vectorize names
    # ---------------------------
    if stage <= 3:
        if stage == 3 and input_files:
            with open(input_files[0], 'rb') as f:
                preprocessed_data = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'rb') as f:
                preprocessed_data = pickle.load(f)

        vectorizer, name_vectors, unique_entries = stage3_vectorize_names(preprocessed_data)
        with open(os.path.join(output_dir, 'vectorizer_stage3.pkl'), 'wb') as f:
            pickle.dump(vectorizer, f)
        with open(os.path.join(output_dir, 'name_vectors_stage3.pkl'), 'wb') as f:
            pickle.dump(name_vectors, f)
        with open(os.path.join(output_dir, 'unique_entries_stage3.pkl'), 'wb') as f:
            pickle.dump(unique_entries, f)
        # Save unique_entries as JSON for review
        with open(os.path.join(output_dir, 'unique_entries_stage3.json'), 'w') as f:
            json.dump(unique_entries, f, indent=2)
        logging.info("Stage 3 complete.")

    # ---------------------------
    # Stage 4: Group similar names
    # ---------------------------
    if stage <= 4:
        if stage == 4 and input_files:
            with open(input_files[0], 'rb') as f:
                vectorizer = pickle.load(f)
            with open(input_files[1], 'rb') as f:
                name_vectors = pickle.load(f)
            with open(input_files[2], 'rb') as f:
                unique_entries = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'vectorizer_stage3.pkl'), 'rb') as f:
                vectorizer = pickle.load(f)
            with open(os.path.join(output_dir, 'name_vectors_stage3.pkl'), 'rb') as f:
                name_vectors = pickle.load(f)
            with open(os.path.join(output_dir, 'unique_entries_stage3.pkl'), 'rb') as f:
                unique_entries = pickle.load(f)

        grouped_names = stage4_group_similar_names(
            vectorizer, name_vectors, unique_entries, threshold=args.threshold
        )
        with open(os.path.join(output_dir, 'grouped_names_stage4.json'), 'w') as f:
            json.dump(grouped_names, f, indent=2)
        logging.info("Stage 4 complete.")

    # ---------------------------
    # Stage 5: Perform web search
    # ---------------------------
    if stage <= 5:
        if stage == 5 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
        else:
            with open(os.path.join(output_dir, 'grouped_names_stage4.json'), 'r') as f:
                grouped_names = json.load(f)

        web_search_results = stage5_perform_web_search(
            grouped_names, search_method=args.search_method
        )
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'w') as f:
            json.dump(web_search_results, f, indent=2)
        logging.info("Stage 5 complete.")

    # ---------------------------
    # Stage 6: Process groups with LLM
    # ---------------------------
    if stage <= 6:
        if stage == 6 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'grouped_names_stage4.json'), 'r') as f:
                grouped_names = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
                web_search_results = json.load(f)

        refined_groups = stage6_process_groups_with_llm(grouped_names, web_search_results)
        with open(os.path.join(output_dir, 'refined_groups_stage6.json'), 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 6 complete.")

    # ---------------------------
    # Stage 7: Combine overlapping groups
    # ---------------------------
    if stage <= 7:
        if stage == 7 and input_files:
            with open(input_files[0], 'r') as f:
                refined_groups = json.load(f)
        else:
            with open(os.path.join(output_dir, 'refined_groups_stage6.json'), 'r') as f:
                refined_groups = json.load(f)

        merged_groups = stage7_combine_overlapping_groups(refined_groups)
        with open(os.path.join(output_dir, 'merged_groups_stage7.json'), 'w') as f:
            json.dump(merged_groups, f, indent=2)
        logging.info("Stage 7 complete.")

    # ---------------------------
    # Stage 8: Determine organisation type
    # ---------------------------
    if stage <= 8:
        if stage == 8 and input_files:
            with open(input_files[0], 'r') as f:
                merged_groups = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'merged_groups_stage7.json'), 'r') as f:
                merged_groups = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
                web_search_results = json.load(f)

        groups_with_types = stage8_determine_organisation_type(merged_groups, web_search_results)
        with open(os.path.join(output_dir, 'groups_with_types_stage8.json'), 'w') as f:
            json.dump(groups_with_types, f, indent=2)
        logging.info("Stage 8 complete.")

    # ---------------------------
    # Stage 9: Finalize groups
    # ---------------------------
    if stage <= 9:
        if stage == 9 and input_files:
            with open(input_files[0], 'r') as f:
                groups_with_types = json.load(f)
            with open(input_files[1], 'r') as f:
                web_search_results = json.load(f)
        else:
            with open(os.path.join(output_dir, 'groups_with_types_stage8.json'), 'r') as f:
                groups_with_types = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
                web_search_results = json.load(f)

        # Also load the identical_name_groups from Stage 2 to ensure we can link them
        with open(os.path.join(output_dir, 'identical_name_groups_stage2.json'), 'r') as f:
            identical_name_groups = json.load(f)

        final_groups = stage9_finalize_groups(groups_with_types, web_search_results, identical_name_groups)

        with open(os.path.join(output_dir, 'final_groups_stage9.json'), 'w') as f:
            json.dump(final_groups, f, indent=2)
        logging.info("Stage 9 complete.")

if __name__ == '__main__':
    main()
