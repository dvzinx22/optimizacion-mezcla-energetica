"""
================================================================================
UNIVERSIDAD DE LA GUAJIRA - FACULTAD DE INGENIERÍA
Programa: Ingeniería de Sistemas
Asignatura: Investigación de Operaciones + Desarrollo Tecnológico + IA
Docente: Prof. Nicolás de Jesús Sánchez
Proyecto: Optimización de Mezcla Energética y Descarbonización Industrial
Script: optimizacion_energia.py
Solvers / Librerías: PuLP, Pandas, Matplotlib, Seaborn, OpenPyXL
================================================================================
Nomenclatura Estricta de Variables:
- x_{e}_{t}: MWh comprados de la fuente de energía e en el bloque tarifario t.
- y_{t}: Costo monetario acumulado ($USD) en el bloque tarifario t.
================================================================================
"""

import os
import pulp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración visual de gráficos
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'

# -------------------------------------------------------------------------
# 1. DEFINICIÓN DE CONJUNTOS Y PARÁMETROS DE ENTRADA
# -------------------------------------------------------------------------
fuentes = ['e1', 'e2', 'e3', 'e4']
nombres_fuentes = {
    'e1': 'e1: Red Tradicional',
    'e2': 'e2: Solar Fotovoltaica',
    'e3': 'e3: Parque Eólico',
    'e4': 'e4: Cogeneración Gas'
}

bloques = ['t1', 't2', 't3']
nombres_bloques = {
    't1': 't1 (Pico)',
    't2': 't2 (Medio)',
    't3': 't3 (Valle)'
}

# Demanda energética mensual (MWh)
demanda = {
    't1': 1200.0,
    't2': 1800.0,
    't3': 2000.0
}
demanda_total = sum(demanda.values())  # 5,000 MWh

# Costos unitarios por bloque ($USD / MWh)
costos = {
    ('e1', 't1'): 110.0, ('e1', 't2'): 85.0, ('e1', 't3'): 60.0,
    ('e2', 't1'): 45.0,  ('e2', 't2'): 45.0, ('e2', 't3'): 0.0,
    ('e3', 't1'): 50.0,  ('e3', 't2'): 50.0, ('e3', 't3'): 50.0,
    ('e4', 't1'): 75.0,  ('e4', 't2'): 75.0, ('e4', 't3'): 75.0
}

# Capacidades máximas disponibles por bloque (MWh)
cap_max = {
    ('e1', 't1'): None,   ('e1', 't2'): None,   ('e1', 't3'): None,
    ('e2', 't1'): 600.0,  ('e2', 't2'): 1000.0, ('e2', 't3'): 0.0,
    ('e3', 't1'): 500.0,  ('e3', 't2'): 500.0,  ('e3', 't3'): 500.0,
    ('e4', 't1'): 800.0,  ('e4', 't2'): 800.0,  ('e4', 't3'): 800.0
}

# Factor de emisión de CO2 (kg CO2 / MWh)
emisiones_unit = {
    'e1': 500.0,  # 0.50 ton/MWh
    'e2': 0.0,    # 0.00 ton/MWh
    'e3': 0.0,    # 0.00 ton/MWh
    'e4': 250.0   # 0.25 ton/MWh
}

# Parámetros regulatorios
limite_emisiones_kg = 1200000.0   # 1,200 toneladas = 1,200,000 kg CO2
cuota_min_renovable_mwh = 1500.0  # 30% de 5,000 MWh

# -------------------------------------------------------------------------
# 2. CONSTRUCCIÓN DEL MODELO DE PROGRAMACIÓN LINEAL (PuLP)
# -------------------------------------------------------------------------
prob = pulp.LpProblem("Optimizacion_Mezcla_Energetica_Industrial", pulp.LpMinimize)

# Variables de decisión estrictas:
# x_{e}_{t}: MWh comprados de la fuente e en el bloque t
x = {}
for e in fuentes:
    for t in bloques:
        ub = cap_max[(e, t)]
        var_name = f"x_{e}_{t}"
        x[(e, t)] = pulp.LpVariable(var_name, lowBound=0.0, upBound=ub, cat=pulp.LpContinuous)

# y_{t}: Costo monetario acumulado en el bloque t ($USD)
y = {}
for t in bloques:
    var_name = f"y_{t}"
    y[t] = pulp.LpVariable(var_name, lowBound=0.0, cat=pulp.LpContinuous)

# Función Objetivo: Minimizar el costo total mensual sumando los costos por bloque
prob += pulp.lpSum([y[t] for t in bloques]), "Costo_Total_Suministro"

# Restricción de Balance / Definición de Costo Acumulado y_t
for t in bloques:
    prob += y[t] == pulp.lpSum([costos[(e, t)] * x[(e, t)] for e in fuentes]), f"R_Def_Costo_y_{t}"

