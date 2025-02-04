import os
from io import BytesIO
from typing import List

import pymupdf
import requests
from dotenv import load_dotenv
from llama_parse import LlamaParse
from pydantic import BaseModel
from pymupdf import Document

load_dotenv()

llama_cloud_key = os.getenv('LLAMA_CLOUD_API_KEY')


class PDFTextLoaderResponse(BaseModel):
    text: str
    segments: List[str]


# ################################################
# ### Main class
# #################################################
class PDFLoader:
    def __init__(self, file_url: str, ):
        self.file_url = file_url

        ### Fetch the pdf bytes from the URL
        response = requests.get(self.file_url)
        response.raise_for_status()  # Raise error if request fails

        ### Create a PyMuPDF doc from downloaded bytes
        self.pdf_data = BytesIO(response.content)

    def load_text(self) -> PDFTextLoaderResponse:
        """Reads the PDF and returns a PDFTextLoaderResponse object"""
        ### Read bytes
        doc: Document = pymupdf.open(stream=self.pdf_data, filetype='application/pdf')
        texts = []
        for page in doc:
            text = page.get_text()
            texts.append(text)

        ### Create the response object
        response = PDFTextLoaderResponse(
            segments=texts,
            text="\n\n".join(texts),
        )
        return response

    def load_images(self):
        """Load all the images in the pdf file"""
        ### Read bytes
        doc: Document = pymupdf.open(stream=self.pdf_data, filetype='application/pdf')

        all_images = []
        for idx in range(len(doc)):
            page = doc[idx]
            images = page.get_images()
            for img_idx, image in enumerate(images):
                base_img = doc.extract_image(image[img_idx])
                all_images.append(base_img)

        return all_images

    async def cloud_load(self, file):
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
            file_path=self.pdf_data,
            extra_info={
                "file_name": file['display_name'],
                "tags": file['tags'],
                "file_extension": file['extension'],
                "file_id": file['id']
            }
        )

        return docs
 