import streamlit as st
import streamlit.components.v1 as components
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Pro",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BASE DE DATOS DE ONDAS (SUAVIZADA Y DE ALTA RESOLUCIÓN) ---
# He aumentado la densidad de puntos para evitar saltos bruscos.
ECG_DATA = {
    "Ritmo Sinusal Normal": [
        0, 0, 0, 0, 0.02, 0.05, 0.08, 0.05, 0.02, 0, 0, # P
        0, 0, -0.05, # PR
        -0.1, 1.0, -0.4, # QRS (Pico alto y limpio)
        0, 0.05, 0.15, 0.2, 0.25, 0.2, 0.15, 0.05, 0, # T
        0, 0, 0, 0, 0 # Isoeléctrica
    ],
    "Bradicardia Sinusal": [
        0, 0, 0, 0.03, 0.06, 0.03, 0, 0, 0, 0, # P
        -0.05, 0.9, -0.3, # QRS
        0, 0, 0.1, 0.2, 0.1, 0, 0, 0, 0, 0, 0, 0 # T larga + pausa
    ],
    "Taquicardia Sinusal": [
        0.05, 0.1, 0.05, # P rápida
        -0.1, 1.0, -0.5, # QRS estrecho
        0.05, 0.2, 0.05, 0 # T fusionada
    ],
    "Fibrilación Auricular (FA)": [
        0.02, -0.03, 0.04, -0.02, 0.03, 0.05, -0.02, # f waves (ruido)
        -0.1, 0.8, -0.2, # QRS irregular amplitud
        0.03, -0.04, 0.02, 0.05, -0.03, 0.02,
        0.04, -0.02, 0.03
    ],
    "Taquicardia Ventricular (TV)": [
        -0.4, 0.2, 0.8, 1.2, 0.6, 0.0, -0.6, -1.0, -0.6, -0.2
    ],
    "Fibrilación Ventricular (FV)": [
        0.2, 0.5, 0.2, -0.3, -0.6, -0.2, 0.4, 0.7, 0.3, -0.1, -0.5
    ],
    "Asistolia": [
        0.01, -0.01, 0.005, -0.005, 0.01, 0, 0.01, -0.01
    ]
}

# --- 3. ESTADO DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": "Ritmo Sinusal Normal",
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
    }

# ==============================================================================
# FASE 1: LOGIN
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

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div class='login-card'><h2>🏥 Control Docente</h2></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", type="primary", use_container_width=True):
                if u == "simularitmos" and p == "javier":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Error de acceso")

# ==============================================================================
# FASE 2: SIMULADOR (TRAZADO CONTINUO)
# ==============================================================================
else:
    st.markdown("""
    <style>
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* Panel Docente Blanco */
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 3px solid #999; }
        section[data-testid="stSidebar"] * { color: #000000 !important; }
        
        /* Botón Menú */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background-color: white !important;
            border: 2px solid #ccc; z-index: 9999999;
        }
        
        /* Cajas Monitor */
        .vital-box {
            background: #080808; border-left: 8px solid;
            padding: 5px 15px; margin-bottom: 8px; height: 16vh;
            display: flex; flex-direction: column; justify-content: center;
        }
        .hr { border-color: #00ff00; color: #00ff00; }
        .spo2 { border-color: #ffff00; color: #ffff00; }
        .bp { border-color: #ff3333; color: #ff3333; }
        .rr { border-color: #00ffff; color: #00ffff; }
        
        .val { font-size: 75px; font-weight: bold; line-height: 1; text-align: right; text-shadow: 0 0 15px currentColor; }
        .lbl { font-size: 16px; opacity: 0.8; }
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # --- PANEL DOCENTE ---
    with st.sidebar:
        st.title("🎛️ Configuración")
        with st.form("control_panel"):
            sel_ritmo = st.selectbox("Ritmo (PhysioNet Data)", list(ECG_DATA.keys()))
            
            p = st.session_state.params
            v_hr = st.slider("Frecuencia Cardíaca", 0, 300, p["hr"])
            st.caption("ℹ️ La FC controla la velocidad del barrido.")
            
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            v_rr = st.slider("FR", 0, 60, p["rr"])
            
            if st.form_submit_button("🚀 APLICAR CAMBIOS", type="primary"):
                st.session_state.params = {
                    "ritmo": sel_ritmo, "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr
                }
                st.rerun()
        
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
        # Preparar datos para JS
        raw_data = json.dumps(ECG_DATA[d['ritmo']])
        js_hr = d['hr']
        
        components.html(f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; background-color: #000; overflow: hidden;">
            <canvas id="ecgCanvas"></canvas>
            
            <script>
                const canvas = document.getElementById('ecgCanvas');
                const ctx = canvas.getContext('2d');
                
                function resize() {{
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;
                }}
                window.addEventListener('resize', resize);
                resize();

                // DATOS
                const ecgPattern = {raw_data};
                const heartRate = {js_hr};
                
                // VARIABLES DE ESTADO (CRÍTICO PARA CONTINUIDAD)
                let xPos = 0;
                let lastY = canvas.height / 2; // Guardamos la última Y
                let patternIndex = 0;
                
                // Configuración Visual
                ctx.strokeStyle = '#00ff00'; // Verde Monitor
                ctx.lineWidth = 3;
                ctx.shadowBlur = 10; // Efecto Glow (Neón)
                ctx.shadowColor = '#00ff00';
                ctx.lineJoin = 'round'; // Suaviza las esquinas
                ctx.lineCap = 'round';

                // Cálculo de velocidad de lectura
                // Base: 60 BPM recorre el patrón normal
                let speedFactor = (heartRate / 60);
                if (speedFactor < 0.1) speedFactor = 0.1;
                
                // Velocidad horizontal en píxeles por frame
                let horizontalSpeed = 3; 

                function draw() {{
                    // 1. EFECTO BARRIDO (Borrar lo que está justo adelante)
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';
                    // Borramos una franja un poco más ancha que el salto para asegurar limpieza
                    ctx.fillRect(xPos, 0, horizontalSpeed + 20, canvas.height); 

                    // 2. DIBUJO CONTINUO
                    ctx.beginPath();
                    
                    // CRUCIAL: Empezar EXACTAMENTE donde terminó el frame anterior
                    ctx.moveTo(xPos, lastY);

                    // Calculamos nueva posición X
                    xPos += horizontalSpeed;

                    // Interpolamos el valor Y del array de datos
                    let idx = Math.floor(patternIndex) % ecgPattern.length;
                    let val = ecgPattern[idx];
                    
                    // Escala vertical (Amplitud)
                    let newY = (canvas.height / 2) - (val * 180); 

                    // Ruido eléctrico muy leve para realismo
                    newY += (Math.random() - 0.5) * 2;

                    // Trazar línea
                    ctx.lineTo(xPos, newY);
                    ctx.stroke();

                    // Actualizar memoria para el siguiente frame
                    lastY = newY;
                    
                    // Avanzar en el array de datos
                    patternIndex += (speedFactor * 0.5); // 0.5 es un factor de suavizado de lectura

                    // 3. RESET DE PANTALLA (WRAP AROUND)
                    if (xPos >= canvas.width) {{
                        xPos = 0;
                        // Al saltar al inicio, debemos evitar tirar una línea cruzada
                        // Así que solo movemos el cursor sin dibujar
                        ctx.beginPath();
                        ctx.moveTo(0, newY);
                        lastY = newY; // Reiniciamos la referencia Y
                    }}

                    requestAnimationFrame(draw);
                }}

                draw();
            </script>
        </body>
        </html>
        """, height=700)

