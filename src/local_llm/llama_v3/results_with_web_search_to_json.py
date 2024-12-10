# Save this script as generate_final_output.py in the root directory where main.py is located

import os
import json
import logging

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Define paths to the necessary files
    output_dir = 'outputs'  # Adjust if your outputs are in a different directory
    stage8_file = os.path.join(output_dir, 'final_groups_stage8.json')  # Output from stage 8
    stage4_file = os.path.join(output_dir, 'web_search_results_stage4.json')  # Output from stage 4
    final_output_file = os.path.join(output_dir, 'final_output_with_context.json')  # Final output file

    # Check if the required files exist
    if not os.path.exists(stage8_file):
        logger.error(f"Stage 8 output file not found: {stage8_file}")
        return
    if not os.path.exists(stage4_file):
        logger.error(f"Stage 4 output file not found: {stage4_file}")
        return

    # Load the data from stage 8
    with open(stage8_file, 'r') as f:
        groups_with_types = json.load(f)

    # Load the web search results from stage 4
    with open(stage4_file, 'r') as f:
        web_search_results = json.load(f)

    # Filter groups to only those with more than one name
    filtered_groups = [group for group in groups_with_types if len(group.get('selected_names', [])) > 1]
    logger.info(f"Filtered down to {len(filtered_groups)} groups with more than one name.")

    # Prepare the final output data
    final_output = []
    for group in filtered_groups:
        group_names = group.get('selected_names', [])
        organisation_type = group.get('organisation_type', '')

        # Attach web search results for each name in the group
        names_with_search_results = []
        for name in group_names:
            # The names in web_search_results might have different casing or punctuation
            # Normalize the names to improve matching
            normalized_name = name.lower().strip()
            search_results = web_search_results.get(normalized_name, [])

            if not search_results:
                # Try to find the name in web_search_results using a case-insensitive match
                for key in web_search_results.keys():
                    if key.lower().strip() == normalized_name:
                        search_results = web_search_results[key]
                        break

            names_with_search_results.append({
                'name': name,
                'web_search_results': search_results
            })

        final_output.append({
            'names': group_names,
            'organisation_type': organisation_type,
            'names_with_search_results': names_with_search_results
        })

    # Save the final output to a JSON file
    with open(final_output_file, 'w') as f:
        json.dump(final_output, f, indent=2)

    logger.info(f"Final output saved to {final_output_file}")

if __name__ == '__main__':
    main()
