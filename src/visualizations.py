import plotly.express as px
import pandas as pd

# P1: ¿Cuál es el clima general y la humedad? (Para planificar la semana)
def plot_clima_general(df: pd.DataFrame):
    df_agrupado = df.groupby('fecha')[['temperature_2m', 'relative_humidity_2m']].mean().reset_index()
    fig = px.line(df_agrupado, x='fecha', y=['temperature_2m', 'relative_humidity_2m'],
                  title="Evolución de Temperatura (°C) y Humedad (%)",
                  labels={'value': 'Valor', 'fecha': 'Fecha', 'variable': 'Métrica'})
    fig.update_layout(plot_bgcolor="white", hovermode="x unified")
    return fig

# P2: ¿Cuándo es seguro fumigar? (Evitar pérdida de agroquímicos por lluvia)
def plot_ventana_fumigacion(df: pd.DataFrame):
    conteo = df.groupby(['region', 'ventana_fumigacion']).size().reset_index(name='Dias')
    fig = px.bar(conteo, x='region', y='Dias', color='ventana_fumigacion',
                 title="Días con Ventana Óptima vs Riesgo de Lavado por Región",
                 color_discrete_map={'Óptima (Verde)': '#2E7D32', 'Riesgo de Lavado (Roja)': '#C62828'},
                 barmode='group')
    fig.update_layout(plot_bgcolor="white")
    return fig

# P3: ¿Cuál es el riesgo biológico por región? (Alerta de plagas/hongos)
def plot_riesgo_biologico(df: pd.DataFrame):
    conteo = df[df['riesgo_biologico'] == 'Riesgo Alto'].groupby('region').size().reset_index(name='Dias_Riesgo_Alto')
    fig = px.bar(conteo, x='Dias_Riesgo_Alto', y='region', orientation='h',
                 title="Total de Días con Alerta de Riesgo Biológico ALTO",
                 color='Dias_Riesgo_Alto', color_continuous_scale='Reds')
    fig.update_layout(plot_bgcolor="white")
    return fig

# P4: ¿Qué# P4 MEJORADA: Frecuencia de heladas por región y tipo de evento
def plot_alertas_heladas(df: pd.DataFrame):
    # Filtrar eventos donde realmente ocurrieron heladas
    df_heladas = df[df['alerta_helada_tipo'].isin(['Helada Blanca', 'Helada Negra'])].copy()
    
    if df_heladas.empty:
        # Retorna un gráfico vacío con mensaje limpio
        fig = px.bar(title="❄️ No se registraron heladas en las regiones y años seleccionados.")
        fig.update_layout(plot_bgcolor="white")
        return fig

    # Agrupar por Región y Tipo de Helada
    conteo = df_heladas.groupby(['region', 'alerta_helada_tipo']).size().reset_index(name='Dias_Evento')

    # Gráfico de barras apiladas por región
    fig = px.bar(
        conteo, 
        x='region', 
        y='Dias_Evento', 
        color='alerta_helada_tipo',
        title="Frecuencia de Heladas (Blanca vs. Negra) por Región",
        labels={
            'region': 'Región', 
            'Dias_Evento': 'Días con Helada', 
            'alerta_helada_tipo': 'Tipo de Helada'
        },
        color_discrete_map={
            'Helada Blanca': '#64B5F6',  # Azul claro
            'Helada Negra': '#37474F'    # Gris/Negro oscuro (alto riesgo)
        },
        barmode='stack'
    )
    fig.update_layout(plot_bgcolor="white", xaxis_title="", yaxis_title="Número de Días")
    return fig

# P5: ¿Cómo impacta el clima en la rentabilidad (Penalización y Calidad)?
def plot_calidad_vs_penalizacion(df: pd.DataFrame):
    fig = px.box(df, x='calidad_estimada_fruto', y='penalizacion_rendimiento_pct', color='region',
                 title="Impacto en la Penalización de Rendimiento (%) según Calidad del Fruto",
                 labels={'calidad_estimada_fruto': 'Calidad Estimada', 'penalizacion_rendimiento_pct': 'Penalización (%)'})
    fig.update_layout(plot_bgcolor="white")
    return fig