import sys
# importamos el modulo cplex
import cplex

# EN ESTA VERSION SE ASUME QUE EL CLIENTE 1 ACTUA COMO DEPOSITO, POR LO QUE NO SE PERIMITE QUE SALGAN REPARTIDORES A PIE
# NI LLEGEN REPARTIDORES A PIE A ESTE CLIENTE

TOLERANCE = 1e-6

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cant_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        self.refrigerados = []
        self.exclusivos = []
        self.distancias = []        
        self.costos = []        
        self.pares_Y = dict()

    def leer_datos(self,filename):
        # abrimos el archivo de datos
        f = open(filename)

        # leemos la cantidad de clientes
        self.cant_clientes = int(f.readline())

        # Creamos el conjunto J_i
        self.pares_Y = {i+1 : set() for i in range(self.cant_clientes)}

        # leemos el costo por pedido del repartidor
        self.costo_repartidor = int(f.readline())
        # leemos la distamcia maxima del repartidor
        self.d_max = int(f.readline())
        
        # inicializamos distancias y costos con un valor muy grande (por si falta algun par en los datos)
        self.distancias = [[1000000 for _ in range(self.cant_clientes)] for _ in range(self.cant_clientes)]
        self.costos = [[1000000 for _ in range(self.cant_clientes)] for _ in range(self.cant_clientes)]
        
        # leemos la cantidad de refrigerados
        cantidad_refrigerados = int(f.readline())
        # leemos los clientes refrigerados
        for i in range(cantidad_refrigerados):
            self.refrigerados.append(int(f.readline()))
        
        # leemos la cantidad de exclusivos
        cantidad_exclusivos = int(f.readline())
        # leemos los clientes exclusivos
        for i in range(cantidad_exclusivos):
            self.exclusivos.append(int(f.readline()))
        
        # leemos las distancias y costos entre clientes
        lineas = f.readlines()
        for linea in lineas:
            row = list(map(int,linea.split(' ')))
            self.distancias[row[0]-1][row[1]-1] = row[2]
            self.distancias[row[1]-1][row[0]-1] = row[2]
            self.costos[row[0]-1][row[1]-1] = row[3]
            self.costos[row[1]-1][row[0]-1] = row[3]
        
        # cerramos el archivo
        f.close()


def cargar_instancia():
    nombre_archivo = sys.argv[1].strip()
    instancia = InstanciaRecorridoMixto()
    instancia.leer_datos(nombre_archivo)
    return instancia


def agregar_variables(prob, instancia, version_modelo, deseable):

    # Formulacion Miller, Tucker and Zemlin
    
    n = instancia.cant_clientes

    # X_i_j = 1 si el camion se mueve del cliente i al cliente j / 0 cc
    nombres_Xij = [f"X_{i}_{j}" for i in range(1,n+1) for j in range(1,n+1) if i != j]
    coeficientes_funcion_objetivo = [instancia.costos[i][j] for i in range(n) for j in range(n) if i != j]   
    prob.variables.add(obj = coeficientes_funcion_objetivo,
                       types = ['B']*len(nombres_Xij), 
                       names = nombres_Xij)


    # U_i = orden en el que el camion visita al cliente i
    # Definimos al Cliente 1 como el punto de partida y llegada => U_1 = 0
    nombres_U = [f"U_{i}" for i in range(1,n+1)]
    prob.variables.add(lb = [0] + [1]*(n - 1), 
                       ub = [0] + [n-1]*(n - 1), 
                       types= ['I'] * n, 
                       names = nombres_U)
    
    if ( not version_modelo ):
        # Y_i_j = 1 si el cliente j es visitado a pie desde la parada en el cliente i / 0 cc
        nombres_Yij = []
        coeficientes_funcion_objetivo = []
        for i in range(1,n): # REMUEVO LA POSIBILIDAD DE QUE DEL CLIENTE 1 SALGAN REPARTIDORES A PIE/BICI
            for j in range(1,n):
                if (i != j and instancia.distancias[i][j] <= instancia.d_max):
                    nombres_Yij.append(f"Y_{i+1}_{j+1}")
                    coeficientes_funcion_objetivo.append(instancia.costo_repartidor)
                    instancia.pares_Y[i+1].add(j+1)

        prob.variables.add(obj = coeficientes_funcion_objetivo,
                            types = ['B'] * len(nombres_Yij), 
                            names = nombres_Yij)
        
        if(deseable):
            # delta_i = 1 si desde la parada i se entregan al menos 4 pedidos a pie
            # REMUEVO LA POSIBILIDAD DE QUE DEL CLIENTE 1 SALGAN REPARTIDORES A PIE/BICI
            nombres_delta = [f"delta_{i}" for i in range(2,n+1)]
            prob.variables.add(obj = [0.0] * len(nombres_delta), 
                                lb = [0] * len(nombres_delta), 
                                ub = [1] * len(nombres_delta), 
                                types = ['B'] * len(nombres_delta), 
                                names = nombres_delta)


