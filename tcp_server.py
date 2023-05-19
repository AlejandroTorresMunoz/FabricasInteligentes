import socket
import sys
import pandas as pd
import time
import struct
from Components import Actuator, Sensor
from ControlAlgorithms import CheckGenZone # Función para chequear si la zona de generación está libre o no

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
    # print(df_prod)
    df_prod['Rate Production'] = df_prod['Cont Cat'] / df_prod['Cont Comm Loops']
    # print("Dentro de la función de ActRate")
    return df_prod
    
# Parámetros Globales
COMM_PERIOD = 0.1 # Periodicidad de las comunicaciones 
DEN_MIN_RATE_PROD = 1 # Denominador del número de minutos en el que calcular el rate
NUMBER_LOOP_COMM_CHECK_RATE = int(int(DEN_MIN_RATE_PROD *(60 / COMM_PERIOD)) / 12) # Número de loops en el que actualizar el rate de producción (cada 2 minutos)

# DataFrame con los datos de los sensores
data_sensors = {'Nombre' : ['S1', 'S2', 'S3', 'Act_Cinta', 'S_In', 'In_Gen_3', 'Ang_Eje_Desv', 'Vel_Cinta', 'Rot_Base_ABB', 'Rot_L1_ABB', 'Rot_L2_ABB', 'Rot_L3_ABB', 'Rot_L4_ABB', 'Rot_L5_ABB', 'Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'],
                'Type' : ['Boolean', 'Boolean', 'Boolean', 'Boolean', 'Boolean', 'Boolean', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Int', 'Int', 'Int'],
                'Dir.Mem' : ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '4.0', '8.0', '12.0', '16.0', '20.0', '24.0', '28.0', '32.0', '36.0', '38.0', '40.0'],
                'Data' : [False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                }
df_sensors = pd.DataFrame(data_sensors) # DataFrame con los datos de los sensores
# Creación de la columna con la estructuras de datos de los distintos sensores
df_sensors['DataStructs'] = df_sensors.apply(lambda row : Sensor.CreateDataSensor(row), axis=1)

# DataFrame con los datos de los actuadores
data_actuators = {'Nombre' : ['Gen_1', 'Gen_2', 'Gen_3', 'Vel_Cinta'],
                  'Type' : ['Boolean', 'Boolean', 'Boolean', 'Real'],
                  'Dir.Mem' : ['0.0', '0.1', '0.2', '4.0'],
                  'Data' : [False, False, False, 150]
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

print(NUMBER_LOOP_COMM_CHECK_RATE)

# Crear TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Unir el socket al puerto
server_address = ('localhost', 6000)
print('Inicializando el servidor {} en el puerto {}'.format(*server_address))
sock.bind(server_address)

# Buscando conexiones entrantes
sock.listen(1)
first_loop = False


'''
Variables for the control algorithms
'''
GenObjectCat3 = False

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
                    
            '''
            Actualización de los datos de los sensores --> df_sensors
            '''
            # Se guardan los datos del array de datos en bits 
            df_sensors['Data'] = df_sensors['DataStructs'].apply(lambda obj : obj.GetValue(data))
            # print(df_sensors.head(20))
            
            '''
            Implementación de control y actualización de dataframe de actuadores --> df_actuators
            '''
            # Implementación de algoritmo de control y actualización del DataFrame de los actuadores
            
            if cont_loop_comm % 30 == 0:
                GenObjectCat3 = not GenObjectCat3 # Invertir el valor de la señal
            if GenObjectCat3:
                df_actuators = Actuator.ActivateGen(df_actuators, 'Gen_3')
            else:
                df_actuators = Actuator.ResetGen(df_actuators, 'Gen_3')
            '''
            if cont_loop_comm == NUMBER_LOOP_COMM_CHECK_RATE:
                print("")
                print("")
                print("Se setea la señal para generar un objeto")
                if GenObjectCat3 == False:
                    print("Activando valores")
                    GenObjectCat3 = True # Se marca que se debe generar un objeto de la categoría
                    df_actuators = Actuator.ActivateGen(df_actuators, 'Gen_3')
                    print(df_actuators.head())
                else:
                    GenObjectCat3 = False
                    print("Reseteando valores")
                    df_actuators = Actuator.ResetGen(df_actuators, 'Gen_3')
                    print(df_actuators.head())
            '''            
                
            
            '''
            if(not Sensor.GetValueSensorByName(df_sensors, 'S_In') and (cont_loop_comm == int(NUMBER_LOOP_COMM_CHECK_RATE/60))):
            
                df_actuators = Actuator.ActivateGen(df_actuators, 'Gen_3')
            else:
                df_actuators = Actuator.ResetGen(df_actuators, 'Gen_3')     
            '''
            # Lectura del DataFrame de los actuadores para la generación del mensaje que se envía
            data_act = Actuator.GetMessageActuators(df_actuators, 16) 
            #print(df_actuators.head())
            
            if data:
                # print(type(data))
                print(data_act)
                connection.sendall(data_act)
            else:
                print('Datos inexistentes desde', client_address)
                break
            
            '''
            Implementación de actualización de los rates de producción --> df_production
            '''
            # Actualización de los DataFrames de producción 
            df_production = ActCont(df_sensors = df_sensors, list_name_cat = ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], df_prod = df_production) # Se actualiza el DataFrame de producción, en cuanto a los valores de conteo
            # print(df_production.head())
            if cont_loop_comm == NUMBER_LOOP_COMM_CHECK_RATE: # --> Cada minuto
                # Si se deben actualizar los valores de rate production
                cont_loop_comm = 0 # Resetear el conteo de los loops de comunicaciones
                print("Reseteando contador")
                df_production['Cont Comm Loops'] += 1 # Incremento en 1 el contador de chequeos
                df_production = ActRate(df_prod=df_production) # Actualización de los rates de producción
            first_loop = True

    except KeyboardInterrupt:
        # Finalización del programa
        print("Cerrando canal de conexión")
        connection.close()
    finally:
        # Limpiar conexion
        connection.close()
        