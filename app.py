import streamlit as st
import pandas as pd
import random
import string

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS (Interfaz Monitor) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: white; }
    
    /* Cajas de métricas */
    .metric-box {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 12px;
        border-left: 6px solid;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Colores */
    .hr { border-color: #00ff00; color: #00ff00; }     
    .spo2 { border-color: #ffff00; color: #ffff00; }   
    .bp { border-color: #ff3333; color: #ff3333; }     
    .rr { border-color: #00ffff; color: #00ffff; }     
    
    /* Tipografía */
    .value-large { font-family: 'Courier New', monospace; font-size: 65px; font-weight: bold; line-height: 0.9; }
    .label { font-size: 14px; opacity: 0.7; font-weight: normal; margin-bottom: 2px; }
    .sub-value { font-size: 20px; font-family: 'Courier New', monospace; opacity: 0.9; margin-top: 5px; }

    /* Ocultar elementos nativos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE SEGURIDAD (STRICT SECRETS) ---
def verificar_acceso():
    if st.session_state.get("authenticated", False):
        return True

    # Intentar cargar secretos primero. Si no existen, detener la app por seguridad.
    if "credentials" not in st.secrets:
        st.error("⛔ ERROR DE CONFIGURACIÓN: No se detectaron los 'Secrets'.")
        st.info("Configura las claves en .streamlit/secrets.toml (Local) o en el panel de Streamlit Cloud.")
        st.stop()

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("### 🔐 Acceso al Simulador")
        input_user = st.text_input("Usuario")
        input_pass = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar"):
            # Validación estricta contra secrets
            sec_user = st.secrets["credentials"]["username"]
            sec_pass = st.secrets["credentials"]["password"]

            if input_user == sec_user and input_pass == sec_pass:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    
    return False

if not verificar_acceso():
    st.stop()

# --- CARGA DE BASE DE DATOS (CSV) ---
@st.cache_data
def cargar_ritmos_csv():
    try:
        # Lee el archivo CSV subido al repositorio
        df = pd.read_csv("ritmos.csv", header=0, usecols=[0,1])
        df.dropna(inplace=True) # Eliminar filas vacías
        return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    except FileNotFoundError:
        st.error("⚠️ CRÍTICO: No se encuentra el archivo 'ritmos.csv' en el repositorio.")
        return {}
    except Exception as e:
        st.error(f"Error leyendo la base de datos: {e}")
        return {}

ritmos_db = cargar_ritmos_csv()

if not ritmos_db:
    st.warning("La base de datos de ritmos está vacía o no se pudo cargar.")
    st.stop()

# --- INICIALIZACIÓN DE ESTADO ---
if 'params' not in st.session_state:
    first_ritmo = list(ritmos_db.keys())[0]
    st.session_state.params = {
        "ritmo_nombre": first_ritmo,
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }
    st.session_state.id_sim = "READY"

# --- PANEL INSTRUCTOR (SIDEBAR) ---
with st.sidebar:
    st.title("🎛️ Panel Instructor")
    
    sel_ritmo = st.selectbox("Ritmo Cardíaco", options=list(ritmos_db.keys()))
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        v_hr = st.number_input("FC (lpm)", 0, 300, 80)
        v_spo2 = st.number_input("SpO2 (%)", 0, 100, 98)
    with c2:
        v_pas = st.number_input("PAS (mmHg)", 0, 300, 120)
        v_pad = st.number_input("PAD (mmHg)", 0, 200, 80)
    
    v_rr = st.number_input("FR (rpm)", 0, 60, 16)
    v_vol = st.slider("Volumen QRS", 0.0, 1.0, 0.5)

    if st.button("🚀 ENVIAR AL MONITOR", type="primary"):
        st.session_state.params = {
            "ritmo_nombre": sel_ritmo,
            "hr": v_hr, "spo2": v_spo2, 
            "pas": v_pas, "pad": v_pad, 
            "rr": v_rr, "vol": v_vol
        }
        st.session_state.id_sim = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.rerun()

    st.caption(f"ID Sesión: {st.session_state.id_sim}")

# --- VISUALIZACIÓN MONITOR ---
p = st.session_state.params
pam = int((p['pas'] + 2*p['pad']) / 3)

col_izq, col_der = st.columns([1.2, 3])

with col_izq:
    # FC
    st.markdown(f"""
    <div class="metric-box hr">
        <div class="label">FC (lpm)</div>
        <div class="value-large">{p['hr']}</div>
    </div>
    """, unsafe_allow_html=True)

    # SpO2
    st.markdown(f"""
    <div class="metric-box spo2">
        <div class="label">SpO2 (%)</div>
        <div class="value-large">{p['spo2']}</div>
    </div>
    """, unsafe_allow_html=True)

    # PA
    st.markdown(f"""
    <div class="metric-box bp">
        <div class="label">PANI (mmHg)</div>
        <div class="value-large" style="font-size: 55px;">{p['pas']}/{p['pad']}</div>
        <div class="sub-value">PAM: {pam}</div>
    </div>
    """, unsafe_allow_html=True)

    # FR
    st.markdown(f"""
    <div class="metric-box rr">
        <div class="label">FR (rpm)</div>
        <div class="value-large" style="font-size: 55px;">{p['rr']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_der:
    url = ritmos_db.get(p['ritmo_nombre'])
    if url:
        st.video(url, autoplay=True, loop=True)
    else:
        st.error(f"No hay video vinculado a: {p['ritmo_nombre']}")

# --- SONIDO SINTÉTICO (JS) ---
if p['hr'] > 0 and p['vol'] > 0:
    intervalo_ms = (60 / p['hr']) * 1000
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
            gn.gain.value = {p['vol']};
            osc.start();
            setTimeout(()=>osc.stop(), 150);
        }}
        if(window.t) clearInterval(window.t);
        window.t = setInterval(beep, {intervalo_ms});
    </script>
    """
    import streamlit.components.v1 as components
    components.html(js, height=0)