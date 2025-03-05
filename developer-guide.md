## 1. Overview of the Pipeline

This codebase processes raw organization data (e.g., from UK data), identifies duplicates, groups together organizations that refer to the same entity, enriches them with web search results, refines these groups using a Large Language Model (LLM), and finally outputs a consolidated, deduplicated, and refined set of grouped organizations.

The **main entry point** is `main.py`, which implements **12 stages** (0 to 11). You can selectively run (or re-run) each stage by specifying `--stage <number>`. The pipeline flow is:

1. **Load old vs. new data**; mark newly added records.
2. **Preprocess** organization names into a normalized format.
3. **Identify** identical or similar names.
4. **Enrich** via web searches (currently DuckDuckGo only; Google is not yet implemented).
5. **Refine** these groups with LLM logic.
6. **Finalize** group outputs in a single JSON.

Because identifying new entries is important, you can optionally run in a “new only” mode (`--data-mode=new`) so that you do not have to re-process the entire dataset each time.

---

## 2. How to Run the Pipeline

Invoke the pipeline via:

bash

CopyEdit

`python main.py [--stage N] [other arguments]`

- **`--stage N`** (0–11) sets the stage to start from. If unspecified, defaults to 0 (runs all stages in order).
- You can provide additional arguments such as `--threshold`, `--search-method`, `--data-mode`, etc. (see below).

---

## 3. Command-Line Arguments

Defined in `parse_arguments()` within `main.py`:

- **`--stage`** _(int, default=0)_  
    Which stage to start from (0 through 11).
    
- **`--threshold`** _(float, default=0.5)_  
    Used in **Stage 4** for grouping similar names based on TF-IDF vectors.
    
- **`--search-method`** _(string, default='duckduckgo')_  
    Choices: `duckduckgo`, `google` (but Google is **not yet implemented**).
    
- **`--input`** _(list of strings)_  
    Allows specifying custom input file(s) for a particular stage.
    
- **`--output-dir`** _(string, default='outputs')_  
    Where each stage outputs its files (pickles and JSON).
    
- **`--num-search-results`** _(int, default=5)_  
    How many web search hits are retrieved in **Stage 5**.
    
- **`--data-mode`** _(string, default='all'; choices=['all', 'new'])_
    
    - `all`: processes the entire dataset.
    - `new`: only continues forward with new data from Stage 4 onward (to avoid re-processing all data every time).

Example:

bash

CopyEdit

`python main.py --stage 4 --threshold 0.75 --data-mode=new`

---

## 4. Detailed Stage-by-Stage Explanation

### Stage 0: Check New Data (`stage0.py`)

- **Purpose**:  
    Merge old and new data, marking truly new entries with `is_new=True`.
- **Input**:
    - `uk_data.json` (new)
    - `old_uk_data.json` (old)
- **Process**:
    1. Load old data (if it exists).
    2. Identify new entries that aren’t in the old dataset.
    3. Merge them and mark `is_new=True` on fresh records.
    4. Update `old_uk_data.json` by overwriting it with the merged version (so subsequent runs treat it as “old data”).
- **Outputs**:
    - `stage0_merged_data.pkl` (pickled Python list).
    - A new “merged_uk_data.json” plus “new_entries.json” for reference.

### Stage 1: Load & Preprocess Data (`stage1.py`)

- **Purpose**:  
    Convert `name` + `short_name` into a single normalized `combined_name`, preserving `is_new`.
- **Input**:
    - `stage0_merged_data.pkl`
- **Process**:
    1. Lowercase, strip punctuation.
    2. Combine name fields into `combined_name`.
- **Output**:
    - `preprocessed_data.pkl`.

### Stage 2: Identify Identical Names (`stage2.py`)

- **Purpose**:  
    Group entries that share the exact same `combined_name`.
- **Input**:
    - `preprocessed_data.pkl`
- **Process**:
    1. Build a dictionary of `combined_name -> [entries with that name]`.
    2. Keep only groups where size > 1.
- **Output**:
    - `identical_name_groups_stage2.json`.

### Stage 3: Vectorize Names (`stage3.py`)

- **Purpose**:  
    Create TF-IDF vectors for each unique entry’s `combined_name`.
- **Input**:
    - `preprocessed_data.pkl`
- **Process**:
    1. Remove exact-duplicate items.
    2. TF-IDF vectorize all `combined_name` fields.
