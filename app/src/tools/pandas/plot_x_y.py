from typing import Dict, Any

import pandas as pd


def plot_x_y(file_url: str, x_key: str, y_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Plots one value against the other. Suitable for the following chart types
    - Bar chart
    - Line chart
    - Histogram
    - Scatter plot
    - Area chart

    :param file_url: URL to access the file for pandas
    :param x_key: column name of the value on the x-axis
    :param y_key: column name of the value on the y-axis
    :return: A dictionary containing the x and y axis data
    """
    df = pd.read_csv(file_url)

    return {
        "x_axis": {
            "key": x_key,
            "values": df[x_key].to_list()
        },
        "y_axis": {
            "key": y_key,
            "values": df[y_key].to_list()
        }
    }
