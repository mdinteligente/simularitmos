import streamlit as st
import random
import string

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador SV", layout="wide", initial_sidebar_state="collapsed")

# --- ESTILOS CSS (Mismos de antes) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: white; }
    .metric-box { background-color: #1a1a1a; border-radius: 8px; padding: 10px; margin-bottom: 10px; border-left: 5px solid; }
    .hr { border-color: #00ff00; color: #00ff00; }
    .spo2 { border-color: #ffff00; color: #ffff00; }
    .bp { border-color: #ff3333; color: #ff3333; }
    .rr { border-color: #00ffff; color: #00ffff; }
    .value-large { font-family: 'Courier New', monospace; font-size: 60px; font-weight: bold; line-height: 1; }
    .label { font-size: 14px; opacity: 0.7; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SEGURIDAD Y DATOS ---
def cargar_simulador():
    # 1. Verificar si existen los secretos
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR: Configuración incompleta en Secrets.")
        st.info("Debes configurar [credentials] y [ritmos] en el panel de Streamlit.")
        st.stop()

    # 2. Login
    if not st.session_state.get("authenticated", False):
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.markdown("### 🔐 Acceso Docente")
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("Entrar"):
                if u == st.secrets["credentials"]["username"] and p == st.secrets["credentials"]["password"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Datos incorrectos")
        st.stop()

    # 3. Cargar Ritmos desde Secrets (No desde CSV)
    # st.secrets["ritmos"] ya nos devuelve un diccionario python automáticamente
    return st.secrets["ritmos"]

ritmos_db = cargar_simulador()

# --- LÓGICA DEL SIMULADOR ---
if 'params' not in st.session_state:
    # Seleccionar el primer ritmo disponible por defecto
    first = list(ritmos_db.keys())[0]
    st.session_state.params = {"ritmo": first, "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0}
    st.session_state.id_sim = "READY"

# --- SIDEBAR (INSTRUCTOR) ---
with st.sidebar:
    st.title("🎛️ Panel de Control")
    sel_ritmo = st.selectbox("Ritmo", options=list(ritmos_db.keys()))
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        v_hr = st.number_input("FC", 0, 300, 80)
        v_spo2 = st.number_input("SpO2", 0, 100, 98)
    with c2:
        v_pas = st.number_input("PAS", 0, 300, 120)
        v_pad = st.number_input("PAD", 0, 300, 80)
    v_rr = st.number_input("FR", 0, 60, 16)
    v_vol = st.slider("Volumen", 0.0, 1.0, 0.5)
    
    if st.button("🚀 ENVIAR", type="primary"):
        st.session_state.params = {
            "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2, 
            "pas": v_pas, "pad": v_pad, "rr": v_rr, "vol": v_vol
        }
        st.session_state.id_sim = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.rerun()
    st.caption(f"ID: {st.session_state.id_sim}")

# --- MONITOR ---
p = st.session_state.params
pam = int((p['pas'] + 2*p['pad']) / 3)
c_izq, c_der = st.columns([1, 3])

with c_izq:
    st.markdown(f"""<div class="metric-box hr"><div class="label">FC</div><div class="value-large">{p['hr']}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-box spo2"><div class="label">SpO2</div><div class="value-large">{p['spo2']}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-box bp"><div class="label">PNI ({pam})</div><div class="value-large" style="font-size:50px">{p['pas']}/{p['pad']}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-box rr"><div class="label">FR</div><div class="value-large">{p['rr']}</div></div>""", unsafe_allow_html=True)

with c_der:
    url = ritmos_db.get(p['ritmo'])
    if url: st.video(url, autoplay=True, loop=True)
    else: st.error("Video no configurado en Secrets.")

# --- AUDIO (JS) ---
if p['hr'] > 0 and p['vol'] > 0:
    interval = (60 / p['hr']) * 1000
    st.components.v1.html(f"""<script>
    var ac = new (window.AudioContext||window.webkitAudioContext)();
    function beep(){{
        if(ac.state==='suspended')ac.resume();
        var o=ac.createOscillator();o.connect(ac.destination);
        o.type='square';o.frequency.value=750;
        var g=ac.createGain();o.connect(g);g.connect(ac.destination);
        o.start();setTimeout(()=>o.stop(),150);
    }}
    setInterval(beep,{interval});
    </script>""", height=0)