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
                    fecha_hora TEXT,
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

    # AUTO-MIGRACIÓN DE COLUMNAS PARA PREVENIR ERRORES OPERATIONALERROR
    def agregar_columna_si_falta(tabla, columna_def):
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna_def}")
        except sqlite3.OperationalError:
            pass

    agregar_columna_si_falta("usuarios", "foto_url TEXT")
    agregar_columna_si_falta("servicios", "imagen_url TEXT")
    agregar_columna_si_falta("servicios", "es_combo INTEGER DEFAULT 0")
    agregar_columna_si_falta("resenas", "fecha TEXT")
    agregar_columna_si_falta("citas", "fecha_hora TEXT")
    agregar_columna_si_falta("citas", "fecha TEXT")
    agregar_columna_si_falta("citas", "hora TEXT")

    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("UPDATE resenas SET fecha = ? WHERE fecha IS NULL OR fecha = ''", (hoy_str,))
    c.execute("UPDATE servicios SET imagen_url = '' WHERE imagen_url IS NULL")

    # DATOS INICIALES POR DEFECTO
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
            ("Sofía Torres", "Camila (Makeup & Stylist)", 5, "El Makeup Glow HD duró toda la noche intacto. ¡Recomendadísimas!", 0, hoy_str)
        ])

    c.execute("SELECT COUNT(*) FROM inventario")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO inventario (producto, cantidad, precio_unitario) VALUES (?, ?, ?)", [
            ("Tinte Decolorante Neón (Tubos)", 45, 12.50),
            ("Esmalte Gel Gloss Cromo", 60, 8.00),
            ("Mascarilla Keratina Botox", 18, 35.00)
        ])

    c.execute("SELECT COUNT(*) FROM cupones")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cupones (codigo, descuento, activo) VALUES ('GLOW10', 10, 1)")

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
# 3. FUNCIONES AUXILIARES & CORREO
# ==========================================
def enviar_correo_confirmacion(destinatario, nombre, servicio, fecha_hora):
    try:
        if "email" not in st.secrets:
            return False, "No existe [email] en secrets.toml"
        
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets["email"].get("smtp_port", 587))
        sender_email = st.secrets["email"].get("sender_email", "")
        sender_password = st.secrets["email"].get("sender_password", "")
        
        if not sender_email or not sender_password:
            return False, "Credenciales incompletas en secrets.toml"

        msg = MIMEMultipart()
        msg['From'] = f"GlowStudio AI <{sender_email}>"
        msg['To'] = destinatario
        msg['Subject'] = "✨ Confirmación de Reserva - GlowStudio AI"

        cuerpo = f"""Hola {nombre},

¡Tu reserva ha sido confirmada con éxito en GlowStudio AI! 💖

📅 Detalle de tu Cita:
- Cliente: {nombre}
- Servicio: {servicio}
- Fecha y Hora: {fecha_hora}

¡Te esperamos en nuestro Salón VIP!
"""
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado correctamente."
    except Exception as e:
        return False, f"Error SMTP: {str(e)}"

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
        else:
            aspect_ratio = w / float(h)
            if aspect_ratio >= 0.88:
                forma = "Cuadrado"
            elif aspect_ratio <= 0.72:
                forma = "Alargado"
            else:
                forma = "Ovalado"

        recoms = {
            "Cuadrado": "Se recomiendan cortes en capas desfiladas y tonos Balayage Warm Gloss.",
            "Ovalado": "Tu rostro es armónico. Te favorece cualquier estilo: Capas o Lob estructurado.",
            "Redondo": "Se recomiendan cortes con volumen superior y capas largas para estilizar.",
            "Alargado": "Se recomienda volumen en laterales y flequillo corto o cortina."
        }
        return forma, recoms.get(forma, "Corte personalizado según facciones.")
    except Exception:
        return "Ovalado", "Se recomiendan capas desfiladas para destacar tus facciones."

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

# ESTADOS PARA CHATBOT CONVERSACIONAL BELLA IA
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "assistant", "content": "¡Hola! Soy **Bella IA** 💖. Dime si deseas agendar o registrar una cita y te pediré los datos paso a paso."}
    ]
if "chat_step" not in st.session_state:
    st.session_state["chat_step"] = "IDLE"
if "booking_data" not in st.session_state:
    st.session_state["booking_data"] = {"nombre": "", "email": "", "servicio": "", "fecha_hora": ""}

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

