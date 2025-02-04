import os
from typing import List

from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.extractors import (
    TitleExtractor,
    SummaryExtractor,
    KeywordExtractor,
    QuestionsAnsweredExtractor,
    DocumentContextExtractor,
)
from llama_index.core.node_parser import MarkdownNodeParser, TokenTextSplitter
from llama_index.core.storage.docstore.simple_docstore import SimpleDocumentStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
 
# Load environment variables
load_dotenv()
qdrant_host = os.getenv('QDRANT_HOST')
llama_cloud_key = os.getenv('LLAMA_CLOUD_API_KEY')


async def chunk_files(docs: List[Document], collection: str):
    """
    Process and chunk documents using LlamaIndex pipeline
    
    :param collection:
    :param docs: List of Document objects to process
    :return: Processed nodes with extracted metadata
    """
    llm = OpenAI(
        model='gpt-4o-mini',
    )

    # Create vector client
    vector_client = QdrantClient(
        host=qdrant_host,
        port=6333,
    )

    # Initialize document store
    docstore = SimpleDocumentStore()

    # Create vector store instance from client
    vector_store = QdrantVectorStore(client=vector_client, collection_name=collection)

    # LLama index storage context
    storage_context = StorageContext.from_defaults(docstore=docstore, vector_store=vector_store)

    # TRANSFORMATIONS - Text Splitter
    text_splitter = TokenTextSplitter(
        separator=' ',
        chunk_size=1500,
        chunk_overlap=50,
    )

    # Add documents to document store
    docstore.add_documents(docs)

    # TRANSFORMATIONS - Context extractor
    context_extractor = DocumentContextExtractor(
        docstore=docstore,
        vector_store=vector_store,
        max_context_size=128000,
        llm=llm,
        oversized_document_strategy="warn",
        max_output_tokens=8000,
        key="context",
    )

    # Define base transformations
    transformations = [
        text_splitter,  # Split text first
        MarkdownNodeParser(),
        context_extractor,
        TitleExtractor(nodes=10, llm=llm),
        SummaryExtractor(llm=llm),
        KeywordExtractor(llm=llm),
        QuestionsAnsweredExtractor(questions=5, llm=llm),
    ]

    # Add documents to vector store
    try:
        index = VectorStoreIndex.from_documents(
            documents=docs,
            storage_context=storage_context,
            embed_model=OpenAIEmbedding(),
            transformations=transformations,
            show_progress=True,
        )
        print(f'Indexing complete for index: {index.index_id} in collection: {collection}')

    except Exception as e:
        print(f"Error during index creation: {str(e)}")
        raise
