import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Función para cargar los datos con caché
def cargar_datos():
    return pd.read_excel("Consolidado.xlsx")

# Cargar el archivo de Excel con caché
@st.cache_data
def get_data():
    return cargar_datos()

df = get_data()

# Código para actualizar datos (desactivado para futuro uso)
# if st.button("Actualizar Datos"):
#     st.cache_data.clear()
#     st.rerun()

# Convertir columnas relevantes a texto
df["Temporada"] = df["Temporada"].astype(str)
df["Liga"] = df["Liga"].astype(str)
df["Equipo"] = df["Equipo"].astype(str)

# Reemplazar NaN por "Otros" en la columna 'Técnico'
df["Técnico"] = df["Técnico"].fillna("Otros").astype(str)

# Crear una columna combinada de Equipo + Temporada
df["Equipo_Temporada"] = df["Equipo"] + " " + df["Temporada"]

# Título de la aplicación
st.title("Comparación de Equipos por Métricas")

# Crear filtros en la barra lateral
with st.sidebar:
    st.header("Filtros")
    
    # Filtro por Temporada dentro de su propio expander
    with st.expander("Temporada", expanded=True):
        temporada_options = sorted(df["Temporada"].unique())
        # Lista de temporadas que se desean DESDELECCIONAR por defecto
        temporadas_deseleccionadas = [
            "2019/2020HC",
            "2020/2021HC",
            "2021/2022AK",
            "2021HC",
            "2022/2023AK",
            "2022/2023JL",
            "2024/2025JL"
        ]
        seleccion_todas_temporadas = st.checkbox("Seleccionar Todas (Temporada)", value=False)
        temporadas_seleccionadas = [
            t for t in temporada_options
            if seleccion_todas_temporadas or st.checkbox(t, key=f"temp_{t}", value=(t not in temporadas_deseleccionadas))
        ]
    
    # Filtro por Liga dentro de su propio expander
    with st.expander("Liga", expanded=True):
        liga_options = sorted(df["Liga"].unique())
        seleccion_todas_ligas = st.checkbox("Seleccionar Todas (Liga)", value=True)
        ligas_seleccionadas = [
            l for l in liga_options
            if seleccion_todas_ligas or st.checkbox(l, key=f"liga_{l}")
        ]
    
    # Sección de equipos (sin cambios)
    st.subheader("Equipo (Máximo 5 seleccionados)")
    equipos_disponibles = sorted(df["Equipo_Temporada"].unique())
    
    # Botón "Borrar todos los equipos seleccionados"
    if st.button("Borrar todos los equipos seleccionados"):
        for equipo in equipos_disponibles:
            key = f"equipo_{equipo}"
            if key in st.session_state:
                st.session_state[key] = False
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        elif hasattr(st, "rerun"):
            st.rerun()
    
    # Para llevar la cuenta de los equipos únicos ya seleccionados (sin la temporada)
    unique_selecciones = set()
    for equipo_temp in equipos_disponibles:
        key = f"equipo_{equipo_temp}"
        if st.session_state.get(key, False):
            team = equipo_temp.rsplit(" ", 1)[0]
            unique_selecciones.add(team)
    
    equipos_seleccionados = []
    with st.expander("Seleccionar Equipos Individualmente"):
        # --- MODIFICACIÓN ÚNICAMENTE EN EL SEARCHBOX ---
        search_text = st.text_input("Buscar equipo", key="search_equipo")
        # Siempre incluir los equipos ya seleccionados, aunque no cumplan el criterio de búsqueda
        seleccionados = [e for e in equipos_disponibles if st.session_state.get(f"equipo_{e}", False)]
        if search_text:
            equipos_filtrados = [e for e in equipos_disponibles if search_text.lower() in e.lower()]
            # Unir los seleccionados y los filtrados, preservando el orden y evitando duplicados
            equipos_filtrados = list(dict.fromkeys(seleccionados + equipos_filtrados))
        else:
            equipos_filtrados = equipos_disponibles
        # --- FIN MODIFICACIÓN ---
        
        # Iterar sobre la lista filtrada y mostrar cada checkbox
        for equipo_temp in equipos_filtrados:
            key = f"equipo_{equipo_temp}"
            team = equipo_temp.rsplit(" ", 1)[0]
            # Si el equipo no está ya seleccionado y ya se tienen 5 equipos únicos, se deshabilita
            disabled = False
            if team not in unique_selecciones and len(unique_selecciones) >= 5:
                disabled = True
            if st.checkbox(equipo_temp, key=key, disabled=disabled):
                equipos_seleccionados.append(equipo_temp)
                unique_selecciones.add(team)
    
    # Opción para activar/desactivar normalización (sin cambios)
    normalizar_datos = st.checkbox("Normalizar métricas", value=True)

# Filtrar datos para la normalización (basado en liga y temporada, no en equipo)
df_normalizacion = df[
    (df["Temporada"].isin(temporadas_seleccionadas)) &
    (df["Liga"].isin(ligas_seleccionadas))
]

