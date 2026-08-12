import streamlit as st
import pandas as pd
import folium
from folium.plugins import FloatImage
from streamlit_folium import st_folium

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Mapa Interactivo IMSS Oaxaca")
st.title("Unidades Médicas en el OOAD Oaxaca IMSS")

@st.cache_data
def cargar_datos():
    # Leer el catálogo y filtrar Oaxaca
    df = pd.read_excel('CLUES_IMSS.xlsx')
    df_oax = df[(df['ENTIDAD'] == 'OAXACA') & (df['LATITUD'].notna()) & (df['LONGITUD'].notna())].copy()
    
    # Crear una categoría limpia para los filtros
    def simplificar_tipo(tipo):
        if 'HOSPITAL' in str(tipo): return 'Hospitales'
        elif 'FAMILIAR' in str(tipo) or 'CLINICA' in str(tipo): return 'UMF (Clínicas)'
        elif 'RURAL' in str(tipo): return 'UMR (Rurales)'
        else: return 'Otras'
    
    df_oax['TIPO_SIMPLIFICADO'] = df_oax['NOMBRE DE TIPOLOGIA'].apply(simplificar_tipo)
    return df_oax

df_oax = cargar_datos()

# --- PANEL DE CONTROL (MENÚ LATERAL) ---
st.sidebar.header("⚙️ Configuración Visual")

# Selector de mapa de fondo
estilo_mapa = st.sidebar.selectbox(
    "1. Estilo geográfico del mapa:",
    ["Mapa Claro (Sencillo)", "Satélite (Tipo Google Maps)", "Calles y Caminos"]
)

st.sidebar.markdown("---")

# Filtros por tipo de unidad
tipos_disponibles = df_oax['TIPO_SIMPLIFICADO'].unique().tolist()
tipos_seleccionados = st.sidebar.multiselect(
    "2. ¿Qué unidades deseas visualizar en el mapa?",
    options=tipos_disponibles,
    default=tipos_disponibles # Inicia mostrando todas
)

# Aplicar el filtro a la base de datos
df_filtrado = df_oax[df_oax['TIPO_SIMPLIFICADO'].isin(tipos_seleccionados)]

# Selector de unidades a resaltar (Por defecto el Plan Amuzgo)
clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_oax[df_oax['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

unidades_resaltadas = st.sidebar.multiselect(
    "3. Unidades prioritarias a destacar con logo IMSS:",
    options=df_filtrado['NOMBRE DE LA UNIDAD'].unique(),
    default=[u for u in nombres_amuzgo if u in df_filtrado['NOMBRE DE LA UNIDAD'].values]
)

# --- CONSTRUCCIÓN DEL MAPA ---
# Asignar la capa base seleccionada
if estilo_mapa == "Satélite (Tipo Google Maps)":
    tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
elif estilo_mapa == "Calles y Caminos":
    tiles = "OpenStreetMap"
    attr = None
else:
    tiles = "CartoDB positron"
    attr = None

mapa = folium.Map(location=[17.0, -96.5], zoom_start=7.5, tiles=tiles, attr=attr)

# Logo estático en la esquina
logo_url = "https://upload.wikimedia.org/wikipedia/commons/4/43/IMSS_Logo.png"
FloatImage(logo_url, bottom=3, left=3).add_to(mapa)

# Iterar el dataframe ya filtrado y dibujar
for idx, row in df_filtrado.iterrows():
    lat = row['LATITUD']
    lon = row['LONGITUD']
    nombre = row['NOMBRE DE LA UNIDAD']
    tipo_simp = row['TIPO_SIMPLIFICADO']
    municipio = row['MUNICIPIO']
    
    tooltip_text = f"<b>{nombre}</b><br>Municipio: {municipio}<br>Tipo: {row['NOMBRE DE TIPOLOGIA']}"
    
    if nombre in unidades_resaltadas:
        # Poner logo IMSS directo en la coordenada
        icono_imss = folium.features.CustomIcon(logo_url, icon_size=(45, 45))
        folium.Marker(
            location=[lat, lon],
            tooltip=tooltip_text + "<br><b>⭐ UNIDAD PLAN AMUZGO</b>",
            icon=icono_imss,
            z_index_offset=1000 # Lo mantiene sobre otras unidades
        ).add_to(mapa)
    else:
        # Iconos normales
        if tipo_simp == 'Hospitales':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='red', icon='h-square', prefix='fa')
            ).add_to(mapa)
        elif tipo_simp == 'UMF (Clínicas)':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='blue', icon='medkit', prefix='fa')
            ).add_to(mapa)
        elif tipo_simp == 'UMR (Rurales)':
            folium.CircleMarker(
                location=[lat, lon], radius=4, color='#2c7c54', fill=True, fill_opacity=0.8, tooltip=tooltip_text
            ).add_to(mapa)

# Renderizado final adaptativo al ancho de la pantalla
st_folium(mapa, width="100%", height=700)
