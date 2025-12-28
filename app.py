import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIONES ---
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

# --- ESTADO ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
    }

# ==============================================================================
# FASE 1: LOGIN (FONDO CLARO)
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #f0f2f6; color: black; }
        header { visibility: hidden; }
        .login-card {
            background: white; padding: 40px; border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center;
            max-width: 400px; margin: 80px auto;
        }
        input { color: black !important; background: white !important; border: 1px solid #ccc !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card'><h2>🏥 Control Docente</h2><p>Ingrese credenciales</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", type="primary", use_container_width=True):
                if u == CREDS["username"] and p == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Acceso denegado")

# ==============================================================================
# FASE 2: SIMULADOR (SIN AUDIO)
# ==============================================================================
else:
    st.markdown("""
    <style>
        /* MONITOR NEGRO */
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* PANEL DOCENTE BLANCO */
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 3px solid #d1d1d1; }
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 { color: #000000 !important; }
        
        /* BOTÓN DE MENÚ */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background-color: white !important;
            border: 2px solid #ccc; top: 15px; left: 15px; z-index: 9999999;
        }
        
        /* CAJAS MONITOR */
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
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # --- PANEL DOCENTE ---
    with st.sidebar:
        st.title("🎛️ Configuración")
        with st.form("control_panel"):
            sel_ritmo = st.selectbox("Ritmo ECG", list(RITMOS_DB.keys()))
            p = st.session_state.params
            v_hr = st.slider("FC (LPM)", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            v_rr = st.slider("FR (RPM)", 0, 60, p["rr"])
            
            if st.form_submit_button("🚀 APLICAR CAMBIOS", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr
                }
                st.rerun()

        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- MONITOR ---
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
                </body>""", height=700
            )
        else:
            st.error("Video no configurado.")