# Restricción 1: Satisfacción de Demanda Energética en cada Bloque Tarifario
for t in bloques:
    prob += pulp.lpSum([x[(e, t)] for e in fuentes]) == demanda[t], f"R_Demanda_Bloque_{t}"

# Restricción 2: Límite Regulatorio de Emisiones Totales de CO2 (<= 1,200,000 kg)
prob += (
    pulp.lpSum([emisiones_unit[e] * x[(e, t)] for e in fuentes for t in bloques]) <= limite_emisiones_kg,
    "R_Limite_Max_Emisiones_CO2"
)

# Restricción 3: Cuota Mínima Obligatoria de Generación Renovable (Solar + Eólica >= 1,500 MWh)
prob += (
    pulp.lpSum([x[(e, t)] for e in ['e2', 'e3'] for t in bloques]) >= cuota_min_renovable_mwh,
    "R_Cuota_Minima_Renovable"
)

# -------------------------------------------------------------------------
# 3. RESOLUCIÓN DEL MODELO
# -------------------------------------------------------------------------
solver = pulp.PULP_CBC_CMD(msg=False)
prob.solve(solver)

status_resolucion = pulp.LpStatus[prob.status]
costo_total_optimo = pulp.value(prob.objective)

# -------------------------------------------------------------------------
# 4. EXTRACCIÓN Y PROCESAMIENTO DE RESULTADOS
# -------------------------------------------------------------------------
matriz_resultados = []
for t in bloques:
    for e in fuentes:
        mwh = pulp.value(x[(e, t)])
        costo_unit = costos[(e, t)]
        costo_total_parcial = mwh * costo_unit
        kg_co2 = mwh * emisiones_unit[e]
        matriz_resultados.append({
            'Bloque': nombres_bloques[t],
            'Bloque_ID': t,
            'Fuente': nombres_fuentes[e],
            'Fuente_ID': e,
            'MWh_Comprados': mwh,
            'Costo_Unitario_USD': costo_unit,
            'Costo_Total_USD': costo_total_parcial,
            'Factor_CO2_kg_MWh': emisiones_unit[e],
            'Emisiones_kg_CO2': kg_co2,
            'Emisiones_ton_CO2': kg_co2 / 1000.0
        })

df_detalle = pd.DataFrame(matriz_resultados)
df_pivot_mwh = df_detalle.pivot(index='Fuente', columns='Bloque', values='MWh_Comprados')
df_pivot_costos = df_detalle.pivot(index='Fuente', columns='Bloque', values='Costo_Total_USD')

costos_bloques = {t: pulp.value(y[t]) for t in bloques}
emisiones_totales_kg = df_detalle['Emisiones_kg_CO2'].sum()
emisiones_totales_ton = emisiones_totales_kg / 1000.0

mwh_renovables = df_detalle[df_detalle['Fuente_ID'].isin(['e2', 'e3'])]['MWh_Comprados'].sum()
pct_renovable = (mwh_renovables / demanda_total) * 100.0

# -------------------------------------------------------------------------
# 5. ESCENARIO BASE SIN OPTIMIZAR (DATOS HISTÓRICOS)
# -------------------------------------------------------------------------
costo_base = 422500.0          # $USD mensual histórico
emisiones_base_ton = 2187.5    # Toneladas CO2 mensuales históricas
emisiones_base_kg = emisiones_base_ton * 1000.0
renovables_base_mwh = 0.0
pct_renovables_base = 0.0

# Cálculo de mejoras cuantitativas
ahorro_costo_usd = costo_base - costo_total_optimo
ahorro_costo_pct = (ahorro_costo_usd / costo_base) * 100.0

reduccion_co2_ton = emisiones_base_ton - emisiones_totales_ton
reduccion_co2_pct = (reduccion_co2_ton / emisiones_base_ton) * 100.0

# -------------------------------------------------------------------------
# 6. ANÁLISIS DE SENSIBILIDAD Y DUALIDAD
# -------------------------------------------------------------------------
dual_records = []
for name, c in prob.constraints.items():
    dual_records.append({
        'Restriccion': name,
        'Precio_Sombra_Dual': c.pi,
        'Holgura_Slack': c.slack
    })
df_duales = pd.DataFrame(dual_records)

# -------------------------------------------------------------------------
# 7. EXPORTACIÓN A ARCHIVOS EXCEL Y CSV
# -------------------------------------------------------------------------
with pd.ExcelWriter("matriz_abastecimiento.xlsx", engine="openpyxl") as writer:
    df_detalle.to_excel(writer, sheet_name="Detalle_x_et", index=False)
    df_pivot_mwh.to_excel(writer, sheet_name="Matriz_MWh")
    df_pivot_costos.to_excel(writer, sheet_name="Matriz_Costos_USD")
    df_duales.to_excel(writer, sheet_name="Sensibilidad_Duales", index=False)

