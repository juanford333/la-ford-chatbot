import streamlit as st
import anthropic
import pandas as pd
from datetime import datetime
import json
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 🔑 CONFIGURACIÓN INICIAL
# ==========================================
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ClGVOcDcgogynxE8lgNdmJUhzP10UvE-1gpjQKl428k/edit#gid=0"
MI_NUMERO_WHATSAPP = "5491162756333"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ClGVOcDcgogynxE8lgNdmJUhzP10UvE-1gpjQKl428k/edit"
client = anthropic.Anthropic(api_key=API_KEY)

st.set_page_config(page_title="La Ford de Warnes", layout="wide", page_icon="🛞")
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
    <div style="background-color:#003478;padding:20px;border-radius:10px;margin-bottom:25px;border: 2px solid #0056b3">
    <h1 style="color:white;text-align:center;margin:0;font-family:Arial;">🛞 La Ford de Warnes</h1>
    <p style="color:#d1d1d1;text-align:center;margin:0;font-weight:bold;">Mostrador Digital Sincronizado - Juan</p>
    </div>
""", unsafe_allow_html=True)

# Inicializar estados
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"nom": "", "pat": "", "mod": "", "añ": "", "mot": "", "con": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

def guardar_en_google_sheets():
    d = st.session_state.form_data
    if not (d['nom'] or d['pat']) or not d['con']:
        st.warning("⚠️ Faltan datos críticos para guardar.")
        return False
    try:
        df_existente = conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
        fecha_reg = datetime.now().strftime("%d/%m/%Y %H:%M")
        nueva_fila = pd.DataFrame([[
            fecha_reg, str(d['nom']).upper(), str(d['pat']).upper(), "",
            str(d['mod']).upper(), str(d['añ']), str(d['mot']).upper(), 
            str(d['con']).upper(), "CONSULTA"
        ]], columns=["FECHA", "CLIENTE", "PATENTE", "VIN/CHASIS", "MODELO", "AÑO", "MOTOR", "REPUESTOS/CONSULTA", "ESTADO"])
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(spreadsheet=SPREADSHEET_URL, data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# BARRA LATERAL (FICHA)
with st.sidebar:
    st.header("📋 Ficha del Cliente")
    st.session_state.form_data["nom"] = st.text_input("Nombre", value=st.session_state.form_data["nom"])
    st.session_state.form_data["pat"] = st.text_input("Patente", value=st.session_state.form_data["pat"])
    st.session_state.form_data["mod"] = st.text_input("Modelo", value=st.session_state.form_data["mod"])
    st.session_state.form_data["añ"] = st.text_input("Año", value=st.session_state.form_data["añ"])
    st.session_state.form_data["mot"] = st.text_input("Motor", value=st.session_state.form_data["mot"])
    st.session_state.form_data["con"] = st.text_area("Pedido", value=st.session_state.form_data["con"])
    
    if st.button("💾 GUARDAR CONSULTA", use_container_width=True, type="primary"):
        if guardar_en_google_sheets():
            st.success("✅ ¡Guardado en Drive!")

# CHAT
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribí acá tu pedido..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Instrucción ultra-clara para que Juan llene la ficha
    instruct = (
        "Sos Juan de La Ford. Tu misión es extraer datos para una ficha. "
        "SIEMPRE empezá tu respuesta con un bloque JSON que contenga: "
        "nombre, patente, modelo, año, motor, pedido. "
        "Luego poné '---' y saludá al cliente. "
        "Ejemplo: {\"nombre\":\"Juan\",\"patente\":\"ABC123\",...} --- Hola Carlos..."
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514", 
        max_tokens=800,
        system=instruct,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    
    full_text = response.content[0].text
    
    # Procesar JSON y Texto
    if "---" in full_text:
        partes = full_text.split("---", 1)
        try:
            data_ext = json.loads(partes[0].strip())
            # Actualizar ficha lateral
            if data_ext.get("nombre"): st.session_state.form_data["nom"] = data_ext["nombre"]
            if data_ext.get("patente"): st.session_state.form_data["pat"] = data_ext["patente"]
            if data_ext.get("modelo"): st.session_state.form_data["mod"] = data_ext["modelo"]
            if data_ext.get("año"): st.session_state.form_data["añ"] = data_ext["año"]
            if data_ext.get("motor"): st.session_state.form_data["mot"] = data_ext["motor"]
            if data_ext.get("pedido"): st.session_state.form_data["con"] = data_ext["pedido"]
        except: pass
        res_visual = partes[1].strip()
    else:
        res_visual = full_text

    with st.chat_message("assistant"):
        st.markdown(res_visual)
        st.session_state.messages.append({"role": "assistant", "content": res_visual})
    st.rerun()
