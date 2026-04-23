import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import base64
import zxingcpp
from PIL import Image
from datetime import datetime

SHEET_URL = st.secrets["public_gsheets_url"]
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

st.set_page_config(page_title="Inventario de Bebidas", page_icon="🥤", layout="wide")

def get_client():
    creds_dict = json.loads(base64.b64decode(st.secrets["gcp_b64"]).decode())
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=30)
def leer_datos():
    gc = get_client()
    sh = gc.open_by_url(SHEET_URL)
    ws = sh.get_worksheet(0)
    registros = ws.get_all_records()
    if registros:
        return pd.DataFrame(registros)
    return pd.DataFrame(columns=["Codigo", "Producto", "Stock", "Ultima_Actualizacion"])

def guardar_datos(df):
    gc = get_client()
    sh = gc.open_by_url(SHEET_URL)
    ws = sh.get_worksheet(0)
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

def procesar_codigo(img_buffer):
    img = Image.open(img_buffer)
    resultados = zxingcpp.read_barcodes(img)
    if resultados:
        return resultados[0].text
    return None

st.title("🥤 Inventario de Bebidas")
menu = ["📦 Ver Stock", "➕ Ingreso (Entrada)", "🛒 Venta (Salida)"]
opcion = st.sidebar.selectbox("¿Qué deseas hacer?", menu)
st.sidebar.markdown("---")
st.sidebar.caption("Sistema de inventario en la nube")

if opcion == "📦 Ver Stock":
    st.subheader("📦 Stock Actual")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
    df = leer_datos()
    if df.empty:
        st.info("No hay productos registrados todavía.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total productos", len(df))
        try:
            col2.metric("Unidades totales", int(df["Stock"].astype(int).sum()))
            bajo_stock = df[df["Stock"].astype(int) <= 5]
            col3.metric("⚠️ Bajo stock (≤5)", len(bajo_stock))
        except:
            pass
        st.dataframe(df, use_container_width=True)
        try:
            if not bajo_stock.empty:
                st.warning("⚠️ Productos con stock bajo:")
                st.dataframe(bajo_stock[["Producto", "Stock"]], use_container_width=True)
        except:
            pass

else:
    es_venta = "Venta" in opcion
    icono = "🛒" if es_venta else "➕"
    st.subheader(f"{icono} {'Registrar Venta' if es_venta else 'Registrar Ingreso'}")
    df = leer_datos()
    metodo = st.radio("Método:", ["📷 Cámara", "⌨️ Manual"], horizontal=True)

    codigo_final = None
    if metodo == "📷 Cámara":
        foto = st.camera_input("Apunta la cámara al código de barras")
        if foto:
            codigo_final = procesar_codigo(foto)
            if not codigo_final:
                st.warning("⚠️ No se detectó código. Usa el método manual.")
    else:
        codigo_final = st.text_input("Código del producto:")

    if codigo_final:
        codigo_str = str(codigo_final).strip()
        st.success(f"✅ Código: **{codigo_str}**")
        df["Codigo"] = df["Codigo"].astype(str)
        existe = codigo_str in df["Codigo"].values

        if existe:
            nombre_actual = df.loc[df["Codigo"] == codigo_str, "Producto"].values[0]
            stock_actual  = int(df.loc[df["Codigo"] == codigo_str, "Stock"].values[0])
            st.info(f"Producto: **{nombre_actual}** | Stock actual: **{stock_actual}**")
        else:
            nombre_actual = ""
            stock_actual  = 0
            st.info("Producto nuevo — se registrará al confirmar.")

        nombre   = st.text_input("Nombre del producto:", value=str(nombre_actual))
        cantidad = st.number_input("Cantidad:", min_value=1, value=1)

        if es_venta and existe and cantidad > stock_actual:
            st.error(f"❌ Stock insuficiente. Disponible: {stock_actual}")
        else:
            if st.button(f"{'🛒 Confirmar Venta' if es_venta else '➕ Confirmar Ingreso'}", type="primary"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                if existe:
                    ajuste      = -cantidad if es_venta else cantidad
                    nuevo_stock = stock_actual + ajuste
                    df.loc[df["Codigo"] == codigo_str, "Stock"]                = nuevo_stock
                    df.loc[df["Codigo"] == codigo_str, "Ultima_Actualizacion"] = ahora
                    if nombre:
                        df.loc[df["Codigo"] == codigo_str, "Producto"] = nombre
                else:
                    stock_ini  = -cantidad if es_venta else cantidad
                    nuevo_item = pd.DataFrame([{
                        "Codigo": codigo_str, "Producto": nombre,
                        "Stock": stock_ini,   "Ultima_Actualizacion": ahora
                    }])
                    df = pd.concat([df, nuevo_item], ignore_index=True)
                guardar_datos(df)
                st.cache_data.clear()
                st.balloons()
                st.success("✅ ¡Actualizado!")
