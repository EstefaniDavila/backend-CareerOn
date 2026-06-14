import os
import random
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Faltan las credenciales de Supabase en el archivo .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def seed_database():
    print("🌱 Iniciando proceso de Seed (Poblado de Base de Datos)...")

    skills_data = [
        {"name": "Python", "category": "Desarrollo"},
        {"name": "React", "category": "Desarrollo"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "SQL", "category": "Data"},
        {"name": "AWS", "category": "Cloud"},
        {"name": "Node.js", "category": "Desarrollo"},
        {"name": "Machine Learning", "category": "Data"},
        {"name": "Power BI", "category": "Data"},
        {"name": "C#", "category": "Desarrollo"},
        {"name": "Figma", "category": "Diseño UI/UX"},
        
        # Negocios & Marketing
        {"name": "SEO", "category": "Marketing"},
        {"name": "Google Ads", "category": "Marketing"},
        {"name": "Ventas B2B", "category": "Negocios"},
        {"name": "Finanzas Corporativas", "category": "Negocios"},
        {"name": "Análisis Financiero", "category": "Finanzas"},
        
        # Ingeniería y Otras Ciencias
        {"name": "AutoCAD", "category": "Ingeniería Civil/Arquitectura"},
        {"name": "Gestión de Proyectos", "category": "Ingeniería Industrial"},
        {"name": "Logística", "category": "Ingeniería Industrial"},
        {"name": "SolidWorks", "category": "Ingeniería Mecánica"},
        
        # Habilidades Blandas (Soft Skills) - Clave para el Matchmaking
        {"name": "Liderazgo", "category": "Soft Skill"},
        {"name": "Scrum", "category": "Metodología"},
        {"name": "Comunicación Asertiva", "category": "Soft Skill"},
        {"name": "Resolución de Problemas", "category": "Soft Skill"},
        {"name": "Trabajo en Equipo", "category": "Soft Skill"},
        {"name": "Gestión del Tiempo", "category": "Soft Skill"},
        {"name": "Pensamiento Crítico", "category": "Soft Skill"}
    ]
    
    print("👉 Insertando Skills...")
    skills_inserted = []
    for skill in skills_data:
        # Verifica si ya existe para no duplicar
        res = supabase.table("Skill").select("id, name").eq("name", skill["name"]).execute()
        if not res.data:
            inserted = supabase.table("Skill").insert(skill).execute()
            skills_inserted.append(inserted.data[0])
        else:
            skills_inserted.append(res.data[0])

    skill_ids = [s["id"] for s in skills_inserted]

    first_names = ["Ana", "Carlos", "Maria", "Juan", "Laura", "Pedro", "Sofia", "Diego", "Luis", "Elena", "Andres", "Valeria", "Jorge", "Camila", "Miguel", "Lucia", "Fernando", "Diana", "Gabriel", "Isabella"]
    last_names = ["Perez", "Gomez", "Lopez", "Diaz", "Martinez", "Rodriguez", "Fernandez", "Garcia", "Sanchez", "Romero", "Suarez", "Torres", "Ruiz", "Flores", "Acosta", "Medina", "Rojas", "Cruz"]
    companies = ["Google", "Globant", "Microsoft", "Amazon", "BCP", "Interbank", "Mercado Libre", "Kavak", "Rappi", "IBM"]
    careers = ["Ing. Sistemas", "Ciencias de la Computacion", "Ing. Industrial", "Marketing", "Administracion", "Diseno Grafico", "Economia", "Ing. Mecanica"]
    
    print("👉 Insertando Reclutadores...")
    recruiters_inserted = []
    for i in range(10):
        company = companies[i % len(companies)]
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        rec = {
            "name": f"{fname} {lname}", 
            "email": f"hr{i}@{company.lower().replace(' ', '')}.com", 
            "type": "Recruiter", 
            "company_name": company, 
            "streak_count": random.randint(1, 10)
        }
        res = supabase.table("Usuario").select("id").eq("email", rec["email"]).execute()
        if not res.data:
            inserted = supabase.table("Usuario").insert(rec).execute()
            rec_id = inserted.data[0]["id"]
            recruiters_inserted.append(rec_id)
            supabase.table("CompanyTokenPool").insert({"recruiter_id": rec_id, "total_tokens_available": 10000}).execute()
        else:
            recruiters_inserted.append(res.data[0]["id"])

    print("👉 Insertando Ofertas de Trabajo...")
    if recruiters_inserted:
        job_titles = [
            "Junior Backend Developer", "React Frontend Engineer", "Data Scientist Trainee", "Analista de Marketing",
            "Ingeniero Civil Junior", "Diseñador UX/UI", "Gestor de Proyectos", "Especialista SEO", 
            "Analista Financiero", "Cloud Engineer Junior", "Desarrollador C#", "Analista de Datos Bilingüe"
        ]
        
        jobs_inserted = []
        locations = ["Lima, Perú (Híbrido)", "Remoto", "Bogotá, Colombia", "Ciudad de México", "Remoto (Latam)", "Santiago, Chile"]
        job_types = ["Tiempo completo", "Media jornada", "Por contrato", "Prácticas"]
        salaries = ["S/ 1,500 - S/ 2,500", "S/ 3,000 - S/ 5,000", "S/ 1,025 - S/ 1,200", "No especificado", "S/ 6,000 - S/ 8,000"]
        
        for i in range(25):
            rec_id = random.choice(recruiters_inserted)
            title = random.choice(job_titles)
            job = {
                "recruiter_id": rec_id, 
                "title": f"{title} #{i+1}", 
                "description": f"Buscamos talento para {title} con muchas ganas de crecer en nuestra empresa. Requerimos experiencia comprobable y capacidad para trabajar en equipo.",
                "location": random.choice(locations),
                "job_type": random.choice(job_types),
                "salary_range": random.choice(salaries)
            }
            res = supabase.table("JobPost").select("id").eq("title", job["title"]).execute()
            if not res.data:
                inserted = supabase.table("JobPost").insert(job).execute()
                job_id = inserted.data[0]["id"]
                jobs_inserted.append(job_id)
                # Requerimientos: 3 a 5 skills random
                if len(skill_ids) >= 5:
                    reqs = random.sample(skill_ids, random.randint(3, 5))
                    for r_id in reqs:
                        supabase.table("JobRequirement").insert({"job_id": job_id, "skill_id": r_id, "required_level": random.choice(["Básico", "Intermedio", "Avanzado"])}).execute()
                
               
    # 5. Crear Estudiantes Masivos (50 Estudiantes)
    print("👉 Insertando Estudiantes y sus Skills (50 Alumnos)...")
    for i in range(50):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        stu = {
            "name": f"{fname} {lname}", 
            "email": f"estudiante{i}@utp.edu.pe", 
            "type": "Student", 
            "career": random.choice(careers), 
            "current_cycle": random.randint(1, 10), 
            "streak_count": random.randint(0, 30),
            "coins_balance": random.randint(10, 500)
        }
        res = supabase.table("Usuario").select("id").eq("email", stu["email"]).execute()
        if not res.data:
            inserted = supabase.table("Usuario").insert(stu).execute()
            stu_id = inserted.data[0]["id"]
            # Asignarles de 2 a 6 skills random
            if skill_ids:
                my_skills = random.sample(skill_ids, random.randint(2, 6))
                for s_id in my_skills:
                    supabase.table("UserSkill").insert({"user_id": stu_id, "skill_id": s_id, "level": random.choice(["Básico", "Intermedio", "Avanzado"])}).execute()

    # 6. Crear Retos (Challenges)
    print("👉 Insertando Retos Masivos (Misiones)...")
    if skill_ids:
        challenge_verbs = ["Optimiza", "Crea", "Diseña", "Analiza", "Resuelve", "Configura"]
        for s in skills_inserted:
            title = f"{random.choice(challenge_verbs)} un proyecto básico con {s['name']}"
            res = supabase.table("Challenge").select("id").eq("title", title).execute()
            if not res.data:
                try:
                    supabase.table("Challenge").insert({
                        "skill_id": s["id"], 
                        "title": title, 
                        "reward_coins": random.randint(20, 100), 
                        "reward_xp": random.randint(50, 200)
                    }).execute()
                except Exception as e:
                    pass
                
    # 7. Crear Postulaciones (Applications) para rellenar los contadores
    print("👉 Creando postulaciones aleatorias...")
    # Obtener todos los trabajos y estudiantes de la BD para asegurarnos de que existan
    all_jobs_res = supabase.table("JobPost").select("id").execute()
    all_students_res = supabase.table("Usuario").select("id").eq("type", "Student").execute()
    
    all_jobs = [j["id"] for j in all_jobs_res.data]
    all_students = [s["id"] for s in all_students_res.data]
    
    if all_jobs and all_students:
        for job_id in all_jobs:
            # Seleccionar entre 2 y 15 estudiantes al azar para que postulen a este job
            num_applicants = random.randint(2, 15)
            applicants = random.sample(all_students, min(num_applicants, len(all_students)))
            
            for student_id in applicants:
                try:
                    supabase.table("Application").insert({
                        "job_id": job_id,
                        "student_id": student_id,
                        "status": "Pendiente"
                    }).execute()
                except Exception:
                    pass

    print("✅ Seed completado con éxito. ¡BD Lista!")

if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
