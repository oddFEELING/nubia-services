import os
from llama_parse import LlamaParse
from dotenv import load_dotenv
from rich.pretty import pprint

load_dotenv()

llama_cloud_key = os.getenv('LLAMA_CLOUD_API_KEY')


async def parse_files(file_url: str)-> str:
    """
    Retrieves the content of a file and presents it in a markdown format
    :param file_url: The URL of the file whose content is to be extracted
    :return: A string of text
    """
    # Create parser
    parser = LlamaParse(
        api_key=llama_cloud_key,
        result_type='markdown',
        verbose=True,
        num_workers=8,  # Number of workers for sending API requests
        spreadsheet_extract_sub_tables=True,  # Identify sub tables within the file
        output_tables_as_HTML=True,  # Return table as html instead of markdown
    )
    
    docs = await parser.aload_data(
        file_path=file_url,
        )
    
    doc_text = []
    for doc in docs:
        doc_text.append(doc.text)

    
    return "\n\n".join(doc_text)