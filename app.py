import streamlit as st
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador SV",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed" # Inicia con el panel cerrado (Modo Monitor)
)

# --- 2. FUNCIÓN DE REPARACIÓN DE ENLACES (CRÍTICO) ---
def obtener_url_embed(url_original):
    """
    Convierte el enlace de 'Watch' (Página web) a 'Player' (Video incrustado)
    para que ScreenPal funcione dentro de la app sin bordes ni menús.
    """
    if "screenpal.com/watch/" in url_original:
        # Extraemos el ID del video (lo que está después de /watch/)
        video_id = url_original.split("/")[-1].strip()
        # Construimos la URL del reproductor puro
        return f"https://screenpal.com/player/{video_id}?width=100%&height=100%&autoplay=1&controls=0"
    return url_original

# --- 3. CARGA DE DATOS ---
def cargar_ritmos():
    if "ritmos" not in st.secrets:
        st.error("⛔ ERROR: No se detectaron ritmos en Secrets.")
        st.stop()
    return st.secrets["ritmos"]

RITMOS_DB = cargar_ritmos()

# --- 4. CSS: DISEÑO DE MONITOR MÉDICO ---
st.markdown("""
<style>
    /* Fondo Negro Clínico */
    .stApp { background-color: #000000; color: white; font-family: 'Consolas', 'Segoe UI', monospace; }
    
    /* Ocultar elementos de Streamlit que sobran */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* ESTILOS DE LA BARRA LATERAL (DOCENTE) */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #333;
    }
    
    /* ESTILOS DEL MONITOR (ESTUDIANTE) */
    .monitor-container {
        display: flex;
        gap: 10px;
        margin-top: -50px; /* Subir todo para aprovechar espacio */
    }
    
    /* Columna Izquierda: Números */
    .numbers-col {
        width: 25%;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    /* Columna Derecha: Video */
    .video-col {
        width: 75%;
        border: 2px solid #333;
        background: #000;
        height: 80vh; /* Altura del monitor */
        position: relative;
    }

    /* Cajas de Signos Vitales */
    .vital-box {
        background: #080808;
        padding: 10px;
        border-left: 8px solid;
        height: 18vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
    }

    /* Colores */
    .hr { border-color: #00ff00; color: #00ff00; }
    .spo2 { border-color: #ffff00; color: #ffff00; }
    .bp { border-color: #ff3333; color: #ff3333; }
    .rr { border-color: #00ffff; color: #00ffff; }

    /* Tipografía */
    .label { font-size: 14px; opacity: 0.7; text-transform: uppercase; position: absolute; top: 5px; left: 10px; }
    .value { font-size: 70px; font-weight: bold; text-align: right; line-height: 1; text-shadow: 0 0 10px currentColor; }
    .sub { font-size: 20px; text-align: right; opacity: 0.8; margin-top: -5px; }

</style>
""", unsafe_allow_html=True)

# --- 5. ESTADO DE LA SESIÓN ---
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# ==========================================
# ZONA 1: PANEL DE CONTROL DOCENTE (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("## 🎛️ Mando Docente")
    st.info("Oculta esta barra (❌) para mostrar solo el monitor.")
    
    # 1. Ritmo
    sel_ritmo = st.selectbox("Seleccionar Ritmo", list(RITMOS_DB.keys()))
    
    st.markdown("---")
    
    # 2. Signos Vitales (Sliders compactos)
    p = st.session_state.params
    v_hr = st.slider("FC (lpm)", 0, 300, p["hr"])
    v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
    
    c1, c2 = st.columns(2)
    with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
    with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
    
    v_rr = st.slider("FR (rpm)", 0, 60, p["rr"])
    v_vol = st.slider("🔈 Volumen", 0.0, 1.0, p["vol"])
    
    # Botón de actualización
    if st.button("🔴 APLICAR CAMBIOS", type="primary", use_container_width=True):
        st.session_state.params = {
            "ritmo": sel_ritmo,
            "hr": v_hr, "spo2": v_spo2,
            "pas": v_pas, "pad": v_pad,
            "rr": v_rr, "vol": v_vol
        }
        st.rerun()

# ==========================================
# ZONA 2: MONITOR ESTUDIANTE (MAIN)
# ==========================================

# Variables de renderizado
d = st.session_state.params
pam = int((d['pas'] + 2*d['pad']) / 3)

# Maquetación manual HTML/CSS para control total del diseño
c_izq, c_der = st.columns([1, 3.5])

with c_izq:
    # 1. FC
    st.markdown(f"""
    <div class="vital-box hr">
        <div class="label">FC / ECG</div>
        <div class="value">{d['hr']}</div>
        <div class="sub">lpm</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. SpO2
    st.markdown(f"""
    <div class="vital-box spo2">
        <div class="label">SpO2</div>
        <div class="value">{d['spo2']}</div>
        <div class="sub">%</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. PA
    st.markdown(f"""
    <div class="vital-box bp">
        <div class="label">PANI</div>
        <div class="value" style="font-size: 50px;">{d['pas']}/{d['pad']}</div>
        <div class="sub">PAM: {pam}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. RR
    st.markdown(f"""
    <div class="vital-box rr">
        <div class="label">RESP</div>
        <div class="value">{d['rr']}</div>
        <div class="sub">rpm</div>
    </div>
    """, unsafe_allow_html=True)

with c_der:
    # REPRODUCCIÓN DE VIDEO (IFRAME CORREGIDO)
    raw_url = RITMOS_DB.get(d['ritmo'])
    
    if raw_url:
        # Convertimos la URL de 'watch' a 'player' automáticamente
        embed_url = obtener_url_embed(raw_url)
        
        # Usamos iframe con CSS personalizado para quitar bordes
        components.html(
            f"""
            <body style="margin:0; padding:0; background-color:black; overflow:hidden;">
                <iframe src="{embed_url}" 
                        style="width:100%; height:100vh; border:none;" 
                        allow="autoplay; fullscreen"
                        scrolling="no">
                </iframe>
            </body>
            """,
            height=650, # Altura ajustada a la pantalla
            scrolling=False
        )
    else:
        st.error("Enlace no encontrado")

# --- AUDIO (JS) ---
if d['hr'] > 0 and d['vol'] > 0:
    intervalo = (60 / d['hr']) * 1000
    components.html(f"""
    <script>
    var ac = new (window.AudioContext || window.webkitAudioContext)();
    function beep() {{
        if (ac.state === 'suspended') ac.resume();
        var o=ac.createOscillator(); var g=ac.createGain();
        o.connect(g); g.connect(ac.destination);
        o.type='square'; o.frequency.value=750; g.gain.value={d['vol']};
        o.start(); setTimeout(()=>o.stop(),150);
    }}
    clearInterval(window.t); window.t = setInterval(beep, {intervalo});
    </script>
    """, height=0, width=0)
