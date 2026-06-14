import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# +3 days from now
future_date = (datetime.now() + timedelta(days=3)).isoformat()

jobs = supabase.table('JobPost').select('id').execute()
for job in jobs.data:
    supabase.table('JobPost').update({
        'status': 'publicada',
        'deadline': future_date
    }).eq('id', job['id']).execute()

print('Fix aplicado correctamente a JobPost: status=publicada y deadline +3 dias')
