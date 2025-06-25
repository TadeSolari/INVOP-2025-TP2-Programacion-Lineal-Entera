#%%

# Esto lo hice para ver si genero bien las variables cuando agrego las restricciones

n = 3 

nombres = [f"X_{i+1}{j+1}" for i in range(n) for j in range(n) if i != j]

print(nombres)

#%%

for i in range(n):
    index = [f"X_{i+1}{j+1}" for j in range(n) if i!=j]
    index_inv = [f"X_{j+1}{i+1}" for j in range(n) if i!=j]
    print(f"Genero las combinaciones que salen de {i+1}")
    print(index)
    print(f"Genero las combinaciones que llegan a {i+1}")
    print(index_inv)



# %%

# aca no contamos U_1 que va a ser el cliente de salida
# restriccion de continuidad
for i in range(1, n):
    for j in range(1,n):
        if i!=j:
            index = [f"U_{i+1}", f"U_{j+1}", f"X_{i+1}{j+1}"]
            print(index)