df_comparacion = pd.DataFrame([
    {
        'Métrica': 'Costo Total Mensual ($USD)',
        'Sin Optimizar': f"${costo_base:,.2f}",
        'Optimizado (PuLP)': f"${costo_total_optimo:,.2f}",
        'Mejora Absoluta': f"-${ahorro_costo_usd:,.2f}",
        'Mejora Porcentual': f"-{ahorro_costo_pct:.2f}%"
    },
    {
        'Métrica': 'Emisiones CO2 (Toneladas)',
        'Sin Optimizar': f"{emisiones_base_ton:,.2f} ton",
        'Optimizado (PuLP)': f"{emisiones_totales_ton:,.2f} ton",
        'Mejora Absoluta': f"-{reduccion_co2_ton:,.2f} ton",
        'Mejora Porcentual': f"-{reduccion_co2_pct:.2f}%"
    },
    {
        'Métrica': 'Participación Renovable (%)',
        'Sin Optimizar': f"{pct_renovables_base:.1f}%",
        'Optimizado (PuLP)': f"{pct_renovable:.1f}%",
        'Mejora Absoluta': f"+{pct_renovable - pct_renovables_base:.1f}%",
        'Mejora Porcentual': "N/A (Desde 0%)"
    },
    {
        'Métrica': 'Cumplimiento Regulatorio CO2',
        'Sin Optimizar': 'NO CUMPLE (Violación +82.3%)',
        'Optimizado (PuLP)': 'CUMPLE (Holgura de 350 ton)',
        'Mejora Absoluta': '100% Mitigación de Multas',
        'Mejora Porcentual': 'Conformidad Legal Total'
    }
])
df_comparacion.to_csv("comparacion_escenarios.csv", index=False, encoding="utf-8-sig")

# -------------------------------------------------------------------------
# 8. GENERACIÓN DE GRÁFICOS VISUALES
# -------------------------------------------------------------------------
# Gráfico 1: Comparación Costos y Emisiones (Escenario Actual vs Optimizado)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Subgráfico Costos
categorias = ['Sin Optimizar\n(Histórico)', 'Optimizado\n(Modelo PuLP)']
costos_plot = [costo_base, costo_total_optimo]
colores_costos = ['#d9534f', '#2b8a3e']

bars1 = ax1.bar(categorias, costos_plot, color=colores_costos, width=0.55, edgecolor='black', linewidth=1.2)
ax1.set_title("Costo de Abastecimiento Eléctrico Mensual ($USD)", pad=15)
ax1.set_ylabel("Costo Total ($USD)")
ax1.set_ylim(0, 480000)
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 10000, f"${yval:,.0f}\n(-{ahorro_costo_pct:.1f}%)" if yval < costo_base else f"${yval:,.0f}", ha='center', va='bottom', fontweight='bold')
ax1.axhline(costo_base, color='#d9534f', linestyle='--', alpha=0.5)

# Subgráfico Emisiones
emisiones_plot = [emisiones_base_ton, emisiones_totales_ton]
colores_emisiones = ['#c92a2a', '#12b886']
bars2 = ax2.bar(categorias, emisiones_plot, color=colores_emisiones, width=0.55, edgecolor='black', linewidth=1.2)
ax2.axhline(limite_emisiones_kg / 1000.0, color='#e03131', linestyle='-', linewidth=2.0, label='Límite Legal (1,200 ton)')
ax2.set_title("Emisiones Totales de CO2 Mensuales (Toneladas)", pad=15)
ax2.set_ylabel("Emisiones (Ton CO2)")
ax2.set_ylim(0, 2600)
ax2.legend(loc='upper right')
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 50, f"{yval:,.1f} ton\n(-{reduccion_co2_pct:.1f}%)" if yval < emisiones_base_ton else f"{yval:,.1f} ton\n(ILEGAL)", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig("comparacion_costos_emisiones.png", dpi=300)
plt.close()

# Gráfico 2: Despacho Óptimo por Bloque Horario y Fuente (MWh)
fig, ax = plt.subplots(figsize=(10, 6))
bloques_labels = ['t1 (Pico: 1,200 MWh)', 't2 (Medio: 1,800 MWh)', 't3 (Valle: 2,000 MWh)']

# Datos apilados por fuente
bottoms = np.zeros(3)
palette = {'e1': '#495057', 'e2': '#f59f00', 'e3': '#22b8cf', 'e4': '#20c997'}

