import streamlit as st
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CARGA SEGURA DE DATOS (SOLO SECRETS) ---
def cargar_ritmos_seguros():
    # Verificación estricta: Si no está en secrets, detiene la app.
    if "ritmos" not in st.secrets:
        st.error("⛔ BASE DE DATOS NO ENCONTRADA")
        st.info("Configura la sección [ritmos] en los Secrets de Streamlit Cloud.")
        st.stop() # Detiene la ejecución para no mostrar nada más
    return st.secrets["ritmos"]

# Cargamos la DB solo desde la nube
RITMOS_DB = cargar_ritmos_seguros()

# --- 3. ESTILOS CSS (MODO MONITOR OSCURO) ---
st.markdown("""
<style>
    /* Fondo negro clínico */
    .stApp { background-color: #000000; color: white; }

    /* Contenedor del Panel de Control (Gris Oscuro) */
    .control-box {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 20px;
    }

    /* Botón de Aplicar (Rojo Urgencias) */
    div.stButton > button:first-child {
        background-color: #d32f2f;
        color: white;
        height: 3em;
        font-size: 18px;
        font-weight: bold;
        border: none;
        width: 100%;
    }
    div.stButton > button:hover { background-color: #b71c1c; color: white; }

    /* Cajas de Valores del Monitor */
    .monitor-box {
        background-color: #000000;
        border-left: 6px solid;
        padding: 10px;
        margin-bottom: 8px;
    }
    
    /* Colores Específicos */
    .c-hr { border-color: #00ff00; color: #00ff00; }
    .c-spo2 { border-color: #ffff00; color: #ffff00; }
    .c-bp { border-color: #ff3333; color: #ff3333; }
    .c-rr { border-color: #00ffff; color: #00ffff; }

    /* Tipografía Digital */
    .val-big { font-family: 'Consolas', monospace; font-size: 75px; font-weight: bold; line-height: 0.9; }
    .lbl-small { font-size: 14px; opacity: 0.8; text-transform: uppercase; }

    /* Limpieza de interfaz */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 4. ESTADO DE LA SESIÓN ---
if "monitor" not in st.session_state:
    # Valores iniciales por defecto (fisiológicos)
    primero = list(RITMOS_DB.keys())[0]
    st.session_state.monitor = {
        "ritmo": primero,
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# --- 5. BARRA LATERAL (CONTROL DE VISIBILIDAD) ---
with st.sidebar:
    st.title("🎛️ Control Maestro")
    st.markdown("---")
    # Este switch permite ocultar el panel para que los alumnos solo vean el monitor
    mostrar_panel = st.toggle("🛠️ Mostrar Panel de Ajustes", value=True)
    
    st.markdown("Use este interruptor para ocultar los controles cuando proyecte la pantalla.")

# --- 6. PANEL DE CONTROL (AJUSTES RÁPIDOS) ---
# Solo se dibuja si el interruptor está activado
if mostrar_panel:
    st.markdown("<div class='control-box'><h3>⚡ Ajustes Rápidos</h3>", unsafe_allow_html=True)
    
    # 1. Selector de Ritmo (Cargado desde Secrets)
    sel_ritmo = st.selectbox("Seleccionar Ritmo (DII)", options=list(RITMOS_DB.keys()))
    
    # 2. Sliders de Signos Vitales
    c1, c2, c3 = st.columns(3)
    with c1:
        v_hr = st.slider("FC (lpm)", 0, 300, st.session_state.monitor["hr"])
        v_spo2 = st.slider("SpO2 (%)", 0, 100, st.session_state.monitor["spo2"])
    with c2:
        v_pas = st.slider("P. Sistólica", 0, 300, st.session_state.monitor["pas"])
        v_pad = st.slider("P. Diastólica", 0, 200, st.session_state.monitor["pad"])
    with c3:
        v_rr = st.slider("F. Respiratoria", 0, 60, st.session_state.monitor["rr"])
        v_vol = st.slider("Volumen Audio", 0.0, 1.0, st.session_state.monitor["vol"])

    # 3. Botón de Acción
    if st.button("APLICAR NUEVA CONFIGURACIÓN"):
        st.session_state.monitor = {
            "ritmo": sel_ritmo,
            "hr": v_hr, "spo2": v_spo2, 
            "pas": v_pas, "pad": v_pad, 
            "rr": v_rr, "vol": v_vol
        }
        st.rerun() # Recarga inmediata para mostrar cambios
        
    st.markdown("</div>", unsafe_allow_html=True)

# --- 7. VISUALIZACIÓN DEL MONITOR (SALIDA) ---
# Separador visual si el panel está abierto
if mostrar_panel:
    st.divider()

d = st.session_state.monitor
pam = int((d['pas'] + 2*d['pad']) / 3)

# Layout: Datos Numéricos (Izquierda) | Trazado ECG (Derecha)
col_mon_izq, col_mon_der = st.columns([1, 3])

with col_mon_izq:
    # Frecuencia Cardíaca
    st.markdown(f"""
    <div class="monitor-box c-hr">
        <div class="lbl-small">LPM</div>
        <div class="val-big">{d['hr']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Saturación
    st.markdown(f"""
    <div class="monitor-box c-spo2">
        <div class="lbl-small">SpO2 %</div>
        <div class="val-big">{d['spo2']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Presión Arterial
    st.markdown(f"""
    <div class="monitor-box c-bp">
        <div class="lbl-small">PANI mmHg (PAM {pam})</div>
        <div class="val-big" style="font-size: 55px;">{d['pas']}/{d['pad']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Respiración / CO2
    st.markdown(f"""
    <div class="monitor-box c-rr">
        <div class="lbl-small">RR rpm</div>
        <div class="val-big">{d['rr']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_mon_der:
    # Video desde URL Segura
    url = RITMOS_DB.get(d['ritmo'])
    
    if url:
        st.video(url, autoplay=True, loop=True)
    else:
        st.error(f"Error: URL no encontrada para {d['ritmo']}")

# --- 8. AUDIO SINTÉTICO (JS INJECTION) ---
if d['hr'] > 0 and d['vol'] > 0:
    intervalo_ms = (60 / d['hr']) * 1000
    
    # Script optimizado para mantener el ritmo constante
    js = f"""
    <script>
        var ac = new (window.AudioContext || window.webkitAudioContext)();
        function beep() {{
            if (ac.state === 'suspended') ac.resume();
            var osc = ac.createOscillator();
            var gn = ac.createGain();
            osc.connect(gn);
            gn.connect(ac.destination);
            osc.type = 'square';
            osc.frequency.value = 750;
            gn.gain.value = {d['vol']};
            osc.start();
            setTimeout(() => osc.stop(), 150);
        }}
        // Limpia timer anterior para evitar superposiciones
        if(window.sndTimer) clearInterval(window.sndTimer);
        window.sndTimer = setInterval(beep, {intervalo_ms});
    </script>
    """
    components.html(js, height=0, width=0)

