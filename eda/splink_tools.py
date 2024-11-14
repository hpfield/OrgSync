import os, sys
import pandas as pd
import numpy as np

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


def blank_to_nan(df, column):
    """
    Convert empty strings and whitespace-only strings to NaN in specified column

    r'^\s*$' is commonly used to:

    - Check if a string is empty
    - Check if a string contains only whitespace
    - Match blank lines in text
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    column (str): Name of column to process
    
    Returns:
    pandas.DataFrame: DataFrame with processed column
    """
    df[column] = df[column].replace(r'^\s*$', np.nan, regex=True)
    return df

def nan_to_empty_list(df, column):
    pass





## Text Processing
def convert_text_to_lowercase(df, column):
    """Convert text to lowercase"""
    pass

def remove_whitespace(df, column):
    """Remove leading and trailing whitespace"""
    pass

def remove_special_characters(df, column):
    """Remove special characters"""
    pass
