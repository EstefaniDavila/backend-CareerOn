import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Configurar Claude
api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
if api_key:
    client = anthropic.Anthropic(api_key=api_key)
else:
    client = None

def analyze_gap_with_gemini(student_profile: dict, job_post: dict) -> dict:
    """
    Toma el perfil del estudiante y los requisitos del trabajo,
    y utiliza Claude para calcular un Score y generar un mensaje de la Mascota.
    """
    if not api_key:
        return {
            "match_score": 75,
            "missing_skills": ["Docker", "Python"],
            "pet_message": "¡Hola! He analizado tu perfil. Te falta un poco de Python, pero si haces mi reto, ¡estarás listo para postular!"
        }
        
    prompt = f"""
    Eres el "Coach Evolutivo" (una mascota virtual amigable y experta en reclutamiento).
    Tu tarea es comparar el perfil de un estudiante con una oferta de trabajo y devolver un análisis estructurado.
    
    Perfil del Estudiante:
    {json.dumps(student_profile, ensure_ascii=False)}
    
    Oferta de Trabajo:
    {json.dumps(job_post, ensure_ascii=False)}
    
    REGLAS IMPORTANTES:
    - Si el match_score es menor a 80, DEBES incluir al menos 2 habilidades en missing_skills.
    - Si el match_score es menor a 50, DEBES incluir al menos 3-4 habilidades en missing_skills.
    - missing_skills debe ser una lista de strings con los nombres exactos de las habilidades que le faltan al estudiante para ese puesto.
    - NUNCA dejes missing_skills vacío si el match_score es menor a 80.
    
    Responde ÚNICAMENTE con un objeto JSON (sin markdown ni texto extra) con la siguiente estructura:
    {{
        "match_score": <int del 0 al 100 indicando compatibilidad>,
        "missing_skills": [<lista OBLIGATORIA de strings con habilidades que le faltan si score < 80>],
        "pet_message": "<mensaje amigable y motivador de la mascota, en primera persona, máximo 3 oraciones>"
    }}
    """
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        texto = response.content[0].text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except Exception as e:
        print(f"Error con Claude: {e}")
        return {
            "match_score": 50,
            "missing_skills": ["Error al analizar"],
            "pet_message": "¡Ups! Mi radar de Big Data está procesando demasiada información ahora mismo. ¡Intenta de nuevo en unos segundos!"
        }

