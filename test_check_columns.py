import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

resp = supabase.table("Usuario").select("*").limit(1).execute()
if resp.data:
    print("Columns in DB:")
    for col in resp.data[0].keys():
        print(f"- {col}")
else:
    print("No rows to infer columns, or table empty.")
