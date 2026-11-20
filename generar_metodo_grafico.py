"""
Generador de la Gráfica del Método Gráfico 2D para la Defensa del Proyecto
Subproblema Representativo: Despacho Térmico/Fósil entre Red Tradicional (x1) y Gas (x2)
en el Bloque Valle (t3) para cubrir 1,500 MWh netos.
"""

import numpy as np
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax = plt.subplots(figsize=(9, 7))

# Definimos rango de variables
# x1: Red Tradicional en Valle (MWh)
# x2: Cogeneración Gas en Valle (MWh)
x1 = np.linspace(0, 2000, 400)

# Restricción 1: Demanda exacta o mínima x1 + x2 >= 1500  -->  x2 = 1500 - x1
x2_demanda = 1500 - x1

# Restricción 2: Capacidad máxima de Gas: x2 <= 800
x2_cap_gas = np.full_like(x1, 800)

# Región factible sobre la recta de demanda x1 + x2 = 1500 con x2 <= 800, x1, x2 >= 0
# x2 <= 800  -->  1500 - x1 <= 800  -->  x1 >= 700.
# Por tanto el segmento factible va desde x1 = 700 (x2 = 800) hasta x1 = 1500 (x2 = 0)

# Graficamos las restricciones
ax.plot(x1, x2_demanda, label=r'R1: Demanda Valle ($x_1 + x_2 = 1500$ MWh)', color='#1c7ed6', linewidth=2.5)
ax.axhline(800, label=r'R2: Capacidad Gas ($x_2 \leq 800$ MWh)', color='#e03131', linestyle='--', linewidth=2)

# Sombreado de la recta factible (o región si fuese inecuación x1 + x2 >= 1500)
# Mostramos la región x1 + x2 >= 1500 y x2 <= 800
x_fill = np.linspace(700, 1800, 200)
y_bottom = np.maximum(0, 1500 - x_fill)
y_top = np.full_like(x_fill, 800)
ax.fill_between(x_fill, y_bottom, y_top, where=(y_top >= y_bottom), color='#b2f2bb', alpha=0.4, label='Región Factible (Inecuaciones)')

# Segmento de Demanda Exacta (Restricción de Igualdad)
ax.plot([700, 1500], [800, 0], color='#2b8a3e', linewidth=4.5, label='Frontera Factible de Demanda Exacta')

# Vértices de la frontera
# Vértice A: (700, 800)  --> Costo: 700*60 + 800*75 = 42,000 + 60,000 = $102,000
# Vértice B: (1500, 0)   --> Costo: 1500*60 + 0*75 = $90,000 (ÓPTIMO!)
ax.plot(700, 800, marker='o', markersize=10, color='#d9480f')
ax.annotate('Vértice A (700, 800)\nZ = $102,000 USD', xy=(700, 800), xytext=(730, 850),
            fontweight='bold', fontsize=9, arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

ax.plot(1500, 0, marker='*', markersize=16, color='#2b8a3e')
ax.annotate('VÉRTICE ÓPTIMO B (1500, 0)\nZ = $90,000 USD (MÍNIMO)', xy=(1500, 0), xytext=(1150, 200),
            fontweight='bold', fontsize=10, color='#2b8a3e',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ebfbee', edgecolor='#2b8a3e', linewidth=1.5),
            arrowprops=dict(facecolor='#2b8a3e', shrink=0.05, width=2, headwidth=8))

# Curvas de Nivel de la Función Objetivo (Isocostos Z = 60*x1 + 75*x2)
# Para Z = 120,000: x2 = (120000 - 60*x1)/75 = 1600 - 0.8*x1
# Para Z = 102,000: x2 = (102000 - 60*x1)/75 = 1360 - 0.8*x1
# Para Z = 90,000:  x2 = (90000 - 60*x1)/75  = 1200 - 0.8*x1
ax.plot(x1, (120000 - 60*x1)/75, color='#868e96', linestyle=':', label='Isocosto Z = $120,000 USD')
ax.plot(x1, (102000 - 60*x1)/75, color='#495057', linestyle='-.', label='Isocosto Z = $102,000 USD (Pasa por A)')
ax.plot(x1, (90000 - 60*x1)/75, color='#2b8a3e', linestyle='--', linewidth=2, label=r'Isocosto Óptimo $Z^* = \$90,000$ USD (Toca en B)')

# Flecha del gradiente de minimización
ax.annotate('Dirección de Minimización de Z', xy=(600, 400), xytext=(1000, 750),
            arrowprops=dict(facecolor='#e03131', shrink=0.05, width=2.5, headwidth=8),
            fontweight='bold', color='#e03131', fontsize=9)

ax.set_xlim(0, 1800)
ax.set_ylim(0, 1200)
ax.set_xlabel(r'Energía Red Tradicional en Valle $x_1$ (MWh) [Costo = \$60/MWh]', fontsize=11, fontweight='bold')
ax.set_ylabel(r'Energía Cogeneración Gas en Valle $x_2$ (MWh) [Costo = \$75/MWh]', fontsize=11, fontweight='bold')
ax.set_title(r'Método Gráfico 2D: Optimización de Abastecimiento Térmico en Franja Valle ($t_3$)', fontsize=12, fontweight='bold', pad=15)
ax.legend(loc='upper right', frameon=True, fontsize=8.5)

plt.tight_layout()
plt.savefig('metodo_grafico_2d.png', dpi=300)
plt.close()
print('metodo_grafico_2d.png generado exitosamente.')
