import streamlit as st
import pandas as pd
import plotly.express as px

# Cargar el archivo de Excel
df = pd.read_excel("Tecnicos.xlsx")

# Convertir columnas relevantes a texto
df["Temporada"] = df["Temporada"].astype(str)
df["Liga"] = df["Liga"].astype(str)
df["Equipo"] = df["Equipo"].astype(str)

# Reemplazar NaN por "Desconocido" en la columna 'Técnico'
df["Técnico"] = df["Técnico"].fillna("Otros")

df["Técnico"] = df["Técnico"].astype(str)

# Título de la aplicación
st.title("Comparación de Técnicos por Métricas")

# Crear filtros en la barra lateral con checkboxes
with st.sidebar:
    st.header("Filtros")

    # Filtro por Temporada
    st.subheader("Temporada")
    temporada_options = sorted(df["Temporada"].unique())
    seleccion_todas_temporadas = st.checkbox("Seleccionar Todas (Temporada)", value=True)
    temporadas_seleccionadas = [t for t in temporada_options if seleccion_todas_temporadas or st.checkbox(t, key=f"temp_{t}")]

    # Filtro por Liga
    st.subheader("Liga")
    liga_options = sorted(df["Liga"].unique())
    seleccion_todas_ligas = st.checkbox("Seleccionar Todas (Liga)", value=True)
    ligas_seleccionadas = [l for l in liga_options if seleccion_todas_ligas or st.checkbox(l, key=f"liga_{l}")]

    # Filtro por Equipo con opción colapsable
    st.subheader("Equipo")
    seleccion_todos_equipos = st.checkbox("Seleccionar Todos (Equipo)", value=True)
    equipos_seleccionados = sorted(df["Equipo"].unique()) if seleccion_todos_equipos else []

    if not seleccion_todos_equipos:
        with st.expander("Seleccionar Equipos Individualmente"):
            for equipo in sorted(df["Equipo"].unique()):
                if st.checkbox(equipo, key=f"equipo_{equipo}"):
                    equipos_seleccionados.append(equipo)

    # Filtro por Técnico
    st.subheader("Técnico")
    seleccion_todos_tecnicos = st.checkbox("Seleccionar Todos (Técnico)", value=True)
    tecnicos_seleccionados = [t for t in sorted(df["Técnico"].unique()) if seleccion_todos_tecnicos or st.checkbox(t, key=f"tecnico_{t}")]

# Aplicar los filtros
df_filtrado = df[
    (df["Temporada"].isin(temporadas_seleccionadas)) &
    (df["Liga"].isin(ligas_seleccionadas)) &
    (df["Equipo"].isin(equipos_seleccionados)) &
    (df["Técnico"].isin(tecnicos_seleccionados))
]

# Verificar si hay datos después del filtrado
if df_filtrado.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
else:
    # Omitir la métrica "Games"
    metricas = df_filtrado.select_dtypes(include=["number"]).columns.drop("Games", errors="ignore")

    if len(metricas) == 0:
        st.error("No hay métricas numéricas disponibles.")
    else:
        # Agrupar por técnico y calcular promedio
        radar_data = df_filtrado.groupby("Técnico")[metricas].mean().reset_index()

        # Transformar datos para gráfico de radar
        radar_melted = radar_data.melt(id_vars="Técnico", var_name="Métrica", value_name="Valor")

        # Asignación de colores a técnicos específicos con mayor transparencia
        color_map = {
            "Anselmi": "rgba(0, 51, 102, 0.5)",  # Azul marino con 50% de opacidad
            "JCO": "rgba(255, 0, 0, 0.5)",      # Rojo con 50% de opacidad
        }

        # Para los demás técnicos, asignar un color aleatorio de la paleta
        colores_restantes = [
            "rgba(255, 255, 0, 0.5)",  # Amarillo con 50% de opacidad
            "rgba(255, 165, 0, 0.5)",  # Naranja con 50% de opacidad
            "rgba(128, 0, 128, 0.5)",  # Morado con 50% de opacidad
            "rgba(0, 255, 255, 0.5)",  # Cian con 50% de opacidad
            "rgba(255, 105, 180, 0.5)",  # Rosa con 50% de opacidad
            "rgba(255, 140, 0, 0.5)",  # Naranja oscuro con 50% de opacidad
            "rgba(0, 128, 128, 0.5)"   # Verde azulado con 50% de opacidad
        ]

        # Completar color_map para técnicos que no sean Anselmi ni JCO
        for i, tecnico in enumerate(radar_data["Técnico"]):
            if tecnico not in color_map:
                color_map[tecnico] = colores_restantes[i % len(colores_restantes)]

        # Crear figura en Plotly con colores específicos y configurar hovertemplate
        fig = px.line_polar(
            radar_melted,
            r="Valor",
            theta="Métrica",
            color="Técnico",
            line_close=True,
            color_discrete_map=color_map
        )

        # Personalizar los tooltips (hovertemplate) para mostrar la métrica y el valor
        for trace in fig.data:
            trace.update(
                hovertemplate="<b>Técnico:</b> %{customdata[0]}<br>" +
                              "<b>Métrica:</b> %{theta}<br>" +
                              "<b>Valor:</b> %{r}<br>" +
                              "<extra></extra>",  # Esto elimina información extra no deseada
                customdata=radar_melted[['Técnico']].values  # Incluir el nombre del técnico
            )
            # Aplicar estilo similar al que mencionaste, con color y transparencia
            trace.update(
                line=dict(color=color_map[trace.name], width=2),  # Color sólido de la línea
                fill="toself",  # Relleno del área
                fillcolor=color_map[trace.name]  # Color de relleno con transparencia (rgba)
            )

        # Configurar título del gráfico
        fig.update_layout(title="Comparación de Técnicos por Métricas")

        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
