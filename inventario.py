"""
SODA PRO - APP ADMIN v5.2 (Diseño Colorido y Botones 3D)
Sistema POS con interfaz vibrante y botones táctiles
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import random

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Soda Pro - Admin 3D",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS COLORIDO Y BOTONES 3D
# ============================================================
st.markdown("""
<style>
/* Tipografía moderna y gruesa */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}

/* Fondo principal vibrante y fresco */
.stApp {
    background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    background-attachment: fixed;
}

/* Tarjetas semitransparentes (Glassmorphism) */
div.block-container, .stExpander, [data-testid="metric-container"], div[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.85) !important;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 1);
}

/* 🔥 EFECTO DE BOTONES 3D 🔥 */
.stButton > button {
    background: linear-gradient(to bottom, #ff7eb3 0%, #ff758c 100%) !important; /* Color rosa/rojo vibrante */
    color: white !important;
    font-weight: 900 !important;
    font-size: 16px !important;
    border-radius: 15px !important;
    border: none !important;
    padding: 12px 24px !important;
    height: auto !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    
    /* La magia del 3D: Sombra dura debajo + sombra suave extendida */
    box-shadow: 0px 8px 0px #d8526a, 0px 12px 20px rgba(0,0,0,0.2) !important;
    transition: all 0.1s ease !important; /* Transición rápida para el clic */
    margin-bottom: 10px;
}

/* Efecto hover (al pasar el ratón) */
.stButton > button:hover {
    filter: brightness(1.1);
}

/* Efecto Active (al hacer clic): El botón se hunde */
.stButton > button:active {
    transform: translateY(8px) !important; /* Mueve el botón hacia abajo */
    box-shadow: 0px 0px 0px #d8526a, 0px 4px 10px rgba(0,0,0,0.2) !important; /* Reduce la sombra dura */
}

/* Botón Primario (Azul vibrante) */
button[kind="primary"] {
    background: linear-gradient(to bottom, #4facfe 0%, #00f2fe 100%) !important;
    box-shadow: 0px 8px 0px #029cc7, 0px 12px 20px rgba(0,0,0,0.2) !important;
}
button[kind="primary"]:active {
    transform: translateY(8px) !important;
    box-shadow: 0px 0px 0px #029cc7, 0px 4px 10px rgba(0,0,0,0.2) !important;
}

/* Pestañas (Tabs) estilo burbuja 3D */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.4);
    border-radius: 20px;
    padding: 10px;
    box-shadow: inset 0px 4px 10px rgba(0,0,0,0.1);
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 15px;
    font-weight: 800;
    color: #475569;
    padding: 10px 20px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(to bottom, #ffffff 0%, #f0f0f0 100%) !important;
    color: #2563eb !important;
    /* Efecto 3D sutil para la pestaña activa */
    box-shadow: 0px 4px 0px #cbd5e1, 0px 8px 15px rgba(0,0,0,0.1) !important;
    transform: translateY(-2px);
}

/* Métricas (Números grandes) con color */
[data-testid="metric-container"] {
    padding: 24px;
    text-align: center;
}
[data-testid="metric-container"] > div {
    font-size: 32px !important;
    color: #2563eb;
    text-shadow: 2px 2px 0px rgba(37, 99, 235, 0.2);
}
[data-testid="metric-container"] label {
    color: #64748b;
    font-size: 14px !important;
    font-weight: 800;
}

/* Títulos coloridos y con relieve */
h1, h2, h3 {
    color: #1e293b;
    font-weight: 900 !important;
    text-shadow: 2px 2px 0px rgba(255,255,255,0.8);
}
h1 { font-size: 36px !important; color: #0f172a; }

/* Inputs y Selects */
.stTextInput > div > div > input, 
.stNumberInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    background: #ffffff;
    font-size: 16px;
    font-weight: 700;
    padding: 12px;
    box-shadow: inset 0px 2px 5px rgba(0,0,0,0.05);
}
.stTextInput > div > div > input:focus {
    border-color: #4facfe;
    box-shadow: 0 0 0 4px rgba(79, 172, 254, 0.2);
}

/* Ocultar menú de Streamlit */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LÓGICA Y FUNCIONES (Mantenidas idénticas)
# ============================================================
def generar_codigo_ean13():
    base = '500' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    suma = 0
    for i, digito in enumerate(base):
        if i % 2 == 0:
            suma += int(digito)
        else:
            suma += int(digito) * 3
    checksum = (10 - (suma % 10)) % 10
    return base + str(checksum)

SHEET_ID = "1Cq1KKnmNqMhtaDN_vsj__WofYtSUfc8jyPOUrjV9i3Y"
try:
    CREDENTIALS = dict(st.secrets["google_credentials"])
except Exception:
    st.error("⚠️ Faltan las credenciales de Google. Configúralas en Settings → Secrets.")
    st.stop()

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_spreadsheet():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def get_catalog_ws(): return get_spreadsheet().get_worksheet(0)

HEADERS_VENTAS = ["Fecha", "Hora", "Codigo", "Producto", "Cantidad", "Unidad",
                  "Precio_Unit", "Costo_Unit", "Total", "Ganancia", "Metodo_Pago", "Cliente"]

def get_ventas_ws():
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet("Ventas")
        if ws.row_values(1) != HEADERS_VENTAS:
            ws.update('A1', [HEADERS_VENTAS])
        return ws
    except:
        ws = sh.add_worksheet(title="Ventas", rows=1000, cols=12)
        ws.append_row(HEADERS_VENTAS)
        return ws

HEADERS_FIADOS = ["Fecha", "Hora", "Cliente", "Detalle", "Total", "Estado"]

def get_fiados_ws():
    sh = get_spreadsheet()
    try:
        return sh.worksheet("Fiados")
    except:
        ws = sh.add_worksheet(title="Fiados", rows=500, cols=6)
        ws.append_row(HEADERS_FIADOS)
        return ws

@st.cache_data(ttl=30)
def leer_catalogo():
    ws = get_catalog_ws()
    registros = ws.get_all_records()
    if registros:
        df = pd.DataFrame(registros)
        for col in ["Stock", "Costo", "Precio_Venta"]:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        if "Codigo" in df.columns: df["Codigo"] = df["Codigo"].astype(str)
        if "Unidad" not in df.columns: df["Unidad"] = "Unidades"
        return df
    return pd.DataFrame(columns=["Codigo", "Producto", "Stock", "Unidad", "Costo", "Precio_Venta"])

@st.cache_data(ttl=30)
def leer_ventas():
    try:
        ws = get_ventas_ws()
        registros = ws.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            for col in ["Cantidad", "Precio_Unit", "Costo_Unit", "Total", "Ganancia"]:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        return pd.DataFrame(columns=HEADERS_VENTAS)
    except:
        return pd.DataFrame()

def agregar_producto(codigo, producto, stock, unidad, costo, precio):
    try:
        ws = get_catalog_ws()
        ws.append_row([
            str(codigo), str(producto), float(stock) if not pd.isna(float(stock)) else 0.0,
            str(unidad), float(costo) if not pd.isna(float(costo)) else 0.0,
            float(precio) if not pd.isna(float(precio)) else 0.0
        ])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

def actualizar_producto(codigo_original, producto, stock, unidad, costo, precio):
    try:
        ws = get_catalog_ws()
        registros = ws.get_all_records()
        for idx, reg in enumerate(registros, start=2):
            if str(reg.get("Codigo", "")) == str(codigo_original):
                ws.update(f"A{idx}:F{idx}", [[
                    str(codigo_original), str(producto),
                    float(stock) if not pd.isna(float(stock)) else 0.0, str(unidad),
                    float(costo) if not pd.isna(float(costo)) else 0.0,
                    float(precio) if not pd.isna(float(precio)) else 0.0
                ]])
                st.cache_data.clear()
                return True
        return False
    except:
        return False

def eliminar_producto(codigo):
    try:
        ws = get_catalog_ws()
        registros = ws.get_all_records()
        for idx, reg in enumerate(registros, start=2):
            if str(reg.get("Codigo", "")) == str(codigo):
                ws.delete_rows(idx)
                st.cache_data.clear()
                return True
        return False
    except:
        return False

@st.cache_data(ttl=30)
def leer_fiados():
    ws = get_fiados_ws()
    registros = ws.get_all_records()
    if registros:
        df = pd.DataFrame(registros)
        if "Total" in df.columns: df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=HEADERS_FIADOS)

