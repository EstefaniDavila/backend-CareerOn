import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configurar Gemini
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)

def analyze_gap_with_gemini(student_profile: dict, job_post: dict) -> dict:
    """
    Toma el perfil del estudiante y los requisitos del trabajo,
    y utiliza Gemini para calcular un Score y generar un mensaje de la Mascota.
    """
    if not api_key:
        # Modo Fallback si no hay API Key configurada
        return {
            "match_score": 75,
            "missing_skills": ["Docker", "Python"],
            "pet_message": "¡Hola! He analizado tu perfil. Te falta un poco de Python, pero si haces mi reto, ¡estarás listo para postular!"
        }
        
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""
    Eres el "Coach Evolutivo" (una mascota virtual amigable y experta en reclutamiento).
    Tu tarea es comparar el perfil de un estudiante con una oferta de trabajo y devolver un análisis estructurado.
    
    Perfil del Estudiante:
    {json.dumps(student_profile, ensure_ascii=False)}
    
    Oferta de Trabajo:
    {json.dumps(job_post, ensure_ascii=False)}
    
    Responde ÚNICAMENTE con un objeto JSON (sin markdown ni texto extra) con la siguiente estructura:
    {{
        "match_score": <int del 0 al 100 indicando compatibilidad>,
        "missing_skills": [<lista de strings con habilidades técnicas que le faltan>],
        "pet_message": "<mensaje amigable y motivador de la mascota, en primera persona, recomendándole aprender lo que le falta y animándolo>"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiar posible markdown (ej. ```json ... ```)
        texto = response.text.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(texto)
        return resultado
    except Exception as e:
        print(f"Error con Gemini: {e}")
        return {
            "match_score": 50,
            "missing_skills": ["Error al analizar"],
            "pet_message": "¡Ups! Mi radar de Big Data está procesando demasiada información ahora mismo. ¡Intenta de nuevo en unos segundos!"
        }

def optimize_cv_with_gemini(cv_text: str) -> dict:
    """
    Toma el texto de un CV y devuelve recomendaciones para mejorarlo,
    enfocándose en palabras clave, impacto y formato ATS.
    """
    if not api_key:
        return {
            "score": 70,
            "feedback_general": "Tienes un buen perfil, pero falta resaltar tus logros.",
            "mejoras": [
                {"seccion": "Experiencia", "sugerencia": "Usa verbos de acción (Lideré, Desarrollé)."},
                {"seccion": "Habilidades", "sugerencia": "Incluye tecnologías clave relevantes para tu área."}
            ],
            "cv_optimizado": "Aquí iría tu CV mejorado por la IA."
        }
        
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""
    Eres un Reclutador Tech Experto y un 'Coach de Empleabilidad'. 
    Analiza el siguiente texto extraído de un Currículum Vitae y propón mejoras para que pase los filtros ATS (Applicant Tracking Systems) y destaque ante reclutadores.
    
    TEXTO DEL CV:
    {cv_text}
    
    Responde ÚNICAMENTE con un objeto JSON (sin markdown ni texto extra) con la siguiente estructura:
    {{
        "score": <int del 0 al 100 evaluando qué tan fuerte es el CV actual>,
        "feedback_general": "<párrafo corto con tu opinión profesional general>",
        "mejoras": [
            {{ "seccion": "<nombre de la sección a mejorar>", "sugerencia": "<tu recomendación específica>" }}
        ],
        "cv_optimizado": "<una versión redactada y mejorada del perfil o resumen profesional para que el candidato la copie y pegue>"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        texto = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except Exception as e:
        print(f"Error con Gemini CV Optimizer: {e}")
        return {
            "score": 0,
            "feedback_general": "Ocurrió un error al procesar tu CV con Inteligencia Artificial.",
            "mejoras": [],
            "cv_optimizado": ""
        }
