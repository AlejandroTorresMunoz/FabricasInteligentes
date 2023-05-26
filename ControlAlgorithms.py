from Components import Sensor, Actuator
# Importado de valores constantes de parámetros
import numpy as np
import pandas as pd
from tcp_server_parameters import COMM_PERIOD, DEN_MIN_RATE_PROD, NUMBER_LOOP_COMM_CHECK_RATE, LIM_NUM_CYCLES_TO_GENERATE, LIM_VEL_EJE_DESV_MAX, LIM_VEL_EJE_DESV_MIN, LIM_VEL_EJE_ARM_MAX, LIM_VEL_EJE_ARM_MIN, LIM_VEL_CINTA_MAX, LIM_VEL_CINTA_MIN



def CategoryControlAlgorithm(IsGoingToGenerate, GenerationZoneOccupied, SensorZonaGeneracion, NameCatDfAct, df_act, NameCatDfProd, df_prod):
    # Función que ejecuta el algoritmo de control de una categoría dada
    df_act.loc[df_act['Nombre'] == NameCatDfAct, 'Data'] = df_prod.loc[df_prod['Nombre'] == NameCatDfProd]['GenObject'].reset_index(drop=True)[0]
    NumberCategory = int(NameCatDfAct[-1])
    # Se cheque de manera global que se debe generar un objeto y si se debe genera el objeto y la zona de generación está libre
    if IsGoingToGenerate == NumberCategory and not GenerationZoneOccupied:
        print("Generando objeto de la categoría : "+str(NumberCategory))
        df_act = Actuator.ResetGen(df_act, 'Gen_'+str(NumberCategory)) # Se pone a false la generación --> Se activa por flanco de bajada la generación de objetos 
        df_prod.loc[df_prod['Nombre'] == NameCatDfProd, 'GenObject'] = False # Se resetea la flag para indicar que se genere un objeto de la categoría
        
    # Reseteo de la variable de generación
    if IsGoingToGenerate != 0 and SensorZonaGeneracion:
        IsGoingToGenerate = 0
        
    if df_prod.loc[df_prod['Nombre'] == NameCatDfProd, 'GenObject'].reset_index(drop=True)[0]:
        # Si se ha marcado que se debe generar una cateogría
        if IsGoingToGenerate == 0:
            # Si no está reservado el valor de generación a otra categoría
            # print("Generando objeto de la categoría : "+str(NumberCategory))
            IsGoingToGenerate = NumberCategory # Se reserva el valor con el número de la categoría
            df_act = Actuator.ActivateGen(df_act, NameCatDfAct)
        
    return IsGoingToGenerate, df_act, df_prod

def ActRateProd(df_prod):
    # Función para actualizar el rate de producción de una categoría dada
    df_prod['Rate Production'] = df_prod['Cont Cat'] / df_prod['Cont Comm Loops']
    return df_prod

def ActContProd(df_sensors, list_name_cat, df_prod):
    # Función para actualizar el valor de conteo de producción de las categorías
    for name_cat in list_name_cat:
        # Para cada nombre de la señal
        df_prod.loc[df_prod['Nombre'] == name_cat, 'Cont Cat'] = Sensor.GetValueSensorByName(df_sensors, name_cat)
        df_prod.loc[df_prod['Nombre'] == name_cat, 'NumCycles'] += 1 # Incrementar en 1 el número de loops de comunicaciones
        if df_prod.loc[df_prod['Nombre'] == name_cat].reset_index(drop=True)['NumCycles'][0] >= df_prod.loc[df_prod['Nombre'] == name_cat].reset_index(drop=True)['NumCyclesToGenerate'][0]:
            df_prod.loc[df_prod['Nombre'] == name_cat, 'NumCycles'] = 0 # Se resetea el conteo
            df_prod.loc[df_prod['Nombre'] == name_cat, 'GenObject'] = True # Se indica que se debe generar un objeto de la cateogoría
    return df_prod

