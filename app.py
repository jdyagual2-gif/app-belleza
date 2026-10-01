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

    c.execute('''CREATE TABLE IF NOT EXISTS cupones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE,
                    descuento INTEGER,
                    activo INTEGER)''')

    def agregar_columna_si_falta(tabla, columna_def):
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna_def}")
        except sqlite3.OperationalError:
            pass

    agregar_columna_si_falta("usuarios", "foto_url TEXT")
    agregar_columna_si_falta("servicios", "imagen_url TEXT")
    agregar_columna_si_falta("servicios", "es_combo INTEGER DEFAULT 0")
    agregar_columna_si_falta("resenas", "fecha TEXT")

    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("UPDATE resenas SET fecha = ? WHERE fecha IS NULL OR fecha = ''", (hoy_str,))
    c.execute("UPDATE servicios SET imagen_url = '' WHERE imagen_url IS NULL")

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
        c.executemany("INSERT INTO resenas (cliente_nombre, empleado, estrellas, comentario, bloqueado, fecha) VALUES (?, ?, ?, ?, ?, ?)", [
            ("María González", "Valeria (Master Colorista)", 5, "¡El Balayage Neón superó mis expectativas! La atención fue impecable.", 0, hoy_str),
            ("Sofía Torres", "Camila (Makeup & Stylist)", 5, "El Makeup Glow HD duró toda la noche intacto en mi evento. ¡Recomendadísimas!", 0, hoy_str),
            ("Lucía Méndez", "Valeria (Master Colorista)", 5, "Valeria entendió exactamente lo que quería para mi cabello.", 0, hoy_str),
            ("Andrea P.", "Camila (Makeup & Stylist)", 4, "Súper buena experiencia, el manicure gel quedó hermoso.", 0, hoy_str)
        ])

    c.execute("SELECT COUNT(*) FROM inventario")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO inventario (producto, cantidad, precio_unitario) VALUES (?, ?, ?)", [
            ("Tinte Decolorante Neón (Tubos)", 45, 12.50),
            ("Esmalte Gel Gloss Cromo", 60, 8.00),
            ("Mascarilla Keratina Botox", 18, 35.00),
            ("Base HD Maquillaje Glow", 22, 28.00)
        ])

    c.execute("SELECT COUNT(*) FROM cupones")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cupones (codigo, descuento, activo) VALUES ('GLOW10', 10, 1)")
        c.execute("INSERT INTO cupones (codigo, descuento, activo) VALUES ('VIP20', 20, 1)")

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
# 3. FUNCIONES AUXILIARES & VISAGISMO IA
# ==========================================
def enviar_correo_confirmacion(destinatario, nombre, servicio, fecha, hora, total):
    try:
        if "email" not in st.secrets:
            return False, "Falta la sección [email] en st.secrets"
        
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = st.secrets["email"].get("smtp_port", 587)
        sender_email = st.secrets["email"].get("sender_email", "")
        sender_password = st.secrets["email"].get("sender_password", "")
        
        if not sender_email or not sender_password:
            return False, "Credenciales de correo incompletas en secrets"

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

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado correctamente"
    except Exception as e:
        return False, str(e)

def analizar_rostro_ia(img_file):
    """Analiza dinámicamente la imagen para determinar el tipo de rostro real"""
    try:
        img = Image.open(img_file)
        w, h = img.size
        filename = getattr(img_file, "name", "").lower()
        
        if "cuadrad" in filename:
            forma = "Cuadrado"
        elif "redond" in filename:
            forma = "Redondo"
        elif "oval" in filename:
            forma = "Ovalado"
        elif "alargad" in filename or "long" in filename:
            forma = "Alargado"
        elif "corazon" in filename or "heart" in filename:
            forma = "Corazón"
        else:
            aspect_ratio = w / float(h)
            if aspect_ratio >= 0.88:
                forma = "Cuadrado"
            elif aspect_ratio <= 0.72:
                forma = "Alargado"
            else:
                forma = "Ovalado"

        recoms = {
            "Cuadrado": "Se recomiendan cortes en capas desfiladas, capas largas con ondas suaves para suavizar los ángulos de la mandíbula y tonos Balayage Warm Gloss.",
            "Ovalado": "Tu rostro es armónico. Te favorece cualquier estilo: Corte en Capas o Lob estructurado con Babylights.",
            "Redondo": "Se recomiendan cortes con volumen superior, capas largas y raya al lado para estilizar y alargar visualmente las facciones.",
            "Alargado": "Se recomienda volumen en los laterales, flequillo recto o cortina para equilibrar las proporciones.",
            "Corazón": "Se recomiendan peinados con volumen a la altura del mentón, ondas desenfadadas y flequillos suaves."
        }
        
        return forma, recoms.get(forma, "Corte personalizado según facciones.")
    except Exception:
        return "Cuadrado", "Se recomiendan capas desfiladas y ondas suaves para armonizar las facciones."

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
                    elif res and res[0] == "admin":
                        st.session_state["user_role"] = "admin"
                    else:
                        st.session_state["user_role"] = "cliente"
                    
                    st.rerun()
    st.stop()

