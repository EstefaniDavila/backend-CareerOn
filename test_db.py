import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- Usuarios en Supabase ---")
resp = supabase.table("Usuario").select("email, name, type, temp_code, company_name").execute()
if not resp.data:
    print("La tabla está vacía.")
else:
    for user in resp.data:
        print(f"[{user.get('type')}] Email: {user.get('email')} | Código: {user.get('temp_code')} | Empresa: {user.get('company_name')}")
