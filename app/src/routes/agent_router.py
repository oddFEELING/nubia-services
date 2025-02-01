from dataclasses import dataclass
from typing import List

from fastapi import APIRouter, BackgroundTasks
from pydantic_ai.messages import ModelResponse, ModelRequest, TextPart, UserPromptPart

from src.agents import AnalyserAgent, AnalyserAgentDependencies
from src.utils import supabase

agent_router = APIRouter(prefix="/agent", tags=["agent"])


# ################################################
# ### Analyser Agent routes
# #################################################
@dataclass
class AnalyserAgentRouteBody:
    project_id: str
    analysis_id: str
    prompt: str


async def run_analyser_agent(body: AnalyserAgentRouteBody, message_model: List[ModelResponse]):
    try:
        print('Starting analyser agent background task...')
        result = await AnalyserAgent.run(
            body.prompt,
            messages=message_model,
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
            "usage": str(result.usage().total_tokens)
        }).execute())

    except Exception as e:
        print(f"Error in analyser agent background task: {str(e)}")
        # Log the full error traceback for debugging
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        raise  # Re-raise the exception after logging


@agent_router.post("/analyser/chat")
async def analyser_agent(body: AnalyserAgentRouteBody, background_tasks: BackgroundTasks):
    messages = (supabase
                .table('analysis_messages')
                .select("*")
                .eq('analyses_id', body.analysis_id)
                .order('created_at', desc=True)
                .execute())

    ### Create pydantic model from messages
    messages_model = [
        ModelResponse(
            kind='response',
            parts=[
                TextPart(
                    content=message['content'],
                    part_kind='text'
                )])
        if message['sender_role'] == 'assistant'
        else ModelRequest(
            kind="request",
            parts=[
                UserPromptPart(
                    content=message['content'],
                    part_kind='user-prompt'
                )
            ])
        for message in messages.data]

    print(messages_model)

    background_tasks.add_task(run_analyser_agent, body, messages_model)
    return {
        "status": "ok",
    }
