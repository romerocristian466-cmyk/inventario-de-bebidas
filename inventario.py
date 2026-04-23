import streamlit as st
from streamlit_gsheets import GSheetsConnection
import cv2
import numpy as np
from datetime import datetime

# --- CONFIGURACIÓN DE LA NUBE ---
# Aquí pegaremos la URL de tu Google Sheet más adelante en los "Secrets" de Streamlit
SHEET_URL = st.secrets["public_gsheets_url"]

st.set_page_config(page_title="Inventario Cloud", page_icon="☁️")
st.title("☁️ Inventario en la Nube")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    return conn.read(spreadsheet=SHEET_URL, usecols=[0, 1, 2, 3], ttl=0)

def procesar_codigo(img_buffer):
    file_bytes = np.asarray(bytearray(img_buffer.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    detector = cv2.barcode.BarcodeDetector()
    resultado = detector.detectAndDecode(img)
    # Manejo de versiones de OpenCV
    if len(resultado) == 4:
        ok, decoded_info, _, _ = resultado
    else:
        decoded_info, _, _ = resultado
        ok = True if decoded_info and decoded_info[0] else False
    
    if ok and decoded_info and decoded_info[0]:
        return decoded_info[0]
    return None

# --- LÓGICA DE LA APP ---
menu = ["Venta (Salida)", "Ingreso (Entrada)", "Ver Stock"]
opcion = st.sidebar.selectbox("Acción", menu)

df = leer_datos()

if opcion == "Ver Stock":
    st.dataframe(df, use_container_width=True)

else:
    st.subheader(f"Registro de {opcion}")
    metodo = st.radio("Método:", ["Cámara", "Manual"])
    
    codigo_final = None
    if metodo == "Cámara":
        foto = st.camera_input("Escanea")
        if foto:
            codigo_final = procesar_codigo(foto)
    else:
        codigo_final = st.text_input("Escribe el código:")

    if codigo_final:
        codigo_str = str(codigo_final)
        st.success(f"Código: {codigo_str}")
        
        # Buscar en el DataFrame de Google Sheets
        df['Codigo'] = df['Codigo'].astype(str)
        existe = codigo_str in df['Codigo'].values
        
        nombre_act = df.loc[df['Codigo'] == codigo_str, 'Producto'].values[0] if existe else ""
        nombre = st.text_input("Nombre:", value=nombre_act)
        cantidad = st.number_input("Cantidad:", min_value=1, value=1)

        if st.button("Confirmar"):
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if existe:
                ajuste = -cantidad if "Venta" in opcion else cantidad
                nuevo_stock = int(df.loc[df['Codigo'] == codigo_str, 'Stock'].values[0]) + ajuste
                df.loc[df['Codigo'] == codigo_str, 'Stock'] = nuevo_stock
                df.loc[df['Codigo'] == codigo_str, 'Ultima_Actualizacion'] = ahora
                if nombre: df.loc[df['Codigo'] == codigo_str, 'Producto'] = nombre
            else:
                stock_ini = -cantidad if "Venta" in opcion else cantidad
                nuevo_item = pd.DataFrame([{"Codigo": codigo_str, "Producto": nombre, "Stock": stock_ini, "Ultima_Actualizacion": ahora}])
                df = pd.concat([df, nuevo_item], ignore_index=True)

            # GUARDAR EN GOOGLE SHEETS
            conn.update(spreadsheet=SHEET_URL, data=df)
            st.balloons()
            st.success("¡Google Sheets actualizado!")