def UpdateActProd(df_prod, df_act, VelRotAxis3, VelRotAxis2, VelRotArms, VelCinta1, VelCinta2, VelCinta3):
    # Función para actualizar el número de loops de comunicaciones para los que una categoría debería generar una señal para cumplir con el rate de producción
    NewPeriodCategories = NUMBER_LOOP_COMM_CHECK_RATE / df_prod['ObjRateProduction']
    NewPeriodCategories = NewPeriodCategories.apply(lambda x: int(x) if np.isfinite(x) else x)
    # Se recorre cada fila del DataFrame:
    for index, row in df_prod.iterrows():
        # Para cada fila del DataFrame de producción
        if index == 0 :
            # Para la categoría 3
            if df_prod['Rate Production'][index] <= df_prod['ObjRateProduction'][index]-1:
                # En el caso de que la producción sea inferior al objetivo
                VelRotAxis3 = VelRotAxis3 + 5 # Se incrementa en 5 la velocidad de giro del eje de desviación
                if VelRotAxis3 > LIM_VEL_EJE_DESV_MAX:
                    VelRotAxis3 = LIM_VEL_EJE_DESV_MAX

                VelCinta3 = VelCinta3 + 10 # Se incrementa en 10 la velocidad de la cinta
                if VelCinta3 > LIM_VEL_CINTA_MAX:
                    VelCinta3 = LIM_VEL_CINTA_MAX
            elif df_prod['Rate Production'][index] >= df_prod['ObjRateProduction'][index]+1:
                # En el caso de que la producción sea superior al objetivo
                VelRotAxis3 =VelRotAxis3 - 5 # Se decrementa en 5 la velocidad de giro del eje de desviación
                if VelRotAxis3 < LIM_VEL_EJE_DESV_MIN:
                    VelRotAxis3 = LIM_VEL_EJE_DESV_MIN

                VelCinta3 = VelCinta3 - 10 # Se decrementa en 10 la velocidad de la cinta
                if VelCinta3 < LIM_VEL_CINTA_MIN:
                    VelCinta3 = LIM_VEL_CINTA_MIN
        elif index == 1:
            # Para la categoría 2
            if df_prod['Rate Production'][index] <= df_prod['ObjRateProduction'][index]-1:
                # En el caso de que la producción sea inferior al objetivo
                VelRotAxis2 =VelRotAxis3 + 5 # Se incrementa en 5 la velocidad de giro del eje de desviación
                if VelRotAxis2 > LIM_VEL_EJE_DESV_MAX:
                    VelRotAxis2 = LIM_VEL_EJE_DESV_MAX

                VelCinta2 = VelCinta2 + 10 # Se incrementa en 10 la velocidad de la cinta
                if VelCinta2 > LIM_VEL_CINTA_MAX:
                    VelCinta2 = LIM_VEL_CINTA_MAX
            elif df_prod['Rate Production'][index] >= df_prod['ObjRateProduction'][index]+1:
                # En el caso de que la producción sea superior al objetivo
                VelRotAxis2 =VelRotAxis3 - 5 # Se decrementa en 5 la velocidad de giro del eje de desviación
                if VelRotAxis2 < LIM_VEL_EJE_DESV_MIN:
                    VelRotAxis2 = LIM_VEL_EJE_DESV_MIN
                
                VelCinta2 = VelCinta2 - 10 # Se decrementa en 10 la velocidad de la cinta
                if VelCinta2 < LIM_VEL_CINTA_MIN:
                    VelCinta2 = LIM_VEL_CINTA_MIN
        elif index == 2:
            # Para la categoría 1
            if df_prod['Rate Production'][index] <= df_prod['ObjRateProduction'][index]-1:
                # En el caso de que la producción sea inferior al objetivo
                VelRotArms =VelRotArms + 15 # Se incrementa en 5 la velocidad de giro del eje de desviación
                if VelRotArms > LIM_VEL_EJE_ARM_MAX:
                    VelRotArms = LIM_VEL_EJE_ARM_MAX

                VelCinta1 = VelCinta1 + 10 # Se incrementa en 10 la velocidad de la cinta
                if VelCinta1 > LIM_VEL_CINTA_MAX:
                    VelCinta1 = LIM_VEL_CINTA_MAX
            elif df_prod['Rate Production'][index] >= df_prod['ObjRateProduction'][index]+1:
                # En el caso de que la producción sea superior al objetivo
                VelRotArms =VelRotArms - 15 # Se decrementa en 5 la velocidad de giro del eje de desviación
                if VelRotArms < LIM_VEL_EJE_ARM_MIN:
                    VelRotArms = LIM_VEL_EJE_ARM_MIN
                VelCinta1 = VelCinta1 - 10 # Se decrementa en 10 la velocidad de la cinta
                if VelCinta1 < LIM_VEL_CINTA_MIN:
                    VelCinta1 = LIM_VEL_CINTA_MIN

    NewPeriodCategories = NewPeriodCategories.clip(lower = LIM_NUM_CYCLES_TO_GENERATE) # Establecer el límite mínimo del período en el que enviar una nueva señal de generación
    df_prod['NumCyclesToGenerate'] = NewPeriodCategories # Se carga en el DataFrame los valores de período con el límite ya checkeado
    
    # Actualización del DataFrame de los actuadores
    index_row = df_act.loc[df_act['Nombre'] == "Vel_Eje_Desv"].index[0]
    df_act.loc[index_row, 'Data'] = (VelRotAxis3 + VelRotAxis2) / 2

    index_row = df_act.loc[df_act['Nombre'] == "Vel_Cinta"].index[0]
    df_act.loc[index_row, 'Data'] = (VelCinta1 + VelCinta2 + VelCinta3) / 3

    names = ["Vel_L" + str(i) for i in range(1, 7)]
    for name in names:
        index_row = df_act.loc[df_act['Nombre'] == name].index[0]
        df_act.loc[index_row, 'Data'] = VelRotArms
    

    
    return df_prod, df_act, VelRotAxis3, VelRotAxis2, VelRotArms, VelCinta1, VelCinta2, VelCinta3

def UpdateRateObj(df_prod, df_obj):
    # Función para actualizar el rate de producción
    print("UpdateRateObj")
    df_prod['ObjRateProduction'] = df_obj.iloc[0].tolist()
    print(pd.Series(df_obj.iloc[0]))
    df_obj = df_obj.drop(df_prod.index[0]).reset_index(drop=True)
    return df_prod, df_obj