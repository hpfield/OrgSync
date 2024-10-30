# OrgSync

In a database of academic publications, we must resolve situations where the same organisation has been referred to by different names. To do this, we apply a multi-stage technique, where we:


1. Identify unique organisation names in the database.
2. Preprocess the organisation names with regex.
3. Create vectorized embeddings of the names using off the shelf tools from sklearn.
4. Use K-nearest-neighbours to create a set of similar entries to each unique name
5. Sequentially pass these pairs of names and sets of similar names to an LLM (Llama3.1), which further sorts the names based on organisation.
6. Combine the resulting groups where overlap occurs into larger groups.
7. Pass the combined groups to the LLM for final sorting and selection of a master name for the organisation.


## Setting up the repo

### Download raw data

go to <https://drive.google.com/drive/folders/1PptOmEKYwbQHtcLrwRGgIGTcjq3vRGXB?usp=drive_link> and download all data into `data/raw/all_scraped`.

### Setup files

`python setup.py`

Setup.py will establish the project root directory for relative file paths, wrangle the dataset from multiple sources and setup any other configuration parameters that are required.



