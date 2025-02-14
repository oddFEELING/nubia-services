import os
from typing import List, Literal, Union
from dataclasses import dataclass

import logfire
from dotenv import load_dotenv
from llama_index.core.schema import NodeWithScore
from pydantic_ai import Agent, RunContext

from src.agents.analyser.types import AnalyserAgentDependencies, ChatReturnType
from src.tools import describe_csv, plot_x_y, PlotXYParams, get_nodes
from src.tools import project_file_list
from src.utils import supabase
from src.utils.prompts.template import TemplateEngine

# Load environment variables and configure logging
load_dotenv()
logfire.configure(send_to_logfire='if-token-present')
api_key = os.getenv('ANTHROPIC_API_KEY')

# Initialize system prompt template
prompt_template = TemplateEngine(
    path='./src/utils/prompts/prompts.toml',
    section="ORCHESTRATORS",
    template_name="main",
)

system_prompt = prompt_template.format(
    ROLE="""
    You are a world class professional journalist and efficient analysis companion specializing in journalistic data and document analysis. Your personality is warm and focused and comprehensive, always ensuring you understand exactly what the user needs and finding the most direct path to valuable insights.

    CONVERSATION STYLE:
    - Always start with a warm welcome message introducing yourself and an overview of the project files
    - Be conversational and expressive
    - Ask targeted clarifying questions when needed
    - Break down complex concepts simply
    - Focus on the most relevant information
    - Show enthusiasm while staying focused on goals
    - Validate user's specific needs quickly

    EFFICIENCY PRINCIPLES:
    - Always choose the most direct path to the solution
    - Use the minimum number of tools necessary
    - Focus on high-value insights first
    - Avoid redundant analysis steps
    - Prioritize user's immediate needs
    - Skip unnecessary data exploration

    3. Initial Engagement (MANDATORY):
    - Warm welcome and engaging introduction
    - Provide quick short summary data in the project example (political_doc: csv file about politics)
    - Understand core user needs immediately
    - Confirm the shortest path forward
    - Execute get_project_files() only when needed
    - Focus on most relevant findings
    - Get quick agreement on approach

    Your primary responsibility is to help journalists uncover and understand the complete story within their data, leaving no stone unturned. You should provide thorough, detailed analysis with all relevant information, context, and potential leads for further investigation.
    Start every new conversation with a warm welcome and a short introduction. Make sure to be very expressive and conversational without being strictly formal and short.

    CORE COMPETENCIES:
    1. Efficient Data Analysis:
       - Quick pattern recognition
       - Focused trend analysis
       - Rapid fact verification
       - Targeted statistical assessment
       - Essential cross-validation
       - Strategic time-series analysis

    2. Streamlined Document Processing:
       - Key content extraction
       - Critical connection identification
       - Focused information retrieval
       - Quick credibility assessment
       - Essential metadata analysis

    3. Direct Insight Generation:
       - Core evidence chain building
       - Key pattern recognition
       - Essential timeline construction
       - Critical narrative identification

    4. Insight Explainability:
       - Ensure clarity in presenting insights
       - Highlight key findings with clear explanations
       - Simplify complex data points for better understanding
       - Use visual aids where possible to enhance comprehension
       - Provide context for each insight to show relevance
       - Address potential questions or confusions proactively
       - Validate insights with supporting data and evidence
    
    CRITICAL REQUIREMENTS:
    - NEVER start analysis without clear user goals
    - ALWAYS begin with a welcome message
    - check if get_project_files() is needed before analysis
    - Use the minimum tools needed for the task
    - Prioritize efficiency in every step
    """,
    
    TASK="""Follow these efficient analysis guidelines:

    1. Initial Engagement (MANDATORY):
       - Warm welcome and engaging introduction
       - Provide quick short summary data in the project example (political_doc: csv file about politics)
       - Understand core user needs immediately
       - Confirm the shortest path forward
       - Execute get_project_files() only when needed
       - Focus on most relevant findings

    2. Efficient Workflow:
       - Choose most direct analysis path
       - make sure you have access to all the files in the project
       - Use minimal necessary tools
       - Keep user informed of progress
       - Ask only essential questions
       - Suggest fastest viable approach
       - Adapt quickly to feedback

    3. Tool Usage Protocol:
       - Use tools only when necessary
       - Choose most efficient tool for task
       - Avoid redundant tool calls
       - Focus on essential data points
       - Keep process streamlined

    4. Insight Generation:
    - Uncover all relevant patterns and connections
    - Identify key narrative threads
    - Map relationships between data points
    - Flag unusual patterns or anomalies
    - Provide comprehensive evidence chains
    - Suggest angles for further investigation
    - Document potential story leads

    5. Quick Quality Control:
        - Verify essential understanding
        - Note key limitations
        - Focus on critical accuracy
        - Maintain efficiency
        - Flag only significant issues""",
    
    SPECIAL_INSTRUCTIONS="""
    Key Efficiency Requirements:
    1. Start warm welcome and introduce yourself and the project files
    2. Get to core user needs quickly
    3. Use minimal necessary tools
    4. Focus on essential findings
    5. Choose direct solution paths
    6. Provide richly explained relevant updates
    7. Be efficient yet friendly
    8. Focus on immediate value
    9. Avoid unnecessary steps
    10. Maintain solution focus
    11. Never withhold relevant information
    12. Explain all potential implications
    """
)

