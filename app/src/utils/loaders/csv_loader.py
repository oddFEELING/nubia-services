import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv
from llama_extract import LlamaExtract
from pydantic import BaseModel

load_dotenv()

llama_cloud_key = os.getenv('LLAMA_CLOUD_API_KEY')

extractor = LlamaExtract()


@dataclass
class ExtractionSchema(BaseModel):
    men: List[str]
    women: List[str]


agent = extractor.create_agent('test-schema-3', data_schema=ExtractionSchema)
print(extractor.list_agents())
# results = extractor.extract_data(extraction_schema.id, [
#     'https://ncqfadextqcbsnockmgm.supabase.co/storage/v1/object/public/project_files/c66434f3-feea-47b1-9cb8-efe94b158734/files/c81b534ed7c88dd97d52f7ebc2644bc9b9e4319646e65b4d7948ea13baeeba30_2025_02_02T23_54_01_578Z'])

results = agent.extract('./suicide.csv')

print(results.data)

extractor.delete_agent('test-schema-3')
