from docx import Document

from llama_index.core import Document as Doc

# ################################################
# ### Loads docx files
# #################################################

def docx_txt_loader(file_url: str, file)-> Doc:
    """
    Parse and load docx file content
    :param file_url: the path to the file
    :param file: the file object 
    :return: Llama Index Document Object
    """

    content = Document(file_url)
    full_text = []
    for para in content.paragraphs:
        full_text.append(para.text)

    text = "\n\n".join(full_text)

    ###Create metadata attribute

    extra_info = {
                "file_name": file['display_name'],
                "tags": file['tags'],
                "file_extension": file['extension'],
                "file_id": file['id']
            }
    document = Doc(text, extra_info)

    return document