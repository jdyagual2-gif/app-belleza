import os
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(
    page_title="GlowStudio AI | Asistente de Citas",
    page_icon="✨",
    layout="wide"
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_email TEXT,
                    cliente_nombre TEXT,
                    empleado TEXT,
                    servicio TEXT,
                    fecha_hora TEXT,
                    metodo_pago TEXT,
                    monto_total REAL,
                    estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. FUNCIÓN DE ENVÍO DE CORREO Y DIAGNÓSTICO
# ==========================================
def enviar_correo_confirmacion(destinatario, nombre, servicio, fecha_hora):
    """Envía correo de confirmación y retorna (estado_bool, mensaje_detalle)"""
    try:
        if "email" not in st.secrets:
            return False, "Falta la sección [email] en la configuración de secrets.toml."
        
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets["email"].get("smtp_port", 587))
        sender_email = st.secrets["email"].get("sender_email", "")
        sender_password = st.secrets["email"].get("sender_password", "")
        
        if not sender_email or not sender_password:
            return False, "Las credenciales 'sender_email' o 'sender_password' están vacías en secrets.toml."

        msg = MIMEMultipart()
        msg['From'] = f"GlowStudio AI <{sender_email}>"
        msg['To'] = destinatario
        msg['Subject'] = "✨ Confirmación de tu Reserva - GlowStudio AI"

        cuerpo = f"""Hola {nombre},

¡Tu cita ha sido agendada con éxito en GlowStudio AI! 💖

📋 Detalle de la reserva:
- Cliente: {nombre}
- Correo: {destinatario}
- Servicio: {servicio}
- Fecha y Hora: {fecha_hora}

Si necesitas realizar cambios en tu horario, contáctanos con anticipación.

¡Te esperamos!
Atentamente,
El equipo de GlowStudio AI
"""
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado exitosamente."
    except Exception as e:
        return False, f"Error SMTP: {str(e)}"

# ==========================================
# 3. MANEJO DE BASE DE DATOS PARA CLIENTES Y CITAS
# ==========================================
def registrar_cliente_y_cita(nombre, email, servicio, fecha_hora):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Registrar o actualizar cliente en la tabla usuarios
    c.execute("""INSERT INTO usuarios (email, nickname, rol, cedula, estado_pago, foto_url) 
                 VALUES (?, ?, 'cliente', '0000000000', 'Al Día', '')
                 ON CONFLICT(email) DO UPDATE SET nickname=excluded.nickname""", 
              (email, nombre))
    
    # 2. Registrar la cita
    c.execute("""INSERT INTO citas (cliente_email, cliente_nombre, empleado, servicio, fecha_hora, metodo_pago, monto_total, estado)
                 VALUES (?, ?, 'Estilista Asignado', ?, ?, 'Pendiente', 0.0, 'Confirmada')""",
              (email, nombre, servicio, fecha_hora))
    
    conn.commit()
    conn.close()

# ==========================================
# 4. ESTADOS DE LA SESIÓN DE CHAT
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy **Bella IA** 💖. ¿En qué te puedo ayudar hoy? Si deseas agendar o registrar una cita, solo dímelo."}
    ]

if "step" not in st.session_state:
    st.session_state.step = "IDLE"

if "booking_data" not in st.session_state:
    st.session_state.booking_data = {"nombre": "", "email": "", "servicio": "", "fecha_hora": ""}

# ==========================================
# 5. INTERFAZ Y FLUJO CONVERSACIONAL DE IA
# ==========================================
st.title("✨ GlowStudio AI — Asistente Virtual 24/7")

# Mostrar historial de conversación
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Capturar entrada del usuario
user_input = st.chat_input("Escribe tu mensaje aquí...")

