import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN: PANEL ABIERTO AL INICIO ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded" # <--- ESTO OBLIGA A QUE EL PANEL SALGA ABIERTO
)

# --- 2. FUNCIONES Y SECRETOS ---
def obtener_url_embed(url_original):
    if "screenpal.com/watch/" in url_original:
        vid_id = url_original.split("/")[-1].strip()
        return f"https://screenpal.com/player/{vid_id}?width=100%&height=100%&autoplay=1&controls=0&title=0"
    return url_original

def get_secrets():
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR: Faltan Secrets.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

CREDS, RITMOS_DB = get_secrets()

# --- 3. ESTADO ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# ==============================================================================
# FASE 1: LOGIN (FONDO CLARO)
# ==============================================================================
if not st.session_state.auth:
    # CSS para limpiar la pantalla de Login
    st.markdown("""
    <style>
        .stApp { background-color: #f0f2f6; color: black; }
        header { visibility: hidden; } /* Ocultamos header solo en login */
        .login-card {
            background: white; padding: 40px; border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
            max-width: 400px; margin: 60px auto;
        }
        input { border: 1px solid #ddd !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card'><h2>🏥 Control Docente</h2></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", type="primary", use_container_width=True):
                if u == CREDS["username"] and p == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Error de acceso")

# ==============================================================================
# FASE 2: PANEL DOCENTE + MONITOR (FONDO OSCURO)
# ==============================================================================
else:
    # CSS PARA EL MODO SIMULACIÓN
    st.markdown("""
    <style>
        /* 1. FONDO NEGRO GLOBAL */
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* 2. PANEL LATERAL (DOCENTE) - GRIS OSCURO */
        section[data-testid="stSidebar"] {
            background-color: #262730; /* Gris visible */
            border-right: 1px solid #444;
        }
        
        /* 3. BOTÓN PARA ABRIR EL PANEL (>): SIEMPRE VISIBLE Y BLANCO */
        [data-testid="stSidebarCollapsedControl"] {
            color: white !important;
            background-color: #333 !important;
            display: block !important;
            visibility: visible !important;
            top: 10px; left: 10px;
            z-index: 9999999; /* Por encima de todo */
        }
        
        /* 4. CAJAS DEL MONITOR */
        .vital-box {
            background: #080808; border-left: 6px solid;
            padding: 5px 15px; margin-bottom: 8px; height: 16vh;
            display: flex; flex-direction: column; justify-content: center;
        }
        .hr { border-color: #00ff00; color: #00ff00; }
        .spo2 { border-color: #ffff00; color: #ffff00; }
        .bp { border-color: #ff3333; color: #ff3333; }
        .rr { border-color: #00ffff; color: #00ffff; }
        
        .val { font-size: 75px; font-weight: bold; line-height: 1; text-align: right; text-shadow: 0 0 10px currentColor; }
        .lbl { font-size: 16px; opacity: 0.8; }
        
        /* Ocultar solo footer, DEJAR HEADER VISIBLE PARA PODER USAR LA FLECHA */
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # --- PANEL DOCENTE (IZQUIERDA) ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        st.info("Configura aquí. Cierra este panel ('X') para ver pantalla completa.")
        
        with st.form("control_panel"):
            st.markdown("### Selección de Ritmo")
            sel_ritmo = st.selectbox("Ritmo ECG", list(RITMOS_DB.keys()))
            
            st.markdown("### Signos Vitales")
            p = st.session_state.params
            v_hr = st.slider("Frecuencia Cardíaca", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("P. Sistólica", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("P. Diastólica", 0, 200, p["pad"])
            
            v_rr = st.slider("F. Respiratoria", 0, 60, p["rr"])
            v_vol = st.slider("🔊 Volumen Audio", 0.0, 1.0, p["vol"])
            
            if st.form_submit_button("🚀 APLICAR CAMBIOS", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr, "vol": v_vol
                }
                st.rerun()

        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- MONITOR ESTUDIANTE (DERECHA) ---
    d = st.session_state.params
    pam = int((d['pas'] + 2*d['pad']) / 3)

    c_izq, c_der = st.columns([1, 3.5])

    with c_izq:
        st.markdown(f"""
        <div class="vital-box hr"><div class="lbl">FC</div><div class="val">{d['hr']}</div></div>
        <div class="vital-box spo2"><div class="lbl">SpO2</div><div class="val">{d['spo2']}</div></div>
        <div class="vital-box bp"><div class="lbl">PANI ({pam})</div><div class="val" style="font-size:55px">{d['pas']}/{d['pad']}</div></div>
        <div class="vital-box rr"><div class="lbl">RR</div><div class="val">{d['rr']}</div></div>
        """, unsafe_allow_html=True)

    with c_der:
        url_raw = RITMOS_DB.get(d['ritmo'])
        if url_raw:
            url_embed = obtener_url_embed(url_raw)
            components.html(
                f"""<body style="margin:0; background:black; overflow:hidden;">
                    <iframe src="{url_embed}" width="100%" height="700" frameborder="0" allow="autoplay"></iframe>
                </body>""",
                height=700
            )
        else:
            st.error("Error: Video no configurado en Secrets.")

    # --- AUDIO (Script JS Invisible) ---
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
