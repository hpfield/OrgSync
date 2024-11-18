import os, sys
import pandas as pd
import numpy as np
import re

def combine_dfs(df1, df2):
    "combine two dfs with same column headers"
    return pd.concat([df1, df2])


# Splink suggested str processing: remove special characters, replace abbreviations with full words (st -> street etc.)

def clean_string_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Clean specified string columns, skipping non-string values and missing data.
    """
    df_copy = df.copy()
    
    def clean_string(x):
        if pd.isna(x) or not isinstance(x, str):
            return x
        return re.sub(r'[^\w\s]', '', 
            re.sub(r'\s+', ' ', 
                x.lower()
            )
        ).strip()
    
    for col in columns:
        df_copy[col] = df_copy[col].apply(clean_string)
    
    return df_copy

def change_col_names(df, col_map):
    """
    Take a dictionary {"column_name": "new_column_name",...}

    And change the column names in the dataframe accordingly.
    """
    return df.rename(columns=col_map)

def drop_cols(df, cols):
    """
    Drop columns from a dataframe
    """
    return df.drop(columns=cols)

def reorder_cols(df, order):
    """
    Take in dataframe and place the specified columns in the order of the list, skipping any that are not present in the dataframe.
    Any remaining columns should appear in the order they were in the original dataframe, after the specified columns.
    """
    cols = [col for col in order if col in df.columns]
    remaining = [col for col in df.columns if col not in cols]
    return df[cols + remaining]

def remove_df_columns_not_in_list(df, list_of_col_names):
    """
    Remove columns from a DataFrame that are not in the list of column names
    
    Parameters:
    df (pandas.DataFrame): Input DataFrame
    list_of_col_names (list): List of column names to keep
    
    Returns:
    pandas.DataFrame: DataFrame with columns not in list_of_col_names removed
    """
    return df[[col for col in df.columns if col in list_of_col_names]]

## Consistency of Data Types
def check_column_datatypes(d, column):
    """Inspect all data types present in column"""
    return d[column].apply(type).value_counts()

def return_rows_in_column_with_dtype(df, col, dtype):
    """
    Example usage:
        float_rows = return_rows_in_column_with_dtype(gtr_orgs, "EMPLOYEE_ids", float)
        print(float_rows)
    """
    return df[df[col].apply(lambda x: isinstance(x, dtype))]



def convert_column_str_list_to_list(df, column):
    """
    Convert string representation of list to actual list.

    If any values are Nan, they will be converted to an empty list.
    """
    #df[column] = df[column].apply(eval) # no nan handling
    df[column] = df[column].apply(lambda x: eval(x) if pd.notnull(x) else [])
    return df

def convert_empty_list_to_nan(df, col):
    """
    Convert empty lists to np.nan
    """
    df[col] = df[col].apply(lambda x: np.nan if type(x) == list and len(x) == 0 else x)
    return df

def empty_list_to_nan_full(df, column):
    """
    Convert empty lists to NaN in specified column
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    column (str): Name of column to process
    
    Returns:
    pandas.DataFrame: DataFrame with processed column
    """
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    ##
    # Convert string representations of lists to actual lists if needed
    if df[column].dtype == 'object':
        # First handle any string representations of lists
        def safe_eval(x):
            if isinstance(x, str):
                try:
                    return eval(x)
                except:
                    return x
            return x
        df[column] = df[column].apply(safe_eval)
    ##
    
    # Convert empty lists to NaN
    df[column] = df[column].apply(lambda x: np.nan if isinstance(x, list) and len(x) == 0 else x)
    return df

def count_nans(df, column):
    if not column:
        return df.isna().sum() 
    return df[column].isna().sum()

def check_empty_strings(df) -> dict:
    """
    Check each column in a DataFrame for empty strings matching regex pattern r'^\s*$'
    
    Args:
        df: pandas DataFrame to check
        
    Returns:
        dict: Dictionary mapping column names to boolean values indicating if empty strings were found
    """
    return {
        col: df[col].astype(str).str.match(r'^\s*$').any() 
        for col in df.columns
    }

def blank_to_nan(df, column):
    """
    Convert empty strings and whitespace-only strings to NaN in specified column

    r'^\s*$' is commonly used to:

    - Check if a string is empty
    - Check if a string contains only whitespace
    - Match blank lines in text
    
    If column = None, apply to all columns containing strs

    Parameters:
    df (pandas.DataFrame): Input dataframe
    column (str): Name of column to process
    
    Returns:
    pandas.DataFrame: DataFrame with processed column
    """
    if column:
        df[column] = df[column].replace(r'^\s*$', np.nan, regex=True)
        return df
    
    return df.apply(lambda x: x.replace(r'^\s*$', np.nan, regex=True) if x.dtype == 'object' else x)


    

def nan_to_empty_list(df, column):
    pass



def convert_text_to_lowercase(df, column):
    """Convert text to lowercase"""
    pass

def remove_whitespace(df, column):
    """Remove leading and trailing whitespace"""
    pass

def remove_special_characters(df, column):
    """Remove special characters"""
    pass
