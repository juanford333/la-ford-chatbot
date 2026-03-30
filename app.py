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
# LINK DE TU PLANILLA DE GOOGLE SHEETS
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ClGVOcDcgogynxE8lgNdmJUhzP10UvE-1gpjQKl428k/edit#gid=0"
MI_NUMERO_WHATSAPP = "5491162756333"

client = anthropic.Anthropic(api_key=API_KEY)

st.set_page_config(page_title="La Ford de Warnes", layout="wide", page_icon="🛞")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Estética del Mostrador
st.markdown("""
    <div style="background-color:#003478;padding:20px;border-radius:10px;margin-bottom:25px;border: 2px solid #0056b3">
    <h1 style="color:white;text-align:center;margin:0;font-family:Arial;">🛞 La Ford de Warnes</h1>
    <p style="color:#d1d1d1;text-align:center;margin:0;font-weight:bold;">Mostrador Digital Sincronizado - Juan</p>
    </div>
""", unsafe_allow_html=True)

if 'form_data' not in st.session_state:
    st.session_state.form_data = {"nom": "", "pat": "", "mod": "", "añ": "", "mot": "", "con": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

def guardar_en_google_sheets():
    d = st.session_state.form_data
    if not (d['nom'] or d['pat']) or not d['con']:
        st.warning("⚠️ Faltan datos en la ficha.")
        return False
    try:
        # Leer datos actuales (ttl=0 para que no use memoria vieja)
        df_existente = conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
        
        fecha_reg = datetime.now().strftime("%d/%m/%Y %H:%M")
        nueva_fila = pd.DataFrame([[
            fecha_reg, str(d['nom']).upper(), str(d['pat']).upper(), "",
            str(d['mod']).upper(), str(d['añ']), str(d['mot']).upper(), 
            str(d['con']).upper(), "CONSULTA"
        ]], columns=["FECHA", "CLIENTE", "PATENTE", "VIN/CHASIS", "MODELO", "AÑO", "MOTOR", "REPUESTOS/CONSULTA", "ESTADO"])

        # Unir lo viejo con lo nuevo
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # Guardar en Google Sheets
        conn.update(spreadsheet=SPREADSHEET_URL, data=df_final)
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

# PANEL LATERAL
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
            st.success("✅ ¡Guardado en Google Drive!")
            d = st.session_state.form_data
            msj = f"*PEDIDO LA FORD*%0A*Cliente:* {d['nom']}%0A*Vehículo:* {d['mod']} {d['añ']}%0A*Pedido:* {d['con']}"
            st.markdown(f'''<a href="https://wa.me/{MI_NUMERO_WHATSAPP}?text={msj}" target="_blank">
                <div style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;margin-top:10px;">MANDAR WHATSAPP</div></a>''', unsafe_allow_html=True)

# CHAT PRINCIPAL
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("¿Qué repuesto buscás para tu Ford?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    instruct = (
        "Sos Juan, el experto de La Ford de Warnes. Hablás como repuestero porteño amable. "
        "PROHIBIDO dar precios. SIEMPRE empezá con el JSON, luego '---' y tu respuesta. "
        "JSON: {\"nombre\":\"\",\"patente\":\"\",\"modelo\":\"\",\"año\":\"\",\"motor\":\"\",\"repuesto\":\"\"}"
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022", 
        max_tokens=600,
        system=instruct,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    
    texto = response.content[0].text
    if "---" in texto:
        partes = texto.split("---", 1)
        try:
            d = json.loads(partes[0].strip())
            if d.get("nombre"): st.session_state.form_data["nom"] = d["nombre"]
            if d.get("patente"): st.session_state.form_data["pat"] = d["patente"]
            if d.get("modelo"): st.session_state.form_data["mod"] = d["modelo"]
            if d.get("año"): st.session_state.form_data["añ"] = d["año"]
