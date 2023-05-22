import socket
import sys
import pandas as pd
import time
import struct
from Components import Actuator, Sensor
from ControlAlgorithms import CategoryControlAlgorithm, UpdateActProd, ActRateProd, ActContProd, UpdateRateObj
import numpy as np
from tcp_server_parameters import COMM_PERIOD, DEN_MIN_RATE_PROD, NUMBER_LOOP_COMM_CHECK_RATE, LIM_NUM_CYCLES_TO_GENERATE, LIM_VEL_EJE_DESV_MAX, LIM_VEL_EJE_DESV_MIN
    
    
'''
Variables for the control algorithms
'''
GenerationZoneOccupied = False # Variable booleana para indicar si la zona de generación está ocupada. Su valor se rige por los dos sensores de la zona de generación
IsGoingToGenerate = 0 # Variable para indicar la categoría de la próxima categoría que se va a generar
NumberBeingGenerated = 0 # Variable para indicar la categoría que se está generando
VelRotAxis3 = 30 # Variable para indicar la velocidad de giro del eje de rotación establecido por la categoría 3
VelRotAxis2 = 30 # Variable para indicar la velocidad de giro del eje de rotación establecido por la categoría 2


# DataFrame con los datos de los sensores
data_sensors = {'Nombre' : ['S1', 'S2', 'S3', 'Act_Cinta', 'S_In', 'S_In_2', 'Ang_Eje_Desv', 'Vel_Cinta', 'Rot_Base_ABB', 'Rot_L1_ABB', 'Rot_L2_ABB', 'Rot_L3_ABB', 'Rot_L4_ABB', 'Rot_L5_ABB', 'Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1', 'Vel_Eje_Desv'],
                'Type' : ['Boolean', 'Boolean', 'Boolean', 'Boolean', 'Boolean', 'Boolean', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Int', 'Int', 'Int', 'Real'],
                'Dir.Mem' : ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '4.0', '8.0', '12.0', '16.0', '20.0', '24.0', '28.0', '32.0', '36.0', '38.0', '40.0', '42.0'],
                'Data' : [False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                }
df_sensors = pd.DataFrame(data_sensors) # DataFrame con los datos de los sensores
# Creación de la columna con la estructuras de datos de los distintos sensores
df_sensors['DataStructs'] = df_sensors.apply(lambda row : Sensor.CreateDataSensor(row), axis=1)

# DataFrame con los datos de los actuadores
data_actuators = {'Nombre' : ['Gen_1', 'Gen_2', 'Gen_3', 'Vel_Cinta', 'Vel_Eje_Desv'],
                  'Type' : ['Boolean', 'Boolean', 'Boolean', 'Real', 'Real'],
                  'Dir.Mem' : ['0.0', '0.1', '0.2', '4.0', '8.0'],
                  'Data' : [False, False, False, 200, 60]
                  }
df_actuators = pd.DataFrame(data_actuators) # DataFrame con los datos de los actuadores
df_actuators['DataStructs'] = df_actuators.apply(lambda row : Actuator.CreateDataActuator(row), axis=1)

# DataFrame con los datos de producción
data_production = {'Category' : [3, 2, 1], # Número de la categoría
                   'Nombre' : ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], # Nombre de la señal asociada
                   'Cont Cat' : [0.0, 0.0, 0.0], # Contador de la categoría
                   'Cont Comm Loops' : [0, 0, 0], # Contador de los loops de comunicaciones
                   'Rate Production' : [0.0, 0.0, 0.0], # Rate de producción de la categoría
                   'ObjRateProduction' : [5.0 , 2.0, 0.0], # Rate objetivo de producción de las categorías
                   'NumCyclesToGenerate' : [0, 0, 0], # Número de ciclos tras los que generar un objeto de la categoría en Python
                   'NumCycles' : [0, 0, 0], # Número de ciclos de la categoría
                   'GenObject' : [False, False, False], # Flags para establecer si se debe generar un objeto o no de la categoría correspondiente
                   'Units' : ['Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)', 'Prod/('+str(DEN_MIN_RATE_PROD)+' min)'] # Unidad de medida de la producción
                } 
df_production = pd.DataFrame(data_production) # DataFrame con los datos de producción
df_production, df_actuators, _ , _ = UpdateActProd(df_production, df_actuators, VelRotAxis3, VelRotAxis2) # Obtención inicial del número de loops con los que generar una nueva señal de generación de objeto


