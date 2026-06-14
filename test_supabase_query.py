import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res = supabase.table('Application').select('id, status, student_id, job_id, Usuario(name), JobPost(title)').limit(5).execute()
print(res.data)
