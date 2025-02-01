from dataclasses import dataclass
from typing import List

from llama_index.core.schema import NodeWithScore
from pydantic_ai import Agent, RunContext

from src.tools import get_nodes


# ################################################
# ### Agent
# #################################################
@dataclass
class PDFAnalyserAgentDependencies:
    project_id: str


pdf_analyser_agent = Agent(
    'claude-3-5-sonnet-latest',
    deps_type=PDFAnalyserAgentDependencies,
    name='PDF Analyser',
    result_type=str,
)


# ################################################
# ### Tools
# #################################################
@pdf_analyser_agent.tool(docstring_format='sphinx', require_parameter_descriptions=True)
async def get_retrieve_pdf_content(
        ctx: RunContext[PDFAnalyserAgentDependencies],
        instructions: str,
        file_ids: List[str]) -> List[NodeWithScore]:
    """
    Returns a list of retrieved nodes from a given list of pdf documents
    :param ctx: Context of the current run
    :param file_ids: ids of the pdf files to search through.
    :param instructions: Descriptive query text to use in retrieving document nodes. Takes multiple urls
    :return: A list of nodes relevant to the query
    """
    return get_nodes(
        collection=f'proj_{ctx.deps.project_id}',
        query=instructions,
        file_ids=file_ids
    )
