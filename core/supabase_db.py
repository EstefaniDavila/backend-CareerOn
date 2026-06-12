from supabase import create_client, Client
from .config import settings

# Se inicializa el cliente de Supabase
supabase: Client | None = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_db():
    if not supabase:
        raise Exception("Supabase credentials are not configured in .env")
    return supabase
