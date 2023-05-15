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

# DataFrame con los datos de los sensores
data_sensors = {'Nombre' : ['S1', 'S2', 'S3', 'Act_Cinta', 'Ang_Eje_Desv', 'Vel_Cinta', 'Rot_Base_ABB', 'Rot_L1_ABB', 'Rot_L2_ABB', 'Rot_L3_ABB', 'Rot_L4_ABB', 'Rot_L5_ABB', 'Cont_Cat_3'],
                'Type' : ['Boolean', 'Boolean', 'Boolean', 'Boolean', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Real', 'Int'],
                'Dir.Mem' : ['0.0', '0.1', '0.2', '0.3', '4.0', '8.0', '12.0', '16.0', '20.0', '24.0', '28.0', '32.0', '36.0'],
                'Data' : [False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
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
    try:
        print('conexion desde', client_address)
        # Recibir datos y reenviar
        while True:    
            data = connection.recv(40)
            bits = []
            for index_byte, byte in enumerate(data):
                bits_byte = []
                #print(byte)
                for i in range(8):
                    bit = byte & (1 << i) != 0
                    bits.append(bit)
            # Se guardan los datos del array de datos en bits 
            df_sensors['Data'] = df_sensors['DataStructs'].apply(lambda obj : obj.GetValue(data))
            df_actuators.loc[df_actuators['Nombre'] == 'Vel_Cinta', 'Data'] = ControlCinta(df_sensors, 'Act_Cinta')
            # Se obtienen los valores del DataFrame de actuadores
            data_act = Actuator.GetMessageActuators(df_actuators, 64)
            print(df_sensors.head(20))
            print(df_actuators.head())
            if data:
                # print(type(data))
                print(data_act)
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
        