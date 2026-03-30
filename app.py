import streamlit as st
import anthropic
import pandas as pd
from datetime import datetime
import json
from streamlit_gsheets import GSheetsConnection

# CONFIGURACIÓN
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ClGVOcDcgogynxE8lgNdmJUhzP10UvE-1gpjQKl428k/edit"

client = anthropic.Anthropic(api_key=API_KEY)

st.set_page_config(page_title="La Ford de Warnes", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown('<h1 style="color:#003478;text-align:center;">🛞 La Ford de Warnes</h1>', unsafe_allow_html=True)

if 'form_data' not in st.session_state:
    st.session_state.form_data = {"nom": "", "pat": "", "mod": "", "añ": "", "mot": "", "con": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

def guardar_en_google_sheets():
    d = st.session_state.form_data
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

with st.sidebar:
    st.header("📋 Ficha del Cliente")
    st.session_state.form_data["nom"] = st.text_input("Nombre", value=st.session_state.form_data["nom"])
    st.session_state.form_data["pat"] = st.text_input("Patente", value=st.session_state.form_data["pat"])
    st.session_state.form_data["mod"] = st.text_input("Modelo", value=st.session_state.form_data["mod"])
    st.session_state.form_data["añ"] = st.text_input("Año", value=st.session_state.form_data["añ"])
    st.session_state.form_data["mot"] = st.text_input("Motor", value=st.session_state.form_data["mot"])
    st.session_state.form_data["con"] = st.text_area("Pedido", value=st.session_state.form_data["con"])
    if st.button("💾 GUARDAR CONSULTA", type="primary"):
        if guardar_en_google_sheets():
            st.success("✅ ¡Guardado!")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("¿Qué repuesto buscás?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    instruct = "Sos Juan de La Ford. Hablás como repuestero de Warnes. SIEMPRE JSON primero, luego '---'. JSON: {\"nombre\":\"\",\"patente\":\"\",\"modelo\":\"\",\"año\":\"\",\"motor\":\"\",\"repuesto\":\"\"}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514", 
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
            if d.get("motor"): st.session_state.form_data["mot"] = d["motor"]
            if d.get("repuesto"): st.session_state.form_data["con"] = d["repuesto"]
        except: pass
        res_cli = partes[1].strip()
    else: res_cli = texto

    with st.chat_message("assistant"):
        st.markdown(res_cli)
        st.session_state.messages.append({"role": "assistant", "content": res_cli})
    st.rerun()
