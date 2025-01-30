import json

import pandas as pd


def describe_csv_files(file_url: str) -> str:
    """
    Returns basic information about a csv file
    :param file_url:
    :return: str
    """
    df = pd.read_csv(file_url)

    # List of column names
    columns = df.columns.to_list()

    # Sample of 5 rows from the dataframe
    sample = df.sample(5).to_string(index=False)

    # Summary statistics of the dataframe
    summary = df.describe(include='all').to_string(index=False)

    # Count of null values in each column
    is_null = df.isnull().sum().to_string()

    # Information about the dataframe
    info = df.info

    # Data types of each column
    column_dtypes = df.dtypes.to_string()

    # Number of rows in the dataframe
    num_rows = len(df)

    # Number of columns in the dataframe
    num_columns = len(df.columns)

    # Memory usage of the dataframe
    memory_usage = df.memory_usage(deep=True).sum()

    return json.dumps({
        "columns": columns,
        "sample": sample,
        "summary": summary,
        "is_null": is_null,
        "info": info,
        "column_dtypes": column_dtypes,
        "num_rows": num_rows,
        "num_columns": num_columns,
        "memory_usage": memory_usage
    })
