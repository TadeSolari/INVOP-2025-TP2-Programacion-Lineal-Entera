#%%
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import math

#%%
np.random.seed(234)

n = int(input("Cantidad de puntos:"))


mod = n // 3
resto = n % 3
puntos_por_cluster = [mod + (1 if i < resto else 0) for i in range(3)]  # Suma el resto a los primeros clusters
centros = np.array([[0, 0], [20, 0], [10, 20]])  


puntos = []
labels = []
for i, (centro, n) in enumerate(zip(centros, puntos_por_cluster)):
    cluster = centro + np.random.randint(-2, 3, size=(n, 2))  # Rango reducido para formar clúster
    puntos.append(cluster)
    labels += [i] * n

puntos = np.vstack(puntos)
labels = np.array(labels)


distancias = cdist(puntos, puntos)
distancias = np.rint(distancias).astype(int)  # Redondeo a enteros


#%%
# Graficar scatterplot
plt.figure(figsize=(8, 6))
colores = ['red', 'green', 'blue']
for i in range(3):
    cluster_pts = puntos[labels == i]
    plt.scatter(cluster_pts[:, 0], cluster_pts[:, 1], color=colores[i], label=f'Cluster {i+1}')

for i, (x, y) in enumerate(puntos):
    plt.text(x + 0.3, y + 0.3, str(i+1), fontsize=9)  # Número del punto

plt.title("Clientes en 3 clusters")
plt.xlabel("Distancia en X")
plt.ylabel("Distancia en Y")
plt.grid(True)
plt.legend()
plt.axis('equal')
plt.show()

#%%
# Escribir archivo de salida
costo_repartidor = input("Costo por repartidor: ")
d_max = input("Distancia máxima (d_max): ")

n = len(puntos)
clientes = list(range(2, int(n) + 1))

with open("archivo.txt", "w") as f:
    f.write(str(n) + "\n")  # Cantidad de puntos
    f.write(str(costo_repartidor) + "\n")
    f.write(str(d_max) + "\n")

    
    # 10% de nodos refrigerados 
    num_refrigerados = max(1, math.ceil(0.10 * len(clientes))) if len(clientes) > 0 else 0
    refrigerados = set(np.random.choice(clientes, size=num_refrigerados, replace=False))

    f.write(str(len(refrigerados)) + "\n")
    for nodo in sorted(refrigerados):
        f.write(str(nodo) + "\n")
    


    # 15% de nodos exclusivos
    num_exclusivos = max(1, math.ceil(0.15 * len(clientes))) if len(clientes) > 0 else 0
    exclusivos = set(np.random.choice(clientes, size=num_exclusivos, replace=False))
    
    f.write(str(len(exclusivos)) + "\n")
    for nodo in sorted(exclusivos):
        f.write(str(nodo) + "\n")



    # Escribir matriz de distancias (i j dij dij)
    for i in range(n):
        for j in range(i, n):
            d = distancias[i, j]
            linea = f"{i+1} {j+1} {d} {d}\n"
            f.write(linea)

print(f"Archivo de salida generado correctamente con {n} puntos: archivo.txt")

# %%
