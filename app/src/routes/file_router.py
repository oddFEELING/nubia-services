from typing import List

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from rich import print

from src.tools.qdrant import get_nodes
from src.utils.loaders import PDFLoader
from src.utils.loaders.chunker import chunk_files
from src.utils.supabase import supabase

file_router = APIRouter(prefix="/files", tags=["files"])


# ################################################
# ### Index new files
# #################################################
async def process_files_background(file_ids: List[str]):
    """
    Background task to process and index files
    :param file_ids: List of file IDs to process
    """
    files = (supabase
             .table('files')
             .update({"index_status": "pending"})
             .in_("id", file_ids)
             .execute())

    doc_list = []
    collection = ''
    if files:
        # Parse files
        for file in files.data:
            try:
                docs = await PDFLoader(file['file_url']).cloud_load(file)
                doc_list.extend(docs)
                collection = f"proj_{file['project_id']}"
            except Exception as e:
                print(f"Error processing file {file['id']}: {str(e)}")
                print(e)
                (supabase
                 .table('files')
                 .update({"index_status": "failed"})
                 .in_("id", file_ids)
                 .execute())
                return

        # Index files
        if collection:
            try:
                await chunk_files(doc_list, collection)
                (supabase
                 .table('files')
                 .update({"index_status": "indexed"})
                 .in_("id", file_ids)
                 .execute())
            except Exception as e:
                print(e)
                (supabase
                 .table('files')
                 .update({"index_status": "failed"})
                 .in_("id", file_ids)
                 .execute())
                return


@file_router.post('/add-index')
async def add_file_index(file_ids: List[str], background_tasks: BackgroundTasks):
    """
    Starts background processing of files for indexing
    :param file_ids: Ids of files to index
    :param background_tasks: FastAPI BackgroundTasks instance
    :return: Dict with status message
    """
    # Add the processing function to background tasks
    background_tasks.add_task(process_files_background, file_ids)

    return {
        "status": "File uploaded and index processing",
        "message": f"Started processing {len(file_ids)} files in the background",
        "file_ids": file_ids
    }


# ################################################
# ### Retrieve indexes based on query and file_id
# #################################################
class TestQueryBody(BaseModel):
    query: str
    collection: str
    file_ids: List[str]


@file_router.post("/test-index")
async def test_index(body: TestQueryBody):
    nodes = get_nodes(collection=body.collection, query=body.query, file_ids=body.file_ids)
    print(nodes)
    return nodes
