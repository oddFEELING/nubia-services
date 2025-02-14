import os

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from app.src.tools.pandas.csv_reader import load_csv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

anthropic_model = AnthropicModel(
    'claude-3-5-sonnet-latest',
    api_key=api_key,
)


class ChBaseModel(BaseModel):
    description: str


agent = Agent(
    anthropic_model,
    deps_type=str,
    tools=[load_csv],
    result_type=CityLocation
)

# @agent.tool_plain
# def load_csv() -> str:
#     """
#     Loads the context from the csv file intended to be used for analysis
#     :return: Details of the csv file
#     """
#     print('This was called')
#     # df = pd.read_csv('./faac.csv')
#
#     return 'The csv holds data on Nigerias money spending '
