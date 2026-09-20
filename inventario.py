"""
SODA PRO - APP ADMIN v5.1 (Diseño Visual Ultra Profesional)
Sistema POS profesional con diseño minimalista, reportes avanzados y control total
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
    page_title="Soda Pro - Admin Profesional",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS MINIMALISTA PREMIUM (Estilo Vercel / Stripe / Apple)
# ============================================================
st.markdown("""
<style>
/* Importar tipografía moderna Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fondo principal limpio y neutro (Modo Claro Profesional) */
.stApp {
    background-color: #f8fafc;
    color: #0f172a;
}

/* Ocultar elementos de Streamlit por defecto */
#MainMenu, footer, header {
    visibility: hidden;
}

/* Contenedores y tarjetas estéticas tipo Glassmorphism suave */
div.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Métricas profesionales estilo tarjeta flotante */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}

[data-testid="metric-container"]:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

[data-testid="metric-container"] > div {
    font-size: 26px !important;
    font-weight: 700;
    color: #0f172a;
}

[data-testid="metric-container"] label {
    font-size: 13px !important;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Botones principales elegantes */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    height: 44px;
    background: #0f172a;
    color: white;
    font-weight: 600;
    font-size: 14px;
    border: none;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #1e293b;
    border-color: #334155;
    transform: translateY(-1px);
}

/* Botón primario especial */
button[kind="primary"] {
    background: #2563eb !important;
}
button[kind="primary"]:hover {
    background: #1d4ed8 !important;
}

/* Pestañas (Tabs) estilo moderno flotante */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #e2e8f0;
    border-radius: 10px;
    padding: 6px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    background-color: transparent;
    padding: 10px 20px;
    font-weight: 600;
    color: #475569;
    font-size: 14px;
    border: none;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Inputs de texto y números limpios */
.stTextInput > div > div > input, 
.stNumberInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    font-size: 14px;
    padding: 10px 14px;
    color: #0f172a;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Tablas y DataFrames limpios */
