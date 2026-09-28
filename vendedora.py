"""
SODA PRO - APP VENDEDORA v5
2 pestañas (Bebidas / Accesorios) + Apertura/Cierre de Caja + Control de efectivo
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import urllib.parse

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
    .stButton>button, .stLinkButton>a {
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
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.98);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        border: 3px solid rgba(255,255,255,0.5);
    }
    [data-testid="metric-container"] > div { font-size: 24px !important; font-weight: bold; }
    [data-testid="metric-container"] label { font-size: 16px !important; font-weight: bold; color: #333; }
    #MainMenu, footer, header { visibility: hidden; }
    h1 { color: white; text-align: center; text-shadow: 0 4px 15px rgba(0,0,0,0.3);
         font-size: 42px !important; font-weight: 900; letter-spacing: 2px; }
    h2, h3 { color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
    .stTextInput input {
        font-size: 22px !important; height: 65px !important; border-radius: 20px !important;
        text-align: center; border: 3px solid rgba(255,255,255,0.5) !important;
        background: rgba(255,255,255,0.95) !important; box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        font-weight: bold;
    }
    .stNumberInput input { font-size: 22px !important; height: 55px !important; text-align: center; border-radius: 15px !important; }
    .total-grande {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white; padding: 25px; border-radius: 20px; text-align: center;
        font-size: 32px; font-weight: 900; box-shadow: 0 8px 25px rgba(0,0,0,0.3); margin: 20px 0;
    }
    .caja-card {
        background: rgba(255,255,255,0.97);
        border-radius: 20px; padding: 30px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        text-align: center; margin: 15px 0;
    }
    .caja-cerrada {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 40px; border-radius: 25px; text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4); margin: 20px 0;
    }
    .ticket-box {
        background: rgba(255,255,255,0.97);
        border-radius: 15px; padding: 20px;
        font-family: 'Courier New', monospace; font-size: 15px;
        white-space: pre-wrap; color: #222;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2); margin: 15px 0;
    }
    .stAlert { border-radius: 15px !important; border: none !important; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
    .stRadio { background: rgba(255,255,255,0.9); padding: 15px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#  GOOGLE SHEETS
# ============================================================
SHEET_ID = "1Cq1KKnmNqMhtaDN_vsj__WofYtSUfc8jyPOUrjV9i3Y"

try:
    CREDENTIALS = dict(st.secrets["google_credentials"])
except Exception:
    st.error("⚠️ Faltan las credenciales de Google. Pídele al administrador que configure los 'Secrets' de esta app.")
    st.stop()

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

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
        encabezados_actuales = ws.row_values(1)
        if "Categoria" not in encabezados_actuales:
            # Agregar columna Categoria si no existe
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
    """Obtiene o crea la hoja de Caja para registrar aperturas, ventas y cierres"""
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
def leer_caja():
    """Lee todos los registros de la hoja Caja"""
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

def actualizar_stock_producto(codigo, nuevo_stock):
    """Actualiza SOLO el stock de un producto. No toca otras filas."""
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

def registrar_fiado(cliente, detalle, total):
    ws_fiados = get_fiados_ws()
    ahora = datetime.now()
    ws_fiados.append_row([
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"),
        cliente, detalle, total, "Pendiente"
    ])

def registrar_en_caja(tipo, metodo, monto, descripcion, categoria, efectivo_inicial=0.0):
    """Registra un movimiento en la hoja Caja"""
    ws = get_caja_ws()
    ahora = datetime.now()
    ws.append_row([
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"),
        tipo, float(efectivo_inicial), metodo, float(monto), descripcion, categoria
    ])
    st.cache_data.clear()

def generar_ticket(carrito, total, metodo_pago, monto_recibido=None, cambio=None, cliente="", categoria=""):
    ahora = datetime.now()
    lineas = []
    lineas.append("SODA PRO")
    lineas.append(f"{categoria}" if categoria else "")
    lineas.append(f"{ahora.strftime('%d/%m/%Y')}  {ahora.strftime('%H:%M')}")
    lineas.append("------------------------------")
    for item in carrito:
        lineas.append(f"{item['producto']} x{item['cantidad']:g}  ${item['subtotal']:.2f}")
    lineas.append("------------------------------")
    lineas.append(f"TOTAL: ${total:.2f}")
    lineas.append(f"Metodo: {metodo_pago}")
    if metodo_pago == "Efectivo" and monto_recibido is not None:
        lineas.append(f"Recibido: ${monto_recibido:.2f}")
        lineas.append(f"Cambio: ${cambio:.2f}")
    if metodo_pago == "Fiado":
        lineas.append(f"Cliente: {cliente}")
        lineas.append("PENDIENTE DE PAGO")
    lineas.append("------------------------------")
    lineas.append("¡Gracias por su compra!")
    return "\n".join(l for l in lineas if l)

# ============================================================
#  SESSION STATE
# ============================================================
# Estado por categoría (beb = Bebidas, acc = Accesorios)
defaults = {
    # Carritos por categoría
    "carrito_beb": [], "carrito_acc": [],
    # Contadores por categoría
    "ventas_beb": 0, "ventas_acc": 0,
    "total_beb": 0.0, "total_acc": 0.0,
    # Estado de caja
    "caja_abierta": False,
    "caja_efectivo_inicial_beb": 0.0,
    "caja_efectivo_inicial_acc": 0.0,
    "caja_metodos_beb": [],   # lista de métodos habilitados para Bebidas
    "caja_metodos_acc": [],   # lista de métodos habilitados para Accesorios
    "caja_fecha_apertura_beb": None,
    "caja_fecha_apertura_acc": None,
    # Totales caja en tiempo real (por categoría y método)
    "caja_efectivo_beb": 0.0, "caja_transferencia_beb": 0.0, "caja_fiado_beb": 0.0,
    "caja_efectivo_acc": 0.0, "caja_transferencia_acc": 0.0, "caja_fiado_acc": 0.0,
    # Ticket y última venta
    "ticket_texto_beb": None, "ticket_link_beb": None,
    "ticket_texto_acc": None, "ticket_link_acc": None,
    "ultima_venta_carrito_beb": [], "ultima_venta_metodo_beb": "", "ultima_venta_total_beb": 0.0,
    "ultima_venta_carrito_acc": [], "ultima_venta_metodo_acc": "", "ultima_venta_total_acc": 0.0,
    # Contadores de UI
    "input_counter_beb": 0, "input_counter_acc": 0,
    "venta_counter_beb": 0, "venta_counter_acc": 0,
    "busqueda_counter_beb": 0, "busqueda_counter_acc": 0,
    "flash": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
#  FUNCIONES DE CARRITO POR CATEGORÍA
# ============================================================
def agregar_al_carrito(df, codigo, cat_key):
    """Agrega al carrito de la categoría (cat_key = 'beb' o 'acc')"""
    carrito_key = f"carrito_{cat_key}"
    if codigo not in df["Codigo"].values:
        return False
    fila = df[df["Codigo"] == codigo].iloc[0]
    for item in st.session_state[carrito_key]:
        if item["codigo"] == codigo:
            item["cantidad"] += 1
            item["subtotal"] = item["cantidad"] * item["precio"]
            return True
    st.session_state[carrito_key].append({
        "codigo": codigo, "producto": fila["Producto"], "cantidad": 1,
        "unidad": fila.get("Unidad", "Unidades"),
        "precio": float(fila.get("Precio_Venta", 0)), "costo": float(fila.get("Costo", 0)),
        "subtotal": float(fila.get("Precio_Venta", 0)),
        "stock_disponible": float(fila["Stock"]),
        "categoria": str(fila.get("Categoria", ""))
    })
    return True

def deshacer_ultima_venta(cat_key):
    """Revierte la última venta de la categoría indicada"""
    carrito_key = f"ultima_venta_carrito_{cat_key}"
    metodo_key = f"ultima_venta_metodo_{cat_key}"
    total_key = f"ultima_venta_total_{cat_key}"
    cat_nombre = "Bebidas" if cat_key == "beb" else "Accesorios"

    df_actual = leer_catalogo()
    for item in st.session_state[carrito_key]:
        idx = df_actual[df_actual["Codigo"] == item["codigo"]].index
        if len(idx):
            nuevo_stock = df_actual.at[idx[0], "Stock"] + item["cantidad"]
            actualizar_stock_producto(item["codigo"], nuevo_stock)

    # Borrar filas de Ventas
    try:
        ws_v = get_ventas_ws()
        total_filas = len(ws_v.get_all_values())
        n = len(st.session_state[carrito_key])
        if n > 0 and total_filas > n:
            ws_v.delete_rows(total_filas - n + 1, total_filas)
    except Exception:
        pass

    # Borrar fila de Fiados si aplica
    if st.session_state[metodo_key] == "Fiado":
        try:
            ws_f = get_fiados_ws()
            total_f = len(ws_f.get_all_values())
            if total_f > 1:
                ws_f.delete_rows(total_f)
        except Exception:
            pass

    # Revertir totales de caja
    metodo = st.session_state[metodo_key]
    monto = st.session_state[total_key]
    if metodo == "Efectivo":
        st.session_state[f"caja_efectivo_{cat_key}"] = max(0.0, st.session_state[f"caja_efectivo_{cat_key}"] - monto)
    elif metodo == "Transferencia":
        st.session_state[f"caja_transferencia_{cat_key}"] = max(0.0, st.session_state[f"caja_transferencia_{cat_key}"] - monto)
    elif metodo == "Fiado":
        st.session_state[f"caja_fiado_{cat_key}"] = max(0.0, st.session_state[f"caja_fiado_{cat_key}"] - monto)

    # Revertir totales del día
    st.session_state[f"ventas_{cat_key}"] = max(0, st.session_state[f"ventas_{cat_key}"] - 1)
    st.session_state[f"total_{cat_key}"] = max(0.0, st.session_state[f"total_{cat_key}"] - monto)

    # Registrar reversa en caja
    registrar_en_caja("REVERSA", metodo, -monto, "Venta anulada", cat_nombre)

    st.session_state[f"ticket_texto_{cat_key}"] = None
    st.session_state[f"ticket_link_{cat_key}"] = None
    st.session_state[carrito_key] = []
    st.session_state[f"venta_counter_{cat_key}"] += 1
    st.session_state.flash = "↩️ Venta corregida. El stock fue restaurado."
    st.cache_data.clear()

# ============================================================
#  PANTALLA DE APERTURA DE CAJA
# ============================================================
def pantalla_apertura_caja():
    st.title("🥤 SODA PRO")
    st.markdown('<div class="caja-cerrada">'
                '<h2 style="color:white;">📦 APERTURA DE CAJA</h2>'
                '<p style="color:#ccc;">Configura tu turno antes de empezar</p>'
                '</div>', unsafe_allow_html=True)

    st.markdown("### 💰 EFECTIVO INICIAL")
    col1, col2 = st.columns(2)
    with col1:
        efectivo_ini_beb = st.number_input(
            "💰 Efectivo inicial 🥤 Bebidas:",
            min_value=0.0, value=0.0, step=1.0, format="%.2f",
            key="inp_ef_ini_beb"
        )
    with col2:
        efectivo_ini_acc = st.number_input(
            "💰 Efectivo inicial 👜 Accesorios:",
            min_value=0.0, value=0.0, step=1.0, format="%.2f",
            key="inp_ef_ini_acc"
        )

    st.markdown("---")
    st.markdown("### 💳 MÉTODOS DE PAGO HABILITADOS")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🥤 Bebidas**")
        m_ef_beb   = st.checkbox("💵 Efectivo",      value=True, key="m_ef_beb")
        m_tr_beb   = st.checkbox("🏦 Transferencia", value=True, key="m_tr_beb")
        m_fi_beb   = st.checkbox("📝 Fiado",         value=True, key="m_fi_beb")
    with col2:
        st.markdown("**👜 Accesorios**")
        m_ef_acc   = st.checkbox("💵 Efectivo",      value=True, key="m_ef_acc")
        m_tr_acc   = st.checkbox("🏦 Transferencia", value=True, key="m_tr_acc")
        m_fi_acc   = st.checkbox("📝 Fiado",         value=True, key="m_fi_acc")

    metodos_beb = []
    if m_ef_beb: metodos_beb.append("Efectivo")
    if m_tr_beb: metodos_beb.append("Transferencia")
    if m_fi_beb: metodos_beb.append("Fiado")

    metodos_acc = []
    if m_ef_acc: metodos_acc.append("Efectivo")
    if m_tr_acc: metodos_acc.append("Transferencia")
    if m_fi_acc: metodos_acc.append("Fiado")

    st.markdown("---")

    if not metodos_beb and not metodos_acc:
        st.warning("⚠️ Debes habilitar al menos un método de pago en cada sección")

    if st.button("🔓 ABRIR CAJA Y EMPEZAR", use_container_width=True, type="primary",
                 disabled=(not metodos_beb and not metodos_acc)):
        ahora = datetime.now()

        # Guardar estado en session_state
        st.session_state.caja_efectivo_inicial_beb = efectivo_ini_beb
        st.session_state.caja_efectivo_inicial_acc = efectivo_ini_acc
        st.session_state.caja_metodos_beb = metodos_beb
        st.session_state.caja_metodos_acc = metodos_acc
        st.session_state.caja_fecha_apertura_beb = ahora.strftime("%Y-%m-%d %H:%M")
        st.session_state.caja_fecha_apertura_acc = ahora.strftime("%Y-%m-%d %H:%M")

        # Reset totales
        for cat in ["beb", "acc"]:
            st.session_state[f"caja_efectivo_{cat}"] = 0.0
            st.session_state[f"caja_transferencia_{cat}"] = 0.0
            st.session_state[f"caja_fiado_{cat}"] = 0.0
            st.session_state[f"ventas_{cat}"] = 0
            st.session_state[f"total_{cat}"] = 0.0

        st.session_state.caja_abierta = True

        # Registrar apertura en Google Sheets
        try:
            registrar_en_caja("APERTURA", "Efectivo", efectivo_ini_beb, "Apertura de turno", "Bebidas", efectivo_ini_beb)
            registrar_en_caja("APERTURA", "Efectivo", efectivo_ini_acc, "Apertura de turno", "Accesorios", efectivo_ini_acc)
        except Exception:
            pass

        st.rerun()

# ============================================================
#  MÓDULO POS POR CATEGORÍA
# ============================================================
def render_pos(cat_key, cat_nombre, cat_emoji, df_cat, metodos_habilitados):
    """Renderiza el POS completo para una categoría"""
    carrito_key       = f"carrito_{cat_key}"
    ticket_txt_key    = f"ticket_texto_{cat_key}"
    ticket_link_key   = f"ticket_link_{cat_key}"
    vc_key            = f"venta_counter_{cat_key}"
    ic_key            = f"input_counter_{cat_key}"
    bc_key            = f"busqueda_counter_{cat_key}"
    ult_carrito_key   = f"ultima_venta_carrito_{cat_key}"
    ult_metodo_key    = f"ultima_venta_metodo_{cat_key}"
    ult_total_key     = f"ultima_venta_total_{cat_key}"

    # Flash
    if st.session_state.flash:
        st.info(st.session_state.flash)
        st.session_state.flash = None

    # Ticket de última venta
    if st.session_state[ticket_txt_key]:
        st.success("### 🎉 ¡VENTA REGISTRADA!")
        st.markdown(f'<div class="ticket-box">{st.session_state[ticket_txt_key]}</div>', unsafe_allow_html=True)
        if st.session_state[ticket_link_key]:
            st.link_button("📲 Enviar por WhatsApp", st.session_state[ticket_link_key], use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"↩️ CORREGIR", use_container_width=True, key=f"anular_{cat_key}"):
                deshacer_ultima_venta(cat_key)
                st.rerun()
        with c2:
            if st.button(f"🆕 NUEVA VENTA", use_container_width=True, key=f"nueva_{cat_key}"):
                st.session_state[ticket_txt_key] = None
                st.session_state[ticket_link_key] = None
                st.rerun()
        st.markdown("---")

    # Métricas del día para esta categoría
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🛒 Ventas", st.session_state[f"ventas_{cat_key}"])
    with col2:
        st.metric("💵 Efectivo", f"${st.session_state[f'caja_efectivo_{cat_key}']:.2f}")
    with col3:
        st.metric("🏦 Transf.", f"${st.session_state[f'caja_transferencia_{cat_key}']:.2f}")
    with col4:
        st.metric("📝 Fiado", f"${st.session_state[f'caja_fiado_{cat_key}']:.2f}")

    st.markdown("---")

    if df_cat.empty:
        st.warning(f"⚠️ No hay productos en {cat_nombre}. El administrador debe agregar la categoría.")
        return

    # Escáner
    st.markdown(f"### 📷 ESCANEA EL PRODUCTO")
    codigo_escaneado = st.text_input(
        "",
        placeholder="Apunta el escáner o escribe el código...",
        key=f"scanner_{cat_key}_{st.session_state[ic_key]}",
        label_visibility="collapsed"
    )
    if codigo_escaneado:
        codigo_escaneado = codigo_escaneado.strip()
        st.session_state[ticket_txt_key] = None
        st.session_state[ticket_link_key] = None
        if not agregar_al_carrito(df_cat, codigo_escaneado, cat_key):
            st.error(f"❌ Código {codigo_escaneado} no encontrado en {cat_nombre}")
        st.session_state[ic_key] += 1
        st.rerun()

    with st.expander("🔎 ¿No lee el código? Busca por nombre"):
        opciones = ["--- Selecciona ---"] + sorted(df_cat["Producto"].dropna().unique().tolist())
        seleccion = st.selectbox(
            "Producto:", opciones,
            key=f"buscar_{cat_key}_{st.session_state[bc_key]}",
            label_visibility="collapsed"
        )
        if seleccion != "--- Selecciona ---":
            codigo_sel = str(df_cat.loc[df_cat["Producto"] == seleccion, "Codigo"].values[0])
            st.session_state[ticket_txt_key] = None
            st.session_state[ticket_link_key] = None
            agregar_al_carrito(df_cat, codigo_sel, cat_key)
            st.session_state[bc_key] += 1
            st.rerun()

    st.markdown("---")

    # Carrito
    carrito = st.session_state[carrito_key]
    if carrito:
        st.markdown("### 🛒 CARRITO")
        total_carrito = 0
        items_a_eliminar = []
        for i, item in enumerate(carrito):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1:
                st.markdown(f"**{item['producto']}**")
                st.caption(f"${item['precio']:.2f} × {item['cantidad']:g} {item['unidad']}")
            with c2:
                nueva_cantidad = st.number_input(
                    "Cant:", min_value=0.01, value=float(item['cantidad']),
                    step=1.0, key=f"cant_{cat_key}_{i}", label_visibility="collapsed"
                )
                if nueva_cantidad != item['cantidad']:
                    item['cantidad'] = nueva_cantidad
                    item['subtotal'] = nueva_cantidad * item['precio']
            with c3:
                st.markdown(f"### ${item['subtotal']:.2f}")
            with c4:
                if st.button("🗑️", key=f"del_{cat_key}_{i}"):
                    items_a_eliminar.append(i)
            total_carrito += item['subtotal']
            st.markdown("---")

        for i in sorted(items_a_eliminar, reverse=True):
            carrito.pop(i)
            st.rerun()

        st.markdown(f'<div class="total-grande">💰 TOTAL A COBRAR<br>${total_carrito:.2f}</div>',
                    unsafe_allow_html=True)

        # Método de pago (solo los habilitados en apertura)
        st.markdown("### 💳 MÉTODO DE PAGO")
        iconos_metodo = {"Efectivo": "💵 Efectivo", "Transferencia": "🏦 Transferencia", "Fiado": "📝 Fiado"}
        opciones_metodo = [iconos_metodo[m] for m in metodos_habilitados if m in iconos_metodo]
        mapeo_reverso = {v: k for k, v in iconos_metodo.items()}

        metodo_pago_raw = st.radio(
            "Método:", opciones_metodo,
            horizontal=True,
            key=f"metodo_{cat_key}_{st.session_state[vc_key]}",
            label_visibility="collapsed"
        )
        metodo_pago = mapeo_reverso.get(metodo_pago_raw, "Efectivo")

        monto_recibido, cambio, cliente = None, None, ""
        puede_cobrar = True

        if metodo_pago == "Efectivo":
            monto_recibido = st.number_input(
                "💵 Monto recibido:", min_value=0.0, value=float(total_carrito),
                step=1.0, key=f"monto_{cat_key}_{st.session_state[vc_key]}"
            )
            cambio = monto_recibido - total_carrito
            if monto_recibido < total_carrito:
                st.warning(f"⚠️ Faltan ${total_carrito - monto_recibido:.2f}")
                puede_cobrar = False
            else:
                st.metric("💰 Cambio a devolver", f"${cambio:.2f}")

        elif metodo_pago == "Fiado":
            cliente = st.text_input(
                "👤 Nombre del cliente:",
                key=f"cliente_{cat_key}_{st.session_state[vc_key]}"
            )
            if not cliente.strip():
                st.warning("⚠️ Escribe el nombre del cliente")
                puede_cobrar = False
            else:
                st.info(f"📝 Deuda pendiente de **{cliente}**")

        # Botones
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ CANCELAR", use_container_width=True, key=f"cancel_{cat_key}"):
                st.session_state[carrito_key] = []
                st.session_state[vc_key] += 1
                st.rerun()
        with c2:
            if st.button("✅ COBRAR", type="primary", use_container_width=True,
                         disabled=not puede_cobrar, key=f"cobrar_{cat_key}"):
                # Verificar stock
                df_actual = leer_catalogo()
                stock_ok = True
                for item in carrito:
                    fila = df_actual[df_actual["Codigo"] == item["codigo"]]
                    if not fila.empty:
                        stock_real = float(fila.iloc[0]["Stock"])
                        if item["cantidad"] > stock_real:
                            st.error(f"❌ Stock insuficiente para {item['producto']}. Solo hay {stock_real:g}")
                            stock_ok = False
                            break

                if stock_ok:
                    for item in carrito:
                        fila_idx = df_actual[df_actual["Codigo"] == item["codigo"]].index
                        if len(fila_idx):
                            nuevo_stock = df_actual.at[fila_idx[0], "Stock"] - item["cantidad"]
                            actualizar_stock_producto(item["codigo"], nuevo_stock)
                        registrar_venta(
                            item["codigo"], item["producto"], item["cantidad"],
                            item["unidad"], item["precio"], item["costo"],
                            metodo_pago=metodo_pago, cliente=cliente,
                            categoria=cat_nombre
                        )

                    if metodo_pago == "Fiado":
                        detalle = ", ".join(f"{it['producto']} x{it['cantidad']:g}" for it in carrito)
                        registrar_fiado(cliente, detalle, total_carrito)

                    # Actualizar totales de caja en session_state
                    if metodo_pago == "Efectivo":
                        st.session_state[f"caja_efectivo_{cat_key}"] += total_carrito
                    elif metodo_pago == "Transferencia":
                        st.session_state[f"caja_transferencia_{cat_key}"] += total_carrito
                    elif metodo_pago == "Fiado":
                        st.session_state[f"caja_fiado_{cat_key}"] += total_carrito

                    # Registrar en hoja Caja
                    registrar_en_caja(
                        "VENTA", metodo_pago, total_carrito,
                        f"Venta {len(carrito)} items", cat_nombre
                    )

                    # Generar ticket
                    ticket = generar_ticket(
                        carrito, total_carrito, metodo_pago,
                        monto_recibido=monto_recibido, cambio=cambio,
                        cliente=cliente, categoria=cat_nombre
                    )
                    st.session_state[ticket_txt_key] = ticket
                    st.session_state[ticket_link_key] = (
                        "https://api.whatsapp.com/send?text=" + urllib.parse.quote(ticket)
                    )

                    # Guardar última venta para poder anular
                    st.session_state[ult_carrito_key] = list(carrito)
                    st.session_state[ult_metodo_key] = metodo_pago
                    st.session_state[ult_total_key] = total_carrito

                    st.session_state[f"ventas_{cat_key}"] += 1
                    st.session_state[f"total_{cat_key}"] += total_carrito
                    st.session_state[carrito_key] = []
                    st.session_state[vc_key] += 1

                    st.cache_data.clear()
                    st.balloons()
                    st.rerun()
    else:
        st.info(f"🛒 Carrito vacío. Escanea un producto de {cat_nombre}.")

# ============================================================
#  VISTA RESUMEN DE CAJA POR FECHA
# ============================================================
def render_resumen_caja():
    st.markdown("### 📊 RESUMEN DE CAJA")

    df_caja = leer_caja()
    df_ventas = leer_ventas()

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualizar", use_container_width=True, key="refresh_caja"):
            st.cache_data.clear()
            st.rerun()

    hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_filtro = st.date_input("📅 Ver fecha:", value=datetime.now().date(), key="fecha_caja")
    fecha_str = fecha_filtro.strftime("%Y-%m-%d")

    if not df_ventas.empty and "Fecha" in df_ventas.columns:
        ventas_fecha = df_ventas[df_ventas["Fecha"] == fecha_str]
    else:
        ventas_fecha = pd.DataFrame()

    st.markdown("---")

    for cat_nombre, cat_emoji in [("Bebidas", "🥤"), ("Accesorios", "👜")]:
        st.markdown(f"#### {cat_emoji} {cat_nombre}")

        if ventas_fecha.empty or "Categoria" not in ventas_fecha.columns:
            st.caption("Sin ventas registradas")
        else:
            ventas_cat = ventas_fecha[ventas_fecha["Categoria"] == cat_nombre]
            if ventas_cat.empty:
                st.caption("Sin ventas")
            else:
                por_metodo = ventas_cat.groupby("Metodo_Pago")["Total"].sum()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("💵 Efectivo", f"${por_metodo.get('Efectivo', 0):.2f}")
                with c2:
                    st.metric("🏦 Transf.", f"${por_metodo.get('Transferencia', 0):.2f}")
                with c3:
                    st.metric("📝 Fiado", f"${por_metodo.get('Fiado', 0):.2f}")
                with c4:
                    st.metric("💰 TOTAL", f"${ventas_cat['Total'].sum():.2f}")

        st.markdown("---")

    # Efectivo inicial de la apertura del día (de hoja Caja)
    if not df_caja.empty and "Fecha" in df_caja.columns and "Tipo" in df_caja.columns:
        aperturas = df_caja[(df_caja["Fecha"] == fecha_str) & (df_caja["Tipo"] == "APERTURA")]
        if not aperturas.empty:
            st.markdown("#### 🔓 Aperturas del día")
            st.dataframe(
                aperturas[["Hora", "Categoria", "Efectivo_Inicial"]].rename(columns={
                    "Hora": "Hora", "Categoria": "Sección", "Efectivo_Inicial": "Efectivo Inicial"
                }),
                use_container_width=True, hide_index=True
            )

# ============================================================
#  INVENTARIO (solo lectura para vendedora)
# ============================================================
def render_inventario():
    st.markdown("### 📦 INVENTARIO")
    st.caption("Solo lectura — el administrador es quien modifica el stock.")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualizar", use_container_width=True, key="refresh_inv_vend"):
            st.cache_data.clear()
            st.rerun()

    # Selector de fecha para ver lo vendido ese día
    fecha_sel = st.date_input("📅 Ver ventas del día:", value=datetime.now().date(), key="inv_fecha")
    fecha_str = fecha_sel.strftime("%Y-%m-%d")

    df_cat  = leer_catalogo()
    df_vtas = leer_ventas()

    if df_cat.empty:
        st.warning("No hay productos registrados.")
        return

    # Calcular vendido en la fecha seleccionada por código
    vendido_por_codigo = {}
    if not df_vtas.empty and "Fecha" in df_vtas.columns and "Codigo" in df_vtas.columns:
        vtas_fecha = df_vtas[df_vtas["Fecha"] == fecha_str]
        if not vtas_fecha.empty:
            vendido_por_codigo = (
                vtas_fecha.groupby("Codigo")["Cantidad"].sum().to_dict()
            )

    st.markdown("---")

    for cat_nombre, cat_emoji in [("Bebidas", "🥤"), ("Accesorios", "👜")]:
        df_c = df_cat[df_cat["Categoria"].str.strip().str.lower() == cat_nombre.lower()]
        if df_c.empty:
            continue

        st.markdown(f"#### {cat_emoji} {cat_nombre}")

        filas = []
        for _, row in df_c.iterrows():
            cod = str(row["Codigo"])
            stock_actual = float(row["Stock"])
            vendido      = float(vendido_por_codigo.get(cod, 0))
            # Stock inicial estimado = stock actual + lo vendido en esa fecha
            stock_ini    = stock_actual + vendido

            filas.append({
                "Producto":       row["Producto"],
                "Unidad":         row.get("Unidad", "Unidades"),
                "Stock Inicial":  f"{stock_ini:g}",
                f"Vendido ({fecha_str})": f"{vendido:g}",
                "Stock Actual":   f"{stock_actual:g}",
            })

        df_display = pd.DataFrame(filas)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.markdown("---")

    st.caption("📌 'Stock Inicial' = Stock actual + lo vendido en la fecha seleccionada")

# ============================================================
#  CIERRE DE CAJA
# ============================================================
def render_cierre_caja():
    st.markdown("### 🔒 CIERRE DE CAJA")
    st.warning("⚠️ Al cerrar la caja se registrará el corte. Podrás abrir una nueva caja después.")

    df_ventas = leer_ventas()
    hoy = datetime.now().strftime("%Y-%m-%d")

    for cat_nombre, cat_emoji, cat_key in [("Bebidas", "🥤", "beb"), ("Accesorios", "👜", "acc")]:
        st.markdown(f"#### {cat_emoji} {cat_nombre}")
        ef_ini = st.session_state[f"caja_efectivo_inicial_{cat_key}"]
        ef_vtas = st.session_state[f"caja_efectivo_{cat_key}"]
        tr_vtas = st.session_state[f"caja_transferencia_{cat_key}"]
        fi_vtas = st.session_state[f"caja_fiado_{cat_key}"]
        total_esperado = ef_ini + ef_vtas

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("🔓 Efectivo Inicial", f"${ef_ini:.2f}")
        with c2:
            st.metric("💵 Ventas Efectivo", f"${ef_vtas:.2f}")
        with c3:
            st.metric("🏦 Transferencias", f"${tr_vtas:.2f}")
        with c4:
            st.metric("📝 Fiados", f"${fi_vtas:.2f}")

        st.info(f"💰 Total esperado en caja: ${total_esperado:.2f}")
        st.markdown("---")

    if st.button("🔒 CONFIRMAR CIERRE DE CAJA", use_container_width=True, type="primary"):
        ahora = datetime.now()
        # Registrar cierre para cada categoría
        for cat_nombre, cat_key in [("Bebidas", "beb"), ("Accesorios", "acc")]:
            ef = st.session_state[f"caja_efectivo_{cat_key}"]
            tr = st.session_state[f"caja_transferencia_{cat_key}"]
            fi = st.session_state[f"caja_fiado_{cat_key}"]
            total = ef + tr + fi
            registrar_en_caja(
                "CIERRE", "Todos", total,
                f"Cierre: Ef=${ef:.2f} Tr=${tr:.2f} Fi=${fi:.2f}",
                cat_nombre,
                st.session_state[f"caja_efectivo_inicial_{cat_key}"]
            )

        # Resetear estado de caja
        st.session_state.caja_abierta = False
        st.session_state.carrito_beb = []
        st.session_state.carrito_acc = []
        st.cache_data.clear()
        st.success("✅ Caja cerrada correctamente. Puedes abrir una nueva caja cuando quieras.")
        st.rerun()

# ============================================================
#  APP PRINCIPAL
# ============================================================
st.title("🛒 PUNTO DE VENTA")

# Si la caja no está abierta → mostrar pantalla de apertura
if not st.session_state.caja_abierta:
    pantalla_apertura_caja()
    st.stop()

# Caja abierta → mostrar POS
df_full = leer_catalogo()

# Separar catálogo por categoría
df_bebidas    = df_full[df_full["Categoria"].str.strip().str.lower() == "bebidas"].copy() if not df_full.empty else pd.DataFrame()
df_accesorios = df_full[df_full["Categoria"].str.strip().str.lower() == "accesorios"].copy() if not df_full.empty else pd.DataFrame()

# Tabs principales
tab_beb, tab_acc, tab_inv, tab_caja, tab_cierre = st.tabs(
    ["🥤 Bebidas", "👜 Accesorios", "📦 Inventario", "💰 Mi Caja", "🔒 Cerrar Caja"]
)

with tab_beb:
    render_pos("beb", "Bebidas", "🥤", df_bebidas, st.session_state.caja_metodos_beb)

with tab_acc:
    render_pos("acc", "Accesorios", "👜", df_accesorios, st.session_state.caja_metodos_acc)

with tab_inv:
    render_inventario()

with tab_caja:
    render_resumen_caja()

with tab_cierre:
    render_cierre_caja()
