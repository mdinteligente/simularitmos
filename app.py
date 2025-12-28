import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Simulador Clínico Pro",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BASE DE DATOS DE MORFOLOGÍAS (SVG PATHS) ---
# Estas son instrucciones de dibujo vectorial. Son fijas y perfectas.
# No se deforman con la velocidad.

RITMOS_SVG = {
    "Ritmo Sinusal Normal": {
        # Dibuja P, QRS, T con proporciones médicas exactas
        "path": "M 0 50 L 10 50 Q 15 40 20 50 L 25 50 L 28 45 L 35 90 L 40 20 L 45 55 L 50 50 L 60 50 Q 75 35 90 50 L 100 50",
        "color": "#00ff00", # Verde
        "width": 100 # Ancho del latido en unidades relativas
    },
    "Fibrilación Auricular": {
        # Ondas f basales + QRS irregular
        "path": "M 0 50 Q 5 48 10 52 Q 15 48 20 52 L 25 50 L 35 90 L 40 20 L 45 55 L 50 52 Q 55 48 60 52 Q 65 48 70 52 Q 75 48 80 52",
        "color": "#00ff00",
        "width": 80
    },
    "Taquicardia Ventricular": {
        # Ondas anchas y monomórficas (Dientes de sierra grandes)
        "path": "M 0 50 Q 20 100 40 50 Q 60 0 80 50",
        "color": "#ff0000", # Rojo alerta opcional, o verde
        "width": 80
    },
    "Fibrilación Ventricular": {
        # Caos ondulante
        "path": "M 0 50 Q 10 20 20 50 Q 30 80 40 50 Q 50 10 60 50 Q 70 90 80 50",
        "color": "#00ff00",
        "width": 80
    },
    "Bloqueo de Rama Izquierda (BRIHH)": {
        # QRS ancho y mellado ("Orejas de conejo")
        "path": "M 0 50 L 10 50 Q 15 40 20 50 L 25 50 L 30 20 L 35 30 L 40 20 L 45 55 L 50 50 L 60 50 Q 75 35 90 50",
        "color": "#00ff00",
        "width": 110
    },
    "Asistolia": {
        # Línea casi plana con mínimo ruido
        "path": "M 0 50 L 100 50",
        "color": "#00ff00",
        "width": 100
    },
     "Infarto Agudo (IAM con Supra ST)": {
        # QRS normal + Elevación brutal del punto J y onda T
        "path": "M 0 50 L 10 50 Q 15 40 20 50 L 25 50 L 35 90 L 40 20 L 45 40 Q 60 20 80 40 L 90 50",
        "color": "#00ff00", # Verde
        "width": 100
    }
}