if user_input:
    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    input_lower = user_input.lower().strip()
    bot_response = ""

    # FLUJO CONVERSACIONAL
    if st.session_state.step == "IDLE":
        if any(kw in input_lower for kw in ["agendar", "cita", "registrar", "reservar", "agg"]):
            st.session_state.step = "ASK_NAME"
            bot_response = "¡Claro que sí! Con gusto te ayudo a agendar tu cita y registrarte como cliente.\n\nPara comenzar, **¿cuál es tu nombre completo?**"
        else:
            bot_response = "Soy Bella IA. Puedo ayudarte a agendar o registrar citas en nuestro salón. Escribe **'quiero agendar una cita'** para comenzar."

    elif st.session_state.step == "ASK_NAME":
        st.session_state.booking_data["nombre"] = user_input.strip()
        st.session_state.step = "ASK_EMAIL"
        bot_response = f"Encantada, **{st.session_state.booking_data['nombre']}**.\n\nAhora, **¿cuál es tu correo electrónico?**"

    elif st.session_state.step == "ASK_EMAIL":
        if "@" not in user_input or "." not in user_input:
            bot_response = "⚠️ El correo ingresado no parece válido. Por favor escribe un correo electrónico válido (ejemplo: cliente@gmail.com):"
        else:
            st.session_state.booking_data["email"] = user_input.strip().lower()
            st.session_state.step = "ASK_SERVICE"
            bot_response = "¡Perfecto! **¿Qué servicio o tratamiento te gustaría realizarte?**\n*(Ejemplos: Balayage, Corte de Cabello, Makeup, Manicure Gel Gloss)*"

    elif st.session_state.step == "ASK_SERVICE":
        st.session_state.booking_data["servicio"] = user_input.strip()
        st.session_state.step = "ASK_DATETIME"
        bot_response = "¡Excelente elección!\n\nPor último, **¿para qué fecha y hora deseas la cita?**\n*(Ejemplo: Mañana a las 4:00 PM o 2026-10-10 a las 15:00)*"

    elif st.session_state.step == "ASK_DATETIME":
        st.session_state.booking_data["fecha_hora"] = user_input.strip()
        
        datos = st.session_state.booking_data
        
        # 1. Guardar en SQLite (Cliente + Cita)
        registrar_cliente_y_cita(
            nombre=datos["nombre"],
            email=datos["email"],
            servicio=datos["servicio"],
            fecha_hora=datos["fecha_hora"]
        )
        
        # 2. Intentar enviar correo de confirmación
        exito_correo, msg_correo = enviar_correo_confirmacion(
            destinatario=datos["email"],
            nombre=datos["nombre"],
            servicio=datos["servicio"],
            fecha_hora=datos["fecha_hora"]
        )

        bot_response = f"""🎉 **¡Cita registrada con éxito!**

📌 **Resumen del Registro:**
- **Cliente:** {datos['nombre']}
- **Correo:** {datos['email']}
- **Servicio:** {datos['servicio']}
- **Fecha/Hora:** {datos['fecha_hora']}

✅ Te hemos dado de alta automáticamente en el sistema.
"""
        if exito_correo:
            bot_response += "\n📧 **Correo enviado:** Te hemos enviado un mensaje de confirmación a tu casilla de entrada."
        else:
            bot_response += f"\n⚠️ **Nota sobre el correo:** No se pudo enviar el correo automático ({msg_correo}). Revisa la sección de soporte de correo en el panel lateral."

        # Reiniciar estado para nuevas consultas
        st.session_state.step = "IDLE"
        st.session_state.booking_data = {"nombre": "", "email": "", "servicio": "", "fecha_hora": ""}

    # Guardar y mostrar respuesta de la IA
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)

# ==========================================
# 6. PANEL LATERAL: BASE DE DATOS Y CONFIGURACIÓN CORREO
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración & Registros")
    
    with st.expander("📬 Diagnóstico de Envío de Correos"):
        st.markdown("""
        Si el correo no te llega, asegúrate de tener el archivo `.streamlit/secrets.toml` configurado así:
        
        ```toml
        [email]
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "tu_correo@gmail.com"
        sender_password = "tu_contraseña_de_aplicacion"
        ```
        
        > **Importante para Gmail:** Debes usar una **Contraseña de Aplicación** de 16 caracteres generada desde tu cuenta de Google (Seguridad > Verificación en 2 pasos > Contraseñas de aplicaciones), **no** tu clave personal.
        """)

    with st.expander("👥 Clientes Registrados"):
        conn = sqlite3.connect(DB_PATH)
        df_u = pd.read_sql_query("SELECT email, nickname AS nombre, rol FROM usuarios", conn)
        st.dataframe(df_u, use_container_width=True)
        conn.close()

    with st.expander("📅 Citas Registradas"):
        conn = sqlite3.connect(DB_PATH)
        df_c = pd.read_sql_query("SELECT id, cliente_nombre, cliente_email, servicio, fecha_hora, estado FROM citas ORDER BY id DESC", conn)
        st.dataframe(df_c, use_container_width=True)
        conn.close()
