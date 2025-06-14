import sys
#importamos el modulo cplex
import cplex

TOLERANCE =10e-6 

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cant_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        self.refrigerados = []
        self.exclusivos = []
        self.distancias = []        
        self.costos = []        

    def leer_datos(self,filename):
        # abrimos el archivo de datos
        f = open(filename)

        # leemos la cantidad de clientes
        self.cantidad_clientes = int(f.readline())
        # leemos el costo por pedido del repartidor
        self.costo_repartidor = int(f.readline())
        # leemos la distamcia maxima del repartidor
        self.d_max = int(f.readline())
        
        # inicializamos distancias y costos con un valor muy grande (por si falta algun par en los datos)
        self.distancias = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        self.costos = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        
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
    # El 1er parametro es el nombre del archivo de entrada
    nombre_archivo = sys.argv[1].strip()
    # Crea la instancia vacia
    instancia = InstanciaRecorridoMixto()
    # Llena la instancia con los datos del archivo de entrada 
    instancia.leer_datos(nombre_archivo)
    return instancia

def agregar_variables(prob, instancia):
    # Definir y agregar las variables:
	# metodo 'add' de 'variables', con parametros:
	# obj: costos de la funcion objetivo
	# lb: cotas inferiores
    # ub: cotas superiores
    # types: tipo de las variables
    # names: nombre (como van a aparecer en el archivo .lp)
	
    # Poner nombre a las variables y llenar coef_funcion_objetivo

    # Formulacion Miller, Tucker and Zemlin

    # Xij = 1 si el camion se mueve del cliente i al cliente j / 0 cc
    n = instancia.cant_clientes
    nombres = [f"X_{i+1}{j+1}" for i in range(n) for j in range(n) if i != j]
    coeficientes_funcion_objetivo = [instancia.costos[i][j] for i in range(n) for j in range(instancia.cant_clientes) if i != j]
    
    # Agregar las variables
    prob.variables.add(obj = coeficientes_funcion_objetivo, 
                       lb = [0]*len(nombres), 
                       ub = [1]*len(nombres), 
                       types= ['B']*len(nombres), 
                       names=nombres)
    
    # U_i = orden en que se visita la ciudad i. (i = 2 hasta n)
    # Declaro al cliente 1 como el primero => U_1 = 1
    nombres = [f"U_{i+1}" for i in range(n)]
    prob.variables.add(obj = [0] * n, 
                        lb = [2] * n, 
                        ub = [n] * n, 
                        types= ['I'] * n, 
                        names=nombres)

def agregar_restricciones(prob, instancia):
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
    valores = [1] * len(n - 1) # -1 pq no contamos los repetidos

    for i in range(n-1):
        index = [f"X_{i+1}{j+1}" for j in range(n-1) if i!=j]
        index_inv = [f"X_{j+1}{i+1}" for j in range(4) if i!=j]
        filas = [index, valores]
        filas_inv = [index_inv, valores]

        # de toda ciudad tengo que salir
        prob.linear_constraints.add(lin_expr=filas,
                                    senses=['E'], 
                                    rhs=[1],
                                    names = [f'Salgo de cliente{i+1}']) 
        
        # a toda ciudad se debe llegar
        prob.linear_constraints.add(lin_expr=filas_inv,
                                    senses=['E'], 
                                    rhs=[1],
                                    names = [f'Llego a cliente{i+1}']) 
        
    # continuidad
    for i in range(1, n):
        for j in range(1,n):
            if i!=j:
                index = [f"U_{i+1}", f"U_{j+1}", f"X_{i+1}{j+1}"]
                valores = [1, -1, n]
                fila = [index, valores]

                prob.linear_constraints.add(lin_expr=fila,
                                            senses=['L'], 
                                            rhs=[n-1],
                                            names = [f'Continuidad desde {i+1}']) 
                
    # cliente 1 es el primero en visitarse
    prob.linear_constraints.add(lin_expr=["U_1"],
                                senses=['E'], 
                                rhs=[1],
                                names = ['Comienzo desde Cliente 1']) 
            

def armar_lp(prob, instancia):

    # Agregar las variables
    agregar_variables(prob, instancia)
   
    # Agregar las restricciones 
    agregar_restricciones(prob, instancia)

    # Setear el sentido del problema
    prob.objective.set_sense(prob.objective.sense.minimize)

    # Escribir el lp a archivo
    prob.write('recorridoMixto.lp')

def resolver_lp(prob):
    
    # Definir los parametros del solver
    #prob.parameters.mip.....
       
    # Resolver el lp
    prob.solve()

def mostrar_solucion(prob,instancia):
    
    # Obtener informacion de la solucion a traves de 'solution'
    
    # Tomar el estado de la resolucion
    status = prob.solution.get_status_string(status_code = prob.solution.get_status())
    
    # Tomar el valor del funcional
    valor_obj = prob.solution.get_objective_value()
    
    print('Funcion objetivo: ',valor_obj,'(' + str(status) + ')')
    
    # Tomar los valores de las variables
    x  = prob.solution.get_values()

    # Mostrar las variables con valor positivo (mayor que una tolerancia)
    ..... 

def main():
    
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    
    # Definicion del problema de Cplex
    prob = cplex.Cplex()
    
    # Definicion del modelo
    armar_lp(prob,instancia)

    # Resolucion del modelo
    resolver_lp(prob)

    # Obtencion de la solucion
    mostrar_solucion(prob,instancia)

if __name__ == '__main__':
    main()