import argparse
import sys
import os
import pickle
import json
import logging
from datetime import datetime
import asyncio

# Import stage functions
from stages.stage0 import stage0_check_new_data
from stages.stage1 import stage1_load_and_preprocess_data
from stages.stage2 import stage2_identify_identical_names
from stages.stage3 import stage3_vectorize_names
from stages.stage4 import stage4_group_similar_names
from stages.stage5 import stage5_perform_web_search
from stages.stage6 import stage6_process_groups_with_llm
from stages.stage7 import stage7_combine_overlapping_groups
from stages.stage8 import stage8_determine_organisation_type
from stages.stage9 import stage9_finalize_groups
from stages.stage10 import stage10_refine_groups_with_llm
from stages.stage11 import stage11_capitalize_group_names

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, default=0, help='Stage to start from (0-11)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], default='duckduckgo',
                        help='Method for web searching in Stage 5')
    parser.add_argument('--input', nargs='+', help='Input file(s) for the starting stage')
    parser.add_argument('--output-dir', type=str, default='outputs', help='Output directory to save results')
    parser.add_argument('--num-search-results', type=int, default=5,
                        help='Number of web search results to retrieve for each org name')
    parser.add_argument('--data-mode', type=str, choices=['all', 'new'], default='all',
                        help='Run pipeline over all data or only new data')
    return parser.parse_args()

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
    return timestamp

