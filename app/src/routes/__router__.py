import json
import os
from datetime import date

import unstructured_client
from dotenv import load_dotenv
from fastapi import APIRouter
from rich import print
from unstructured_client.models import operations, shared

### Import all the routes
from src.routes.agent_router import agent_router
from src.routes.file_router import file_router
from src.routes.ollama_router import ollama_router

app_router = APIRouter()
load_dotenv()
client = unstructured_client.UnstructuredClient(
    api_key_auth="jZHOgOoifmT4cagpmgDkgVhsj322vE",
    server_url=os.getenv("UNSTRUCTURED_API_URL"), )


@app_router.get('/')
async def root():
    return {
        'message': 'Nubia server 2.0',
        'version': '2.0',
        'date': date.today().strftime('%B %d, %Y'),
    }


@app_router.get('/dent')
async def dent():
    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(
            files=shared.Files(
                content=open('./src/agents/report.pdf', 'rb'),
                file_name='./src/agents/report.pdf'
            ),
            strategy=shared.Strategy.AUTO,
            languages=['eng'],
            split_pdf_allow_failed=True,
            split_pdf_concurrency_level=15
        )
    )

    try:
        res = client.general.partition(request=req)
        element_dicts = [element for element in res.elements]

        print(element_dicts)

        json_elements = json.dumps(element_dicts, indent=4)
        with open('./output.json', 'w') as f:
            f.write(json_elements)

    except Exception as e:
        print(e)

    return 'Hello'


### Attach the routes
app_router.include_router(ollama_router)
app_router.include_router(agent_router)
app_router.include_router(file_router)
