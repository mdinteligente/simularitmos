import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNCIONES Y SECRETOS ---
def obtener_url_embed(url_original):
    # Convierte enlace ScreenPal Watch -> Player
    if "screenpal.com/watch/" in url_original:
        vid_id = url_original.split("/")[-1].strip()
        # autoplay=1, controls=0 para que sea video puro
        return f"https://screenpal.com/player/{vid_id}?width=100%&height=100%&autoplay=1&controls=0&title=0"
    return url_original

def get_secrets():
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR: Faltan Secrets.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

CREDS, RITMOS_DB = get_secrets()

# --- 3. ESTADO DE LA SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False

# Inicializamos parámetros si no existen
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
    }
# El volumen lo manejamos por separado para que sea tiempo real
if "volumen_realtime" not in st.session_state:
    st.session_state.volumen_realtime = 0.5

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
# FASE 2: SIMULADOR (PANEL CLARO vs MONITOR OSCURO)
# ==============================================================================
else:
    # CSS CLÍNICO
    st.markdown("""
    <style>
        /* FONDO GLOBAL NEGRO (MONITOR) */
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* PANEL LATERAL DOCENTE (BLANCO) */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 3px solid #d1d1d1;
        }
        /* Texto Negro en Sidebar */
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {
            color: #000000 !important;
        }
        
        /* BOTÓN > (ABRIR PANEL) */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background-color: white !important;
            display: block !important; border: 2px solid #ccc;
            top: 15px; left: 15px; z-index: 9999999;
        }
        
        /* CAJAS SIGNOS VITALES */
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
        
        # 1. CONTROL DE VOLUMEN (FUERA DEL FORMULARIO PARA TIEMPO REAL)
        st.markdown("### 🔊 Sonido Monitor")
        vol_realtime = st.slider(
            "Nivel de Volumen", 
            min_value=0.0, max_value=1.0, 
            value=st.session_state.volumen_realtime,
            step=0.05,
            key="volumen_realtime" # Actualiza session_state automáticamente
        )
        st.info("💡 Mueve el volumen para escuchar cambios en tiempo real.")
        st.divider()

        # 2. PARÁMETROS CLÍNICOS (DENTRO DEL FORMULARIO 'STEALTH')
        with st.form("control_panel"):
            st.markdown("### Escenario Clínico")
            sel_ritmo = st.selectbox("Ritmo ECG", list(RITMOS_DB.keys()))
            
            p = st.session_state.params
            v_hr = st.slider("Frecuencia Cardíaca (LPM)", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("P. Sistólica", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("P. Diastólica", 0, 200, p["pad"])
            
            v_rr = st.slider("F. Respiratoria (RPM)", 0, 60, p["rr"])
            
            # Botón ROJO
            if st.form_submit_button("🚀 APLICAR ESCENARIO", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr
                }
                st.rerun()

        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- MONITOR ESTUDIANTE ---
    d = st.session_state.params
    pam = int((d['pas'] + 2*d['pad']) / 3)
    
    # Usamos el volumen de tiempo real, no el guardado en params
    volumen_actual = st.session_state.volumen_realtime

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
            st.error("Video no configurado.")

    # --- AUDIO SINTÉTICO (MEJORADO Y SINCRONIZADO) ---
    if d['hr'] > 0 and volumen_actual > 0:
        intervalo = (60 / d['hr']) * 1000
        
        # Script JS con control de ganancia mejorado
        components.html(f"""
        <script>
            var ac = window.audioCtx || new (window.AudioContext || window.webkitAudioContext)();
            window.audioCtx = ac;

            function beep() {{
                if (ac.state === 'suspended') ac.resume();
                
                var osc = ac.createOscillator(); 
                var gainNode = ac.createGain();
                
                osc.connect(gainNode); 
                gainNode.connect(ac.destination);
                
                osc.type = 'square'; 
                osc.frequency.setValueAtTime(750, ac.currentTime);
                
                // CURVA DE VOLUMEN NATURAL (Cuadrática)
                // Esto hace que el slider se sienta más realista
                var rawVol = {volumen_actual};
                var realVol = Math.pow(rawVol, 2); 
                
                gainNode.gain.setValueAtTime(realVol, ac.currentTime);
                
                osc.start(); 
                osc.stop(ac.currentTime + 0.12);
            }}

            if (window.monitorInterval) clearInterval(window.monitorInterval);
            window.monitorInterval = setInterval(beep, {intervalo});
        </script>
        """, height=0, width=0)
    else:
        # Silencio absoluto si vol es 0
        components.html("<script>if (window.monitorInterval) clearInterval(window.monitorInterval);</script>", height=0, width=0)
