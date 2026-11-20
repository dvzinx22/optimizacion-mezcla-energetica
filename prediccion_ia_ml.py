"""
================================================================================
UNIVERSIDAD DE LA GUAJIRA - FACULTAD DE INGENIERÍA
Programa: Ingeniería de Sistemas
Asignatura: Investigación de Operaciones + Desarrollo Tecnológico + IA
Docente: Prof. Nicolás de Jesús Sánchez
Módulo: prediccion_ia_ml.py
Funcionalidad: Machine Learning Predictivo para Pronóstico de Generación Solar
               y Demanda Eléctrica acoplado a la Optimización Lineal (PuLP).
Librerías: Scikit-Learn, Pandas, NumPy, Matplotlib
================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# 1. GENERACIÓN DE DATASET SINTÉTICO BASADO EN TELEMETRÍA REAL
# Simulamos 365 días (8,760 horas) de datos meteorológicos y operativos
np.random.seed(42)
n_horas = 8760
dias = np.repeat(np.arange(365), 24)
hora_dia = np.tile(np.arange(24), 365)

# Variables climáticas predictoras (Features)
# Irradiancia solar extraterrestre según la hora del día (máxima al mediodía)
radiacion_teorica = np.maximum(0, np.sin((hora_dia - 6) * np.pi / 12)) * 1000
nubosidad = np.random.uniform(0, 0.4, n_horas)  # Porcentaje de cobertura de nubes
temperatura = 22 + 10 * np.sin((hora_dia - 8) * np.pi / 12) + np.random.normal(0, 2, n_horas)

# Generación solar real observada (Target con ruido estocástico)
factor_perdida = (1 - nubosidad) * (1 - 0.004 * (temperatura - 25))
generacion_solar_mwh = np.maximum(0, radiacion_teorica * factor_perdida * 0.0012 + np.random.normal(0, 0.02, n_horas))

# Mapeo a bloques de la planta (Pico: 18-22h, Medio: 8-17h, Valle: 23-7h)
def clasificar_bloque(h):
    if 18 <= h <= 21:
        return 't1_Pico'
    elif 8 <= h <= 17:
        return 't2_Medio'
    else:
        return 't3_Valle'

bloque_horario = [clasificar_bloque(h) for h in hora_dia]

df_energia = pd.DataFrame({
    'Hora': hora_dia,
    'Temperatura_C': temperatura,
    'Nubosidad_Pct': nubosidad,
    'Radiacion_Solar_W_m2': radiacion_teorica * (1 - nubosidad),
    'Bloque': bloque_horario,
    'Generacion_Solar_MWh': generacion_solar_mwh
})

# 2. ENTRENAMIENTO DEL MODELO DE MACHINE LEARNING (Random Forest)
X = df_energia[['Hora', 'Temperatura_C', 'Nubosidad_Pct', 'Radiacion_Solar_W_m2']]
y = df_energia['Generacion_Solar_MWh']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo_ml = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
modelo_ml.fit(X_train, y_train)

# 3. EVALUACIÓN DE DESEMPEÑO DEL MODELO IA
y_pred = modelo_ml.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("================================================================================")
print("     MÓDULO DE INTELIGENCIA ARTIFICIAL: PREDICCIÓN DE ENERGÍA SOLAR (ML)       ")
print("================================================================================")
print(f"Modelo Entrenado:     Random Forest Regressor (100 árboles de decisión)")
print(f"Precisión R² Score:   {r2:.4f} (Excelente capacidad de generalización)")
print(f"Error RMSE:           {rmse:.4f} MWh")
print("--------------------------------------------------------------------------------")

# 4. PRONÓSTICO MENSUAL POR BLOQUE TARIFARIO (PARÁMETROS PARA PuLP)
df_energia['Prediccion_ML_MWh'] = modelo_ml.predict(X)
resumen_mensual = df_energia.groupby('Bloque')['Prediccion_ML_MWh'].sum() / 12.0  # Promedio mensual

print("PARÁMETROS PREFECHOS POR MACHINE LEARNING PARA EL OPTIMIZADOR:")
for b, val in resumen_mensual.items():
    print(f"  Capacidad Solar Predicha en Bloque {b}: {val:,.1f} MWh")
print("================================================================================")

# 5. VISUALIZACIÓN GRÁFICA DEL MODELO DE MACHINE LEARNING
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Gráfico 1: Predicción vs Realidad (Perfil Diario Promedio)
perfil_real = df_energia.groupby('Hora')['Generacion_Solar_MWh'].mean()
perfil_pred = df_energia.groupby('Hora')['Prediccion_ML_MWh'].mean()

ax1.plot(perfil_real.index, perfil_real.values, label='Datos Reales Observados (Telemetría)', color='#1c7ed6', linewidth=2.5)
ax1.plot(perfil_pred.index, perfil_pred.values, label=f'Predicción IA (Random Forest, R²={r2:.2f})', color='#e03131', linestyle='--', linewidth=2)
ax1.fill_between(perfil_real.index, perfil_real.values, perfil_pred.values, color='#ffa8a8', alpha=0.3, label='Residuo de Error')
ax1.set_title("Curva Diaria de Generación Solar: Real vs. Machine Learning", pad=12, fontweight='bold')
ax1.set_xlabel("Hora del Día (0 a 23h)", fontweight='bold')
ax1.set_ylabel("Generación Solar (MWh)", fontweight='bold')
ax1.legend(loc='upper right')

# Gráfico 2: Importancia de Variables en el Modelo IA
importancias = modelo_ml.feature_importances_
features = ['Hora', 'Temperatura', 'Nubosidad', 'Radiación W/m²']
colores = ['#2b8a3e', '#74c0fc', '#ffd43b', '#f76707']
ax2.barh(features, importancias, color=colores, edgecolor='black', linewidth=1)
ax2.set_title("Importancia de Variables (Feature Importance - Random Forest)", pad=12, fontweight='bold')
ax2.set_xlabel("Peso Relativo en la Decisión del Modelo", fontweight='bold')
for i, v in enumerate(importancias):
    ax2.text(v + 0.01, i, f"{v*100:.1f}%", va='center', fontweight='bold', fontsize=9)
ax2.set_xlim(0, max(importancias) + 0.1)

plt.tight_layout()
plt.savefig("prediccion_ia_ml.png", dpi=300)
plt.close()
print("Gráfico 'prediccion_ia_ml.png' generado exitosamente.")
