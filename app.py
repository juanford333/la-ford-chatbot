import streamlit as st
import anthropic
import pandas as pd
from datetime import datetime
import os
import json
import urllib.parse

# ==========================================
# 🔑 CONFIGURACIÓN INICIAL
# ==========================================
API_KEY = "API_KEY = st.secrets["ANTHROPIC_API_KEY"]"
EXCEL_FILE = "clientes_ford.xlsx"
MI_NUMERO_WHATSAPP = "5491162756333" # <--- PONÉ TU NÚMERO ACÁ (EJ: 5491165432100)

try:
    client = anthropic.Anthropic(api_key=API_KEY)
except:
    st.error("Error de conexión con la IA.")

st.set_page_config(page_title="La Ford de Warnes", layout="wide", page_icon="🛞")

# Estética del Mostrador
st.markdown("""
    <div style="background-color:#003478;padding:20px;border-radius:10px;margin-bottom:25px;border: 2px solid #0056b3">
    <h1 style="color:white;text-align:center;margin:0;font-family:Arial;">🛞 La Ford de Warnes</h1>
    <p style="color:#d1d1d1;text-align:center;margin:0;font-weight:bold;">Mostrador Digital Sincronizado - Juan</p>
    </div>
""", unsafe_allow_html=True)

# --- MEMORIA ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"nom": "", "pat": "", "mod": "", "añ": "", "mot": "", "con": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FUNCIÓN DE GUARDADO PROFESIONAL ---
def guardar_excel_profesional():
    d = st.session_state.form_data
    try:
        fecha_reg = datetime.now().strftime("%d/%m/%Y %H:%M")
        nueva_fila = pd.DataFrame([[
            fecha_reg, str(d['nom']).upper(), str(d['pat']).upper(), "",
            str(d['mod']).upper(), str(d['añ']), str(d['mot']).upper(), 
            str(d['con']).upper(), "CONSULTA"
        ]], columns=["FECHA", "CLIENTE", "PATENTE", "VIN/CHASIS", "MODELO", "AÑO", "MOTOR", "REPUESTOS/CONSULTA", "ESTADO"])

        if os.path.exists(EXCEL_FILE):
            df_e = pd.read_excel(EXCEL_FILE)
            df_e = df_e.dropna(subset=['FECHA'])
            df_final = pd.concat([df_e, nueva_fila], ignore_index=True)
        else:
            df_final = nueva_fila

        with pd.ExcelWriter(EXCEL_FILE, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Ventas')
            workbook  = writer.book
            worksheet = writer.sheets['Ventas']
            fmt_header = workbook.add_format({'bold':True,'fg_color':'#003478','font_color':'white','border':1})
            fmt_celda = workbook.add_format({'border':1})
            for i, col in enumerate(df_final.columns):
                max_len = max(df_final[col].astype(str).map(len).max(), len(col)) + 4
                worksheet.set_column(i, i, max_len, fmt_celda)
                worksheet.write(0, i, col, fmt_header)
        return True
    except:
        return False

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Ficha del Cliente")
    st.session_state.form_data["nom"] = st.text_input("Nombre", value=st.session_state.form_data["nom"])
    st.session_state.form_data["pat"] = st.text_input("Patente", value=st.session_state.form_data["pat"])
    st.session_state.form_data["mod"] = st.text_input("Modelo", value=st.session_state.form_data["mod"])
    st.session_state.form_data["añ"] = st.text_input("Año", value=st.session_state.form_data["añ"])
    st.session_state.form_data["mot"] = st.text_input("Motor", value=st.session_state.form_data["mot"])
    st.session_state.form_data["con"] = st.text_area("Pedido", value=st.session_state.form_data["con"])

    st.markdown("---")
    if st.button("💾 GUARDAR CONSULTA", use_container_width=True, type="primary"):
        if guardar_excel_profesional():
            st.success("✅ Guardado en Excel")
            # Generar Link de WhatsApp
            d = st.session_state.form_data
            mensaje_wa = f"*NUEVA CONSULTA - LA FORD*%0A*Cliente:* {d['nom']}%0A*Vehículo:* {d['mod']} {d['añ']}%0A*Pedido:* {d['con']}"
            link_wa = f"https://wa.me/{5491162756333}?text={mensaje_wa}"
            st.markdown(f'''<a href="{link_wa}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;">
                📲 ENVIAR A MI WHATSAPP</div></a>''', unsafe_allow_html=True)

    if st.button("🗑️ NUEVA CONSULTA"):
        st.session_state.form_data = {"nom": "", "pat": "", "mod": "", "añ": "", "mot": "", "con": ""}
        st.session_state.messages = []
        st.rerun()

# --- CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("¿En qué te ayudo con tu Ford?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        instruct = (
            "Tu nombre es Juan, repuestero de 'La Ford de Warnes'. Sos experto, amable y usás jerga argentina. "
            "PASO 1: Extrae datos en JSON: {\"nombre\":\"\",\"patente\":\"\",\"modelo\":\"\",\"año\":\"\",\"motor\":\"\",\"repuesto\":\"\"}. "
            "PASO 2: Escribe '---'. "
            "PASO 3: Responde como Juan, asesora y usa siempre Pesos Argentinos ($)."
        )

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
                js_raw = partes[0].strip()
                js_raw = js_raw[js_raw.find('{'):js_raw.rfind('}') + 1]
                d = json.loads(js_raw)
                for k, v in {"nombre":"nom","patente":"pat","modelo":"mod","año":"añ","motor":"mot","repuesto":"con"}.items():
                    if d.get(k): st.session_state.form_data[v] = d[k]
            except: pass
            res_cli = partes[1].strip()
        else: res_cli = texto

        with st.chat_message("assistant"):
            st.markdown(res_cli)
            st.session_state.messages.append({"role": "assistant", "content": res_cli})
        st.rerun()
    except Exception as e: st.error(f"Error: {e}")
