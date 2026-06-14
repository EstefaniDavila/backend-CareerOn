import sys
import os
import joblib
import warnings

# Ignore scikit-learn warnings about feature names
warnings.filterwarnings("ignore", category=UserWarning)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.supabase_db import get_db

db = get_db()
model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "random_forest_model.pkl")
ml_model = joblib.load(model_path)

def test_matchmaking(job_id=23): # Example job_id
    # 1. Obtener requerimientos
    reqs_resp = db.table("JobRequirement").select("skill_id").eq("job_id", job_id).execute()
    job_skills = set([r["skill_id"] for r in reqs_resp.data]) if reqs_resp.data else set()
    
    # Obtener nombres de los skills de este job
    if job_skills:
        skills_resp = db.table("Skill").select("id, name").in_("id", list(job_skills)).execute()
        job_skills_dict = {s["id"]: s["name"] for s in skills_resp.data}
    else:
        job_skills_dict = {}

    # 2. Obtener estudiantes
    students_resp = db.table("Usuario").select("id, name, career, current_cycle, streak_count, email").eq("type", "Student").execute()
    students = students_resp.data

    # Obtener skills de todos los estudiantes
    student_ids = [s["id"] for s in students]
    user_skills_resp = db.table("UserSkill").select("user_id, skill_id").in_("user_id", student_ids).execute()
    
    student_skills_map = {}
    for us in user_skills_resp.data:
        uid = us["user_id"]
        if uid not in student_skills_map:
            student_skills_map[uid] = set()
        student_skills_map[uid].add(us["skill_id"])

    # Obtener todos los nombres de skills de los estudiantes
    all_skill_ids = list(set([us["skill_id"] for us in user_skills_resp.data]))
    all_skills_dict = {}
    if all_skill_ids:
        all_skills_resp = db.table("Skill").select("id, name").in_("id", all_skill_ids).execute()
        all_skills_dict = {s["id"]: s["name"] for s in all_skills_resp.data}

    results = []
    
    for student in students:
        s_skills = student_skills_map.get(student["id"], set())
        
        # Calcular skill match
        if job_skills:
            intersection = s_skills.intersection(job_skills)
            skill_match = (len(intersection) / len(job_skills)) * 100
            missing_skills = job_skills - intersection
            missing_names = [job_skills_dict.get(m, "Desconocido") for m in missing_skills]
        else:
            skill_match = 100
            missing_names = []

        # Mock AI Fit Score
        import random
        ai_fit_score = random.randint(50, 95)
        
        # Pet Message
        if not missing_names:
            pet_message = f"¡{student['name'].split()[0]} cumple con todos los requisitos técnicos!"
        else:
            pet_message = f"¡Excelente perfil! Solo le vendría bien reforzar: {', '.join(missing_names[:2])}."

        cycle = student.get("current_cycle") or 1
        streak = student.get("streak_count") or 0
        
        # Predecir Probabilidad
        prob = ml_model.predict_proba([[skill_match, ai_fit_score, cycle, streak]])[0][1]
        
        # Extraer nombres de conocimiento para el UI
        knowledge = [all_skills_dict.get(sk, "Desconocido") for sk in s_skills]

        results.append({
            "id": student["id"],
            "name": student["name"],
            "career": student["career"] or "Estudiante UTP",
            "cycle": f"{cycle}vo",
            "email": student["email"],
            "cellphone": "999 999 999", # TODO: Agregar a la BD si es necesario
            "match": int(skill_match),
            "ai_fit_score": ai_fit_score,
            "hiring_probability": int(prob * 100),
            "status": "revision",
            "softSkills": ["Trabajo en equipo"], # Placeholder
            "knowledge": knowledge[:3], # UI muestra max ~3
            "pet_message": pet_message
        })

    # Ordenar por probabilidad
    results = sorted(results, key=lambda x: x["hiring_probability"], reverse=True)
    
    for i, r in enumerate(results):
        r["ranking"] = i + 1

    return {"status": "success", "candidates": results, "job_skills": list(job_skills_dict.values())}

if __name__ == "__main__":
    res = test_matchmaking()
    print(f"Top 1 Candidate: {res['candidates'][0]}")
