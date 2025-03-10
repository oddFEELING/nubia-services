from typing import List

from rich import print
from rich.pretty import pprint

from src.utils import supabase

 
async def get_story_details(story_id: str) -> List[dict]:
    """
    Fetches all the details associated with a story
    :param story_id: Id of the story to query
    :return: A list of dictionary object
    """

    print(f'Getting details of the story: {story_id}')
    result = (supabase
                .table('stories')
                .select("id", "projectId")
                .eq('id', story_id)
                .execute())
    
    return result.data