for e in fuentes:
    valores = [pulp.value(x[(e, t)]) for t in bloques]
    ax.bar(bloques_labels, valores, bottom=bottoms, label=nombres_fuentes[e], color=palette[e], edgecolor='white', width=0.5)
    # Anotar texto en la barra si el valor es positivo
    for idx, val in enumerate(valores):
        if val > 150:
            ax.text(idx, bottoms[idx] + val / 2.0, f"{val:.0f} MWh", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
    bottoms += np.array(valores)

ax.set_title("Plan de Despacho Energético Óptimo x_{e,t} por Bloque Tarifario", pad=15)
ax.set_ylabel("Energía Asignada (MWh)")
ax.set_ylim(0, 2400)
ax.legend(title="Fuentes de Energía", bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig("matriz_despacho_energia.png", dpi=300)
plt.close()

# Gráfico 3: Análisis de Sensibilidad al Límite de Emisiones
limites_prueba = [700, 800, 900, 1000, 1100, 1200, 1400, 1600]
costos_sensibilidad = []

for lim in limites_prueba:
    p_temp = pulp.LpProblem("Sensibilidad", pulp.LpMinimize)
    x_t = { (e, t): pulp.LpVariable(f"x_{e}_{t}", lowBound=0, upBound=cap_max[(e, t)]) for e in fuentes for t in bloques }
    y_t = { t: pulp.LpVariable(f"y_{t}", lowBound=0) for t in bloques }
    p_temp += pulp.lpSum([y_t[t] for t in bloques])
    for t in bloques:
        p_temp += y_t[t] == pulp.lpSum([costos[(e, t)] * x_t[(e, t)] for e in fuentes])
        p_temp += pulp.lpSum([x_t[(e, t)] for e in fuentes]) == demanda[t]
    p_temp += pulp.lpSum([emisiones_unit[e] * x_t[(e, t)] for e in fuentes for t in bloques]) <= lim * 1000.0
    p_temp += pulp.lpSum([x_t[(e, t)] for e in ['e2', 'e3'] for t in bloques]) >= cuota_min_renovable_mwh
    p_temp.solve(solver)
    if p_temp.status == pulp.LpStatusOptimal:
        costos_sensibilidad.append((lim, pulp.value(p_temp.objective), "Factible"))
    else:
        costos_sensibilidad.append((lim, None, "Infactible"))

df_sens = pd.DataFrame(costos_sensibilidad, columns=['Limite_CO2_Ton', 'Costo_Optimo_USD', 'Estado'])

fig, ax = plt.subplots(figsize=(9, 5))
factibles = df_sens[df_sens['Estado'] == 'Factible']
ax.plot(factibles['Limite_CO2_Ton'], factibles['Costo_Optimo_USD'], marker='o', linewidth=2.5, color='#1c7ed6', markersize=8)
ax.axvline(1200, color='#e03131', linestyle='--', label='Límite Base Actual (1,200 ton)')
ax.set_title("Curva de Compensación (Trade-off): Costo Total vs. Límite de CO2", pad=15)
ax.set_xlabel("Límite Máximo de Emisiones Permitido (Toneladas CO2)")
ax.set_ylabel("Costo Mínimo de Suministro ($USD)")
for _, row in factibles.iterrows():
    ax.annotate(f"${row['Costo_Optimo_USD']:,.0f}", (row['Limite_CO2_Ton'], row['Costo_Optimo_USD']),
                textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig("analisis_sensibilidad.png", dpi=300)
plt.close()

# -------------------------------------------------------------------------
# 9. IMPRESIÓN CONSOLA DE RESULTADOS
# -------------------------------------------------------------------------
print("================================================================================")
print("             REPORTE EJECUTIVO - OPTIMIZACIÓN ENERGÉTICA INDUSTRIAL             ")
print("================================================================================")
print(f"Estado de Solución Solver: {status_resolucion}")
print(f"Costo Óptimo Total:        ${costo_total_optimo:,.2f} USD")
print(f"Ahorro Frente al Histórico: ${ahorro_costo_usd:,.2f} USD ({ahorro_costo_pct:.2f}%)")
print(f"Emisiones CO2 Óptimas:      {emisiones_totales_ton:,.2f} Toneladas ({emisiones_totales_kg:,.0f} kg)")
print(f"Reducción de Emisiones CO2: {reduccion_co2_ton:,.2f} Toneladas ({reduccion_co2_pct:.2f}%)")
print(f"Porcentaje Renovable:       {pct_renovable:.2f}% ({mwh_renovables:,.0f} MWh)")
print("--------------------------------------------------------------------------------")
print("MATRIZ DE ASIGNACIÓN ÓPTIMA (MWh):")
print(df_pivot_mwh)
print("--------------------------------------------------------------------------------")
print("COSTO POR BLOQUE TARIFARIO (y_t):")
for t in bloques:
    print(f"  Bloque {nombres_bloques[t]}: y_{t} = ${costos_bloques[t]:,.2f} USD")
print("================================================================================")
