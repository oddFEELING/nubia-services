import pandas as pd
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import List, Literal


@dataclass
class CompareDataProps(BaseModel):
    operations: List[Literal["sum", "subtract", "multiply", "divide"]] = Field(
        description="The operations to perform on the columns"
    )
    columns: List[str] = Field(
        description="The columns to perform the operations on"
    )
    file_url: str = Field(description="The URL of the file to process")



def compare_data(props: CompareDataProps) -> pd.DataFrame:
    """
    Compare multiple fields in a dataframe based on the operations specified.

    """
    df = pd.read_csv(props.file_url)
    for operation in props.operations:
        df[operation] = df.apply(lambda row: row[operation], axis=1)
    return df
