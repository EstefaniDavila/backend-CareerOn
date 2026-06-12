import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Inicializar el modelo
model = genai.GenerativeModel('gemini-1.5-flash-latest')

print("🤖 Conectando con Gemini...")
respuesta = model.generate_content("Escribe una frase motivadora de 10 palabras exacta para un equipo universitario que está programando en una Hackathon.")
print("\nRespuesta de Gemini:")
print("--------------------")
print(respuesta.text)
print("--------------------")
