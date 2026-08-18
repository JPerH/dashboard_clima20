import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# P1: Proyección Meteorológica a 14 Días (Líneas históricas vs proyectadas)
def plot_clima_general(df: pd.DataFrame):
    if df.empty: return px.line(title="Sin datos")
    
    fig = go.Figure()
    df = df.sort_values('fecha')
    
    if 'es_proyeccion' in df.columns:
        df_hist = df[df['es_proyeccion'] == False].groupby('fecha')[['temperature_2m', 'relative_humidity_2m']].mean().reset_index()
        df_proy = df[df['es_proyeccion'] == True].groupby('fecha')[['temperature_2m', 'relative_humidity_2m']].mean().reset_index()
        
        # Conectar la última fecha histórica con la primera de la proyección para que la línea no se corte
        if not df_hist.empty and not df_proy.empty:
            df_proy = pd.concat([df_hist.iloc[-1:], df_proy])

        if not df_hist.empty:
            fig.add_trace(go.Scatter(x=df_hist['fecha'], y=df_hist['temperature_2m'], 
                                     mode='lines', name='Temperatura Histórica (°C)', line=dict(color='#2b7bba', width=2)))
            fig.add_trace(go.Scatter(x=df_hist['fecha'], y=df_hist['relative_humidity_2m'], 
                                     mode='lines', name='Humedad Histórica (%)', line=dict(color='#2ca02c', width=2)))
        
        if len(df_proy) > 1:
            fig.add_trace(go.Scatter(x=df_proy['fecha'], y=df_proy['temperature_2m'], 
                                     mode='lines+markers', name='Proyección Temp (14d)', line=dict(color='#ff7f0e', dash='dash', width=2)))
            fig.add_trace(go.Scatter(x=df_proy['fecha'], y=df_proy['relative_humidity_2m'], 
                                     mode='lines+markers', name='Proyección Humedad (14d)', line=dict(color='#d62728', dash='dash', width=2)))
    
    fig.update_layout(title="P1: Proyección Meteorológica a 14 Días", 
                      plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      xaxis_title="Fecha", yaxis_title="Valor")
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    return fig


# Función auxiliar para preparar las matrices de los Heatmaps (P2, P3, P4)
def _generar_matriz_heatmap(df, columna, mapeo):
    if 'es_proyeccion' in df.columns:
        df = df[df['es_proyeccion'] == True].copy()
    else:
        df = df.tail(14 * len(df['region'].unique())).copy() # Fallback si no hay bool
        
    df['fecha_str'] = df['fecha'].dt.strftime('%d/%m')
    
    # Pivotar para crear la matriz: Filas = Región, Columnas = Día
    matrix_texto = df.pivot_table(index='region', columns='fecha_str', values=columna, aggfunc='last')
    
    # Reemplazar el texto por los valores numéricos del mapeo para aplicar la escala de color
    matrix_num = matrix_texto.replace(mapeo).apply(pd.to_numeric, errors='coerce')
    
    return matrix_num, matrix_texto


# P2: Calendario Diario de Ventana de Fumigación a 14 Días (Heatmap)
def plot_ventana_fumigacion(df: pd.DataFrame):
    if df.empty: return go.Figure()
    
    # 1. CORRECCIÓN: El texto debe coincidir exactamente con los datos de tu DataFrame
    mapeo = {'Óptima (Verde)': 1, 'Riesgo de Lavado (Roja)': 0}
    
    matrix_num, hover_txt = _generar_matriz_heatmap(df, 'ventana_fumigacion', mapeo)
    matrix_num = matrix_num.fillna(0) # Rojo por defecto si falta
    
    fig = px.imshow(matrix_num, 
                    labels=dict(x="Día Proyectado", y="Región", color="Estado"),
                    color_continuous_scale=[[0, '#C62828'], [1, '#2E7D32']], # 0: Rojo, 1: Verde
                    zmin=0, zmax=1, # 2. CORRECCIÓN: Obligar a Plotly a usar 0 para rojo y 1 para verde
                    title="P2: Calendario Diario de Ventana de Fumigación a 14 Días<br><sup>Ubicación exacta de días Óptimos (Verde) vs Riesgo (Rojo)</sup>")
    
    fig.update_traces(xgap=2, ygap=2, hovertemplate="Región: %{y}<br>Día: %{x}<br>Estado: %{customdata}<extra></extra>", customdata=hover_txt)
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-45)
    return fig


