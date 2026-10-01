import os
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import plotly.express as px
from PIL import Image
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y BASE DE DATOS
# ==========================================
st.set_page_config(
    page_title="GlowStudio AI | Luxury Salon & Spa",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "glowstudio.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Recrear tabla si falta columna imagen_url
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nickname TEXT,
                    rol TEXT,
                    cedula TEXT,
                    estado_pago TEXT,
                    foto_url TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    categoria TEXT,
                    precio REAL,
                    disponible INTEGER,
                    es_combo INTEGER,
                    imagen_url TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_email TEXT,
                    cliente_nombre TEXT,
                    empleado TEXT,
                    servicio TEXT,
                    fecha TEXT,
                    hora TEXT,
                    metodo_pago TEXT,
                    monto_total REAL,
                    estado TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS resenas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nombre TEXT,
                    empleado TEXT,
                    estrellas INTEGER,
                    comentario TEXT,
                    bloqueado INTEGER,
                    fecha TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS preguntas_escaladas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_email TEXT,
                    pregunta TEXT,
                    fecha_hora TEXT,
                    respuesta TEXT,
                    atendido INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto TEXT,
                    cantidad INTEGER,
                    precio_unitario REAL)''')
    
    # Cargar datos por defecto
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('jdyagual2@tes.edu.ec', 'SuperAdmin', 'admin', '0000000000', 'Al Día', '')")
        c.execute("INSERT INTO usuarios VALUES ('valeria@glowstudio.ai', 'Valeria (Master Colorista)', 'empleado', '0987654321', 'Al Día', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400')")
        c.execute("INSERT INTO usuarios VALUES ('camila@glowstudio.ai', 'Camila (Makeup & Stylist)', 'empleado', '0912345678', 'Al Día', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400')")

    c.execute("SELECT COUNT(*) FROM servicios")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO servicios (nombre, categoria, precio, disponible, es_combo, imagen_url) VALUES (?, ?, ?, ?, ?, ?)", [
            ("Balayage Neón", "Colorimetría", 160.0, 1, 0, "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600"),
            ("Makeup Glow HD", "Maquillaje", 95.0, 1, 0, "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600"),
            ("Manicure Gel Gloss", "Uñas", 55.0, 1, 0, "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=600"),
            ("Corte & Visagismo", "Corte", 45.0, 1, 0, "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600"),
            ("Tratamiento Keratina", "Capilar", 120.0, 1, 0, "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=600"),
            ("Combo Glam: Balayage + Makeup Glow", "Combos", 220.0, 1, 1, "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=600"),
            ("Combo VIP: Corte + Keratina + Manicure", "Combos", 190.0, 1, 1, "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=600")
        ])

    c.execute("SELECT COUNT(*) FROM resenas")
    if c.fetchone()[0] == 0:
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        c.executemany("INSERT INTO resenas (cliente_nombre, empleado, estrellas, comentario, bloqueado, fecha) VALUES (?, ?, ?, ?, ?, ?)", [
            ("María González", "Valeria (Master Colorista)", 5, "¡El Balayage Neón superó mis expectativas! La atención fue impecable y el salón súper elegante.", 0, hoy_str),
            ("Sofía Torres", "Camila (Makeup & Stylist)", 5, "El Makeup Glow HD duró toda la noche intacto en mi evento. ¡100% recomendadas!", 0, hoy_str),
            ("Lucía Méndez", "Valeria (Master Colorista)", 5, "Valeria es una experta en colorimetría, entendió exactamente lo que quería para mi cabello.", 0, hoy_str),
            ("Andrea P.", "Camila (Makeup & Stylist)", 4, "Súper buena experiencia, el manicure de gel con brillo espejo quedó precioso.", 0, hoy_str)
        ])

    c.execute("SELECT COUNT(*) FROM inventario")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO inventario (producto, cantidad, precio_unitario) VALUES (?, ?, ?)", [
            ("Tinte Decolorante Neón (Tubos)", 45, 12.50),
            ("Esmalte Gel Gloss Cromo", 60, 8.00),
            ("Mascarilla Keratina Botox", 18, 35.00),
            ("Base HD Maquillaje Glow", 22, 28.00)
        ])

    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. ESTILOS CSS LUXURY DARK MODE
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');

.stApp {
    background-color: #0B0B10;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #F8F9FA;
}

.brand-header {
    font-family: 'Space Grotesk', sans-serif;
    background: linear-gradient(90deg, #FF007F, #FFD700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.3rem;
    font-weight: 800;
    margin-bottom: 0px;
}

.role-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 15px;
}

.role-admin { background: rgba(255, 0, 127, 0.2); color: #FF007F; border: 1px solid #FF007F; }
.role-empleado { background: rgba(138, 43, 226, 0.2); color: #BB86FC; border: 1px solid #8A2BE2; }
.role-cliente { background: rgba(0, 240, 255, 0.2); color: #00F0FF; border: 1px solid #00F0FF; }

.stButton > button {
    background: linear-gradient(135deg, #FF007F 0%, #8A2BE2 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.review-card {
    background-color: #161622;
    border-left: 4px solid #FF007F;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORREO Y AUXILIARES
# ==========================================
def enviar_correo_confirmacion(destinatario, nombre, servicio, fecha, hora, total):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinatario
        msg['Subject'] = "✨ Confirmación de tu Reserva en GlowStudio AI"

        cuerpo = f"""
        Hola {nombre},

        ¡Tu reserva ha sido confirmada con éxito en GlowStudio AI! 💖

        📅 Detalle de tu Cita:
        - Servicio/Combo: {servicio}
        - Fecha y Hora: {fecha} a las {hora}
        - Total Pagado: ${total:.2f} USD

        Nos encontramos en nuestro Salón VIP. Te recomendamos llegar 5 minutos antes.

        ¡Gracias por preferir GlowStudio AI!
        """
        msg.attach(MIMEText(cuerpo, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

def check_toxic_comment(texto):
    palabras_prohibidas = ["pésimo", "estafadores", "basura", "horrible", "asco", "malditos", "idiotas", "robo"]
    return any(word in texto.lower() for word in palabras_prohibidas)

# ==========================================
# 4. CONTROL DE SESIÓN Y LOGIN (RBAC)
# ==========================================
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "user_nickname" not in st.session_state:
    st.session_state["user_nickname"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "carrito" not in st.session_state:
    st.session_state["carrito"] = []
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "🛍️ Catálogo & Combos"

if not st.session_state["user_email"]:
    st.markdown('<div class="brand-header">GlowStudio AI</div>', unsafe_allow_html=True)
    st.subheader("Acceso al Portal de Belleza & Gestión")
    
    col_login_l, _ = st.columns([1, 1])
    with col_login_l:
        with st.container(border=True):
            nickname_in = st.text_input("Apodo / Nombre (Nickname):")
            email_in = st.text_input("Correo Electrónico:").strip().lower()
            btn_login = st.button("Iniciar Sesión / Entrar", use_container_width=True)
            
            if btn_login:
                if not email_in or not nickname_in:
                    st.warning("⚠️ Ingresa un nickname y correo válido.")
                else:
                    st.session_state["user_email"] = email_in
                    st.session_state["user_nickname"] = nickname_in
                    
                    super_admin = st.secrets.get("admin", {}).get("super_admin", "jdyagual2@tes.edu.ec")
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT rol FROM usuarios WHERE LOWER(email) = ?", (email_in,))
                    res = c.fetchone()
                    conn.close()
                    
                    if email_in == super_admin.lower():
                        st.session_state["user_role"] = "admin"
                    elif res and res[0] == "empleado":
                        st.session_state["user_role"] = "empleado"
                    else:
                        st.session_state["user_role"] = "cliente"
                    
                    st.rerun()
    st.stop()

# --- SIDEBAR (INCLUYE CHATBOT FLOTANTE BELLA IA) ---
st.sidebar.markdown(f"### 👤 {st.session_state['user_nickname']}")
role_class = f"role-{st.session_state['user_role']}"
st.sidebar.markdown(f'<span class="role-badge {role_class}">Rol: {st.session_state["user_role"].upper()}</span>', unsafe_allow_html=True)

if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["user_email"] = ""
    st.session_state["user_nickname"] = ""
    st.session_state["user_role"] = ""
    st.session_state["carrito"] = []
    st.rerun()

st.sidebar.markdown("---")

# CHATBOT FLOTANTE SIEMPRE DISPONIBLE EN EL SIDEBAR
with st.sidebar.expander("💖 Bella IA & Visagismo (Asistente 24/7)", expanded=False):
    st.markdown("#### 📷 Visagismo por Imagen")
    img_file = st.file_uploader("Sube una foto de tu rostro:", type=["jpg", "png", "jpeg"], key="bot_img")
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True, caption="Rostro Analizado por IA")
        st.success("✨ **Visagismo IA:** Rostro ovalado. Te recomendamos **Corte en Capas** y tonos **Balayage Warm Gloss**.")

    st.markdown("#### 💬 Asistente Virtual")
    user_msg = st.text_input("Haz una pregunta a Bella:", key="bot_input")
    if st.button("Enviar Consulta", key="bot_btn"):
        if user_msg:
            msg_lower = user_msg.lower()
            if any(k in msg_lower for k in ["estresada", "estresado", "cansada", "relajación"]):
                st.info("💖 **Bella IA:** *Te recomiendo nuestro tratamiento Spa Keratina con masaje capilar relajante.*")
            elif any(k in msg_lower for k in ["precio", "descuento", "combo"]):
                st.info("💖 **Bella IA:** *Los combos tienen hasta un 20% de ahorro directo. Paga con tarjeta para 5% adicional.*")
            else:
                st.warning("🤖 **Bella IA:** *He escalado tu consulta al Administrador.*")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO preguntas_escaladas (cliente_email, pregunta, fecha_hora, respuesta, atendido) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state["user_email"], f"Intervención: [{user_msg}]", ahora, "", 0))
                conn.commit()
                conn.close()

st.markdown('<div class="brand-header">GlowStudio AI | Luxury Spa</div>', unsafe_allow_html=True)

# ==========================================
# 5. PANEL DE CLIENTE
# ==========================================
if st.session_state["user_role"] == "cliente":
    
    # Header del Carrito con Redirección Directa
    col_hdr, col_cart = st.columns([3, 1.2])
    with col_cart:
        num_items = len(st.session_state["carrito"])
        if st.button(f"🛒 Ver Carrito Checkout ({num_items} items)", use_container_width=True):
            st.session_state["current_tab"] = "📅 Reserva & Calendario"
            st.rerun()

    # Navegación Principal
    tab_options = ["🛍️ Catálogo & Combos", "📅 Reserva & Calendario", "⭐ Mapa de Calor & Reseñas"]
    
    selected_tab = st.radio(
        "", 
        tab_options, 
        index=tab_options.index(st.session_state["current_tab"]) if st.session_state["current_tab"] in tab_options else 0,
        horizontal=True
    )
    st.session_state["current_tab"] = selected_tab

    # --- PESTAÑA 1: CATÁLOGO CON IMÁGENES ---
    if selected_tab == "🛍️ Catálogo & Combos":
        st.markdown("### 💄 Servicios Individuales y Combos Especiales")
        st.info("💡 **Regla de Descuento:** Los cupones aplican únicamente sobre servicios individuales. Los combos ya poseen precio especial.")
        
        conn = sqlite3.connect(DB_PATH)
        df_serv = pd.read_sql_query("SELECT * FROM servicios WHERE disponible = 1", conn)
        conn.close()
        
        col_s1, col_s2 = st.columns(2)
        for i, row in df_serv.iterrows():
            target_col = col_s1 if i % 2 == 0 else col_s2
            with target_col:
                with st.container(border=True):
                    if row["imagen_url"]:
                        st.image(row["imagen_url"], use_container_width=True)
                    badge_combo = "🔥 COMBO ESPECIAL" if row["es_combo"] else "✨ SERVICIO INDIVIDUAL"
                    st.caption(badge_combo)
                    st.subheader(row["nombre"])
                    st.write(f"Categoría: **{row['categoria']}**")
                    st.markdown(f"### ${row['precio']:.2f} USD")
                    if st.button(f"➕ Agregar al Carrito", key=f"add_{row['id']}"):
                        st.session_state["carrito"].append({"id": row["id"], "nombre": row["nombre"], "precio": row["precio"], "es_combo": row["es_combo"]})
                        st.toast(f"¡{row['nombre']} agregado al carrito!", icon="🛒")
                        st.rerun()

    # --- PESTAÑA 2: RESERVA, CALENDARIO & CHECKOUT ---
    elif selected_tab == "📅 Reserva & Calendario":
        col_res1, col_res2 = st.columns([1.3, 1])
        
        with col_res1:
            st.markdown("### 🗓️ Calendario de Espacios & Estilista")
            
            conn = sqlite3.connect(DB_PATH)
            df_emp = pd.read_sql_query("SELECT nickname, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
            
            emp_opciones = df_emp["nickname"].tolist() if not df_emp.empty else ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"]
            estilista_sel = st.selectbox("Selecciona tu Estilista Favorita:", emp_opciones)
            
            foto_row = df_emp[df_emp["nickname"] == estilista_sel]
            if not foto_row.empty and foto_row.iloc[0]["foto_url"]:
                st.image(foto_row.iloc[0]["foto_url"], width=180, caption=f"Estilista: {estilista_sel}")
            
            st.markdown("#### Selección de Fecha:")
            opcion_fecha = st.radio("¿Cuándo deseas agendar?", ["📅 Hoy", "📆 Mañana", "🗓️ Seleccionar otra fecha"], horizontal=True)
            
            if opcion_fecha == "📅 Hoy":
                fecha_sel = datetime.date.today()
            elif opcion_fecha == "📆 Mañana":
                fecha_sel = datetime.date.today() + datetime.timedelta(days=1)
            else:
                fecha_sel = st.date_input("Selecciona la fecha:", value=datetime.date.today() + datetime.timedelta(days=2))
            
            st.markdown(f"**Fecha elegida:** `{fecha_sel.strftime('%A, %d de %B de %Y')}`")
            
            # Horarios decorados
            st.markdown("#### Horarios Disponibles:")
            citas_existentes = pd.read_sql_query("SELECT hora FROM citas WHERE fecha = ? AND empleado = ?", conn, params=(str(fecha_sel), estilista_sel))["hora"].tolist()
            conn.close()
            
            horarios = ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"]
            cols_h = st.columns(3)
            for idx, h in enumerate(horarios):
                c_target = cols_h[idx % 3]
                ocupado = h in citas_existentes
                btn_label = f"🔴 {h} (Ocupado)" if ocupado else f"🟢 {h} (Libre)"
                if c_target.button(btn_label, key=f"slot_{h}", disabled=ocupado):
                    st.session_state["hora_seleccionada"] = h
            
            if "hora_seleccionada" in st.session_state:
                st.success(f"✨ Horario seleccionado: **{st.session_state['hora_seleccionada']}**")

        with col_res2:
            st.markdown("### 🛒 Resumen de Pago (Checkout)")
            if not st.session_state["carrito"]:
                st.info("Tu carrito está vacío. Agrega servicios desde el Catálogo.")
            else:
                total_base = 0.0
                st.write("**Servicios en tu carrito:**")
                
                # Lista de items con opción para ELIMINAR / CANCELAR
                for idx, item in enumerate(st.session_state["carrito"]):
                    col_i1, col_i2 = st.columns([3, 1])
                    col_i1.write(f"- {item['nombre']}: **${item['precio']:.2f}**")
                    if col_i2.button("🗑️", key=f"del_{idx}"):
                        st.session_state["carrito"].pop(idx)
                        st.rerun()
                    total_base += item["precio"]
                
                st.markdown("---")
                metodo_pago = st.radio("Método de Pago:", ["💵 Efectivo en Salón", "💳 Tarjeta (5% Mini-Descuento Extra)"])
                
                descuento_tarjeta = (total_base * 0.05) if "Tarjeta" in metodo_pago else 0.0
                total_final = total_base - descuento_tarjeta
                
                if descuento_tarjeta > 0:
                    st.caption(f"🎉 Descuento aplicado por Tarjeta: -${descuento_tarjeta:.2f}")
                
                st.markdown(f"## Total Final: ${total_final:.2f} USD")
                
                btn_finalizar = st.button("💖 Confirmar y Agendar Cita", use_container_width=True)
                if btn_finalizar:
                    if "hora_seleccionada" not in st.session_state:
                        st.error("⚠️ Por favor selecciona un horario disponible.")
                    else:
                        nombres_serv = ", ".join([x["nombre"] for x in st.session_state["carrito"]])
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, metodo_pago, monto_total, estado) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                  (st.session_state["user_email"], st.session_state["user_nickname"], estilista_sel,
                                   nombres_serv, str(fecha_sel), st.session_state["hora_seleccionada"], metodo_pago, total_final, "Confirmada"))
                        conn.commit()
                        conn.close()
                        
                        envio_ok = enviar_correo_confirmacion(st.session_state["user_email"], st.session_state["user_nickname"], nombres_serv, str(fecha_sel), st.session_state["hora_seleccionada"], total_final)
                        
                        st.balloons()
                        st.success(f"¡Cita reservada con éxito para el {fecha_sel} a las {st.session_state['hora_seleccionada']}!")
                        if envio_ok:
                            st.info("📧 Se ha enviado un correo electrónico de confirmación.")
                        
                        st.session_state["carrito"] = []
                        del st.session_state["hora_seleccionada"]

    # --- PESTAÑA 3: MAPA DE CALOR & RESEÑAS PÚBLICAS ---
    elif selected_tab == "⭐ Mapa de Calor & Reseñas":
        st.markdown("### 📊 Rendimiento de Estilistas & Reseñas de Clientes")
        
        conn = sqlite3.connect(DB_PATH)
        df_rev = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 0", conn)
        
        if not df_rev.empty:
            avg_stars = df_rev.groupby("empleado")["estrellas"].mean().reset_index()
            fig = px.bar(avg_stars, x="empleado", y="estrellas", color="estrellas", title="Calificación Promedio por Estilista (1-5 Estrellas)", color_continuous_scale="Plasma", range_y=[0, 5])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#FFF"))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 💬 Comentarios de Clientes")
            for _, r in df_rev.iterrows():
                st.markdown(f"""
                <div class="review-card">
                    <b>👤 {r['cliente_nombre']}</b> — <span style="color:#FFD700;">{"⭐"*int(r['estrellas'])}</span><br/>
                    <small>Atendido por: {r['empleado']} | {r['fecha']}</small><br/>
                    <p style="margin-top:6px; margin-bottom:0px;">"{r['comentario']}"</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### ⭐ Deja tu Calificación y Comentario")
        with st.form("form_resena"):
            emp_resena = st.selectbox("Estilista:", ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"])
            estrellas_in = st.slider("Calificación (Estrellas):", 1, 5, 5)
            comentario_in = st.text_area("Comentario:")
            btn_sub_rev = st.form_submit_button("Enviar Reseña")
            
            if btn_sub_rev:
                es_toxico = check_toxic_comment(comentario_in)
                hoy_f = datetime.date.today().strftime("%Y-%m-%d")
                c = conn.cursor()
                c.execute("INSERT INTO resenas (cliente_nombre, empleado, estrellas, comentario, bloqueado, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                          (st.session_state["user_nickname"], emp_resena, estrellas_in, comentario_in, 1 if es_toxico else 0, hoy_f))
                conn.commit()
                if es_toxico:
                    st.warning("⚠️ Tu comentario pasará a revisión del Administrador antes de publicarse.")
                else:
                    st.success("¡Gracias por tu valoración!")
                st.rerun()
        conn.close()

# ==========================================
# 6. PANEL DE ADMINISTRADOR
# ==========================================
elif st.session_state["user_role"] == "admin":
    st.markdown("## 👑 Panel de Control del Administrador")
    
    t_citas, t_emp, t_serv, t_mod, t_inv, t_bot = st.tabs([
        "📅 Citas & Walk-ins",
        "👩‍🎨 Empleados",
        "🛠️ Servicios",
        "🛡️ Moderación Reseñas",
        "📊 Finanzas e Inventario",
        "📥 Consultas Chatbot"
    ])
    
    conn = sqlite3.connect(DB_PATH)
    
    with t_citas:
        st.markdown("### Citas Registradas")
        df_c = pd.read_sql_query("SELECT * FROM citas ORDER BY id DESC", conn)
        st.dataframe(df_c, use_container_width=True)

    with t_emp:
        st.markdown("### Perfiles de Empleados")
        df_e = pd.read_sql_query("SELECT email, nickname, cedula, estado_pago, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
        st.dataframe(df_e, use_container_width=True)

    with t_serv:
        st.markdown("### Control de Disponibilidad")
        df_s = pd.read_sql_query("SELECT * FROM servicios", conn)
        for _, row in df_s.iterrows():
            col_s1, col_s2 = st.columns([3, 1])
            col_s1.write(f"**{row['nombre']}** - ${row['precio']:.2f}")
            disp = col_s2.toggle("Disponible", value=bool(row['disponible']), key=f"sw_{row['id']}")
            if disp != bool(row['disponible']):
                c = conn.cursor()
                c.execute("UPDATE servicios SET disponible = ? WHERE id = ?", (1 if disp else 0, row['id']))
                conn.commit()
                st.rerun()

    with t_mod:
        st.markdown("### Moderación de Comentarios")
        df_r = pd.read_sql_query("SELECT * FROM resenas", conn)
        for _, row in df_r.iterrows():
            st.write(f"**Cliente:** {row['cliente_nombre']} | **Estrellas:** {row['estrellas']}")
            st.write(f"*'{row['comentario']}'*")
            if row['bloqueado']:
                st.error("🚫 Bloqueado")
                if st.button("Desbloquear", key=f"unblk_{row['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE resenas SET bloqueado = 0 WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            st.markdown("---")

    with t_inv:
        st.markdown("### Inventario & Finanzas")
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        st.dataframe(df_inv, use_container_width=True)

    with t_bot:
        st.markdown("### Preguntas Escaladas")
        df_esc = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
        st.dataframe(df_esc, use_container_width=True)

    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown("## ✂️ Panel de Atención para Empleados")
    conn = sqlite3.connect(DB_PATH)
    df_p = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
    st.dataframe(df_p, use_container_width=True)
    conn.close()
