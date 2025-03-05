import os

def concatenate_files(output_filename="concatenated_output.txt"):
    main_file = "main.py"
    stages_dir = "stages"
    output_path = os.path.join(os.getcwd(), output_filename)
    
    # Ensure output file is empty before writing
    with open(output_path, "w") as outfile:
        pass
    
    def append_to_output(file_path):
        with open(output_path, "a", encoding="utf-8") as outfile, open(file_path, "r", encoding="utf-8") as infile:
            outfile.write(f"\n# --- Start of {file_path} ---\n\n")
            outfile.write(infile.read())
            outfile.write(f"\n# --- End of {file_path} ---\n\n")
    
    # Append main.py first
    if os.path.exists(main_file):
        append_to_output(main_file)
    else:
        print(f"Warning: {main_file} not found.")
    
    # Append all files in stages directory
    if os.path.isdir(stages_dir):
        for filename in sorted(os.listdir(stages_dir)):
            file_path = os.path.join(stages_dir, filename)
            if os.path.isfile(file_path):
                append_to_output(file_path)
    else:
        print(f"Warning: {stages_dir} directory not found.")
    
    print(f"Concatenation complete. Output saved in {output_filename}")

if __name__ == "__main__":
    concatenate_files()