- **Outputs**:
    - `vectorizer_stage3.pkl`
    - `name_vectors_stage3.pkl`
    - `unique_entries_stage3.pkl` (and a JSON version).

### Stage 4: Group Similar Names (`stage4.py`)

- **Purpose**:  
    Use the TF-IDF vectors to cluster names with **cosine distance <= threshold**.
- **Inputs**:
    - `vectorizer_stage3.pkl`, `name_vectors_stage3.pkl`, `unique_entries_stage3.pkl`
    - `--threshold` argument
- **Process**:
    1. For each name, find neighbors within a certain distance.
    2. Group them under a “representative” name.
    3. If `--data-mode=new`, filter out any groups that do **not** contain newly added entries.
- **Outputs**:
    - `grouped_names_stage4_all_data.json` _(default if data-mode=all)_
    - `grouped_names_stage4_new_data_only.json` _(if data-mode=new)_

### Stage 5: Perform Web Search (`stage5.py`)

- **Purpose**:  
    Enrich group info by searching DuckDuckGo (or Google, once implemented) for each name.
- **Inputs**:
    - `grouped_names_stage4_*.json` (from Stage 4)
    - `unique_entries_stage3.json` for postcode lookups.
    - `--num-search-results`, `--search-method`
- **Process**:
    1. Maintain a rolling DB: `all_web_search_results.json`.
    2. For each name, if fewer than `--num-search-results` results exist, do a fresh search.
    3. Store new search results.
- **Outputs**:
    - `all_web_search_results.json` (rolling DB)
    - `web_search_results_stage5.json` (sub-dict relevant to the chosen search method).

### Stage 6: Process Groups with LLM (`stage6.py`)

- **Purpose**:  
    Use LLM calls to refine each group’s list of names, removing those that don’t appear to be the same organization.
- **Inputs**:
    - `grouped_names_stage4_*.json`
    - `web_search_results_stage5.json`
- **Process**:
    1. For each group, prompt the LLM with the group’s names + search results.
    2. Output a final list of names that truly refer to the same org.
- **Output**:
    - `refined_groups_stage6.json`.

### Stage 7: Combine Overlapping Groups (`stage7.py`)

- **Purpose**:  
    Merge any groups that share overlapping names.
- **Input**:
    - `refined_groups_stage6.json`
- **Process**:
    1. If two groups share at least one name, merge them into a single group.
    2. Re-check repeatedly until no more merges are required.
- **Output**:
    - `merged_groups_stage7.json`.

### Stage 8: Determine Organisation Type (`stage8.py`)

- **Purpose**:  
    Classify each merged group’s type (e.g., company, university, government, nonprofit) using LLM calls + search results.
- **Inputs**:
    - `merged_groups_stage7.json`
    - `web_search_results_stage5.json`
- **Process**:
    1. For each group, gather search results for all names.
    2. Prompt the LLM to output `"organisation_type": "<type>"`.
- **Output**:
    - `groups_with_types_stage8.json`.

### Stage 9: Finalize Groups (`stage9.py`)

- **Purpose**:  
    Construct a final dictionary with a chosen representative name, a unique group ID (UUID), and the group’s items.
- **Inputs**:
    - `groups_with_types_stage8.json`
    - `web_search_results_stage5.json`
    - `identical_name_groups_stage2.json` and `unique_entries_stage3.json` for name lookups.
- **Process**:
    1. Collect all the items from the group’s names.
    2. Use the LLM to pick a single “representative name.”
    3. Generate a UUID per group.
- **Output**:
    - `formatted_groups_stage9.json`.
    - Each group is stored as `{"UUID": {"name": "...", "items": [...], "organisation_type": "..."}, ...}`.

### Stage 10: Refine Groups with LLM (Post-Stage 9) (`stage10.py`)

- **Purpose**:  
    Another pass of LLM-based refinement once each group has a chosen representative name.
- **Inputs**:
    - `formatted_groups_stage9.json`
    - `web_search_results_stage5.json`
    - `unique_entries_stage3.json`
- **Process**:
    1. Prompt the LLM to confirm each item’s membership in the final group.
- **Output**:
    - `refined_groups_stage10.json`.

### Stage 11: Capitalize Group Names & Merge Rolling Output (`stage11.py`)

