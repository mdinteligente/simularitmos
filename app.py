import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Urgencias",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GESTIÓN DE SECRETOS (Simulada para estabilidad) ---
# En producción, usa st.secrets. Aquí usamos diccionarios directos para que te funcione YA.
CREDS = {"username": "simularitmos", "password": "javier"}

# --- 3. ESTADO DE LA SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": "Ritmo Sinusal",
        "hr": 60, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
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
                if u == CREDS["username"] and p == CREDS["password"]:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# ==============================================================================
# FASE 2: SIMULADOR (CHARTIST.JS)
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
        st.title("🎛️ Generador ECG")
        
        with st.form("control_panel"):
            # Opciones matemáticas generativas
            sel_ritmo = st.selectbox("Tipo de Onda", ["Ritmo Sinusal", "Taquicardia Sinusal", "Fibrilación Ventricular", "Asistolia"])
            
            p = st.session_state.params
            
            # EL SLIDER DE FC AHORA SÍ CAMBIA LA VELOCIDAD REAL
            v_hr = st.slider("Frecuencia Cardíaca (LPM)", 0, 250, p["hr"])
            
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
        
        st.info("ℹ️ La gráfica ahora es generada por código (Chartist.js). Si subes la FC, las ondas se juntarán más.")

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
        # INTEGRACIÓN CHARTIST.JS
        # ======================================================================
        
        # Preparamos variables para JS
        js_hr = d['hr']
        js_ritmo = d['ritmo']
        
        components.html(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/chartist.js/latest/chartist.min.css">
            <script src="https://cdn.jsdelivr.net/chartist.js/latest/chartist.min.js"></script>
            <style>
                body {{ background-color: #000; margin: 0; overflow: hidden; }}
                
                /* Estilo de la línea del ECG */
                .ct-series-a .ct-line {{
                    stroke: #00ff00; /* Verde Monitor */
                    stroke-width: 3px;
                    stroke-linecap: round;
                }}
                
                /* Ocultar rejillas y ejes para realismo */
                .ct-grid {{ stroke: none; }}
                .ct-label {{ display: none; }}
                
                #chart {{
                    height: 95vh;
                    width: 100%;
                }}
            </style>
        </head>
        <body>
            <div id="chart" class="ct-chart"></div>

            <script>
                // --- 1. DATOS DE ALTA FIDELIDAD (COMPLEJO PQRST REAL) ---
                // Estos puntos dibujan un latido perfecto. No son aleatorios.
                const pqrst_complex = [
                    0,0,0,0, 
                    0.05, 0.1, 0.15, 0.1, 0.05, 0, // Onda P suave
                    0,0, -0.1, // Segmento PR
                    -0.2, 1.2, -0.4, // QRS (Pico alto y agudo)
                    0, 0, 0.05, 0.15, 0.25, 0.3, 0.25, 0.15, 0.05, 0, // Onda T ancha
                    0,0,0 // Isoeléctrica final
                ];

                // Configuración clínica
                var heartRate = {js_hr}; 
                var rhythmType = "{js_ritmo}";
                
                // Variables de simulación
                var dataPoints = [];
                var maxPoints = 200; // Puntos visibles en pantalla (ventana de tiempo)
                var timeStep = 0;
                
                // Inicializar array vacío
                for(var i=0; i<maxPoints; i++) dataPoints.push(0);

                // --- 2. CONFIGURAR GRÁFICO ---
                var chart = new Chartist.Line('#chart', {{
                    series: [dataPoints]
                }}, {{
                    low: -0.5,
                    high: 1.5,
                    showArea: false,
                    showPoint: false, // No mostrar puntos, solo línea
                    fullWidth: true,
                    axisX: {{ showGrid: false, showLabel: false, offset: 0 }},
                    axisY: {{ showGrid: false, showLabel: false, offset: 0 }}
                }});

                // --- 3. MOTOR DE GENERACIÓN DE ONDA ---
                var complexIndex = 0;
                var isBeating = false;
                var samplesSinceLastBeat = 0;

                function updateECG() {{
                    var newVal = 0;
                    var noise = (Math.random() - 0.5) * 0.05; // Ruido base ligero

                    if (rhythmType === "Asistolia") {{
                        newVal = noise; // Solo ruido
                    }} 
                    else if (rhythmType === "Fibrilación Ventricular") {{
                        // Ondas caóticas grandes y rápidas
                        newVal = (Math.sin(timeStep / 2) * 0.5) + (Math.cos(timeStep / 1.5) * 0.3) + noise;
                    }} 
                    else {{ 
                        // RITMOS SINUSALES / TAQUI
                        // Calculamos cuándo toca el siguiente latido según HR
                        // A 60FPS (aprox), 60LPM = 1 latido cada 60 frames
                        // Ajustamos factor de velocidad
                        var framesPerBeat = (60 / heartRate) * 50; // Calibración de velocidad
                        
                        if (!isBeating && samplesSinceLastBeat > framesPerBeat) {{
                            isBeating = true;
                            complexIndex = 0;
                            samplesSinceLastBeat = 0;
                        }}

                        if (isBeating) {{
                            newVal = pqrst_complex[complexIndex];
                            complexIndex++;
                            if (complexIndex >= pqrst_complex.length) {{
                                isBeating = false;
                            }}
                        }}
                        newVal += noise;
                        samplesSinceLastBeat++;
                    }}

                    // EFECTO SCROLL: Quitamos el primero, agregamos el nuevo
                    dataPoints.shift();
                    dataPoints.push(newVal);

                    // Renderizar
                    chart.update({{ series: [dataPoints] }});
                    
                    timeStep++;
                    
                    // Control de velocidad de refresco (Simular monitor)
                    // HR alto = refresco más rápido para suavidad
                    var refreshRate = (heartRate > 100) ? 20 : 40;
                    setTimeout(updateECG, refreshRate);
                }}

                // Iniciar motor
                updateECG();

            </script>
        </body>
        </html>
        """, height=700)
