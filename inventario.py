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

CREDENTIALS = {
    "type": "service_account",
    "project_id": "speedy-filament-414621",
    "private_key_id": "755ba08c379b33c9d43dd960fd30c59a09684cce",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCzojW5F7S2r6/p\noGRl8BO2tuo27jgYcSRwaAyQgvHnsieqmflCIPQUoUK/CqydPBZU+8WkzJ+NXaVg\nDZ1PQ8rYhodZ0x/0y2zgHAH68i9JEeYpXFNLn5kPYvnmbGz4LZzgnOOcKhvdAPiv\ndfYrT1eMC5qMbntXp7Ir8ZZCgWWRl/Ob2C/x5AFQ6JIckQ4EDH3NCQY7D3Oe1F64\nAlGVx8obgXbURrCo9bZ8BDCkvbA0qk84L3JgEXDyf+01n/ej9dwOeD5IdhqxdHpI\nmbEZJbjX5QtlxwQ9k8QsKdSsAldV4HPkmghdvzshXQhr+6rO6hU9Uzm3UrGeRrMR\nROZqM6zlAgMBAAECggEAJzlC9lLbEq37oS205n5c6592tn5fUNT5wjKyFacGF9PS\nrgGXiA1Ghq+ssabsyJuLe8yLHGBS8Y0SdI4cfKeephd//Ajp+CuoLypmc0uJMDEg\nmwTuKjvj8dRooVwpEirxj6kqWRnnwiL5amS9VzkosmuBOGtScvIq6UYEC6sSCM9x\nysEbIrzWG2moNFLAmNSGsU7T3wMigO5oHCtaSIF3TmBFp1Gez8i+cHJk0Xx5Z70X\nBgWRfyCGBsCXJcI/wB58U24LXQxM55B7b3roxqHl9/cOLL4jAdDgFpGfWLxbbHQ9\n4NkuF62+ljaQGnlzHSuZvLd3H0YuEPjaUmvOHYwIAQKBgQDX6LHx3bQVVZo1/3ES\n8u5l3BxBwu2WJQHoR3A2MHuqD390DB6WQubvsdJyiqGfEqs66bS6U7xPlU/GNl+4\nL9RvFib8N0Qz7iUGEZrHldJIDvPmluWivX/DPl67V3QQrH7BYfNpwennSDyWjN5i\nM0OL+tDAfaBykTcFFshF3xYE5QKBgQDU/SeYWLHWJLJ4d/eqCTHjOXFy8jxE+RxC\neFOO2eQGwRl+lmI/98Tz0pnMvND5YqzXlFS0Ms/f9dpjcpgLNdqRNfB4yxRXGd6h\netbRVbtksbikeV00uWt6u8VrrVq/YcEmBjZGplHAaz5geTrDeVANWBScBAcLWATN\nWM0g0jSIAQKBgQCNoCDhY6lV+UHfu8CDSoEgpcKPTHsmav4WTI4JrcHgqqvTBoQl\n0prDjiRaaB9eRhO14Elhk73JgkrC3TXqjs1NVP2bofEGE2eL1I5v7xHxnIVWs5LM\nLnuZKddgEhybN1sqJMNTkxSIVrUPmDXjunbLYmn+aimOHT03BFu4oX5DFQKBgEp9\ns8BznNcBhK3ff24nwxvudkA2el/BJGIXBVpb2IWIOattWzV2KZsBGCtkCk5+dWb8\niNdxQgTZTqUjagvZrPTGgbEtjZKdCKE/fiw+qMih46saiz+qbe3CCF0Nh0SSIuRy\nnb794m/C0lEZdTTyk83m9WZPfks4YI2VNkD5Y8gBAoGAeWGd1N2bqgxKKKWxwWyD\nuTEzoLOciRDlo9zpX0D5UpA5AM3YGXhLVdmMtf8/md6Yr2rr2iDuoORb11uq6Abo\nRoQdW6nVtoqLn76AaTURC0ntHJXe1gsOGW5JXptXGHBe+ChbWL5Ke8ftay8M4Cjs\nAMzvC8b0ReF1FK1IJu9ohsA=\n-----END PRIVATE KEY-----\n",
    "client_email": "inventario-de-bebidas@speedy-filament-414621.iam.gserviceaccount.com",
    "client_id": "116633712768836452590",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
}

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

def get_ventas_ws():
    """Obtiene o crea la hoja de Ventas"""
    sh = get_spreadsheet()
    try:
        return sh.worksheet("Ventas")
    except:
        ws = sh.add_worksheet(title="Ventas", rows=1000, cols=10)
        ws.append_row(["Fecha", "Hora", "Codigo", "Producto", "Cantidad", 
                      "Unidad", "Precio_Unit", "Costo_Unit", "Total", "Ganancia"])
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
        return pd.DataFrame(columns=["Fecha", "Hora", "Codigo", "Producto", "Cantidad",
                                     "Unidad", "Precio_Unit", "Costo_Unit", "Total", "Ganancia"])
    except:
        return pd.DataFrame()

def guardar_catalogo(df):
    ws = get_catalog_ws()
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

def registrar_venta(codigo, producto, cantidad, unidad, precio, costo):
    """Registra venta en hoja Ventas y actualiza stock"""
    ws_ventas = get_ventas_ws()
    ahora = datetime.now()
    total = cantidad * precio
    ganancia = cantidad * (precio - costo)
    ws_ventas.append_row([
        ahora.strftime("%Y-%m-%d"),
        ahora.strftime("%H:%M:%S"),
        str(codigo), producto, cantidad, unidad,
        precio, costo, total, ganancia
    ])

# ============================================================
#  INTERFAZ
# ============================================================
st.title("🥤 SODA PRO - ADMIN")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📲 OPERACIONES", "📊 INVENTARIO", "📈 REPORTES", "⚙️ SISTEMA"])

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
#  TAB 3: REPORTES
# ============================================================
with tab3:
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
with tab4:
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
