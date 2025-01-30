import os

from dotenv import load_dotenv
from fastapi import APIRouter
from ollama import Client
from qdrant_client import QdrantClient, models

load_dotenv()
qdrant_host = os.getenv('QDRANT_HOST')
ollama_router = APIRouter(prefix="/ollama", tags=['ollama'])
collection_name = 'test'

qclient = QdrantClient(
    host=qdrant_host,
    port=6333,
)


@ollama_router.post("/chat")
async def ollama_chat(prompt: str):
    client = Client(
        host="http://ollama:11434"
    )
    res = client.embeddings("llama3.2", prompt=prompt)
    embeddings = res['embedding']

    vectors_config = models.VectorParams(
        size=len(embeddings),
        distance=models.Distance.COSINE
    )

    if not qclient.collection_exists(collection_name):
        qclient.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config
        )

    qclient.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=1,
                vector=embeddings,
                payload={"text": prompt}
            )
        ]
    )

    response = client.generate(
        model='llama3.2',
        prompt=prompt,
    )

    return response
