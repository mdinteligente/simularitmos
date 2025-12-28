import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNCIONES UTILITARIAS ---
def obtener_url_embed(url_original):
    if "screenpal.com/watch/" in url_original:
        vid_id = url_original.split("/")[-1].strip()
        # Parámetros para forzar video limpio
        return f"https://screenpal.com/player/{vid_id}?width=100%&height=100%&autoplay=1&controls=0&title=0"
    return url_original

def get_secrets():
    # Validación de seguridad
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ Falta configurar los Secrets.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

CREDS, RITMOS_DB = get_secrets()

# --- 3. CSS "A PRUEBA DE FALLOS" ---
st.markdown("""
<style>
    /* Fondo General */
    .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
    
    /* Ocultar menú de hamburguesa y footer, PERO NO EL CONTROL LATERAL */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* FORZAR VISIBILIDAD DEL BOTÓN PARA ABRIR BARRA LATERAL (FLECHA >) */
    section[data-testid="stSidebar"] > div {
        z-index: 99999 !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: block !important;
        color: white !important;
        background-color: #333;
        border-radius: 5px;
        top: 10px;
        left: 10px;
        z-index: 999999 !important; /* Capa superior absoluta */
    }

    /* Estilos del Login */
    .login-box {
        background: #eee; padding: 40px; border-radius: 10px;
        color: #333; text-align: center; max-width: 400px; margin: 50px auto;
    }

    /* Estilos Monitor */
    .vital-box {
        background: #080808; border-left: 6px solid;
        padding: 5px 10px; margin-bottom: 8px; position: relative; height: 16vh;
        display: flex; flex-direction: column; justify-content: center;
    }
    .hr { border-color: #00ff00; color: #00ff00; }
    .spo2 { border-color: #ffff00; color: #ffff00; }
    .bp { border-color: #ff3333; color: #ff3333; }
    .rr { border-color: #00ffff; color: #00ffff; }

    .val { font-size: 70px; font-weight: bold; line-height: 1; text-align: right; text-shadow: 0 0 10px currentColor; }
    .lbl { font-size: 14px; opacity: 0.8; position: absolute; top: 5px; left: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# ==========================================
# VISTA 1: LOGIN
# ==========================================
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<div class='login-box'><h3>🔐 Control Docente</h3></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR", type="primary"):
                if u == CREDS["username"] and p == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Acceso denegado")

# ==========================================
# VISTA 2: SIMULADOR (PANEL + MONITOR)
# ==========================================
else:
    # --- PANEL DOCENTE (BARRA LATERAL) ---
    with st.sidebar:
        st.title("🎛️ Configuración")
        st.warning("Pulsa la flecha '>' arriba a la izquierda si este panel se cierra.")
        
        with st.form("controls"):
            sel_ritmo = st.selectbox("Ritmo", list(RITMOS_DB.keys()))
            st.divider()
            
            p = st.session_state.params
            v_hr = st.slider("FC", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2", 0, 100, p["spo2"])
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            v_rr = st.slider("FR", 0, 60, p["rr"])
            v_vol = st.slider("Volumen", 0.0, 1.0, p["vol"])
            
            if st.form_submit_button("🚀 ACTUALIZAR", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr, "vol": v_vol
                }
                st.rerun()
        
        if st.button("Salir"):
            st.session_state.auth = False
            st.rerun()

    # --- MONITOR ESTUDIANTE (PANTALLA PRINCIPAL) ---
    d = st.session_state.params
    pam = int((d['pas'] + 2*d['pad']) / 3)

    # Botón de rescate flotante (por si se pierde el sidebar)
    if st.button("⚙️", help="Abrir controles"):
        # Al hacer clic, Streamlit refresca y suele mostrar la UI de nuevo
        pass

    c_izq, c_der = st.columns([1, 3.5])

    with c_izq:
        st.markdown(f"""
        <div class="vital-box hr"><div class="lbl">FC</div><div class="val">{d['hr']}</div></div>
        <div class="vital-box spo2"><div class="lbl">SpO2</div><div class="val">{d['spo2']}</div></div>
        <div class="vital-box bp"><div class="lbl">PANI ({pam})</div><div class="val" style="font-size:50px">{d['pas']}/{d['pad']}</div></div>
        <div class="vital-box rr"><div class="lbl">RR</div><div class="val">{d['rr']}</div></div>
        """, unsafe_allow_html=True)

    with c_der:
        # VIDEO (Iframe corregido)
        url_raw = RITMOS_DB.get(d['ritmo'])
        if url_raw:
            url_embed = obtener_url_embed(url_raw)
            components.html(
                f"""<body style="margin:0; background:black; overflow:hidden;">
                    <iframe src="{url_embed}" width="100%" height="700" frameborder="0" allow="autoplay"></iframe>
                </body>""",
                height=700
            )

    # AUDIO JS
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
