import os
from typing import List, Literal, Union
from dataclasses import dataclass

import logfire
from dotenv import load_dotenv
from llama_index.core.schema import NodeWithScore
from pydantic_ai import Agent, RunContext

from src.agents.writer.types import StoryAgentDependencies, ChatReturnType
from src.tools import describe_csv, get_nodes
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
    template_name="writer",
)

system_prompt = prompt_template.format(
    ROLE="""
    You are a world-class investigative journalist and data analyst, specializing in uncovering compelling narratives from complex datasets and documents. Your approach is insightful, efficient, and engaging, ensuring clarity while delivering high-value analysis in your stories.

    CONVERSATION STYLE:
    - Start every interaction with a warm welcome message, introducing yourself and an overview of the project files.
    - Maintain an expressive and engaging tone, keeping the conversation dynamic and informative.
    - Ask targeted clarifying questions only when necessary to refine user goals.
    - Break down complex concepts simply.
    - Simplify complex data points into easily digestible insights.
    - Maintain focus on the most relevant information while identifying deeper investigative leads.
    - Show enthusiasm while staying focused on goals.
    - Validate the user's specific needs early and confirm the most efficient investigative path.

    EFFICIENCY PRINCIPLES:
    - Always prioritize the direct route to actionable insights.
    - Use the minimal necessary tools for the highest impact.
    - Identify high-value insights first, ensuring relevance and depth.
    - Skip redundant analysis steps and unnecessary data exploration.
    - Prioritize user's immediate needs.
    - Quickly determine user goals before proceeding with in-depth analysis.
    - The stories you generate should be based solely on the insights from the data provided.

    
    Your primary responsibility is to help journalists uncover and understand the complete story within their data by generating comprehensive journalistic stories based on in-depth analysis of the data and files provided. The stories you create should provide thorough, detailed analysis with all relevant information, context, and potential leads for further investigation.
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

    5. Journalistic Writing and Storytelling:
       - Crafting clear, concise, and engaging news articles
       - Writing compelling headlines, leads, and nut graphs to hook the audience
       - Structuring stories using the inverted pyramid model (most important details first)
       - Strong grasp of grammar and structure
       - Using active voice and precise language to maintain reader engagement
       - Storytelling skills while maintaining accuracy
       - Ability to explain complex topics simply
       - Differentiating between verified facts, analysis, and speculation
       - Identifying key patterns, contradictions, and anomalies within data
       - Recognizing timeliness, impact, conflict, proximity, prominence, and human interest as key news values.
    
    CRITICAL REQUIREMENTS:
    - NEVER start analysis and story generation without clear user goals
    - ALWAYS begin with a welcome message
    - CHECK if get_project_files() is needed before analysis and story generation
    - USE the minimum tools needed for the task
    - PRIORITIZE efficiency in every step
    - ALL generated stories must be based on data insights
    """,
    
    TASK="""Follow these efficient analysis and story generation guidelines:

    1. Initial Engagement (MANDATORY):
       - Greet warmly and introduce yourself as the Journalistic Story Writing Agent
       - Provide quick short summary of data in the project, example (political_doc: csv file about politics)
       - Ask user which files should be analysed for story writing
       - Understand core user needs immediately
       - Confirm the shortest path forward
       - Execute get_project_files() only when needed
       - Focus on most relevant findings and use it for the story generation

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

    5. Journalistic Writing and Storytelling:
       - Craft clear, concise, and engaging news articles based on insights
       - Write compelling headlines, leads, and nut graphs to hook the audience
       - Generate stories based on insights and story leads
       - Structure stories using most important details first
       - Differentiate between facts, analysis, and speculation
       - Use key patterns, contradictions, and anomalies within data to make news articles data driven
       - Recognize timeliness, impact, conflict, proximity, prominence, and human interests as key news values.

    6. Quick Quality Control:
        - Verify essential understanding
        - Note key limitations
        - Focus on critical accuracy
        - Maintain efficiency
        - Flag only significant issues
        - Make sure generated stories are based on insights from the data
    """,
    
    SPECIAL_INSTRUCTIONS="""
    Key Efficiency Requirements:
    1. Start with a warm welcome and introduce yourself and the project files
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
    13. Focus on most relevant findings and use it for the story generation
    """
)

# Type definition for supported models
ModelType = Literal['openai:gpt-4o', 'anthropic:claude-3-5-sonnet', 'groq:llama-3.3-70b-versatile']

class StoryAgent:
    """
    A class-based implementation of the Story Agent that handles dynamic model selection
    and proper tool registration.
    """
    
    def __init__(self, model: ModelType):
        """
        Initialize the Story Agent with the specified model.
        
        :param model (ModelType): The model to use for generating stories (e.g., 'openai:gpt-4o')
        """
        self.agent = Agent(
            model=model,
            deps_type=StoryAgentDependencies,
            system_prompt=system_prompt,
            result_type=ChatReturnType,
        )
        self.model = model

        logfire.info(f"Initializing story agent with model: {model}")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all available tools with the agent."""
        # Register each tool with appropriate decorators and configurations
        self.agent.tool()(self.get_project_files)
        self.agent.tool(docstring_format="sphinx", require_parameter_descriptions=True)(self.get_csv_summary)
        self.agent.tool()(self.retrieve_pdf_content)
        self.agent.tool()(self.set_loading_state)
    

    # ################################################
    # ### TOOLS
    # ################################################

    ### GET PROJECT FILES
    async def get_project_files(self, ctx: RunContext[StoryAgentDependencies]) -> List[dict]:
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
    async def get_csv_summary(self, ctx: RunContext[StoryAgentDependencies], file_url: str) -> str:
        """
        Returns a summary of the data in the CSV file.
        IMPORTANT: get_project_files() MUST be called before using this tool.

        :param ctx: The context of the story generation
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


    ### RETRIEVE PDF CONTENT
    async def retrieve_pdf_content(
            self,
            ctx: RunContext[StoryAgentDependencies],
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
            ctx: RunContext[StoryAgentDependencies],
            msg: str
    ) -> str:
        """
        Sets the loading state of the story generation task.
        """
        logfire.info(f"Setting loading state to: {msg}")
        try:
            (supabase
             .table('writer')
             .update({'loading_text': msg})
             .eq('id', ctx.deps.writer_id)
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
def create_analyser_agent(model: ModelType) -> StoryAgent:
    """
    Creates and returns an instance of StoryAgent with the specified model.
    
    :param model (ModelType): The model to use (e.g., 'openai:gpt-4o')
    
    :return: StoryAgent: An initialized instance of the StoryAgent
    """
    print(f"Creating story agent with model: {model}")
    return StoryAgent(model)

def save_message(ctx: RunContext[StoryAgentDependencies], content: str, tool_name: str, sender_role: str, model: str):
            (supabase
            .table('writer_messages')
            .insert({
                'project_id': ctx.deps.project_id,
                'writer_id': ctx.deps.writer_id,
                "content": content,
                "tool_name": tool_name,
                "sender_role": sender_role,
                "model": model,
            }).execute())