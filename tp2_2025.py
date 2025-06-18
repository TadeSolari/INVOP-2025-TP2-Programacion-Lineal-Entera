import sys
# importamos el modulo cplex
import cplex

TOLERANCE = 1e-6

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cant_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        # almacenar índices 0-based
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
        self.pares_Y = {i: set() for i in range(self.cant_clientes)}

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


def agregar_variables(prob, instancia, version_modelo):
    # Definir y agregar las variables:
	# metodo 'add' de 'variables', con parametros:
	# obj: costos de la funcion objetivo
	# lb: cotas inferiores
    # ub: cotas superiores
    # types: tipo de las variables
    # names: nombre (como van a aparecer en el archivo .lp)
	
    # Poner nombre a las variables y llenar coef_funcion_objetivo

    # Formulacion Miller, Tucker and Zemlin
    
    n = instancia.cant_clientes

    # Xij = 1 si el camion se mueve del cliente i al cliente j / 0 cc
    nombres_Xij = [f"X_{i+1}{j+1}" for i in range(n) for j in range(n) if i != j]
    coeficientes_funcion_objetivo = [instancia.costos[i][j] for i in range(n) for j in range(n) if i != j]   
    prob.variables.add(obj = coeficientes_funcion_objetivo,
                       types = ['B']*len(nombres_Xij), 
                       names = nombres_Xij)


    # U_i = orden en que se visita la ciudad i. (i = 2 hasta n)
    # Declaramos al cliente 1 como el primero en visitarse => U_1 = 0
    nombres_U = [f"U_{i+1}" for i in range(n)]
    prob.variables.add(lb = [0] + [1]*(n - 1), 
                       ub = [0] + [n-1]*(n - 1), 
                       types= ['I'] * n, 
                       names = nombres_U)
    
    if ( not version_modelo ):
        # Yij = 1 si el cliente j es visitado a pie desde la parada en el cliente i / 0 cc
        nombres_Yij = []
        coeficientes_funcion_objetivo = []
        for i in range(n):
            for j in range(n):
                if (i != j and instancia.distancias[i][j] <= instancia.d_max):
                    nombres_Yij.append(f"Y_{i+1}{j+1}")
                    coeficientes_funcion_objetivo.append(instancia.costo_repartidor)
                    instancia.pares_Y[i].add(j)

        prob.variables.add(obj = coeficientes_funcion_objetivo,
                            types = ['B'] * len(nombres_Yij), 
                            names = nombres_Yij)
            
        # Variables delta_i
        nombres_delta = [f"delta_{i+1}" for i in range(n)]
        prob.variables.add(obj = [0.0]*n, 
                        lb = [0]*n, 
                        ub = [1]*n, 
                        types = ['B']*n, 
                        names = nombres_delta)


