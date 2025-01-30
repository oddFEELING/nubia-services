import os

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.ollama import OllamaModel

from src.tools.csv_reader import load_csv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

ollama_model = OllamaModel(
    model_name="llama3.2",
    base_url="http://ollama:11434/v1"
)

anthropic_model = AnthropicModel(
    'claude-3-5-sonnet-latest',
    api_key=api_key,
)


class CityLocation(BaseModel):
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
