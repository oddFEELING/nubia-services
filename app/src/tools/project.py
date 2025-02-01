from typing import List

from rich import print

from src.utils import supabase


async def project_file_list(project_id: str) -> List[dict]:
    """
    Get the files uploaded within a project
    :param project_id: Id of the project to query
    :return:
    """

    print(f'Getting project files for {project_id}')
    files = (supabase
             .table('files')
             .select(
        "id", "display_name", "file_url", "extension",
        "tags", "index_status"
    ).eq('project_id', project_id)
             .execute()
             )
    return files.data
