# Algoritmos de control de producción
from Components import Sensor, Actuator

class ControlAlg:
    # Clase que representa el algoritmo de control para la producción de un objeto
    def __init__(self, NameAlg, Category, InitSensorName, EndSensorName):
        # Parámetros genéricos del algoritmo
        self._name = NameAlg # Nombre del algoritmo
        self._category = Category # Categoría del objeto asociada
        # Sensores asociados
        self._init_sensor_name = InitSensorName # Nombre del sensor de la zona de generación
        self._end_sensor_name = EndSensorName # Nombre del sensor de final de carrera asociado
        # Señales internas del algoritmo
        self._gen_object_signal = False # Para determinar si se debe generar un objeto o no
        
    def GetGenObject(self):
        # Función para determinar si se debe generar un nuevo objeto
        return self._gen_object_signal
    
    def SetGenObject(self):
        # Función para establecer que se debe generar un nuevo objeto
        self._gen_object_signal = True
    
    def ResetGenObject(self):
        # Función para resetear que se debe generar un nuevo objeto
        self._gen_object_signal = False
    
    def UpdateGenSignal(self, df_actuators):
        # Función para actualizar el valor de la señal para generar los datos
        # Índice de la fila donde se encuentra el sensor de fin de carrera en el dataframe de actuadores
        index_row = df_actuators.loc[df_actuators['Nombre'] == self._end_sensor_associated].index[0] 
        # Se cambia el valor
        df_actuators.loc[index_row, 'Data'] = self._gen_object_signal
        return df_actuators
    
    def GetInitSensorSignal(self, df_sensors):
        # Función para obtener el valor del sensor de entrada
        return df_sensors.loc[df_sensors['Nombre'] == self._init_sensor_name]['Data'].reset_index()[0]
    
    def GetEndSensorSignal(self, df_sensors):
        # Función para obtener el valor del sensor de final de carrera
        return df_sensors.loc[df_sensors['Nombre'] == self._end_sensor_name]['Data'].reset_index()[0]
    
    def ExecuteControlAlgCat3(self, df_sensors, df_actuators):
        # Función para ejecutar el algoritmo de control de la categoría 3
        # Obtención de la señal de la zona de generación
        init_sensor_value = self.GetInitSensorSignal(df_sensors)
        # Obtención de la señal de final de la cinta
        end_sensor_value = self.GetEndSensorSignal(df_sensors)
        
        if(end_sensor_value == True):
            self.SetGenObject()
        
        df_actuators = self.UpdateGenSignal(df_actuators)
        return df_actuators

def CheckGenZone(df):
    # Función para comprobar si la zona de generación de objetos está libre
    if(Sensor.GetValueSensorByName(df, "S_In")):
        # Devolver un false en caso de que la zona esté ocupada
        return False
    else:
        # Devolver un true en caso de que la zona esté libre
        return True