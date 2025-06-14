#%%

import numpy as np

with open("salida.txt", "w") as f:

    cant_clientes = input("Cantidad de clientes (menor a 100): ")
    f.write(cant_clientes + "\n")
    costo_repartidor =input("Costo por repartidor: ")
    f.write(costo_repartidor + "\n")
    d_max = input("Distancia máxima: ")
    f.write(d_max + "\n")

    cantidad_refrigerados = input("Cantidad_refrigerados: ")
    f.write(cantidad_refrigerados + "\n")

    for i in range(int(cantidad_refrigerados)):
        dato = input(f"Refrigerado nro {i + 1}: ")
        f.write(dato + "\n")

    cantidad_exclusivos = input("Cantidad_exclusivos: ")
    f.write(cantidad_exclusivos + "\n")
    for i in range(int(cantidad_exclusivos)):
        dato = input(f"Exclusivo nro {i + 1}: ")
        f.write(dato + "\n")

    # supongo grilla de 100x100 y los ubico aleatoriamente
    def generador_distancias_costos(cant_clientes, ancho=100, alto=100):
        coord_disponibles = [(x,y) for x in range(ancho) for y in range(alto)]
        coord_eleccion = np.random.choice(ancho**2, size=cant_clientes, replace=False) # selección uniforme
        coords = np.array([coord_disponibles[i] for i in coord_eleccion])
        
        lineas = []
        for i in range(cant_clientes):
            for j in range(i, cant_clientes): #ir de 1 a 2 = ir de 2 a 1, lo usa en la class que crearon los profes
                d = np.linalg.norm(coords[i] - coords[j])
                # en princpio costos = distancia
                linea = f"{i+1} {j+1} {d:.2f} {d:.2f}" # redondeo ?
                lineas.append(linea)

        return lineas

    lineas = generador_distancias_costos(int(cant_clientes))

    for linea in lineas:
        f.write(linea + "\n")