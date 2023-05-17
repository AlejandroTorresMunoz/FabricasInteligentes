import pandas as pd
DEN_MIN_RATE_PROD = 2 # Denominador del número de minutos en el que calcular el rate

# Creación de la curva de demandas de la categoría 3
# La producción va a ser de x piezas/2 min
data_production = {'Category' : [3, 2, 1], # Número de la categoría
                   'Nombre' : ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], # Nombre de la señal asociada
                   'Cont Cat' : [0.0, 0.0, 0.0], # Contador de la categoría
                   'Cont Comm Loops' : [0, 0, 0], # Contador de los loops de comunicaciones
                   'Rate Production' : [0.0, 0.0, 0.0], # Rate de producción de la categoría
                   'Units' : ['Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)'] # Unidad de medida de la producción
                } 
df_production = pd.DataFrame(data_production) # DataFrame con los datos de producción

print(df_production)

df_production[:, 'Cont Comm Loops'] += 1
print(df_production)