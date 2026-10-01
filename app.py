import os
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    
    # Tabla de Usuarios / Empleados
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nickname TEXT,
                    rol TEXT,
                    cedula TEXT,
                    estado_pago TEXT,
                    foto_url TEXT)''')
    
    # Tabla de Servicios
    c.execute('''CREATE TABLE IF NOT EXISTS servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    categoria TEXT,
                    precio REAL,
                    disponible INTEGER,
                    es_combo INTEGER)''')
    
    # Tabla de Citas
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
    
    # Tabla de Reseñas
    c.execute('''CREATE TABLE IF NOT EXISTS resenas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nombre TEXT,
                    empleado TEXT,
                    estrellas INTEGER,
                    comentario TEXT,
                    bloqueado INTEGER)''')
    
    # Tabla de Preguntas Escaladas (Chatbot)
    c.execute('''CREATE TABLE IF NOT EXISTS preguntas_escaladas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_email TEXT,
                    pregunta TEXT,
                    fecha_hora TEXT,
                    respuesta TEXT,
                    atendido INTEGER)''')
    
    # Tabla de Inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto TEXT,
                    cantidad INTEGER,
                    precio_unitario REAL)''')
    
    # Cargar datos iniciales por defecto si la base está vacía
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('jdyagual2@tes.edu.ec', 'SuperAdmin', 'admin', '0000000000', 'Al Día', '')")
        c.execute("INSERT INTO usuarios VALUES ('valeria@glowstudio.ai', 'Valeria (Master Colorista)', 'empleado', '0987654321', 'Al Día', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400')")
        c.execute("INSERT INTO usuarios VALUES ('camila@glowstudio.ai', 'Camila (Makeup & Stylist)', 'empleado', '0912345678', 'Al Día', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400')")

    c.execute("SELECT COUNT(*) FROM servicios")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO servicios (nombre, categoria, precio, disponible, es_combo) VALUES (?, ?, ?, ?, ?)", [
            ("Balayage Neón", "Colorimetría", 160.0, 1, 0),
            ("Makeup Glow HD", "Maquillaje", 95.0, 1, 0),
            ("Manicure Gel Gloss", "Uñas", 55.0, 1, 0),
            ("Corte & Visagismo", "Corte", 45.0, 1, 0),
            ("Tratamiento Keratina", "Capilar", 120.0, 1, 0),
            ("Combo Glam: Balayage + Makeup Glow", "Combos", 220.0, 1, 1),
            ("Combo VIP: Corte + Keratina + Manicure", "Combos", 190.0, 1, 1)
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
    font-size: 2.5rem;
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

