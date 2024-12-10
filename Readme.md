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
  
  

## Setting up the repo

Clone this repo.

### Setup environment

```
conda create -f orgsync.yml
conda activate orgsync
```

### Download data

Install git lfs to handle large files in the repo with:
```
sudo apt update
sudo apt install git-lfs
```

Initialise git lfs and track json files:
```
git lfs install
git lfs track "*.json"
```

Pull the large files (may take a while):
```
git lfs pull
```

  
### Prepare data

```
python setup.py
```


## Install Llama-3.1

Follow instructions on the [llama-models](https://github.com/meta-llama/llama-models) git repo.

When you reach the meta [llama-downloads](https://www.llama.com/llama-downloads/) page, request access to **Llama 3.1: 405B, 70B & 8B**.

## Setup config

Once you have llama-3.1 installed, you will need to configure the locations of certain files so that our pipeline can find the model.

Go to the `cfg/config.yaml` file and update the following values to reflect where the files are stored on your machine:
```
models_dir: "/home/ubuntu/OrgSync/llama-models/models"
default_ckpt_dir: "/home/ubuntu/OrgSync/.llama/checkpoints/Meta-Llama3.1-8B-Instruct"
tokenizer_subpath: "llama3/api/tokenizer.model" # relative to models_dir
```

## Use latest pipeline

```
cd src/local_llm/llama_v3
python main.py
```

Optionally, you can specify the stage at which to start with `--stage=NUM` where `NUM` can be 1 - 8. This is especially useful if you've had to stop the process part way through and wish to pick up where you left off. 