# DataFrame con los datos objetivos de producción
data_objective = {'Cat_3' : [5.0, 5.0, 5.0, 7.0, 7.0, 3.0, 3.0],
                  'Cat_2' : [2.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0],
                  'Cat_1' : [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
df_objective = pd.DataFrame(data_objective) # DataFrame con los valores de producción objetivos
df_production, df_objective = UpdateRateObj(df_production, df_objective)
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
print("El dataframe de producción es : ")
print(df_production.head())


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
                    
            '''
            Actualización de los datos de los sensores --> df_sensors
            '''
            # Se guardan los datos del array de datos en bits 
            df_sensors['Data'] = df_sensors['DataStructs'].apply(lambda obj : obj.GetValue(data))
            
            # Obtención de los valores de los sensores
            SensorZonaGeneracion = Sensor.GetValueSensorByName(df_sensors, 'S_In') # Valor del sensor de la zona de generación de objetos
            SensorZonaGeneracion2 = Sensor.GetValueSensorByName(df_sensors, 'S_In_2') # Valor del sensor de abandono de la zona de generación de objetos
            if SensorZonaGeneracion:
                # Si el sensor de la zona de generación se activa, se marca la zona de generación como ocupada
                GenerationZoneOccupied = True # Se marca la zona como ocupada
            if SensorZonaGeneracion2 and not SensorZonaGeneracion:
                # Si pasa un brownie por el sensor de abandona de la zona de generación, y no hay objeto sobre la zona de generación
                GenerationZoneOccupied = False # Se marca la zona como libre
            
            '''
            Implementación de actualización de los rates de producción y modificación de los valores a enviar de actuación--> df_production, df_actuators 
            '''
            # Actualización de los DataFrames de producción 
            df_production = ActContProd(df_sensors = df_sensors, list_name_cat = ['Cont_Cat_3', 'Cont_Cat_2', 'Cont_Cat_1'], df_prod = df_production) # Se actualiza el DataFrame de producción, en cuanto a los valores de conteo
            # print(df_production.head())
            if cont_loop_comm == NUMBER_LOOP_COMM_CHECK_RATE: # --> Cada minuto
                # Si se deben actualizar los valores de rate production
                cont_loop_comm = 0 # Resetear el conteo de los loops de comunicaciones
                df_production['Cont Comm Loops'] += 1 # Incremento en 1 el contador de chequeos
                df_production = ActRateProd(df_prod=df_production) # Actualización de los rates de producción
                # Actualización del número de loops tras los que generar una señal de generación de objeto en Python
                df_production, df_objective = UpdateRateObj(df_production, df_objective)
                df_production, df_actuators, VelRotAxis3, VelRotAxis2 = UpdateActProd(df_production, df_actuators, VelRotAxis3, VelRotAxis2) # Obtención inicial del número de loops con los que generar una nueva señal de generación de objeto
                print("Actualización de los valores de los actuadores realizada")
                print(df_actuators.head())
                print("Los valores de producción son : ")
                print(df_production.head())
                
                
                
            '''
            Implementación de control y actualización de dataframe de actuadores --> df_actuators
            '''
            # Implementación de algoritmo de control y actualización del DataFrame de los actuadores
            
            # Actualización de señales de generación en función de las indicaciones de producción 
            # Para la categoría 3
            IsGoingToGenerate, df_actuators, df_production = CategoryControlAlgorithm(IsGoingToGenerate = IsGoingToGenerate,
                                    GenerationZoneOccupied = GenerationZoneOccupied,
                                    SensorZonaGeneracion = SensorZonaGeneracion,
                                    NameCatDfAct = "Gen_3",
                                    df_act = df_actuators,
                                    NameCatDfProd = "Cont_Cat_3",
                                    df_prod = df_production
                                    )
            # Para la categoría 2
            IsGoingToGenerate, df_actuators, df_production = CategoryControlAlgorithm(IsGoingToGenerate = IsGoingToGenerate,
                                    GenerationZoneOccupied = GenerationZoneOccupied,
                                    SensorZonaGeneracion = SensorZonaGeneracion,
                                    NameCatDfAct = "Gen_2",
                                    df_act = df_actuators,
                                    NameCatDfProd = "Cont_Cat_2",
                                    df_prod = df_production
                                    )
                    
            # Lectura del DataFrame de los actuadores para la generación del mensaje que se envía
            data_act = Actuator.GetMessageActuators(df_actuators, 16) 
            #print(df_actuators.head())
            
            if data:
                # print(type(data))
                connection.sendall(data_act)
            else:
                print('Datos inexistentes desde', client_address)
                break
            

    except KeyboardInterrupt:
        # Finalización del programa
        print("Cerrando canal de conexión")
        connection.close()
    finally:
        # Limpiar conexion
        connection.close()
        