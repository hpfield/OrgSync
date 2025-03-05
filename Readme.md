# OrgSync

## Overview
In a database of academic publications, we must resolve situations where the same organisation has been referred to by different names. To do this, we apply a multi-stage techniqueoutlined in the following diagram:


![orgsync drawio](https://github.com/user-attachments/assets/14e55f07-2c33-4c86-bfbd-8d623611db94)

## Performance
We manually label the pipeline output groups (multiple database entries that refer to the same organisation) to obtain a Precision score. Our final implementation uses OpenAI's GPT-4o and obtains a **precision of 0.94**. With this score, we generate a complete set of labels over the entire dataset for integration with UKTIN's research discovery tool.

## Limitations of Current Approach & Proposed Improvements

1. **Web Search**
    - **Current Limitation**: We rely on a DuckDuckGo-based utility for fetching context on organisation names. It is free to use, but rate-limited and often returns empty or incomplete results. This can result in insufficient context for the language model to make accurate grouping decisions.
    - **Proposed Improvement**: Adopt a paid Google Search API to retrieve richer, more complete information. This would help the pipeline better differentiate between organisations, catch synonyms or expansions for acronyms, and improve overall grouping accuracy.
2. **Initial Group Offerings**
    - **Current Limitation**: We use an off-the-shelf embeddings model to create initial groupings based purely on semantic similarity. This often misses organisations frequently listed under acronyms or those composed of multiple child entities with different names. We adopted this approach due to limited accessible data sources (e.g., we could not reliably use advanced linking solutions such as [moj-analytical-services/splink](https://github.com/moj-analytical-services/splink)).
    - **Proposed Improvement**: Incorporate additional data sources capable of linking organisations more concretely (e.g., authoritative registry or knowledge-graph data). With better external data, we could establish stronger, more meaningful connections between references and significantly increase recall.
3. **Group Refinement**
    - **Current Limitation**: The LLM-based refinement stage is a proof-of-concept that favors _precision_ over _recall_. When multiple valid entities appear in a single candidate group, the pipeline currently forces the removal of all but the single “best-fit” organisation. While this boosts precision, it can leave many organisations unlabelled.
    - **Proposed Improvement**: Add a _group-splitting_ component to the pipeline that handles multi-entity clusters more gracefully. Instead of discarding extra members, we should split them off, preserving potentially valid sub-groupings that represent distinct organisations.
4. **Determining a Group’s Representative Name**
    - **Current Limitation**: The final (representative) name for a group is chosen by asking an LLM to pick the best fit. This can be inefficient, and relies on the LLM’s reasoning over multiple names.
    - **Proposed Improvement**: Embed all names in a group and select the one with the highest average similarity to the rest. This data-driven approach can speed up the final naming step and reduce potential LLM inaccuracies.

## Repo Setup 

```
git clone https://github.com/hpfield/OrgSync.git
```

### Setup environment

```
conda create -f orgsync.yml   
conda activate orgsync
```

### Setup Data
Either:
#### Update Data (For UKTIN Employee & Online Deployment)
Conduct scraping of data from data sources and deposit files in `data/raw/all_scraped` so that `setup.py` can find the following files:
```
cordis_files = [
    "cordis/FP7/organization.json",
    "cordis/Horizon 2020/organization.json",
    "cordis/Horizon Europe/organization.json",
]
gtr_file = "gtr/organisations.json"
```

Or...

#### Download & Extract test data (Not for deployment)
Download test data from [google drive](https://drive.google.com/file/d/19sb1UXM6v9p0s617t5LD9rOfjLMYbqpM/view?usp=drive_link) and save the tar file to the repo root.

Extract the data:
```
tar -xzvf data.tar.gz
```

### Prepare data
For full combined Cordis and GtR organisations data
```
python setup.py
```

For Cordis only (~5k records for testing)
```
python setup.py --cordis_only
```

## Quick Grab Results

The repo data includes all experiment results to date, and so running the code yourself isn't necessary to view the labelled data. The final output is stored at `src/api_llm/gpt-4o/outputs/output_groups.json`.

## Run Pipeline

### Install Llama-3.1

Follow instructions on the [llama-models](https://github.com/meta-llama/llama-models/tree/main) git repo.

When you reach the meta llama-downloads page, request access to **Llama 3.1: 405B, 70B & 8B**.

### Setup config

Once you have llama-3.1 installed, you will need to configure the locations of certain files so that our pipeline can find the model.

Go to the `cfg/config.yaml` file and update the following values to reflect where the files are stored on your machine:

```
models_dir: "/home/ubuntu/OrgSync/llama-models/models"   
default_ckpt_dir: "/home/ubuntu/OrgSync/.llama/checkpoints/Meta-Llama3.1-8B-Instruct"   
tokenizer_subpath: "llama3/api/tokenizer.model" # relative to models_dir
```

### Latest version
You will need an OpenAI API key to run this code placed into the environemnt with `export OPENAI_API_KEY="YOUR API KEY HERE"`.
```
cd src/api_llm/gpt-4o  
python main.py
```

Optionally, you can specify the stage at which to start with `--stage=NUM` where `NUM` can be 1 - 8. This is useful if you've had to stop the process part way through and wish to pick up where you left off.


