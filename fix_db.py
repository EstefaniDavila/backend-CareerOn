import os
import random
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

locations = ["Lima, Perú (Híbrido)", "Remoto", "Bogotá, Colombia", "Ciudad de México", "Remoto (Latam)", "Santiago, Chile"]
job_types = ["Tiempo completo", "Media jornada", "Por contrato", "Prácticas"]
salaries = ["S/ 1,500 - S/ 2,500", "S/ 3,000 - S/ 5,000", "S/ 1,025 - S/ 1,200", "No especificado", "S/ 6,000 - S/ 8,000"]

jobs = supabase.table('JobPost').select('id').execute()
for job in jobs.data:
    supabase.table('JobPost').update({
        'location': random.choice(locations),
        'job_type': random.choice(job_types),
        'salary_range': random.choice(salaries)
    }).eq('id', job['id']).execute()

print('Fix aplicado correctamente')
