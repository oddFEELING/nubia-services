from typing import List

from rich import print
from rich.pretty import pprint

from src.utils import supabase


async def get_analysis_conversation(analysis_id: str) -> List[dict]:
    """
    Get the conversation associated with an analysis
    :param analysis_id: Id of the analysis to query
    :return: A list of the messages (conversation)
    """

    print(f'Getting the conversations for analysis: {analysis_id}')
    messages = (supabase
                .table('analysis_messages')
                .select("*")
                .eq('id', analysis_id)
                .order('created_at', desc=True)
                .execute())
    pprint(messages.data)
    return messages.data
