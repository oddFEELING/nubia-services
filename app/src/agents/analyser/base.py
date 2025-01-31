import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from src.agents.analyser.csv_analyser import agent as csv_analyser
from src.utils.prompts.template import TemplateEngine

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

### Create LLm instance
anthropic_model = AnthropicModel(
    "claude-3-5-sonnet-latest",
    api_key=api_key
)

"""
Brainstorming:
if the agent calls a chart tool, the tool saves the chart to the database and returns a success message that showas
what the chart is about.

if the agent calls a table tool, the tool saves the table to the database and returns a success message that shows
what the table is about.

if the agent calls a chat tool, the tool saves the chat to the database and returns a success message that shows
what the chat is about.

if the agent calls the table tool, the tool creates the table schema and saves it to the database and returns a success message that shows
what the table is about.
"""


### Return type definitions
class ChatReturnType(BaseModel):
    """Return type for the chat rendering on the front end"""
    content: str = Field(description="The content of the chat message")
    options: List[str] = Field(
        description="A list of options that the user can choose from. Could be suggestions of next actions or suggestions of how to handle a pending task")


### Dependencies definitions
class Dependencies(BaseModel):
    file_url: str = Field(description="The url of the file to be analysed")


system_prompt = TemplateEngine(
    path='./src/utils/prompts/prompts.toml',
    section="ORCHESTRATORS",
    template_name="main",
)

data_res = system_prompt.format(
    ROLE="Your role is to Have a conversation with a user, helping them to attain their analyses goal",
    TASK=("Use the tools available to you to hold a conversation with a user. You can suggest some options to them in "
          "cases where it is deemed necessary. In other scenarios just call the tool and let them do their thing.\n"
          "You can call multiple tools if there is need for that.\n"
          "Always return a message content to the user and prompt them to check if they need your help for anything else."),
    SPECIAL_INSTRUCTION=("After receiving the files, always initiate the chat with a warm welcome message asking "
                         "relevant questions on how the user wants to proceed.")
)

# ################################################
# ### AGENT
# ################################################
agent = Agent(
    "claude-3-5-sonnet-latest",
    deps_type=Dependencies,
    system_prompt=system_prompt.template,
    result_type=ChatReturnType
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
    resp = await csv_analyser.run(file_url)
    print(resp.usage())
    return resp.data
