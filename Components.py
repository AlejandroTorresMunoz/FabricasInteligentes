import struct

# Valores de las direcciones de los sensores
class DirMem:
    # Clase para representar una dirección de memoria
    def __init__(self, bit_dir, byte_dir, length_bits):
        self.bit_dir = int(bit_dir) # Dirección del bit
        self.byte_dir = int(byte_dir) # Dirección del byte de inicio 
        self.length_bits = length_bits # Número de bits que ocupa en la memoria

class Sensor:
    class BoolSensor:
        # Estructura para almacenar el valor de un sensor booleano --> 1 bit
        def __init__(self, bit_dir, byte_dir, name_sensor):
            self.value = False # Valor del sensor
            self.dir_mem = DirMem(bit_dir, byte_dir, length_bits=1) # Dirección de memoria donde se encuentra el dato
        def GetValue(self, array_mem):
            # Función para obtener el valor del sensor dentro del array de bits de la memoria
            
            byte_val = array_mem[self.dir_mem.byte_dir]
            bit_val = (byte_val >> self.dir_mem.bit_dir) & 0x01
            return bool(bit_val) 
    class IntSensor:
        # structura para almacenar el valor de un sensor de tipo int --> 4 bytes
        def __init__(self, bit_dir, byte_dir, name_sensor):
            self.value = 0
            self.dir_mem = DirMem(bit_dir, byte_dir, length_bits= 2 * 8)
        def GetValue(self, array_mem):
            # Función para obtener el valor del sensor dentro de un array de bits de memoria
            valor_int = struct.unpack('>H', array_mem[self.dir_mem.byte_dir : self.dir_mem.byte_dir + 2])[0]
            return valor_int
    class RealSensor:
        # Estructura para almacenar el valor de un sensor de tipo real --> 4 bytes
        def __init__(self, bit_dir, byte_dir, name_sensor):
            self.value = 0
            self.dir_mem = DirMem(bit_dir, byte_dir, length_bits= 4 * 8) # Dirección de memoria donde se encuentra el dato
        def GetValue(self, array_mem):
            # Función para obtener el valor del sensor dentro del array de bits de memoria
            valor_float = struct.unpack('>f', array_mem[self.dir_mem.byte_dir : self.dir_mem.byte_dir + 4])[0]
            return valor_float
            # init_dir = self.dir_mem.bit_dir + (self.dir_mem.byte_dir * 8)
    def CreateDataSensor(row):
        # Función para crear las estructuras de datos en el DataFrame dado
        if row['Type'] == 'Boolean':
            DataStruct = Sensor.BoolSensor(byte_dir = row['Dir.Mem'].split('.')[0], bit_dir = row['Dir.Mem'].split('.')[1], name_sensor=row['Nombre']) 
        elif row['Type'] == 'Int':
            DataStruct = Sensor.IntSensor(byte_dir = row['Dir.Mem'].split('.')[0], bit_dir = row['Dir.Mem'].split('.')[1], name_sensor=row['Nombre'])
        elif row['Type'] == 'Real':
            DataStruct = Sensor.RealSensor(byte_dir = row['Dir.Mem'].split('.')[0], bit_dir = row['Dir.Mem'].split('.')[1], name_sensor=row['Nombre'])    
        return DataStruct
    
    def GetValueSensorByName(df, name):
        # Función para devolver el valor de un sensor dado su nombre
        return df.loc[df['Nombre'] == name]['Data'].reset_index(drop=True)[0]

class Actuator:
    class BoolActuator:
        # Estructura para almacenar el valor de un actuador booleano --> 1 bit
        def __init__(self, bit_dir, byte_dir, value, name_actuator):
            self.value = value # Valor del actuador
            print("Creando el actuador Booleano : ")
            print(name_actuator)
            print("bit_dir : "+str(bit_dir))
            print("byte_dir : "+str(byte_dir))
            self.dir_mem = DirMem(bit_dir, byte_dir, length_bits=1) # Dirección de memoria donde se encuentra el dato
        def SetValue(self, value):
            # Función para establecer el valor
            self.value = value
        def GetValue(self):
            # Función para obtener el valor
            return self.value
    class RealActuator:
        # Estructura para almacenar el valor de un actuador de tipo real --> 4 bytes
        def __init__(self, bit_dir, byte_dir, value, name_actuator):
            self.value = value
            self.dir_mem = DirMem(bit_dir, byte_dir, length_bits = 4 * 8)
        def SetValue(self, value):
            # Función para establecer el valor
            self.value = value
        def GetValue(self):
            # Función para obtener el valor
            return self.value
        
    def CreateDataActuator(row):
        # Función para crear las estructuras de datos en el DataFrame dado
        if row['Type'] == 'Boolean':
            DataStruct = Actuator.BoolActuator(byte_dir = row['Dir.Mem'].split('.')[0], bit_dir = row['Dir.Mem'].split('.')[1], value=row['Data'], name_actuator=row['Nombre']) 
        elif row['Type'] == 'Real':
            DataStruct = Actuator.RealActuator(byte_dir = row['Dir.Mem'].split('.')[0], bit_dir = row['Dir.Mem'].split('.')[1], value=row['Data'], name_actuator=row['Nombre']) 
        return DataStruct
    
    def GetValueActuatorByName(df, name):
        # Función para devolver el valor de un sensor dado su nombre
        return df.loc[df['Nombre'] == name]['Data'].reset_index(drop=True)[0]
    
    def ActivateGen(df, cat):
        # Función para activar una generación de objeto de una categoría dada
        index_row = df.loc[df['Nombre'] == cat].index[0]
        df.loc[index_row, 'Data'] = True
        return df
    
    def ResetGen(df, cat):
        # Función para desactivar la generación de objetos de una categoría dada
        index_row = df.loc[df['Nombre'] == cat].index[0]
        df.loc[index_row, 'Data'] = False
        return df
    
    def GetMessageActuators(df, length_in_bytes):
        # Función para crear el mensaje de datos a enviar a partir de los datos del dataframe de los actuadores
        # Creamos una variable de tipo bytes vacía
        b = bytearray(length_in_bytes)
        # Iteramos sobre cada fila del dataframe
        for index, row in df.iterrows():        
            # Calculamos el índice del byte y el offset del bit dentro del byte
            byte_index = row['DataStructs'].dir_mem.byte_dir
            bit_offset = row['DataStructs'].dir_mem.bit_dir
            # byte_index = row['DataStructs'].dir_mem.bit_dir + (row['DataStructs'].dir_mem.byte_dir * 8) // 8
            # bit_offset = row['DataStructs'].dir_mem.bit_dir + (row['DataStructs'].dir_mem.byte_dir * 8) % 8
            if row['Type'] == 'Real':
                # Si la fila se corresponde con un valor real que ocupa 4 bytes,
                # convertimos el valor a bytes utilizando el formato de punto flotante de 32 bits
                float_value = struct.pack('>f', row['Data'])
                # Guardamos los 4 bytes del valor en la variable de tipo 'bytes'
                for i in range(4):
                    b[byte_index + i] = float_value[i]
            elif row['Type'] == 'Boolean':
                # Si la fila se corresponde con un bit individual, modificamos el valor del byte correspondiente
                # utilizando el operador de bits OR y el desplazamiento de bits
                current_byte_value = b[byte_index]
                new_byte_value = current_byte_value | (row['Data'] << bit_offset)
                b[byte_index] = new_byte_value
        # Convertimos la variable de tipo 'bytearray' en 'bytes'
        b = bytes(b)
        return b