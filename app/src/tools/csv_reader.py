import pandas as pd
from rich import print


def load_csv() -> str:
    """
    Loads the context from the csv file intended to be used for analysis
    :return: Details of the csv file
    """
    print('This was called')
    df = pd.read_csv('./src/agents/faac.csv')

    return str(df.describe())
