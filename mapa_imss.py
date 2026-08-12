import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Mapa Interactivo IMSS Oaxaca")
st.title("Unidades Médicas en el OOAD Oaxaca IMSS")

with st.expander("ℹ️ Guía rápida de uso"):
    st.markdown("""
    1. **Estilo del Mapa:** Cambia entre mapa de calles, satélite o vista limpia.
    2. **Filtros por Categoría:** Usa las casillas (checkbox) del panel izquierdo para prender o apagar todos los Hospitales, UMF o UMR.
    3. **Unidades Prioritarias:** Debajo de cada casilla, puedes buscar y seleccionar unidades específicas. Estas se mostrarán con una **estrella verde** y su nombre visible permanentemente, sin importar si apagaste su categoría general.
    """)

@st.cache_data
def cargar_datos():
    df = pd.read_excel('CLUES_IMSS.xlsx')
    df_oax = df[(df['ENTIDAD'] == 'OAXACA') & (df['LATITUD'].notna()) & (df['LONGITUD'].notna())].copy()
    
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

estilo_mapa = st.sidebar.selectbox(
    "1. Estilo geográfico del mapa:",
    ["Calles y Caminos", "Satélite (Tipo Google Maps)", "Mapa Claro (Sencillo)"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("**2. Filtros y Búsqueda por Tipo**")

# Inicializar listas vacías para las selecciones
unidades_resaltadas_totales = []
condiciones_mostrar = []

# --- SECCIÓN HOSPITALES ---
mostrar_hospitales = st.sidebar.checkbox("Mostrar todos los Hospitales", value=True)
df_hospitales = df_oax[df_oax['TIPO_SIMPLIFICADO'] == 'Hospitales']
resaltar_hosp = st.sidebar.multiselect(
    "Destacar Hospital(es):", 
    options=df_hospitales['NOMBRE DE LA UNIDAD'].unique(),
    placeholder="Busca un hospital..."
)
unidades_resaltadas_totales.extend(resaltar_hosp)
if mostrar_hospitales:
    condiciones_mostrar.append(df_oax['TIPO_SIMPLIFICADO'] == 'Hospitales')

st.sidebar.markdown("<br>", unsafe_allow_html=True) # Espaciador

# --- SECCIÓN UMF ---
mostrar_umf = st.sidebar.checkbox("Mostrar todas las UMF (Clínicas)", value=True)
df_umf = df_oax[df_oax['TIPO_SIMPLIFICADO'] == 'UMF (Clínicas)']
resaltar_umf = st.sidebar.multiselect(
    "Destacar UMF(s):", 
    options=df_umf['NOMBRE DE LA UNIDAD'].unique(),
    placeholder="Busca una clínica..."
)
unidades_resaltadas_totales.extend(resaltar_umf)
if mostrar_umf:
    condiciones_mostrar.append(df_oax['TIPO_SIMPLIFICADO'] == 'UMF (Clínicas)')

st.sidebar.markdown("<br>", unsafe_allow_html=True) # Espaciador

# --- SECCIÓN UMR ---
mostrar_umr = st.sidebar.checkbox("Mostrar todas las UMR (Rurales)", value=True)
df_umr = df_oax[df_oax['TIPO_SIMPLIFICADO'] == 'UMR (Rurales)']

# Precargar las del Plan Amuzgo
clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_umr[df_umr['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

resaltar_umr = st.sidebar.multiselect(
    "Destacar UMR(s):", 
    options=df_umr['NOMBRE DE LA UNIDAD'].unique(),
    default=nombres_amuzgo,
    placeholder="Busca una rural..."
)
unidades_resaltadas_totales.extend(resaltar_umr)
if mostrar_umr:
    condiciones_mostrar.append(df_oax['TIPO_SIMPLIFICADO'] == 'UMR (Rurales)')

# Consolidar lógica: Mostrar si está el checkbox activado OR si está en la lista de resaltadas
condicion_final = df_oax['NOMBRE DE LA UNIDAD'].isin(unidades_resaltadas_totales)
if condiciones_mostrar:
    from functools import reduce
    import operator
    condicion_categorias = reduce(operator.or_, condiciones_mostrar)
    condicion_final = condicion_final | condicion_categorias

df_a_dibujar = df_oax[condicion_final]

st.sidebar.markdown("---")

# --- SIMBOLOGÍA EXACTA CON IMÁGENES ---
st.sidebar.subheader("📌 Simbología del Mapa")
st.sidebar.markdown("""
<div style="font-size: 14px; display: flex; flex-direction: column; gap: 15px;">
    <div style="display: flex; align-items: center;">
        <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png" width="16" style="margin-right: 10px;">
        <span>Hospitales</span>
    </div>
    <div style="display: flex; align-items: center;">
        <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png" width="16" style="margin-right: 10px;">
        <span>UMF (Clínicas)</span>
    </div>
    <div style="display: flex; align-items: center;">
        <div style="width: 14px; height: 14px; border-radius: 50%; background-color: #2c7c54; margin-right: 12px; margin-left: 1px;"></div>
        <span>UMR (Puntos Verdes)</span>
    </div>
    <div style="display: flex; align-items: center;">
        <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png" width="16" style="margin-right: 10px;">
        <b>Unidades Destacadas</b>
    </div>
</div>
""", unsafe_allow_html=True)

# --- CONSTRUCCIÓN DEL MAPA ---
if estilo_mapa == "Satélite (Tipo Google Maps)":
    tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    attr = "Tiles &copy; Esri"
elif estilo_mapa == "Calles y Caminos":
    tiles = "OpenStreetMap"
    attr = None
else:
    tiles = "CartoDB positron"
    attr = None

mapa = folium.Map(location=[16.8, -96.5], zoom_start=7.5, tiles=tiles, attr=attr)

# Diccionario de desplazamientos manuales para evitar solapamientos en unidades específicas
desplazamientos = {
    "SANTA MARÍA IPALAPA": "translate(-50%, 15px)", # Centro Abajo
    "SAN PEDRO AMUZGOS": "translate(-50%, -45px)",  # Centro Arriba (lo aleja de Ipalapa)
    "SAN VICENTE PIÑAS": "translate(15px, -15px)",  # Derecha
    "SAN ANTONIO OCOTLÁN": "translate(-110%, -15px)", # Izquierda
}

for idx, row in df_a_dibujar.iterrows():
    lat = row['LATITUD']
    lon = row['LONGITUD']
    nombre = row['NOMBRE DE LA UNIDAD']
    tipo_simp = row['TIPO_SIMPLIFICADO']
    municipio = row['MUNICIPIO']
    
    tooltip_text = f"<b>{nombre}</b><br>Municipio: {municipio}<br>Tipo: {row['NOMBRE DE TIPOLOGIA']}"
    
    if nombre in unidades_resaltadas_totales:
        folium.Marker(
            location=[lat, lon],
            tooltip=tooltip_text + "<br><b>⭐ UNIDAD DESTACADA</b>",
            icon=folium.Icon(color='green', icon='star', prefix='fa'),
            z_index_offset=1000 
        ).add_to(mapa)
        
        # Asignar desplazamiento específico o el por defecto (centro-abajo)
        transformacion = desplazamientos.get(nombre, "translate(-50%, 15px)")
        
        etiqueta_html = f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #005c2a;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                font-weight: 800;
                color: #000;
                white-space: nowrap;
                box-shadow: 2px 2px 4px rgba(0,0,0,0.4);
                transform: {transformacion};
                display: inline-block;
            ">
                {nombre}
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=etiqueta_html)
        ).add_to(mapa)

    else:
        if tipo_simp == 'Hospitales':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='red', icon='h-square', prefix='fa')
            ).add_to(mapa)
        elif tipo_simp == 'UMF (Clínicas)':
            folium.Marker(
                location=[lat, lon], tooltip=tooltip_text,
                icon=folium.Icon(color='blue', icon='plus', prefix='fa') 
            ).add_to(mapa)
        elif tipo_simp == 'UMR (Rurales)':
            folium.CircleMarker(
                location=[lat, lon], radius=4, color='#2c7c54', fill=True, fill_opacity=0.9, tooltip=tooltip_text
            ).add_to(mapa)

st_folium(mapa, width="100%", height=700)
