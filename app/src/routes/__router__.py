
from datetime import date

from dotenv import load_dotenv
from fastapi import APIRouter
from rich import print

### Import all the routes
from src.routes.agent_router import agent_router
from src.routes.file_router import file_router
from src.routes.ollama_router import ollama_router

app_router = APIRouter()
load_dotenv()


@app_router.get('/')
async def root():
    return {
        'message': 'Nubia server 2.0',
        'version': '2.0',
        'date': date.today().strftime('%B %d, %Y'),
    }


### Attach the routes
app_router.include_router(ollama_router)
app_router.include_router(agent_router)
app_router.include_router(file_router)
