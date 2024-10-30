Usage Instructions:

You can run the script and specify the stage you want to start from using the --stage argument. For stages beyond 1, you need to provide the required input files using the --input argument.


Here is the Mermaid code:

```mermaid
flowchart TB
    %% Main Flow Subgraph on the left
    subgraph MainFlow [Main Flow]
        direction LR
        S1[Stage 1:<br>**Load and Preprocess Data**] 
        --> S2[Stage 2:<br>**Vectorize Names**]
        S2 --> S3[Stage 3:<br>**Group Similar Names**]
        S3 --> S4[Stage 4:<br>**Process Groups with LLM**]
        S4 --> S5[Stage 5:<br>**Combine Overlapping Groups**]
        S5 --> S6[Stage 6:<br>**Process Combined Groups with LLM**]
        S6 --> S7[Stage 7:<br>**Process Unsure Groups with LLM Using Web Search**]
    end
    
    %% Details Subgraph on the right
    subgraph Details [Details]
        direction LR
        D1["**Stage 1 Details**<br><br>**Input:** Raw organization names<br><br>**Process:**<br>- Load data from sources<br>- Clean and normalize names<br><br>**Output:** Cleaned organization names"]
        D2["**Stage 2 Details**<br><br>**Input:** Cleaned organization names<br><br>**Process:**<br>- Convert names to numerical vectors<br>- Use techniques like TF-IDF or embeddings<br><br>**Output:** Vector representations of names"]
        D3["**Stage 3 Details**<br><br>**Input:** Vector representations<br><br>**Process:**<br>- Compute similarities between vectors<br>- Cluster names into groups of similar organizations<br><br>**Output:** Groups of similar organization names"]
        D4["**Stage 4 Details**<br><br>**Input:** Groups of similar names<br><br>**Process:**<br>- Use a Large Language Model (LLM)<br>- Refine groups and confirm name similarities<br><br>**Output:** Refined groups of organization names"]
        D5["**Stage 5 Details**<br><br>**Input:** Refined groups<br><br>**Process:**<br>- Identify overlapping groups<br>- Merge groups to consolidate variations<br><br>**Output:** Merged groups of organization names"]
        D6["**Stage 6 Details**<br><br>**Input:** Merged groups<br><br>**Process:**<br>- Re-evaluate merged groups with LLM<br>- Further refine groupings<br><br>**Output:** Final groups and unsure groups"]
        D7["**Stage 7 Details**<br><br>**Input:** Unsure groups<br><br>**Process:**<br>- Perform web searches for additional context<br>- Use LLM with web data to finalize decisions<br><br>**Output:** Finalized organization groups"]
    end
    
    %% Connect main stages to details
    S1 --> D1
    S2 --> D2
    S3 --> D3
    S4 --> D4
    S5 --> D5
    S6 --> D6
    S7 --> D7
    
    %% Styling
    classDef stage fill:#1f77b4,stroke:#333,stroke-width:2px,color:#fff
    classDef details fill:#d9edf7,stroke:#333,stroke-width:1px,color:#000
    class S1,S2,S3,S4,S5,S6,S7 stage
    class D1,D2,D3,D4,D5,D6,D7 details

    

```mermaid
graph TD
    S1[Stage 1: Load and Preprocess Data] --> S2[Stage 2: Vectorize Names]
    S2 --> S3[Stage 3: Group Similar Names Using K-Nearest Neighbours]
    S3 --> S4[Stage 4: Filter Groups with LLM]
    S4 --> S5[Stage 5: Combine Groups With Overlapping Data]
    S5 --> S6[Stage 6: Process Combined Groups with LLM]
    S6 --> S7[Stage 7: Further Process Groups with LLM Using Web Search]
```
For example:

To start from Stage 1:

bash
Copy code
python main.py --stage 1 --output-dir outputs --search-method google
To start from Stage 2, using the output from Stage 1 (preprocessed_data.pkl):

bash
Copy code
python main.py --stage 2 --input preprocessed_data.pkl
To start from Stage 3, using the outputs from Stage 2:

bash
Copy code
python main.py --stage 3 --input vectorizer.pkl name_vectors.pkl unique_combined_names.pkl --output-dir outputs
To start from Stage 4, using the output from Stage 3 (grouped_names.json):

bash
Copy code
python script.py --stage 4 --input grouped_names.json
To start from Stage 5, using the output from Stage 4 (refined_groups.json):

bash
Copy code
python main.py --stage 5 --input refined_groups.json --output-dir outputs
To start from Stage 6, using the output from Stage 5 (merged_groups.pkl):

bash
Copy code
python script.py --stage 6 --input merged_groups.pkl
To start from Stage 7, using the outputs from Stage 6 (unsure_groups.json and final_groups.json):

bash
Copy code
python main.py --stage 7 --input final_groups.json unsure_groups.json --output-dir outputs --search-method duckduckgo
Notes:

Each stage saves its outputs to files, which are then used as inputs for the subsequent stages.
The script uses the LLM (language model) in stages where necessary. Ensure that the model is properly initialized and accessible.
The thresholds and parameters can be adjusted as needed using the command-line arguments or by modifying the script.
Important:

Ensure that all required dependencies are installed and properly configured.
Adjust file paths and configurations according to your environment.
Be cautious with web searches in Stage 7 to avoid being blocked by search engines due to too many requests.