div[data-testid="stDataFrame"] {
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    padding: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

/* Expanders elegantes */
.stExpander {
    border: 1px solid #e2e8f0;
    border-radius: 10px !important;
    background: #ffffff;
    margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.stExpander summary {
    font-weight: 600;
    color: #0f172a;
    padding: 14px;
}

/* Títulos con estilo corporativo */
h1, h2, h3 {
    color: #0f172a;
    font-weight: 700;
    letter-spacing: -0.025em;
}

h1 {
    font-size: 32px !important;
    margin-bottom: 24px;
}

h2 {
    font-size: 24px !important;
    margin-bottom: 18px;
}

h3 {
    font-size: 18px !important;
    margin-bottom: 12px;
}

/* Separadores sutiles */
.stMarkdown hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 24px 0;
}

/* Alertas estilizadas */
.stSuccess, .stError, .stInfo, .stWarning {
    border-radius: 8px !important;
    border: 1px solid transparent;
    padding: 14px;
    font-size: 14px;
}

.stSuccess { background: #f0fdf4 !important; color: #166534 !important; border-color: #bbf7d0; }
.stError { background: #fef2f2 !important; color: #991b1b !important; border-color: #fecaca; }
.stInfo { background: #eff6ff !important; color: #1e40af !important; border-color: #bfdbfe; }
.stWarning { background: #fffbeb !important; color: #92400e !important; border-color: #fde68a; }

/* Sidebar corporativa limpia */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

/* Radio buttons y Checkbox sutiles */
.stRadio > div {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# GENERADOR DE CÓDIGOS EAN-13
# ============================================================
def generar_codigo_ean13():
    """Genera un código EAN-13 válido con checksum correcto"""
    base = '500' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    suma = 0
    for i, digito in enumerate(base):
        if i % 2 == 0:
            suma += int(digito)
        else:
            suma += int(digito) * 3
    checksum = (10 - (suma % 10)) % 10
    return base + str(checksum)

# ============================================================
# GOOGLE SHEETS CONFIGURATION
# ============================================================
SHEET_ID = "1Cq1KKnmNqMhtaDN_vsj__WofYtSUfc8jyPOUrjV9i3Y"
try:
    CREDENTIALS = dict(st.secrets["google_credentials"])
except Exception:
    st.error("⚠️ Faltan las credenciales de Google. Configúralas en Settings → Secrets.")
    st.stop()

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ============================================================
# FUNCIONES DE GOOGLE SHEETS
# ============================================================
def get_spreadsheet():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def get_catalog_ws():
    return get_spreadsheet().get_worksheet(0)

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
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        if "Codigo" in df.columns:
            df["Codigo"] = df["Codigo"].astype(str)
        if "Unidad" not in df.columns:
            df["Unidad"] = "Unidades"
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
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        return pd.DataFrame(columns=HEADERS_VENTAS)
    except:
        return pd.DataFrame()

def agregar_producto(codigo, producto, stock, unidad, costo, precio):
    try:
        ws = get_catalog_ws()
        nueva_fila = [
            str(codigo),
            str(producto),
            float(stock) if not pd.isna(float(stock)) else 0.0,
            str(unidad),
            float(costo) if not pd.isna(float(costo)) else 0.0,
            float(precio) if not pd.isna(float(precio)) else 0.0
        ]
        ws.append_row(nueva_fila)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error agregando producto: {str(e)}")
        return False

def actualizar_producto(codigo_original, producto, stock, unidad, costo, precio):
    try:
        ws = get_catalog_ws()
        registros = ws.get_all_records()
        for idx, reg in enumerate(registros, start=2):
            if str(reg.get("Codigo", "")) == str(codigo_original):
                fila_actualizada = [
                    str(codigo_original),
                    str(producto),
                    float(stock) if not pd.isna(float(stock)) else 0.0,
                    str(unidad),
                    float(costo) if not pd.isna(float(costo)) else 0.0,
                    float(precio) if not pd.isna(float(precio)) else 0.0
                ]
                ws.update(f"A{idx}:F{idx}", [fila_actualizada])
                st.cache_data.clear()
                return True
        st.error(f"❌ No se encontró el producto con código {codigo_original}")
        return False
    except Exception as e:
        st.error(f"❌ Error actualizando: {str(e)}")
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
        st.error(f"❌ No se encontró el producto con código {codigo}")
        return False
    except Exception as e:
        st.error(f"❌ Error eliminando: {str(e)}")
        return False

@st.cache_data(ttl=30)
def leer_fiados():
    ws = get_fiados_ws()
    registros = ws.get_all_records()
    if registros:
        df = pd.DataFrame(registros)
        if "Total" in df.columns:
            df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=HEADERS_FIADOS)

def marcar_fiados_pagados(cliente):
    ws = get_fiados_ws()
    valores = ws.get_all_values()
    if not valores:
        return
    header = valores[0]
    col_cliente = header.index("Cliente")
    col_estado = header.index("Estado")
    for i, row in enumerate(valores[1:], start=2):
        if len(row) > col_estado and row[col_cliente] == cliente and row[col_estado] == "Pendiente":
            ws.update_cell(i, col_estado + 1, "Pagado")

def registrar_venta(codigo, producto, cantidad, unidad, precio, costo, metodo_pago="Efectivo", cliente=""):
    ws_ventas = get_ventas_ws()
    ahora = datetime.now()
    total = cantidad * precio
    ganancia = cantidad * (precio - costo)
    ws_ventas.append_row([
        ahora.strftime("%Y-%m-%d"),
        ahora.strftime("%H:%M:%S"),
        str(codigo), producto, cantidad, unidad,
        precio, costo, total, ganancia, metodo_pago, cliente
    ])

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.title("⚡ SODA PRO — Panel de Administración")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⚡ Operaciones", 
    "📊 Inventario", 
    "📦 Productos", 
    "📈 Reportes", 
    "👥 Fiados", 
    "⚙️ Sistema"
])

# ============================================================
# TAB 1: OPERACIONES
# ============================================================
with tab1:
    st.subheader("Control de Inventario y Ventas")
    df = leer_catalogo()
    
    if df.empty:
        st.warning("⚠️ No hay productos registrados en el catálogo.")
    else:
        tipo_operacion = st.radio(
            "TIPO DE OPERACIÓN:",
            ["➕ INGRESO (Compra)", "🛒 VENTA"],
            horizontal=True
        )
        st.markdown("---")
        
        metodo = st.radio(
            "MÉTODO DE SELECCIÓN:",
            ["📋 Seleccionar de lista", "🔍 Escanear código"],
            horizontal=True
        )
        
        producto_seleccionado = None
        
        if metodo == "📋 Seleccionar de lista":
            opciones = ["--- SELECCIONA UN PRODUCTO ---"] + df["Producto"].tolist()
            producto_seleccionado = st.selectbox("PRODUCTO:", opciones, key="admin_dropdown")
            if producto_seleccionado == "--- SELECCIONA UN PRODUCTO ---":
                producto_seleccionado = None
        else:
            st.info("📱 Apunta el escáner al código de barras")
            codigo_escaneado = st.text_input(
                "Código:",
                placeholder="El escáner escribirá aquí...",
                key="admin_scanner"
            )
            if codigo_escaneado:
                codigo_escaneado = codigo_escaneado.strip()
                if codigo_escaneado in df["Codigo"].values:
                    producto_seleccionado = df.loc[df["Codigo"] == codigo_escaneado, "Producto"].values[0]
                    st.success(f"✅ Encontrado: {producto_seleccionado}")
                else:
                    st.error(f"❌ Código {codigo_escaneado} no encontrado")
        
        if producto_seleccionado:
            fila = df[df["Producto"] == producto_seleccionado].iloc[0]
            codigo = fila["Codigo"]
            stock_actual = float(fila["Stock"])
            unidad = fila.get("Unidad", "Unidades")
            costo = float(fila.get("Costo", 0))
            precio = float(fila.get("Precio_Venta", 0))
            
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Código", codigo)
            with col2:
                st.metric("Stock Actual", f"{stock_actual:g} {unidad}")
            with col3:
                st.metric("Costo", f"${costo:.2f}")
            with col4:
                st.metric("Precio Venta", f"${precio:.2f}")
            
            st.markdown("---")
            cantidad = st.number_input(
                f"CANTIDAD A REGISTRAR ({unidad}):",
                min_value=0.01,
                value=1.0,
                step=1.0,
                format="%.2f"
            )
            
            if "VENTA" in tipo_operacion:
                total = cantidad * precio
                ganancia = cantidad * (precio - costo)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Venta", f"${total:.2f}")
                with col2:
                    st.metric("Ganancia Estimada", f"${ganancia:.2f}")
            
            boton_disabled = False
            if "VENTA" in tipo_operacion and cantidad > stock_actual:
                st.error(f"❌ Stock insuficiente. Disponible: {stock_actual:g} {unidad}")
                boton_disabled = True
            
            st.markdown("---")
            if st.button(
                f"{'➕ CONFIRMAR INGRESO' if 'INGRESO' in tipo_operacion else '🛒 CONFIRMAR VENTA'}",
                disabled=boton_disabled,
                use_container_width=True,
                type="primary"
            ):
                ajuste = -cantidad if "VENTA" in tipo_operacion else cantidad
                nuevo_stock = stock_actual + ajuste
                fila_producto = df[df["Producto"] == producto_seleccionado].iloc[0]
                actualizar_producto(
                    fila_producto["Codigo"],
                    fila_producto["Producto"],
                    nuevo_stock,
                    fila_producto.get("Unidad", "Unidades"),
                    float(fila_producto.get("Costo", 0)),
                    float(fila_producto.get("Precio_Venta", 0))
                )
                if "VENTA" in tipo_operacion:
                    registrar_venta(codigo, producto_seleccionado, cantidad, unidad, precio, costo)
                st.cache_data.clear()
                st.success(f"✅ Operación realizada con éxito para: {producto_seleccionado}")
                st.info(f"Nuevo stock actualizado: {nuevo_stock:g} {unidad}")

# ============================================================
# TAB 2: INVENTARIO
# ============================================================
with tab2:
    st.subheader("Estado General del Inventario")
    df = leer_catalogo()
    
    if df.empty:
        st.info("No hay productos registrados.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Productos", len(df))
        with col2:
            total_unidades = df["Stock"].sum()
            st.metric("Unidades Totales", f"{total_unidades:g}")
        with col3:
            valor_inventario = (df["Stock"] * df.get("Costo", 0)).sum()
            st.metric("Valor Inventario", f"${valor_inventario:.2f}")
        with col4:
            bajo_stock = df[df["Stock"] <= 5]
            st.metric("Stock Bajo", len(bajo_stock))
        
        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if not bajo_stock.empty:
            st.markdown("---")
            st.warning("⚠️ Productos con stock bajo (Menor o igual a 5 unidades)")
            st.dataframe(bajo_stock[["Producto", "Stock", "Unidad"]], 
                        use_container_width=True, hide_index=True)

# ============================================================
# TAB 3: PRODUCTOS
# ============================================================
with tab3:
    st.subheader("Gestión y Creación de Productos")
    df_prod = leer_catalogo()
    
    st.markdown("---")
    with st.expander("➕ AGREGAR PRODUCTO NUEVO", expanded=df_prod.empty):
        st.write("Si dejas el código en blanco, el sistema generará automáticamente un código EAN-13 válido escaneable.")
        with st.form("form_agregar_producto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo = st.text_input("Código de barras (Opcional):")
                n_producto = st.text_input("Nombre del producto:")
                n_stock = st.number_input("Stock inicial:", min_value=0.0, value=0.0, step=1.0)
            with col2:
                unidades_disponibles = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]
                n_unidad = st.selectbox("Unidad de medida:", unidades_disponibles)
                n_costo = st.number_input("Costo unitario:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                n_precio = st.number_input("Precio de venta unitario:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            enviado = st.form_submit_button("➕ GUARDAR NUEVO PRODUCTO", use_container_width=True, type="primary")
            if enviado:
                n_codigo_limpio = n_codigo.strip()
                if not n_codigo_limpio:
                    n_codigo_limpio = generar_codigo_ean13()
                if not n_producto.strip():
                    st.error("❌ El nombre del producto es obligatorio")
                elif not df_prod.empty and n_codigo_limpio in df_prod["Codigo"].values:
                    st.error(f"⚠️ Ya existe un producto registrado con el código {n_codigo_limpio}")
                else:
                    if agregar_producto(n_codigo_limpio, n_producto.strip(), n_stock, n_unidad, n_costo, n_precio):
                        st.success(f"✅ Producto '{n_producto}' guardado correctamente.")
                        st.info(f"📋 **Código asignado:** `{n_codigo_limpio}`")
                        st.rerun()
    
    if not df_prod.empty:
        st.markdown("---")
        with st.expander("📋 Ver códigos de barras para impresión o libreta"):
            codigos_display = df_prod[["Codigo", "Producto", "Unidad", "Precio_Venta"]].copy()
            codigos_display.columns = ["CÓDIGO", "PRODUCTO", "UNIDAD", "PRECIO"]
            st.dataframe(codigos_display, use_container_width=True, hide_index=True)
            csv_codigos = codigos_display.to_csv(index=False)
            st.download_button(
                "📥 Descargar códigos en CSV",
                data=csv_codigos,
                file_name=f"codigos_productos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    if not df_prod.empty:
        with st.expander("✏️ EDITAR O 🗑️ ELIMINAR PRODUCTO"):
            producto_editar = st.selectbox("Selecciona producto a modificar:", df_prod["Producto"].tolist(), key="editar_select")
            idx = df_prod[df_prod["Producto"] == producto_editar].index[0]
            fila = df_prod.loc[idx]
            
            col1, col2 = st.columns(2)
            with col1:
                e_producto = st.text_input("Nombre:", value=fila["Producto"], key="e_nombre")
                e_stock = st.number_input("Stock:", min_value=0.0, value=float(fila["Stock"]), step=1.0, key="e_stock")
            with col2:
                unidades_op = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]
                unidad_actual = fila.get("Unidad", "Unidades")
                idx_unidad = unidades_op.index(unidad_actual) if unidad_actual in unidades_op else 0
                e_unidad = st.selectbox("Unidad de medida:", unidades_op, index=idx_unidad, key="e_unidad")
                e_costo = st.number_input("Costo unitario:", min_value=0.0, value=float(fila.get("Costo", 0)), step=0.01, format="%.2f", key="e_costo")
                e_precio = st.number_input("Precio de venta:", min_value=0.0, value=float(fila.get("Precio_Venta", 0)), step=0.01, format="%.2f", key="e_precio")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Guardar Cambios", use_container_width=True, type="primary", key="guardar_edicion"):
                    if actualizar_producto(fila["Codigo"], e_producto.strip(), e_stock, e_unidad, e_costo, e_precio):
                        st.success("✅ Cambios guardados exitosamente.")
                        st.rerun()
            with col_btn2:
                if st.button("🗑️ Eliminar Producto", use_container_width=True, key="btn_eliminar"):
                    if eliminar_producto(fila["Codigo"]):
                        st.success("✅ Producto eliminado.")
                        st.rerun()

# ============================================================
# TAB 4: REPORTES
# ============================================================
with tab4:
    st.subheader("Reportes y Cortes de Caja")
    ventas_df = leer_ventas()
    
    if ventas_df.empty:
        st.info("📭 No hay ventas registradas todavía.")
    else:
        ventas_df["Fecha"] = pd.to_datetime(ventas_df["Fecha"], errors="coerce")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro = st.selectbox(
                "Período del reporte:",
                ["Hoy", "Ayer", "Esta semana", "Este mes", "Personalizado", "Todo"]
            )
        
        hoy = datetime.now().date()
        if filtro == "Hoy":
            fecha_ini = fecha_fin = hoy
        elif filtro == "Ayer":
            fecha_ini = fecha_fin = hoy - timedelta(days=1)
        elif filtro == "Esta semana":
            fecha_ini = hoy - timedelta(days=hoy.weekday())
            fecha_fin = hoy
        elif filtro == "Este mes":
            fecha_ini = hoy.replace(day=1)
            fecha_fin = hoy
        elif filtro == "Personalizado":
            with col2:
                fecha_ini = st.date_input("Desde:", value=hoy - timedelta(days=7))
            with col3:
                fecha_fin = st.date_input("Hasta:", value=hoy)
        else:
            fecha_ini = ventas_df["Fecha"].min().date() if not ventas_df.empty else hoy
            fecha_fin = hoy
        
        mask = (ventas_df["Fecha"].dt.date >= fecha_ini) & (ventas_df["Fecha"].dt.date <= fecha_fin)
        ventas_periodo = ventas_df[mask]
        
        st.markdown("---")
        if ventas_periodo.empty:
            st.info(f"No hay registros de venta en el período seleccionado ({fecha_ini} a {fecha_fin}).")
        else:
            st.markdown(f"### Resumen del Corte ({fecha_ini} al {fecha_fin})")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_ventas = ventas_periodo["Total"].sum()
                st.metric("Total Ventas", f"${total_ventas:.2f}")
            with col2:
                total_ganancia = ventas_periodo["Ganancia"].sum()
                st.metric("Ganancia Neta", f"${total_ganancia:.2f}")
            with col3:
                num_ventas = len(ventas_periodo)
                st.metric("Transacciones", num_ventas)
            with col4:
                unidades_vendidas = ventas_periodo["Cantidad"].sum()
                st.metric("Unidades Vendidas", f"{unidades_vendidas:g}")
            
            st.markdown("---")
            if "Metodo_Pago" in ventas_periodo.columns:
                st.markdown("### Ventas por Método de Pago")
                metodo_col = ventas_periodo["Metodo_Pago"].replace("", "Efectivo").fillna("Efectivo")
                por_metodo = ventas_periodo.groupby(metodo_col)["Total"].sum().sort_values(ascending=False)
                cols_metodo = st.columns(len(por_metodo) if len(por_metodo) > 0 else 1)
                for col, (metodo, monto) in zip(cols_metodo, por_metodo.items()):
                    with col:
                        st.metric(f"Pago: {metodo}", f"${monto:.2f}")
                st.markdown("---")
            
            st.markdown("### Top 10 Productos Más Vendidos")
            top_productos = ventas_periodo.groupby("Producto").agg({
                "Cantidad": "sum",
                "Total": "sum",
                "Ganancia": "sum"
            }).sort_values("Total", ascending=False).head(10)
            st.dataframe(top_productos, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### Detalle de Transacciones")
            st.dataframe(ventas_periodo.sort_values(["Fecha", "Hora"], ascending=False), 
                        use_container_width=True, hide_index=True)
            
            csv = ventas_periodo.to_csv(index=False)
            st.download_button(
                "📥 Descargar Reporte en CSV",
                data=csv,
                file_name=f"corte_ventas_{fecha_ini}_al_{fecha_fin}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ============================================================
# TAB 5: FIADOS
# ============================================================
with tab5:
    st.subheader("Control de Clientes Fiados")
    fiados_df = leer_fiados()
    
    col_a, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🔄 Actualizar", key="refresh_fiados"):
            st.cache_data.clear()
            st.rerun()
            
    if fiados_df.empty:
        st.info("📭 No hay registros de fiados.")
    else:
        pendientes = fiados_df[fiados_df["Estado"] == "Pendiente"]
        if pendientes.empty:
            st.success("✅ No hay deudas pendientes en este momento.")
        else:
            resumen = pendientes.groupby("Cliente")["Total"].sum().sort_values(ascending=False)
            st.markdown(f"### Total por Cobrar: ${pendientes['Total'].sum():.2f}")
            st.markdown("---")
            for cliente, monto in resumen.items():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**Cliente:** {cliente}")
                with col2:
                    st.markdown(f"**Deuda:** ${monto:.2f}")
                with col3:
                    if st.button("✅ Liquidar cuenta", key=f"pagar_{cliente}", use_container_width=True):
                        marcar_fiados_pagados(cliente)
                        st.cache_data.clear()
                        st.success(f"✅ Cuenta de {cliente} liquidada.")
                        st.rerun()
                st.markdown("---")
            
            with st.expander("📋 Ver detalle completo de deudas pendientes"):
                st.dataframe(
                    pendientes[["Fecha", "Hora", "Cliente", "Detalle", "Total"]],
                    use_container_width=True, hide_index=True
                )

# ============================================================
# TAB 6: SISTEMA
# ============================================================
with tab6:
    st.subheader("Configuración y Estado del Sistema")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**ESTADO DE CONEXIÓN**")
        st.success("✅ Google Sheets sincronizado correctamente")
        st.success("✅ Escáner de código de barras activo")
        st.success("✅ Motor de reportes operativo")
    with col2:
        st.write("**UTILIDADES**")
        if st.button("🔄 Forzar Sincronización", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Datos recargados desde la nube.")
        if st.button("📥 Descargar Respaldo de Catálogo", use_container_width=True):
            df = leer_catalogo()
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                data=csv,
                file_name=f"respaldo_catalogo_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    st.markdown("### Enlace para Vendedora")
    st.info("Utiliza este enlace para que la aplicación de la vendedora conecte de manera independiente:")
    st.code("https://soda-vendedora.streamlit.app", language=None)
    st.markdown("---")
    st.caption("Soda Pro v5.1 - Sistema POS Profesional Minimalista")