# --- 3. ESTADO DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "params" not in st.session_state:
    st.session_state.params = {
        "ritmo": "Ritmo Sinusal Normal",
        "hr": 60, "spo2": 98, "pas": 120, "pad": 80, "rr": 16
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
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card'><h2>🏥 Acceso Docente</h2></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", type="primary", use_container_width=True):
                if u == "simularitmos" and p == "javier":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Error")

# ==============================================================================
# FASE 2: MONITOR DE ALTA FIDELIDAD
# ==============================================================================
else:
    # ESTILOS CLÍNICOS
    st.markdown("""
    <style>
        .stApp { background-color: #000000; color: white; font-family: 'Consolas', monospace; }
        
        /* Sidebar Blanco */
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 3px solid #999; }
        section[data-testid="stSidebar"] * { color: #000000 !important; }
        
        /* Botón Menú */
        [data-testid="stSidebarCollapsedControl"] {
            color: black !important; background: white !important;
            border: 2px solid #ccc; z-index: 999999;
        }
        
        /* Cajas Signos Vitales */
        .vital-box {
            background: #080808; border-left: 8px solid;
            padding: 5px 15px; margin-bottom: 8px; height: 16vh;
            display: flex; flex-direction: column; justify-content: center;
        }
        .hr { border-color: #00ff00; color: #00ff00; }
        .spo2 { border-color: #ffff00; color: #ffff00; }
        .bp { border-color: #ff3333; color: #ff3333; }
        .rr { border-color: #00ffff; color: #00ffff; }
        
        .val { font-size: 75px; font-weight: bold; line-height: 1; text-align: right; text-shadow: 0 0 10px currentColor; }
        .lbl { font-size: 16px; opacity: 0.8; }
        footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

    # --- PANEL DOCENTE ---
    with st.sidebar:
        st.title("🎛️ Generador Vectorial")
        with st.form("control_panel"):
            sel_ritmo = st.selectbox("Morfología", list(RITMOS_SVG.keys()))
            
            p = st.session_state.params
            v_hr = st.slider("Frecuencia Cardíaca", 20, 250, p["hr"])
            st.caption("ℹ️ Al subir la FC, el ritmo se acelera sin deformar el QRS.")
            
            v_spo2 = st.slider("SpO2", 0, 100, p["spo2"])
            c1, c2 = st.columns(2)
            with c1: v_pas = st.number_input("PAS", 0, 300, p["pas"])
            with c2: v_pad = st.number_input("PAD", 0, 200, p["pad"])
            v_rr = st.slider("FR", 0, 60, p["rr"])
            
            if st.form_submit_button("🚀 APLICAR", type="primary"):
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
        # MOTOR SVG ANIMADO (LA SOLUCIÓN A LA MORFOLOGÍA)
        # ======================================================================
        
        # 1. Obtenemos el dibujo vectorial del latido seleccionado
        svg_data = RITMOS_SVG[d['ritmo']]
        path_d = svg_data["path"]
        beat_width = svg_data["width"]
        
        # 2. Cálculos Matemáticos para NO DEFORMAR
        # Heart Rate (BPM) -> Latidos por segundo (Hz)
        bps = d['hr'] / 60.0 
        
        # Duración de un ciclo completo en segundos
        cycle_duration = 1 / bps if bps > 0 else 0
        
        # CSS Animation Duration: Controla qué tan rápido pasa la animación
        # Hacemos que la animación de "desplazamiento" coincida con la FC
        anim_duration = f"{cycle_duration}s"
        
        # Renderizado HTML/CSS/SVG
        components.html(f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ background: #000; margin: 0; overflow: hidden; }}
            
            /* Contenedor del ECG */
            .ecg-container {{
                width: 100%;
                height: 100vh;
                display: flex;
                align-items: center;
                /* El fondo es una cuadrícula milimétrica sutil */
                background-image: 
                    linear-gradient(rgba(0, 255, 0, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 255, 0, 0.1) 1px, transparent 1px);
                background-size: 20px 20px;
            }}

            /* La línea del ECG */
            .ecg-line {{
                height: 300px; /* Altura de la onda */
                width: 100%;
                
                /* AQUÍ ESTÁ EL TRUCO: USAMOS UN PATRÓN SVG REPETITIVO */
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {beat_width} 100' preserveAspectRatio='none'%3E%3Cpath d='{path_d}' fill='none' stroke='%2300ff00' stroke-width='2' vector-effect='non-scaling-stroke'/%3E%3C/svg%3E");
                
                background-repeat: repeat-x; /* Se repite infinitamente */
                background-size: {beat_width * 3}px 100%; /* Tamaño fijo del latido (NO SE DEFORMA) */
                background-position: 0 center;
                
                /* Animación de desplazamiento */
                animation: slideLeft {anim_duration} linear infinite;
            }}

            /* Definición de la animación: Mover el fondo hacia la izquierda */
            @keyframes slideLeft {{
                from {{ background-position: 0 center; }}
                to {{ background-position: -{beat_width * 3}px center; }}
            }}
            
            /* Efecto de desvanecimiento a la derecha (Barrido) */
            .fade-overlay {{
                position: absolute;
                top: 0; right: 0;
                width: 100px;
                height: 100%;
                background: linear-gradient(to right, transparent, #000);
            }}
        </style>
        </head>
        <body>
            <div class="ecg-container">
                <div class="ecg-line"></div>
                <div class="fade-overlay"></div>
            </div>
        </body>
        </html>
        """, height=700)

