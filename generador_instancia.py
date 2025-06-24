#%%

import numpy as np

with open("salida.txt", "w") as f:

    cant_clientes = input("Cantidad de clientes (menor a 100): ")
    f.write(cant_clientes + "\n")
    costo_repartidor =input("Costo por repartidor: ")
    f.write(costo_repartidor + "\n")
    d_max = input("Distancia máxima: ")
    f.write(d_max + "\n")
    # 10% de nodos refrigerados 
    num_refrigerados = max(1, math.ceil(0.10 * len(clientes))) if len(clientes) > 0 else 0
    refrigerados = set(np.random.choice(clientes, size=num_refrigerados, replace=False))

    # 15% de nodos exclusivos
    num_exclusivos = max(1, math.ceil(0.15 * len(clientes))) if len(clientes) > 0 else 0
    exclusivos = set(np.random.choice(clientes, size=num_exclusivos, replace=False))

    f.write(str(len(refrigerados)) + "\n")
    for nodo in sorted(refrigerados):
        f.write(str(nodo) + "\n")

    f.write(str(len(exclusivos)) + "\n")
    for nodo in sorted(exclusivos):
        f.write(str(nodo) + "\n")

    # supongo grilla de 100x100 y los ubico aleatoriamente
    def generador_distancias_costos(cant_clientes, ancho=100, alto=100):
        coord_disponibles = [(x,y) for x in range(ancho) for y in range(alto)]
        coord_eleccion = np.random.choice(ancho**2, size=cant_clientes, replace=False) # selección uniforme
        coords = np.array([coord_disponibles[i] for i in coord_eleccion])
        
        lineas = []
        for i in range(cant_clientes):
            for j in range(i, cant_clientes): #ir de 1 a 2 = ir de 2 a 1, lo usa en la class que crearon los profes
                d = round(np.linalg.norm(coords[i] - coords[j])) # Redondeamos ?? la class espera int
                # en princpio costos = distancia
                linea = f"{i+1} {j+1} {d} {d}"
                lineas.append(linea)

        return lineas

    lineas = generador_distancias_costos(int(cant_clientes))

    for i in range(len(lineas)-1):
        f.write(lineas[i] + "\n")
    f.write(lineas[-1])
