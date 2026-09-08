"""
SODA PRO - APP ADMIN
Sistema POS completo con reportes, cortes y control total
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
#  CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Soda Pro - Admin",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Profesional
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5em;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.95);
        border-radius: 12px;
        padding: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        background-color: rgba(255,255,255,0.1);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255,255,255,0.3) !important;
    }
    #MainMenu, footer, header { visibility: hidden; }
    h1, h2 { color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#  GOOGLE SHEETS
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

# ============================================================
#  FUNCIONES
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
    """Obtiene o crea la hoja de Ventas, asegurando encabezados actualizados"""
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
    """Obtiene o crea la hoja de Fiados (clientes con deuda pendiente)"""
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
        # Limpiar valores numéricos
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

def guardar_catalogo(df):
    ws = get_catalog_ws()
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

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
    """Marca como Pagado todas las filas Pendientes de un cliente"""
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
    """Registra venta en hoja Ventas y actualiza stock"""
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
#  INTERFAZ
# ============================================================
st.title("🥤 SODA PRO - ADMIN")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📲 OPERACIONES", "📊 INVENTARIO", "📦 PRODUCTOS", "📈 REPORTES", "👥 FIADOS", "⚙️ SISTEMA"]
)

# ============================================================
#  TAB 1: OPERACIONES
# ============================================================
with tab1:
    df = leer_catalogo()
    
    if df.empty:
        st.warning("⚠️ No hay productos. Agrega en Google Sheets.")
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
            opciones = ["--- SELECCIONA ---"] + df["Producto"].tolist()
            producto_seleccionado = st.selectbox("PRODUCTO:", opciones, key="admin_dropdown")
            if producto_seleccionado == "--- SELECCIONA ---":
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
                    st.success(f"✅ {producto_seleccionado}")
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
                st.metric("🔖 Código", codigo)
            with col2:
                st.metric(f"📦 Stock", f"{stock_actual:g} {unidad}")
            with col3:
                st.metric("💰 Costo", f"${costo:.2f}")
            with col4:
                st.metric("💵 Precio", f"${precio:.2f}")
            
            st.markdown("---")
            
            cantidad = st.number_input(
                f"CANTIDAD ({unidad}):",
                min_value=0.01,
                value=1.0,
                step=1.0,
                format="%.2f"
            )
            
            # Mostrar totales si es venta
            if "VENTA" in tipo_operacion:
                total = cantidad * precio
                ganancia = cantidad * (precio - costo)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💵 Total Venta", f"${total:.2f}")
                with col2:
                    st.metric("📈 Ganancia", f"${ganancia:.2f}")
            
            # Validación
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
                
                df.loc[df["Producto"] == producto_seleccionado, "Stock"] = nuevo_stock
                guardar_catalogo(df)
                
                # Registrar venta en historial
                if "VENTA" in tipo_operacion:
                    registrar_venta(codigo, producto_seleccionado, cantidad, unidad, precio, costo)
                
                st.cache_data.clear()
                st.success(f"✅ {producto_seleccionado} actualizado!")
                st.info(f"Nuevo stock: {nuevo_stock:g} {unidad}")
                st.balloons()

# ============================================================
#  TAB 2: INVENTARIO
# ============================================================
with tab2:
    df = leer_catalogo()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 ESTADO DEL INVENTARIO")
    with col2:
        if st.button("🔄 ACTUALIZAR"):
            st.cache_data.clear()
            st.rerun()
    
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
            st.metric("💰 Valor Inventario", f"${valor_inventario:.2f}")
        with col4:
            bajo_stock = df[df["Stock"] <= 5]
            st.metric("⚠️ Stock Bajo", len(bajo_stock))
        
        st.markdown("---")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if not bajo_stock.empty:
            st.markdown("---")
            st.warning("⚠️ PRODUCTOS CON STOCK BAJO")
            st.dataframe(bajo_stock[["Producto", "Stock", "Unidad"]], 
                        use_container_width=True, hide_index=True)

# ============================================================
#  TAB 3: PRODUCTOS (agregar / editar / eliminar)
# ============================================================
with tab3:
    st.subheader("📦 GESTIÓN DE PRODUCTOS")
    df_prod = leer_catalogo()

    with st.expander("➕ AGREGAR PRODUCTO NUEVO", expanded=df_prod.empty):
        with st.form("form_agregar_producto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo = st.text_input("Código de barras:")
                n_producto = st.text_input("Nombre del producto:")
                n_stock = st.number_input("Stock inicial:", min_value=0.0, value=0.0, step=1.0)
            with col2:
                n_unidad = st.selectbox("Unidad:", ["Unidades", "Libras", "Kilos", "Otro"])
                n_costo = st.number_input("Costo:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                n_precio = st.number_input("Precio de venta:", min_value=0.0, value=0.0, step=0.01, format="%.2f")

            enviado = st.form_submit_button("➕ AGREGAR PRODUCTO", use_container_width=True, type="primary")

            if enviado:
                n_codigo = n_codigo.strip()
                if not n_codigo or not n_producto.strip():
                    st.error("❌ El código y el nombre son obligatorios")
                elif not df_prod.empty and n_codigo in df_prod["Codigo"].values:
                    st.error(f"❌ Ya existe un producto con el código {n_codigo}")
                else:
                    nueva_fila = pd.DataFrame([{
                        "Codigo": n_codigo, "Producto": n_producto.strip(), "Stock": n_stock,
                        "Unidad": n_unidad, "Costo": n_costo, "Precio_Venta": n_precio
                    }])
                    df_actualizado = pd.concat([df_prod, nueva_fila], ignore_index=True)
                    guardar_catalogo(df_actualizado)
                    st.cache_data.clear()
                    st.success(f"✅ {n_producto} agregado al catálogo")
                    st.rerun()

    st.markdown("---")

    if df_prod.empty:
        st.info("Agrega tu primer producto arriba para poder editarlo o eliminarlo.")
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
                unidades_op = ["Unidades", "Libras", "Kilos", "Otro"]
                unidad_actual = fila.get("Unidad", "Unidades")
                idx_unidad = unidades_op.index(unidad_actual) if unidad_actual in unidades_op else 0
                e_unidad = st.selectbox("Unidad:", unidades_op, index=idx_unidad, key="e_unidad")
                e_costo = st.number_input("Costo:", min_value=0.0, value=float(fila.get("Costo", 0)),
                                          step=0.01, format="%.2f", key="e_costo")
                e_precio = st.number_input("Precio de venta:", min_value=0.0, value=float(fila.get("Precio_Venta", 0)),
                                           step=0.01, format="%.2f", key="e_precio")

            if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary", key="guardar_edicion"):
                df_prod.at[idx, "Producto"] = e_producto.strip()
                df_prod.at[idx, "Stock"] = e_stock
                df_prod.at[idx, "Unidad"] = e_unidad
                df_prod.at[idx, "Costo"] = e_costo
                df_prod.at[idx, "Precio_Venta"] = e_precio
                guardar_catalogo(df_prod)
                st.cache_data.clear()
                st.success(f"✅ {e_producto} actualizado")
                st.rerun()

        with st.expander("🗑️ ELIMINAR PRODUCTO"):
            producto_eliminar = st.selectbox("Selecciona producto a eliminar:", df_prod["Producto"].tolist(), key="eliminar_select")
            confirmar = st.checkbox(f"Sí, quiero eliminar '{producto_eliminar}' permanentemente")
            if st.button("🗑️ ELIMINAR PRODUCTO", use_container_width=True, disabled=not confirmar, key="btn_eliminar"):
                df_actualizado = df_prod[df_prod["Producto"] != producto_eliminar]
                guardar_catalogo(df_actualizado)
                st.cache_data.clear()
                st.success(f"✅ {producto_eliminar} eliminado del catálogo")
                st.rerun()

# ============================================================
#  TAB 4: REPORTES
# ============================================================
with tab4:
    st.subheader("📈 REPORTES Y CORTES DE VENTA")
    
    ventas_df = leer_ventas()
    
    if ventas_df.empty:
        st.info("📭 No hay ventas registradas todavía.")
    else:
        # Convertir fecha
        ventas_df["Fecha"] = pd.to_datetime(ventas_df["Fecha"], errors="coerce")
        
        # Filtros
        st.markdown("### 📅 FILTRAR POR FECHA")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro = st.selectbox(
                "Período:",
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
        
        # Filtrar
        mask = (ventas_df["Fecha"].dt.date >= fecha_ini) & (ventas_df["Fecha"].dt.date <= fecha_fin)
        ventas_periodo = ventas_df[mask]
        
        st.markdown("---")
        
        if ventas_periodo.empty:
            st.info(f"No hay ventas en el período: {fecha_ini} a {fecha_fin}")
        else:
            # Métricas
            st.markdown(f"### 💰 CORTE: {fecha_ini} a {fecha_fin}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_ventas = ventas_periodo["Total"].sum()
                st.metric("💵 Total Ventas", f"${total_ventas:.2f}")
            with col2:
                total_ganancia = ventas_periodo["Ganancia"].sum()
                st.metric("📈 Ganancia", f"${total_ganancia:.2f}")
            with col3:
                num_ventas = len(ventas_periodo)
                st.metric("🛒 Transacciones", num_ventas)
            with col4:
                unidades_vendidas = ventas_periodo["Cantidad"].sum()
                st.metric("📦 Unidades Vendidas", f"{unidades_vendidas:g}")
            
            st.markdown("---")

            # Corte por método de pago
            if "Metodo_Pago" in ventas_periodo.columns:
                st.markdown("### 💳 CORTE POR MÉTODO DE PAGO")
                metodo_col = ventas_periodo["Metodo_Pago"].replace("", "Sin especificar").fillna("Sin especificar")
                por_metodo = ventas_periodo.groupby(metodo_col)["Total"].sum().sort_values(ascending=False)
                iconos = {"Efectivo": "💵", "Transferencia": "🏦", "Fiado": "📝", "Sin especificar": "❔"}
                cols_metodo = st.columns(len(por_metodo))
                for col, (metodo, monto) in zip(cols_metodo, por_metodo.items()):
                    with col:
                        st.metric(f"{iconos.get(metodo, '💳')} {metodo}", f"${monto:.2f}")
                st.markdown("---")

            # Top productos
            st.markdown("### 🏆 TOP PRODUCTOS MÁS VENDIDOS")
            top_productos = ventas_periodo.groupby("Producto").agg({
                "Cantidad": "sum",
                "Total": "sum",
                "Ganancia": "sum"
            }).sort_values("Total", ascending=False).head(10)
            st.dataframe(top_productos, use_container_width=True)
            
            st.markdown("---")
            
            # Detalle de ventas
            st.markdown("### 📋 DETALLE DE VENTAS")
            st.dataframe(ventas_periodo.sort_values(["Fecha", "Hora"], ascending=False), 
                        use_container_width=True, hide_index=True)
            
            # Descargar
            csv = ventas_periodo.to_csv(index=False)
            st.download_button(
                "📥 Descargar Reporte CSV",
                data=csv,
                file_name=f"corte_{fecha_ini}_{fecha_fin}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ============================================================
#  TAB 4: SISTEMA
# ============================================================
with tab5:
    st.subheader("👥 CLIENTES FIADOS")

    fiados_df = leer_fiados()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Aquí liquidas a un cliente cuando venga a pagar su deuda")
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
                with col1:
                    st.markdown(f"**👤 {cliente}**")
                with col2:
                    st.markdown(f"### ${monto:.2f}")
                with col3:
                    if st.button("✅ Marcar pagado", key=f"pagar_{cliente}", use_container_width=True):
                        marcar_fiados_pagados(cliente)
                        st.cache_data.clear()
                        st.success(f"✅ {cliente} liquidado")
                        st.rerun()
                st.markdown("---")

            with st.expander("📋 Ver detalle de deudas pendientes"):
                st.dataframe(
                    pendientes[["Fecha", "Hora", "Cliente", "Detalle", "Total"]],
                    use_container_width=True, hide_index=True
                )

        pagados = fiados_df[fiados_df["Estado"] == "Pagado"]
        if not pagados.empty:
            with st.expander(f"✅ Historial de fiados pagados ({len(pagados)})"):
                st.dataframe(
                    pagados[["Fecha", "Hora", "Cliente", "Detalle", "Total"]],
                    use_container_width=True, hide_index=True
                )

with tab6:
    st.subheader("⚙️ CONFIGURACIÓN DEL SISTEMA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**ESTADO**")
        st.info("✅ Sistema operativo")
        st.info("✅ Google Sheets conectado")
        st.info("✅ Escáner listo")
        st.info("✅ Registro de ventas activo")
    
    with col2:
        st.write("**ACCIONES**")
        if st.button("🔄 Sincronizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Sincronizado")
        
        if st.button("📥 Descargar Catálogo", use_container_width=True):
            df = leer_catalogo()
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                data=csv,
                file_name=f"catalogo_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    st.markdown("### 🔗 ENLACE PARA VENDEDORA")
    st.info("Comparte este enlace con la vendedora (solo puede vender, no ver reportes)")
    st.code("https://soda-vendedora.streamlit.app", language=None)
    
    st.markdown("---")
    st.caption("Soda Pro v4.0 - Sistema POS Completo")