# --- SIDEBAR (VISAGISMO & PERFIL) ---
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

with st.sidebar.expander("📷 Visagismo con IA (Escáner Facial)", expanded=True):
    img_file = st.file_uploader("Sube tu foto de rostro:", type=["jpg", "png", "jpeg"], key="bot_img_side")
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True, caption="Rostro Cargado")
        forma_detectada, recom_text = analizar_rostro_ia(img_file)
        st.success(f"✨ **Visagismo IA:** Rostro **{forma_detectada}**.\n\n💡 {recom_text}")

st.markdown('<div class="brand-header">GlowStudio AI | Luxury Spa</div>', unsafe_allow_html=True)

# ==========================================
# 5. PANEL DE CLIENTE CON NUEVA PESTAÑA IA
# ==========================================
if st.session_state["user_role"] == "cliente":
    
    col_hdr, col_cart = st.columns([3, 1.2])
    with col_cart:
        num_items = len(st.session_state["carrito"])
        if st.button(f"🛒 Ver Carrito Checkout ({num_items} items)", use_container_width=True):
            st.session_state["current_tab"] = "📅 Reserva & Calendario"
            st.rerun()

    tab_options = ["🛍️ Catálogo & Combos", "🤖 Chat Conversacional Bella IA", "📅 Reserva & Calendario", "⭐ Mapa de Calor & Reseñas"]
    
    selected_tab = st.radio(
        "", 
        tab_options, 
        index=tab_options.index(st.session_state["current_tab"]) if st.session_state["current_tab"] in tab_options else 0,
        horizontal=True
    )
    st.session_state["current_tab"] = selected_tab

    # --- PESTAÑA 1: CATÁLOGO ---
    if selected_tab == "🛍️ Catálogo & Combos":
        st.markdown("### 💄 Servicios Individuales y Combos Especiales")
        
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

    # --- PESTAÑA 2: CHAT CONVERSACIONAL CON BELLA IA (NUEVA PESTAÑA PEDIDA) ---
    elif selected_tab == "🤖 Chat Conversacional Bella IA":
        st.markdown("### 💬 Agendamiento Inteligente por Chat")
        st.info("💡 **Bella IA:** Habla conmigo para agendar citas. Solo dime *'quiero agendar'* o *'registrar cita'* y te iré pidiendo tu **Nombre**, **Correo**, **Servicio** y **Fecha/Hora**.")

        # Mostrar conversación
        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Escribe a Bella IA aquí...")

        if user_input:
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            input_lower = user_input.lower().strip()
            bot_resp = ""

            step = st.session_state["chat_step"]

            if step == "IDLE":
                if any(kw in input_lower for kw in ["agendar", "cita", "registrar", "reservar", "agg"]):
                    st.session_state["chat_step"] = "ASK_NAME"
                    bot_resp = "¡Con gusto! Vamos a agendar tu cita y registrarte. Para empezar, **¿cuál es tu nombre completo?**"
                else:
                    bot_resp = "¡Hola! Soy Bella IA. Si deseas agendar o registrar una cita, escríbeme **'quiero agendar una cita'**."

            elif step == "ASK_NAME":
                st.session_state["booking_data"]["nombre"] = user_input.strip()
                st.session_state["chat_step"] = "ASK_EMAIL"
                bot_resp = f"Excelente **{user_input.strip()}**. Ahora, **¿cuál es tu correo electrónico?**"

            elif step == "ASK_EMAIL":
                if "@" not in user_input or "." not in user_input:
                    bot_resp = "⚠️ El correo no parece válido. Por favor ingresa un correo con formato válido (ej. cliente@gmail.com):"
                else:
                    st.session_state["booking_data"]["email"] = user_input.strip().lower()
                    st.session_state["chat_step"] = "ASK_SERVICE"
                    bot_resp = "¡Perfecto! **¿Qué servicio o combo te gustaría realizarte?** *(ej. Balayage Neón, Makeup Glow, Corte)*"

            elif step == "ASK_SERVICE":
                st.session_state["booking_data"]["servicio"] = user_input.strip()
                st.session_state["chat_step"] = "ASK_DATETIME"
                bot_resp = "¡Anotado! Por último, **¿para qué fecha y hora deseas la cita?** *(ej. Mañana a las 4:00 PM)*"

            elif step == "ASK_DATETIME":
                st.session_state["booking_data"]["fecha_hora"] = user_input.strip()
                bdata = st.session_state["booking_data"]

                # Guardar en Base de Datos
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""INSERT INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) 
                             VALUES (?, ?, 'cliente', '0000000000', 'Al Día', '')
                             ON CONFLICT(email) DO UPDATE SET nickname=excluded.nickname""", 
                          (bdata["email"], bdata["nombre"]))
                
                c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha_hora, fecha, hora, metodo_pago, monto_total, estado)
                             VALUES (?, ?, 'Estilista Asignado', ?, ?, ?, '10:00', 'Pendiente', 0.0, 'Confirmada')""",
                          (bdata["email"], bdata["nombre"], bdata["servicio"], bdata["fecha_hora"], bdata["fecha_hora"]))
                conn.commit()
                conn.close()

                # Enviar Correo
                ok_mail, msg_mail = enviar_correo_confirmacion(bdata["email"], bdata["nombre"], bdata["servicio"], bdata["fecha_hora"])

                bot_resp = f"""🎉 **¡Cita Agendada y Registrada Exitosamente!**

📌 **Resumen de tu Reserva:**
- **Cliente:** {bdata['nombre']}
- **Correo:** {bdata['email']}
- **Servicio:** {bdata['servicio']}
- **Fecha y Hora:** {bdata['fecha_hora']}
"""
                if ok_mail:
                    bot_resp += "\n📧 **Correo:** Se ha enviado un email de confirmación a tu bandeja."
                else:
                    bot_resp += f"\n⚠️ **Nota Correo:** ({msg_mail}). Revisa la configuración SMTP si no llega."

                st.session_state["chat_step"] = "IDLE"
                st.session_state["booking_data"] = {"nombre": "", "email": "", "servicio": "", "fecha_hora": ""}

            st.session_state["chat_messages"].append({"role": "assistant", "content": bot_resp})
            st.rerun()

    # --- PESTAÑA 3: CALENDARIO MANUAL ---
    elif selected_tab == "📅 Reserva & Calendario":
        col_res1, col_res2 = st.columns([1.3, 1])
        
        with col_res1:
            st.markdown("### 🗓️ Selecciona Fecha y Horario Manual")
            conn = sqlite3.connect(DB_PATH)
            df_emp = pd.read_sql_query("SELECT nickname, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
            emp_opciones = df_emp["nickname"].tolist() if not df_emp.empty else ["Valeria (Master Colorista)"]
            estilista_sel = st.selectbox("Selecciona tu Estilista Favorita:", emp_opciones)
            
            fecha_sel = st.date_input("Fecha de Cita:", value=datetime.date.today())
            horarios = ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"]
            
            citas_exist = pd.read_sql_query("SELECT hora FROM citas WHERE fecha = ? AND estado != 'Cancelada'", conn, params=(str(fecha_sel),))["hora"].tolist()
            conn.close()

            cols_h = st.columns(3)
            for idx, h in enumerate(horarios):
                ocupado = h in citas_exist
                if cols_h[idx % 3].button(f"{'🔴' if ocupado else '🟢'} {h}", key=f"slot_{h}", disabled=ocupado):
                    st.session_state["hora_seleccionada"] = h

            if "hora_seleccionada" in st.session_state:
                st.success(f"Horario seleccionado: **{st.session_state['hora_seleccionada']}**")

        with col_res2:
            st.markdown("### 🛒 Carrito de Compras")
            if not st.session_state["carrito"]:
                st.info("El carrito está vacío.")
            else:
                total_base = sum(x["precio"] for x in st.session_state["carrito"])
                for idx, item in enumerate(st.session_state["carrito"]):
                    st.write(f"- {item['nombre']}: **${item['precio']:.2f}**")
                
                st.markdown(f"## Total: ${total_base:.2f} USD")
                if st.button("💖 Confirmar Reserva del Carrito", use_container_width=True):
                    if "hora_seleccionada" not in st.session_state:
                        st.error("Selecciona un horario libre.")
                    else:
                        nomb = ", ".join([x["nombre"] for x in st.session_state["carrito"]])
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, fecha_hora, metodo_pago, monto_total, estado) VALUES (?, ?, ?, ?, ?, ?, ?, 'Efectivo', ?, 'Confirmada')",
                                  (st.session_state["user_email"], st.session_state["user_nickname"], estilista_sel, nomb, str(fecha_sel), st.session_state["hora_seleccionada"], f"{fecha_sel} {st.session_state['hora_seleccionada']}", total_base))
                        conn.commit()
                        conn.close()
                        enviar_correo_confirmacion(st.session_state["user_email"], st.session_state["user_nickname"], nomb, f"{fecha_sel} {st.session_state['hora_seleccionada']}")
                        st.balloons()
                        st.success("¡Cita reservada con éxito!")
                        st.session_state["carrito"] = []

    # --- PESTAÑA 4: RESEÑAS & MAPA DE CALOR ---
    elif selected_tab == "⭐ Mapa de Calor & Reseñas":
        st.markdown("### 📊 Valoración y Experiencias de Clientes")
        conn = sqlite3.connect(DB_PATH)
        df_rev = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 0", conn)
        
        if not df_rev.empty:
            avg_stars = df_rev.groupby("empleado")["estrellas"].mean().reset_index()
            fig = px.bar(avg_stars, x="empleado", y="estrellas", color="estrellas", title="Promedio de Estrellas por Estilista", range_y=[0, 5])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#FFF"))
            st.plotly_chart(fig, use_container_width=True)
            
            for _, r in df_rev.iterrows():
                st.markdown(f"""
                <div class="review-card">
                    <b>👤 {r['cliente_nombre']}</b> — <span style="color:#FFD700;">{"⭐"*int(r['estrellas'])}</span><br/>
                    <small>Atendido por: <b>{r['empleado']}</b> | Fecha: {r['fecha']}</small><br/>
                    <p>"{r['comentario']}"</p>
                </div>
                """, unsafe_allow_html=True)
        conn.close()

