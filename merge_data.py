import json
import pandas as pd
import numpy as np
import os
from eda.splink_tools import *

if __name__ == "__main__":
    data_dir = os.path.join("data", "raw", "processed")

    with open(os.path.join(data_dir, "gtr_data.json"), "r", encoding="utf8") as f:
        gtr_json = json.load(f)
    with open(os.path.join(data_dir, "cordis_data.json"), "r", encoding="utf8") as f:
        cordis_json = json.load(f)


    gtr_df = pd.DataFrame(gtr_json)
    # gtr_df.head()

    map_names_gtr = {
        "id": "unique_id",
        "address.postCode": "postcode"

    }
    drop_cols_gtr = ["link.EMPLOYEE","address.type","address.region"]
    gtr_order = ["unique_id", "name"]


    gtr_df = drop_cols(gtr_df, drop_cols_gtr)
    gtr_df = change_col_names(gtr_df, map_names_gtr)
    gtr_df = reorder_cols(gtr_df, gtr_order)
    gtr_df = clean_string_columns(gtr_df, columns=["name", "postcode"])
    gtr_df["dataset"] = "gtr"
    cordis_df = pd.DataFrame(cordis_json)
    # cordis_df.head()

    map_names_cordis = {
        # "organisationID": "unique_id",
        "rcn": "unique_id",
        "postCode": "postcode", 
    }

    drop_cols_cordis = ["geolocation", "nutsCode", "shortName", "street", "city", "organisationID"]

    cordis_order = ["unique_id", "name", "postcode"]

    cordis_df = drop_cols(cordis_df, drop_cols_cordis)
    cordis_df = change_col_names(cordis_df, map_names_cordis)
    cordis_df = reorder_cols(cordis_df, cordis_order)
    # print all enties in cordis_df["postcode"] that are not strings
    # print(cordis_df[~cordis_df["postcode"].apply(lambda x: isinstance(x, str))])
    # remove all entries in cordis_df["postcode"] that are not strings
    cordis_df = cordis_df[cordis_df["postcode"].apply(lambda x: isinstance(x, str))]
    cordis_df = blank_to_nan(cordis_df, column=None)
    cordis_df = clean_string_columns(cordis_df, columns=["name", "postcode"])
    cordis_df["dataset"] = "cordis"

    df = pd.concat([cordis_df, gtr_df], ignore_index=True)

    # save the merged data to a json file
    output_dir = os.path.join("data", "splink")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    df.to_json(os.path.join(output_dir, "all_data.json"), orient="records", indent=2)