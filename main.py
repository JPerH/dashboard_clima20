"""
Dashboard Analítico — Proyecto Final Clima
"""
import streamlit as st
import pandas as pd
import datetime
from src.data_processor import cargar_y_filtrar_datos
from src.visualizations import (
    plot_clima_general, 
    plot_ventana_fumigacion, 
    plot_riesgo_biologico, 
    plot_alertas_heladas, 
    plot_calidad_vs_penalizacion
)

st.set_page_config(
    page_title="AgroClima Analytics · Proyecto Final",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    with st.spinner("⏳ Analizando registros climáticos y agrícolas..."):
        df = cargar_y_filtrar_datos()

    if df.empty:
        st.stop()

    # ── Sidebar con filtros (UX) ──────────────────────────────────
    with st.sidebar:
        st.title("🎛️ Filtros de Análisis")
        st.caption("Filtra la información para tu campo")
        
        regiones_disponibles = sorted(df["region"].unique())
        regiones_sel = st.multiselect(
            "📍 Selecciona Región(es)",
            options=regiones_disponibles,
            default=regiones_disponibles[:2] if len(regiones_disponibles) > 1 else regiones_disponibles
        )
        
        anios_disponibles = sorted(df["anio"].unique(), reverse=True)
        anios_sel = st.multiselect(
            "📅 Selecciona Año(s)",
            options=anios_disponibles,
            default=anios_disponibles
        )
        
        st.divider()
        incluir_proyeccion = st.checkbox("🔮 Incluir proyección al 31 de Agosto", value=True)

        st.divider()
        st.caption("🎓 GRUPO 1 · Proyecto Final")

    # 1. Aplicar filtros de región y año
    df_filtrado = df[(df["region"].isin(regiones_sel)) & (df["anio"].isin(anios_sel))]

    # 2. Aplicar filtro de proyección
    if not incluir_proyeccion and "es_proyeccion" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["es_proyeccion"] == False]

    # ── Header principal y KPIs Generales ─────────────────────────
    st.markdown("## 🌾 Dashboard AgroClimático para Toma de Decisiones")
    
    if df_filtrado.empty:
        st.warning("⚠️ No hay datos para los filtros seleccionados.")
        st.stop()

    # ── SECCIÓN: PANORAMA ACTUAL Y PROYECCIÓN A 14 DÍAS ───────────
    if incluir_proyeccion and "es_proyeccion" in df_filtrado.columns:
        st.markdown("### 🔮 Proyección Operativa (17 Ago - 31 Ago)")
        st.caption("Resumen de alertas y condiciones esperadas para las próximas dos semanas.")
        
        # Filtramos solo los datos del futuro (proyectados)
        df_proy = df_filtrado[df_filtrado["es_proyeccion"] == True]
        
        if not df_proy.empty:
            # 1. KPIs
            p1, p2, p3, p4, p5 = st.columns(5)
            
            temp_proy = df_proy["temperature_2m"].mean()
            p1.metric("🌡️ Temp. Esperada", f"{temp_proy:.1f} °C")
            
            dias_optimos = len(df_proy[df_proy["ventana_fumigacion"] == "Óptima (Verde)"])
            p2.metric("🚜 Días para Fumigar", f"{dias_optimos} días", delta="Óptimos", delta_color="normal")
            
            dias_riesgo_bio = len(df_proy[df_proy["riesgo_biologico"] == "Riesgo Alto"])
            color_bio = "inverse" if dias_riesgo_bio > 0 else "normal"
            p3.metric("🐛 Días Riesgo Plagas", f"{dias_riesgo_bio} días", delta="Precaución", delta_color=color_bio)
            
            dias_helada = len(df_proy[df_proy["alerta_helada_tipo"].isin(["Helada Blanca", "Helada Negra"])])
            color_helada = "inverse" if dias_helada > 0 else "normal"
            p4.metric("❄️ Alertas de Helada", f"{dias_helada} días", delta="Peligro", delta_color=color_helada)
            
            # KPI Calidad Premium
            if "calidad_estimada_fruto" in df_proy.columns:
                dias_premium = len(df_proy[df_proy["calidad_estimada_fruto"] == "Premium"])
                p5.metric("🍎 Calidad Premium", f"{dias_premium} días", delta="Proyección de cosecha", delta_color="normal")
            else:
                p5.metric("📉 Merma Estimada", "0%", delta="Sin alertas", delta_color="normal")
            
            # 2. Tabla Operativa Diaria
            st.markdown("#### 📅 Detalle de Proyección Diaria")
            
            # REEMPLAZO: Cambiamos precipitación por relative_humidity_2m
            cols_tabla = [
                "fecha", "temperature_2m", "relative_humidity_2m", 
                "estres_hidrico", "ventana_fumigacion", 
                "riesgo_biologico", "alerta_helada_tipo", "calidad_estimada_fruto"
            ]
            
            # Filtramos solo las columnas que existan en el DataFrame para evitar errores
            cols_existentes = [c for c in cols_tabla if c in df_proy.columns]
            df_tabla = df_proy[cols_existentes].copy()
            
            # Formateamos la humedad relativa para que se vea limpia (1 decimal)
            if "relative_humidity_2m" in df_tabla.columns:
                df_tabla["relative_humidity_2m"] = df_tabla["relative_humidity_2m"].round(1)
            
            # Formatear fecha y renombrar columnas
            if 'fecha' in df_tabla.columns:
                df_tabla['fecha'] = df_tabla['fecha'].dt.strftime('%Y-%m-%d')
                
            nombres_amigables = {
                "fecha": "Fecha",
                "temperature_2m": "Temp. Prom. (°C)",
                "relative_humidity_2m": "Humedad Rel. (%)",
                "estres_hidrico": "Estado Hídrico",
                "ventana_fumigacion": "Fumigación",
                "riesgo_biologico": "Riesgo Plagas",
                "alerta_helada_tipo": "Heladas",
                "calidad_estimada_fruto": "Calidad Esperada"
            }
            df_tabla.rename(columns=nombres_amigables, inplace=True)
            
            # Mostrar dataframe
            st.dataframe(df_tabla, hide_index=True, use_container_width=True)

        else:
            st.info("No hay datos de proyección disponibles para esta región.")
            
        st.divider()

    # ── Tabs enfocados en el Análisis Histórico y Detallado ────────
    st.markdown("### 📊 Análisis Detallado (Histórico + Proyección)")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌡️ Clima Diario", 
        "🚜 Fumigación", 
        "🐛 Riesgos Biológicos", 
        "❄️ Heladas", 
        "📉 Rendimiento"
    ])

    with tab1:
        st.subheader("1. Monitoreo de Temperatura y Humedad")
        st.plotly_chart(plot_clima_general(df_filtrado), use_container_width=True)

    with tab2:
        st.subheader("2. Días óptimos para aplicación de agroquímicos")
        st.plotly_chart(plot_ventana_fumigacion(df_filtrado), use_container_width=True)

    with tab3:
        st.subheader("3. Días con condiciones propicias para plagas y hongos")
        st.plotly_chart(plot_riesgo_biologico(df_filtrado), use_container_width=True)

    with tab4:
        st.subheader("4. Monitoreo y Frecuencia de Heladas por Región")
        st.caption("Las heladas negras representan un congelamiento seco de alto riesgo para los tejidos del cultivo.")

        df_heladas_sel = df_filtrado[df_filtrado['alerta_helada_tipo'].isin(['Helada Blanca', 'Helada Negra'])]
        total_dias_analizados = len(df_filtrado)
        total_dias_helada = len(df_heladas_sel)
        
        prob_helada = (total_dias_helada / total_dias_analizados * 100) if total_dias_analizados > 0 else 0
        dias_helada_negra = len(df_filtrado[df_filtrado['alerta_helada_tipo'] == 'Helada Negra'])

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Días con Helada", f"{total_dias_helada} días")
        k2.metric("Frecuencia de Ocurrencia", f"{prob_helada:.1f}%")
        k3.metric("🚨 Días con Helada Negra (Alto Riesgo)", f"{dias_helada_negra} días", delta_color="inverse")

        st.divider()
        st.plotly_chart(plot_alertas_heladas(df_filtrado), use_container_width=True)

    with tab5:
        st.subheader("5. Proyección de Calidad y Penalizaciones Económicas")
        st.plotly_chart(plot_calidad_vs_penalizacion(df_filtrado), use_container_width=True)

if __name__ == "__main__":
    main()