# Filtrar datos finales según los equipos seleccionados (usando Equipo_Temporada)
df_filtrado = df[df["Equipo_Temporada"].isin(equipos_seleccionados)].copy()

# Verificar si hay datos después del filtrado
if df_filtrado.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
else:
    # Omitir la métrica "Games" si existe
    metricas = df_filtrado.select_dtypes(include=["number"]).columns.drop("Games", errors="ignore")
    
    if len(metricas) == 0:
        st.error("No hay métricas numéricas disponibles.")
    else:
        # Extraer solo el nombre del equipo (sin la temporada) para el gráfico
        df_filtrado["Equipo"] = df_filtrado["Equipo_Temporada"].apply(lambda x: x.rsplit(" ", 1)[0])
        
        # Reordenar las métricas según el orden especificado
        orden_metricas = [
            "NP xG",
            "Shots",
            "Successful Box Cross%",
            "Directness",
            "Deep Progressions",
            "Possession%",
            "OBV",
            "Pressures F2%",
            "Counterpressures F2%",
            "NP xG Conceded",
            "Shots Conceded",
            "Deep Progressions Conceded",
            "PPDA",
            "Defensive Distance"
        ]
        metricas = [m for m in orden_metricas if m in metricas]
        
        radar_data = df_filtrado.groupby("Equipo")[metricas].mean().reset_index()
        
        if normalizar_datos:
            # Calcular valores min y max basados en las ligas y temporadas seleccionadas
            min_values = df_normalizacion[metricas].min()
            max_values = df_normalizacion[metricas].max()
            
            # Aplicar normalización Min-Max
            radar_data[metricas] = (radar_data[metricas] - min_values) / (max_values - min_values)
            radar_data[metricas] = radar_data[metricas].fillna(0)  # Manejo de posibles divisiones por cero
            
            # Aplicar clip para asegurar que los valores se mantengan en el rango [0, 1]
            radar_data[metricas] = radar_data[metricas].clip(0, 1)
        
        # Configurar colores para los equipos (manteniendo la lógica original)
        # Se modifica el orden para que el primer color sea naranja y el segundo azul, luego los demás
        colores_restantes = [
            "rgba(255, 165, 0, 0.5)",  # Naranja
            "rgba(0, 51, 102, 0.5)",   # Azul oscuro (equivalente a #003366)
            "rgba(164, 91, 2, 0.5)",   # Naranja oscuro
            "rgba(0, 128, 128, 0.5)",  # Verde azulado
            "rgba(255, 255, 0, 0.5)",  # Amarillo
            "rgba(128, 0, 128, 0.5)",  # Morado
            "rgba(0, 255, 255, 0.5)",  # Cian
            "rgba(255, 105, 180, 0.5)" # Rosa
        ]
        
        color_map = {equipo: colores_restantes[i % len(colores_restantes)] for i, equipo in enumerate(radar_data["Equipo"])}
        
        # Crear gráfico de radar
        fig = go.Figure()
        
        # Función auxiliar para ajustar el color: reducir alpha para fill y fijar contorno en alpha 1
        def ajustar_color(rgba_str, nuevo_alpha):
            # Se espera el formato "rgba(r, g, b, alpha)"
            partes = rgba_str.replace("rgba(", "").replace(")", "").split(",")
            r = partes[0].strip()
            g = partes[1].strip()
            b = partes[2].strip()
            return f"rgba({r}, {g}, {b}, {nuevo_alpha})"
        
        for equipo in radar_data["Equipo"]:
            equipo_data = radar_data[radar_data["Equipo"] == equipo]
            # Extraer el color original con alpha 0.5
            orig_color = color_map[equipo]
            # Nuevo color de relleno con mayor transparencia (alpha 0.25)
            fill_color = ajustar_color(orig_color, 0.25)
            # Color de la línea (contorno) con alpha 1
            line_color = ajustar_color(orig_color, 1)
            
            # Obtener los valores "r" y cerrar el polígono añadiendo el primer valor al final
            r_values = equipo_data[metricas].values.flatten()
            r_complete = np.append(r_values, r_values[0])
            # Cerrar también la secuencia de categorías ("theta") añadiendo el primer elemento al final
            theta_complete = list(metricas) + [metricas[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=r_complete,
                theta=theta_complete,
                mode="lines",  # O "lines+markers" si deseas ver los puntos
                fill='toself',
                name=equipo,
                fillcolor=fill_color,
                line=dict(color=line_color, width=2),
                hoveron="fills+points",  # Esto activa el hover sobre el relleno
                hoverinfo="all"  # Opcional, para asegurarte de que se muestre toda la información
            ))
                
        # Personalizar gráfico
        fig.update_layout(
            title="Comparación de Equipos por Métricas",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1.05] if normalizar_datos else [0, radar_data[metricas].max().max()]
                )
            ),
            showlegend=True
        )
        
        # Mostrar el gráfico
        st.plotly_chart(fig)
