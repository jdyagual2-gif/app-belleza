import os
import json
import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="GlowStudio AI | Salón de Belleza Moderno",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

EXCEL_PATH = r"C:\GlowStudio\Citas_GlowStudio.xlsx"
RECENT_JSON_PATH = r"C:\GlowStudio\cita_reciente.json"

LOCAL_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_EXCEL_PATH = os.path.join(LOCAL_BASE_DIR, "Citas_GlowStudio.xlsx")
LOCAL_JSON_PATH = os.path.join(LOCAL_BASE_DIR, "cita_reciente.json")

def guardar_cita_directa(datos_cita):
    os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)
    if os.path.exists(EXCEL_PATH):
        df_existente = pd.read_excel(EXCEL_PATH)
        df_nuevo = pd.DataFrame([datos_cita])
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = pd.DataFrame([datos_cita])

    df_final.to_excel(EXCEL_PATH, index=False)

    try:
        with open(RECENT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(datos_cita, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

    try:
        df_final.to_excel(LOCAL_EXCEL_PATH, index=False)
        with open(LOCAL_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(datos_cita, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

# ==========================================
# ESTILOS Y DISEÑO NEÓN
# ==========================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');

:root {
    --bg-dark: #0F0F15;
    --card-bg: #1A1A24;
    --card-border: rgba(255, 0, 127, 0.25);
    --primary-neon: #FF007F;
    --secondary-neon: #8A2BE2;
    --gold-accent: #FFD700;
    --cyan-accent: #00F0FF;
    --text-primary: #F8F9FA;
    --text-muted: #A0A5B5;
}

.stApp {
    background-color: var(--bg-dark);
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--text-primary);
}

.neon-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 0.3rem;
    background: linear-gradient(90deg, #FF007F, #FFD700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    filter: drop-shadow(0 0 20px rgba(255, 0, 127, 0.35));
}

.neon-subtitle {
    font-size: 1.02rem;
    color: var(--text-muted);
    margin-bottom: 1.1rem;
}

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-top: 1rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid var(--primary-neon);
    padding-left: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(255, 0, 127, 0.12) !important;
    padding: 1.2rem !important;
    margin-bottom: 1rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background-color: #12121A;
    padding: 10px 14px;
    border-radius: 14px;
    border: 1px solid rgba(255, 0, 127, 0.25);
    margin-bottom: 1rem;
}

.stTabs [data-baseweb="tab"] {
    color: #A0A5B5 !important;
    font-weight: 700;
    font-size: 1.05rem;
    padding: 10px 22px;
    border-radius: 10px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(255, 0, 127, 0.3), rgba(138, 43, 226, 0.4)) !important;
    color: #FFFFFF !important;
    border-bottom: 3px solid var(--primary-neon) !important;
}

.glow-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 20px rgba(255, 0, 127, 0.15);
    margin-bottom: 1rem;
}

.neon-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(255, 0, 127, 0.15);
    color: var(--primary-neon);
    border: 1px solid rgba(255, 0, 127, 0.4);
    margin-right: 6px;
}

.gold-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(255, 215, 0, 0.15);
    color: var(--gold-accent);
    border: 1px solid rgba(255, 215, 0, 0.4);
    margin-right: 6px;
}

.purple-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(138, 43, 226, 0.18);
    color: #BB86FC;
    border: 1px solid rgba(138, 43, 226, 0.45);
    margin-right: 6px;
}

.stButton > button {
    background: linear-gradient(135deg, #FF007F 0%, #8A2BE2 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.3rem !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# ESTADOS DE SESIÓN
# ==========================================
if "selected_stylist" not in st.session_state:
    st.session_state["selected_stylist"] = "Valeria"

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": (
                "¡Hola! 💖 Soy **Bella**, tu asesora personal en **GlowStudio AI**. "
                "\n\n✨ *Dato especial:* Si abonas el **50% de anticipo por transferencia**, "
                "¡obtienes **10% de DESCUENTO AUTO** en tu cita! ¿En qué puedo ayudarte hoy?"
            )
        }
    ]

