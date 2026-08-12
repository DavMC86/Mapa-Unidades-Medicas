import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Mapa Interactivo IMSS Oaxaca")
st.title("Unidades Médicas en el OOAD Oaxaca IMSS")

# --- MANUAL DE USUARIO DESPLEGABLE ---
with st.expander("ℹ️ Guía rápida de uso (Haz clic para expandir)"):
    st.markdown("""
    **¿Cómo utilizar esta herramienta?**
    1. **Estilo del Mapa:** Usa el panel lateral izquierdo para cambiar el fondo. La vista 'Satélite' es ideal para observar la geografía y orografía.
    2. **Filtro de Unidades:** Activa o desactiva las casillas para mostrar u ocultar Hospitales, UMF o UMR de la red global del estado.
    3. **Unidades Prioritarias:** Puedes escribir o seleccionar en el buscador las clínicas que deseas destacar con un marcador especial y nombre permanente. *Por defecto, están seleccionadas las 5 unidades en transición a UMU del Plan Amuzgo.*
    4. **Navegación:** Usa la rueda del ratón para hacer Zoom y haz clic sostenido para desplazarte por el mapa. Al pasar el puntero sobre cualquier punto, verás los detalles de esa unidad.
    """)

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

# Selector de mapa de fondo (Reordenado para que 'Calles y Caminos' sea el primero)
estilo_mapa = st.sidebar.selectbox(
    "1. Estilo geográfico del mapa:",
    ["Calles y Caminos", "Satélite (Tipo Google Maps)", "Mapa Claro (Sencillo)"]
)

st.sidebar.markdown("---")

# Filtros por tipo de unidad
tipos_disponibles = df_oax['TIPO_SIMPLIFICADO'].unique().tolist()
tipos_seleccionados = st.sidebar.multiselect(
    "2. ¿Qué unidades deseas visualizar en el mapa?",
    options=tipos_disponibles,
    default=tipos_disponibles
)

# Aplicar el filtro a la base de datos
df_filtrado = df_oax[df_oax['TIPO_SIMPLIFICADO'].isin(tipos_seleccionados)]

# Selector de unidades a resaltar (Por defecto el Plan Amuzgo)
clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_oax[df_oax['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

unidades_resaltadas = st.sidebar.multiselect(
    "3. Unidades prioritarias a destacar (Nombres Visibles):",
    options=df_filtrado['NOMBRE DE LA UNIDAD'].unique(),
    default=[u for u in nombres_amuzgo if u in df_filtrado['NOMBRE DE LA UNIDAD'].values]
)

st.sidebar.markdown("---")

# --- SIMBOLOGÍA VISUAL EN EL PANEL LATERAL ---
st.sidebar.subheader("📌 Simbología del Mapa")
st.sidebar.markdown("""
<div style="font-size: 14px; line-height: 2;">
    <span><b style="color: red; font-size: 18px;">⊞</b> Hospitales</span><br>
    <span><b style="color: blue; font-size: 18px;">➕</b> UMF (Clínicas)</span><br>
    <span><b style="color: #2c7c54; font-size: 18px;">●</b> UMR (Puntos Verdes)</span><br>
    <span><b style="color: darkgreen; font-size: 18px;">⭐</b> <b>Unidades Destacadas (Prioritarias)</b></span>
</div>
""", unsafe_allow_html=True)

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

# Iterar el dataframe ya filtrado y dibujar
for idx, row in df_filtrado.iterrows():
    lat = row['LATITUD']
    lon = row['LONGITUD']
    nombre = row['NOMBRE DE LA UNIDAD']
    tipo_simp = row['TIPO_SIMPLIFICADO']
    municipio = row['MUNICIPIO']
    
    tooltip_text = f"<b>{nombre}</b><br>Municipio: {municipio}<br>Tipo: {row['NOMBRE DE TIPOLOGIA']}"
    
    if nombre in unidades_resaltadas:
        # 1. Marcador principal (El Pin Verde con Estrella)
        folium.Marker(
            location=[lat, lon],
            tooltip=tooltip_text + "<br><b>⭐ UNIDAD PRIORITARIA</b>",
            icon=folium.Icon(color='darkgreen', icon='star', prefix='fa'),
            z_index_offset=1000 # Lo mantiene sobre otras unidades
        ).add_to(mapa)
        
        # 2. Etiqueta de Texto Permanente (DivIcon)
        etiqueta_html = f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.85);
                border: 2px solid #005c2a;
                border-radius: 5px;
                padding: 4px;
                font-size: 11px;
                font-weight: bold;
                color: #1a1a1a;
                white-space: nowrap;
                box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                transform: translate(-10px, -35px); /* Sube y mueve la etiqueta */
            ">
                {nombre}
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=etiqueta_html)
        ).add_to(mapa)

    else:
        # Iconos normales (los que no están resaltados)
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
