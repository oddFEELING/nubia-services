import os
from typing import Literal

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from src.agents.writer.types import StoryAgentDependencies, ChatReturnType, ConversationSummaryReturn
from src.tools import get_analysis_conversation
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
    You are a world-class journalist, specializing in writing compelling narratives. Your approach is insightful, efficient, and engaging, ensuring clarity while delivering high-value analysis in your stories.

    EFFICIENCY PRINCIPLES:
    - The stories you generate should be based solely on the insights from the information provided.

    CORE COMPETENCIES:
    
    1. Journalistic Writing and Storytelling:
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

    - Run get_analysis_conversation_summary() before story generation
    - Prioritize efficiency in every step
    - All generated stories must be based on the insights provided
    """,

    TASK=""" story generation guidelines:

    1. Journalistic Writing and Storytelling:
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

    5. Balanced & Objective Tone:
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

    # ################################################
    # ### TOOLS
    # ################################################

    ### GET CONVERSATION SUMMARY

    async def get_analysis_conversation_summary(self, ctx: RunContext[StoryAgentDependencies]) -> str:
        """
        MANDATORY FIRST STEP: Retrieve the conversation related to previous analysis.
        This tool MUST be called before using any other tools. No exceptions.

        :param ctx: The context of the story generation
        :return: A summary of detailed and comprehensive key findings of the analysis conversation
        """
        try:
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
                        
                        
                        Kindly summarize the attached conversation.
                        
                        <CONVERSATIONS>
                        {str(messages)}
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
