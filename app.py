import streamlit as st
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador SV Procedural",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GESTIÓN DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "tipo_ritmo": "Sinusal", # Opciones: Sinusal, FV, Asistolia
        "hr": 80, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
    }

# ==============================================================================
# FASE 1: LOGIN
# ==============================================================================
if not st.session_state.auth:
    # (Usamos credenciales simples para demo, puedes poner las tuyas de secrets)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔐 Acceso Docente")
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR", type="primary"):
                if u == "simularitmos" and p == "javier":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# ==============================================================================
# FASE 2: SIMULADOR PROCEDURAL
# ==============================================================================
else:
    # CSS CLÍNICO (MONITOR NEGRO / PANEL BLANCO)
    st.markdown("""
    <style>
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* Panel Docente Blanco */
        section[data-testid="stSidebar"] { background-color: white !important; }
        section[data-testid="stSidebar"] * { color: black !important; }
        
        /* Cajas Monitor */
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
        
        /* Botón Recuperar Panel */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background: white !important; border: 2px solid #ccc;
            z-index: 999999;
        }
        
        header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

    # --- PANEL DOCENTE ---
    with st.sidebar:
        st.title("🎛️ Generador de Ritmos")
        
        with st.form("controls"):
            # AHORA SELECCIONAMOS TIPO DE ONDA, NO VIDEO
            tipo_ritmo = st.selectbox("Tipo de Ritmo", ["Sinusal", "Fibrilación Ventricular", "Asistolia"])
            
            st.markdown("---")
            p = st.session_state.params
            
            # EL CAMBIO DE HR AHORA AFECTA LA VELOCIDAD DE LA ONDA
            v_hr = st.slider("Frecuencia Cardíaca", 0, 300, p["hr"])
            v_spo2 = st.slider("SpO2 (%)", 0, 100, p["spo2"])
            
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            v_rr = st.slider("FR", 0, 60, p["rr"])
            
            if st.form_submit_button("🚀 APLICAR CAMBIOS", type="primary"):
                st.session_state.params = {
                    "tipo_ritmo": tipo_ritmo,
                    "hr": v_hr, "spo2": v_spo2,
                    "pas": v_pas, "pad": v_pad, "rr": v_rr
                }
                st.rerun()
        
        st.info("💡 Nota: En 'Sinusal', si subes la FC, el dibujo se acelera automáticamente.")

    # --- MONITOR ESTUDIANTE ---
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
        # MOTOR DE ECG GENERATIVO (JavaScript + Canvas)
        # ======================================================================
        # Pasamos las variables de Python a JS
        ritmo_js = d['tipo_ritmo']
        hr_js = d['hr']

        components.html(f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; background-color: #000; overflow: hidden;">
            <canvas id="ecgCanvas"></canvas>
            
            <script>
                const canvas = document.getElementById('ecgCanvas');
                const ctx = canvas.getContext('2d');
                
                // Ajustar canvas al tamaño de la ventana
                function resize() {{
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;
                }}
                window.addEventListener('resize', resize);
                resize();

                // VARIABLES CLÍNICAS (Vienen de Python)
                let heartRate = {hr_js}; 
                let rhythmType = "{ritmo_js}"; // 'Sinusal', 'Fibrilación Ventricular', 'Asistolia'
                
                // Configuración de dibujo
                let x = 0;
                let speed = 2; // Velocidad base de barrido
                let lastY = canvas.height / 2;
                
                // Datos de un latido normal (P-QRS-T simplificado)
                // Valores entre -1 y 1
                const pqrst = [
                    0, 0, 0, 0.05, 0.1, 0, 0, // P wave
                    0, -0.1, 1.0, -0.4, 0,    // QRS complex (High spike)
                    0, 0, 0.15, 0.2, 0.15, 0, 0, 0 // T wave
                ];
                
                let beatIndex = 0;
                let framesPerBeat = 0;
                let currentFrameInBeat = 0;
                let isBeating = false;

                function draw() {{
                    // Velocidad de barrido: Ajustamos según HR para que se vea más rápido
                    // Si HR es 60, speed 2. Si HR es 120, speed 4.
                    let pixelSpeed = (window.innerWidth / 300) * (heartRate / 60);
                    if (pixelSpeed < 1) pixelSpeed = 1;
                    if (rhythmType === 'Asistolia') pixelSpeed = 2; // Velocidad fija para asisto

                    // Efecto de barrido (Borrar un poco adelante)
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';
                    ctx.fillRect(x, 0, pixelSpeed + 10, canvas.height); // Borra barra negra

                    // Calcular nueva Y
                    let y = canvas.height / 2;
                    let noise = (Math.random() - 0.5) * 5; // Ruido base

                    if (rhythmType === 'Asistolia') {{
                        y += noise;
                    }} 
                    else if (rhythmType === 'Fibrilación Ventricular') {{
                        // Caos total: Ondas seno aleatorias
                        y += Math.sin(Date.now() / 100) * 50 + noise * 5;
                    }} 
                    else {{ 
                        // RITMO SINUSAL (Generación PQRST)
                        
                        // Si no estamos dibujando un latido, ver si toca empezar uno
                        if (!isBeating) {{
                            // Probabilidad de iniciar latido basada en HR
                            // 60 BPM = 1 latido cada 1000ms
                            // A 60FPS, 1 latido cada 60 frames
                            let framesBetweenBeats = (60 / heartRate) * 60; 
                            
                            // Usamos un contador simple o probabilidad
                            if (Math.random() < (1 / framesBetweenBeats)) {{
                                isBeating = true;
                                beatIndex = 0;
                            }}
                        }}

                        if (isBeating) {{
                            // Dibujar la forma del latido
                            // Interpolamos el array pqrst
                            let sampleIndex = Math.floor(beatIndex);
                            let val = pqrst[sampleIndex];
                            
                            // Escalar amplitud (Alto del QRS)
                            y -= val * (canvas.height * 0.4); 
                            
                            // Avanzar en el array
                            beatIndex += 0.5; // Velocidad de dibujo de la onda en sí
                            if (beatIndex >= pqrst.length) {{
                                isBeating = false;
                            }}
                        }}
                        y += noise; // Añadir un poco de ruido eléctrico
                    }}

                    // Dibujar línea verde
                    ctx.beginPath();
                    ctx.strokeStyle = '#00ff00';
                    ctx.lineWidth = 3;
                    ctx.lineCap = 'round';
                    ctx.moveTo(x, lastY); // Desde punto anterior
                    
                    // Avanzar X
                    x += pixelSpeed;
                    if (x > canvas.width) {{
                        x = 0;
                        ctx.moveTo(0, y); // Resetear sin dibujar línea cruzada
                    }}
                    
                    ctx.lineTo(x, y); // Hasta punto nuevo
                    ctx.stroke();

                    lastY = y;

                    requestAnimationFrame(draw);
                }}

                // Iniciar animación
                draw();

            </script>
        </body>
        </html>
        """, height=700)
