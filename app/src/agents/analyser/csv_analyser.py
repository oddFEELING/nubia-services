from pydantic import BaseModel
from pydantic_ai import Agent
from rich import print
from src.tools.pandas.describe import describe_csv






# ################################################
# ### AGENT
# ################################################
agent = Agent(
    "claude-3-5-sonnet-latest",
    name="CSV Analyser",
    result_type=str,
    tools=[describe_csv]
)



# ################################################
# ### Tools
# ################################################
@agent.tool_plain(docstring_format="sphinx", require_parameter_descriptions=True)
async def get_csv_summary(file_url: str) -> str:
    """
    Returns a summary of the data in the CSV file
    :param file_url: The url of the CSV file to be analysed
    :return: A summary of the data in the CSV file
    """
    data = describe_csv(file_url)
    print(data)
    return str(data)

