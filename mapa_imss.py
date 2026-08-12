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
    2. **Filtro de Unidades (Independiente):** Activa o desactiva las casillas para mostrar u ocultar Hospitales, UMF o UMR de la red global.
    3. **Unidades Prioritarias (Siempre visibles):** Puedes escribir o seleccionar clínicas para destacar con un marcador especial y nombre permanente. **Nota:** Las unidades que selecciones aquí *siempre* se mostrarán en el mapa con su diseño destacado, incluso si desactivaste su categoría en el filtro de arriba.
    4. **Navegación:** Usa la rueda del ratón para hacer Zoom y haz clic sostenido para desplazarte. Al pasar el puntero sobre cualquier punto, verás los detalles.
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

# Selector de mapa de fondo 
estilo_mapa = st.sidebar.selectbox(
    "1. Estilo geográfico del mapa:",
    ["Calles y Caminos", "Satélite (Tipo Google Maps)", "Mapa Claro (Sencillo)"]
)

st.sidebar.markdown("---")

# Filtros por tipo de unidad
tipos_disponibles = df_oax['TIPO_SIMPLIFICADO'].unique().tolist()
tipos_seleccionados = st.sidebar.multiselect(
    "2. ¿Qué unidades deseas visualizar en el mapa general?",
    options=tipos_disponibles,
    default=tipos_disponibles
)

# Selector de unidades a resaltar (Por defecto el Plan Amuzgo)
clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_oax[df_oax['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

# AHORA EL SELECTOR TOMA TODA LA BASE (df_oax), NO LA FILTRADA
unidades_resaltadas = st.sidebar.multiselect(
    "3. Unidades prioritarias a destacar (Nombres Visibles y siempre activas):",
    options=df_oax['NOMBRE DE LA UNIDAD'].unique(),
    default=nombres_amuzgo
)

# LÓGICA DE FILTRADO INDEPENDIENTE:
# Mostrar unidad SI (Su tipo está seleccionado) O SI (Está en la lista de resaltadas)
condicion_mostrar = (df_oax['TIPO_SIMPLIFICADO'].isin(tipos_seleccionados)) | (df_oax['NOMBRE DE LA UNIDAD'].isin(unidades_resaltadas))
df_a_dibujar = df_oax[condicion_mostrar]

st.sidebar.markdown("---")

# --- SIMBOLOGÍA VISUAL EN EL PANEL LATERAL (Corregida para que coincida exactamente) ---
st.sidebar.subheader("📌 Simbología del Mapa")

estilo_pin = """
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 30px;
    border-radius: 50% 50% 50% 0;
    transform: rotate(-45deg);
    margin-right: 15px;
    margin-left: 5px;
    color: white;
    font-size: 12px;
    box-shadow: -1px 1px 3px rgba(0,0,0,0.5);
"""
estilo_icono_interior = "transform: rotate(45deg); font-family: sans-serif; font-weight: bold;"

st.sidebar.markdown(f"""
<div style="font-size: 15px; line-height: 2.5; display: flex; flex-direction: column; gap: 8px;">
    
    <!-- Hospitales (Pin Rojo con H) -->
    <div style="display: flex; align-items: center;">
        <div style="{estilo_pin} background-color: #d33d2a;">
            <span style="{estilo_icono_interior}">H</span>
        </div>
        <span>Hospitales</span>
    </div>

    <!-- UMF (Pin Azul con Cruz) -->
    <div style="display: flex; align-items: center;">
        <div style="{estilo_pin} background-color: #38aadd;">
            <span style="{estilo_icono_interior}">+</span>
        </div>
        <span>UMF (Clínicas)</span>
    </div>

    <!-- UMR (Punto Verde) -->
    <div style="display: flex; align-items: center;">
        <div style="
            width: 12px; height: 12px; 
            border-radius: 50%; 
            background-color: #2c7c54; 
            border: 2px solid #2c7c54;
            margin-left: 10px; margin-right: 22px;">
        </div>
        <span>UMR (Rurales)</span>
    </div>

    <!-- Prioritarias (Pin Verde Oscuro con Estrella) -->
    <div style="display: flex; align-items: center;">
        <div style="{estilo_pin} background-color: #006400;">
            <span style="{estilo_icono_interior}">★</span>
        </div>
        <b>Unidades Destacadas</b>
    </div>
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

# Iterar el dataframe combinado y dibujar
for idx, row in df_a_dibujar.iterrows():
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
        
        # 2. Etiqueta de Texto Permanente (Movida a la IZQUIERDA)
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
                /* calc(-100% - 15px) mueve la caja totalmente a la izquierda del pin */
                transform: translate(calc(-100% - 15px), -15px); 
            ">
                {nombre}
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=etiqueta_html)
        ).add_to(mapa)

    else:
        # Iconos normales (solo se dibujan si pasaron el filtro general)
        if tipo_simp == 'Hospitales':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='red', icon='h-square', prefix='fa') # Folium usa 'red' (rojo) y FontAwesome 'h-square' (H en cuadro)
            ).add_to(mapa)
        elif tipo_simp == 'UMF (Clínicas)':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='blue', icon='medkit', prefix='fa') # Folium usa 'blue' (azul) y FontAwesome 'medkit' (cruz)
            ).add_to(mapa)
        elif tipo_simp == 'UMR (Rurales)':
            folium.CircleMarker(
                location=[lat, lon], radius=4, color='#2c7c54', fill=True, fill_opacity=0.8, tooltip=tooltip_text
            ).add_to(mapa)

# Renderizado final adaptativo al ancho de la pantalla
st_folium(mapa, width="100%", height=700)
