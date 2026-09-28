"""
SODA PRO - APP ADMIN v5
Sistema POS completo con reportes, cortes, categorías y control de caja
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import random

# ============================================================
#  CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Soda Pro - Admin",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
#  GENERADOR DE CÓDIGOS EAN-13
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

HEADERS_VENTAS = ["Fecha", "Hora", "Codigo", "Producto", "Cantidad", "Unidad",
                  "Precio_Unit", "Costo_Unit", "Total", "Ganancia", "Metodo_Pago", "Cliente", "Categoria"]
HEADERS_FIADOS = ["Fecha", "Hora", "Cliente", "Detalle", "Total", "Estado"]
HEADERS_CAJA   = ["Fecha", "Hora", "Tipo", "Efectivo_Inicial", "Metodo", "Monto", "Descripcion", "Categoria"]

# ============================================================
#  FUNCIONES DE GOOGLE SHEETS
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
        encabezados = ws.row_values(1)
        if "Categoria" not in encabezados:
            ws.update('A1', [HEADERS_VENTAS])
        return ws
    except Exception:
        ws = sh.add_worksheet(title="Ventas", rows=1000, cols=13)
        ws.append_row(HEADERS_VENTAS)
        return ws

def get_fiados_ws():
    sh = get_spreadsheet()
    try:
        return sh.worksheet("Fiados")
    except Exception:
        ws = sh.add_worksheet(title="Fiados", rows=500, cols=6)
        ws.append_row(HEADERS_FIADOS)
        return ws

def get_caja_ws():
    sh = get_spreadsheet()
    try:
        return sh.worksheet("Caja")
    except Exception:
        ws = sh.add_worksheet(title="Caja", rows=2000, cols=8)
        ws.append_row(HEADERS_CAJA)
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
        if "Categoria" not in df.columns:
            df["Categoria"] = "Bebidas"
        return df
    return pd.DataFrame(columns=["Codigo", "Producto", "Stock", "Unidad", "Costo", "Precio_Venta", "Categoria"])

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
    except Exception:
        return pd.DataFrame()

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

@st.cache_data(ttl=30)
def leer_caja():
    try:
        ws = get_caja_ws()
        registros = ws.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            if "Monto" in df.columns:
                df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            if "Efectivo_Inicial" in df.columns:
                df["Efectivo_Inicial"] = pd.to_numeric(df["Efectivo_Inicial"], errors="coerce").fillna(0)
            return df
        return pd.DataFrame(columns=HEADERS_CAJA)
    except Exception:
        return pd.DataFrame(columns=HEADERS_CAJA)

def agregar_producto(codigo, producto, stock, unidad, costo, precio, categoria):
    """Agrega UNA fila nueva sin tocar las demás. 100% seguro."""
    try:
        ws = get_catalog_ws()
        nueva_fila = [
            str(codigo), str(producto),
            float(stock) if not pd.isna(float(stock)) else 0.0,
            str(unidad),
            float(costo) if not pd.isna(float(costo)) else 0.0,
            float(precio) if not pd.isna(float(precio)) else 0.0,
            str(categoria)
        ]
        ws.append_row(nueva_fila)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error agregando producto: {str(e)}")
        return False

def actualizar_producto(codigo_original, producto, stock, unidad, costo, precio, categoria):
    """Actualiza UNA fila específica sin tocar las demás. 100% seguro."""
    try:
        ws = get_catalog_ws()
        registros = ws.get_all_records()
        for idx, reg in enumerate(registros, start=2):
            if str(reg.get("Codigo", "")) == str(codigo_original):
                fila_actualizada = [
                    str(codigo_original), str(producto),
                    float(stock) if not pd.isna(float(stock)) else 0.0,
                    str(unidad),
                    float(costo) if not pd.isna(float(costo)) else 0.0,
                    float(precio) if not pd.isna(float(precio)) else 0.0,
                    str(categoria)
                ]
                # Detectar cuántas columnas tiene la hoja
                n_cols = len(ws.row_values(1))
                col_fin = chr(ord('A') + len(fila_actualizada) - 1)
                ws.update(f"A{idx}:{col_fin}{idx}", [fila_actualizada])
                st.cache_data.clear()
                return True
        st.error(f"❌ No se encontró el producto con código {codigo_original}")
        return False
    except Exception as e:
        st.error(f"❌ Error actualizando: {str(e)}")
        return False

def eliminar_producto(codigo):
    """Elimina UNA fila específica. 100% seguro."""
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

def actualizar_stock_producto(codigo, nuevo_stock):
    """Actualiza solo el stock de un producto (columna C)."""
    try:
        ws = get_catalog_ws()
        registros = ws.get_all_records()
        for idx, reg in enumerate(registros, start=2):
            if str(reg.get("Codigo", "")) == str(codigo):
                ws.update_cell(idx, 3, float(nuevo_stock))
                st.cache_data.clear()
                return True
        return False
    except Exception as e:
        st.error(f"❌ Error actualizando stock: {str(e)}")
        return False

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

def registrar_venta(codigo, producto, cantidad, unidad, precio, costo, metodo_pago="Efectivo", cliente="", categoria=""):
    ws_ventas = get_ventas_ws()
    ahora = datetime.now()
    total = cantidad * precio
    ganancia = cantidad * (precio - costo)
    ws_ventas.append_row([
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"),
        str(codigo), producto, cantidad, unidad,
        precio, costo, total, ganancia, metodo_pago, cliente, categoria
    ])

# ============================================================
#  INTERFAZ
# ============================================================
st.title("🥤 SODA PRO - ADMIN")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["📲 OPERACIONES", "📊 INVENTARIO", "📦 PRODUCTOS", "📈 REPORTES", "👥 FIADOS", "📦 CAJA VENDEDORA", "⚙️ SISTEMA"]
)

# ============================================================
#  TAB 1: OPERACIONES
# ============================================================
with tab1:
    df = leer_catalogo()

    if df.empty:
        st.warning("⚠️ No hay productos. Agrega en la pestaña PRODUCTOS.")
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
            categoria = fila.get("Categoria", "")

            st.markdown("---")

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("🔖 Código", codigo)
            with col2:
                st.metric(f"📦 Stock", f"{stock_actual:g} {unidad}")
            with col3:
                st.metric("💰 Costo", f"${costo:.2f}")
            with col4:
                st.metric("💵 Precio", f"${precio:.2f}")
            with col5:
                st.metric("🏷️ Categoría", categoria)

            st.markdown("---")

            cantidad = st.number_input(
                f"CANTIDAD ({unidad}):",
                min_value=0.01, value=1.0, step=1.0, format="%.2f"
            )

            if "VENTA" in tipo_operacion:
                total = cantidad * precio
                ganancia = cantidad * (precio - costo)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💵 Total Venta", f"${total:.2f}")
                with col2:
                    st.metric("📈 Ganancia", f"${ganancia:.2f}")

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

                fila_prod = df[df["Producto"] == producto_seleccionado].iloc[0]
                actualizar_producto(
                    fila_prod["Codigo"], fila_prod["Producto"], nuevo_stock,
                    fila_prod.get("Unidad", "Unidades"),
                    float(fila_prod.get("Costo", 0)),
                    float(fila_prod.get("Precio_Venta", 0)),
                    fila_prod.get("Categoria", "")
                )

                if "VENTA" in tipo_operacion:
                    registrar_venta(codigo, producto_seleccionado, cantidad, unidad,
                                    precio, costo, categoria=categoria)

                st.cache_data.clear()
                st.success(f"✅ {producto_seleccionado} actualizado!")
                st.info(f"Nuevo stock: {nuevo_stock:g} {unidad}")
                st.balloons()

# ============================================================
#  TAB 2: INVENTARIO
# ============================================================
with tab2:
    df = leer_catalogo()

    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.subheader("📊 ESTADO DEL INVENTARIO")
    with col_h2:
        if st.button("🔄 Actualizar", key="refresh_inv"):
            st.cache_data.clear()
            st.rerun()

    if df.empty:
        st.info("No hay productos registrados.")
    else:
        # Filtro por categoría
        categorias_disponibles = ["Todas"] + sorted(df["Categoria"].dropna().unique().tolist())
        filtro_cat = st.selectbox("🏷️ Filtrar por categoría:", categorias_disponibles, key="filtro_inv_cat")

        df_filtrado = df if filtro_cat == "Todas" else df[df["Categoria"] == filtro_cat]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Productos", len(df_filtrado))
        with col2:
            st.metric("Unidades Totales", f"{df_filtrado['Stock'].sum():g}")
        with col3:
            valor_inventario = (df_filtrado["Stock"] * df_filtrado["Costo"]).sum()
            st.metric("💰 Valor Inventario", f"${valor_inventario:.2f}")
        with col4:
            bajo_stock = df_filtrado[df_filtrado["Stock"] <= 5]
            st.metric("⚠️ Stock Bajo", len(bajo_stock))

        st.markdown("---")

        # Tabla por categoría
        if filtro_cat == "Todas":
            for cat in sorted(df["Categoria"].dropna().unique().tolist()):
                df_cat = df[df["Categoria"] == cat]
                emoji = "🥤" if cat.lower() == "bebidas" else "👜"
                st.markdown(f"#### {emoji} {cat}")
                st.dataframe(
                    df_cat[["Codigo", "Producto", "Stock", "Unidad", "Costo", "Precio_Venta"]],
                    use_container_width=True, hide_index=True
                )
                st.markdown("---")
        else:
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        if not bajo_stock.empty:
            st.warning("⚠️ PRODUCTOS CON STOCK BAJO (≤ 5)")
            st.dataframe(bajo_stock[["Producto", "Stock", "Unidad", "Categoria"]],
                         use_container_width=True, hide_index=True)

# ============================================================
#  TAB 3: PRODUCTOS (agregar / editar / eliminar)
# ============================================================
with tab3:
    st.subheader("📦 GESTIÓN DE PRODUCTOS")
    df_prod = leer_catalogo()

    CATEGORIAS = ["Bebidas", "Accesorios"]
    UNIDADES   = ["Unidades", "Media Libra", "Libra", "Kilo", "Saco", "Docena", "Bolsa", "Otro"]

    st.markdown("---")

    with st.expander("➕ AGREGAR PRODUCTO NUEVO", expanded=df_prod.empty):
        st.write("**Tip:** Deja el código vacío para generar uno automático (EAN-13 válido, escaneable)")

        with st.form("form_agregar_producto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo   = st.text_input("Código de barras (opcional):")
                n_producto = st.text_input("Nombre del producto:")
                n_stock    = st.number_input("Stock inicial:", min_value=0.0, value=0.0, step=1.0)
                n_categoria = st.selectbox("Categoría:", CATEGORIAS, key="n_cat")
            with col2:
                n_unidad   = st.selectbox("Unidad de medida:", UNIDADES)
                n_costo    = st.number_input("Costo unitario:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                n_precio   = st.number_input("Precio de venta unitario:", min_value=0.0, value=0.0, step=0.01, format="%.2f")

            enviado = st.form_submit_button("➕ AGREGAR PRODUCTO", use_container_width=True, type="primary")

            if enviado:
                n_codigo_limpio = n_codigo.strip()
                if not n_codigo_limpio:
                    n_codigo_limpio = generar_codigo_ean13()

                if not n_producto.strip():
                    st.error("❌ El nombre del producto es obligatorio")
                elif not df_prod.empty and n_codigo_limpio in df_prod["Codigo"].values:
                    st.error(f"❌ Ya existe un producto con el código {n_codigo_limpio}")
                else:
                    if agregar_producto(n_codigo_limpio, n_producto.strip(), n_stock, n_unidad, n_costo, n_precio, n_categoria):
                        st.success(f"✅ {n_producto} agregado como {n_categoria}")
                        st.info(f"📋 **Anota este código:** `{n_codigo_limpio}`")
                        st.rerun()

    if not df_prod.empty:
        st.markdown("---")
        with st.expander("📋 VER TODOS LOS CÓDIGOS"):
            st.write("**Copia estos códigos a tu libreta — la vendedora los escaneará con la pistola:**")
            codigos_display = df_prod[["Codigo", "Producto", "Unidad", "Categoria"]].copy()
            codigos_display.columns = ["📌 CÓDIGO", "📦 PRODUCTO", "🔖 UNIDAD", "🏷️ CATEGORÍA"]
            st.dataframe(codigos_display, use_container_width=True, hide_index=True)
            csv_codigos = codigos_display.to_csv(index=False)
            st.download_button(
                "📥 Descargar lista (CSV)", data=csv_codigos,
                file_name=f"codigos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True
            )

    st.markdown("---")

    if not df_prod.empty:
        with st.expander("✏️ EDITAR PRODUCTO"):
            producto_editar = st.selectbox("Selecciona producto:", df_prod["Producto"].tolist(), key="editar_select")
            idx = df_prod[df_prod["Producto"] == producto_editar].index[0]
            fila = df_prod.loc[idx]

            col1, col2 = st.columns(2)
            with col1:
                e_producto = st.text_input("Nombre:", value=fila["Producto"], key="e_nombre")
                e_stock    = st.number_input("Stock:", min_value=0.0, value=float(fila["Stock"]), step=1.0, key="e_stock")
                cat_actual  = fila.get("Categoria", "Bebidas")
                idx_cat     = CATEGORIAS.index(cat_actual) if cat_actual in CATEGORIAS else 0
                e_categoria = st.selectbox("Categoría:", CATEGORIAS, index=idx_cat, key="e_cat")
            with col2:
                unidad_actual = fila.get("Unidad", "Unidades")
                idx_unidad    = UNIDADES.index(unidad_actual) if unidad_actual in UNIDADES else 0
                e_unidad  = st.selectbox("Unidad:", UNIDADES, index=idx_unidad, key="e_unidad")
                e_costo   = st.number_input("Costo:", min_value=0.0, value=float(fila.get("Costo", 0)),
                                             step=0.01, format="%.2f", key="e_costo")
                e_precio  = st.number_input("Precio venta:", min_value=0.0, value=float(fila.get("Precio_Venta", 0)),
                                             step=0.01, format="%.2f", key="e_precio")

            if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary", key="guardar_edicion"):
                if actualizar_producto(fila["Codigo"], e_producto.strip(), e_stock,
                                       e_unidad, e_costo, e_precio, e_categoria):
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
#  TAB 4: REPORTES
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
            filtro = st.selectbox(
                "Período:", ["Hoy", "Ayer", "Esta semana", "Este mes", "Personalizado", "Todo"]
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
            fecha_ini = ventas_df["Fecha"].min().date() if not ventas_df["Fecha"].isna().all() else hoy
            fecha_fin = hoy

        # Filtro categoría
        categorias_rep = ["Todas", "Bebidas", "Accesorios"]
        filtro_cat_rep = st.selectbox("🏷️ Categoría:", categorias_rep, key="rep_cat")

        mask = (ventas_df["Fecha"].dt.date >= fecha_ini) & (ventas_df["Fecha"].dt.date <= fecha_fin)
        ventas_periodo = ventas_df[mask]

        if filtro_cat_rep != "Todas" and "Categoria" in ventas_periodo.columns:
            ventas_periodo = ventas_periodo[ventas_periodo["Categoria"] == filtro_cat_rep]

        st.markdown("---")

        if ventas_periodo.empty:
            st.info(f"No hay ventas en el período seleccionado.")
        else:
            st.markdown(f"### 💰 CORTE: {fecha_ini} a {fecha_fin}")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💵 Total Ventas", f"${ventas_periodo['Total'].sum():.2f}")
            with col2:
                st.metric("📈 Ganancia", f"${ventas_periodo['Ganancia'].sum():.2f}")
            with col3:
                st.metric("🛒 Transacciones", len(ventas_periodo))
            with col4:
                st.metric("📦 Unidades", f"{ventas_periodo['Cantidad'].sum():g}")

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

            # Corte por categoría (solo si se muestra "Todas")
            if filtro_cat_rep == "Todas" and "Categoria" in ventas_periodo.columns:
                st.markdown("### 🏷️ CORTE POR CATEGORÍA")
                por_cat = ventas_periodo.groupby("Categoria")["Total"].sum().sort_values(ascending=False)
                cols_cat = st.columns(max(len(por_cat), 1))
                for col, (cat, monto) in zip(cols_cat, por_cat.items()):
                    with col:
                        emoji = "🥤" if cat.lower() == "bebidas" else "👜"
                        st.metric(f"{emoji} {cat}", f"${monto:.2f}")
                st.markdown("---")

            # Top productos
            st.markdown("### 🏆 TOP PRODUCTOS MÁS VENDIDOS")
            top_productos = ventas_periodo.groupby("Producto").agg({
                "Cantidad": "sum", "Total": "sum", "Ganancia": "sum"
            }).sort_values("Total", ascending=False).head(10)
            st.dataframe(top_productos, use_container_width=True)

            st.markdown("---")

            st.markdown("### 📋 DETALLE DE VENTAS")
            cols_mostrar = [c for c in ["Fecha", "Hora", "Producto", "Cantidad", "Unidad",
                                         "Precio_Unit", "Total", "Metodo_Pago", "Cliente", "Categoria"]
                            if c in ventas_periodo.columns]
            st.dataframe(ventas_periodo[cols_mostrar].sort_values(["Fecha", "Hora"], ascending=False),
                         use_container_width=True, hide_index=True)

            csv = ventas_periodo.to_csv(index=False)
            st.download_button(
                "📥 Descargar Reporte CSV", data=csv,
                file_name=f"corte_{fecha_ini}_{fecha_fin}.csv",
                mime="text/csv", use_container_width=True
            )

# ============================================================
#  TAB 5: FIADOS
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
            with st.expander(f"✅ Historial pagados ({len(pagados)})"):
                st.dataframe(
                    pagados[["Fecha", "Hora", "Cliente", "Detalle", "Total"]],
                    use_container_width=True, hide_index=True
                )

# ============================================================
#  TAB 6: CAJA VENDEDORA (vista en tiempo real)
# ============================================================
with tab6:
    st.subheader("📦 ESTADO DE CAJA DE VENDEDORA")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualizar", key="refresh_caja_admin"):
            st.cache_data.clear()
            st.rerun()

    df_caja   = leer_caja()
    df_ventas = leer_ventas()
    hoy_str   = datetime.now().strftime("%Y-%m-%d")

    fecha_caja = st.date_input("📅 Ver fecha:", value=datetime.now().date(), key="admin_caja_fecha")
    fecha_caja_str = fecha_caja.strftime("%Y-%m-%d")

    st.markdown("---")

    # Aperturas del día
    if not df_caja.empty and "Fecha" in df_caja.columns and "Tipo" in df_caja.columns:
        aperturas = df_caja[(df_caja["Fecha"] == fecha_caja_str) & (df_caja["Tipo"] == "APERTURA")]
        cierres   = df_caja[(df_caja["Fecha"] == fecha_caja_str) & (df_caja["Tipo"] == "CIERRE")]

        if not aperturas.empty:
            st.markdown("### 🔓 Aperturas de caja")
            for _, ap in aperturas.iterrows():
                cat = ap.get("Categoria", "")
                emoji = "🥤" if str(cat).lower() == "bebidas" else "👜"
                ef_ini = float(ap.get("Efectivo_Inicial", 0))
                st.info(f"{emoji} **{cat}** — Apertura a las {ap.get('Hora', '')} | Efectivo inicial: ${ef_ini:.2f}")
        else:
            st.warning("⚠️ Aún no se ha abierto la caja hoy")

        if not cierres.empty:
            st.markdown("### 🔒 Cierres de caja")
            for _, ci in cierres.iterrows():
                cat = ci.get("Categoria", "")
                emoji = "🥤" if str(cat).lower() == "bebidas" else "👜"
                st.success(f"{emoji} **{cat}** — Cierre a las {ci.get('Hora', '')} | Total: ${float(ci.get('Monto', 0)):.2f}")

    st.markdown("---")

    # Ventas del día por categoría y método
    if not df_ventas.empty and "Fecha" in df_ventas.columns:
        ventas_hoy = df_ventas[df_ventas["Fecha"] == fecha_caja_str]
    else:
        ventas_hoy = pd.DataFrame()

    for cat_nombre, emoji in [("Bebidas", "🥤"), ("Accesorios", "👜")]:
        st.markdown(f"### {emoji} {cat_nombre}")

        if ventas_hoy.empty or "Categoria" not in ventas_hoy.columns:
            st.caption("Sin ventas registradas")
        else:
            v_cat = ventas_hoy[ventas_hoy["Categoria"] == cat_nombre]
            if v_cat.empty:
                st.caption("Sin ventas")
            else:
                por_metodo = v_cat.groupby("Metodo_Pago")["Total"].sum()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("💵 Efectivo", f"${por_metodo.get('Efectivo', 0):.2f}")
                with c2:
                    st.metric("🏦 Transf.", f"${por_metodo.get('Transferencia', 0):.2f}")
                with c3:
                    st.metric("📝 Fiado", f"${por_metodo.get('Fiado', 0):.2f}")
                with c4:
                    st.metric("💰 TOTAL", f"${v_cat['Total'].sum():.2f}")

                with st.expander(f"Ver detalle {cat_nombre}"):
                    cols_d = [c for c in ["Hora", "Producto", "Cantidad", "Total", "Metodo_Pago", "Cliente"]
                              if c in v_cat.columns]
                    st.dataframe(v_cat[cols_d].sort_values("Hora", ascending=False),
                                 use_container_width=True, hide_index=True)

        st.markdown("---")

    # Inventario actual (solo lectura — admin ve, pero podría tomar nota del conteo físico)
    st.markdown("### 📦 INVENTARIO ACTUAL (conteo)")
    df_inv = leer_catalogo()
    if not df_inv.empty:
        df_inv_display = df_inv[["Producto", "Stock", "Unidad", "Categoria"]].copy()
        df_inv_display.columns = ["Producto", "Stock Actual", "Unidad", "Categoría"]
        st.dataframe(df_inv_display, use_container_width=True, hide_index=True)
        st.caption("ℹ️ La vendedora puede ver este inventario pero no modificarlo.")

# ============================================================
#  TAB 7: SISTEMA
# ============================================================
with tab7:
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
                "📥 Descargar CSV", data=csv,
                file_name=f"catalogo_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True
            )

    st.markdown("---")
    st.markdown("### 🔗 CONFIGURACIÓN DE HOJAS GOOGLE SHEETS")
    st.info("""
    **Columnas necesarias en la hoja del catálogo (Hoja 1):**

    | Columna | Descripción |
    |---------|-------------|
    | Codigo | EAN-13 del producto |
    | Producto | Nombre |
    | Stock | Cantidad disponible |
    | Unidad | Unidades / Libra / etc. |
    | Costo | Precio de compra |
    | Precio_Venta | Precio de venta |
    | Categoria | **Bebidas** o **Accesorios** |

    ⚠️ La columna **Categoria** debe existir para que funcione la separación por pestañas.
    """)

    st.markdown("---")
    st.markdown("### 🔗 ENLACE PARA VENDEDORA")
    st.info("Comparte este enlace con la vendedora")
    st.code("https://soda-vendedora.streamlit.app", language=None)

    st.markdown("---")
    st.caption("Soda Pro v5.0 - Sistema POS Completo con Caja y Categorías")
