import os
from typing import List

from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()
qdrant_host = os.getenv('QDRANT_HOST')

client = QdrantClient(
    host=qdrant_host,
    port=6333
)


def get_nodes(collection: str, query: str, file_ids: List[str]) -> List[NodeWithScore]:
    """
    Get nodes from Qdrant vector store
    
    :param collection: Name of the collection to get nodes from
    :param query: Query to search for
    :param file_ids: ID of the file to get nodes from
    :return: List of LLamaIndex nodes with scores
    """
    if file_ids is None:
        file_ids = ['']

    # Create vector store instance
    vector_store = QdrantVectorStore(client=client, collection_name=collection)

    # Create filters
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key='file_id', operator=FilterOperator.ANY, value=file_ids)
        ]
    )

    # Create index from vector store
    index = VectorStoreIndex.from_vector_store(vector_store)

    # Get nodes from index
    nodes = (index.as_retriever(
        similarity_top_k=5,
        filters=filters)
             .retrieve(query))

    return nodes
