import streamlit as st
import pandas as pd
import folium
from folium.plugins import FloatImage
from streamlit_folium import st_folium

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Unidades Médicas OOAD Oaxaca IMSS")
st.title("Unidades Médicas en el OOAD Oaxaca IMSS")

@st.cache_data
def cargar_datos():
    # Leer el catálogo y filtrar Oaxaca con coordenadas válidas
    df = pd.read_excel('CLUES_IMSS.xlsx')
    df_oax = df[(df['ENTIDAD'] == 'OAXACA') & (df['LATITUD'].notna()) & (df['LONGITUD'].notna())].copy()
    return df_oax

df_oax = cargar_datos()

# 2. Lógica de selección múltiple (n cantidad de unidades)
# Las 5 unidades Amuzgo identificadas en amarillo por defecto
clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_oax[df_oax['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

st.sidebar.header("Panel de Control")
unidades_seleccionadas = st.sidebar.multiselect(
    "Selecciona las unidades médicas a resaltar en el mapa:",
    options=df_oax['NOMBRE DE LA UNIDAD'].unique(),
    default=nombres_amuzgo
)

# 3. Creación del mapa base centrado en el estado de Oaxaca
mapa = folium.Map(location=[17.0, -96.5], zoom_start=7, tiles='CartoDB positron')

# Agregar el logo institucional del IMSS en la esquina inferior izquierda
logo_url = "https://upload.wikimedia.org/wikipedia/commons/4/43/IMSS_Logo.png"
FloatImage(logo_url, bottom=3, left=3).add_to(mapa)

# 4. Procesamiento e iteración de las unidades médicas
for idx, row in df_oax.iterrows():
    lat = row['LATITUD']
    lon = row['LONGITUD']
    nombre = row['NOMBRE DE LA UNIDAD']
    tipo = row['NOMBRE DE TIPOLOGIA']
    
    # Datos a desplegar al pasar el mouse
    tooltip_text = f"<b>{nombre}</b><br>Tipo: {tipo}<br>Municipio: {row['MUNICIPIO']}"
    
    if nombre in unidades_seleccionadas:
        # Unidades resaltadas (Marcador distintivo)
        folium.Marker(
            location=[lat, lon],
            tooltip=tooltip_text,
            icon=folium.Icon(color='orange', icon='star', prefix='fa')
        ).add_to(mapa)
    else:
        # Clasificación para el resto de las unidades
        if 'HOSPITAL' in tipo:
            # Hospitales
            folium.Marker(
                location=[lat, lon],
                tooltip=tooltip_text,
                icon=folium.Icon(color='red', icon='h-square', prefix='fa')
            ).add_to(mapa)
        elif 'FAMILIAR' in tipo or 'CLINICA' in tipo:
            # UMF (Clínicas)
            folium.Marker(
                location=[lat, lon],
                tooltip=tooltip_text,
                icon=folium.Icon(color='blue', icon='medkit', prefix='fa')
            ).add_to(mapa)
        elif 'RURAL' in tipo:
            # UMR (Puntos de colores)
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color='green',
                fill=True,
                fill_color='green',
                tooltip=tooltip_text
            ).add_to(mapa)

# 5. Renderizar el mapa en la aplicación
st_folium(mapa, width=1000, height=600)
st.caption("Instrucciones de exportación: Usa la función de impresión de tu navegador (Ctrl+P). Ajusta el formato a horizontal, elimina los márgenes y selecciona 'Guardar como PDF'.")