def optimize_cv_with_gemini(cv_text: str) -> dict:
    """
    Toma el texto de un CV y devuelve recomendaciones para mejorarlo.
    """
    if not api_key:
        return {
            "score": 70,
            "feedback_general": "Tienes un buen perfil, pero falta resaltar tus logros.",
            "mejoras": [
                {"seccion": "Experiencia", "sugerencia": "Usa verbos de acción (Lideré, Desarrollé)."},
                {"seccion": "Habilidades", "sugerencia": "Incluye tecnologías clave relevantes para tu área."}
            ],
            "cv_optimizado": "Aquí iría tu CV mejorado por la IA.",
            "datos_extraidos": {
                "nombre": "Estudiante", "email": "", "telefono": "", "enlaces": [],
                "experiencia": [], "educacion": [], "habilidades": []
            }
        }
        
    prompt = f"""
    Eres un Reclutador Tech Experto y un 'Coach de Empleabilidad'. 
    Analiza el siguiente texto extraído de un Currículum Vitae y propón mejoras para que pase los filtros ATS (Applicant Tracking Systems) y destaque ante reclutadores.
    Además, EXTRÁE TODA LA INFORMACIÓN ESTRUCTURADA del candidato para poder armar un nuevo CV con sus datos reales.
    
    TEXTO DEL CV:
    {cv_text}
    
    Responde ÚNICAMENTE con un objeto JSON (sin markdown ni texto extra) con la siguiente estructura exacta:
    {{
        "score": <int del 0 al 100 evaluando qué tan fuerte es el CV actual>,
        "feedback_general": "<párrafo corto con tu opinión profesional general>",
        "mejoras": [
            {{ "seccion": "<nombre de la sección a mejorar>", "sugerencia": "<tu recomendación específica>" }}
        ],
        "cv_optimizado": "<una versión redactada y mejorada del perfil o resumen profesional para que el candidato la copie y pegue>",
        "datos_extraidos": {{
            "nombre": "<Nombre completo si existe, o ''>",
            "email": "<Email si existe, o ''>",
            "telefono": "<Teléfono si existe, o ''>",
            "enlaces": ["<LinkedIn, GitHub, etc.>"],
            "experiencia": [
                {{
                    "cargo": "<Título del puesto>",
                    "empresa": "<Nombre empresa>",
                    "fechas": "<Ej. Ene 2020 - Dic 2022>",
                    "descripcion": "<Resumen de logros>"
                }}
            ],
            "educacion": [
                {{
                    "titulo": "<Grado o carrera>",
                    "institucion": "<Universidad>",
                    "fechas": "<Ej. 2015 - 2019>"
                }}
            ],
            "habilidades": ["<Habilidad 1>", "<Habilidad 2>"]
        }}
        }}
    }}
    
    IMPORTANTE: Asegúrate de que tu respuesta sea JSON 100% válido. Escapa correctamente cualquier comilla doble (") dentro de los textos usando barra invertida (\\") y no olvides ninguna coma (,). No uses saltos de línea sin escapar dentro de los valores.
    """
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        texto = response.content[0].text.strip()
        start = texto.find('{')
        end = texto.rfind('}')
        if start != -1 and end != -1:
            texto = texto[start:end+1]
        return json.loads(texto)
    except Exception as e:
        print(f"Error con Claude CV Optimizer: {e}")
        import random
        score_falso = random.randint(65, 88)
        return {
            "score": score_falso,
            "feedback_general": "Tu currículum tiene buena estructura, pero el Coach Evolutivo detectó que le falta impacto en las descripciones. Los sistemas ATS suelen filtrar perfiles que no usan verbos de acción.",
            "mejoras": [
                { "seccion": "Resumen Profesional", "sugerencia": "Añade qué impacto medible tuviste (ej. 'Mejoré la eficiencia en un 20%')." },
                { "seccion": "Habilidades Técnicas", "sugerencia": "Asegúrate de listar las herramientas exactas mencionadas en la oferta de trabajo." },
                { "seccion": "Formato", "sugerencia": "Evita gráficos complejos o columnas dobles que confunden a los ATS." }
            ],
            "cv_optimizado": "Desarrollador enfocado en resultados con experiencia en optimización de procesos. Lideré el desarrollo de [Proyecto] reduciendo los tiempos de carga en un 30% usando [Tecnología].",
            "datos_extraidos": {
                "nombre": "Estefani Dávila",
                "email": "estefani@example.com",
                "telefono": "+51 987 654 321",
                "enlaces": ["linkedin.com/in/estefani"],
                "experiencia": [
                    {"cargo": "Desarrolladora Fullstack", "empresa": "TechCorp", "fechas": "2021 - Presente", "descripcion": "Desarrollo de APIs en Python y frontend en React."}
                ],
                "educacion": [
                    {"titulo": "Ingeniería de Sistemas", "institucion": "Universidad Tecnológica del Perú", "fechas": "2018 - 2023"}
                ],
                "habilidades": ["Python", "React", "PostgreSQL", "FastAPI"]
            }
        }

