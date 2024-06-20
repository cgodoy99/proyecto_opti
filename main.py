import pandas as pd
from gurobipy import Model, GRB, quicksum
from gurobipy import GRB
import csv
import glob

# Parametros

# Z: Presupuesto anual de la empresa
Z = 1158040800

# M: Valor suficientemente grande para las restricciones
M = 100000000000

# Parametro c_gt: Costo asociado al funcionamiento de la planta g en el dia t
c_gt = []
with open('costos.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        costo_de_g_en_cada_dia = []
        for t in range(len(row)):
            costo_de_g_en_cada_dia.append(float(row[t]))
        c_gt.append(costo_de_g_en_cada_dia)

# Parametro p_ht: Costo marginal en la hora h en el dia t
p_th = [] 

with open('costo-marginal.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        costo_marginal_en_cada_dia= []
        for t in range(len(row)):
            costo_marginal_en_cada_dia.append(float(row[t]))
        p_th.append(costo_marginal_en_cada_dia)

# Parametro i_a: Costo inicial de instalacion del almacenamiento a por unidad
i_a = []
with open('costo_instalacion.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        costo_inicial_de_a = float(row[0])
        i_a.append(costo_inicial_de_a)

# Parametro k_a: Costo de uso del almacenamiento a por hora
k_a = []
with open('costo_uso_almacenamiento.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        costo_de_uso_de_a = float(row[0])
        k_a.append(costo_de_uso_de_a)

# Parametro e_gth: Energia generada por la planta g en el dia t en la hora h
# Un archivo por planta, cada fila representa el dia y la columna la hora

e_gth = []
archivos_energia_generada = sorted(glob.glob('energia_generada*.csv'))
for archivo in archivos_energia_generada:
    planta = []
    with open(archivo, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            dia = [float(valor) for valor in row]
            planta.append(dia)
    e_gth.append(planta)

# Parametro w_a: Capacidad maxima del almacenamiento a
w_a = []
with open('capacidad_almacenamiento.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        capacidad_maxima_de_a = float(row[0])
        w_a.append(capacidad_maxima_de_a)

# Parametro y_a: Eficiencia del almacenamiento a
y_a = []
with open('eficiencia_almacenamiento.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        eficiencia_de_a = float(row[0])
        y_a.append(eficiencia_de_a)

# Parametro ds_a: Tasa de descarga del almacenamiento a
ds_a = []
with open('tasa_descarga.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        tasa_de_descarga_de_a = float(row[0])
        ds_a.append(tasa_de_descarga_de_a)

# Rangos
na = len(i_a)  # Número de tipos de almacenamiento
ng = len(e_gth)  # Número de plantas generadoras

# Conjuntos

T_ = range(1, 8)  # Días de 1 a 7
H_ = range(1, 25)  # Horas de 1 a 24
A_ = range(na)  # Tipos de almacenamiento
G_ = range(ng)  # Plantas generadoras

# Crear el modelo
model = Model("Parque Eólico")


# # Variables
X = model.addVars(A_, T_, vtype=GRB.CONTINUOUS, name="X_at")
S= model.addVars(G_, A_, T_, H_, vtype=GRB.CONTINUOUS, name="S_gath")
Q = model.addVars(A_, T_, H_, vtype=GRB.CONTINUOUS, name="Q_ath")
P = model.addVars(A_, T_, H_, vtype=GRB.BINARY, name="P_ath")
L = model.addVars(A_, T_, H_, vtype=GRB.CONTINUOUS, name="L_ath")
H = model.addVars(G_, T_, H_, vtype=GRB.CONTINUOUS, name="H_gth")
B = model.addVars(T_, vtype=GRB.CONTINUOUS, name="B_t")
GAlm = model.addVars(A_, T_, H_, vtype=GRB.CONTINUOUS, name="GAlm_ath")
GPar = model.addVars(G_, T_, H_, vtype=GRB.CONTINUOUS, name="GPar_gth")

# # Función Objetivo: Maximizar ganancias
# model.setObjective(
#     4 * (
#         gp.quicksum(GParquethg[t, h, g] + GAlmtha[t, h, a] - Ctg[g, t] - Ptha[t, h, a] * Ka[a]
#                     for t in T for h in H for a in A for g in G))
#         + Z - Ia[a] * Xat[a, t] )

# # Restricciones

# Almacenamiento

# Restricion 1: Balance de energía del almacenamiento a
# REVISAR ESTA RESTRICCIÓN
for g in G_:
    for a in A_:
        for t in T_:
            for h in H_:
                if h == 1:
                    model.addConstr(Q[a, t, h] == y_a[a-1] * S[g, a, t, h] - L[a, t, h])
                else:
                    model.addConstr(Q[a, t, h] == Q[a, t, h-1] - ds_a[a-1] * Q[a, t, h-1] + y_a[a-1] * S[g, a, t, h] - L[a, t, h])

# Restricion 2: Capacidad máxima del almacenamiento a
                    
model.addConstrs(Q[a, t, h] <= w_a[a-1] for a in A_ for t in T_ for h in H_)      

model.addConstrs(y_a[a-1] * S[g, a, t, h] <= w_a[a-1] for g in G_ for a in A_ for t in T_ for h in H_)
                    
# Restriccion 3: No se puede liberar más energía de la que se tiene

model.addConstrs(L[a, t, h] <= Q[a, t, h] for a in A_ for t in T_ for h in H_)

# Generacion de energía

# Restriccion 4: No se puede almacenar e inyectar más energía de la que se genera

model.addConstrs(quicksum(S[g, a, t, h] for a in A_) + H[g, t, h] <= e_gth[g-1][t-1][h-1] for g in G_ for t in T_ for h in H_)
                    
# Costos
                    
# Restriccion 5: No se puede superar el presupuesto en la inversión inicial

model.addConstr(quicksum(i_a[a-1] * X[a, t] for a in A_ for t in T_) <= Z)                    

# Restriccion 6: Activar variable binaria para luego calcular costos

model.addConstrs(Q[a, t, h] * M >= P[a, t, h] for a in A_ for t in T_ for h in H_)
                    
model.addConstrs(Q[a, t, h] <= P[a, t, h] * M for a in A_ for t in T_ for h in H_)

# Restriccion 7: Definicion de ganancias

model.addConstrs(GPar[g, t, h] == p_th[t-1][h-1] * H[g, t, h] for g in G_ for t in T_ for h in H_)

model.addConstrs(GAlm[a, t, h] == p_th[t-1][h-1] * L[a, t, h] for a in A_ for t in T_ for h in H_)

# Funcion Objetivo

model.update()

model.setObjective(4*quicksum(GPar[g, t, h] + GAlm[a, t, h] - c_gt[g-1][t-1] - P[a, t, h] * k_a[a-1] for g in G_ for t in T_ for h in H_) + Z - quicksum(i_a[a-1] * X[a, t] for a in A_ for t in T_), GRB.MAXIMIZE)

model.optimize()

# Resultados

# Valor optimo
print("----------------------")
print()
print(f"El valor óptimo es {model.ObjVal} pesos")
print()
print("----------------------")
print()

# Variables

# for v in model.getVars():
#     print(f'{v.varName}: {v.x}')


# # Capacidad máxima del almacenamiento
# for t in T:
#     for h in H:
#         for a in A:
#             model.addConstr(Qtha[t, h, a] <= Wa[a], name=f"Capacidad_max_{t}_{h}_{a}")
#             model.addConstr(Ya[a] * Sthag[t, h, a] <= Wa[a], name=f"Eficiencia_max_{t}_{h}_{a}")

# # No se puede liberar más energía de la que se tiene
# for t in T:
#     for h in H:
#         for a in A:
#             model.addConstr(Ltha[t, h, a] <= Qtha[t, h, a], name=f"Energia_inyectada_{t}_{h}_{a}")

# # No se puede almacenar e inyectar más energía de la que se genera
# for t in T:
#     for h in H:
#         for g in G:
#             for a in A:
#                 model.addConstr(Sthag[t, h, a, g] + Hthg[t, h, g] <= Ethg[g, t, h], name=f"Generacion_max_{t}_{h}_{g}")

# # No se puede superar el presupuesto en la inversión inicial
# model.addConstr(gp.quicksum(Ia[a] * Xat[a, t] for a in A for t in T) <= Z, name="Presupuesto")

# # Activar variable binaria para costos
# M = 1e6  # Un valor suficientemente grande
# for t in T:
#     for h in H:
#         for a in A:
#             model.addConstr(Qtha[t, h, a] * M >= Ptha[t, h, a], name=f"Binary_activation_1_{t}_{h}_{a}")
#             model.addConstr(Qtha[t, h, a] <= Ptha[t, h, a] * M, name=f"Binary_activation_2_{t}_{h}_{a}")

# # Definición de ganancias
# for t in T:
#     for h in H:
#         for g in G:
#             model.addConstr(GParquethg[t, h, g] == Pht[h, t] * Hthg[t, h, g], name=f"Ganancia_generacion_{t}_{h}_{g}")
#         for a in A:
#             model.addConstr(GAlmtha[t, h, a] == Pht[h, t] * Ltha[t, h, a], name=f"Ganancia_almacenamiento_{t}_{h}_{a}")

# # Optimización
# model.optimize()

# # Resultados
# if model.status == GRB.OPTIMAL:
#     print('Optimal solution found:')
#     for v in model.getVars():
#         print(f'{v.varName}: {v.x}')
# else:
#     print('No optimal solution found')

