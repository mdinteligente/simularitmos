import streamlit as st
import time
import random
import string

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. FUNCIONES DE UTILIDAD ---

def generar_id_sesion():
    """Genera un ID único para la simulación clínica actual"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def cargar_secretos():
    """Manejo robusto de errores para secrets"""
    if "credentials" not in st.secrets or "ritmos" not in st.secrets:
        st.error("⛔ ERROR CRÍTICO: Secrets no configurados.")
        st.info("Por favor configura [credentials] y [ritmos] en el panel de Streamlit Cloud.")
        st.stop()
    return st.secrets["credentials"], st.secrets["ritmos"]

# --- 3. GESTIÓN DE ESTADO (SESSION STATE) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "sim_id" not in st.session_state:
    st.session_state.sim_id = generar_id_sesion()
if "params" not in st.session_state:
    # Valores por defecto fisiológicos
    st.session_state.params = {
        "ritmo_nombre": "Ritmo Sinusal", # Placeholder hasta cargar DB
        "hr": 80,
        "spo2": 98,
        "pas": 120,
        "pad": 80,
        "rr": 16,
        "vol": 0.0
    }

# --- 4. INTERFAZ DE LOGIN (ESTADO 1) ---
def mostrar_login(creds):
    # CSS específico para la pantalla de login (Limpio y visible)
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 30px;
            background-color: #f0f2f6;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stApp { background-color: white; color: black; } /* Forzar fondo claro en login */
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>🏥 Acceso Docente</h1></div>", unsafe_allow_html=True)
        st.markdown("### Simulador de Signos Vitales - Urgencias")
        
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("INGRESAR AL SIMULADOR", type="primary")
            
            if submit:
                if user == creds["username"] and password == creds["password"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

# --- 5. INTERFAZ DEL MONITOR (ESTADO 2) ---
def mostrar_monitor(ritmos_db):
    # CSS AGRESIVO PARA EL MODO MONITOR (NEGRO TOTAL)
    st.markdown("""
    <style>
        /* Fondo negro absoluto */
        .stApp { background-color: #000000 !important; color: white; }
        
        /* Ocultar elementos de Streamlit que distraen */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Estilos de las cajas de signos vitales */
        .vital-box {
            background-color: #111;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 15px;
            border-left: 6px solid;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        /* Colores Clínicos Estándar */
        .ecg-color { border-color: #00ff00; color: #00ff00; }     /* Verde */
        .spo2-color { border-color: #ffff00; color: #ffff00; }   /* Amarillo */
        .bp-color { border-color: #ff3333; color: #ff3333; }     /* Rojo */
        .rr-color { border-color: #00ffff; color: #00ffff; }     /* Cyan */
        
        /* Tipografía Digital */
        .vital-label { font-size: 16px; opacity: 0.8; font-weight: normal; margin-bottom: 0px; }
        .vital-value { font-family: 'Courier New', monospace; font-size: 80px; font-weight: bold; line-height: 1; text-shadow: 0 0 10px rgba(255,255,255,0.3); }
        .vital-sub { font-size: 24px; font-family: 'Courier New', monospace; opacity: 0.9; }
        
        /* Ajuste del contenedor de video */
        .stVideo { border: 2px solid #333; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

    # --- BARRA LATERAL (CONTROL DOCENTE) ---
    with st.sidebar:
        st.header("🎛️ Configuración")
        st.info(f"Simulación ID: **{st.session_state.sim_id}**")
        
        # Formulario para evitar recargas constantes, solo al aplicar
        with st.form("control_panel"):
            # Selección de Ritmo
            lista_ritmos = list(ritmos_db.keys())
            # Intentar mantener la selección anterior si existe
            idx_actual = 0
            if st.session_state.params["ritmo_nombre"] in lista_ritmos:
                idx_actual = lista_ritmos.index(st.session_state.params["ritmo_nombre"])
            
            sel_ritmo = st.selectbox("Ritmo Cardíaco (DII)", options=lista_ritmos, index=idx_actual)
            
            st.divider()
            
            # Signos Vitales
            c1, c2 = st.columns(2)
            with c1:
                new_hr = st.number_input("FC (lpm)", 0, 300, st.session_state.params["hr"])
                new_spo2 = st.number_input("SpO2 (%)", 0, 100, st.session_state.params["spo2"])
            with c2:
                new_pas = st.number_input("PAS (mmHg)", 0, 300, st.session_state.params["pas"])
                new_pad = st.number_input("PAD (mmHg)", 0, 300, st.session_state.params["pad"])
            
            new_rr = st.number_input("FR (rpm)", 0, 60, st.session_state.params["rr"])
            
            st.divider()
            new_vol = st.slider("Volumen Sonido QRS", 0.0, 1.0, st.session_state.params["vol"])
            
            # Botón de Aplicar
            aplicar = st.form_submit_button("🚀 ACTUALIZAR MONITOR")
            
            if aplicar:
                # Actualizar estado
                st.session_state.params = {
                    "ritmo_nombre": sel_ritmo,
                    "hr": new_hr,
                    "spo2": new_spo2,
                    "pas": new_pas,
                    "pad": new_pad,
                    "rr": new_rr,
                    "vol": new_vol
                }
                # Generar nuevo ID de evento si cambian parámetros críticos
                st.session_state.sim_id = generar_id_sesion()
                st.rerun()

        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.rerun()

    # --- ÁREA PRINCIPAL DEL MONITOR ---
    
    p = st.session_state.params
    # Cálculo de PAM (Presión Arterial Media)
    pam = int((p['pas'] + (2 * p['pad'])) / 3)

    # Layout: 25% Signos numéricos | 75% Trazados (Video)
    col_izq, col_der = st.columns([1.2, 3.5])

    with col_izq:
        # 1. Frecuencia Cardíaca (Verde)
        st.markdown(f"""
        <div class="vital-box ecg-color">
            <div class="vital-label">FC (lpm)</div>
            <div class="vital-value">{p['hr']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. SpO2 (Amarillo)
        st.markdown(f"""
        <div class="vital-box spo2-color">
            <div class="vital-label">SpO2 (%)</div>
            <div class="vital-value">{p['spo2']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. Presión Arterial (Rojo)
        st.markdown(f"""
        <div class="vital-box bp-color">
            <div class="vital-label">PANI (mmHg)</div>
            <div class="vital-value" style="font-size: 60px;">{p['pas']}/{p['pad']}</div>
            <div class="vital-sub">PAM: {pam}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 4. Frecuencia Respiratoria (Cyan)
        st.markdown(f"""
        <div class="vital-box rr-color">
            <div class="vital-label">FR (rpm)</div>
            <div class="vital-value" style="font-size: 60px;">{p['rr']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        # Trazado / Video
        # Nota: Screenpal permite pausar haciendo clic en el video (nativo del navegador)
        url_video = ritmos_db.get(p['ritmo_nombre'])
        
        if url_video:
            st.markdown(f"<h3 style='color:white; margin:0;'>Derivación DII - {p['ritmo_nombre']}</h3>", unsafe_allow_html=True)
            st.video(url_video, autoplay=True, loop=True)
        else:
            st.error(f"Video no encontrado para: {p['ritmo_nombre']}")
            st.warning("Verifica la configuración en Secrets.")

    # --- INYECCIÓN DE AUDIO (JavaScript) ---
    # Solo inyectamos el script si hay frecuencia cardíaca y volumen > 0
    if p['hr'] > 0 and p['vol'] > 0:
        intervalo_ms = (60 / p['hr']) * 1000
        # Script JS optimizado para evitar superposición de sonidos
        js_audio = f"""
        <script>
            var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            
            function beep() {{
                if (audioCtx.state === 'suspended') {{ audioCtx.resume(); }}
                
                var osc = audioCtx.createOscillator();
                var gain = audioCtx.createGain();
                
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.type = 'square';
                osc.frequency.value = 750; // Tono Hz típico de monitor
                gain.gain.value = {p['vol']};
                
                osc.start();
                setTimeout(function() {{ osc.stop(); }}, 150); // Duración beep
            }}
            
            // Limpiar intervalo anterior si existe
            if (window.monitorInterval) clearInterval(window.monitorInterval);
            
            // Iniciar nuevo intervalo
            window.monitorInterval = setInterval(beep, {intervalo_ms});
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js_audio, height=0)


# --- 6. EJECUCIÓN PRINCIPAL ---

def main():
    creds, ritmos_db = cargar_secretos()
    
    if not st.session_state.authenticated:
        mostrar_login(creds)
    else:
        mostrar_monitor(ritmos_db)

if __name__ == "__main__":
    main()