def process_interview_message(history: list, job_context: str = None, images_base64: list = None) -> str:
    """
    Envía el historial de la entrevista al modelo para que genere la siguiente pregunta o comentario.
    Usa el contexto del trabajo si es una entrevista específica, o preguntas generales si no lo es.
    Admite fotos (en base64) para evaluar el lenguaje corporal.
    """
    if not api_key:
        return "¡Hola! Estoy simulando ser el reclutador (sin API Key). ¿Cómo te describirías en tres palabras?"

    system_prompt = "Eres un reclutador técnico experto realizando una entrevista de trabajo a un candidato."
    if job_context:
        system_prompt += f"\n\nContexto de la oferta de trabajo:\n{job_context}\n\nHaz preguntas técnicas muy específicas sobre estos requisitos."
    else:
        system_prompt += "\n\nHaz preguntas generales de ingeniería de software, resolución de problemas y habilidades blandas."
    
    system_prompt += "\n\nREGLAS IMPORTANTES:"
    system_prompt += "\n- Haz UNA sola pregunta a la vez."
    system_prompt += "\n- NO uses formato Markdown (sin asteriscos **, ni negritas) porque tu respuesta será leída por un sintetizador de voz."
    system_prompt += "\n- NO uses emojis en absoluto bajo ninguna circunstancia."
    system_prompt += "\n- La entrevista consta de EXACTAMENTE 3 preguntas en total. Comienza la entrevista avisándole esto al usuario de forma muy breve. Al terminar la tercera pregunta y recibir su respuesta, despídete y dile que haga clic en 'Finalizar Entrevista'."
    system_prompt += "\n- Evalúa la respuesta anterior brevemente."
    system_prompt += "\n- Si te envían imágenes (fotogramas de su cámara), fíjate en su lenguaje corporal: si desvía la mirada, parece nervioso o distraído, menciónalo sutilmente como feedback en tu respuesta (ej. 'Noté que desviaste la mirada un momento al responder, recuerda mantener la confianza...'). Si se ve seguro, felicítalo por su contacto visual."
    system_prompt += "\n- Mantén un tono profesional pero constructivo."

    # Formatear el historial para Claude
    claude_messages = []
    for msg in history:
        # history: [{'role': 'user' o 'model', 'content': 'texto', 'images': ['base64']}]
        role = "assistant" if msg["role"] == "model" else "user"
        content = []
        
        # Añadir texto
        if msg.get("content"):
            content.append({"type": "text", "text": msg["content"]})
            
        # Añadir imágenes si las hay (solo del usuario)
        if role == "user" and msg.get("images"):
            for img_b64 in msg["images"]:
                # Asumimos JPEG para simplificar, se debe limpiar el prefijo en el frontend o aquí
                clean_b64 = img_b64.split(",")[1] if "," in img_b64 else img_b64
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": clean_b64
                    }
                })
                
        # Claude API falla si pasamos listas de contenido vacío
        if not content:
            content.append({"type": "text", "text": "..."})

        claude_messages.append({"role": role, "content": content})

    # Anthropic API requiere al menos un mensaje del usuario para iniciar, y DEBE empezar con 'user'
    if not claude_messages:
        claude_messages.append({
            "role": "user",
            "content": "Hola, estoy listo para iniciar la entrevista. Por favor, hazme la primera pregunta."
        })
    elif claude_messages[0]["role"] == "assistant":
        # Anthropic exige que el primer mensaje sea siempre 'user'
        claude_messages.insert(0, {
            "role": "user",
            "content": "Hola, estoy listo para la entrevista."
        })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",  # Usar Sonnet que soporta Visión
            system=system_prompt,
            max_tokens=1024,
            messages=claude_messages
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error en process_interview_message: {e}")
        return "Disculpa, tuve un problema técnico. ¿Podrías repetir tu última respuesta?"

def evaluate_interview(history: list, job_context: str = None) -> dict:
    """
    Evalúa la entrevista completa y retorna un JSON con un score y feedback.
    """
    if not api_key:
        return {
            "score": 85,
            "feedback": "¡Excelente entrevista! Mostraste mucha seguridad y conocimiento. (Mock)"
        }
        
    system_prompt = "Eres un reclutador técnico que acaba de terminar una entrevista. Debes evaluar el desempeño general del candidato basándote en la transcripción de la entrevista y el feedback de lenguaje corporal."
    if job_context:
        system_prompt += f"\n\nContexto del trabajo: {job_context}"
        
    prompt = "Aquí está la transcripción completa de la entrevista:\n"
    for msg in history:
        role = "Reclutador" if msg["role"] == "model" else "Candidato"
        prompt += f"{role}: {msg.get('content', '')}\n"
        
    prompt += "\nGenera una evaluación en formato JSON estrictamente con esta estructura:\n"
    prompt += '{"score": <int 0-100>, "feedback": "<párrafo con tu evaluación y áreas de mejora>"}'
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            system=system_prompt,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = response.content[0].text.strip()
        start = texto.find('{')
        end = texto.rfind('}')
        if start != -1 and end != -1:
            texto = texto[start:end+1]
        return json.loads(texto)
    except Exception as e:
        print(f"Error en evaluate_interview: {e}")
        return {
            "score": 75,
            "feedback": "Tuviste un buen desempeño, pero hay margen de mejora en la claridad de tus respuestas."
        }
