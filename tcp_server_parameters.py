# Parámetros Globales
COMM_PERIOD = 0.1 # Periodicidad de las comunicaciones 
DEN_MIN_RATE_PROD = 1 # Denominador del número de minutos en el que calcular el rate
NUMBER_LOOP_COMM_CHECK_RATE = int(int(DEN_MIN_RATE_PROD *(60 / COMM_PERIOD))) # Número de loops en el que actualizar el rate de producción (cada 1 minuto)
LIM_NUM_CYCLES_TO_GENERATE = 100 # Límite mínimo con el que enviar una señal de generación de objetos
LIM_VEL_EJE_DESV_MAX = 90 # Límite máximo en la velocidad del eje de desviación
LIM_VEL_EJE_DESV_MIN = 30 # Límite mínimo en la velocidad del eje de desviación