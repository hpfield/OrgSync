# OrgSync

In a database of academic publications, we must resolve situations where the same organisation has been referred to by different names. To do this, we apply a multi-stage technique, where we:

1. Isolate the unique listed organisation names
2. Vectorise the names with sklearn
3. Cluster similar names using K-Nearest-Neighbours
4. Search the web for information on each name using duckduckgo search API
5. Process the name clusters using Llama3.1 and web search results as context
6. Combine & Merge any overlapping groups
7. Determine the type of organisation each group refers to using LLM
8. Process name groups using LLM, web search results and organisation type as context

We conduct micro-labelling sessions as we progress to account for the absence of labelled data. We do this to obtain some metric of success beyond anecdotal experiences reading model outputs.

## Repo Setup 

Clone this repo.

### Setup environment

```
conda create -f orgsync.yml   
conda activate orgsync
```

### Download data

Download the data from [google drive](https://drive.google.com/file/d/19sb1UXM6v9p0s617t5LD9rOfjLMYbqpM/view?usp=drive_link) and save the tar file to the repo root.

### Extract the data:

```
tar -xzvf data.tar.gz
```

### Prepare data

```
python setup.py
```

## Quick Grab Results

The repo data includes all experiment results to date, and so running the code yourself isn't necessary to view the labelled data. The final output is stored at `src/local_llm/llama_v3/outputs/final_groups_stage8.json`, the same output with associated web search results can be found at `src/local_llm/llama_v3/outputs/final_output_with_context.json`.

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

```
cd src/local_llm/llama_v3   
python main.py
```

Optionally, you can specify the stage at which to start with `--stage=NUM` where `NUM` can be 1 - 8. This is useful if you've had to stop the process part way through and wish to pick up where you left off.

## Continue Project

The next phase of this project is to continue data labelling of the model outputs and implement changes to the pipeline based on insights drawn from the labelling process.

### Conducting labelling:

We use a browser based labelling tool which automatically saves labels in `src/local_llm/llama_v3/outputs/human_labelled_data.json`. Unlabelled examples will have the "Not Labelled" option checked.

```
cd src/local_llm/llama_v3   
streamlit run manual_label_app.py
```

### Changes to implement

- Developing from `src/local_llm/llama_v3`
- Obtain 5 web search results per name: 3 often only shows companies house, when additional context is required to distinguish between names.
- Design alternative web-search options: Can use rate-limited options but over several days, the current option frequently cannot find answers and takes a long time.
- Reorient pipeline around api-based LLM queries for better results: Historically these have proven to be overly cautious, but web search results context could help with this.
- Include the gtr data in the pipeline by editing the `setup.py` file to omit the UK country filter on the gtr data: This will increase the dataset size from ~5k to ~60k so omit this for any exploratory research.

### Most recent performance

With 20 of the final outputs labelled in the llama_v3 pipeline, the current strategy results in a precision of 0.7. We cannot calculate other metrics with the current strategy as we are only manually labelling the final outputs with are all positive label predictions in the form of groups. We are labelling the groups as True if we find the names to refer to the same organisation, the group need not be an exhaustive list of all the names that refer to the same organisation.