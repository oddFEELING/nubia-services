from src.utils.supabase import supabase


async def update_user_info(user_id: str, user_info: dict):
    supabase.table('users').update(user_info).eq('id', user_id).execute()
