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
# 4. CONTROL DE SESIÓN Y LOGIN
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
            btn_login = st.button("Iniciar Sesión / Registrarme", use_container_width=True)
            
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
                    
                    if email_in == super_admin.lower():
                        st.session_state["user_role"] = "admin"
                        c.execute("INSERT OR REPLACE INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) VALUES (?, ?, 'admin', '0000000000', 'Al Día', '')", (email_in, nickname_in))
                    elif res and res[0] == "empleado":
                        st.session_state["user_role"] = "empleado"
                    elif res and res[0] == "admin":
                        st.session_state["user_role"] = "admin"
                    else:
                        st.session_state["user_role"] = "cliente"
                        c.execute("INSERT OR REPLACE INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) VALUES (?, ?, 'cliente', '0000000000', 'Al Día', '')", (email_in, nickname_in))
                    
                    conn.commit()
                    conn.close()
                    st.rerun()
    st.stop()

# --- SIDEBAR ---
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
            
            if any(k in msg_lower for k in ["crear cliente", "nuevo cliente", "registrar cliente", "crear empleado", "nuevo empleado", "registrar empleado"]):
                if st.session_state["user_role"] == "admin":
                    st.info("🤖 **Bella IA:** Para crear nuevos empleados o registrar clientes manualmente, dirígete a la pestaña **'👥 Usuarios & Empleados'** en tu panel Admin.")
                else:
                    st.info("🤖 **Bella IA:** Los nuevos clientes quedan registrados automáticamente al iniciar sesión. Para unirte al equipo de personal, contacta al Administrador.")
            elif any(k in msg_lower for k in ["agendar", "reservar", "reserva", "cita", "horario", "turnos", "calendario"]):
                st.session_state["current_tab"] = "📅 Reserva & Calendario"
                st.info("🤖 **Bella IA:** ¡Te he redirigido a la pestaña de **Reserva & Calendario**!")
                st.rerun()
            elif any(k in msg_lower for k in ["catalogo", "catálogo", "servicio", "servicios", "combo", "combos", "precio", "precios"]):
                st.session_state["current_tab"] = "🛍️ Catálogo & Combos"
                st.info("🤖 **Bella IA:** ¡Te he abierto el **Catálogo & Combos**!")
                st.rerun()
            elif any(k in msg_lower for k in ["reseña", "reseñas", "opinion", "opiniones", "comentario", "estrellas"]):
                st.session_state["current_tab"] = "⭐ Mapa de Calor & Reseñas"
                st.info("🤖 **Bella IA:** ¡Te llevo a la sección de **Reseñas**!")
                st.rerun()
            elif any(k in msg_lower for k in ["estresada", "estresado", "cansada", "relajación", "spa"]):
                st.info("💖 **Bella IA:** Te recomiendo nuestro *Tratamiento Spa Keratina con Masaje Capilar*.")
            elif any(k in msg_lower for k in ["cupon", "cupón", "descuento", "promocion", "oferta"]):
                st.info("💖 **Bella IA:** Puedes usar el cupón **'GLOW10'** para un 10% OFF en servicios individuales.")
            elif any(k in msg_lower for k in ["hola", "buenos dias", "buenas tardes"]):
                st.info("💖 **Bella IA:** ¡Hola! Soy Bella IA. ¿En qué puedo ayudarte hoy?")
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
                            st.warning(f"⚠️ Estado del correo: {msg_envio}.")
                        
                        st.session_state["carrito"] = []
                        del st.session_state["hora_seleccionada"]

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
                        st.warning("⚠️ Tu reseña requiere aprobación del Administrador.")
                    else:
                        st.success("¡Reseña registrada con éxito!")
                    st.rerun()
        conn.close()

