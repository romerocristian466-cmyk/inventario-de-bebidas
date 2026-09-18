"""
SODA PRO - APP ADMIN
Sistema POS completo con reportes, cortes y control total
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import random

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Soda Pro - Admin",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
# CSS Profesional
# ============================================================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stButton > button {
    width: 100%; border-radius: 15px; height: 3.5em;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white; font-weight: bold; font-size: 16px; border: none;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px;
}
.stTabs [data-baseweb="tab-list"] { gap: 12px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 12px 12px 0 0; background-color: rgba(255,255,255,0.1);
}
.stTabs [aria-selected="true"] { background-color: rgba(255,255,255,0.3) !important; }
#MainMenu, footer, header { visibility: hidden; }
h1, h2 { color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GOOGLE SHEETS
# ============================================================
SHEET_ID = "1Cq1KKnmNqMhtaDN_vsj__WofYtSUfc8jyPOUrjV9i3Y"
try:
    CREDENTIALS = dict(st.secrets["google_credentials"])
except Exception:
    st.error("⚠️ Faltan las credenciales de Google. Configúralas en Settings → Secrets de esta app en Streamlit Cloud.")
    st.stop()

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Encabezados estandarizados (SIN espacios al final para evitar bugs)
HEADERS_CATALOGO = ["Codigo", "Producto", "Stock", "Unidad de Venta", "Costo", "Precio_Venta"]
HEADERS_VENTAS = ["Fecha", "Hora", "Codigo", "Producto", "Cantidad", "Unidad de Venta", 
                  "Precio_Unit", "Costo_Unit", "Total", "Ganancia", "Metodo_Pago", "Cliente"]
HEADERS_FIADOS = ["Fecha", "Hora", "Cliente", "Detalle", "Total", "Estado"]

# ============================================================
# FUNCIONES
# ============================================================
def get_spreadsheet():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def get_catalog_ws():
    return get_spreadsheet().get_worksheet(0)

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

def get_fiados_ws():
    sh = get_spreadsheet()
    try:
        return sh.worksheet("Fiados")
    except:
        ws = sh.add_worksheet(title="Fiados", rows=500, cols=6)
        ws.append_row(HEADERS_FIADOS)
        return ws

def leer_ws_seguro(ws, headers_esperados):
    """Lee una hoja ignorando columnas duplicadas o basura extra"""
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame(columns=headers_esperados)
    
    filas = []
    num_cols = len(headers_esperados)
    for fila in data[1:]:
        # Rellena con vacíos si faltan columnas, y recorta si sobran
        fila_limpia = (fila + [""] * num_cols)[:num_cols]
        if any(str(c).strip() for c in fila_limpia):
            filas.append(fila_limpia)
            
    return pd.DataFrame(filas, columns=headers_esperados)

@st.cache_data(ttl=30)
def leer_catalogo():
    ws = get_catalog_ws()
    df = leer_ws_seguro(ws, HEADERS_CATALOGO)
    
    for col in ["Stock", "Costo", "Precio_Venta"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Codigo"] = df["Codigo"].astype(str)
    df["Unidad de Venta"] = df["Unidad de Venta"].replace("", "Unidades").fillna("Unidades")
    return df

@st.cache_data(ttl=30)
def leer_ventas():
    try:
        ws = get_ventas_ws()
        df = leer_ws_seguro(ws, HEADERS_VENTAS)
        for col in ["Cantidad", "Precio_Unit", "Costo_Unit", "Total", "Ganancia"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def leer_fiados():
    ws = get_fiados_ws()
    df = leer_ws_seguro(ws, HEADERS_FIADOS)
    if "Total" in df.columns:
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    return df

def agregar_producto(codigo, producto, stock, unidad_venta, costo, precio):
    try:
        ws = get_catalog_ws()
        nueva_fila = [
            str(codigo), str(producto),
            float(stock) if not pd.isna(float(stock)) else 0.0,
            str(unidad_venta),
            float(costo) if not pd.isna(float(costo)) else 0.0,
            float(precio) if not pd.isna(float(precio)) else 0.0
        ]
        ws.append_row(nueva_fila)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error agregando producto: {str(e)}")
        return False

def actualizar_producto(codigo_original, producto, stock, unidad_venta, costo, precio):
    try:
        ws = get_catalog_ws()
        data = ws.get_all_values()
        for idx, fila in enumerate(data[1:], start=2):
            if len(fila) > 0 and str(fila[0]).strip() == str(codigo_original):
                fila_actualizada = [
                    str(codigo_original), str(producto),
                    float(stock) if not pd.isna(float(stock)) else 0.0,
                    str(unidad_venta),
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
        data = ws.get_all_values()
        for idx, fila in enumerate(data[1:], start=2):
            if len(fila) > 0 and str(fila[0]).strip() == str(codigo):
                ws.delete_rows(idx)
                st.cache_data.clear()
                return True
        st.error(f"❌ No se encontró el producto con código {codigo}")
        return False
    except Exception as e:
        st.error(f"❌ Error eliminando: {str(e)}")
        return False

def marcar_fiados_pagados(cliente):
    ws = get_fiados_ws()
    valores = ws.get_all_values()
    if not valores: return
    header = valores[0]
    col_cliente = header.index("Cliente")
    col_estado = header.index("Estado")
    for i, row in enumerate(valores[1:], start=2):
        if len(row) > col_estado and row[col_cliente] == cliente and row[col_estado] == "Pendiente":
            ws.update_cell(i, col_estado + 1, "Pagado")

def registrar_venta(codigo, producto, cantidad, unidad_venta, precio, costo, metodo_pago="Efectivo", cliente=""):
    ws_ventas = get_ventas_ws()
    ahora = datetime.now()
    total = cantidad * precio
    ganancia = cantidad * (precio - costo)
    ws_ventas.append_row([
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"),
        str(codigo), producto, cantidad, unidad_venta,
        precio, costo, total, ganancia, metodo_pago, cliente
    ])

# ============================================================
# INTERFAZ
# ============================================================
st.title("🥤 SODA PRO - ADMIN")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📲 OPERACIONES", "📊 INVENTARIO", "📦 PRODUCTOS", "📈 REPORTES", "👥 FIADOS", "⚙️ SISTEMA"]
)

# ============================================================
# TAB 1: OPERACIONES
# ============================================================
with tab1:
    df = leer_catalogo()
    if df.empty:
        st.warning("⚠️ No hay productos. Agrega en Google Sheets.")
    else:
        tipo_operacion = st.radio("TIPO DE OPERACIÓN:", ["➕ INGRESO (Compra)", "🛒 VENTA"], horizontal=True)
        st.markdown("---")
        metodo = st.radio("MÉTODO DE SELECCIÓN:", ["📋 Seleccionar de lista", "🔍 Escanear código"], horizontal=True)
        
        producto_seleccionado = None
        if metodo == "📋 Seleccionar de lista":
            opciones = ["--- SELECCIONA ---"] + df["Producto"].tolist()
            producto_seleccionado = st.selectbox("PRODUCTO:", opciones, key="admin_dropdown")
            if producto_seleccionado == "--- SELECCIONA ---": producto_seleccionado = None
        else:
            st.info("📱 Apunta el escáner al código de barras")
            codigo_escaneado = st.text_input("Código:", placeholder="El escáner escribirá aquí...", key="admin_scanner")
            if codigo_escaneado:
                codigo_escaneado = codigo_escaneado.strip()
                if codigo_escaneado in df["Codigo"].values:
                    producto_seleccionado = df.loc[df["Codigo"] == codigo_escaneado, "Producto"].values[0]
                    st.success(f"✅ {producto_seleccionado}")
                else:
                    st.error(f"❌ Código {codigo_escaneado} no encontrado")
        
        if producto_seleccionado:
            fila = df[df["Producto"] == producto_seleccionado].iloc[0]
            codigo = fila["Codigo"]
            stock_actual = float(fila["Stock"])
            unidad_venta = fila.get("Unidad de Venta", "Unidades")
            costo = float(fila.get("Costo", 0))
            precio = float(fila.get("Precio_Venta", 0))
            
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("🔖 Código", codigo)
            with col2: st.metric(f"📦 Stock", f"{stock_actual:g} {unidad_venta}")
            with col3: st.metric("💰 Costo", f"${costo:.2f}")
            with col4: st.metric("💵 Precio", f"${precio:.2f}")
            
            st.markdown("---")
            cantidad = st.number_input(f"CANTIDAD ({unidad_venta}):", min_value=0.01, value=1.0, step=1.0, format="%.2f")
            
            if "VENTA" in tipo_operacion:
                total = cantidad * precio
                ganancia = cantidad * (precio - costo)
                col1, col2 = st.columns(2)
                with col1: st.metric("💵 Total Venta", f"${total:.2f}")
                with col2: st.metric("📈 Ganancia", f"${ganancia:.2f}")
            
            boton_disabled = False
            if "VENTA" in tipo_operacion and cantidad > stock_actual:
                st.error(f"❌ Stock insuficiente. Disponible: {stock_actual:g} {unidad_venta}")
                boton_disabled = True
            
            st.markdown("---")
            if st.button(f"{'➕ CONFIRMAR INGRESO' if 'INGRESO' in tipo_operacion else '🛒 CONFIRMAR VENTA'}", 
                         disabled=boton_disabled, use_container_width=True, type="primary"):
                ajuste = -cantidad if "VENTA" in tipo_operacion else cantidad
                nuevo_stock = stock_actual + ajuste
                
                actualizar_producto(fila["Codigo"], fila["Producto"], nuevo_stock, unidad_venta, costo, precio)
                
                if "VENTA" in tipo_operacion:
                    registrar_venta(codigo, producto_seleccionado, cantidad, unidad_venta, precio, costo)
                
                st.cache_data.clear()
                st.success(f"✅ {producto_seleccionado} actualizado!")
                st.info(f"Nuevo stock: {nuevo_stock:g} {unidad_venta}")
                st.balloons()

# ============================================================
# TAB 2: INVENTARIO
# ============================================================
with tab2:
    df = leer_catalogo()
    st.subheader("📊 ESTADO DEL INVENTARIO")
    if df.empty:
        st.info("No hay productos registrados.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Productos", len(df))
        with col2: st.metric("Unidades Totales", f"{df['Stock'].sum():g}")
        with col3: st.metric("💰 Valor Inventario", f"${(df['Stock'] * df['Costo']).sum():.2f}")
        with col4: st.metric("⚠️ Stock Bajo", len(df[df["Stock"] <= 5]))
        
        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        bajo_stock = df[df["Stock"] <= 5]
        if not bajo_stock.empty:
            st.markdown("---")
            st.warning("⚠️ PRODUCTOS CON STOCK BAJO")
            st.dataframe(bajo_stock[["Producto", "Stock", "Unidad de Venta"]], use_container_width=True, hide_index=True)

# ============================================================
# TAB 3: PRODUCTOS
# ============================================================
with tab3:
    st.subheader("📦 GESTIÓN DE PRODUCTOS")
    df_prod = leer_catalogo()
    st.markdown("---")
    
    with st.expander("➕ AGREGAR PRODUCTO NUEVO", expanded=df_prod.empty):
        st.write("**Tip:** Deja el código vacío para generar uno automático (EAN-13 válido)")
        with st.form("form_agregar_producto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo = st.text_input("Código de barras (opcional):")
                n_producto = st.text_input("Nombre del producto:")
                n_stock = st.number_input("Stock inicial:", min_value=0.0, value=0.0, step=1.0)
            with col2:
                unidades_disp = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]
                n_unidad_venta = st.selectbox("Unidad de venta:", unidades_disp)
                n_costo = st.number_input("Costo unitario:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                n_precio = st.number_input("Precio de venta:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            
            enviado = st.form_submit_button("➕ AGREGAR PRODUCTO", use_container_width=True, type="primary")
            if enviado:
                n_codigo_limpio = n_codigo.strip()
                if not n_codigo_limpio: n_codigo_limpio = generar_codigo_ean13()
                
                if not n_producto.strip():
                    st.error("❌ El nombre del producto es obligatorio")
                elif not df_prod.empty and n_codigo_limpio in df_prod["Codigo"].values:
                    st.error(f"❌ Ya existe un producto con el código {n_codigo_limpio}")
                else:
                    if agregar_producto(n_codigo_limpio, n_producto.strip(), n_stock, n_unidad_venta, n_costo, n_precio):
                        st.success(f"✅ {n_producto} agregado")
                        st.info(f"📋 **Anota este código:** `{n_codigo_limpio}`")
                        st.rerun()

    if not df_prod.empty:
        st.markdown("---")
        with st.expander("📋 VER TODOS LOS CÓDIGOS"):
            codigos_display = df_prod[["Codigo", "Producto", "Unidad de Venta"]].copy()
            codigos_display.columns = ["📌 CÓDIGO", "📦 PRODUCTO", "🔖 UNIDAD DE VENTA"]
            st.dataframe(codigos_display, use_container_width=True, hide_index=True)
            csv_codigos = codigos_display.to_csv(index=False)
            st.download_button("📥 Descargar lista (CSV)", data=csv_codigos, 
                               file_name=f"codigos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    st.markdown("---")
    if df_prod.empty:
        st.info("Agrega tu primer producto arriba.")
    else:
        with st.expander("✏️ EDITAR PRODUCTO"):
            producto_editar = st.selectbox("Selecciona producto:", df_prod["Producto"].tolist(), key="editar_select")
            idx = df_prod[df_prod["Producto"] == producto_editar].index[0]
            fila = df_prod.loc[idx]
            
            col1, col2 = st.columns(2)
            with col1:
                e_producto = st.text_input("Nombre:", value=fila["Producto"], key="e_nombre")
                e_stock = st.number_input("Stock:", min_value=0.0, value=float(fila["Stock"]), step=1.0, key="e_stock")
            with col2:
                unidades_op = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]
                unidad_actual = fila.get("Unidad de Venta", "Unidades")
                idx_unidad = unidades_op.index(unidad_actual) if unidad_actual in unidades_op else 0
                e_unidad_venta = st.selectbox("Unidad de venta:", unidades_op, index=idx_unidad, key="e_unidad")
                e_costo = st.number_input("Costo:", min_value=0.0, value=float(fila.get("Costo", 0)), step=0.01, format="%.2f", key="e_costo")
                e_precio = st.number_input("Precio:", min_value=0.0, value=float(fila.get("Precio_Venta", 0)), step=0.01, format="%.2f", key="e_precio")
            
            if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary", key="guardar_edicion"):
                if actualizar_producto(fila["Codigo"], e_producto.strip(), e_stock, e_unidad_venta, e_costo, e_precio):
                    st.success(f"✅ {e_producto} actualizado")
                    st.rerun()
                    
        with st.expander("🗑️ ELIMINAR PRODUCTO"):
            producto_eliminar = st.selectbox("Selecciona producto a eliminar:", df_prod["Producto"].tolist(), key="eliminar_select")
            confirmar = st.checkbox(f"Sí, quiero eliminar '{producto_eliminar}' permanentemente")
            if st.button("🗑️ ELIMINAR PRODUCTO", use_container_width=True, disabled=not confirmar, key="btn_eliminar"):
                codigo_eliminar = df_prod[df_prod["Producto"] == producto_eliminar]["Codigo"].values[0]
                if eliminar_producto(codigo_eliminar):
                    st.success(f"✅ {producto_eliminar} eliminado")
                    st.rerun()

# ============================================================
# TAB 4: REPORTES
# ============================================================
with tab4:
    st.subheader("📈 REPORTES Y CORTES DE VENTA")
    ventas_df = leer_ventas()
    if ventas_df.empty:
        st.info("📭 No hay ventas registradas todavía.")
    else:
        ventas_df["Fecha"] = pd.to_datetime(ventas_df["Fecha"], errors="coerce")
        st.markdown("### 📅 FILTRAR POR FECHA")
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro = st.selectbox("Período:", ["Hoy", "Ayer", "Esta semana", "Este mes", "Personalizado", "Todo"])
        
        hoy = datetime.now().date()
        if filtro == "Hoy": fecha_ini = fecha_fin = hoy
        elif filtro == "Ayer": fecha_ini = fecha_fin = hoy - timedelta(days=1)
        elif filtro == "Esta semana": fecha_ini = hoy - timedelta(days=hoy.weekday()); fecha_fin = hoy
        elif filtro == "Este mes": fecha_ini = hoy.replace(day=1); fecha_fin = hoy
        elif filtro == "Personalizado":
            with col2: fecha_ini = st.date_input("Desde:", value=hoy - timedelta(days=7))
            with col3: fecha_fin = st.date_input("Hasta:", value=hoy)
        else:
            fecha_ini = ventas_df["Fecha"].min().date() if not ventas_df.empty else hoy
            fecha_fin = hoy
            
        mask = (ventas_df["Fecha"].dt.date >= fecha_ini) & (ventas_df["Fecha"].dt.date <= fecha_fin)
        ventas_periodo = ventas_df[mask]
        st.markdown("---")
        
        if ventas_periodo.empty:
            st.info(f"No hay ventas en el período: {fecha_ini} a {fecha_fin}")
        else:
            st.markdown(f"### 💰 CORTE: {fecha_ini} a {fecha_fin}")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("💵 Total Ventas", f"${ventas_periodo['Total'].sum():.2f}")
            with col2: st.metric("📈 Ganancia", f"${ventas_periodo['Ganancia'].sum():.2f}")
            with col3: st.metric("🛒 Transacciones", len(ventas_periodo))
            with col4: st.metric("📦 Unidades Vendidas", f"{ventas_periodo['Cantidad'].sum():g}")
            
            st.markdown("---")
            if "Metodo_Pago" in ventas_periodo.columns:
                st.markdown("### 💳 CORTE POR MÉTODO DE PAGO")
                metodo_col = ventas_periodo["Metodo_Pago"].replace("", "Sin especificar").fillna("Sin especificar")
                por_metodo = ventas_periodo.groupby(metodo_col)["Total"].sum().sort_values(ascending=False)
                iconos = {"Efectivo": "💵", "Transferencia": "🏦", "Fiado": "📝", "Sin especificar": "❔"}
                cols_metodo = st.columns(len(por_metodo))
                for col, (metodo, monto) in zip(cols_metodo, por_metodo.items()):
                    with col: st.metric(f"{iconos.get(metodo, '💳')} {metodo}", f"${monto:.2f}")
            
            st.markdown("---")
            st.markdown("### 🏆 TOP PRODUCTOS MÁS VENDIDOS")
            top_productos = ventas_periodo.groupby("Producto").agg({"Cantidad": "sum", "Total": "sum", "Ganancia": "sum"}).sort_values("Total", ascending=False).head(10)
            st.dataframe(top_productos, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📋 DETALLE DE VENTAS")
            st.dataframe(ventas_periodo.sort_values(["Fecha", "Hora"], ascending=False), use_container_width=True, hide_index=True)
            csv = ventas_periodo.to_csv(index=False)
            st.download_button("📥 Descargar Reporte CSV", data=csv, file_name=f"corte_{fecha_ini}_{fecha_fin}.csv", mime="text/csv")

# ============================================================
# TAB 5: FIADOS
# ============================================================
with tab5:
    st.subheader("👥 CLIENTES FIADOS")
    fiados_df = leer_fiados()
    col1, col2 = st.columns([3, 1])
    with col1: st.caption("Aquí liquidas a un cliente cuando venga a pagar su deuda")
    with col2:
        if st.button("🔄 Actualizar", key="refresh_fiados"):
            st.cache_data.clear()
            st.rerun()
            
    if fiados_df.empty:
        st.info("📭 No hay registros de fiado todavía.")
    else:
        pendientes = fiados_df[fiados_df["Estado"] == "Pendiente"]
        if pendientes.empty:
            st.success("✅ No hay deudas pendientes. Todo al día.")
        else:
            resumen = pendientes.groupby("Cliente")["Total"].sum().sort_values(ascending=False)
            st.markdown(f"### 💰 TOTAL POR COBRAR: ${pendientes['Total'].sum():.2f}")
            st.markdown("---")
            for cliente, monto in resumen.items():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1: st.markdown(f"**👤 {cliente}**")
                with col2: st.markdown(f"### ${monto:.2f}")
                with col3:
                    if st.button("✅ Marcar pagado", key=f"pagar_{cliente}", use_container_width=True):
                        marcar_fiados_pagados(cliente)
                        st.cache_data.clear()
                        st.success(f"✅ {cliente} liquidado")
                        st.rerun()
                st.markdown("---")
                
        pagados = fiados_df[fiados_df["Estado"] == "Pagado"]
        if not pagados.empty:
            with st.expander(f"✅ Historial de fiados pagados ({len(pagados)})"):
                st.dataframe(pagados[["Fecha", "Hora", "Cliente", "Detalle", "Total"]], use_container_width=True, hide_index=True)

# ============================================================
# TAB 6: SISTEMA
# ============================================================
with tab6:
    st.subheader("⚙️ CONFIGURACIÓN DEL SISTEMA")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**ESTADO**")
        st.info("✅ Sistema operativo")
        st.info("✅ Google Sheets conectado")
        st.info("✅ Escáner listo")
    with col2:
        st.write("**ACCIONES**")
        if st.button("🔄 Sincronizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Sincronizado")
        if st.button("📥 Descargar Catálogo", use_container_width=True):
            df = leer_catalogo()
            csv = df.to_csv(index=False)
            st.download_button("📥 Descargar CSV", data=csv, file_name=f"catalogo_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
            
    st.markdown("---")
    st.markdown("### 🔗 ENLACE PARA VENDEDORA")
    st.info("Comparte este enlace con la vendedora")
    st.code("https://soda-vendedora.streamlit.app", language=None)
    st.markdown("---")
    st.caption("Soda Pro v4.1 - Sistema POS Completo")