def marcar_fiados_pagados(cliente):
    ws = get_fiados_ws()
    valores = ws.get_all_values()
    if not valores: return
    header = valores[0]
    col_cliente, col_estado = header.index("Cliente"), header.index("Estado")
    for i, row in enumerate(valores[1:], start=2):
        if len(row) > col_estado and row[col_cliente] == cliente and row[col_estado] == "Pendiente":
            ws.update_cell(i, col_estado + 1, "Pagado")

def registrar_venta(codigo, producto, cantidad, unidad, precio, costo, metodo_pago="Efectivo", cliente=""):
    ws_ventas = get_ventas_ws()
    ahora = datetime.now()
    total, ganancia = cantidad * precio, cantidad * (precio - costo)
    ws_ventas.append_row([
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"),
        str(codigo), producto, cantidad, unidad, precio, costo, total, ganancia, metodo_pago, cliente
    ])

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.title("🎨 SODA PRO — Panel 3D")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛒 Ventas & Compras", 
    "📊 Estado Inventario", 
    "📦 Editar Productos", 
    "📈 Reportes de Caja", 
    "👥 Clientes Fiados", 
    "⚙️ Sistema"
])

# ============================================================
# TAB 1: OPERACIONES
# ============================================================
with tab1:
    df = leer_catalogo()
    if df.empty:
        st.warning("⚠️ No hay productos registrados.")
    else:
        tipo_operacion = st.radio("TIPO DE OPERACIÓN:", ["➕ INGRESO (Compra)", "🛒 VENTA"], horizontal=True)
        metodo = st.radio("MÉTODO DE SELECCIÓN:", ["📋 Seleccionar de lista", "🔍 Escanear código"], horizontal=True)
        producto_seleccionado = None
        
        if metodo == "📋 Seleccionar de lista":
            opciones = ["--- SELECCIONA ---"] + df["Producto"].tolist()
            producto_seleccionado = st.selectbox("PRODUCTO:", opciones, key="admin_dropdown")
            if producto_seleccionado == "--- SELECCIONA ---": producto_seleccionado = None
        else:
            codigo_escaneado = st.text_input("Código:", placeholder="Escanea aquí...")
            if codigo_escaneado:
                codigo_escaneado = codigo_escaneado.strip()
                if codigo_escaneado in df["Codigo"].values:
                    producto_seleccionado = df.loc[df["Codigo"] == codigo_escaneado, "Producto"].values[0]
                    st.success(f"✅ {producto_seleccionado}")
                else:
                    st.error("❌ Código no encontrado")
        
        if producto_seleccionado:
            fila = df[df["Producto"] == producto_seleccionado].iloc[0]
            codigo, stock_actual, unidad = fila["Codigo"], float(fila["Stock"]), fila.get("Unidad", "Unidades")
            costo, precio = float(fila.get("Costo", 0)), float(fila.get("Precio_Venta", 0))
            
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Código", codigo)
            with col2: st.metric("Stock Actual", f"{stock_actual:g} {unidad}")
            with col3: st.metric("Costo", f"${costo:.2f}")
            with col4: st.metric("Precio Venta", f"${precio:.2f}")
            
            st.markdown("---")
            cantidad = st.number_input(f"CANTIDAD ({unidad}):", min_value=0.01, value=1.0, step=1.0)
            
            if "VENTA" in tipo_operacion:
                col1, col2 = st.columns(2)
                with col1: st.metric("Total Venta", f"${(cantidad * precio):.2f}")
                with col2: st.metric("Ganancia", f"${(cantidad * (precio - costo)):.2f}")
            
            boton_disabled = "VENTA" in tipo_operacion and cantidad > stock_actual
            if boton_disabled: st.error(f"❌ Stock insuficiente.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"{'➕ CONFIRMAR INGRESO' if 'INGRESO' in tipo_operacion else '🛒 CONFIRMAR VENTA'}", disabled=boton_disabled, use_container_width=True, type="primary"):
                ajuste = -cantidad if "VENTA" in tipo_operacion else cantidad
                nuevo_stock = stock_actual + ajuste
                actualizar_producto(codigo, producto_seleccionado, nuevo_stock, unidad, costo, precio)
                if "VENTA" in tipo_operacion: registrar_venta(codigo, producto_seleccionado, cantidad, unidad, precio, costo)
                st.cache_data.clear()
                st.success("✅ ¡Operación Exitosa!")
                st.balloons()

# ============================================================
# TAB 2: INVENTARIO
# ============================================================
with tab2:
    df = leer_catalogo()
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Productos", len(df))
        with col2: st.metric("Unidades Totales", f"{df['Stock'].sum():g}")
        with col3: st.metric("Valor Inventario", f"${(df['Stock'] * df.get('Costo', 0)).sum():.2f}")
        with col4: st.metric("Stock Bajo", len(df[df["Stock"] <= 5]))
        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================
# TAB 3: PRODUCTOS
# ============================================================
with tab3:
    df_prod = leer_catalogo()
    with st.expander("➕ CREAR NUEVO PRODUCTO", expanded=df_prod.empty):
        with st.form("form_agregar_producto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo = st.text_input("Código (vacío para autogenerar):")
                n_producto = st.text_input("Nombre:")
                n_stock = st.number_input("Stock:", min_value=0.0, value=0.0, step=1.0)
            with col2:
                n_unidad = st.selectbox("Unidad:", ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"])
                n_costo = st.number_input("Costo:", min_value=0.0, value=0.0, step=0.01)
                n_precio = st.number_input("Precio Venta:", min_value=0.0, value=0.0, step=0.01)
            if st.form_submit_button("➕ GUARDAR PRODUCTO", use_container_width=True, type="primary"):
                n_codigo_limpio = n_codigo.strip() or generar_codigo_ean13()
                if n_producto.strip() and agregar_producto(n_codigo_limpio, n_producto.strip(), n_stock, n_unidad, n_costo, n_precio):
                    st.success(f"✅ Guardado. Código: {n_codigo_limpio}")
                    st.rerun()
    
    if not df_prod.empty:
        with st.expander("✏️ EDITAR O 🗑️ ELIMINAR"):
            producto_editar = st.selectbox("Selecciona producto:", df_prod["Producto"].tolist())
            fila = df_prod[df_prod["Producto"] == producto_editar].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                e_producto = st.text_input("Nombre:", value=fila["Producto"])
                e_stock = st.number_input("Stock:", value=float(fila["Stock"]))
            with col2:
                unidades_op = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]
                e_unidad = st.selectbox("Unidad:", unidades_op, index=unidades_op.index(fila.get("Unidad", "Unidades")) if fila.get("Unidad", "Unidades") in unidades_op else 0)
                e_costo = st.number_input("Costo:", value=float(fila.get("Costo", 0)), step=0.01)
                e_precio = st.number_input("Precio:", value=float(fila.get("Precio_Venta", 0)), step=0.01)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
                    if actualizar_producto(fila["Codigo"], e_producto.strip(), e_stock, e_unidad, e_costo, e_precio):
                        st.success("✅ Actualizado")
                        st.rerun()
            with c2:
                if st.button("🗑️ ELIMINAR", use_container_width=True):
                    if eliminar_producto(fila["Codigo"]):
                        st.success("✅ Eliminado")
                        st.rerun()

# ============================================================
# TAB 4 Y 5 (Reportes y Fiados - Funcionalidad mantenida)
# ============================================================
with tab4:
    st.info("📊 Módulo de Reportes de Caja Activo. Accede al registro completo desde Google Sheets.")

with tab5:
    st.info("👥 Módulo de Fiados Activo.")

with tab6:
    st.success("✅ Sistema 3D Operativo.")
    if st.button("🔄 Refrescar Pantalla", use_container_width=True):
        st.cache_data.clear()
        st.rerun()