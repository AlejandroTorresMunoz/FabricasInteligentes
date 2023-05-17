import socket
import sys
import pandas as pd
import time
import struct
from Components import Actuator, Sensor

def ControlCinta(df, nombre_cinta):
    # Función para controlar la cinta
    act_cinta = df.loc[df['Nombre'] == nombre_cinta]['Data'].reset_index(drop=True)[0]
    if act_cinta:
        return 200
    else:
        return 0
    
def ActCont(df_sensors, list_name_cat, df_prod):
    # Función para actualizar el valor de conteo de producción de las categorías
    for name_cat in list_name_cat:
        # Para cada nombre de la señal
        df_prod.loc[df_prod['Nombre'] == name_cat, 'Cont Cat'] = df_sensors.loc[df_sensors['Nombre'] == name_cat].reset_index()['Data'][0]
    return df_prod

def ActRate(df_prod):
    # Función para actualizar el rate de producción de una categoría dada
    print(df_prod)
    df_prod['Rate Production'] = df_prod['Cont Cat'] / df_prod['Cont Comm Loops']
    print("Dentro de la función de ActRate")
    return df_prod
    
# Parámetros Globales
COMM_PERIOD = 0.2 # Periodicidad de las comunicaciones 
DEN_MIN_RATE_PROD = 1 # Denominador del número de minutos en el que calcular el rate
NUMBER_LOOP_COMM_CHECK_RATE = int(DEN_MIN_RATE_PROD *(60 / COMM_PERIOD)) # Número de loops en el que actualizar el rate de producción (cada 2 minutos)

# DataFrame con los datos de los sensores
data_sensors = {'Nombre' : ['S1', 'S2', 'S3', 'Act_Cinta', 'Ang_Eje_Desv', 'Vel_Cinta', 'Rot_Base_ABB', 'Rot_L1_ABB', 'Rot_L2_ABB', 'Rot_L3_ABB', 'Rot_L4_ABB', 'Rot_L5_ABB', 'Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'],
                'Type' : ['Boolean', 'Boolean', 'Boolean', 'Boolean', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Int', 'Int', 'Int'],
                'Dir.Mem' : ['0.0', '0.1', '0.2', '0.3', '4.0', '8.0', '12.0', '16.0', '20.0', '24.0', '28.0', '32.0', '36.0', '38.0', '40.0'],
                'Data' : [False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                }
df_sensors = pd.DataFrame(data_sensors) # DataFrame con los datos de los sensores
# Creación de la columna con la estructuras de datos de los distintos sensores
df_sensors['DataStructs'] = df_sensors.apply(lambda row : Sensor.CreateDataSensor(row), axis=1)

# DataFrame con los datos de los actuadores
data_actuators = {'Nombre' : ['Vel_Cinta'],
                  'Type' : ['Real'],
                  'Dir.Mem' : ['0.0'],
                  'Data' : [150]
                  }
df_actuators = pd.DataFrame(data_actuators) # DataFrame con los datos de los actuadores
df_actuators['DataStructs'] = df_actuators.apply(lambda row : Actuator.CreateDataActuator(row), axis=1)

# DataFrame con los datos de producción
data_production = {'Category' : [3, 2, 1], # Número de la categoría
                   'Nombre' : ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], # Nombre de la señal asociada
                   'Cont Cat' : [0.0, 0.0, 0.0], # Contador de la categoría
                   'Cont Comm Loops' : [0, 0, 0], # Contador de los loops de comunicaciones
                   'Rate Production' : [0.0, 0.0, 0.0], # Rate de producción de la categoría
                   'Units' : ['Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)'] # Unidad de medida de la producción
                } 
df_production = pd.DataFrame(data_production) # DataFrame con los datos de producción

'''
Parámetros de control para la producción de las distintas categorías : 
    - Categoría 3 : 
        - Cinta Principal : Incrementar cuando la producción es inferior a la demanda.
        - Vel Eje Desv : Incrementar cuando la producción es inferior a la demanda.
        - Generador de objetos : Incrementar cuando la producción es inferior a la demanda.        
    - Categoría 2 :
    - Categoría 1 : 

'''

print("El DataFrame de sensores final es : ")
print(df_sensors.head())
print("El DataFrame final de actuadores es : ")
print(df_actuators.head())

# Crear TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Unir el socket al puerto
server_address = ('localhost', 6000)
print('Inicializando el servidor {} en el puerto {}'.format(*server_address))
sock.bind(server_address)

# Buscando conexiones entrantes
sock.listen(1)

while True: 
    # Espera para conectar
    print('Esperando conexion...')
    connection, client_address = sock.accept()
    cont_loop_comm = 0
    try:
        print('conexion desde', client_address)
        # Recibir datos y reenviar
        while True:    
            data = connection.recv(64)
            cont_loop_comm += 1 # Se incrementa en 1 el contador del loop de las comunicaciones
            bits = []
            for index_byte, byte in enumerate(data):
                bits_byte = []
                #print(byte)
                for i in range(8):
                    bit = byte & (1 << i) != 0
                    bits.append(bit)
            # Se guardan los datos del array de datos en bits 
            df_sensors['Data'] = df_sensors['DataStructs'].apply(lambda obj : obj.GetValue(data))
            #df_actuators.loc[df_actuators['Nombre'] == 'Vel_Cinta', 'Data'] = ControlCinta(df_sensors, 'Act_Cinta')
            # Se obtienen los valores del DataFrame de actuadores
            data_act = Actuator.GetMessageActuators(df_actuators, 64)
            print(df_sensors.head(20))
            print(df_actuators.head())
            print(df_production.head())
            print("cont_loop_comm : "+str(cont_loop_comm))
            print("NUMBER_LOOP_COMM_CHECK_RATE : "+str(NUMBER_LOOP_COMM_CHECK_RATE))
            if data:
                # print(type(data))
                connection.sendall(data_act)
            else:
                print('Datos inexistentes desde', client_address)
                break
            
            # Actualización de los DataFrames de producción 
            df_production = ActCont(df_sensors = df_sensors, list_name_cat = ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], df_prod = df_production) # Se actualiza el DataFrame de producción, en cuanto a los valores de conteo
            if cont_loop_comm == NUMBER_LOOP_COMM_CHECK_RATE:
                # Si se deben actualizar los valores de rate production
                cont_loop_comm = 0 # Resetear el conteo de los loops de comunicaciones
                df_production['Cont Comm Loops'] += 1 # Incremento en 1 el contador de chequeos
                df_production = ActRate(df_prod=df_production) # Actualización de los rates de producción

    except KeyboardInterrupt:
        # Finalización del programa
        print("Cerrando canal de conexión")
        connection.close()
    finally:
        # Limpiar conexion
        connection.close()
        