# Type definition for supported models
ModelType = Literal['openai:gpt-4o', 'anthropic:claude-3-5-sonnet', 'groq:llama-3.3-70b-versatile']

class AnalyserAgent:
    """
    A class-based implementation of the Analyser Agent that handles dynamic model selection
    and proper tool registration.
    """
    
    def __init__(self, model: ModelType):
        """
        Initialize the Analyser Agent with the specified model.
        
        :param model (ModelType): The model to use for analysis (e.g., 'openai:gpt-4o')
        """
        self.agent = Agent(
            model=model,
            deps_type=AnalyserAgentDependencies,
            system_prompt=system_prompt,
            result_type=ChatReturnType,
        )
        self.model = model

        logfire.info(f"Initializing analyser agent with model: {model}")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all available tools with the agent."""
        # Register each tool with appropriate decorators and configurations
        self.agent.tool()(self.get_project_files)
        self.agent.tool(docstring_format="sphinx", require_parameter_descriptions=True)(self.get_csv_summary)
        self.agent.tool()(self.plot_y_over_x_chart)
        self.agent.tool()(self.retrieve_pdf_content)
        self.agent.tool()(self.set_loading_state)
    

    # ################################################
    # ### TOOLS
    # ################################################

    ### GET PROJECT FILES
    async def get_project_files(self, ctx: RunContext[AnalyserAgentDependencies]) -> List[dict]:
        """
        MANDATORY FIRST STEP: Get the list of files and their properties from the repository.
        This tool MUST be called before using any other tools. No exceptions.

        :return: List[dict] - A list of dictionaries containing file information
        """
        try:
            files = await project_file_list(ctx.deps.project_id)
            if not files:
                raise ValueError("No files found in the project")
            save_message(ctx, str(files), 'get_project_files', 'tool', self.model)
    
            return files
        except Exception as e:
            logfire.error(f"Error getting project files: {str(e)}")
            return "Failed to retrieve project files. This step is mandatory before proceeding with analysis."

    ### GET CSV SUMMARY
    async def get_csv_summary(self, ctx: RunContext[AnalyserAgentDependencies], file_url: str) -> str:
        """
        Returns a summary of the data in the CSV file.
        IMPORTANT: get_project_files() MUST be called before using this tool.

        :param ctx: The context of the analysis
        :param file_url: The url of the CSV file to be analysed (obtained from get_project_files)
        :return: A summary of the data in the CSV file
        """
        try:
            if not file_url or 'example.com' in file_url:  # Basic validation to catch placeholder URLs
                return "Invalid file URL. Please ensure get_project_files() was called first to obtain valid file URLs"

            logfire.info(f"Getting summary of {file_url}")
            data = describe_csv(file_url)
            if not data:
                return "No data found in CSV file"
            save_message(ctx, str(data), 'get_csv_summary', 'tool', self.model)
            return str(data)
        except Exception as e:
            logfire.error(f"Error analyzing CSV file: {str(e)}")
            if 'example.com' in str(e) or '404' in str(e):
                return "Invalid file URL detected. Please ensure get_project_files() was called first and returned valid files"
            
            return f"Failed to analyze CSV file: {str(e)}"

    ### PLOT Y OVER X CHART
    async def plot_y_over_x_chart(
            self,
            ctx: RunContext[AnalyserAgentDependencies],
            params: PlotXYParams
    ) -> str:
        """
        Plots a chart of a key y_key on the y axis against another key x x_key
        on the x axis.
        """
        try:
            logfire.info(f"Plotting {params.x_key} over {params.y_key} with chart type {params.chart_type}")
            result = plot_x_y(
                project_id=ctx.deps.project_id,
                analysis_id=ctx.deps.analysis_id,
                params=params
            )
            if not result:
                raise ValueError("Failed to generate plot")
            save_message(ctx, str(result), 'plot_y_over_x_chart', 'tool', self.model)
            return result
        except Exception as e:
            logfire.error(f"Error creating plot: {str(e)}")
            raise ValueError(f"Failed to create plot: {str(e)}")

    ### RETRIEVE PDF CONTENT
    async def retrieve_pdf_content(
            self,
            ctx: RunContext[AnalyserAgentDependencies],
            instructions: str,
            file_ids: List[str]
    ) -> List[NodeWithScore]:
        """
        Retrieves and analyzes content from specified PDF documents based on query instructions.
        """
        try:
            logfire.info(f"Retrieving content from PDFs with query: {instructions}")
            if not file_ids:
                raise ValueError("No file IDs provided for analysis")
            
            nodes = get_nodes(
                collection=f'proj_{ctx.deps.project_id}',
                query=instructions,
                file_ids=file_ids
            )
            
            if not nodes:
                raise ValueError("No relevant content found in the specified PDFs")
            save_message(ctx, str(nodes), 'retrieve_pdf_content', 'tool', self.model)
            return nodes
        except Exception as e:
            logfire.error(f"Error retrieving PDF content: {str(e)}")
            raise ValueError(f"Failed to retrieve PDF content: {str(e)}")

    ### SET LOADING STATE
    async def set_loading_state(
            self,
            ctx: RunContext[AnalyserAgentDependencies],
            msg: str
    ) -> str:
        """
        Sets the loading state of the analysis.
        """
        logfire.info(f"Setting loading state to: {msg}")
        try:
            (supabase
             .table('analyses')
             .update({'loading_text': msg})
             .eq('id', ctx.deps.analysis_id)
             .execute())
            return 'message sent, you can proceed.'
        except Exception as e:
            logfire.error(f"Error sending message to user: {str(e)}")
            return f"Failed to send message to user: {str(e)}"

    # ################################################
    # ### END OF TOOLS
    # ################################################

    async def run(self, *args, **kwargs):
        """
        Run the agent with the given arguments.
        Delegates to the underlying agent's run method.
        """
        return await self.agent.run(*args, **kwargs)

# Factory function to create an instance of AnalyserAgent
def create_analyser_agent(model: ModelType) -> AnalyserAgent:
    """
    Creates and returns an instance of AnalyserAgent with the specified model.
    
    :param model (ModelType): The model to use (e.g., 'openai:gpt-4o')
    
    :return: AnalyserAgent: An initialized instance of the AnalyserAgent
    """
    print(f"Creating analyser agent with model: {model}")
    return AnalyserAgent(model)

def save_message(ctx: RunContext[AnalyserAgentDependencies], content: str, tool_name: str, sender_role: str, model: str):
            (supabase
            .table('analysis_messages')
            .insert({
                'project_id': ctx.deps.project_id,
                'analyses_id': ctx.deps.analysis_id,
                "content": content,
                "tool_name": tool_name,
                "sender_role": sender_role,
                "model": model,
            }).execute())