if "heatmap_stats" not in st.session_state:
    st.session_state["heatmap_stats"] = {
        ("Balayage Neón", "Valeria"): {"satisfaccion": 98, "votos": 260},
        ("Balayage Neón", "Camila"): {"satisfaccion": 74, "votos": 110},
        ("Corte & Styling", "Valeria"): {"satisfaccion": 85, "votos": 145},
        ("Corte & Styling", "Camila"): {"satisfaccion": 92, "votos": 195},
        ("Manicure Gel Gloss", "Valeria"): {"satisfaccion": 68, "votos": 90},
        ("Manicure Gel Gloss", "Camila"): {"satisfaccion": 97, "votos": 280},
        ("Makeup Glow", "Valeria"): {"satisfaccion": 72, "votos": 105},
        ("Makeup Glow", "Camila"): {"satisfaccion": 96, "votos": 240},
        ("Tratamiento Keratina", "Valeria"): {"satisfaccion": 95, "votos": 210},
        ("Tratamiento Keratina", "Camila"): {"satisfaccion": 80, "votos": 125}
    }

SERVICES_CATALOG = {
    "Balayage Neón": {"precio": 160.0, "duracion": "3.5 hrs"},
    "Corte & Styling": {"precio": 45.0, "duracion": "1.0 hr"},
    "Manicure Gel Gloss": {"precio": 55.0, "duracion": "1.5 hrs"},
    "Makeup Glow": {"precio": 95.0, "duracion": "1.5 hrs"},
    "Tratamiento Keratina": {"precio": 120.0, "duracion": "2.5 hrs"}
}

# ==========================================
# ASISTENTE VIRTUAL IA (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("### 💖 Bella IA")
    st.caption("🟢 Asesora en Línea")
    
    chat_container = st.container(height=320)
    with chat_container:
        for msg in st.session_state["chat_messages"]:
            avatar = "💖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    def generate_bella_response(user_input: str) -> str:
        prompt = user_input.lower()
        if any(k in prompt for k in ["descuento", "precio", "promocion", "pago"]):
            return "¡Si abonas el 50% por transferencia obtienes 10% de descuento automático! 💸✨"
        elif "balayage" in prompt:
            return "El Balayage Neón es nuestra especialidad con Valeria (98% satisfacción) 🎨."
        elif "cita" in prompt or "reservar" in prompt:
            return "Puedes reservar en la sección de 'Lookbook & Agendar Cita' abajo. 💖"
        else:
            return f"¡Con gusto te ayudo! Puedes consultar nuestros servicios o agendar tu cita directa."

    side_chat_input = st.chat_input("Escribe a Bella...", key="sidebar_bella_chat")
    if side_chat_input:
        st.session_state["chat_messages"].append({"role": "user", "content": side_chat_input})
        reply = generate_bella_response(side_chat_input)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

# ==========================================
# TÍTULO PRINCIPAL
# ==========================================
st.markdown('<div class="neon-title">GlowStudio AI | Salón de Belleza Moderno</div>', unsafe_allow_html=True)
st.markdown('<div class="neon-subtitle">Don de la belleza impulsado por IA, visagismo inteligente y agendamiento automático.</div>', unsafe_allow_html=True)

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab_experiencia, tab_tendencias = st.tabs([
    "✨ Lookbook & Agendar Cita",
    "📊 Tendencias & Votaciones en Vivo"
])