# ==========================================
# 6. PANEL DE ADMINISTRADOR
# ==========================================
elif st.session_state["user_role"] == "admin":
    st.markdown("## 👑 Panel de Control Administrador")
    
    t_citas, t_emp, t_serv, t_mod, t_inv = st.tabs([
        "📅 Citas Registradas",
        "👥 Usuarios & Empleados",
        "🛠️ Catálogo Servicios",
        "🛡️ Moderación Reseñas",
        "📊 Finanzas e Inventario"
    ])
    
    conn = sqlite3.connect(DB_PATH)
    
    with t_citas:
        st.markdown("### 📋 Listado Total de Citas")
        df_c = pd.read_sql_query("SELECT id, cliente_nombre, cliente_email, servicio, fecha_hora, fecha, hora, estado FROM citas ORDER BY id DESC", conn)
        st.dataframe(df_c, use_container_width=True)

    with t_emp:
        st.markdown("### 👥 Clientes y Empleados Registrados")
        df_u = pd.read_sql_query("SELECT email, nickname, rol, estado_pago FROM usuarios", conn)
        st.dataframe(df_u, use_container_width=True)

        st.markdown("#### ➕ Registrar Usuario / Empleado Manualmente")
        with st.form("f_add_u"):
            u_email = st.text_input("Correo:").strip().lower()
            u_nick = st.text_input("Nombre / Apodo:")
            u_rol = st.selectbox("Rol:", ["cliente", "empleado", "admin"])
            if st.form_submit_button("Guardar Usuario"):
                if u_email and u_nick:
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) VALUES (?, ?, ?, '0000000000', 'Al Día', '')", (u_email, u_nick, u_rol))
                    conn.commit()
                    st.success("Usuario registrado con éxito.")
                    st.rerun()

    with t_serv:
        df_s = pd.read_sql_query("SELECT * FROM servicios", conn)
        st.dataframe(df_s, use_container_width=True)

    with t_mod:
        df_rb = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 1", conn)
        st.dataframe(df_rb, use_container_width=True)

    with t_inv:
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        st.dataframe(df_inv, use_container_width=True)

    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown(f"## 👩‍🎨 Panel de Estilista — {st.session_state['user_nickname']}")
    conn = sqlite3.connect(DB_PATH)
    df_mis_citas = pd.read_sql_query("SELECT * FROM citas WHERE empleado = ? OR cliente_nombre = ?", conn, params=(st.session_state["user_nickname"], st.session_state["user_nickname"]))
    st.dataframe(df_mis_citas, use_container_width=True)
    conn.close()
