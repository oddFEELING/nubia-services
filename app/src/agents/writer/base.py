import os
from typing import Literal, List

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from llama_index.core.schema import NodeWithScore
from src.agents.writer.types import StoryAgentDependencies, ChatReturnType, ConversationSummaryReturn
from src.tools import get_analysis_conversation, project_file_list, describe_csv, get_nodes, parse_files
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
    You are a world-class journalist and journalist and data analyst, specializing in writing compelling narratives from complex datasets and documents. Your approach is insightful, efficient, and engaging, ensuring clarity while delivering high-value analysis in your stories.
    Your primary responsibility is to help journalists uncover and understand the complete story within their data by generating comprehensive journalistic stories based on in-depth analysis of the data and files provided. The stories you create should provide thorough, detailed analysis with all relevant information, context, and potential leads for further investigation.

    EFFICIENCY PRINCIPLES:
    - Always prioritize the direct route to actionable insights.
    - Use the minimal necessary tools for the highest impact.
    - Identify high-value insights first, ensuring relevance and depth.
    - Skip redundant analysis steps and unnecessary data exploration.
    - Prioritize user's immediate needs.
    - Quickly determine user goals before proceeding with in-depth analysis.
    - The stories you generate should be based solely on the insights from the data provided.


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

    - Check if get_project_files() is needed before analysis and story generation
    - Use the minimum tools needed for the task
    - Prioritize efficiency in every step
    - All generated stories must be based on the insights provided
    """,

    TASK=""" Follow these efficient analysis and story generation guidelines:

    1. Efficient Workflow:
       - Choose most direct analysis path
       - make sure you have access to all the files in the project
       - Use minimal necessary tools

    2. Tool Usage Protocol:
       - Use tools only when necessary
       - Choose most efficient tool for task
       - Avoid redundant tool calls
       - Focus on essential data points
       - Keep process streamlined

    3. Insight Generation:
    - Uncover all relevant patterns and connections
    - Identify key narrative threads
    - Map relationships between data points
    - Flag unusual patterns or anomalies
    - Provide comprehensive evidence chains
    - Suggest angles for further investigation
    - Document potential story leads

    4. Journalistic Writing and Storytelling:
       - Craft clear, concise, and engaging news articles based on insights
       - Write compelling headlines, leads, and nut graphs to hook the audience
       - Generate stories based on insights and story leads
       - Structure stories using most important details first
       - Differentiate between facts, analysis, and speculation
       - Use key patterns, contradictions, and anomalies within data to make news articles data driven
       - Recognize timeliness, impact, conflict, proximity, prominence, and human interests as key news values.
    """,

    SPECIAL_INSTRUCTIONS="""

    1. Accuracy and Credibility:
        - Ensure that all details are factually accurate and align with the provided summary.
        - Avoid making assumptions or adding unverifiable information.

    2. Engaging and Clear Narrative:
        - Write in a journalistic style that is informative, engaging, and accessible.
        - Use a strong lead to capture the reader's attention immediately.
        - Maintain logical flow and coherence throughout the story.
    
    3. Detailed and Comprehensive:
        - Expand on key findings with context and significance.
        - Include relevant background information if needed.
        - Highlight trends, patterns, or anomalies in a clear and structured manner.

    4. Compelling Storytelling:
        - Use vivid descriptions and powerful language to make the story impactful.
        - Include direct or paraphrased statements from sources if provided.
        - Frame the findings within a broader societal, economic, or political context to enhance relevance.

    5. Balanced and Objective Tone:
        - Present information neutrally and objectively while maintaining journalistic integrity.
        - If the findings are controversial, provide multiple perspectives where applicable
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
        self.agent.tool()(self.get_analysis_conversation_summary)
        self.agent.tool()(self.get_project_files)
        self.agent.tool(docstring_format="sphinx", require_parameter_descriptions=True)(self.get_csv_summary)
        self.agent.tool()(self.extract_text_from_pdf)
        self.agent.tool()(self.retrieve_pdf_file_context_from_vector_store)

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
            
    
            return files
        except Exception as e:
            logfire.error(f"Error getting project files: {str(e)}")
            return "Failed to retrieve project files. This step is mandatory before proceeding with analysis."

    
    ### GET CSV SUMMARY
    async def get_csv_summary(self, ctx: RunContext[StoryAgentDependencies], file_url: str) -> str:
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
            data = await describe_csv(file_url)
            if not data:
                return "No data found in CSV file"
            
            return str(data)
        except Exception as e:
            logfire.error(f"Error analyzing CSV file: {str(e)}")
            if 'example.com' in str(e) or '404' in str(e):
                return "Invalid file URL detected. Please ensure get_project_files() was called first and returned valid files"
            
            return f"Failed to analyze CSV file: {str(e)}"
        
    
    ### EXTRACT TEXT FROM PDF
    async def extract_text_from_pdf(self, ctx: RunContext[StoryAgentDependencies], file_url: str) -> str:
        """
        Extracts the text contained in a PDF file and returns the content in markdown format.
        IMPORTANT: get_project_files() MUST be called before using this tool.

        :param ctx: The context of the analysis and story generation
        :param file_url: The url of the PDF file to be analysed (obtained from get_project_files)
        :return: Full text contained in the PDF file in markdown format
        """
        try:
            if not file_url or 'example.com' in file_url:  # Basic validation to catch placeholder URLs
                return "Invalid file URL. Please ensure get_project_files() was called first to obtain valid file URLs"

            logfire.info(f"Extracting text from pdf  {file_url}")
            data = await parse_files(file_url)
            if not data:
                return "No text found in PDF file"
            
            return data
        except Exception as e:
            logfire.error(f"Error extracting text from PDF file: {str(e)}")
            if 'example.com' in str(e) or '404' in str(e):
                return "Invalid file URL detected. Please ensure get_project_files() was called first and returned valid files"
            
            return f"Failed to analyze PDF file: {str(e)}"
        
       
    ### RETRIEVE PDF FILE CONTEXT FROM VECTOR STORE
    async def retrieve_pdf_file_context_from_vector_store(
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
            
            nodes = await get_nodes(
                collection=f'proj_{ctx.deps.project_id}',
                query=instructions,
                file_ids=file_ids
            )
            
            if not nodes:
                raise ValueError("No relevant content found in the specified PDFs")
            
            return nodes
        except Exception as e:
            logfire.error(f"Error retrieving PDF content: {str(e)}")
            raise ValueError(f"Failed to retrieve PDF content: {str(e)}")
    
    ### GET CONVERSATION SUMMARY

    async def get_analysis_conversation_summary(self, ctx: RunContext[StoryAgentDependencies]) -> str:
        """
        Retrieves the conversation related to previous analysis and summarizes all the findings of the analysis.
        This tool should be called if only the value of analysis_id is not None. 
        
        :param ctx: The context of the story generation
        :return: A summary of detailed and comprehensive key findings of the analysis conversation
        """
        try:
            if ctx.deps.analysis_id is None:
                return "No analysis_id found, skip this step."
            
            else:
                messages = await get_analysis_conversation(ctx.deps.analysis_id)
                if not messages:
                    raise ValueError("No conversations found for the analysis")

                client = Agent(model="openai:gpt-4o-mini", result_type=ConversationSummaryReturn)
                findings_summary = await client.run(
                    user_prompt=f""" You are an advanced AI assistant specializing in generating structured, detailed, and comprehensive summaries of conversations that involved findings from an analysis. Your goal is to extract key findings, insights, and conclusions drawn from the conversation while maintaining clarity and objectivity. 
                            <GUIDELINES>
                            1. Comprehensiveness:
                                - Capture all key points from the conversation, ensuring no important findings are omitted.
                                - Provide a clear breakdown of the insights derived from the conversation.
                            2. Clarity and Structure:
                                - Present the summary in a well-structured format.
                                - Use bullet points or sections to organize information logically.
                            3. Key Information Extraction:
                                - Main Findings: Summarize the crucial insights derived from the conversation.
                                - Observations and Patterns: Highlight any trends, anomalies, or noteworthy details.
                                - Conclusions and Interpretations: Outline the implications of the findings.
                            4. Objectivity and Accuracy:
                                - Do not introduce assumptions beyond what was explicitly stated.
                                - Maintain a neutral and factual tone.
                            </GUIDELINES>
                            
                            
                            Kindly summarize the findings from the analysis contained in the attached conversation.
                            
                            <CONVERSATIONS>
                            {messages}
                            </CONVERSATIONS>
                            """
                )
    
                return findings_summary.data.content

        except Exception as e:
            logfire.error(f"Error getting analysis conversation: {str(e)}")
            return "Failed to retrieve analysis conversation. This step is mandatory before proceeding with story generation."
    
    
        
    # ################################################
    # ### END OF TOOLS
    # ################################################

    async def run(self, *args, **kwargs):
        """
        Run the agent with the given arguments.
        Delegates to the underlying agent's run method.
        """
        return await self.agent.run(*args, **kwargs)


# Factory function to create an instance of StoryAgent
def create_story_agent(model: ModelType) -> StoryAgent:
    """
    Creates and returns an instance of StoryAgent with the specified model.
    
    :param model (ModelType): The model to use (e.g., 'openai:gpt-4o')
    
    :return: StoryAgent: An initialized instance of the StoryAgent
    """
    print(f"Creating story agent with model: {model}")
    return StoryAgent(model)
