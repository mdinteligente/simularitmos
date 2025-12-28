import streamlit as st
import time
import random
import string

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed" # Inicia cerrado para privacidad
)

# --- ESTILOS CSS AVANZADOS (INTERFAZ MÉDICA) ---
st.markdown("""
<style>
    /* 1. ESTILOS GENERALES Y LOGIN */
    .stApp {
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Ocultar elementos nativos que estorban */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo del Login (Fondo claro forzado para legibilidad) */
    .login-container {
        max-width: 450px;
        margin: 100px auto;
        padding: 40px;
        background-color: #f0f2f6; /* Gris muy claro */
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
        color: #31333F;
    }
    
    /* 2. ESTILOS DEL MODO MONITOR (SOLO SE ACTIVAN AL ENTRAR) */
    .monitor-bg {
        background-color: #000000 !important;
        color: white;
    }
    
    /* Cajas de Signos Vitales (Diseño Phillips/GE) */
    .vital-box {
        background-color: #050505;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 140px;
        position: relative;
    }
    
    /* Indicadores de color lateral */
    .border-hr { border-left: 6px solid #00ff00; }
    .border-spo2 { border-left: 6px solid #ffff00; }
    .border-bp { border-left: 6px solid #ff3333; }
    .border-rr { border-left: 6px solid #00ffff; }

    /* Tipografía de Monitor */
    .vital-label { 
        font-size: 16px; 
        font-weight: bold; 
        opacity: 0.9; 
        position: absolute; 
        top: 10px; 
        left: 15px;
    }
    
    .vital-value { 
        font-family: 'Consolas', 'Courier New', monospace; 
        font-size: 80px; 
        font-weight: bold; 
        text-align: right;
        padding-right: 15px;
        line-height: 1;
        text-shadow: 0 0 5px currentColor; /* Efecto Neón */
    }
    
    .vital-sub {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 20px;
        position: absolute;
        bottom: 10px;
        left: 15px;
        opacity: 0.8;
    }

    /* Colores de texto */
    .txt-green { color: #00ff00; }
    .txt-yellow { color: #ffff00; }
    .txt-red { color: #ff3333; }
    .txt-cyan { color: #00ffff; }

</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE SECRETS ---
def get_secrets():
    # Fallback para pruebas si no hay secrets configurados
    if "credentials" not in st.secrets:
        return {"username":"admin", "password":"123"}, {}
    return st.secrets["credentials"], st.secrets["ritmos"]

creds, ritmos_db = get_secrets()

# --- ESTADO DE LA SESIÓN ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "monitor_data" not in st.session_state:
    # Datos que se muestran EN EL MONITOR (Alumnos)
    st.session_state.monitor_data = {
        "ritmo": list(ritmos_db.keys())[0] if ritmos_db else "Sinusal",
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0
    }
if "id_sim" not in st.session_state:
    st.session_state.id_sim = "INICIO"

# ==========================================
# 1. PANTALLA DE LOGIN (Visible y Clara)
# ==========================================
if not st.session_state.auth:
    # Contenedor centrado manual con HTML para evitar estilos oscuros globales
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <h2 style='color:black; margin-bottom:0;'>🏥 Simulador Clínico</h2>
            <p style='color:gray;'>Acceso exclusivo docente</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            btn = st.form_submit_button("INGRESAR", type="primary")
            
            if btn:
                if u == creds["username"] and p == creds["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("❌ Datos incorrectos")

# ==========================================
# 2. PANTALLA DEL MONITOR (Modo Oscuro)
# ==========================================
else:
    # Inyectar fondo negro SOLO cuando ya estamos logueados
    st.markdown("""<style>.stApp {background-color: #000000 !important; color: white;}</style>""", unsafe_allow_html=True)

    # --- BARRA LATERAL (CONTROLES OCULTOS) ---
    with st.sidebar:
        st.header("🎛️ Configuración Docente")
        st.info(f"ID Actual: {st.session_state.id_sim}")
        
        # FORMULARIO DE BUFFER: Los cambios no se ven hasta dar "Enviar"
        with st.form("panel_control"):
            st.write("### 1. Seleccionar Ritmo")
            # Recuperar valor actual para el default
            curr = st.session_state.monitor_data
            
            # Selector de ritmo con la lista completa de tus secrets
            nuevo_ritmo = st.selectbox("Ritmo (DII)", options=list(ritmos_db.keys()))
            
            st.write("### 2. Signos Vitales")
            c1, c2 = st.columns(2)
            with c1:
                n_hr = st.number_input("FC (lpm)", 0, 300, curr["hr"])
                n_spo2 = st.number_input("SpO2 (%)", 0, 100, curr["spo2"])
            with c2:
                n_pas = st.number_input("PAS (mmHg)", 0, 300, curr["pas"])
                n_pad = st.number_input("PAD (mmHg)", 0, 300, curr["pad"])
            
            n_rr = st.number_input("FR (rpm)", 0, 100, curr["rr"])
            st.write("### 3. Audio")
            n_vol = st.slider("Volumen QRS", 0.0, 1.0, curr["vol"])
            
            # BOTÓN CLAVE: Envía los datos al monitor principal
            aplicar = st.form_submit_button("🚀 ENVIAR AL MONITOR", type="primary")
        
        if aplicar:
            st.session_state.monitor_data = {
                "ritmo": nuevo_ritmo,
                "hr": n_hr, "spo2": n_spo2, 
                "pas": n_pas, "pad": n_pad, "rr": n_rr, "vol": n_vol
            }
            # Generar nuevo ID aleatorio
            st.session_state.id_sim = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            st.rerun()

        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- VISUALIZACIÓN PRINCIPAL (ALUMNOS) ---
    d = st.session_state.monitor_data
    pam = int((d['pas'] + 2*d['pad']) / 3)

    # Layout de Monitor: Signos a la izquierda, Curvas a la derecha
    col_mon1, col_mon2 = st.columns([1.2, 3])

    with col_mon1:
        # FC
        st.markdown(f"""
        <div class="vital-box border-hr">
            <div class="vital-label txt-green">FC <span style="font-size:12px">lpm</span></div>
            <div class="vital-value txt-green">{d['hr']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # SpO2
        st.markdown(f"""
        <div class="vital-box border-spo2">
            <div class="vital-label txt-yellow">SpO2 <span style="font-size:12px">%</span></div>
            <div class="vital-value txt-yellow">{d['spo2']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # PA
        st.markdown(f"""
        <div class="vital-box border-bp">
            <div class="vital-label txt-red">PANI <span style="font-size:12px">mmHg</span></div>
            <div class="vital-value txt-red" style="font-size:60px; margin-top:10px;">{d['pas']}/{d['pad']}</div>
            <div class="vital-sub txt-red">PAM: {pam}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # FR
        st.markdown(f"""
        <div class="vital-box border-rr">
            <div class="vital-label txt-cyan">FR <span style="font-size:12px">rpm</span></div>
            <div class="vital-value txt-cyan">{d['rr']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_mon2:
        # Video del Ritmo
        url = ritmos_db.get(d['ritmo'])
        if url:
            # Contenedor para el video
            st.markdown(f"<h3 style='margin:0; color:#aaa; font-size:14px;'>DERIVACIÓN II | ID: {st.session_state.id_sim}</h3>", unsafe_allow_html=True)
            st.video(url, autoplay=True, loop=True)
        else:
            st.error("Video no disponible en Secrets")

    # --- SCRIPT DE AUDIO ROBUSTO ---
    # Solo inyectamos si hay volumen y latido
    if d['hr'] > 0 and d['vol'] > 0:
        intervalo = (60 / d['hr']) * 1000
        
        # Usamos un botón invisible para "despertar" el AudioContext si está suspendido
        sound_script = f"""
        <script>
            // Crear contexto de audio global
            var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            
            function playBeep() {{
                // Intentar reanudar si el navegador lo bloqueó
                if (audioCtx.state === 'suspended') {{
                    audioCtx.resume();
                }}
                
                var oscillator = audioCtx.createOscillator();
                var gainNode = audioCtx.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                
                oscillator.type = 'square';
                oscillator.frequency.value = 750; // Tono médico
                gainNode.gain.value = {d['vol']}; // Volumen
                
                oscillator.start();
                setTimeout(function() {{ oscillator.stop(); }}, 150);
            }}

            // Limpiar timers anteriores
            if (window.monitorTimer) clearInterval(window.monitorTimer);
            
            // Iniciar nuevo timer
            window.monitorTimer = setInterval(playBeep, {intervalo});
        </script>
        """
        import streamlit.components.v1 as components
        components.html(sound_script, height=0, width=0)
        
        # Botón de rescate por si el navegador bloquea el sonido
        if st.button("🔊 ACTIVAR SONIDO (Click aquí si no suena)"):
            pass # Al hacer click, el script JS aprovecha la interacción para arrancar
