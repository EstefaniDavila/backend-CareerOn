import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

resp = supabase.table("Usuario").select("*").execute()
print("All users:")
for u in resp.data:
    print(u.get("email"), "->", u.get("type"))
