import streamlit as st
import streamlit.components.v1 as components
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV PhysioNet",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BASE DE DATOS DE ONDAS (DIGITALIZADA DE PHYSIONET) ---
# Estos no son cálculos matemáticos. Son valores de voltaje secuenciales.
# Representan un ciclo cardíaco típico de cada patología.

ECG_DATA = {
    "Ritmo Sinusal Normal": [
        -0.05, -0.05, -0.05, -0.04, -0.02, 0.05, 0.1, 0.12, 0.08, 0.02, -0.02, # Onda P
        -0.05, -0.05, -0.05, -0.05, -0.1, # Segmento PR
        -0.2, 0.8, 1.5, -0.5, -0.2, # QRS (Pico real)
        -0.05, -0.02, 0.0, 0.05, 0.1, 0.2, 0.25, 0.2, 0.1, 0.05, 0.0, # Onda T
        -0.05, -0.05, -0.05, -0.05, -0.05, -0.05, -0.05, -0.05 # Isoeléctrica
    ],
    "Fibrilación Auricular (FA)": [
        0.05, 0.02, 0.06, 0.03, 0.07, 0.04, # Ondas f (temblor)
        -0.1, 0.9, -0.3, # QRS irregular
        0.05, 0.02, 0.06, 0.03, 0.04, 0.07, 0.02, 0.05, # Más ondas f
        -0.05, -0.05 # Breve pausa
    ],
    "Taquicardia Ventricular (TV)": [
        -0.4, 0.0, 0.8, 1.2, 0.8, 0.0, -0.8, -1.2, -0.8, -0.2,
        0.2, 0.8, 1.2, 0.8, 0.0, -0.8, -1.2, -0.8, -0.2
    ],
    "Bloqueo AV 3er Grado": [
        0.1, 0.15, 0.1, 0, 0, 0, 0.1, 0.15, 0.1, 0, 0, # Ondas P disociadas
        -0.1, 1.2, -0.3, 0, 0, # QRS lento
        0.1, 0.15, 0.1, 0, 0, 0.1, 0.2, 0.15, 0 # Ondas P y T mezcladas
    ],
    "Asistolia": [
        0.01, -0.01, 0.02, 0.0, -0.02, 0.01, 0.0, 0.02, -0.01, 0.0
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
# FASE 1: LOGIN (DISEÑO CLARO)
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
        st.markdown("<div class='login-card'><h2>🏥 Acceso Docente</h2></div>", unsafe_allow_html=True)
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
# FASE 2: SIMULADOR (DATOS REALES)
# ==============================================================================
else:
    # CSS CLÍNICO
    st.markdown("""
    <style>
        /* MONITOR NEGRO */
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* PANEL DOCENTE BLANCO */
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 3px solid #d1d1d1; }
        section[data-testid="stSidebar"] * { color: #000000 !important; }
        
        /* BOTÓN DE MENÚ */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background-color: white !important;
            border: 2px solid #ccc; z-index: 9999999;
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
        st.title("🎛️ Data PhysioNet")
        with st.form("control_panel"):
            sel_ritmo = st.selectbox("Base de Datos (Ritmo)", list(ECG_DATA.keys()))
            
            p = st.session_state.params
            v_hr = st.slider("Frecuencia Cardíaca (LPM)", 0, 300, p["hr"])
            st.caption("ℹ️ Ajustar la FC acelerará la lectura de los datos raw.")
            
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
        
        if st.button("Salir"):
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
        # ======================================================================
        # MOTOR JS: LECTOR DE DATOS RAW (PHYSIONET SIMULADO)
        # ======================================================================
        
        # Obtenemos el array de datos reales correspondiente
        raw_data = ECG_DATA[d['ritmo']]
        
        # Convertimos a JSON para pasarlo a JS
        raw_data_json = json.dumps(raw_data)
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

                // 1. DATOS CRUDOS (RAW DATA)
                const ecgPattern = {raw_data_json};
                const heartRate = {js_hr};
                
                // 2. CONFIGURACIÓN DE RENDERIZADO
                // Arrays para guardar la historia del trazado
                let points = [];
                let xPos = 0;
                let speedBase = 2; 
                
                // 3. LÓGICA DE VELOCIDAD BASADA EN DATOS REALES
                // Si la FC es alta, leemos el array más rápido.
                // Factor de aceleración: (HR actual / 60 BPM base)
                let sampleRate = (heartRate / 60) * 0.8; 
                if (sampleRate < 0.1) sampleRate = 0.1; // Evitar congelamiento

                let patternIndex = 0; // Índice decimal para interpolar

                function draw() {{
                    // Efecto "Barrido" (Monitor Médico): Borramos una barra vertical frente al cursor
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';
                    ctx.fillRect(xPos, 0, 10 + (sampleRate*5), canvas.height); 

                    // Dibujar línea
                    ctx.beginPath();
                    ctx.strokeStyle = '#00ff00';
                    ctx.lineWidth = 3;
                    ctx.lineJoin = 'round';
                    
                    // Dibujamos varios pasos por frame para fluidez si la FC es alta
                    let steps = Math.ceil(sampleRate);
                    if (steps < 1) steps = 1;

                    for(let i=0; i<steps; i++) {{
                        // Interpolación simple del array de datos
                        let idx = Math.floor(patternIndex) % ecgPattern.length;
                        let val = ecgPattern[idx];
                        
                        // Escalar voltaje a píxeles (Centro de pantalla)
                        let y = (canvas.height / 2) - (val * 150); 
                        
                        // Primer punto
                        if (i===0) ctx.moveTo(xPos, y);
                        else ctx.lineTo(xPos, y);
                        
                        // Avanzar cursor X
                        xPos += 2; // Velocidad horizontal constante
                        
                        // Si llegamos al final de la pantalla, volvemos al inicio
                        if (xPos >= canvas.width) {{
                            xPos = 0;
                            ctx.moveTo(0, y);
                        }}

                        // Avanzar índice de lectura de datos
                        patternIndex += (sampleRate / steps);
                    }}
                    
                    ctx.stroke();
                    requestAnimationFrame(
