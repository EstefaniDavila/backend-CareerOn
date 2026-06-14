from dotenv import load_dotenv
import os, requests
load_dotenv()
url = os.getenv('SUPABASE_URL') + '/rest/v1/rpc/run_sql'
key = os.getenv('SUPABASE_KEY')
print(requests.post(url, headers={'apikey': key, 'Authorization': f'Bearer {key}'}, json={'query': 'ALTER TABLE "Application" ADD COLUMN challenge_url TEXT;'}).text)
