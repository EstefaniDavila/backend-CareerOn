from supabase import create_client, Client
from .config import settings

def get_db():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise Exception("Supabase credentials are not configured in .env")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
