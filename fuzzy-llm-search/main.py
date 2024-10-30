import argparse
import sys
import os
import pickle
import json

# Import stage functions
from stages.stage1 import stage1_load_and_preprocess_data
from stages.stage2 import stage2_vectorize_names
from stages.stage3 import stage3_group_similar_names
from stages.stage4 import stage4_process_groups_with_llm
from stages.stage5 import stage5_combine_overlapping_groups
from stages.stage6 import stage6_process_combined_groups_with_llm
from stages.stage7 import stage7_process_unsure_groups_with_llm

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process organization names in stages.')
    parser.add_argument('--stage', type=int, required=True, help='Stage to start from (1-7)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for grouping similar names')
    parser.add_argument('--search-method', type=str, choices=['google', 'duckduckgo'], required='7' in sys.argv, help='Method for web searching in Stage 7')
    parser.add_argument('--input', nargs='+', help='Input file(s) for the starting stage')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory to save results')
    return parser.parse_args()

def main():
    args = parse_arguments()
    stage = args.stage
    input_files = args.input
    output_dir = args.output_dir

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define default input/output filenames for each stage
    default_input_files = {
        2: ['preprocessed_data.pkl'],
        3: ['vectorizer.pkl', 'name_vectors.pkl', 'unique_combined_names.pkl'],
        4: ['grouped_names.json'],
        5: ['refined_groups.json'],
        6: ['merged_groups.pkl'],
        7: ['final_groups.json', 'unsure_groups.json'],
    }

    # Stage 1
    if stage <= 1:
        preprocessed_data = stage1_load_and_preprocess_data()
        # Save output
        with open(os.path.join(output_dir, 'preprocessed_data.pkl'), 'wb') as f:
            pickle.dump(preprocessed_data, f)
        print("Stage 1 complete.")

    # Stage 2
    if stage <= 2:
        if stage == 2 and input_files:
            # Load input from file
            with open(input_files[0], 'rb') as f:
                preprocessed_data = pickle.load(f)
        elif stage == 2:
            # Load default input
            with open('preprocessed_data.pkl', 'rb') as f:
                preprocessed_data = pickle.load(f)
        # Run stage 2
        vectorizer, name_vectors, unique_combined_names = stage2_vectorize_names(preprocessed_data)
        # Save outputs
        with open(os.path.join(output_dir, 'vectorizer.pkl'), 'wb') as f:
            pickle.dump(vectorizer, f)
        with open(os.path.join(output_dir, 'name_vectors.pkl'), 'wb') as f:
            pickle.dump(name_vectors, f)
        with open(os.path.join(output_dir, 'unique_combined_names.pkl'), 'wb') as f:
            pickle.dump(unique_combined_names, f)
        print("Stage 2 complete.")

    # Stage 3
    if stage <= 3:
        if stage == 3 and input_files:
            with open(input_files[0], 'rb') as f:
                vectorizer = pickle.load(f)
            with open(input_files[1], 'rb') as f:
                name_vectors = pickle.load(f)
            with open(input_files[2], 'rb') as f:
                unique_combined_names = pickle.load(f)
        elif stage == 3:
            with open('vectorizer.pkl', 'rb') as f:
                vectorizer = pickle.load(f)
            with open('name_vectors.pkl', 'rb') as f:
                name_vectors = pickle.load(f)
            with open('unique_combined_names.pkl', 'rb') as f:
                unique_combined_names = pickle.load(f)
        grouped_names = stage3_group_similar_names(vectorizer, name_vectors, unique_combined_names, threshold=args.threshold)
        # Save output
        with open(os.path.join(output_dir, 'grouped_names.json'), 'w') as f:
            json.dump(grouped_names, f, indent=2)
        print("Stage 3 complete.")

    # Stage 4
    if stage <= 4:
        if stage == 4 and input_files:
            with open(input_files[0], 'r') as f:
                grouped_names = json.load(f)
        elif stage == 4:
            with open('grouped_names.json', 'r') as f:
                grouped_names = json.load(f)
        refined_groups = stage4_process_groups_with_llm(grouped_names)
        # Save output
        with open(os.path.join(output_dir, 'refined_groups.json'), 'w') as f:
            json.dump(refined_groups, f, indent=2)
        print("Stage 4 complete.")

    # Stage 5
    if stage <= 5:
        if stage == 5 and input_files:
            with open(input_files[0], 'r') as f:
                refined_groups = json.load(f)
        elif stage == 5:
            with open('refined_groups.json', 'r') as f:
                refined_groups = json.load(f)
        merged_groups = stage5_combine_overlapping_groups(refined_groups)
        # Save output
        with open(os.path.join(output_dir, 'merged_groups.pkl'), 'wb') as f:
            pickle.dump(merged_groups, f)
        print("Stage 5 complete.")

    # Stage 6
    if stage <= 6:
        if stage == 6 and input_files:
            with open(input_files[0], 'rb') as f:
                merged_groups = pickle.load(f)
        elif stage == 6:
            with open('merged_groups.pkl', 'rb') as f:
                merged_groups = pickle.load(f)
        final_groups, unsure_groups = stage6_process_combined_groups_with_llm(merged_groups)
        # Save outputs
        with open(os.path.join(output_dir, 'final_groups.json'), 'w') as f:
            json.dump(final_groups, f, indent=2)
        with open(os.path.join(output_dir, 'unsure_groups.json'), 'w') as f:
            json.dump(unsure_groups, f, indent=2)
        print("Stage 6 complete.")

    # Stage 7
    if stage <= 7:
        if not hasattr(args, 'search_method'):
            print("Error: --search-method is required for Stage 7.")
            sys.exit(1)
        if stage == 7 and input_files:
            with open(input_files[0], 'r') as f:
                final_groups = json.load(f)
            with open(input_files[1], 'r') as f:
                unsure_groups = json.load(f)
        elif stage == 7:
            with open('final_groups.json', 'r') as f:
                final_groups = json.load(f)
            with open('unsure_groups.json', 'r') as f:
                unsure_groups = json.load(f)
        updated_final_groups = stage7_process_unsure_groups_with_llm(unsure_groups, final_groups, args.search_method)
        # Save output
        with open(os.path.join(output_dir, 'updated_final_groups.json'), 'w') as f:
            json.dump(updated_final_groups, f, indent=2)
        print("Stage 7 complete.")

if __name__ == '__main__':
    main()
