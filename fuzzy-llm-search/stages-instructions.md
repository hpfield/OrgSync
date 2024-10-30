Usage Instructions:

You can run the script and specify the stage you want to start from using the --stage argument. For stages beyond 1, you need to provide the required input files using the --input argument.


Here is the Mermaid code:

```mermaid
flowchart TD
    %% Main stages
    S1[Stage 1:\nLoad and Preprocess Data]
    S2[Stage 2:\nVectorize Names]
    S3[Stage 3:\nGroup Similar Names]
    S4[Stage 4:\nProcess Groups with LLM]
    S5[Stage 5:\nCombine Overlapping Groups]
    S6[Stage 6:\nProcess Combined Groups with LLM]
    S7[Stage 7:\nProcess Unsure Groups with LLM Using Web Search]

    %% Connections
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> S7

    %% Supplementary details for each stage
    S1_details{{"**Stage 1 Details**\n\n**Input:** Raw organization names\n\n**Process:**\n- Load data from sources\n- Clean and normalize names\n\n**Output:** Cleaned organization names"}}
    S2_details{{"**Stage 2 Details**\n\n**Input:** Cleaned organization names\n\n**Process:**\n- Convert names to numerical vectors\n- Use techniques like TF-IDF or embeddings\n\n**Output:** Vector representations of names"}}
    S3_details{{"**Stage 3 Details**\n\n**Input:** Vector representations\n\n**Process:**\n- Compute similarities between vectors\n- Cluster names into groups of similar organizations\n\n**Output:** Groups of similar organization names"}}
    S4_details{{"**Stage 4 Details**\n\n**Input:** Groups of similar names\n\n**Process:**\n- Use a Large Language Model (LLM)\n- Refine groups and confirm name similarities\n\n**Output:** Refined groups of organization names"}}
    S5_details{{"**Stage 5 Details**\n\n**Input:** Refined groups\n\n**Process:**\n- Identify overlapping groups\n- Merge groups to consolidate variations\n\n**Output:** Merged groups of organization names"}}
    S6_details{{"**Stage 6 Details**\n\n**Input:** Merged groups\n\n**Process:**\n- Re-evaluate merged groups with LLM\n- Further refine groupings\n\n**Output:** Final groups and unsure groups"}}
    S7_details{{"**Stage 7 Details**\n\n**Input:** Unsure groups\n\n**Process:**\n- Perform web searches for additional context\n- Use LLM with web data to finalize decisions\n\n**Output:** Finalized organization groups"}}

    %% Linking details to main stages
    S1 -->|Details| S1_details
    S2 -->|Details| S2_details
    S3 -->|Details| S3_details
    S4 -->|Details| S4_details
    S5 -->|Details| S5_details
    S6 -->|Details| S6_details
    S7 -->|Details| S7_details

    %% Styling
    classDef stage fill:#1f77b4,stroke:#333,stroke-width:2px,color:#fff
    classDef details fill:#d9edf7,stroke:#333,stroke-width:1px,color:#000
    class S1,S2,S3,S4,S5,S6,S7 stage
    class S1_details,S2_details,S3_details,S4_details,S5_details,S6_details,S7_details details


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