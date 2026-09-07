"""
SODA PRO - APP VENDEDORA v3
Sistema POS con carrito de compras y diseño premium
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ============================================================
#  CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Punto de Venta",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS PREMIUM
st.markdown("""
    <style>
    /* Fondo animado */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Botón principal grande */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 4em;
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        font-weight: bold;
        font-size: 20px;
        border: none;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    }
    
    /* Métricas premium */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.98);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        border: 3px solid rgba(255,255,255,0.5);
    }
    
    [data-testid="metric-container"] > div {
        font-size: 24px !important;
        font-weight: bold;
    }
    
    [data-testid="metric-container"] label {
        font-size: 16px !important;
        font-weight: bold;
        color: #333;
    }
    
    /* Ocultar Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Título épico */
    h1 { 
        color: white; 
        text-align: center;
        text-shadow: 0 4px 15px rgba(0,0,0,0.3);
        font-size: 42px !important;
        font-weight: 900;
        letter-spacing: 2px;
    }
    
    h2, h3 {
        color: white;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    /* Input premium */
    .stTextInput input {
        font-size: 22px !important;
        height: 65px !important;
        border-radius: 20px !important;
        text-align: center;
        border: 3px solid rgba(255,255,255,0.5) !important;
        background: rgba(255,255,255,0.95) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        font-weight: bold;
    }
    
    .stNumberInput input {
        font-size: 22px !important;
        height: 55px !important;
        text-align: center;
        border-radius: 15px !important;
    }
    
    /* Tarjeta del carrito */
    .carrito-item {
        background: rgba(255,255,255,0.95);
        border-radius: 15px;
        padding: 15px 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #11998e;
    }
    
    /* Total grande */
    .total-grande {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        font-size: 32px;
        font-weight: 900;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        margin: 20px 0;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    
    .stSuccess {
        background: linear-gradient(90deg, #11998e, #38ef7d) !important;
        color: white !important;
    }
    
    .stError {
        background: linear-gradient(90deg, #ff416c, #ff4b2b) !important;
        color: white !important;
    }
    
    .stInfo {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    /* Radio buttons */
    .stRadio {
        background: rgba(255,255,255,0.9);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
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
        for col in ["Stock", "Costo", "Precio_Venta"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        if "Codigo" in df.columns:
            df["Codigo"] = df["Codigo"].astype(str)
        if "Unidad" not in df.columns:
            df["Unidad"] = "Unidades"
        return df
    return pd.DataFrame()

def guardar_catalogo(df):
    ws = get_catalog_ws()
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

def registrar_venta(codigo, producto, cantidad, unidad, precio, costo):
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
#  SESSION STATE
# ============================================================
if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "ventas_hoy" not in st.session_state:
    st.session_state.ventas_hoy = 0
if "total_hoy" not in st.session_state:
    st.session_state.total_hoy = 0.0
if "ultima_venta" not in st.session_state:
    st.session_state.ultima_venta = ""
if "codigo_procesado" not in st.session_state:
    st.session_state.codigo_procesado = ""

# ============================================================
#  INTERFAZ
# ============================================================
st.title("🛒 PUNTO DE VENTA")

# Mensaje última venta
if st.session_state.ultima_venta:
    st.success(f"### {st.session_state.ultima_venta}")

# Contadores del día
col1, col2 = st.columns(2)
with col1:
    st.metric("🛒 Ventas HOY", st.session_state.ventas_hoy)
with col2:
    st.metric("💵 Total HOY", f"${st.session_state.total_hoy:.2f}")

st.markdown("---")

df = leer_catalogo()

if df.empty:
    st.error("❌ No hay productos. Contacta al administrador.")
else:
    # ============================================================
    #  ESCÁNER
    # ============================================================
    st.markdown("### 📷 ESCANEA EL PRODUCTO")
    
    codigo_escaneado = st.text_input(
        "",
        placeholder="Apunta el escáner o escribe el código...",
        key="scanner_input",
        label_visibility="collapsed"
    )
    
    # Procesar código escaneado (solo si es nuevo)
    if codigo_escaneado and codigo_escaneado != st.session_state.codigo_procesado:
        codigo_escaneado = codigo_escaneado.strip()
        st.session_state.codigo_procesado = codigo_escaneado
        st.session_state.ultima_venta = ""
        
        if codigo_escaneado in df["Codigo"].values:
            fila = df[df["Codigo"] == codigo_escaneado].iloc[0]
            producto = fila["Producto"]
            stock_actual = float(fila["Stock"])
            unidad = fila.get("Unidad", "Unidades")
            precio = float(fila.get("Precio_Venta", 0))
            costo = float(fila.get("Costo", 0))
            
            # Verificar si ya está en el carrito
            en_carrito = False
            for item in st.session_state.carrito:
                if item["codigo"] == codigo_escaneado:
                    item["cantidad"] += 1
                    item["subtotal"] = item["cantidad"] * item["precio"]
                    en_carrito = True
                    break
            
            # Si no está en el carrito, agregarlo
            if not en_carrito:
                st.session_state.carrito.append({
                    "codigo": codigo_escaneado,
                    "producto": producto,
                    "cantidad": 1,
                    "unidad": unidad,
                    "precio": precio,
                    "costo": costo,
                    "subtotal": precio,
                    "stock_disponible": stock_actual
                })
            
            st.rerun()
        else:
            st.error(f"❌ Código {codigo_escaneado} NO existe")
    
    st.markdown("---")
    
    # ============================================================
    #  CARRITO
    # ============================================================
    if st.session_state.carrito:
        st.markdown("### 🛒 CARRITO DE COMPRAS")
        
        total_carrito = 0
        items_a_eliminar = []
        
        for i, item in enumerate(st.session_state.carrito):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{item['producto']}**")
                    st.caption(f"${item['precio']:.2f} × {item['cantidad']:g} {item['unidad']}")
                
                with col2:
                    # Cambiar cantidad
                    nueva_cantidad = st.number_input(
                        "Cant:",
                        min_value=0.01,
                        value=float(item['cantidad']),
                        step=1.0,
                        key=f"cant_{i}",
                        label_visibility="collapsed"
                    )
                    if nueva_cantidad != item['cantidad']:
                        item['cantidad'] = nueva_cantidad
                        item['subtotal'] = nueva_cantidad * item['precio']
                
                with col3:
                    st.markdown(f"### ${item['subtotal']:.2f}")
                
                with col4:
                    if st.button("🗑️", key=f"del_{i}"):
                        items_a_eliminar.append(i)
                
                total_carrito += item['subtotal']
                st.markdown("---")
        
        # Eliminar items marcados
        for i in sorted(items_a_eliminar, reverse=True):
            st.session_state.carrito.pop(i)
            st.rerun()
        
        # TOTAL
        st.markdown(f"""
        <div class="total-grande">
            💰 TOTAL A COBRAR<br>
            ${total_carrito:.2f}
        </div>
        """, unsafe_allow_html=True)
        
        # BOTONES
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.session_state.carrito = []
                st.session_state.codigo_procesado = ""
                st.rerun()
        
        with col2:
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                # Validar stock antes de cobrar
                stock_ok = True
                for item in st.session_state.carrito:
                    fila = df[df["Codigo"] == item["codigo"]].iloc[0]
                    stock_real = float(fila["Stock"])
                    if item["cantidad"] > stock_real:
                        st.error(f"❌ Stock insuficiente para {item['producto']}. Solo hay {stock_real:g}")
                        stock_ok = False
                        break
                
                if stock_ok:
                    # Procesar todas las ventas
                    for item in st.session_state.carrito:
                        # Actualizar stock
                        fila_idx = df[df["Codigo"] == item["codigo"]].index[0]
                        df.at[fila_idx, "Stock"] = df.at[fila_idx, "Stock"] - item["cantidad"]
                        
                        # Registrar venta
                        registrar_venta(
                            item["codigo"], item["producto"], item["cantidad"],
                            item["unidad"], item["precio"], item["costo"]
                        )
                    
                    # Guardar catálogo actualizado
                    guardar_catalogo(df)
                    
                    # Actualizar contadores
                    st.session_state.ventas_hoy += 1
                    st.session_state.total_hoy += total_carrito
                    st.session_state.ultima_venta = f"🎉 VENTA REGISTRADA - ${total_carrito:.2f} ({len(st.session_state.carrito)} productos)"
                    
                    # Limpiar carrito
                    st.session_state.carrito = []
                    st.session_state.codigo_procesado = ""
                    
                    st.cache_data.clear()
                    st.balloons()
                    st.rerun()
    else:
        st.info("🛒 El carrito está vacío. Escanea productos para empezar.")