def agregar_restricciones(prob, instancia, version_modelo, deseables):

    n = instancia.cant_clientes

    # Restricciones Metodologia inicial
    if (version_modelo):
        # El camion entra y sale una vez de cada cliente
        for i in range(n):
            idx = [f"X_{i}_{j}" for j in range(1,n+1) if i!=j]
            idx_inv = [f"X_{j}_{i}" for j in range(1,n+1) if i!=j]

            # (1) De todo cliente hay que salir
            prob.linear_constraints.add(lin_expr=[[idx, [1] * (n - 1)]],
                                        senses=['E'], 
                                        rhs=[1],
                                        names = [f'Salgo_de_cliente{i+1}']) 
            
            # (2) A todo cliente se debe llegar
            prob.linear_constraints.add(lin_expr=[[idx_inv, [1] * (n - 1)]],
                                        senses=['E'], 
                                        rhs=[1],
                                        names = [f'Llego_a_cliente{i+1}']) 
        
        # (3) Eliminar subtours
        for i in range(2, n+1):
            for j in range(2, n+1):
                if i!=j:
                    prob.linear_constraints.add(lin_expr=[ [[f"U_{i}", f"U_{j}", f"X_{i}_{j}"], [1, -1, n-1]]],
                                                senses=['L'], 
                                                rhs=[n-2],
                                                names = [f'Orden_desde_{i}_{j}']) 
                    
    # Restricciones Modelo Completo
    else:    
        # if n > 1:
        # (1) El camion sale desde el Cliente 1:
        idx_out = [f"X_1_{j}" for j in range(2, n+1)]
        prob.linear_constraints.add(lin_expr=[[idx_out, [1.0]*len(idx_out)]], 
                                    senses=['E'], 
                                    rhs=[1.0], 
                                    names=['Salida_desde_deposito'])
    
        # (2) El camion vuelve al Cliente 1:
        idx_in = [f"X_{i}_1" for i in range(2, n+1)]
        prob.linear_constraints.add(lin_expr=[[idx_in, [1.0]*len(idx_in)]], 
                                    senses=['E'], 
                                    rhs=[1.0], 
                                    names=['Entrada_al_deposito'])

        # (3) El camión entra y sale una vez de cada casa de su recorrido (Flujo balanceado)
        for i in range(2, n+1):
            idx_out = [f"X_{i}_{j}" for j in range(1, n+1) if j != i]
            idx_in = [f"X_{j}_{i}" for j in range(1, n+1) if j != i]
            expr = idx_out + idx_in
            coefs = [1.0]*len(idx_out) + [-1.0]*len(idx_in)

            prob.linear_constraints.add(lin_expr=[ [expr, coefs] ], 
                                        senses=['E'], 
                                        rhs=[0.0], 
                                        names=[f"Balance_{i}_a"])

        # (4) Eliminar subtours (formulacion MTZ)
        for i in range(2, n+1):
            for j in range(2, n+1):
                if i != j:
                    prob.linear_constraints.add(lin_expr=[ [[f"U_{i}", f"U_{j}", f"X_{i}_{j}"], [1, -1, n-1]] ],
                                                senses=['L'], 
                                                rhs=[n-2], 
                                                names=[f"Subtour_{i}_{j}"])
                
        # (5) Todo cliente es atendido
        for j in range(2, n+1):
            idx_X = [f"X_{i}_{j}" for i in range(1, n+1) if i != j]
            idx_Y = [f"Y_{i}_{j}" for i in range(2, n+1) if i != j and j in instancia.pares_Y[i]]
            expr = idx_X + idx_Y
            coefs = [1.0]*len(idx_X) + [1.0]*len(idx_Y)
            prob.linear_constraints.add(lin_expr=[[expr, coefs]], 
                                        senses=['E'], 
                                        rhs=[1.0], 
                                        names=[f"Atiendo_{j}"])
        
        # (6) Si es visitado a pie, el camión para cerca:
        for i in range(2, n+1):
            for j in instancia.pares_Y[i]:
                idx_stop = [f"X_{k}_{i}" for k in range(1, n+1) if k != i]
                expr = [f"Y_{i}_{j}"] + idx_stop
                coefs = [1.0] + [-1.0]*len(idx_stop)
                prob.linear_constraints.add(lin_expr=[[expr, coefs]], 
                                            senses=['L'], 
                                            rhs=[0.0], 
                                            names=[f"Parada_{i}_{j}"])
        
        # (7) Limite de productos refrigerados por repartidor
        for i in range(2, n+1):
            idxs = [f"Y_{i}_{j}" for j in instancia.pares_Y[i] if (j in instancia.refrigerados)]
            if idxs:
                prob.linear_constraints.add(lin_expr=[ [idxs, [1.0]*len(idxs)] ], 
                                            senses=['L'], 
                                            rhs=[1.0], 
                                            names=[f"RefLim_{i}"])
            
    # Restricciones deseables 
    if (deseables):
        # (8) Clientes exclusivos atendidos por camion
        for j in instancia.exclusivos:
            idx_X = [f"X_{i}_{j}" for i in range(1, n+1) if i != j]
            prob.linear_constraints.add(lin_expr=[ [idx_X, [1.0]*len(idx_X)] ], 
                                        senses=['E'], 
                                        rhs=[1.0], 
                                        names=[f"Exclusivo_{j}"])

        
        for i in range(2, n+1):
            idxs = [f"Y_{i}_{j}" for j in instancia.pares_Y[i]]
            if idxs:
                # (9) Minimo de entregas en la parada i
                prob.linear_constraints.add(lin_expr=[ [idxs + [f"delta_{i}"], [1.0]*len(idxs) + [-4.0]] ],
                                            senses=['G'], 
                                            rhs=[0.0], 
                                            names=[f"Min4_{i}"])
                
                # (10) Maximo de entregas en la parada i
                prob.linear_constraints.add(lin_expr=[ [idxs + [f"delta_{i}"], [1.0]*len(idxs) + [-len(idxs)] ] ],
                                            senses=['L'], 
                                            rhs=[0.0], 
                                            names=[f"MaxJ_{i}"])
            else:
                # Si J_i vacío, forzamos delta_i = 0
                prob.linear_constraints.add(lin_expr=[ [[f"delta_{i}"], [1.0]] ],
                                            senses=['E'], 
                                            rhs=[0.0], 
                                            names=[f"Delta0_{i}"])     
  

