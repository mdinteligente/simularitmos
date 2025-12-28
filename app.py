import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNCIONES DE UTILIDAD ---
def obtener_url_embed(url_original):
    # Corrección para enlaces de ScreenPal
    if "screenpal.com/watch/" in url_original:
        vid_id = url_original.split("/")[-1].strip()
        return f"https://screenpal.com/player/{vid_id}?width=100%&height=100%&autoplay=1&controls=0&title=0"
    return url_original

def get_secrets():
    # Validación simple para que no falle si faltan secrets
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR: Configura los Secrets en Streamlit Cloud.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

CREDS, RITMOS_DB = get_secrets()

# --- 3. GESTIÓN DE ESTADO ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }

# ==============================================================================
# FASE 1: LOGIN (DISEÑO CLARO -VISIBLE-)
# ==============================================================================
if not st.session_state.auth:
    # CSS ESPECÍFICO PARA LOGIN (Fondo Claro, Letras Negras)
    st.markdown("""
    <style>
        /* Forzar fondo claro */
        .stApp { 
            background-color: #f0f2f6 !important; 
            color: black !important;
        }
        
        /* Contenedor del Login */
        .login-card {
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 450px;
            margin: 50px auto;
        }
        
        /* Estilos para inputs (Casillas) */
        input[type="text"], input[type="password"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        
        /* Ocultar elementos extra */
        #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # LAYOUT DEL LOGIN
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div class="login-card">
            <h1 style="color: #0d47a1;">🏥 Simulador Clínico</h1>
            <p style="color: #555;">Acceso Docente</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario nativo (Ahora se verá bien gracias al CSS de arriba)
        with st.form("login_form"):
            user = st.text_input("Usuario (simularitmos)")
            pwd = st.text_input("Contraseña", type="password")
            
            # Botón de ancho completo
            submitted = st.form_submit_button("INGRESAR AL SISTEMA", type="primary", use_container_width=True)
            
            if submitted:
                if user == CREDS["username"] and pwd == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

# ==============================================================================
# FASE 2: MONITOR (DISEÑO OSCURO -CLÍNICO-)
# ==============================================================================
else:
    # CSS ESPECÍFICO PARA EL MONITOR (Inyectado solo al entrar)
    st.markdown("""
    <style>
        /* FONDO NEGRO ABSOLUTO */
        .stApp { 
            background-color: #000000 !important; 
            color: white !important;
            font-family: 'Consolas', monospace;
        }

        /* ESTILO DEL PANEL LATERAL (DOCENTE) */
        section[data-testid="stSidebar"] {
            background-color: #1a1a1a !important;
            border-right: 1px solid #333;
        }
        /* Texto del sidebar visible */
        section[data-testid="stSidebar"] * {
            color: #eeeeee !important;
        }
        
        /* BOTÓN FLOTANTE PARA ABRIR SIDEBAR (Siempre visible) */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: #333;
            color: white;
            border-radius: 5px;
            z-index: 999999;
        }

        /* CAJAS DE SIGNOS VITALES */
        .vital-box {
            background: #080808; 
            border-left: 6px solid;
            padding: 5px 15px; 
            margin-bottom: 8px; 
            height: 16vh;
            display: flex; 
            flex-direction: column; 
            justify-content: center;
        }
        /* Colores */
        .hr { border-color: #00ff00; color: #00ff00; }
        .spo2 { border-color: #ffff00; color: #ffff00; }
        .bp { border-color: #ff3333; color: #ff3333; }
        .rr { border-color: #00ffff; color: #00ffff; }

        /* Tipografía Gigante */
        .val { font-size: 75px; font-weight: bold; line-height: 1; text-align: right; text-shadow: 0 0 10px currentColor; }
        .lbl { font-size: 16px; opacity: 0.8; text-transform: uppercase; }

        /* Ocultar UI de Streamlit */
        #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # --- BARRA LATERAL (DOCENTE) ---
    with st.sidebar:
        st.title("🎛️ Configuración")
        st.info("Para ocultar este panel, pulsa la 'X' o '<' arriba.")
        
        with st.form("controls"):
            # Ritmo
            sel_ritmo = st.selectbox("Seleccionar Ritmo", list(RITMOS_DB.keys()))
            st.divider()
            
            # Signos Vitales
            p = st.session_state.params
            v_hr = st.slider("FC (lpm)", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            
            c_a, c_b = st.columns(2)
            with c_a: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c_b: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            
            v_rr = st.slider("FR (rpm)", 0, 60, p["rr"])
            v_vol = st.slider("Volumen Audio", 0.0, 1.0, p["vol"])
            
            # Botón de Aplicar
            if st.form_submit_button("🚀 ACTUALIZAR MONITOR", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr, "vol": v_vol
                }
                st.rerun()

        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- MONITOR (ESTUDIANTE) ---
    d = st.session_state.params
    pam = int((d['pas'] + 2*d['pad']) / 3)

    # Botón de rescate discreto (Arriba a la derecha)
    c_fill, c_btn = st.columns([10, 1])
    with c_btn:
        if st.button("⚙️", key="rescue_btn", help="Si perdiste el panel, clic aquí"):
            pass

    # Layout Principal
    col_nums, col_video = st.columns([1, 3.5])

    with col_nums:
        # 1. FC
        st.markdown(f"""
        <div class="vital-box hr"><div class="lbl">FC (LPM)</div><div class="val">{d['hr']}</div></div>
        """, unsafe_allow_html=True)
        # 2. SpO2
        st.markdown(f"""
        <div class="vital-box spo2"><div class="lbl">SpO2 (%)</div><div class="val">{d['spo2']}</div></div>
        """, unsafe_allow_html=True)
        # 3. PA
        st.markdown(f"""
        <div class="vital-box bp"><div class="lbl">PANI (PAM {pam})</div><div class="val" style="font-size:55px">{d['pas']}/{d['pad']}</div></div>
        """, unsafe_allow_html=True)
        # 4. RR
        st.markdown(f"""
        <div class="vital-box rr"><div class="lbl">RR (RPM)</div><div class="val">{d['rr']}</div></div>
        """, unsafe_allow_html=True)

    with col_video:
        # REPRODUCCIÓN (Iframe ScreenPal)
        url_raw = RITMOS_DB.get(d['ritmo'])
        if url_raw:
            url_embed = obtener_url_embed(url_raw)
            components.html(
                f"""
                <body style="margin:0; background:black; overflow:hidden;">
                    <iframe src="{url_embed}" width="100%" height="700" frameborder="0" allow="autoplay"></iframe>
                </body>
                """,
                height=700
            )
        else:
            st.error("Video no encontrado")

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
