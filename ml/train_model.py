import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

np.random.seed(42)
n_samples = 1500

skill_match = np.random.normal(loc=60, scale=20, size=n_samples)
skill_match = np.clip(skill_match, 0, 100)

ai_fit_score = np.random.normal(loc=55, scale=25, size=n_samples)
ai_fit_score = np.clip(ai_fit_score, 0, 100)

cycle = np.random.randint(1, 11, size=n_samples)
streak = np.random.exponential(scale=10, size=n_samples)
streak = np.clip(streak, 0, 50).astype(int)

# DEFINIR REGLA DE CONTRATACIÓN (Aproximación para que el modelo aprenda la tendencia)
# Pesos: 40% skill, 40% ai_fit, 10% ciclo, 10% racha
score = (0.4 * skill_match) + (0.4 * ai_fit_score) + (cycle * 2) + (streak * 0.5)

# Agregar un poco de ruido aleatorio para que no sea un cálculo determinista
score += np.random.normal(loc=0, scale=5, size=n_samples)

# Threshold para "Contratado" (Aproximadamente el top 30% será contratado)
threshold = np.percentile(score, 70)
hired = (score >= threshold).astype(int)

df = pd.DataFrame({
    'skill_match': skill_match,
    'ai_fit_score': ai_fit_score,
    'cycle': cycle,
    'streak': streak,
    'hired': hired
})

print(f"Dataset generado: {len(df)} registros.")
print(f"Estudiantes contratados: {df['hired'].sum()} ({df['hired'].mean()*100:.1f}%)")

# 3. ENTRENAR RANDOM FOREST
X = df[['skill_match', 'ai_fit_score', 'cycle', 'streak']]
y = df['hired']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# 4. EVALUAR
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Precisión del modelo en datos de prueba: {accuracy*100:.2f}%")

# 5. GUARDAR EL MODELO
output_path = os.path.join(os.path.dirname(__file__), "random_forest_model.pkl")
joblib.dump(model, output_path)
print(f"✅ Modelo guardado exitosamente en: {output_path}")

# Prueba de inferencia
sample = [[85.0, 92.0, 8, 15]] # Un alumno casi perfecto
prob = model.predict_proba(sample)[0][1]
print(f"Probabilidad de contratación para candidato excelente: {prob*100:.1f}%")

sample2 = [[30.0, 40.0, 2, 0]] # Alumno con bajo match
prob2 = model.predict_proba(sample2)[0][1]
print(f"Probabilidad de contratación para candidato con bajo match: {prob2*100:.1f}%")
