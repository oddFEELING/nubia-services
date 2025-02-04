import easyocr
from llama_index.core import Document as Doc

# ################################################
# ### Extract text from image files
# #################################################

def image_text_extractor(file_url: str, file)-> Doc:
    """
    Extract
    :param file_url: file url to process
    :return: Llama Index Document Object
    """

    reader = easyocr.Reader(['en'], gpu=False)
    content = reader.readtext(file_url, detail=0, paragraph=True)
    text = "\n\n".join(content)

    ###Create metadata attribute
    extra_info = {
                "file_name": file['display_name'],
                "tags": file['tags'],
                "file_extension": file['extension'],
                "file_id": file['id']
            }
    document = Doc(text, extra_info)

    return document