- **Purpose**:  
    Apply correct capitalization to the representative names, then merge the final dictionary into a rolling output.
- **Inputs**:
    - `refined_groups_stage10.json`
    - `web_search_results_stage5.json`
- **Process**:
    1. For each group, ask the LLM to correct only the casing (no spelling changes).
    2. Save the capitalized result.
    3. Merge into `output_groups.json`, preserving previously finalized groups.
- **Outputs**:
    - `final_groups_stage11.json`
    - Updated `output_groups.json` (the “rolling” final output).

---

## 5. Important Variables & Data Flow

- **`args.stage`**: Selects the stage to begin from.
- **`args.threshold`**: Determines how aggressively Stage 4 groups names.
- **`args.search_method`**: Currently supports only `duckduckgo`; “google” is not yet implemented.
- **`args.data_mode`**:
    - **`all`** re-runs every name in Stage 4 onward,
    - **`new`** focuses only on newly added data (which is flagged in Stage 0).
- **`args.output_dir`**: Location of all `.pkl` and `.json` outputs for each stage.
- **Identifying new entries**: Happens in Stage 0 and is carried forward by marking items with `is_new=True`. If `--data-mode=new`, only groups containing new entries are processed after Stage 4.

---

## 6. Files Generated and Consumed

All paths default to `outputs/`, except for the raw data (which comes from a `data/raw/` directory). Stages read from prior-stage outputs if no `--input` override is provided.

|**Stage**|**Reads**|**Writes**|
|---|---|---|
|Stage 0|`uk_data.json`, `old_uk_data.json`|`stage0_merged_data.pkl`, `merged_uk_data.json`, `new_entries.json`|
|Stage 1|`stage0_merged_data.pkl`|`preprocessed_data.pkl`|
|Stage 2|`preprocessed_data.pkl`|`identical_name_groups_stage2.json`|
|Stage 3|`preprocessed_data.pkl`|`vectorizer_stage3.pkl`, `name_vectors_stage3.pkl`, `unique_entries_stage3.pkl/json`|
|Stage 4|_Pickled data from Stage 3_|`grouped_names_stage4_all_data.json` or `grouped_names_stage4_new_data_only.json`|
|Stage 5|_Stage 4 output_, `unique_entries_stage3.json`|Updates `all_web_search_results.json` & writes `web_search_results_stage5.json`|
|Stage 6|_Stage 4 output_, `web_search_results_stage5.json`|`refined_groups_stage6.json`|
|Stage 7|`refined_groups_stage6.json`|`merged_groups_stage7.json`|
|Stage 8|`merged_groups_stage7.json`, `web_search_results_stage5.json`|`groups_with_types_stage8.json`|
|Stage 9|`groups_with_types_stage8.json`, `web_search_results_stage5.json`, `identical_name_groups_stage2.json`, `unique_entries_stage3.json`|`formatted_groups_stage9.json`|
|Stage 10|`formatted_groups_stage9.json`, `web_search_results_stage5.json`, `unique_entries_stage3.json`|`refined_groups_stage10.json`|
|Stage 11|`refined_groups_stage10.json`, `web_search_results_stage5.json`|`final_groups_stage11.json`, updates `output_groups.json`|

---

## 7. Final Data Format

By the end of Stage 11, the **final** data is stored in a dictionary of group UUIDs, each mapping to an object with `"name"`, `"items"`, and optionally `"organisation_type"`. For example:

json

CopyEdit

`{   "bf5cba29-2dd1-4433-9ec1-b2fc5a6feeb2": {     "name": "Durham University",     "items": [       {         "org_name": "durham university",         "unique_id": "CB6DB8A7-3191-4B03-B37A-1FC98C252089",         "dataset": "gtr",         "postcode": "DH1 3LE"       },       {         "org_name": "durham university",         "unique_id": "50EEF0BC-3753-464C-85B9-A24293AF091F",         "dataset": "gtr",         "postcode": "DH1 3LE"       },       {         "org_name": "durham university",         "unique_id": "80345FE1-52E7-4194-B9BA-95C482D409A3",         "dataset": "gtr",         "postcode": "Unknown"       }     ]   } }`

Each “items” list contains all the deduplicated entries determined to be the **same** organization, along with any relevant metadata (IDs, postcodes, etc.). The `"organisation_type"` (e.g., `"university"`) can also appear under the main group object if it was assigned in Stage 8–10.