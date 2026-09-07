"""
SODA PRO - APP VENDEDORA
Interfaz ultra-simple: solo escanear y vender
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
    page_title="Ventas",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Grande y Simple
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 5em;
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        font-weight: bold;
        font-size: 24px;
        border: none;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.95);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
    }
    [data-testid="metric-container"] > div {
        font-size: 20px !important;
    }
    [data-testid="metric-container"] label {
        font-size: 18px !important;
        font-weight: bold;
    }
    #MainMenu, footer, header { visibility: hidden; }
    h1 { 
        color: white; 
        text-align: center;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        font-size: 40px !important;
    }
    .stTextInput input {
        font-size: 24px !important;
        height: 60px !important;
        border-radius: 15px !important;
        text-align: center;
    }
    .stNumberInput input {
        font-size: 24px !important;
        height: 60px !important;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Sonidos con JavaScript
st.markdown("""
<script>
function playDing() {
    var audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahVFApGn+DyvmwhBTuGvfXPeS4EJHXH8N+RQAoUXrPq6ahV');
    audio.play();
}
</script>
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

# Contador de ventas del día en session_state
if "ventas_hoy" not in st.session_state:
    st.session_state.ventas_hoy = 0
if "total_hoy" not in st.session_state:
    st.session_state.total_hoy = 0.0

# ============================================================
#  INTERFAZ
# ============================================================
st.title("🛒 VENTAS")

# Contador del día
col1, col2 = st.columns(2)
with col1:
    st.metric("🛒 Ventas de HOY", st.session_state.ventas_hoy)
with col2:
    st.metric("💵 Total HOY", f"${st.session_state.total_hoy:.2f}")

st.markdown("---")

df = leer_catalogo()

if df.empty:
    st.error("❌ No hay productos. Contacta al administrador.")
else:
    # Campo de escáner (grande y centrado)
    st.markdown("### 📷 ESCANEA EL PRODUCTO")
    
    codigo_escaneado = st.text_input(
        "",
        placeholder="Apunta el escáner al código...",
        key="scanner_vendedora",
        label_visibility="collapsed"
    )
    
    if codigo_escaneado:
        codigo_escaneado = codigo_escaneado.strip()
        
        if codigo_escaneado in df["Codigo"].values:
            fila = df[df["Codigo"] == codigo_escaneado].iloc[0]
            producto = fila["Producto"]
            stock_actual = float(fila["Stock"])
            unidad = fila.get("Unidad", "Unidades")
            precio = float(fila.get("Precio_Venta", 0))
            costo = float(fila.get("Costo", 0))
            
            # Sonido de éxito
            st.markdown("""
            <audio autoplay>
                <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.wav" type="audio/wav">
            </audio>
            <script>playDing();</script>
            """, unsafe_allow_html=True)
            
            st.success(f"✅ **{producto}**")
            
            # Info del producto
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📦 Stock", f"{stock_actual:g} {unidad}")
            with col2:
                st.metric("💵 Precio", f"${precio:.2f}")
            
            st.markdown("---")
            
            # Cantidad (por defecto 1)
            cantidad = st.number_input(
                f"CANTIDAD ({unidad}):",
                min_value=0.01,
                value=1.0,
                step=1.0,
                format="%.2f",
                key="cantidad_vendedora"
            )
            
            # Total a cobrar
            total = cantidad * precio
            st.markdown(f"### 💰 TOTAL A COBRAR: **${total:.2f}**")
            
            # Validar stock
            if cantidad > stock_actual:
                st.error(f"❌ Stock insuficiente. Solo hay {stock_actual:g} {unidad}")
            else:
                if st.button("✅ CONFIRMAR VENTA", type="primary", use_container_width=True):
                    # Actualizar stock
                    nuevo_stock = stock_actual - cantidad
                    df.loc[df["Codigo"] == codigo_escaneado, "Stock"] = nuevo_stock
                    guardar_catalogo(df)
                    
                    # Registrar venta
                    registrar_venta(codigo_escaneado, producto, cantidad, unidad, precio, costo)
                    
                    # Actualizar contador
                    st.session_state.ventas_hoy += 1
                    st.session_state.total_hoy += total
                    
                    st.cache_data.clear()
                    st.success(f"✅ VENTA REGISTRADA - ${total:.2f}")
                    st.balloons()
                    
                    # Recargar
                    st.rerun()
        else:
            # Sonido de error
            st.markdown("""
            <audio autoplay>
                <source src="https://www.soundjay.com/misc/sounds/fail-buzzer-04.wav" type="audio/wav">
            </audio>
            """, unsafe_allow_html=True)
            st.error(f"❌ Código {codigo_escaneado} NO existe en el sistema")