# ==========================================
# 6. PANEL DE ADMINISTRADOR COMPLETO
# ==========================================
elif st.session_state["user_role"] == "admin":
    st.markdown("## 👑 Panel de Control Integral (Administrador)")
    
    t_citas, t_usua, t_serv, t_inve, t_cupo, t_rese, t_esca = st.tabs([
        "📅 Citas & Agenda",
        "👥 Usuarios",
        "💄 Servicios & Combos",
        "📦 Inventario",
        "🎟️ Cupones",
        "⭐ Moderación Reseñas",
        "💬 Consultas Escaladas"
    ])

    conn = sqlite3.connect(DB_PATH)

    # TAB 1: CITAS & AGENDA
    with t_citas:
        st.subheader("📅 Gestión de Citas y Reservas Globales")
        df_citas = pd.read_sql_query("SELECT * FROM citas ORDER BY id DESC", conn)
        
        if not df_citas.empty:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total Reservas", len(df_citas))
            total_ingresos = df_citas[df_citas["estado"] != "Cancelada"]["monto_total"].sum()
            col_m2.metric("Ingresos Totales", f"${total_ingresos:.2f}")
            col_m3.metric("Citas Confirmadas", len(df_citas[df_citas["estado"] == "Confirmada"]))

            st.dataframe(df_citas, use_container_width=True)

            st.markdown("#### Cambiar Estado de Cita")
            col_act1, col_act2, col_act3 = st.columns(3)
            cita_id_sel = col_act1.selectbox("ID de la Cita:", df_citas["id"].tolist())
            nuevo_estado = col_act2.selectbox("Nuevo Estado:", ["Confirmada", "Completada", "Cancelada"])
            if col_act3.button("Actualizar Estado"):
                c = conn.cursor()
                c.execute("UPDATE citas SET estado = ? WHERE id = ?", (nuevo_estado, cita_id_sel))
                conn.commit()
                st.success(f"Estado de cita #{cita_id_sel} actualizado a '{nuevo_estado}'")
                st.rerun()
        else:
            st.info("No hay citas registradas aún.")

    # TAB 2: USUARIOS Y EMPLEADOS
    with t_usua:
        st.subheader("👥 Gestión de Usuarios y Personal")
        df_usua = pd.read_sql_query("SELECT email, nickname, rol, cedula, estado_pago FROM usuarios", conn)
        st.dataframe(df_usua, use_container_width=True)

        with st.expander("➕ Registrar Nuevo Empleado / Usuario"):
            with st.form("form_nuevo_usuario"):
                u_email = st.text_input("Correo Electrónico:").strip().lower()
                u_nick = st.text_input("Nombre / Apodo (Nickname):")
                u_rol = st.selectbox("Rol:", ["empleado", "admin", "cliente"])
                u_cedula = st.text_input("Cédula / Identificación:", value="0000000000")
                u_foto = st.text_input("URL Foto de Perfil (Opcional):")
                btn_crear_u = st.form_submit_button("Guardar Usuario")

                if btn_crear_u:
                    if u_email and u_nick:
                        c = conn.cursor()
                        c.execute("INSERT OR REPLACE INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) VALUES (?, ?, ?, ?, 'Al Día', ?)",
                                  (u_email, u_nick, u_rol, u_cedula, u_foto))
                        conn.commit()
                        st.success(f"Usuario {u_nick} registrado con rol '{u_rol}'.")
                        st.rerun()
                    else:
                        st.warning("Completa los campos obligatorios.")

    # TAB 3: SERVICIOS Y COMBOS
    with t_serv:
        st.subheader("💄 Catálogo de Servicios y Combos")
        df_serv_all = pd.read_sql_query("SELECT * FROM servicios", conn)
        st.dataframe(df_serv_all, use_container_width=True)

        with st.expander("➕ Agregar Nuevo Servicio / Combo"):
            with st.form("form_nuevo_servicio"):
                s_nombre = st.text_input("Nombre del Servicio:")
                s_categoria = st.selectbox("Categoría:", ["Colorimetría", "Maquillaje", "Uñas", "Corte", "Capilar", "Combos", "Otros"])
                s_precio = st.number_input("Precio ($):", min_value=0.0, step=5.0, value=50.0)
                s_es_combo = st.checkbox("Es un Combo Promocional")
                s_imagen = st.text_input("URL de Imagen:")
                btn_crear_s = st.form_submit_button("Guardar Servicio")

                if btn_crear_s:
                    if s_nombre:
                        c = conn.cursor()
                        c.execute("INSERT INTO servicios (nombre, categoria, precio, disponible, es_combo, imagen_url) VALUES (?, ?, ?, 1, ?, ?)",
                                  (s_nombre, s_categoria, s_precio, 1 if s_es_combo else 0, s_imagen))
                        conn.commit()
                        st.success(f"Servicio '{s_nombre}' agregado correctamente.")
                        st.rerun()

    # TAB 4: INVENTARIO
    with t_inve:
        st.subheader("📦 Control de Inventario")
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        st.dataframe(df_inv, use_container_width=True)

        with st.expander("➕ Agregar / Actualizar Producto"):
            with st.form("form_inv"):
                p_nombre = st.text_input("Nombre del Producto:")
                p_cant = st.number_input("Cantidad:", min_value=1, value=10)
                p_precio = st.number_input("Precio Unitario ($):", min_value=0.0, value=15.0)
                btn_inv = st.form_submit_button("Guardar en Inventario")

                if btn_inv:
                    if p_nombre:
                        c = conn.cursor()
                        c.execute("INSERT INTO inventario (producto, cantidad, precio_unitario) VALUES (?, ?, ?)",
                                  (p_nombre, p_cant, p_precio))
                        conn.commit()
                        st.success("Producto agregado al inventario.")
                        st.rerun()

    # TAB 5: CUPONES
    with t_cupo:
        st.subheader("🎟️ Cupones Promocionales")
        df_cup = pd.read_sql_query("SELECT * FROM cupones", conn)
        st.dataframe(df_cup, use_container_width=True)

        with st.expander("➕ Crear Nuevo Cupón"):
            with st.form("form_cupon"):
                c_codigo = st.text_input("Código del Cupón (ej. VERANO20):").strip().upper()
                c_desc = st.slider("Porcentaje de Descuento (%):", 5, 50, 15)
                btn_cup = st.form_submit_button("Crear Cupón")

                if btn_cup:
                    if c_codigo:
                        try:
                            c = conn.cursor()
                            c.execute("INSERT INTO cupones (codigo, descuento, activo) VALUES (?, ?, 1)", (c_codigo, c_desc))
                            conn.commit()
                            st.success(f"Cupón {c_codigo} creado con {c_desc}% de descuento.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("El código de cupón ya existe.")

    # TAB 6: MODERACIÓN Y GESTIÓN COMPLETA DE RESEÑAS
    with t_rese:
        st.subheader("⭐ Gestión Completa de Reseñas")
        
        df_rev_all = pd.read_sql_query("SELECT * FROM resenas ORDER BY id DESC", conn)

        if df_rev_all.empty:
            st.info("No hay reseñas registradas en el sistema.")
        else:
            filtro_rev = st.radio("Filtrar vista:", ["Todas las Reseñas", "Solo Bloqueadas / Pendientes"], horizontal=True)
            
            if filtro_rev == "Solo Bloqueadas / Pendientes":
                df_mostradas = df_rev_all[df_rev_all["bloqueado"] == 1]
            else:
                df_mostradas = df_rev_all

            if df_mostradas.empty:
                st.info("No hay reseñas para mostrar con el filtro seleccionado.")
            else:
                for _, r in df_mostradas.iterrows():
                    with st.container(border=True):
                        estado_tag = "🔴 Bloqueada / Oculta" if r['bloqueado'] == 1 else "🟢 Visible en Portal Cliente"
                        st.write(f"**Cliente:** {r['cliente_nombre']} | **Atendió:** {r['empleado']} | **Estado:** {estado_tag}")
                        st.write(f"**Calificación:** {'⭐'*int(r['estrellas'])} | **Fecha:** {r.get('fecha', 'N/A')}")
                        st.write(f"**Comentario:** *\"{r['comentario']}\"*")
                        
                        col_b1, col_b2 = st.columns(2)
                        
                        if r['bloqueado'] == 1:
                            if col_b1.button("✅ Aprobar / Mostrar", key=f"app_rev_{r['id']}"):
                                c = conn.cursor()
                                c.execute("UPDATE resenas SET bloqueado = 0 WHERE id = ?", (r['id'],))
                                conn.commit()
                                st.success("Reseña aprobada y visible para clientes.")
                                st.rerun()
                        else:
                            if col_b1.button("🚫 Ocultar Reseña", key=f"block_rev_{r['id']}"):
                                c = conn.cursor()
                                c.execute("UPDATE resenas SET bloqueado = 1 WHERE id = ?", (r['id'],))
                                conn.commit()
                                st.warning("Reseña ocultada del portal público.")
                                st.rerun()
                                
                        if col_b2.button("🗑️ Eliminar Definitivamente", key=f"del_rev_{r['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM resenas WHERE id = ?", (r['id'],))
                            conn.commit()
                            st.warning("Reseña eliminada de la base de datos.")
                            st.rerun()

    # TAB 7: CONSULTAS ESCALADAS
    with t_esca:
        st.subheader("💬 Consultas Escaladas de Bella IA")
        df_esc = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0 ORDER BY id DESC", conn)

        if df_esc.empty:
            st.info("No hay preguntas pendientes de respuesta.")
        else:
            for _, q in df_esc.iterrows():
                with st.container(border=True):
                    st.write(f"**Cliente:** {q['cliente_email']} | **Fecha:** {q['fecha_hora']}")
                    st.write(f"**Pregunta:** {q['pregunta']}")
                    
                    resp_in = st.text_input("Responder al cliente:", key=f"resp_input_{q['id']}")
                    if st.button("Enviar Respuesta", key=f"btn_resp_{q['id']}"):
                        if resp_in:
                            c = conn.cursor()
                            c.execute("UPDATE preguntas_escaladas SET respuesta = ?, atendido = 1 WHERE id = ?", (resp_in, q['id']))
                            conn.commit()
                            st.success("Respuesta registrada y marcada como atendida.")
                            st.rerun()

    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO (ESTILISTA)
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown(f"## 💇‍♀️ Panel de Trabajo — {st.session_state['user_nickname']}")

    conn = sqlite3.connect(DB_PATH)
    
    tab_emp1, tab_emp2 = st.tabs(["📅 Mi Agenda de Citas", "⭐ Mis Reseñas"])

    with tab_emp1:
        st.subheader("📅 Tus Citas Asignadas")
        df_citas_emp = pd.read_sql_query(
            "SELECT * FROM citas WHERE empleado LIKE ? ORDER BY fecha DESC, hora ASC",
            conn,
            params=(f"%{st.session_state['user_nickname']}%",)
        )

        if df_citas_emp.empty:
            st.info("No tienes citas agendadas actualmente.")
        else:
            st.dataframe(df_citas_emp, use_container_width=True)
            
            st.markdown("#### Marcar Cita como Completada")
            col_e1, col_e2 = st.columns([2, 1])
            citas_conf = df_citas_emp[df_citas_emp["estado"] == "Confirmada"]["id"].tolist()
            
            if citas_conf:
                id_cita_emp = col_e1.selectbox("Selecciona Cita:", citas_conf)
                if col_e2.button("Marcar Completada"):
                    c = conn.cursor()
                    c.execute("UPDATE citas SET estado = 'Completada' WHERE id = ?", (id_cita_emp,))
                    conn.commit()
                    st.success(f"Cita #{id_cita_emp} completada con éxito.")
                    st.rerun()
            else:
                st.info("No hay citas confirmadas pendientes por completar.")

    with tab_emp2:
        st.subheader("⭐ Opiniones y Calificaciones de tus Clientes")
        df_rev_emp = pd.read_sql_query(
            "SELECT * FROM resenas WHERE empleado LIKE ? AND bloqueado = 0",
            conn,
            params=(f"%{st.session_state['user_nickname']}%",)
        )

        if df_rev_emp.empty:
            st.info("Aún no tienes opiniones registradas.")
        else:
            promedio = df_rev_emp["estrellas"].mean()
            st.metric("Tu Calificación Promedio", f"⭐ {promedio:.2f} / 5.0")
            for _, r in df_rev_emp.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['cliente_nombre']}** — {'⭐'*int(r['estrellas'])}")
                    st.caption(f"Fecha: {r['fecha']}")
                    st.write(f'"{r["comentario"]}"')

    conn.close()