def main():
    args = parse_arguments()
    stage = args.stage
    input_files = args.input
    output_dir = args.output_dir
    timestamp = setup_logging(stage)

    os.makedirs(output_dir, exist_ok=True)

    # -----------
    # Stage 0: Load data
    # -----------
    if stage <= 0:
        repo_root = os.path.abspath(os.path.join(__file__, '../../../..'))
        logging.info(f'Repo root: {repo_root}')
        data_dir = os.path.join(repo_root, "data", "raw")
        new_data_path = os.path.join(repo_root, data_dir, "uk_data.json")
        old_data_path = os.path.join(repo_root, data_dir, "old_uk_data.json")
        merged_data_path = os.path.join(repo_root, data_dir, "merged_uk_data.json")
        new_entries_path = os.path.join(repo_root, data_dir, "new_entries.json")
        data_history_path = os.path.join(repo_root, data_dir, timestamp)
        merged_data = stage0_check_new_data(
            new_data_path,
            old_data_path,
            merged_data_path,
            new_entries_path
        )
        with open(os.path.join(output_dir, 'stage0_merged_data.pkl'), 'wb') as f:
            pickle.dump(merged_data, f)
        # Save data history
        os.makedirs(data_history_path, exist_ok=True)
        # Copy the old uk data to history log
        old_data_history_path = os.path.join(data_history_path, f"old_uk_data.json")
        os.system(f"cp {old_data_path} {old_data_history_path}")
        # Copy the new uk data to history log
        new_data_history_path = os.path.join(data_history_path, f"uk_data.json")
        os.system(f"cp {new_data_path} {new_data_history_path}")
        # Merged data becomes new old data
        os.system(f"cp {merged_data_path} {old_data_path}")
        logging.info("Stage 0 complete.")

    # ---------------------------
    # Stage 1: Load and preprocess data
    # ---------------------------
    if stage <= 1:
        if stage == 1 and input_files:
            with open(input_files[0], 'rb') as f:
                merged_data = pickle.load(f)
        else:
            with open(os.path.join(output_dir, 'stage0_merged_data.pkl'), 'rb') as f:
                merged_data = pickle.load(f)

        preprocessed_data = stage1_load_and_preprocess_data(merged_data)
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

        identical_name_groups = stage2_identify_identical_names(preprocessed_data)
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

        # For new data, filter groups to only include those with new entries;
        # for "all", pass along all groups.
        if args.data_mode == "new":
            new_data_groups = {}
            for rep_name, group_info in grouped_names.items():
                items = group_info["items"]
                if any(item.get("is_new", False) for item in items):
                    new_data_groups[rep_name] = group_info
            logging.info(f"Created {len(new_data_groups)} groups with new data.")
            if len(new_data_groups) == 0:
                logging.info("No groups contain new data. Exiting pipeline.")
                sys.exit(0)
            grouped_names_stage4_path = os.path.join(output_dir, 'grouped_names_stage4_new_data_only.json')
            with open(grouped_names_stage4_path, 'w') as f:
                json.dump(new_data_groups, f, indent=2)
        else:
            grouped_names_stage4_path = os.path.join(output_dir, 'grouped_names_stage4_all_data.json')
            with open(grouped_names_stage4_path, 'w') as f:
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
            with open(grouped_names_stage4_path, 'r') as f:
                grouped_names = json.load(f)
            with open(os.path.join(output_dir, 'unique_entries_stage3.json'), 'r') as f:
                unique_entries = json.load(f)

        all_web_results = stage5_perform_web_search(
            grouped_names,
            unique_entries,
            search_method=args.search_method,
            num_results=args.num_search_results,
            output_dir=output_dir
        )

        sub_db = all_web_results.get(args.search_method, {})
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'w') as f:
            json.dump(sub_db, f, indent=2)
        logging.info("Stage 5 complete.")

    # ---------------------------
    # Stage 6: Process groups with LLM
    # ---------------------------
    if stage <= 6:
        refined_groups_out = os.path.join(output_dir, 'refined_groups_stage6.json')
        if stage == 6 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
            with open(input_files[1], 'r') as f:
                method_sub_db = json.load(f)
        else:
            if args.data_mode == "new":
                with open(os.path.join(output_dir, 'grouped_names_stage4_new_data_only.json'), 'r') as f:
                    grouped_names = json.load(f)
            else:
                with open(os.path.join(output_dir, 'grouped_names_stage4_all_data.json'), 'r') as f:
                    grouped_names = json.load(f)
            with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
                method_sub_db = json.load(f)

        # refined_groups = asyncio.run(stage6_process_groups_with_llm(grouped_names, method_sub_db))
        refined_groups = stage6_process_groups_with_llm(grouped_names, method_sub_db)
        with open(refined_groups_out, 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 6 complete.")

    # ---------------------------
    # Stage 7: Combine overlapping groups
    # ---------------------------
    if stage <= 7:
        refined_groups_path = os.path.join(output_dir, 'refined_groups_stage6.json')
        with open(refined_groups_path, 'r') as f:
            refined_groups = json.load(f)

        merged_groups = stage7_combine_overlapping_groups(refined_groups)
        with open(os.path.join(output_dir, 'merged_groups_stage7.json'), 'w') as f:
            json.dump(merged_groups, f, indent=2)
        logging.info("Stage 7 complete.")

    # ---------------------------
    # Stage 8: Determine organisation type
    # ---------------------------
    if stage <= 8:
        merged_groups_path = os.path.join(output_dir, 'merged_groups_stage7.json')
        with open(merged_groups_path, 'r') as f:
            merged_groups = json.load(f)
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
            method_sub_db = json.load(f)

        groups_with_types = stage8_determine_organisation_type(merged_groups, method_sub_db)
        with open(os.path.join(output_dir, 'groups_with_types_stage8.json'), 'w') as f:
            json.dump(groups_with_types, f, indent=2)
        logging.info("Stage 8 complete.")

    # ---------------------------
    # Stage 9: Finalize groups (produce formatted groups)
    # ---------------------------
    if stage <= 9:
        groups_with_types_path = os.path.join(output_dir, 'groups_with_types_stage8.json')
        with open(groups_with_types_path, 'r') as f:
            groups_with_types = json.load(f)
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
            method_sub_db = json.load(f)
        with open(os.path.join(output_dir, 'identical_name_groups_stage2.json'), 'r') as f:
            identical_name_groups = json.load(f)
        with open(os.path.join(output_dir, 'unique_entries_stage3.json'), 'r') as f:
            unique_entries = json.load(f)

        formatted_groups = stage9_finalize_groups(
            groups_with_types, method_sub_db, unique_entries
        )

        # Save as formatted groups (do not merge to rolling output yet)
        formatted_groups_path = os.path.join(output_dir, 'formatted_groups_stage9.json')
        with open(formatted_groups_path, 'w') as f:
            json.dump(formatted_groups, f, indent=2)
        logging.info("Stage 9 complete (formatted groups saved).")

    # ---------------------------
    # Stage 10: Refine groups with LLM (post-stage 9)
    # ---------------------------
    if stage <= 10:
        formatted_groups_path = os.path.join(output_dir, 'formatted_groups_stage9.json')
        with open(formatted_groups_path, 'r') as f:
            formatted_groups = json.load(f)
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
            method_sub_db = json.load(f)
        with open(os.path.join(output_dir, 'unique_entries_stage3.json'), 'r') as f:
            unique_entries = json.load(f)

        refined_groups = stage10_refine_groups_with_llm(formatted_groups, method_sub_db, unique_entries)
        refined_groups_path = os.path.join(output_dir, 'refined_groups_stage10.json')
        with open(refined_groups_path, 'w') as f:
            json.dump(refined_groups, f, indent=2)
        logging.info("Stage 10 complete.")

    # ---------------------------
    # Stage 11: Apply capitalisation to group names and merge to rolling output
    # ---------------------------
    if stage <= 11:
        refined_groups_path = os.path.join(output_dir, 'refined_groups_stage10.json')
        with open(refined_groups_path, 'r') as f:
            groups_to_capitalise = json.load(f)
        with open(os.path.join(output_dir, 'web_search_results_stage5.json'), 'r') as f:
            method_sub_db = json.load(f)
        final_groups = stage11_capitalize_group_names(groups_to_capitalise, method_sub_db)
        final_groups_path = os.path.join(output_dir, 'final_groups_stage11.json')
        with open(final_groups_path, 'w') as f:
            json.dump(final_groups, f, indent=2)
        logging.info("Stage 11 complete.")

        # Merge with rolling output (output_groups.json)
        rolling_path = os.path.join(output_dir, 'output_groups.json')
        if os.path.exists(rolling_path):
            with open(rolling_path, 'r') as f:
                old_final = json.load(f)
        else:
            old_final = {}
        old_final.update(final_groups)
        with open(rolling_path, 'w') as f:
            json.dump(old_final, f, indent=2)
        logging.info(f"Updated rolling final output at {rolling_path}.")

if __name__ == '__main__':
    main()