def armar_lp(prob, instancia, version, deseables):
    agregar_variables(prob, instancia, version, deseables)
    agregar_restricciones(prob, instancia,version, deseables)
    prob.objective.set_sense(prob.objective.sense.minimize)
    prob.write('recorridoMixto.lp')


def resolver_lp(prob):
    # https://www.ibm.com/docs/en/cofz/12.10.0?topic=cplex-list-parameters
    
    # Este siempre activo, la otra strategy no la vimos
    # prob.parameters.mip.strategy.search.set(1) # Traditional branch-and-cut search

    # PREPROCESAMIENTO ACTIVO
    # prob.parameters.preprocessing.presolve.set(1) #

    # ESTRATEGIA DE SELECCION DE NODOS
    # prob.parameters.mip.strategy.nodeselect.set(0) # Depth-first search
    # prob.parameters.mip.strategy.nodeselect.set(1) # Best-bound search

    # HEURISTICAS
    # prob.parameters.mip.strategy.heuristicfreq.set(10) # Heuristicas periodicas cada 10 nodos
    # prob.parameters.mip.strategy.heuristiceffort.set(0) # 0 = Heuristicas desactivadas

    # TODOS LOS CORTES DESACTIVADOS
    # prob.parameters.mip.cuts.cliques.set(-1)
    # prob.parameters.mip.cuts.covers.set(-1)
    # prob.parameters.mip.cuts.flowcovers.set(-1)
    # prob.parameters.mip.cuts.gomory.set(-1)
    # prob.parameters.mip.cuts.mircut.set(-1)
    # prob.parameters.mip.cuts.pathcut.set(-1)
    # prob.parameters.mip.cuts.implied.set(-1)
    # prob.parameters.mip.cuts.liftproj.set(-1)
    # prob.parameters.mip.cuts.mcfcut.set(-1)
    # prob.parameters.mip.cuts.zerohalfcut.set(-1)
    # prob.parameters.mip.cuts.disjunctive.set(-1)
    # prob.parameters.mip.cuts.bqp.set(-1)

    # TIEMPO LIMITE
    # prob.parameters.mip.tolerances.mipgap.set(0.03) # por gap (3%)
    # prob.parameters.timelimit.set(300) # por tiempo (3 minutos)

    # Resolver LP
    prob.solve()


