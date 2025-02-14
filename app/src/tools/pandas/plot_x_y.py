from typing import Literal, List, Union, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
import pandas as pd
import numpy as np
from src.utils import supabase


@dataclass
class PlotXYParams(BaseModel):
    file_url: str = Field(description="The url of the file to be analysed")
    title: str = Field(description="The title of the chart")
    description: str = Field(description="The description of the chart")
    x_key: str = Field(description="The column name of the value on the x-axis")
    y_key: str = Field(description="The column name of the value on the y-axis")
    chart_type: Literal['bar', 'histogram', 'line', 'area'] = Field(description="The type of chart to be plotted")


def convert_to_numeric(value: Any) -> Union[float, str, None]:
    """
    Convert string values to numbers where possible
    Returns the original value if conversion is not possible or needed
    """
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        # Remove any currency symbols, commas, and spaces
        cleaned = str(value).replace('$', '').replace(',', '').replace(' ', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return value


def plot_x_y(project_id: str, analysis_id: str, params: PlotXYParams) -> str:
    """
    Plots one value against the other. Suitable for the following chart types
    :param project_id: The id of the project
    :param analysis_id: The id of the analysis
    :param params: Parameters for the plot
    :return: A dictionary containing the x and y axis data
    :raises: ValueError if required columns are not found in the CSV
    """
    # Read the CSV file
    df = pd.read_csv(params.file_url)
    
    # Validate that required columns exist
    if params.x_key not in df.columns:
        raise ValueError(f"Column '{params.x_key}' not found in CSV file")
    if params.y_key not in df.columns:
        raise ValueError(f"Column '{params.y_key}' not found in CSV file")

    # Transform data into ReCharts format
    recharts_data = []
    for idx, row in df.iterrows():
        data_point = {
            params.x_key: convert_to_numeric(row[params.x_key]),
            params.y_key: convert_to_numeric(row[params.y_key])
        }
        recharts_data.append(data_point)

    # Prepare the data for JSON serialization
    chart_data: Dict[str, Any] = {
        'chart_data': recharts_data,
        "title": params.title,
        "description": params.description,
        "type": params.chart_type,
        "project_id": project_id,
        "analysis_id": analysis_id,
    }

    # Insert into Supabase
    (supabase
     .table('artefact_charts')
     .insert(chart_data)
     .execute())

    return 'Chart has been plotted'
