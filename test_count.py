import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.supabase_db import get_db

db = get_db()
try:
    resp = db.table("JobPost").select("*", count="exact").range(200, 210).execute()
    print("DATA:", resp.data)
    print("COUNT:", resp.count)
except Exception as e:
    print("ERROR:", str(e))
