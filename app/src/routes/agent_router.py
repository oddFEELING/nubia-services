from dataclasses import dataclass
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic_ai.messages import ModelResponse, ModelRequest, TextPart, UserPromptPart, ToolReturnPart

from src.agents import AnalyserAgent, AnalyserAgentDependencies
from src.agents import StoryAgent, StoryAgentDependencies
from src.tools import get_story_details, project_file_list, parse_files
from src.utils import supabase
import logfire
from pydantic_ai import Agent
from pydantic import Field, BaseModel
from rich.pretty import pprint
agent_router = APIRouter(prefix="/agent", tags=["agent"])


# ################################################
# ### Analyser Agent routes
# #################################################
@dataclass
class AnalyserAgentRouteBody:
    project_id: str
    analysis_id: str
    model: str = 'groq:llama-3.3-70b-versatile'
 

async def run_analyser_agent(body: AnalyserAgentRouteBody, message_model: List[ModelResponse], model: str = 'groq:llama-3.3-70b-versatile'):
    try:
        print('Starting analyser agent background task...')
        result = await AnalyserAgent(model=model).run(
            user_prompt=message_model[0].parts[0].content
            if len(message_model) > 0 else "Hello There",
            message_history=message_model,
            deps=AnalyserAgentDependencies(project_id=body.project_id, analysis_id=body.analysis_id),
        )
        

        (supabase
         .table('analysis_messages')
         .insert({
            'project_id': body.project_id,
            'analyses_id': body.analysis_id,
            "content": result.data.content,
            "options": result.data.options,
            "sender_role": 'assistant',
            "model": model,
            "usage": str(result.usage().total_tokens)
        }).execute())

        (supabase
         .table('analyses')
         .update({'loading_text': '', "last_run_success": True})
         .eq('id', body.analysis_id)
         .execute())

    except Exception as e:
        (supabase
         .table('analyses')
         .update({'loading_text': 'Previous run failed.', "last_run_success": False})
         .eq('id', body.analysis_id)
         .execute())
        print(f"Error in analyser agent background task: {str(e)}")
        # Log the full error traceback for debugging
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        raise  # Re-raise the exception after logging


@dataclass
class NameAnalysesReturn:
    title: str = Field(description="A very short 4-6 word name of the analyses")
    description: str = Field(description="A short description phrase of the analyses")

async def name_analyses(body: AnalyserAgentRouteBody, messages: List[dict]):
    client = Agent(model="openai:gpt-4o-mini", result_type=NameAnalysesReturn)
    analyses_name = await client.run(
        user_prompt=f"""an analyses has been going on for a while now with the following conversations: 
                <conversations>
                {messages}
                </conversations>
                give the analyses a name and description based on the conversations"""
    )
    (supabase
     .table('analyses')
     .update({
         'title': analyses_name.data.title, 
         'description': analyses_name.data.description, 
         'loading_text': "Giving the analysis a name..."
     })
     .eq('id', body.analysis_id)
     .execute())
    


@agent_router.post("/analyser/chat")
async def analyser_agent(body: AnalyserAgentRouteBody, background_tasks: BackgroundTasks):
    messages = (supabase
                .table('analysis_messages')
                .select("*")
                .eq('analyses_id', body.analysis_id)
                .order('created_at', desc=True)
                .execute())

    analysis = (supabase
     .table('analyses')
     .update({'loading_text': 'loading...', "last_run_success": True})
     .eq('id', body.analysis_id)
     .execute())


    ### Create pydantic model from messages
    messages_model = []
    for message in messages.data:
        if message['sender_role'] == "user":
            messages_model.append(ModelRequest(
                kind="request",
                parts=[
                    UserPromptPart(
                        content=message['content'],
                        part_kind='user-prompt',
                    )   
                ]
            ))
        elif message['sender_role'] == 'assistant':
            messages_model.append(ModelResponse(
                kind='response',
                parts=[TextPart(content=message['content'], part_kind='text')]
            ))
        elif message['sender_role'] == 'tool':
            messages_model.append(ModelResponse(
                kind='response',
                parts=[
                    TextPart(
                        content=f"Tool: {message['tool_name']}\n\n{message['content']}",
                        part_kind='text',
                    ),
                ],
            ))

    background_tasks.add_task(run_analyser_agent, body, messages_model, body.model)
    print(analysis.data)
    if analysis.data[0]['title'] == 'New Analysis' and len(messages.data) > 8:
        background_tasks.add_task(name_analyses, body, messages.data)

    
    return {
        "status": "ok",
    }



# ################################################
# ### Story Agent routes
# #################################################
@dataclass
class StoryAgentRouteBody(BaseModel):
    analysis_id: Optional[str] = None
    story_id: str
    prompt: Optional[str] = None
    model: str = 'groq:llama-3.3-70b-versatile'
  

async def run_story_agent(body: StoryAgentRouteBody, project_id: str, model: str = 'groq:llama-3.3-70b-versatile'):
    try:
        print('Starting story agent background task...')

        if body.analysis_id is None:
        
            result = await StoryAgent(model=model).run(
                user_prompt=f"""
                                You are an expert journalist with a deep understanding of storytelling. Your task is to analyze files and transform findings into a compelling, well-structured, and engaging journalistic story.
                                Make the story compelling, informative, and impactful. Ensure it reads like a high-quality article suitable for publication in a top-tier news outlet.
                                <USER_REQUEST>
                                {body.prompt}
                                </USER_REQUEST>
                            """,
                deps=StoryAgentDependencies(story_id=body.story_id, project_id=project_id, analysis_id=body.analysis_id),
            )
        
        else:
        
            result = await StoryAgent(model=model).run(
                user_prompt=f"""
                                You are an expert journalist with a deep understanding of storytelling. Your task is to analyze files and transform findings into a compelling, well-structured, and engaging journalistic story.
                                Make the story compelling, informative, and impactful. Ensure it reads like a high-quality article suitable for publication in a top-tier news outlet.
                                <USER_REQUEST>
                                {body.prompt}
                                </USER_REQUEST>

                                Also use the get_analysis_conversation_summary tool to get additional context and insights for the story generation.
                            """,
                deps=StoryAgentDependencies(story_id=body.story_id, project_id=project_id, analysis_id=body.analysis_id),
            )
        
        
        pprint(result.data.content)

        (supabase
         .table('stories')
         .update({'content': result.data.content, "last_run_success": True})
         .eq('id', body.story_id)
         .execute())

    except Exception as e:
        (supabase
         .table('stories')
         .update({'content': 'Failed to run task to generate story.', "last_run_success": False})
         .eq('id', body.story_id)
         .execute())
        print(f"Error in story agent background task: {str(e)}")
        # Log the full error traceback for debugging
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        raise  # Re-raise the exception after logging


@agent_router.post("/story/chat")
async def story_agent(body: StoryAgentRouteBody, background_tasks: BackgroundTasks):

    result = await get_story_details(body.story_id)
    project_id = result[0]["projectId"]
    #new_result = await project_file_list(project_id)
    #txt = await parse_files(body.file_url)
    background_tasks.add_task(run_story_agent, body, project_id, body.model)
    
    
    
    return {
        "status": "ok",
        #"result": txt
    }