def mostrar_solucion(prob, instancia):
      
    # Obtener informacion de la solucion a traves de 'solution'
    
    # Tomar el estado de la resolucion
    status = prob.solution.get_status_string(status_code=prob.solution.get_status())

    # Tomar el valor del funcional
    valor_obj = prob.solution.get_objective_value()
    print('Funcion objetivo: ', valor_obj, '(', status, ')')
  
    n = instancia.cant_clientes
    print("Paradas de camión:")
    recorrido = [(1,0)]

    for i in range(2, n+1):
        orden = prob.solution.get_values(f"U_{i}")
        
        visitado_a_pie = False
        for j in range(2, n+1):
            if i != j:
                try:
                    if prob.solution.get_values(f"Y_{j}_{i}") > 0.5:
                        visitado_a_pie = True
                        break
                except:                    
                    pass
        
        if not visitado_a_pie:
            recorrido.append((i, orden))

    recorrido_ordenado = sorted(recorrido, key = lambda x: x[1])
    recorrido_ordenado.append((1,0))
    for cliente, _ in recorrido_ordenado:
        print(f"  Cliente {cliente}")

    print("Asignaciones a pie:")
    for i in instancia.pares_Y:
        for j in instancia.pares_Y[i]:
            val = prob.solution.get_values(f"Y_{i}_{j}")
            if val > 0.5:
                print(f"  Desde parada {i} atiende a cliente {j}")

    # nombres = prob.variables.get_names()
    # valor_variables = prob.solution.get_values()

    # for nom, val in zip(nombres, valor_variables):
    #     print(f"{nom} = {val}")



def main():
    
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    
    # Definicion del problema de Cplex
    prob = cplex.Cplex()
    
    # Definicion del modelo
    opcion = int(input("Ingresar version de modelo (1 = inicial, 2 = completo) "))
    version_modelo = (opcion == 1)

    deseables = False
    if(not version_modelo):
        restr_deseables = int(input("Agregar restricciones deseables? (1 = si, 2 = no) "))
        deseables = (restr_deseables == 1)

    armar_lp(prob, instancia, version_modelo, deseables)

    # # Resolucion del modelo
    resolver_lp(prob)

    # # Obtencion de la solucion
    mostrar_solucion(prob,instancia)

if __name__ == '__main__':
    main()
