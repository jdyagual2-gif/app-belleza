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
    
    # 1. Creación de tablas base
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

    # 2. MIGRACIÓN AUTOMÁTICA DE ESTRUCTURA (Evita el KeyError en bases de datos existentes)
    def agregar_columna_si_falta(tabla, columna_def):
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna_def}")
        except sqlite3.OperationalError:
            pass # La columna ya existía

    agregar_columna_si_falta("usuarios", "foto_url TEXT")
    agregar_columna_si_falta("servicios", "imagen_url TEXT")
    agregar_columna_si_falta("servicios", "es_combo INTEGER DEFAULT 0")
    agregar_columna_si_falta("resenas", "fecha TEXT")

    # Reparar valores nulos resultantes de la migración
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("UPDATE resenas SET fecha = ? WHERE fecha IS NULL OR fecha = ''", (hoy_str,))
    c.execute("UPDATE servicios SET imagen_url = '' WHERE imagen_url IS NULL")

    # 3. Cargar datos iniciales solo si la tabla está vacía
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
                    elif res and res[0] == "admin":
                        st.session_state["user_role"] = "admin"
                    else:
                        st.session_state["user_role"] = "cliente"
                    
                    st.rerun()
    st.stop()

# --- SIDEBAR (CHATBOT Y NAVEGACIÓN PERMANENTE) ---
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

