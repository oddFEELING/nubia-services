from fastapi import APIRouter

from src.agents import agent

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.get("/")
async def agent_root():
    result = await agent.run('What is the csv about')
    print(result.usage())

    return result.data