def agregar_restricciones(prob, instancia, version_modelo):
    # Agregar las restricciones ax <= (>= ==) b:
	# funcion 'add' de 'linear_constraints' con parametros:
	# lin_expr: lista de listas de [ind,val] de a
    # sense: lista de 'L', 'G' o 'E'
    # rhs: lista de los b
    # names: nombre (como van a aparecer en el archivo .lp)

    # Notar que cplex espera "una matriz de restricciones", es decir, una
    # lista de restricciones del tipo ax <= b, [ax <= b]. Por lo tanto, aun cuando
    # agreguemos una unica restriccion, tenemos que hacerlo como una lista de un unico
    # elemento.

    n = instancia.cant_clientes

    # Restricciones Metodologia inicial
    if (version_modelo):
        # El camion entra y sale una vez de cada cliente
        for i in range(n):
            idx = [f"X_{i+1}{j+1}" for j in range(n) if i!=j]
            idx_inv = [f"X_{j+1}{i+1}" for j in range(n) if i!=j]

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
        for i in range(1, n):
            for j in range(1,n):
                if i!=j:
                    prob.linear_constraints.add(lin_expr=[ [[f"U_{i+1}", f"U_{j+1}", f"X_{i+1}{j+1}"], [1, -1, n-1]]],
                                                senses=['L'], 
                                                rhs=[n-2],
                                                names = [f'Orden_desde_{i+1}_{j+1}']) 
                    
    # Restricciones Modelo Completo
    else:    
        # if n > 1:
        # (1) El camion sale desde el nodo 0:
        idx_out = [f"X_1{j+1}" for j in range(1, n)]
        prob.linear_constraints.add(lin_expr=[[idx_out, [1.0]*len(idx_out)]], 
                                    senses=['E'], 
                                    rhs=[1.0], 
                                    names=['Salida_desde_deposito'])
    
        # (2) El camion vuelve al nodo 0:
        idx_in = [f"X_{i+1}1" for i in range(1, n)]
        prob.linear_constraints.add(lin_expr=[[idx_in, [1.0]*len(idx_in)]], 
                                    senses=['E'], 
                                    rhs=[1.0], 
                                    names=['Entrada_al_deposito'])

        # 3) Nodo 0 tiene pos 0 al inicio
        # YA ESTABA EN LAS COTAS
        # prob.linear_constraints.add(lin_expr=[[[f"U_1"], [1.0]]], senses=['E'], rhs=[0.0], names=['U0'])
    
        # (4) El camión entra y sale una vez de cada casa de su recorrido (Flujo balanceado)
        for i in range(1, n):
            idx_out = [f"X_{i+1}{j+1}" for j in range(n) if j != i]
            idx_in = [f"X_{j+1}{i+1}" for j in range(n) if j != i]
            expr = idx_out + idx_in
            coefs = [1.0]*len(idx_out) + [-1.0]*len(idx_in)
            prob.linear_constraints.add(lin_expr=[ [expr, coefs] ], 
                                        senses=['E'], 
                                        rhs=[0.0], 
                                        names=[f"Balance_{i+1}"])

        # (5) Eliminar subtours (formulacion MTZ)
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    prob.linear_constraints.add(lin_expr=[ [[f"U_{i+1}", f"U_{j+1}", f"X_{i+1}{j+1}"], [1, -1, n-1]] ],
                                                senses=['L'], 
                                                rhs=[n-2], 
                                                names=[f"Subtour_{i+1}_{j+1}"])
                
        # (6) Todo cliente es atendido
        for j in range(1, n):
            idx_X = [f"X_{i+1}{j+1}" for i in range(n) if i != j]
            idx_Y = [f"Y_{i+1}{j+1}" for i in range(n) if i != j and j in instancia.pares_Y[i]]
            expr = idx_X + idx_Y
            coefs = [1.0]*len(idx_X) + [1.0]*len(idx_Y)
            prob.linear_constraints.add(lin_expr=[[expr, coefs]], 
                                        senses=['E'], 
                                        rhs=[1.0], 
                                        names=[f"Atiendo_{j+1}"])
        
        # (7) Si es visitado a pie, el camión para cerca:
        for (i, j) in instancia.pares_Y[i]:
            idx_stop = [f"X_{i+1}{k+1}" for k in range(n) if k != i]
            expr = [f"Y_{i+1}{j+1}"] + idx_stop
            coefs = [1.0] + [-1.0]*len(idx_stop)
            prob.linear_constraints.add(lin_expr=[[expr, coefs]], 
                                        senses=['L'], 
                                        rhs=[0.0], 
                                        names=[f"Parada_{i+1}_{j+1}"])
        
        # (8) Limite de productos refrigerados por repartidor
        for i in range(n):
            idxs = [f"Y_{i+1}{j+1}" for j in instancia.pares_Y[i] if (j in instancia.refrigerados)]
            if idxs:
                prob.linear_constraints.add(lin_expr=[[idxs, [1.0]*len(idxs)] ], 
                                            senses=['L'], 
                                            rhs=[1.0], 
                                            names=[f"RefLim_{i+1}"])
            
    # Restricciones deseables 
  
    # 9) Clientes exclusivos atendidos por camion
    for j in instancia.exclusivos:
      idx_X = [f"X_{i+1}{j+1}" for i in range(n) if i != j]
      prob.linear_constraints.add(lin_expr=[ [idx_X, [1.0]*len(idx_X)] ], senses=['E'], rhs=[1.0], names=[f"Exclusivo_{j+1}"])

      
    for i in range(n):
      idxs = [f"Y_{i+1}_{j+1}" for (i2, j) in instancia.pares_Y if i2 == i]
    if idxs:
        # 10) Minimo de entregas en la parada i
        prob.linear_constraints.add(
            lin_expr=[ [idxs + [f"delta_{i+1}"], [1.0]*len(idxs) + [-4.0]] ],
            senses=['G'], rhs=[0.0], names=[f"Min4_{i+1}"]
        )
        # 11) Maximo de entregas en la parada i
        prob.linear_constraints.add(
            lin_expr=[ [idxs + [f"delta_{i+1}"], [1.0]*len(idxs) + [-len(idxs)] ] ],
            senses=['L'], rhs=[0.0], names=[f"MaxJ_{i+1}"]
        )
    else:
        # Si J_i vacío, fuerzo delta_i = 0
        prob.linear_constraints.add(
            lin_expr=[ [[f"delta_{i+1}"], [1.0]] ],
            senses=['E'], rhs=[0.0], names=[f"Delta0_{i+1}"]
        )
    for i in range(n):
      idxs = [f"Y_{i+1}_{j+1}" for (i2, j) in instancia.pares_Y if i2 == i]
         
  


def armar_lp(prob, instancia, version):
    agregar_variables(prob, instancia, version)
    agregar_restricciones(prob, instancia,version)
    prob.objective.set_sense(prob.objective.sense.minimize)
    prob.write('recorridoMixto.lp')


def resolver_lp(prob):
    # Definir los parametros del solver
    #prob.parameters.mip.....
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
    for i in range(n):
        val_in = sum(prob.solution.get_values(f"X_{j+1}{i+1}") for j in range(n) if j!=i)
        if val_in > TOLERANCE:
            print(f"  Cliente {i+1}")
    print("Asignaciones a pie (i -> j):")
    for (i, j) in instancia.pares_Y:
        val = prob.solution.get_values(f"Y_{i+1}_{j+1}")
        if val > 0.5:
            print(f"  Desde parada {i+1} atiende a cliente {j+1}")



def main():
    
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    
    # Definicion del problema de Cplex
    prob = cplex.Cplex()
    
    # Definicion del modelo
    opcion = int(input("Ingresar version de modelo (1 = inicial, 2 = completo) "))
    version_modelo = (opcion == 1)
    armar_lp(prob,instancia, version_modelo)

    # # Resolucion del modelo
    # resolver_lp(prob)

    # # Obtencion de la solucion
    # mostrar_solucion(prob,instancia)

if __name__ == '__main__':
    main()
