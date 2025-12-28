import streamlit as st
import time
import random
import string

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA ---
st.set_page_config(
    page_title="Simulador Clínico Avanzado",
    page_icon="monitor",
    layout="wide",
    initial_sidebar_state="collapsed" # Inicia colapsado para que los alumnos no vean el panel
)

# --- CSS PROFESIONAL (ESTILO MONITOR DE UCI) ---
st.markdown("""
<style>
    /* 1. FORZAR MODO OSCURO TOTAL Y TIPOGRAFÍA */
    .stApp {
        background-color: #000000 !important;
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 2. OCULTAR ELEMENTOS NATIVOS DE STREAMLIT (HAMBURGUESA, FOOTER) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* 3. CAJAS DE SIGNOS VITALES (ALTA FIDELIDAD) */
    .vital-container {
        background-color: #0a0a0a;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 160px; /* Altura fija para alineación */
    }

    /* Colores Específicos */
    .c-hr { border-left: 8px solid #00ff00; color: #00ff00; } /* Verde */
    .c-spo2 { border-left: 8px solid #ffff00; color: #ffff00; } /* Amarillo */
    .c-nbp { border-left: 8px solid #ff3333; color: #ff3333; } /* Rojo */
    .c-rr { border-left: 8px solid #00ffff; color: #00ffff; } /* Cyan */

    /* Textos dentro de las cajas */
    .vital-label { font-size: 18px; font-weight: 600; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px;}
    .vital-value { 
        font-family: 'Consolas', 'Courier New', monospace; 
        font-size: 85px; 
        font-weight: 700; 
        line-height: 1; 
        text-shadow: 0 0 10px currentColor; /* Efecto Glow/Neón */
    }
    .vital-sub { font-size: 24px; font-family: 'Courier New', monospace; margin-top: 5px; opacity: 0.9;}

    /* 4. VIDEO CONTAINER */
    .video-container {
        border: 2px solid #333;
        border-radius: 10px;
        overflow: hidden;
        background: black;
        box-shadow: 0 0 20px rgba(0,255,0,0.1);
    }
    
    /* 5. MENSAJES DE ERROR/LOGIN */
    .login-box {
        background-color: #ffffff;
        color: #000000;
        padding: 40px;
        border-radius: 10px;
        margin-top: 100px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE SECRETOS Y SEGURIDAD ---
def obtener_ritmos_y_credenciales():
    # Verificar si existen los secretos configurados en la nube
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.warning("⚠️ MODO DEPURACIÓN: Secrets no encontrados.")
        st.info("Configura los secretos en Streamlit Cloud. Usando valores de prueba temporales...")
        # Valores fallback para que NO falle si olvidas configurar (Solo para prueba)
        return {"username":"admin", "password":"123"}, {"Ritmo Sinusal (Demo)":"https://screenpal.com/watch/cTVFFNnf1p2"}
    
    return st.secrets["credentials"], st.secrets["ritmos"]

CREDENTIALS, RITMOS_DB = obtener_ritmos_y_credenciales()

# --- INICIALIZACIÓN DE ESTADO (SESSION STATE) ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "monitor_params" not in st.session_state:
    # Estado inicial del monitor (lo que ve el alumno)
    st.session_state.monitor_params = {
        "ritmo": list(RITMOS_DB.keys())[0],
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16, "vol": 0.0,
        "blackout": False # Pantalla negra inicial
    }
if "sim_id" not in st.session_state:
    st.session_state.sim_id = "INIT-001"

# --- PANTALLA 1: LOGIN (VISIBLE Y CLARA) ---
def login_screen():
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        # Usamos un container con fondo blanco forzado por CSS (clase login-box)
        st.markdown('<div class="login-box"><h2>🔐 Acceso Docente</h2>', unsafe_allow_html=True)
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR AL SISTEMA", type="primary"):
            if user == CREDENTIALS["username"] and pwd == CREDENTIALS["password"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Credenciales inválidas")
        st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 2: MONITOR DE SIGNOS VITALES ---
def monitor_screen():
    # ---------------------------------------------------------
    # PANEL DE CONTROL DOCENTE (BARRA LATERAL / SIDEBAR)
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("🎛️ PANEL DOCENTE")
        st.markdown("*(Los alumnos no ven esto)*")
        st.info(f"🆔 Simulación: {st.session_state.sim_id}")

        # Formulario para que los cambios NO se apliquen inmediatamente
        with st.form("panel_control"):
            st.subheader("1. Selección de Ritmo")
            # Recuperamos el valor actual para ponerlo por defecto
            current = st.session_state.monitor_params
            
            sel_ritmo = st.selectbox("Ritmo Cardíaco", list(RITMOS_DB.keys()))
            
            st.subheader("2. Signos Vitales")
            col_a, col_b = st.columns(2)
            with col_a:
                v_hr = st.number_input("FC (lpm)", 0, 300, current["hr"])
                v_spo2 = st.number_input("SpO2 (%)", 0, 100, current["spo2"])
            with col_b:
                v_pas = st.number_input("PAS (mmHg)", 0, 300, current["pas"])
                v_pad = st.number_input("PAD (mmHg)", 0, 300, current["pad"])
            
            v_rr = st.number_input("FR (rpm)", 0, 100, current["rr"])
            v_vol = st.slider("Volumen Sonido", 0.0, 1.0, current["vol"])

            st.subheader("3. Control de Visualización")
            v_blackout = st.checkbox("⬛ PANTALLA NEGRA (Pausa/Ocultar)", value=current["blackout"])

            # BOTÓN DE ACCIÓN
            aplicar = st.form_submit_button("🚀 ENVIAR AL MONITOR", type="primary")

        if aplicar:
            # Solo aquí actualizamos el estado que ve el alumno
            st.session_state.monitor_params = {
                "ritmo": sel_ritmo,
                "hr": v_hr, "spo2": v_spo2,
                "pas": v_pas, "pad": v_pad,
                "rr": v_rr, "vol": v_vol,
                "blackout": v_blackout
            }
            # Generar nuevo ID único para tracking
            st.session_state.sim_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            st.rerun()
            
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # ---------------------------------------------------------
    # VISUALIZACIÓN DEL MONITOR (LO QUE VEN LOS ALUMNOS)
    # ---------------------------------------------------------
    
    p = st.session_state.monitor_params

    # SI ESTÁ ACTIVO EL "BLACKOUT", NO MOSTRAMOS NADA
    if p["blackout"]:
        st.markdown("""
        <div style="display:flex; justify-content:center; align-items:center; height:80vh; border: 2px solid #333;">
            <h1 style="color:#333; font-family:'Courier New';">MONITOR EN ESPERA...</h1>
        </div>
        """, unsafe_allow_html=True)
        return # Cortamos la ejecución aquí

    # CÁLCULOS CLÍNICOS
    pam = int((p['pas'] + 2*p['pad']) / 3)

    # LAYOUT PRINCIPAL: 2 COLUMNAS (DATOS | ONDAS)
    col_izq, col_der = st.columns([1.5, 4])

    with col_izq:
        # FC (Verde)
        st.markdown(f"""
        <div class="vital-container c-hr">
            <div class="vital-label">ECG / LPM</div>
            <div class="vital-value">{p['hr']}</div>
        </div>
        """, unsafe_allow_html=True)

        # SpO2 (Amarillo)
        st.markdown(f"""
        <div class="vital-container c-spo2">
            <div class="vital-label">SpO2 %</div>
            <div class="vital-value">{p['spo2']}</div>
        </div>
        """, unsafe_allow_html=True)

        # PANI (Rojo)
        st.markdown(f"""
        <div class="vital-container c-nbp">
            <div class="vital-label">PANI mmHg</div>
            <div class="vital-value" style="font-size: 65px;">{p['pas']}/{p['pad']}</div>
            <div class="vital-sub">PAM: {pam}</div>
        </div>
        """, unsafe_allow_html=True)

        # FR (Cyan)
        st.markdown(f"""
        <div class="vital-container c-rr">
            <div class="vital-label">RESP rpm</div>
            <div class="vital-value">{p['rr']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        # ÁREA DE VIDEO (ONDAS)
        url_video = RITMOS_DB.get(p['ritmo'], "")
        
        # Título discreto del ritmo (opcional, para el alumno)
        st.markdown(f"<div style='margin-bottom:5px; color:#666; font-size:12px;'>DERIVACIÓN DII | {st.session_state.sim_id}</div>", unsafe_allow_html=True)
        
        if url_video:
            # Contenedor CSS para darle borde
            st.markdown('<div class="video-container">', unsafe_allow_html=True)
            st.video(url_video, autoplay=True, loop=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error(f"❌ ERROR: Video no encontrado para '{p['ritmo']}'. Revisa tus Secrets.")

    # ---------------------------------------------------------
    # SISTEMA DE SONIDO (JAVASCRIPT)
    # ---------------------------------------------------------
    # Nota: Los navegadores bloquean el sonido si no hay interacción.
    # Solución: Botón invisible que gestiona el contexto.
    
    if p['hr'] > 0 and p['vol'] > 0:
        intervalo_ms = (60 / p['hr']) * 1000
        
        # Script JS robusto que verifica el AudioContext
        js_sound = f"""
        <script>
            // Singleton para el contexto de audio
            if (!window.audioCtx) {{
                window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }}

            function playBeep() {{
                if (window.audioCtx.state === 'suspended') {{
                    // Intentamos reanudar (necesita interacción previa del usuario en la página)
                    window.audioCtx.resume();
                }}
                
                var osc = window.audioCtx.createOscillator();
                var gain = window.audioCtx.createGain();
                
                osc.connect(gain);
                gain.connect(window.audioCtx.destination);
                
                osc.type = 'square';
                osc.frequency.value = 750; // Tono "High Pitch" médico
                gain.gain.value = {p['vol']};
                
                osc.start();
                setTimeout(function() {{ osc.stop(); }}, 120);
            }}

            // Limpiar intervalos previos para evitar caos sonoro
            if (window.monitorInterval) clearInterval(window.monitorInterval);
            
            // Iniciar nuevo ritmo
            window.monitorInterval = setInterval(playBeep, {intervalo_ms});
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js_sound, height=0, width=0)
        
        # Botón pequeño de ayuda si el sonido no arranca (culpa del navegador)
        st.toast("🔊 Si no escuchas sonido, haz clic en cualquier lugar de la página una vez.", icon="ℹ️")


# --- EJECUCIÓN ---
if __name__ == "__main__":
    if not st.session_state.auth:
        login_screen()
    else:
        monitor_screen()