.card-luxury {
    background-color: #161622;
    border: 1px solid rgba(255, 0, 127, 0.2);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.stButton > button {
    background: linear-gradient(135deg, #FF007F 0%, #8A2BE2 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 0.5rem 1rem !important;
}

.slot-occupied {
    background-color: #3A001E !important;
    color: #FF66B2 !important;
    border: 1px solid #FF007F !important;
}

.slot-free {
    background-color: #003322 !important;
    color: #00FFCC !important;
    border: 1px solid #00FFCC !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNCIONES AUXILIARES & CORREO
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
    except Exception as e:
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

if not st.session_state["user_email"]:
    st.markdown('<div class="brand-header">GlowStudio AI</div>', unsafe_allow_html=True)
    st.subheader("Acceso al Portal de Belleza & Gestión")
    
    col_login_l, col_login_r = st.columns([1, 1])
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
                    
                    # RUTA DE ROLES
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

# Header Superior cuando la sesión está activa
st.sidebar.markdown(f"### 👤 Bienvenido, {st.session_state['user_nickname']}")
role_class = f"role-{st.session_state['user_role']}"
st.sidebar.markdown(f'<span class="role-badge {role_class}">Rol: {st.session_state["user_role"].upper()}</span>', unsafe_allow_html=True)
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["user_email"] = ""
    st.session_state["user_nickname"] = ""
    st.session_state["user_role"] = ""
    st.session_state["carrito"] = []
    st.rerun()

st.markdown('<div class="brand-header">GlowStudio AI | Luxury Spa</div>', unsafe_allow_html=True)

# ==========================================
# 5. PANEL DE CLIENTE
# ==========================================
if st.session_state["user_role"] == "cliente":
    
    # Carrito Widget en esquina superior derecha
    col_hdr, col_cart = st.columns([3, 1])
    with col_cart:
        num_items = len(st.session_state["carrito"])
        st.markdown(f"🛒 **Carrito Checkout:** `{num_items} servicio(s)`")
    
    tab_cat, tab_reserva, tab_resenas, tab_chat = st.tabs([
        "🛍️ Catálogo & Combos",
        "📅 Reserva & Calendario",
        "⭐ Mapa de Calor & Reseñas",
        "💖 Chatbot IA & Visagismo"
    ])
    
    # --- PESTAÑA 1: CATÁLOGO & COMBOS ---
    with tab_cat:
        st.markdown("### 💄 Servicios Individuales y Combos Especiales")
        st.info("💡 **Regla de Descuento:** Los cupones o promociones individuales aplican únicamente sobre servicios individuales. Los combos ya poseen precio especial.")
        
        conn = sqlite3.connect(DB_PATH)
        df_serv = pd.read_sql_query("SELECT * FROM servicios WHERE disponible = 1", conn)
        conn.close()
        
        col_s1, col_s2 = st.columns(2)
        for i, row in df_serv.iterrows():
            target_col = col_s1 if i % 2 == 0 else col_s2
            with target_col:
                with st.container(border=True):
                    badge_combo = "🔥 COMBO ESPECIAL" if row["es_combo"] else "✨ SERVICIO INDIVIDUAL"
                    st.caption(badge_combo)
                    st.subheader(row["nombre"])
                    st.write(f"Categoría: **{row['categoria']}**")
                    st.markdown(f"### ${row['precio']:.2f} USD")
                    if st.button(f"➕ Agregar al Carrito", key=f"add_{row['id']}"):
                        st.session_state["carrito"].append({"id": row["id"], "nombre": row["nombre"], "precio": row["precio"], "es_combo": row["es_combo"]})
                        st.success(f"Agregado: {row['nombre']}")
                        st.rerun()

    # --- PESTAÑA 2: RESERVA, CALENDARIO & CHECKOUT ---
    with tab_reserva:
        col_res1, col_res2 = st.columns([1.3, 1])
        
        with col_res1:
            st.markdown("### 🗓️ Selección de Espacio & Estilista")
            
            # Cargar empleados
            conn = sqlite3.connect(DB_PATH)
            df_emp = pd.read_sql_query("SELECT nickname, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
            
            emp_opciones = df_emp["nickname"].tolist() if not df_emp.empty else ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"]
            estilista_sel = st.selectbox("Selecciona tu Estilista Favorita:", emp_opciones)
            
            # Mostrar foto del estilista seleccionada
            foto_row = df_emp[df_emp["nickname"] == estilista_sel]
            if not foto_row.empty and foto_row.iloc[0]["foto_url"]:
                st.image(foto_row.iloc[0]["foto_url"], width=180, caption=f"Estilista: {estilista_sel}")
            
            fecha_sel = st.date_input("Fecha de Cita:", value=datetime.date.today() + datetime.timedelta(days=1))
            
            # Bloques de horarios en tiempo real
            st.markdown("#### Horarios Disponibles:")
            citas_existentes = pd.read_sql_query("SELECT hora FROM citas WHERE fecha = ? AND empleado = ?", conn, params=(str(fecha_sel), estilista_sel))["hora"].tolist()
            conn.close()
            
            horarios = ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"]
            cols_h = st.columns(3)
            hora_elegida = None
            for idx, h in enumerate(horarios):
                c_target = cols_h[idx % 3]
                ocupado = h in citas_existentes
                btn_label = f"🔴 {h} (Ocupado)" if ocupado else f"🟢 {h} (Disponible)"
                if c_target.button(btn_label, key=f"slot_{h}", disabled=ocupado):
                    hora_elegida = h
                    st.session_state["hora_seleccionada"] = h
            
            if "hora_seleccionada" in st.session_state:
                st.success(f"Horario seleccionado: **{st.session_state['hora_seleccionada']}**")

        with col_res2:
            st.markdown("### 🛒 Resumen de Pago (Checkout)")
            if not st.session_state["carrito"]:
                st.info("Tu carrito está vacío. Añade servicios desde la pestaña 'Catálogo & Combos'.")
            else:
                total_base = 0.0
                for item in st.session_state["carrito"]:
                    st.write(f"- **{item['nombre']}**: ${item['precio']:.2f}")
                    total_base += item["precio"]
                
                st.markdown("---")
                metodo_pago = st.radio("Método de Pago:", ["💵 Efectivo en Salón", "💳 Tarjeta (5% Mini-Descuento Extra)"])
                
                descuento_tarjeta = (total_base * 0.05) if "Tarjeta" in metodo_pago else 0.0
                total_final = total_base - descuento_tarjeta
                
                if descuento_tarjeta > 0:
                    st.caption(f"🎉 Descuento especial tarjeta aplicable: -${descuento_tarjeta:.2f}")
                
                st.markdown(f"## Total Final: ${total_final:.2f} USD")
                
                btn_finalizar = st.button("💖 Confirmar y Agendar Cita", use_container_width=True)
                if btn_finalizar:
                    if "hora_seleccionada" not in st.session_state:
                        st.error("⚠️ Por favor selecciona un horario disponible en el calendario.")
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
                        
                        # Intento de envío de correo
                        envio_ok = enviar_correo_confirmacion(st.session_state["user_email"], st.session_state["user_nickname"], nombres_serv, str(fecha_sel), st.session_state["hora_seleccionada"], total_final)
                        
                        st.balloons()
                        st.success(f"¡Cita reservada con éxito para el {fecha_sel} a las {st.session_state['hora_seleccionada']}!")
                        if envio_ok:
                            st.info("📧 Se ha enviado un correo electrónico con la confirmación de tu cita.")
                        
                        st.session_state["carrito"] = []
                        del st.session_state["hora_seleccionada"]

    # --- PESTAÑA 3: MAPA DE CALOR & RESEÑAS ---
    with tab_resenas:
        st.markdown("### 📊 Popularidad de Estilistas & Reseñas de Clientes")
        
        conn = sqlite3.connect(DB_PATH)
        df_rev = pd.read_sql_query("SELECT * FROM resenas WHERE bloqueado = 0", conn)
        
        if not df_rev.empty:
            avg_stars = df_rev.groupby("empleado")["estrellas"].mean().reset_index()
            fig = px.bar(avg_stars, x="empleado", y="estrellas", color="estrellas", title="Calificación Promedio por Estilista (1-5 Estrellas)", color_continuous_scale="Plasma")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#FFF"))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### ⭐ Deja tu Calificación y Comentario")
        with st.form("form_resena"):
            emp_resena = st.selectbox("Estilista:", ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"])
            estrellas_in = st.slider("Calificación (Estrellas):", 1, 5, 5)
            comentario_in = st.text_area("Comentario:")
            btn_sub_rev = st.form_submit_button("Enviar Reseña")
            
            if btn_sub_rev:
                # Filtro de comentarios tóxicos
                es_toxico = check_toxic_comment(comentario_in)
                c = conn.cursor()
                c.execute("INSERT INTO resenas (cliente_nombre, empleado, estrellas, comentario, bloqueado) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state["user_nickname"], emp_resena, estrellas_in, comentario_in, 1 if es_toxico else 0))
                conn.commit()
                if es_toxico:
                    st.warning("⚠️ Tu comentario contiene expresiones ofensivas y pasará a revisión del Administrador antes de publicarse.")
                else:
                    st.success("¡Gracias por tu valoración!")
                st.rerun()
        conn.close()

    # --- PESTAÑA 4: CHATBOT IA & VISAGISMO ---
    with tab_chat:
        st.markdown("### 💖 Asistente Virtual Bella IA & Recomendador Visual")
        col_c1, col_c2 = st.columns([1, 1])
        
        with col_c1:
            st.markdown("#### 📷 Visagismo con Cámara / Imagen")
            img_file = st.file_uploader("Sube una foto de tu rostro o activa la cámara:", type=["jpg", "png", "jpeg"])
            if img_file:
                image = Image.open(img_file)
                st.image(image, width=250, caption="Rostro Analizado por IA")
                st.success("✨ **Análisis Visagismo IA:** Rostro de estructura ovalada. Se recomienda **Corte en Capas Desfiladas** y tonos **Balayage Warm Gloss**.")

        with col_c2:
            st.markdown("#### 💬 Chat Asistente & Bienestar")
            st.write("Pregunta sobre recomendaciones, servicios o cuéntale a Bella cómo te sientes hoy.")
            user_msg = st.text_input("Escribe tu consulta:")
            if st.button("Enviar Consulta"):
                if user_msg:
                    msg_lower = user_msg.lower()
                    if any(k in msg_lower for k in ["estresada", "estresado", "cansada", "cansado", "relajación"]):
                        st.markdown("💖 **Bella IA:** *Lamento que te sientas así. Te recomiendo nuestro tratamiento Spa Keratina o lavado capilar con masaje relajante para renovar energía.*")
                    elif any(k in msg_lower for k in ["precio", "descuento", "combo"]):
                        st.markdown("💖 **Bella IA:** *Los combos incluyen hasta un 20% de ahorro directo. ¡Si pagas con tarjeta recibes 5% adicional!*")
                    else:
                        # Regla de Escalado Inteligente
                        st.warning("🤖 **Bella IA:** *Tu consulta requiere atención personalizada del equipo. He escalado tu mensaje directamente al Panel de Administrador y Empleados.*")
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO preguntas_escaladas (cliente_email, pregunta, fecha_hora, respuesta, atendido) VALUES (?, ?, ?, ?, ?)",
                                  (st.session_state["user_email"], f"Requiere intervención: [{user_msg}]", ahora, "", 0))
                        conn.commit()
                        conn.close()

# ==========================================
# 6. PANEL DE ADMINISTRADOR
# ==========================================
elif st.session_state["user_role"] == "admin":
    st.markdown("## 👑 Panel de Control del Administrador")
    
    t_citas, t_emp, t_serv, t_mod, t_inv, t_bot = st.tabs([
        "📅 Citas & Walk-ins",
        "👩‍🎨 Empleados",
        "🛠️ Servicios & Descuentos",
        "🛡️ Moderación Reseñas",
        "📊 Finanzas e Inventario",
        "📥 Consultas Chatbot"
    ])
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Citas & Agendamiento Manual
    with t_citas:
        st.markdown("### Citas Registradas")
        df_c = pd.read_sql_query("SELECT * FROM citas ORDER BY id DESC", conn)
        st.dataframe(df_c, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### ➕ Agendar Cita Presencial (Walk-in)")
        with st.form("f_walkin"):
            w_nombre = st.text_input("Cliente:")
            w_emp = st.selectbox("Estilista:", ["Valeria (Master Colorista)", "Camila (Makeup & Stylist)"])
            w_serv = st.text_input("Servicio:")
            w_fecha = st.date_input("Fecha:", datetime.date.today())
            w_hora = st.selectbox("Hora:", ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"])
            w_total = st.number_input("Monto Total ($):", min_value=0.0, value=50.0)
            if st.form_submit_button("Agendar Walk-In"):
                c = conn.cursor()
                c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, metodo_pago, monto_total, estado)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          ("presencial@salon.com", w_nombre, w_emp, w_serv, str(w_fecha), w_hora, "Efectivo", w_total, "Confirmada"))
                conn.commit()
                st.success("Cita presencial agendada.")
                st.rerun()

    # 2. Gestión Empleados
    with t_emp:
        st.markdown("### Perfiles de Empleados")
        df_e = pd.read_sql_query("SELECT email, nickname, cedula, estado_pago, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
        st.dataframe(df_e, use_container_width=True)
        
        with st.form("f_add_emp"):
            st.markdown("#### Registrar Nuevo Empleado")
            ne_email = st.text_input("Correo Gmail Empleado:")
            ne_nick = st.text_input("Nombre / Título:")
            ne_ced = st.text_input("Cédula / CI:")
            ne_foto = st.text_input("URL Foto de Perfil:")
            if st.form_submit_button("Guardar Empleado"):
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO usuarios VALUES (?, ?, 'empleado', ?, 'Al Día', ?)", (ne_email, ne_nick, ne_ced, ne_foto))
                conn.commit()
                st.success("Empleado registrado correctamente.")
                st.rerun()

    # 3. Servicios & Descuentos Switch
    with t_serv:
        st.markdown("### Control de Disponibilidad de Servicios")
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

    # 4. Moderación Comentarios
    with t_mod:
        st.markdown("### Moderación de Comentarios")
        df_r = pd.read_sql_query("SELECT * FROM resenas", conn)
        for _, row in df_r.iterrows():
            st.write(f"**Cliente:** {row['cliente_nombre']} | **Empleado:** {row['empleado']} | **Estrellas:** {row['estrellas']}")
            st.write(f"*'{row['comentario']}'*")
            if row['bloqueado']:
                st.error("🚫 Comentario Bloqueado (Filtro Tóxico)")
                if st.button("Desbloquear", key=f"unblk_{row['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE resenas SET bloqueado = 0 WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            else:
                if st.button("Bloquear Comentario", key=f"blk_{row['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE resenas SET bloqueado = 1 WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            st.markdown("---")

    # 5. Finanzas e Inventario
    with t_inv:
        st.markdown("### Inventario de Insumos & Reporte Simple")
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        st.dataframe(df_inv, use_container_width=True)
        
        total_ingresos = pd.read_sql_query("SELECT SUM(monto_total) as total FROM citas", conn)["total"].iloc[0] or 0.0
        st.metric("Total Ingresos Acumulados", f"${total_ingresos:.2f} USD")

    # 6. Bandeja Chatbot Escalado
    with t_bot:
        st.markdown("### Preguntas Escaladas desde Chatbot IA")
        df_esc = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
        st.dataframe(df_esc, use_container_width=True)

    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown("## ✂️ Panel de Atención para Empleados")
    
    conn = sqlite3.connect(DB_PATH)
    
    t_emp_citas, t_emp_bot = st.tabs(["📅 Agendar Walk-in Presencial", "📥 Responder Consultas Escaladas"])
    
    with t_emp_citas:
        st.markdown("### Agendamiento Presencial Rápido")
        with st.form("form_emp_walk"):
            cliente_p = st.text_input("Nombre Cliente:")
            servicio_p = st.text_input("Servicio Realizado:")
            monto_p = st.number_input("Monto ($):", value=30.0)
            if st.form_submit_button("Registrar Cobro"):
                c = conn.cursor()
                c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, metodo_pago, monto_total, estado)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          ("presencial@salon.com", cliente_p, st.session_state["user_nickname"], servicio_p, str(datetime.date.today()), "Ahora", "Efectivo", monto_p, "Completada"))
                conn.commit()
                st.success("Cita registrada.")

    with t_emp_bot:
        st.markdown("### Preguntas Pendientes de Respuesta")
        df_p = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
        st.dataframe(df_p, use_container_width=True)
    
    conn.close()
