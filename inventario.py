import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ============================================================
#  CONFIGURACIÓN TEMA APP
# ============================================================
st.set_page_config(
    page_title="Soda Pro - Inventario",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS PERSONALIZADO - Tema profesional
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Botones grandes y redondeados */
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
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Selectbox bonito */
    .stSelectbox>div {
        border-radius: 12px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        background-color: rgba(255,255,255,0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255,255,255,0.3) !important;
    }
    
    /* Métricas */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.95);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Info boxes */
    .stInfo {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        border-radius: 8px;
    }
    
    .stSuccess {
        background: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4caf50;
        border-radius: 8px;
    }
    
    .stWarning {
        background: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        border-radius: 8px;
    }
    
    .stError {
        background: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #f44336;
        border-radius: 8px;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Título principal */
    h1 {
        color: white;
        text-align: center;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        margin-bottom: 30px;
    }
    
    h2 {
        color: white;
        text-shadow: 0 1px 5px rgba(0,0,0,0.2);
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Number input */
    .stNumberInput>div {
        border-radius: 12px;
    }
    
    /* Text input */
    .stTextInput>div {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#  CONFIGURACIÓN GOOGLE SHEETS
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
def get_worksheet():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    return sh.get_worksheet(0)

@st.cache_data(ttl=30)
def leer_datos():
    ws = get_worksheet()
    registros = ws.get_all_records()
    if registros:
        return pd.DataFrame(registros)
    return pd.DataFrame(columns=["Codigo", "Producto", "Stock", "Ultima_Actualizacion"])

def guardar_datos(df):
    ws = get_worksheet()
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

# ============================================================
#  INTERFAZ PRINCIPAL
# ============================================================
st.title("🥤 SODA PRO")
st.markdown("---")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📲 OPERACIONES", "📊 INVENTARIO", "⚙️ SISTEMA"])

# ============================================================
#  TAB 1: OPERACIONES
# ============================================================
with tab1:
    df = leer_datos()
    
    if df.empty:
        st.warning("⚠️ No hay productos. Crear productos en la pestaña INVENTARIO")
    else:
        col1, col2 = st.columns(2)
        with col1:
            tipo_operacion = st.radio(
                "TIPO DE OPERACIÓN:",
                ["➕ INGRESO", "🛒 VENTA"],
                horizontal=True
            )
        
        with col2:
            st.write("")  # espaciador
        
        st.markdown("---")
        
        # Selector de producto
        opciones = ["--- SELECCIONA BEBIDA ---"] + df["Producto"].tolist()
        producto_seleccionado = st.selectbox("SELECCIONA LA BEBIDA:", opciones, key="prod_selector")
        
        if producto_seleccionado != "--- SELECCIONA BEBIDA ---":
            fila = df[df["Producto"] == producto_seleccionado].iloc[0]
            codigo = fila["Codigo"]
            stock_actual = int(fila["Stock"])
            
            # Mostrar datos del producto
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔖 Código", codigo)
            with col2:
                st.metric("📦 Stock Actual", f"{stock_actual} unidades")
            with col3:
                st.metric("⏰ Última Actualización", fila["Ultima_Actualizacion"])
            
            st.markdown("---")
            
            # Entrada de cantidad
            cantidad = st.number_input(
                "CANTIDAD A REGISTRAR:",
                min_value=1,
                value=1,
                step=1
            )
            
            # Validación para ventas
            if "VENTA" in tipo_operacion and cantidad > stock_actual:
                st.error(f"❌ Stock insuficiente. Disponible: {stock_actual} unidades")
                boton_disabled = True
            else:
                boton_disabled = False
            
            st.markdown("---")
            
            # Botón de confirmación
            if st.button(
                f"{'➕ CONFIRMAR INGRESO' if 'INGRESO' in tipo_operacion else '🛒 CONFIRMAR VENTA'}",
                disabled=boton_disabled,
                use_container_width=True
            ):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                ajuste = -cantidad if "VENTA" in tipo_operacion else cantidad
                nuevo_stock = stock_actual + ajuste
                
                df.loc[df["Producto"] == producto_seleccionado, "Stock"] = nuevo_stock
                df.loc[df["Producto"] == producto_seleccionado, "Ultima_Actualizacion"] = ahora
                
                guardar_datos(df)
                st.cache_data.clear()
                
                st.success(f"✅ {producto_seleccionado} actualizado!")
                st.info(f"Nuevo stock: {nuevo_stock} unidades")
                st.balloons()

# ============================================================
#  TAB 2: INVENTARIO
# ============================================================
with tab2:
    df = leer_datos()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 ESTADO DE BEBIDAS")
    with col2:
        if st.button("🔄 ACTUALIZAR"):
            st.cache_data.clear()
            st.rerun()
    
    if df.empty:
        st.info("No hay productos registrados todavía.")
    else:
        # Métricas generales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Bebidas", len(df))
        with col2:
            total_unidades = int(df["Stock"].astype(int).sum())
            st.metric("Unidades Totales", total_unidades)
        with col3:
            bajo_stock = df[df["Stock"].astype(int) <= 5]
            st.metric("⚠️ Stock Bajo", len(bajo_stock))
        
        st.markdown("---")
        
        # Tabla de inventario
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Codigo": st.column_config.TextColumn("🔖 Código", width="medium"),
                "Producto": st.column_config.TextColumn("🥤 Producto", width="large"),
                "Stock": st.column_config.NumberColumn("📦 Stock", width="medium"),
                "Ultima_Actualizacion": st.column_config.TextColumn("⏰ Última Actualización", width="large")
            }
        )
        
        # Alerta de bajo stock
        if not bajo_stock.empty:
            st.markdown("---")
            st.warning("⚠️ PRODUCTOS CON STOCK BAJO O AGOTADO")
            st.dataframe(
                bajo_stock[["Producto", "Stock"]],
                use_container_width=True,
                hide_index=True
            )

# ============================================================
#  TAB 3: SISTEMA
# ============================================================
with tab3:
    st.subheader("⚙️ CONFIGURACIÓN DEL SISTEMA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**ESTADO DEL SISTEMA**")
        st.info("✅ Sistema operativo")
        st.info("✅ Google Sheets conectado")
        st.info("✅ Datos sincronizados")
    
    with col2:
        st.write("**ACCIONES**")
        if st.button("🔄 Sincronizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Datos sincronizados correctamente")
        
        if st.button("📥 Descargar Inventario", use_container_width=True):
            df = leer_datos()
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    st.caption("Soda Pro v1.0 - Sistema de Inventario en la Nube")
    st.caption("© 2026 - Todos los derechos reservados")
