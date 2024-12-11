import os

# Define file paths
current_dir = os.getcwd()
stages_dir = os.path.join(current_dir, "stages")
output_file = os.path.join(current_dir, "concatenated.py")

# List of files to concatenate
files_to_concatenate = [
    "main.py",
] + [f"stages/stage{n}.py" for n in range(1, 8)] + ["stages/utils.py"]

# Open the output file in write mode
with open(output_file, "w") as outfile:
    for file_name in files_to_concatenate:
        file_path = os.path.join(current_dir, file_name)
        
        # Check if the file exists
        if os.path.exists(file_path):
            # Write a comment with the file name
            outfile.write(f"# --- Start of {file_name} ---\n\n")
            
            # Write the contents of the file
            with open(file_path, "r") as infile:
                outfile.write(infile.read())
            
            # Write a newline for separation
            outfile.write(f"\n\n# --- End of {file_name} ---\n\n")
        else:
            print(f"Warning: {file_name} not found and will be skipped.")

print(f"Files have been concatenated into {output_file}")