with st.sidebar.expander("💖 Bella IA & Visagismo (Asistente 24/7)", expanded=False):
    st.markdown("#### 📷 Análisis de Visagismo")
    img_file = st.file_uploader("Sube foto de tu rostro:", type=["jpg", "png", "jpeg"], key="bot_img_side")
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True, caption="Rostro Analizado por IA")
        st.success("✨ **Visagismo IA:** Rostro ovalado detectado. Se recomienda **Corte en Capas** y tonos **Balayage Warm Gloss**.")

    st.markdown("#### 💬 Consultar a Bella IA")
    user_msg = st.text_input("Pregunta lo que desees:", key="bot_input_side")
    if st.button("Enviar Consulta", key="bot_btn_side"):
        if user_msg:
            msg_lower = user_msg.lower()
            if any(k in msg_lower for k in ["estresada", "estresado", "cansada", "relajación"]):
                st.info("💖 **Bella IA:** *Te recomiendo nuestro tratamiento Spa Keratina con masaje capilar.*")
            elif any(k in msg_lower for k in ["precio", "descuento", "combo", "cupón"]):
                st.info("💖 **Bella IA:** *Los combos tienen un 20% de ahorro directo. Puedes usar el cupón 'GLOW10'.*")
            else:
                st.warning("🤖 **Bella IA:** *He registrado tu consulta para que el Administrador o Estilista te contacte.*")
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

    # --- PESTAÑA 1: CATÁLOGO DE SERVICIOS E IMÁGENES ---
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
                    # Acceso seguro a la columna 'imagen_url'
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
                        
                        envio_ok = enviar_correo_confirmacion(st.session_state["user_email"], st.session_state["user_nickname"], nombres_serv, str(fecha_sel), st.session_state["hora_seleccionada"], total_final)
                        
                        st.balloons()
                        st.success(f"¡Cita reservada para el {fecha_sel} a las {st.session_state['hora_seleccionada']}!")
                        if envio_ok:
                            st.info("📧 Correo de confirmación enviado exitosamente.")
                        
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
                # Acceso seguro al campo 'fecha'
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
    
    with t_citas:
        st.markdown("### 📋 Registro General de Citas")
        df_c = pd.read_sql_query("SELECT * FROM citas ORDER BY id DESC", conn)
        st.dataframe(df_c, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🚶‍♂️ Agendar Cliente Presencial (Walk-in)")
        with st.form("form_walkin"):
            col_w1, col_w2 = st.columns(2)
            c_nom = col_w1.text_input("Nombre del Cliente:")
            c_email = col_w2.text_input("Correo Electrónico del Cliente:")
            
            df_serv_all = pd.read_sql_query("SELECT nombre, precio FROM servicios WHERE disponible=1", conn)
            s_nom = col_w1.selectbox("Servicio / Combo:", df_serv_all["nombre"].tolist() if not df_serv_all.empty else ["Balayage Neón"])
            
            df_emp_all = pd.read_sql_query("SELECT nickname FROM usuarios WHERE rol='empleado'", conn)
            e_nom = col_w2.selectbox("Estilista Asignada:", df_emp_all["nickname"].tolist() if not df_emp_all.empty else ["Valeria (Master Colorista)"])
            
            w_fecha = col_w1.date_input("Fecha:", value=datetime.date.today())
            w_hora = col_w2.selectbox("Hora:", ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"])
            
            monto_val = df_serv_all[df_serv_all["nombre"] == s_nom]["precio"].values[0] if not df_serv_all.empty else 50.0
            
            btn_walkin = st.form_submit_button("Registrar Cita Walk-in")
            if btn_walkin:
                c = conn.cursor()
                c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha, hora, metodo_pago, monto_total, estado)
                             VALUES (?, ?, ?, ?, ?, ?, 'Efectivo Walk-in', ?, 'Confirmada')""",
                          (c_email, c_nom, e_nom, s_nom, str(w_fecha), w_hora, monto_val))
                conn.commit()
                st.success("¡Cita presencial registrada con éxito!")
                st.rerun()

    with t_emp:
        st.markdown("### 👩‍🎨 Lista de Empleados")
        df_e = pd.read_sql_query("SELECT email, nickname, cedula, estado_pago, foto_url FROM usuarios WHERE rol = 'empleado'", conn)
        st.dataframe(df_e, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### ➕ Registrar Nuevo Empleado")
        with st.form("form_add_emp"):
            new_emp_email = st.text_input("Correo Electrónico:")
            new_emp_nick = st.text_input("Nombre y Cargo (Ej: Sofía - Master Barber):")
            new_emp_ced = st.text_input("Cédula:")
            new_emp_foto = st.text_input("URL de Foto de Perfil:")
            btn_add_e = st.form_submit_button("Guardar Empleado")
            
            if btn_add_e:
                if new_emp_email and new_emp_nick:
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO usuarios VALUES (?, ?, 'empleado', ?, 'Al Día', ?)",
                              (new_emp_email.strip().lower(), new_emp_nick, new_emp_ced, new_emp_foto))
                    conn.commit()
                    st.success("Empleado registrado correctamente.")
                    st.rerun()

    with t_serv:
        st.markdown("### 🛠️ Control de Servicios y Disponibilidad")
        df_s = pd.read_sql_query("SELECT * FROM servicios", conn)
        for _, row in df_s.iterrows():
            col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
            col_s1.write(f"**{row['nombre']}** ({row['categoria']}) - ${row['precio']:.2f}")
            disp = col_s2.toggle("Disponible", value=bool(row['disponible']), key=f"sw_{row['id']}")
            if disp != bool(row['disponible']):
                c = conn.cursor()
                c.execute("UPDATE servicios SET disponible = ? WHERE id = ?", (1 if disp else 0, row['id']))
                conn.commit()
                st.rerun()
            if col_s3.button("Eliminar", key=f"del_serv_{row['id']}"):
                c = conn.cursor()
                c.execute("DELETE FROM servicios WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Agregar Nuevo Servicio o Combo")
        with st.form("form_add_serv"):
            ns_nom = st.text_input("Nombre del Servicio:")
            ns_cat = st.selectbox("Categoría:", ["Colorimetría", "Maquillaje", "Uñas", "Corte", "Capilar", "Combos"])
            ns_prec = st.number_input("Precio ($ USD):", min_value=5.0, value=50.0)
            ns_combo = st.checkbox("¿Es un Combo Especial?")
            ns_img = st.text_input("URL de la Imagen:")
            btn_add_s = st.form_submit_button("Guardar Servicio")
            
            if btn_add_s:
                if ns_nom:
                    c = conn.cursor()
                    c.execute("INSERT INTO servicios (nombre, categoria, precio, disponible, es_combo, imagen_url) VALUES (?, ?, ?, 1, ?, ?)",
                              (ns_nom, ns_cat, ns_prec, 1 if ns_combo else 0, ns_img))
                    conn.commit()
                    st.success("¡Servicio añadido al catálogo!")
                    st.rerun()

    with t_mod:
        st.markdown("### 🛡️ Centro de Moderación")
        df_r = pd.read_sql_query("SELECT * FROM resenas", conn)
        for _, row in df_r.iterrows():
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.write(f"**Cliente:** {row['cliente_nombre']} | **Estilista:** {row['empleado']} | **Estrellas:** {row['estrellas']}")
                st.write(f"*'{row['comentario']}'*")
            with col_m2:
                if row['bloqueado']:
                    st.error("🚫 Bloqueado")
                    if st.button("Aprobar / Liberar", key=f"unblk_{row['id']}"):
                        c = conn.cursor()
                        c.execute("UPDATE resenas SET bloqueado = 0 WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.rerun()
                else:
                    st.success("✅ Público")
                if st.button("Eliminar Reseña", key=f"del_rev_{row['id']}"):
                    c = conn.cursor()
                    c.execute("DELETE FROM resenas WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            st.markdown("---")

    with t_inv:
        st.markdown("### 📊 Métricas Financieras y Stock")
        df_tot = pd.read_sql_query("SELECT SUM(monto_total) as total FROM citas WHERE estado != 'Cancelada'", conn)
        total_rec = df_tot['total'].iloc[0] or 0.0
        st.metric(label="Ingresos Totales Registrados", value=f"${total_rec:.2f} USD")
        
        st.markdown("---")
        st.markdown("### 📦 Control de Inventario de Productos")
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        for _, row_inv in df_inv.iterrows():
            col_i1, col_i2, col_i3 = st.columns([2, 1.5, 1])
            col_i1.write(f"**{row_inv['producto']}** - ${row_inv['precio_unitario']:.2f}/unidad")
            new_qty = col_i2.number_input(f"Stock ({row_inv['producto']}):", min_value=0, value=int(row_inv['cantidad']), key=f"inv_{row_inv['id']}")
            if new_qty != row_inv['cantidad']:
                if col_i3.button("Actualizar", key=f"upd_inv_{row_inv['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE inventario SET cantidad = ? WHERE id = ?", (new_qty, row_inv['id']))
                    conn.commit()
                    st.success("Stock actualizado.")
                    st.rerun()

    with t_bot:
        st.markdown("### 📥 Atender Consultas Escaladas del Chatbot")
        df_esc = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
        if df_esc.empty:
            st.info("No hay preguntas pendientes por responder.")
        else:
            for _, r_esc in df_esc.iterrows():
                with st.container(border=True):
                    st.write(f"**Cliente:** {r_esc['cliente_email']} | Fecha: {r_esc['fecha_hora']}")
                    st.write(f"**Pregunta:** {r_esc['pregunta']}")
                    resp_input = st.text_input("Escribe tu respuesta:", key=f"resp_{r_esc['id']}")
                    if st.button("Enviar Respuesta y Cerrar", key=f"btn_resp_{r_esc['id']}"):
                        c = conn.cursor()
                        c.execute("UPDATE preguntas_escaladas SET respuesta = ?, atendido = 1 WHERE id = ?", (resp_input, r_esc['id']))
                        conn.commit()
                        st.success("Respuesta registrada.")
                        st.rerun()

    conn.close()

# ==========================================
# 7. PANEL DE EMPLEADO COMPLETO
# ==========================================
elif st.session_state["user_role"] == "empleado":
    st.markdown("## ✂️ Panel de Atención para Empleados y Estilistas")
    
    conn = sqlite3.connect(DB_PATH)
    st.markdown("### 📅 Mis Citas Asignadas")
    df_emp_citas = pd.read_sql_query("SELECT * FROM citas WHERE empleado LIKE ? ORDER BY fecha, hora", conn, params=(f"%{st.session_state['user_nickname']}%",))
    if df_emp_citas.empty:
        st.info("No tienes citas asignadas por el momento.")
    else:
        st.dataframe(df_emp_citas, use_container_width=True)
        
    st.markdown("---")
    st.markdown("### 💬 Consultas de Clientes Pendientes")
    df_p = pd.read_sql_query("SELECT * FROM preguntas_escaladas WHERE atendido = 0", conn)
    if df_p.empty:
        st.info("Sin consultas pendientes.")
    else:
        for _, row_p in df_p.iterrows():
            st.write(f"**De:** {row_p['cliente_email']} - {row_p['pregunta']}")
            ans = st.text_input("Responder:", key=f"emp_ans_{row_p['id']}")
            if st.button("Marcar como Respondida", key=f"emp_btn_{row_p['id']}"):
                c = conn.cursor()
                c.execute("UPDATE preguntas_escaladas SET respuesta = ?, atendido = 1 WHERE id = ?", (ans, row_p['id']))
                conn.commit()
                st.success("Atendida.")
                st.rerun()
    conn.close()
