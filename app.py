import streamlit as st
import anthropic
import pandas as pd
from datetime import datetime
import json
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 🔑 CONFIGURACIÓN
# ==========================================
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
# ID FIJO DE TU PLANILLA (ESTO NO DA ERROR 404)
SPREADSHEET_ID = "1ClGVOcDcgogynxE8lgNdmJUhzP10UvE-1gpjQKl428k"
MI_NUMERO_WHATSAPP = "5491162756333"

client = anthropic.Anthropic(api_key=API_KEY)

st.set_page_config(page_title="La Ford de Warnes", layout="wide", page_icon="🛞")
conn = st.connection("gsheets", type=GSheetsConnection)

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
        # CONEXIÓN DIRECTA POR ID
        df_existente = conn.read(spreadsheet=SPREADSHEET_ID, ttl=0)
        
        fecha_reg = datetime.now().strftime("%d/%m/%Y %H:%M")
        nueva_fila = pd.DataFrame([[
            fecha_reg, str(d['nom']).upper(), str(d['pat']).upper(), "",
            str(d['mod']).upper(), str(d['añ']), str(d['mot']).upper(), 
            str(d['con']).upper(), "CONSULTA"
        ]], columns=["FECHA", "CLIENTE", "PATENTE", "VIN/CHASIS", "MODELO", "AÑO", "MOTOR", "REPUESTOS/CONSULTA", "ESTADO"])

        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(spreadsheet=SPREADSHEET_ID, data=df_final)
        return True
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return False

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
            st.success("✅ ¡GRABADO!")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribí acá..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    instruct = "Sos Juan de La Ford. SIEMPRE empezá con JSON, luego '---'. JSON: {\"nombre\":\"\",\"patente\":\"\",\"modelo\":\"\",\"año\":\"\",\"motor\":\"\",\"repuesto\":\"\"}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514", 
        max_tokens=800,
        system=instruct,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    
    texto = response.content[0].text
    if "---" in texto:
        partes = texto.split("---", 1)
        try:
            d = json.loads(partes[0].strip())
            for k, v in [("nom","nombre"),("pat","patente"),("mod","modelo"),("añ","año"),("mot","motor"),("con","repuesto")]:
                if d.get(v): st.session_state.form_data[k] = d[v]
        except: pass
        res_cli = partes[1].strip()
    else: res_cli = texto

    with st.chat_message("assistant"):
        st.markdown(res_cli)
        st.session_state.messages.append({"role": "assistant", "content": res_cli})
    st.rerun()
