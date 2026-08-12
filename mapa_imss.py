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
    3. **Unidades Prioritarias (Siempre visibles):** Puedes escribir o seleccionar clínicas para destacar con un marcador especial y nombre permanente. **Nota:** Las unidades que selecciones aquí *siempre* se mostrarán en el mapa con su diseño destacado.
    4. **Navegación:** Usa la rueda del ratón para hacer Zoom y haz clic sostenido para desplazarte.
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

tipos_disponibles = df_oax['TIPO_SIMPLIFICADO'].unique().tolist()
tipos_seleccionados = st.sidebar.multiselect(
    "2. ¿Qué unidades deseas visualizar en el mapa general?",
    options=tipos_disponibles,
    default=tipos_disponibles
)

clues_amuzgo = ['OCIMS001985', 'OCIMS002970', 'OCIMS003892', 'OCIMS004172', 'OCIMS004691']
nombres_amuzgo = df_oax[df_oax['CLUES'].isin(clues_amuzgo)]['NOMBRE DE LA UNIDAD'].tolist()

unidades_resaltadas = st.sidebar.multiselect(
    "3. Unidades prioritarias a destacar (Nombres Visibles y siempre activas):",
    options=df_oax['NOMBRE DE LA UNIDAD'].unique(),
    default=nombres_amuzgo
)

condicion_mostrar = (df_oax['TIPO_SIMPLIFICADO'].isin(tipos_seleccionados)) | (df_oax['NOMBRE DE LA UNIDAD'].isin(unidades_resaltadas))
df_a_dibujar = df_oax[condicion_mostrar]

st.sidebar.markdown("---")

# --- SIMBOLOGÍA VISUAL SEGURA ---
st.sidebar.subheader("📌 Simbología del Mapa")
st.sidebar.markdown("""
* 🏥 **Hospitales** (Pin Rojo con 'H')
* ✚ **UMF / Clínicas** (Pin Azul con '+')
* 🟢 **UMR / Rurales** (Puntos Verdes)
* ⭐ **Unidades Destacadas** (Pin Verde Oscuro)
""")

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

mapa = folium.Map(location=[16.8, -96.5], zoom_start=7, tiles=tiles, attr=attr)

for idx, row in df_a_dibujar.iterrows():
    lat = row['LATITUD']
    lon = row['LONGITUD']
    nombre = row['NOMBRE DE LA UNIDAD']
    tipo_simp = row['TIPO_SIMPLIFICADO']
    municipio = row['MUNICIPIO']
    
    tooltip_text = f"<b>{nombre}</b><br>Municipio: {municipio}<br>Tipo: {row['NOMBRE DE TIPOLOGIA']}"
    
    if nombre in unidades_resaltadas:
        # Marcador principal
        folium.Marker(
            location=[lat, lon],
            tooltip=tooltip_text + "<br><b>⭐ UNIDAD PRIORITARIA</b>",
            icon=folium.Icon(color='darkgreen', icon='star', prefix='fa'),
            z_index_offset=1000 
        ).add_to(mapa)
        
        # Etiqueta de texto (Posicionada DEBAJO y CENTRADA para que nunca se oculte)
        etiqueta_html = f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #005c2a;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 12px;
                font-weight: 900;
                color: #000000;
                white-space: nowrap;
                box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                transform: translate(-50%, 15px); /* Centra y baja */
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
                icon=folium.Icon(color='blue', icon='plus', prefix='fa') # Cambié a 'plus' para evitar cruces cortadas
            ).add_to(mapa)
        elif tipo_simp == 'UMR (Rurales)':
            folium.CircleMarker(
                location=[lat, lon], radius=4, color='#2c7c54', fill=True, fill_opacity=0.9, tooltip=tooltip_text
            ).add_to(mapa)

st_folium(mapa, width="100%", height=700)