# ----------------- PESTAÑA 1: LOOKBOOK Y CITAS -----------------
with tab_experiencia:
    st.markdown('<div class="section-title">📸 Lookbook de Tendencias</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown("""
        <div class="glow-card">
            <img src="https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=700&q=80" style="width:100%; height:200px; object-fit:cover; border-radius:12px;" />
            <span class="neon-badge">Colorimetría</span>
            <h4 style="margin:8px 0; color:#FFF;">Balayage Neón & Gloss</h4>
            <p style="font-size:0.85rem; color:#A0A5B5;">Degradados tridimensionales con brillo espejo.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_l2:
        st.markdown("""
        <div class="glow-card">
            <img src="https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=700&q=80" style="width:100%; height:200px; object-fit:cover; border-radius:12px;" />
            <span class="gold-badge">Glamour</span>
            <h4 style="margin:8px 0; color:#FFF;">Makeup Glow HD</h4>
            <p style="font-size:0.85rem; color:#A0A5B5;">Efecto piel de porcelana e iluminación.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_l3:
        st.markdown("""
        <div class="glow-card">
            <img src="https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=700&q=80" style="width:100%; height:200px; object-fit:cover; border-radius:12px;" />
            <span class="purple-badge">Nail Art</span>
            <h4 style="margin:8px 0; color:#FFF;">Manicure Gel Gloss</h4>
            <p style="font-size:0.85rem; color:#A0A5B5;">Esmaltado en gel con acabado cromado.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">👑 Selecciona tu Estilista</div>', unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💖 Seleccionar a Valeria (Master Colorista)", use_container_width=True):
            st.session_state["selected_stylist"] = "Valeria"
            st.rerun()
    with col_s2:
        if st.button("💜 Seleccionar a Camila (Hair & Makeup)", use_container_width=True):
            st.session_state["selected_stylist"] = "Camila"
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-title">📅 Formulario de Reserva</div>', unsafe_allow_html=True)

    col_book_l, col_book_r = st.columns([1.2, 1])

    with col_book_l:
        with st.container(border=True):
            cliente_nombre = st.text_input("Nombre completo:")
            cliente_telefono = st.text_input("Teléfono celular (10 dígitos):", max_chars=10)
            
            stylist_list = ["Valeria", "Camila"]
            s_idx = stylist_list.index(st.session_state["selected_stylist"])
            estilista_elegida = st.selectbox("Estilista asignada:", options=stylist_list, index=s_idx)
            
            servicio_elegido = st.selectbox("Servicio:", options=list(SERVICES_CATALOG.keys()))
            fecha_cita = st.date_input("Fecha:", value=datetime.date.today() + datetime.timedelta(days=1))
            hora_cita = st.selectbox("Hora:", ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"])
            
            metodo_pago_opcion = st.radio(
                "Forma de pago:",
                ["💵 Efectivo en salón", "💳 Transferencia 50% (¡10% DESCUENTO AUTO!)"],
                index=1
            )
            es_transferencia = "Transferencia" in metodo_pago_opcion

    with col_book_r:
        base_price = SERVICES_CATALOG[servicio_elegido]["precio"]
        descuento = round(base_price * 0.10, 2) if es_transferencia else 0.0
        monto_final = round(base_price - descuento, 2)
        
        with st.container(border=True):
            st.markdown("### 💎 Resumen")
            st.write(f"**Servicio:** {servicio_elegido}")
            st.write(f"**Estilista:** {estilista_elegida}")
            st.metric("Precio Base", f"${base_price:.2f} USD")
            if es_transferencia:
                st.metric("Ahorro 10%", f"-${descuento:.2f} USD")
            st.metric("Total Final", f"${monto_final:.2f} USD")
            
            btn_confirm = st.button("💖 Confirmar y Guardar Cita", use_container_width=True)

    if btn_confirm:
        if not cliente_nombre or len(cliente_telefono) != 10:
            st.error("⚠️ Por favor ingresa un nombre y un teléfono válido de 10 dígitos.")
        else:
            payload = {
                "cliente_nombre": cliente_nombre,
                "cliente_telefono": cliente_telefono,
                "estilista": estilista_elegida,
                "servicio": servicio_elegido,
                "metodo_pago": "Transferencia" if es_transferencia else "Efectivo",
                "monto_total": float(monto_final),
                "fecha_hora_cita": f"{fecha_cita} {hora_cita}"
            }
            guardar_cita_directa(payload)
            st.balloons()
            st.success(f"🎉 ¡Cita confirmada con éxito para {cliente_nombre}!")

# ----------------- PESTAÑA 2: TENDENCIAS Y VOTACIONES -----------------
with tab_tendencias:
    st.markdown('<div class="section-title">📊 Mapa de Calor & Satisfacción</div>', unsafe_allow_html=True)
    
    plot_items = []
    for (srv, est), stat in st.session_state["heatmap_stats"].items():
        plot_items.append({"servicio": srv, "estilista": est, "satisfaccion": stat["satisfaccion"], "votos": stat["votos"]})
    
    fig = go.Figure(data=go.Scatter(
        x=[d["estilista"] for d in plot_items],
        y=[d["servicio"] for d in plot_items],
        mode="markers+text",
        text=[f"{d['satisfaccion']}%" for d in plot_items],
        marker=dict(size=[d["votos"]/4 for d in plot_items], color=[d["satisfaccion"] for d in plot_items], colorscale="Plasma", showscale=True)
    ))
    fig.update_layout(paper_bgcolor="rgba(15,15,21,1)", plot_bgcolor="rgba(26,26,36,0.6)", font=dict(color="#FFF"))
    st.plotly_chart(fig, use_container_width=True)