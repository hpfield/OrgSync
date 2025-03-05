import json
import os
import sys

# Path to the human labelled data file
SAVE_FILE = "outputs/human_labelled_data.json"

def main():
    if not os.path.exists(SAVE_FILE):
        print(f"Error: File {SAVE_FILE} does not exist.")
        sys.exit(1)

    with open(SAVE_FILE, "r") as f:
        try:
            labeled_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading JSON from {SAVE_FILE}: {e}")
            sys.exit(1)

    # Filter out entries that have been labelled (label not None)
    labelled_entries = [entry for entry in labeled_data if entry.get("label") is not None]
    total_labelled = len(labelled_entries)

    if total_labelled == 0:
        print("No entries have been labelled yet.")
        sys.exit(0)

    # Count how many labelled entries are True
    true_count = sum(1 for entry in labelled_entries if entry.get("label") is True)

    precision = true_count / total_labelled
    print(f"Total labelled entries: {total_labelled}")
    print(f"Entries labelled True: {true_count}")
    print(f"Precision: {precision:.2%}")

if __name__ == "__main__":
    main()
