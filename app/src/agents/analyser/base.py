import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

from src.agents.analyser.csv_analyser import agent as csv_analyser
from src.agents.analyser.pdf_analyser import pdf_analyser_agent
from src.tools import project_file_list
from src.utils.prompts.template import TemplateEngine

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

### Create LLm instance
anthropic_model = AnthropicModel(
    "claude-3-5-sonnet-latest",
    api_key=api_key
)


### Return type definitions
class ChatReturnType(BaseModel):
    """Return type for the chat rendering on the front end"""
    content: str = Field(description="The content of the chat message.")
    options: List[str] = Field(
        description="A list of short actionable options/suggestions that the user can choose from. Could be suggestions of next actions or suggestions of how to handle a pending task")


### Dependencies definitions
@dataclass
class AnalyserAgentDependencies:
    project_id: str
    analysis_id: str


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
    SPECIAL_INSTRUCTIONS=("After receiving the files, always initiate the chat with a warm welcome message asking "
                          "relevant questions on how the user wants to proceed. The user does not share the files with you."
                          "These files are available through the project repository."
                          "There is no need for preamble before your staements. make it flow like a conversation")
)

# ################################################
# ### AGENT
# ################################################
AnalyserAgent = Agent(
    "claude-3-5-sonnet-latest",
    deps_type=AnalyserAgentDependencies,
    system_prompt=data_res,
    result_type=ChatReturnType,
)


# ################################################
# ### Tools
# ################################################

# Get project files
@AnalyserAgent.tool(docstring_format='sphinx')
async def get_project_files(ctx: RunContext[AnalyserAgentDependencies]) -> List[dict]:
    """Get the list of files and their properties from the repository"""
    return await project_file_list(ctx.deps.project_id)


# CSV describer tool
@AnalyserAgent.tool_plain(docstring_format="sphinx", require_parameter_descriptions=True)
async def get_csv_summary(instructions: str, file_url: str) -> str:
    """
    Returns a summary of the data in the CSV file
    :param instructions: Instructions on what to do with the csv files
    :param file_url: The url of the CSV file to be analysed. Takes single url
    :return: A summary of the data in the CSV file
    """
    response = await csv_analyser.run(
        f"""
        <INSTRUCTIONS>
        {instructions}
        </INSTRUCTIONS>
        
        <FILE_URLS>
        {file_url}
        <FILE_URL>
        """
    )
    print(response.usage())
    return response.data


# PDF describer tool
@AnalyserAgent.tool(docstring_format='sphinx', require_parameter_descriptions=True)
async def get_pdf_summaries(ctx: RunContext[AnalyserAgentDependencies], instructions: str, file_ids: str) -> str:
    """
    Returns the summary of a list of pdfs or a single one based on instructions
    :param ctx: Context of the run
    :param instructions: instructions on what to do with the pdfs it is given
    :param file_ids: Ids of the pdf files that actions should be performed on
    :return: Returns the result of the analysis
    """
    template = TemplateEngine(
        path='./src/utils/prompts/prompts.toml',
        section="AGENTS",
        template_name="pdf_analyser",
    ).format(
        PDF_IDS=file_ids,
        INSTRUCTIONS=instructions,
    )

    ### Get response
    response = await pdf_analyser_agent.run(
        template,
        deps=ctx.deps
    )
    return response.data