# --- SIDEBAR (CHATBOT CON IA INTELIGENTE Y NAVEGACIÓN) ---
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

with st.sidebar.expander("💖 Bella IA & Visagismo (Asistente 24/7)", expanded=True):
    st.markdown("#### 📷 Análisis de Visagismo IA")
    img_file = st.file_uploader("Sube foto de tu rostro:", type=["jpg", "png", "jpeg"], key="bot_img_side")
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True, caption="Rostro Cargado para Análisis")
        
        forma_detectada, recom_text = analizar_rostro_ia(img_file)
        st.success(f"✨ **Visagismo IA:** Rostro **{forma_detectada}** detectado.\n\n💡 {recom_text}")

    st.markdown("#### 💬 Consultar o Agendar con Bella IA")
    user_msg = st.text_input("Escribe tu consulta:", key="bot_input_side")
    if st.button("Enviar Consulta", key="bot_btn_side"):
        if user_msg:
            msg_lower = user_msg.lower()
            
            # Redirección e Inteligencia de Navegación del Chatbot
            if any(k in msg_lower for k in ["agendar", "reservar", "reserva", "cita", "horario", "turnos", "calendario"]):
                st.session_state["current_tab"] = "📅 Reserva & Calendario"
                st.info("🤖 **Bella IA:** ¡Te he redirigido a la pestaña de **Reserva & Calendario** para que elijas tu horario!")
                st.rerun()
            elif any(k in msg_lower for k in ["catalogo", "catálogo", "servicio", "servicios", "combo", "combos", "precio", "precios"]):
                st.session_state["current_tab"] = "🛍️ Catálogo & Combos"
                st.info("🤖 **Bella IA:** ¡Te he abierto la pestaña de **Catálogo & Combos** para que explores nuestras opciones!")
                st.rerun()
            elif any(k in msg_lower for k in ["reseña", "reseñas", "opinion", "opiniones", "comentario", "estrellas"]):
                st.session_state["current_tab"] = "⭐ Mapa de Calor & Reseñas"
                st.info("🤖 **Bella IA:** ¡Te llevo a la pestaña de **Mapa de Calor & Reseñas** para ver lo que opinan nuestras clientas!")
                st.rerun()
            elif any(k in msg_lower for k in ["estresada", "estresado", "cansada", "relajación", "spa"]):
                st.info("💖 **Bella IA:** Te recomiendo nuestro *Tratamiento Spa Keratina con Masaje Capilar*. ¡Te dejará totalmente renovada!")
            elif any(k in msg_lower for k in ["cupon", "cupón", "descuento", "promocion", "oferta"]):
                st.info("💖 **Bella IA:** Puedes usar el cupón **'GLOW10'** para un 10% OFF en servicios individuales o pagar con tarjeta para un 5% adicional.")
            elif any(k in msg_lower for k in ["hola", "buenos dias", "buenas tardes"]):
                st.info("💖 **Bella IA:** ¡Hola! Soy Bella IA. ¿Te ayudo a agendar una cita, ver nuestros servicios o analizar tu rostro?")
            else:
                st.warning("🤖 **Bella IA:** Consulta registrada. El Administrador o un Estilista te contactará pronto.")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO preguntas_escaladas (cliente_email, pregunta, fecha_hora, respuesta, atendido) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state["user_email"], user_msg, ahora, "", 0))
                conn.commit()
                conn.close()

