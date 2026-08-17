import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_PATH = Path("data/clima_dashboard_optimizado.parquet")

def proyectar_hasta_fin_de_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera filas proyectadas desde el 17 hasta el 31 de agosto de 2026
    basadas en los promedios recientes por región.
    """
    df['fecha'] = pd.to_datetime(df['fecha'])
    ultima_fecha = df['fecha'].max()
    
    # Rango de fechas a proyectar (del 17 al 31 de agosto de 2026)
    fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), end="2026-08-31")
    
    if len(fechas_futuras) == 0:
        df['es_proyeccion'] = False
        return df

    filas_proyectadas = []
    regiones = df['region'].unique()
    
    for region in regiones:
        df_region = df[df['region'] == region]
        
        # Promedio de los últimos 14 días registrados para proyectar
        ultimos_dias = df_region.sort_values('fecha').tail(14)
        
        temp_prom = ultimos_dias['temperature_2m'].mean() if 'temperature_2m' in ultimos_dias else 20.0
        humedad_prom = ultimos_dias['relative_humidity_2m'].mean() if 'relative_humidity_2m' in ultimos_dias else 70.0
        precip_prom = ultimos_dias['precipitation'].mean() if 'precipitation' in ultimos_dias else 0.0
        amplitud_prom = ultimos_dias['amplitud_termica'].mean() if 'amplitud_termica' in ultimos_dias else 8.0
        penaliz_prom = ultimos_dias['penalizacion_rendimiento_pct'].mean() if 'penalizacion_rendimiento_pct' in ultimos_dias else 0.0
        
        for fecha in fechas_futuras:
            # Reglas de negocio para asignar categóricas proyectadas
            es_helada = "Helada Negra" if temp_prom < 0 else ("Helada Blanca" if temp_prom < 3 else "Sin Helada")
            riesgo_bio = "Riesgo Alto" if humedad_prom > 80 and temp_prom > 18 else "Riesgo Bajo"
            ventana_fum = "Riesgo de Lavado (Roja)" if precip_prom > 2.0 else "Óptima (Verde)"
            estres_hid = "Alerta Sequía" if precip_prom < 0.1 and temp_prom > 22 else "Normal"
            calidad_fruto = "Estándar" if penaliz_prom > 10 else "Premium"

            nueva_fila = {
                'region': region,
                'anio': fecha.year,
                'mes': fecha.month,
                'dia': fecha.day,
                'fecha': fecha,
                'temperature_2m': round(temp_prom + np.random.uniform(-0.5, 0.5), 2),
                'relative_humidity_2m': round(humedad_prom, 2),
                'precipitation': round(precip_prom, 2),
                'amplitud_termica': round(amplitud_prom, 2),
                'penalizacion_rendimiento_pct': round(penaliz_prom, 2),
                'alerta_helada_tipo': es_helada,
                'riesgo_biologico': riesgo_bio,
                'ventana_fumigacion': ventana_fum,
                'estres_hidrico': estres_hid,
                'calidad_estimada_fruto': calidad_fruto,
                'es_proyeccion': True  # Marca que indica que es dato proyectado
            }
            filas_proyectadas.append(nueva_fila)
            
    df_proyectado = pd.DataFrame(filas_proyectadas)
    
    # Marcar los datos reales con False
    df['es_proyeccion'] = False
    
    # Concatenar datos históricos con la proyección
    return pd.concat([df, df_proyectado], ignore_index=True)


@st.cache_data(show_spinner=False)
def cargar_y_filtrar_datos() -> pd.DataFrame:
    """Carga y estructura el dataset climático para el dashboard agrícola."""
    if not DATA_PATH.exists():
        st.error(f"No se encontró el archivo en {DATA_PATH}")
        return pd.DataFrame()

    df = pd.read_parquet(DATA_PATH)
    
    # 1. Crear columna 'fecha' consolidando anio, mes y dia
    if all(col in df.columns for col in ["anio", "mes", "dia"]):
        temp_date_df = df[["anio", "mes", "dia"]].rename(columns={"anio": "year", "mes": "month", "dia": "day"})
        df["fecha"] = pd.to_datetime(temp_date_df, errors='coerce')
    else:
        st.error("Faltan las columnas de año, mes o día en el Parquet.")
        st.stop()
        
    # 2. Asegurar que las variables continuas sean numéricas
    cols_numericas = [
        "temperature_2m", "precipitation", "relative_humidity_2m", 
        "amplitud_termica", "penalizacion_rendimiento_pct", "wind_speed_10m"
    ]
    
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 3. Asegurar que las variables de alerta sean categóricas (strings)
    cols_categoricas = [
        "alerta_helada_tipo", "estres_hidrico", "riesgo_biologico", 
        "ventana_fumigacion", "calidad_estimada_fruto"
    ]
    for col in cols_categoricas:
        if col in df.columns:
            df[col] = df[col].astype(str)
            
    # 4. Generar y anexar proyecciones hasta el 31 de agosto
    df = proyectar_hasta_fin_de_mes(df)
    
    return df