# P3: Matriz de Riesgo Biológico (Heatmap)
def plot_riesgo_biologico(df: pd.DataFrame):
    if df.empty: return go.Figure()
    
    mapeo = {'Riesgo Alto': 0, 'Riesgo Bajo': 1, 'Normal': 1} 
    matrix_num, hover_txt = _generar_matriz_heatmap(df, 'riesgo_biologico', mapeo)
    matrix_num = matrix_num.fillna(1)
    
    fig = px.imshow(matrix_num,
                    labels=dict(x="Día Proyectado", y="Región", color="Riesgo"),
                    color_continuous_scale=[[0, '#C62828'], [1, '#2E7D32']],
                    title="P3: Alertas Diarias de Riesgo Biológico (Plagas/Hongos) a 14 Días<br><sup>Fechas exactas con Alerta ALTA (Rojo) vs Condición Segura (Verde)</sup>")
    
    fig.update_traces(xgap=2, ygap=2, hovertemplate="Región: %{y}<br>Día: %{x}<br>Riesgo: %{customdata}<extra></extra>", customdata=hover_txt)
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-45)
    return fig


# P4: Detección Diaria de Heladas (Heatmap)
def plot_alertas_heladas(df: pd.DataFrame):
    if df.empty: return go.Figure()
    
    mapeo = {'Helada Negra': 0, 'Helada Blanca': 0.5, 'Sin Helada': 1}
    matrix_num, hover_txt = _generar_matriz_heatmap(df, 'alerta_helada_tipo', mapeo)
    matrix_num = matrix_num.fillna(1)
    
    fig = px.imshow(matrix_num,
                    labels=dict(x="Día Proyectado", y="Región", color="Helada"),
                    color_continuous_scale=[[0, '#B71C1C'], [0.5, '#F57C00'], [1, '#2E7D32']],
                    zmin=0, zmax=1,
                    title="P4: Detección Diaria de Heladas a 14 Días<br><sup>Ubicación exacta de Heladas Negras (Rojo), Heladas Blancas (Naranja) y Días Seguros (Verde)</sup>")
    
    fig.update_traces(xgap=2, ygap=2, hovertemplate="Región: %{y}<br>Día: %{x}<br>Tipo: %{customdata}<extra></extra>", customdata=hover_txt)
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-45)
    return fig


# P5: Proyección de Calidad y Rendimiento (Boxplot)
def plot_calidad_vs_penalizacion(df: pd.DataFrame):
    if df.empty: return go.Figure()
    
    if 'es_proyeccion' in df.columns:
        df = df[df['es_proyeccion'] == True].copy()
    
    # Invertir la penalización para mostrar un "Índice de Calidad" del 0 al 100% como en tu imagen
    if 'penalizacion_rendimiento_pct' in df.columns:
        df['Indice_Calidad'] = 100 - df['penalizacion_rendimiento_pct']
    else:
        df['Indice_Calidad'] = 100

    fig = px.box(df, x='region', y='Indice_Calidad', color='calidad_estimada_fruto',
                 title="P5: Proyección de Calidad y Rendimiento del Fruto a 14 Días<br><sup>Distribución estimada del rendimiento por región (16/08 al 30/08)</sup>",
                 labels={'region': 'Región', 'Indice_Calidad': 'Índice Estilizado de Calidad (%)', 'calidad_estimada_fruto': 'Categoría Calidad'},
                 color_discrete_map={'Premium': '#4CAF50', 'Estándar': '#FF9800', 'Premium (Exportación)': '#4CAF50', 'Estándar (Mercado Local)': '#FF9800'},
                 points='all')
    
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(plot_bgcolor="rgba(240,240,240,0.4)", 
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                      xaxis_tickangle=-45)
    fig.update_yaxes(showgrid=True, gridcolor='white')
    fig.update_xaxes(showgrid=True, gridcolor='white')
    return fig