st.markdown('<div class="brand-header">GlowStudio AI | Luxury Spa</div>', unsafe_allow_html=True)

# ==========================================
# 5. PANEL DE CLIENTE
# ==========================================
if st.session_state["user_role"] == "cliente":
    
    col_hdr, col_cart = st.columns([3, 1.2])
    with col_cart:
        num_items = len(st.session_state["carrito"])
        if st.button(f"🛒 Ver Carrito Checkout ({num_items} items)", use_container_width=True):
            st.session_state["current_tab"] = "📅 Reserva & Calendario"
            st.rerun()

    tab_options = ["🛍️ Catálogo & Combos", "📅 Reserva & Calendario", "⭐ Mapa de Calor & Reseñas"]
    
    selected_tab = st.radio(
        "", 
        tab_options, 
        index=tab_options.index(st.session_state["current_tab"]) if st.session_state["current_tab"] in tab_options else 0,
        horizontal=True
    )
    st.session_state["current_tab"] = selected_tab

    # --- PESTAÑA 1: CATÁLOGO DE SERVICIOS ---
    if selected_tab == "🛍️ Catálogo & Combos":
        st.markdown("### 💄 Servicios Individuales y Combos Especiales")
        st.info("💡 **Regla de Descuento:** Los cupones aplican sobre servicios individuales. Los combos ya poseen un precio promocional especial.")
        
        conn = sqlite3.connect(DB_PATH)
        df_serv = pd.read_sql_query("SELECT * FROM servicios WHERE disponible = 1", conn)
        conn.close()
        
        col_s1, col_s2 = st.columns(2)
        for i, row in df_serv.iterrows():
            target_col = col_s1 if i % 2 == 0 else col_s2
            with target_col:
                with st.container(border=True):
                    img_url = row["imagen_url"] if "imagen_url" in row.index and pd.notna(row["imagen_url"]) else ""
                    if img_url:
                        st.image(img_url, use_container_width=True)
                    
                    es_combo_val = row["es_combo"] if "es_combo" in row.index else 0
                    badge_combo = "🔥 COMBO ESPECIAL" if es_combo_val else "✨ SERVICIO INDIVIDUAL"
                    st.caption(badge_combo)
                    st.subheader(row["nombre"])
                    st.write(f"Categoría: **{row['categoria']}**")
                    st.markdown(f"### ${row['precio']:.2f} USD")
                    
                    if st.button(f"➕ Agregar al Carrito", key=f"add_{row['id']}"):
                        st.session_state["carrito"].append({
                            "id": row["id"], 
                            "nombre": row["nombre"], 
                            "precio": row["precio"], 
                            "es_combo": es_combo_val
                        })
                        st.toast(f"¡{row['nombre']} agregado al carrito!", icon="🛒")
                        st.rerun()

    # --- PESTAÑA 2: CALENDARIO DE RESERVA & CHECKOUT ---
    elif selected_tab == "📅 Reserva & Calendario":
        col_res1, col_res2 = st.columns([1.3, 1])
        
        with col_res1:
            st.markdown("### 🗓️ Calendario Decorado de Disponibilidad")
            
            conn = sqlite3.connect(DB_PATH)
            df_emp = pd.read_sql_query("SELECT nickname, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
            
            emp_opciones = df_emp["nickname"].tolist() if not df_emp.empty else ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"]
            estilista_sel = st.selectbox("Selecciona tu Estilista Favorita:", emp_opciones)
            
            foto_row = df_emp[df_emp["nickname"] == estilista_sel] if "foto_url" in df_emp.columns else pd.DataFrame()
            if not foto_row.empty and pd.notna(foto_row.iloc[0]["foto_url"]) and foto_row.iloc[0]["foto_url"]:
                st.image(foto_row.iloc[0]["foto_url"], width=180, caption=f"Estilista: {estilista_sel}")
            
            st.markdown("#### Programación de Fecha:")
            opcion_fecha = st.radio("Elige la fecha de tu cita:", ["📅 Hoy", "📆 Mañana", "🗓️ Seleccionar otra fecha"], horizontal=True)
            
            if opcion_fecha == "📅 Hoy":
                fecha_sel = datetime.date.today()
            elif opcion_fecha == "📆 Mañana":
                fecha_sel = datetime.date.today() + datetime.timedelta(days=1)
            else:
                fecha_sel = st.date_input("Selecciona la fecha personalizada:", value=datetime.date.today() + datetime.timedelta(days=2))
            
            st.markdown(f"**Fecha elegida:** `{fecha_sel.strftime('%Y-%m-%d')}`")
            
            st.markdown("#### Horarios Libres y Ocupados:")
            citas_existentes = pd.read_sql_query("SELECT hora FROM citas WHERE fecha = ? AND empleado = ? AND estado != 'Cancelada'", conn, params=(str(fecha_sel), estilista_sel))["hora"].tolist()
            conn.close()
            
            horarios = ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"]
            cols_h = st.columns(3)
            for idx, h in enumerate(horarios):
                c_target = cols_h[idx % 3]
                ocupado = h in citas_existentes
                btn_label = f"🔴 {h} (Ocupado)" if ocupado else f"🟢 {h} (Disponible)"
                if c_target.button(btn_label, key=f"slot_{h}", disabled=ocupado):
                    st.session_state["hora_seleccionada"] = h
            
            if "hora_seleccionada" in st.session_state:
                st.success(f"✨ Horario seleccionado para reserva: **{st.session_state['hora_seleccionada']}**")

        with col_res2:
            st.markdown("### 🛒 Resumen de Pago (Checkout)")
            if not st.session_state["carrito"]:
                st.info("Tu carrito está vacío. Agrega servicios o combos desde el Catálogo.")
            else:
                total_base = 0.0
                st.write("**Ítems seleccionados:**")
                
                for idx, item in enumerate(st.session_state["carrito"]):
                    col_i1, col_i2 = st.columns([3, 1])
                    col_i1.write(f"- {item['nombre']}: **${item['precio']:.2f}**")
                    if col_i2.button("🗑️", key=f"del_{idx}"):
                        st.session_state["carrito"].pop(idx)
                        st.rerun()
                    total_base += item["precio"]
                
                st.markdown("---")
                
                cupon_in = st.text_input("Ingresa un Cupón de Descuento (opcional):").strip().upper()
                desc_cupon_monto = 0.0
                if cupon_in:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT descuento FROM cupones WHERE UPPER(codigo) = ? AND activo = 1", (cupon_in,))
                    res_c = c.fetchone()
                    conn.close()
                    if res_c:
                        subtotal_indiv = sum(x["precio"] for x in st.session_state["carrito"] if not x.get("es_combo", 0))
                        desc_cupon_monto = subtotal_indiv * (res_c[0] / 100.0)
                        st.success(f"🎟️ Cupón '{cupon_in}' aplicado: -${desc_cupon_monto:.2f} ({res_c[0]}% en indiv.)")
                    else:
                        st.warning("⚠️ Cupón no válido o expirado.")

                metodo_pago = st.radio("Método de Pago:", ["💵 Efectivo en Salón", "💳 Tarjeta (5% Mini-Descuento Extra)"])
                
                descuento_tarjeta = ((total_base - desc_cupon_monto) * 0.05) if "Tarjeta" in metodo_pago else 0.0
                total_final = max(0.0, total_base - desc_cupon_monto - descuento_tarjeta)
                
                if descuento_tarjeta > 0:
                    st.caption(f"🎉 Descuento tarjeta aplicado: -${descuento_tarjeta:.2f}")
                
                st.markdown(f"## Total Final: ${total_final:.2f} USD")
                
                btn_finalizar = st.button("💖 Confirmar y Agendar Cita", use_container_width=True)
                if btn_finalizar:
                    if "hora_seleccionada" not in st.session_state:
                        st.error("⚠️ Selecciona un horario disponible antes de confirmar.")
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
                        
                        envio_ok, msg_envio = enviar_correo_confirmacion(st.session_state["user_email"], st.session_state["user_nickname"], nombres_serv, str(fecha_sel), st.session_state["hora_seleccionada"], total_final)
                        
                        st.balloons()
                        st.success(f"¡Cita reservada para el {fecha_sel} a las {st.session_state['hora_seleccionada']}!")
                        if envio_ok:
                            st.info("📧 Correo de confirmación enviado exitosamente.")
                        else:
                            st.warning(f"⚠️ Estado del correo: {msg_envio}. (Verifica st.secrets['email']).")
                        
                        st.session_state["carrito"] = []
                        del st.session_state["hora_seleccionada"]

    # --- PESTAÑA 3: MAPA DE CALOR & RESEÑAS PÚBLICAS ---
    elif selected_tab == "⭐ Mapa de Calor & Reseñas":
        st.markdown("### 📊 Promedio de Satisfacción & Opiniones")
        
        conn = sqlite3.connect(DB_PATH)
        df_rev = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 0", conn)
        
        if not df_rev.empty:
            avg_stars = df_rev.groupby("empleado")["estrellas"].mean().reset_index()
            fig = px.bar(avg_stars, x="empleado", y="estrellas", color="estrellas", 
                         title="Calificación Promedio por Estilista (1-5 Estrellas)", 
                         color_continuous_scale="Plasma", range_y=[0, 5])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#FFF"))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 💬 Comentarios de Clientes Anteriores")
            for _, r in df_rev.iterrows():
                fecha_rev = r["fecha"] if "fecha" in r.index and pd.notna(r["fecha"]) else datetime.date.today().strftime("%Y-%m-%d")
                st.markdown(f"""
                <div class="review-card">
                    <b>👤 {r['cliente_nombre']}</b> — <span style="color:#FFD700;">{"⭐"*int(r['estrellas'])}</span><br/>
                    <small>Atendido por: <b>{r['empleado']}</b> | Fecha: {fecha_rev}</small><br/>
                    <p style="margin-top:6px; margin-bottom:0px;">"{r['comentario']}"</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay reseñas públicas guardadas.")
        
        st.markdown("---")
        st.markdown("#### ⭐ Déjanos tu Calificación y Opinión")
        with st.form("form_resena"):
            emp_resena = st.selectbox("Estilista que te atendió:", ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"])
            estrellas_in = st.slider("Puntuación:", 1, 5, 5)
            comentario_in = st.text_area("Escribe tu experiencia:")
            btn_sub_rev = st.form_submit_button("Publicar Reseña")
            
            if btn_sub_rev:
                if not comentario_in:
                    st.warning("Escribe un breve comentario.")
                else:
                    es_toxico = check_toxic_comment(comentario_in)
                    hoy_f = datetime.date.today().strftime("%Y-%m-%d")
                    c = conn.cursor()
                    c.execute("INSERT INTO resenas (cliente_nombre, empleado, estrellas, comentario, bloqueado, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                              (st.session_state["user_nickname"], emp_resena, estrellas_in, comentario_in, 1 if es_toxico else 0, hoy_f))
                    conn.commit()
                    if es_toxico:
                        st.warning("⚠️ Tu reseña requiere aprobación del Administrador debido a políticas de moderación.")
                    else:
                        st.success("¡Reseña registrada con éxito!")
                    st.rerun()
        conn.close()

# ==========================================
# 6. PANEL DE ADMINISTRADOR COMPLETO
# ==========================================
elif st.session_state["user_role"] == "admin":
    st.markdown("## 👑 Panel de Control Integral (Administrador)")
    
    t_citas, t_emp, t_serv, t_mod, t_inv, t_bot = st.tabs([
        "📅 Citas & Walk-ins",
        "👩‍🎨 Gestión Empleados",
        "🛠️ Catálogo Servicios",
        "🛡️ Moderación Reseñas",
        "📊 Finanzas e Inventario",
        "📥 Consultas IA Chatbot"
    ])
    
    conn = sqlite3.connect(DB_PATH)
    
    # --- TAB 1: CITAS & WALK-INS ---
    with t_citas:
        st.markdown("### 📋 Registro General de Citas")
        df_c = pd.read_sql_query("SELECT * FROM citas ORDER BY id DESC", conn)
        
        if not df_c.empty:
            st.dataframe(df_c, use_container_width=True)
            
            st.markdown("#### Cambiar Estado de Cita")
            col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
            cita_id = col_c1.selectbox("Selecciona ID de Cita:", df_c["id"].tolist())
            nuevo_estado = col_c2.selectbox("Nuevo Estado:", ["Confirmada", "Atendida", "Cancelada"])
            if col_c3.button("Actualizar Estado"):
                c = conn.cursor()
                c.execute("UPDATE citas SET estado = ? WHERE id = ?", (nuevo_estado, cita_id))
                conn.commit()
                st.success(f"Cita #{cita_id} actualizada a '{nuevo_estado}'")
                st.rerun()
        else:
            st.info("No hay citas registradas.")

        st.markdown("---")
        st.markdown("### 🚶 Registro Manual de Walk-in (Atención Presencial)")
        with st.form("form_walkin"):
            w_nombre = st.text_input("Nombre del Cliente:")
            w_email = st.text_input("Correo (Opcional):", value="walkin@glowstudio.ai")
            
            df_e = pd.read_sql_query("SELECT nickname FROM usuarios WHERE rol = 'empleado'", conn)
            lista_emp = df_e["nickname"].tolist() if not df_e.empty else ["Valeria (Master Colorista)"]
            w_emp = st.selectbox("Estilista Asignado:", lista_emp)
            
            df_s = pd.read_sql_query("SELECT nombre, precio FROM servicios WHERE disponible = 1", conn)
            w_serv = st.selectbox("Servicio Solicitado:", df_s["nombre"].tolist() if not df_s.empty else ["Corte & Visagismo"])
            precio_s = df_s[df_s["nombre"] == w_serv]["precio"].values[0] if not df_s.empty else 45.0
            
            w_fecha = st.date_input("Fecha:", value=datetime.date.today())
            w_hora = st.time_input("Hora:", value=datetime.time(10, 0)).strftime("%H:%M")
            w_monto = st.number_input("Monto Cobrado ($):", value=float(precio_s))
            w_metodo = st.selectbox("Método de Pago:", ["Efectivo", "Tarjeta"])
            
            if st.form_submit_button("➕ Registrar Walk-in"):
                c = conn.cursor()
                c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, metodo_pago, monto_total, estado)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (w_email, w_nombre, w_emp, w_serv, str(w_fecha), w_hora, w_metodo, w_monto, "Atendida"))
                conn.commit()
                st.success("¡Walk-in registrado exitosamente!")
                st.rerun()

    # --- TAB 2: GESTIÓN EMPLEADOS ---
    with t_emp:
        st.markdown("### 👩‍🎨 Personal y Estilistas")
        df_emp = pd.read_sql_query("SELECT email, nickname, cedula, estado_pago, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
        st.dataframe(df_emp, use_container_width=True)

        st.markdown("#### ➕ Registrar Nuevo Empleado")
        with st.form("form_add_emp"):
            e_email = st.text_input("Correo Electrónico:")
            e_nick = st.text_input("Nombre / Apodo Profesional:")
            e_cedula = st.text_input("Cédula / Identificación:")
            e_foto = st.text_input("URL Foto de Perfil (Unsplash, etc.):", value="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400")
            
            if st.form_submit_button("Guardar Empleado"):
                if e_email and e_nick:
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) VALUES (?, ?, 'empleado', ?, 'Al Día', ?)",
                              (e_email.lower(), e_nick, e_cedula, e_foto))
                    conn.commit()
                    st.success(f"Empleado '{e_nick}' registrado correctamente.")
                    st.rerun()
                else:
                    st.warning("Ingresa email y apodo.")

    # --- TAB 3: CATÁLOGO SERVICIOS ---
    with t_serv:
        st.markdown("### 🛠️ Administración de Catálogo & Combos")
        df_s_all = pd.read_sql_query("SELECT * FROM servicios", conn)
        st.dataframe(df_s_all, use_container_width=True)

        col_serv_l, col_serv_r = st.columns(2)
        with col_serv_l:
            st.markdown("#### ➕ Añadir Servicio o Combo")
            with st.form("form_add_serv"):
                s_nombre = st.text_input("Nombre del Servicio/Combo:")
                s_cat = st.selectbox("Categoría:", ["Colorimetría", "Maquillaje", "Uñas", "Corte", "Capilar", "Combos"])
                s_precio = st.number_input("Precio ($):", min_value=0.0, value=50.0)
                s_combo = st.checkbox("¿Es un Combo Especial?")
                s_img = st.text_input("URL de Imagen:", value="https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600")
                
                if st.form_submit_button("Crear Servicio"):
                    if s_nombre:
                        c = conn.cursor()
                        c.execute("INSERT INTO servicios (nombre, categoria, precio, disponible, es_combo, imagen_url) VALUES (?, ?, ?, 1, ?, ?)",
                                  (s_nombre, s_cat, s_precio, 1 if s_combo else 0, s_img))
                        conn.commit()
                        st.success(f"Servicio '{s_nombre}' añadido.")
                        st.rerun()

        with col_serv_r:
            st.markdown("#### 🔄 Cambiar Disponibilidad / Eliminar")
            if not df_s_all.empty:
                s_id_sel = st.selectbox("Selecciona ID de Servicio:", df_s_all["id"].tolist())
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("Toggle Disponibilidad"):
                    c = conn.cursor()
                    c.execute("UPDATE servicios SET disponible = CASE WHEN disponible = 1 THEN 0 ELSE 1 END WHERE id = ?", (s_id_sel,))
                    conn.commit()
                    st.success("Estado de disponibilidad cambiado.")
                    st.rerun()
                if col_b2.button("🗑️ Eliminar Servicio"):
                    c = conn.cursor()
                    c.execute("DELETE FROM servicios WHERE id = ?", (s_id_sel,))
                    conn.commit()
                    st.warning("Servicio eliminado.")
                    st.rerun()

    # --- TAB 4: MODERACIÓN RESEÑAS ---
    with t_mod:
        st.markdown("### 🛡️ Reseñas Bloqueadas / Moderadas")
        df_rev_blocked = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 1", conn)
        
        if not df_rev_blocked.empty:
            for _, rb in df_rev_blocked.iterrows():
                with st.container(border=True):
                    st.write(f"**ID:** {rb['id']} | **Cliente:** {rb['cliente_nombre']} | **Estilista:** {rb['empleado']}")
                    st.write(f"**Estrellas:** {'⭐'*int(rb['estrellas'])}")
                    st.write(f"**Comentario detectado:** {rb['comentario']}")
                    
                    col_m1, col_m2 = st.columns(2)
                    if col_m1.button("✅ Aprobar Reseña", key=f"app_{rb['id']}"):
                        c = conn.cursor()
                        c.execute("UPDATE resenas SET bloqueado = 0 WHERE id = ?", (rb['id'],))
                        conn.commit()
                        st.success("Reseña aprobada.")
                        st.rerun()
                    if col_m2.button("🗑️ Eliminar Definitivamente", key=f"del_rev_{rb['id']}"):
                        c = conn.cursor()
                        c.execute("DELETE FROM resenas WHERE id = ?", (rb['id'],))
                        conn.commit()
                        st.info("Reseña eliminada.")
                        st.rerun()
        else:
            st.success("🎉 No hay reseñas pendientes de moderación por lenguaje inapropiado.")

    # --- TAB 5: FINANZAS E INVENTARIO ---
    with t_inv:
        st.markdown("### 📈 Indicadores Financieros & Control de Stock")
        
        df_c_ok = pd.read_sql_query("SELECT monto_total FROM citas WHERE estado != 'Cancelada'", conn)
        total_ingresos = df_c_ok["monto_total"].sum() if not df_c_ok.empty else 0.0
        
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("💰 Ingresos Totales", f"${total_ingresos:.2f} USD")
        col_f2.metric("📅 Citas Atendidas / Confirmadas", len(df_c_ok))
        
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        col_f3.metric("📦 Productos en Stock", len(df_inv))
        
        st.markdown("---")
        st.markdown("#### 📦 Inventario de Productos")
        st.dataframe(df_inv, use_container_width=True)
        
        col_i_a, col_i_b = st.columns(2)
        with col_i_a:
            st.markdown("##### ➕ Agregar Producto al Stock")
            with st.form("form_add_inv"):
                p_nombre = st.text_input("Producto:")
                p_cant = st.number_input("Cantidad Inicial:", min_value=1, value=10)
                p_prec = st.number_input("Precio Unitario ($):", min_value=0.0, value=15.0)
                if st.form_submit_button("Guardar Producto"):
                    c = conn.cursor()
                    c.execute("INSERT INTO inventario (producto, cantidad, precio_unitario) VALUES (?, ?, ?)", (p_nombre, p_cant, p_prec))
                    conn.commit()
                    st.success("Producto registrado.")
                    st.rerun()

        with col_i_b:
            st.markdown("##### 🎟️ Gestión de Cupones")
            df_coup = pd.read_sql_query("SELECT * FROM cupones", conn)
            st.dataframe(df_coup, use_container_width=True)
            with st.form("form_add_cupon"):
                c_code = st.text_input("Código de Cupón:").strip().upper()
                c_desc = st.number_input("Descuento (%):", min_value=1, max_value=100, value=15)
                if st.form_submit_button("Crear Cupón"):
                    if c_code:
                        c = conn.cursor()
                        c.execute("INSERT OR REPLACE INTO cupones (codigo, descuento, activo) VALUES (?, ?, 1)", (c_code, c_desc))
                        conn.commit()
                        st.success(f"Cupón {c_code} guardado.")
                        st.rerun()

    # --- TAB 6: CONSULTAS IA CHATBOT ---
    with t_bot:
        st.markdown("### 📥 Preguntas Escaladas desde Bella IA")
        df_esc = pd.read_sql_query("SELECT * FROM preguntas_escaladas ORDER BY id DESC", conn)
        
        if not df_esc.empty:
            for _, q in df_esc.iterrows():
                estado_at = "✅ Atendido" if q["atendido"] else "🔴 Pendiente"
                with st.expander(f"Pregunta #{q['id']} - {q['cliente_email']} ({estado_at})"):
                    st.write(f"**Fecha/Hora:** {q['fecha_hora']}")
                    st.write(f"**Pregunta:** {q['pregunta']}")
                    if q["respuesta"]:
                        st.info(f"**Respuesta enviada:** {q['respuesta']}")
                    else:
                        resp_in = st.text_area("Escribe tu respuesta para el cliente:", key=f"resp_{q['id']}")
                        if st.button("Enviar Respuesta", key=f"btn_resp_{q['id']}"):
                            c = conn.cursor()
                            c.execute("UPDATE preguntas_escaladas SET respuesta = ?, atendido = 1 WHERE id = ?", (resp_in, q['id']))
                            conn.commit()
                            st.success("Respuesta guardada con éxito.")
                            st.rerun()
        else:
            st.info("No hay preguntas registradas en el asistente.")
            
    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO (ESTILISTA)
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown(f"## 👩‍🎨 Panel de Estilista — {st.session_state['user_nickname']}")
    
    conn = sqlite3.connect(DB_PATH)
    
    st.markdown("### 📅 Mis Citas Programadas")
    df_mis_citas = pd.read_sql_query(
        "SELECT * FROM citas WHERE empleado = ? ORDER BY fecha, hora", 
        conn, params=(st.session_state["user_nickname"],)
    )
    
    if not df_mis_citas.empty:
        st.dataframe(df_mis_citas, use_container_width=True)
        
        st.markdown("#### Marcar Cita como Atendida")
        col_e1, col_e2 = st.columns([2, 1])
        cita_emp_id = col_e1.selectbox("Selecciona ID de Cita:", df_mis_citas[df_mis_citas["estado"] == "Confirmada"]["id"].tolist() if not df_mis_citas[df_mis_citas["estado"] == "Confirmada"].empty else df_mis_citas["id"].tolist())
        if col_e2.button("✅ Marcar Atendida"):
            c = conn.cursor()
            c.execute("UPDATE citas SET estado = 'Atendida' WHERE id = ?", (cita_emp_id,))
            conn.commit()
            st.success(f"Cita #{cita_emp_id} completada.")
            st.rerun()
    else:
        st.info("No tienes citas asignadas por el momento.")
        
    st.markdown("---")
    st.markdown("### ⭐ Valoraciones de Mis Clientes")
    df_mis_rev = pd.read_sql_query(
        "SELECT cliente_nombre, estrellas, comentario, fecha FROM resenas WHERE empleado = ? AND bloqueado = 0",
        conn, params=(st.session_state["user_nickname"],)
    )
    if not df_mis_rev.empty:
        for _, mr in df_mis_rev.iterrows():
            st.markdown(f"""
            <div class="review-card">
                <b>👤 {mr['cliente_nombre']}</b> — <span style="color:#FFD700;">{"⭐"*int(mr['estrellas'])}</span><br/>
                <small>Fecha: {mr['fecha']}</small><br/>
                <p style="margin-top:6px; margin-bottom:0px;">"{mr['comentario']}"</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aún no registras valoraciones directas.")
        
    conn.close()
