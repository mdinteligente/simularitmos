import streamlit as st
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    # INICIAMOS EXPANDIDO para que veas el panel apenas entras
    initial_sidebar_state="expanded" 
)

# --- 2. FUNCIONES DE UTILIDAD ---
def obtener_url_embed(url_original):
    """Transforma enlaces ScreenPal Watch -> Player para evitar errores."""
    if "screenpal.com/watch/" in url_original:
        video_id = url_original.split("/")[-1].strip()
        # Parámetros para limpiar la interfaz del video
        return f"https://screenpal.com/player/{video_id}?width=100%&height=100%&autoplay=1&controls=0&title=0"
    return url_original

def cargar_secretos():
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR DE CONFIGURACIÓN: Faltan 'credentials' o 'ritmos' en Secrets.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

# Cargamos configuración
CREDS, RITMOS_DB = cargar_secretos()

# --- 3. ESTILOS CSS (Adaptables) ---
st.markdown("""
<style>
    /* Ocultar elementos nativos de Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* ESTILOS DEL MONITOR (Solo activos en la vista principal) */
    .stApp {
        background-color: #000000;
        color: white;
        font-family: 'Consolas', 'Segoe UI', monospace;
    }

    /* ESTILOS DEL LOGIN (Caja blanca flotante) */
    .login-container {
        background-color: #f0f2f6;
        padding: 40px;
        border-radius: 10px;
        color: black;
        text-align: center;
        max-width: 500px;
        margin: 100px auto;
    }

    /* Cajas de Signos Vitales */
    .vital-box {
        background: #080808;
        padding: 10px;
        border-left: 6px solid;
        margin-bottom: 10px;
        position: relative;
    }
    .hr { border-color: #00ff00; color: #00ff00; }
    .spo2 { border-color: #ffff00; color: #ffff00; }
    .bp { border-color: #ff3333; color: #ff3333; }
    .rr { border-color: #00ffff; color: #00ffff; }

    .val-big { font-size: 65px; font-weight: bold; text-align: right; line-height: 1; text-shadow: 0 0 8px currentColor; }
    .lbl-small { font-size: 14px; opacity: 0.8; text-transform: uppercase; position: absolute; top: 5px; left: 10px; }
    
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE SESIÓN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# ==========================================
# FASE 1: LOGIN (SI NO ESTÁ AUTENTICADO)
# ==========================================
if not st.session_state.auth:
    # Forzamos un fondo diferente para el login mediante columnas vacías
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div class="login-container">
            <h2 style="color: #333;">🔐 Acceso Docente</h2>
            <p style="color: #666;">Simulador de Signos Vitales</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario nativo de Streamlit
        with st.form("login_form"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("INGRESAR", type="primary")
            
            if submitted:
                if user == CREDS["username"] and pwd == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# ==========================================
# FASE 2: SIMULADOR (SI ESTÁ AUTENTICADO)
# ==========================================
else:
    # --- BARRA LATERAL (PANEL DE CONTROL DOCENTE) ---
    with st.sidebar:
        st.title("🎛️ Configuración")
        st.caption("Ajusta y pulsa 'Aplicar' para actualizar el monitor.")
        
        # Formulario para evitar recargas constantes
        with st.form("panel_docente"):
            sel_ritmo = st.selectbox("Ritmo Cardíaco", list(RITMOS_DB.keys()))
            st.divider()
            
            p = st.session_state.params
            v_hr = st.slider("FC (lpm)", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            
            v_rr = st.slider("FR (rpm)", 0, 60, p["rr"])
            v_vol = st.slider("Volumen Audio", 0.0, 1.0, p["vol"])
            
            # BOTÓN DE APLICAR
            aplicar = st.form_submit_button("🚀 ACTUALIZAR MONITOR", type="primary")

        if aplicar:
            st.session_state.params = {
                "ritmo": sel_ritmo,
                "hr": v_hr, "spo2": v_spo2,
                "pas": v_pas, "pad": v_pad,
                "rr": v_rr, "vol": v_vol
            }
            st.rerun()
        
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- PANTALLA PRINCIPAL (MONITOR ESTUDIANTE) ---
    d = st.session_state.params
    pam = int((d['pas'] + 2*d['pad']) / 3)

    col_izq, col_der = st.columns([1, 3.5])

    with col_izq:
        # Panel de Números (Izquierda)
        st.markdown(f"""
        <div class="vital-box hr"><div class="lbl-small">FC</div><div class="val-big">{d['hr']}</div></div>
        <div class="vital-box spo2"><div class="lbl-small">SpO2</div><div class="val-big">{d['spo2']}</div></div>
        <div class="vital-box bp"><div class="lbl-small">PANI (PAM {pam})</div><div class="val-big" style="font-size:50px">{d['pas']}/{d['pad']}</div></div>
        <div class="vital-box rr"><div class="lbl-small">RR</div><div class="val-big">{d['rr']}</div></div>
        """, unsafe_allow_html=True)

    with col_der:
        # Video Incrustado (Derecha) - Solución Iframe
        url_raw = RITMOS_DB.get(d['ritmo'])
        if url_raw:
            url_embed = obtener_url_embed(url_raw)
            components.html(
                f"""
                <body style="margin:0; background:black; overflow:hidden;">
                    <iframe src="{url_embed}" width="100%" height="650" frameborder="0" allow="autoplay"></iframe>
                </body>
                """,
                height=650
            )
        else:
            st.error("Video no encontrado")

    # --- AUDIO JS ---
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
