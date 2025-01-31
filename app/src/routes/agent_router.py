from fastapi import APIRouter

from src.agents import agent
from src.utils import supabase

agent_router = APIRouter(prefix="/agent", tags=["agent"])


# ################################################
# ### Analyser AGent routes
# #################################################
@agent_router.get("/analyser/{project_id}/chat")
async def agent_root():
    messages = await supabase.table('messages').select().execute()
    result = await agent.run(
        'What is the csv hosted on https://ncqfadextqcbsnockmgm.supabase.co/storage/v1/object/public/project_files/c66434f3-feea-47b1-9cb8-efe94b158734/files/17c9845799407fb3717d5b66a7c542132cd681f0f4f6822c42a18f8420c5735c_2025_01_30T23_58_48_851Z about')
    print(result.usage())

    return result.data
