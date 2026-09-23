import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import urllib.parse

st.set_page_config(page_title="Soda Pro - POS", page_icon="🥤", layout="wide")

# ==========================================
# 1. BASE DE DATOS Y FUNCIONES COMPARTIDAS
# ==========================================
def init_db():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_general (codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, unidad TEXT, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bebidas (codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, marca TEXT, mililitros INTEGER, fecha_caducidad DATE, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS joyeria (codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, material TEXT, peso_gramos REAL, pureza TEXT, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventas_historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE, hora TIME, codigo TEXT, producto TEXT, cantidad REAL, precio_unit REAL, total REAL, metodo_pago TEXT, cliente TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fiados (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE, hora TIME, cliente TEXT NOT NULL, detalle TEXT, total REAL NOT NULL, estado TEXT DEFAULT 'Pendiente')''')
    conn.commit()
    conn.close()

init_db()

def query_db(query, params=(), fetch=False):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

def generar_codigo_ean13():
    base = '500' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    suma = sum(int(d) if i % 2 == 0 else int(d) * 3 for i, d in enumerate(base))
    checksum = (10 - (suma % 10)) % 10
    return base + str(checksum)

def obtener_catalogo_completo():
    conn = sqlite3.connect("inventario.db")
    query = '''
        SELECT codigo_barras, nombre, precio, stock, 'inventario_general' as tabla FROM inventario_general
        UNION ALL
        SELECT codigo_barras, nombre, precio, stock, 'bebidas' as tabla FROM bebidas
        UNION ALL
        SELECT codigo_barras, nombre, precio, stock, 'joyeria' as tabla FROM joyeria
    '''
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def generar_ticket(carrito_df, total, metodo, recibido=None, cambio=None, cliente=""):
    ahora = datetime.now()
    lineas = ["🥤 SODA PRO - TICKET DE VENTA", f"Fecha: {ahora.strftime('%d/%m/%Y')} {ahora.strftime('%H:%M')}", "-" * 30]
    for _, row in carrito_df.iterrows():
        lineas.append(f"{row['nombre']} (x{row['cantidad']})\n   ${row['subtotal']:.2f}")
    lineas.append("-" * 30)
    lineas.append(f"TOTAL: ${total:.2f}")
    lineas.append(f"Método: {metodo}")
    if metodo == "Efectivo" and recibido is not None:
        lineas.append(f"Recibido: ${recibido:.2f}\nCambio: ${cambio:.2f}")
    elif metodo == "Fiado":
        lineas.append(f"Cliente: {cliente}\nESTADO: PENDIENTE DE PAGO")
    lineas.append("-" * 30)
    lineas.append("¡Gracias por su preferencia!")
    return "\n".join(lineas)

# Variables de estado
if "carrito" not in st.session_state or type(st.session_state.carrito) is dict:
    st.session_state.carrito = []
if "ticket_texto" not in st.session_state:
    st.session_state.ticket_texto = None
if "ticket_link" not in st.session_state:
    st.session_state.ticket_link = None

# ==========================================
# 2. NAVEGACIÓN (SIN CONTRASEÑAS)
# ==========================================
st.sidebar.title("Navegación")
modo = st.sidebar.radio("Ir a:", ["🛒 Punto de Venta (Vendedora)", "⚙️ Administrador"])

# ==========================================
# 3. MÓDULO VENDEDORA
# ==========================================
if modo == "🛒 Punto de Venta (Vendedora)":
    st.title("🛒 PUNTO DE VENTA")

    if st.session_state.ticket_texto:
        st.success("### 🎉 ¡VENTA PROCESADA EXITOSAMENTE!")
        st.markdown(f'<div style="background:#f0f2f6; padding:20px; border-radius:10px; font-family:monospace; white-space:pre-wrap; color:#000; margin-bottom:20px;">{st.session_state.ticket_texto}</div>', unsafe_allow_html=True)
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.link_button("📲 Enviar por WhatsApp", st.session_state.ticket_link, use_container_width=True)
        with col_t2:
            if st.button("🆕 NUEVA VENTA", type="primary", use_container_width=True):
                st.session_state.ticket_texto = None
                st.session_state.ticket_link = None
                st.rerun()
        st.stop()

    def procesar_escaneo():
        codigo = st.session_state.escaner_input.strip()
        if codigo:
            encontrado = False
            for tabla in ["inventario_general", "bebidas", "joyeria"]:
                prod = query_db(f"SELECT nombre, precio, stock FROM {tabla} WHERE codigo_barras=?", (codigo,), fetch=True)
                if prod:
                    st.session_state.carrito.append({"codigo": codigo, "nombre": prod[0][0], "precio": prod[0][1], "tabla": tabla})
                    encontrado = True
                    break
            if not encontrado:
                st.error(f"El código {codigo} no existe en el inventario.")
        st.session_state.escaner_input = ""

    st.markdown("### 📷 ESCANEA EL PRODUCTO")
    st.text_input("Apunta el escáner (o escribe el código y presiona Enter):", key="escaner_input", on_change=procesar_escaneo)

    st.markdown("---")
    st.markdown("### 🔎 BÚSQUEDA MANUAL")
    catalogo_df = obtener_catalogo_completo()

    if not catalogo_df.empty:
        opciones = ["--- Selecciona un producto ---"] + catalogo_df["nombre"].tolist()
        seleccion = st.selectbox("Busca por nombre:", opciones)
        if seleccion != "--- Selecciona un producto ---":
            if st.button("➕ Agregar al carrito", use_container_width=True):
                fila = catalogo_df[catalogo_df["nombre"] == seleccion].iloc[0]
                st.session_state.carrito.append({"codigo": fila["codigo_barras"], "nombre": fila["nombre"], "precio": fila["precio"], "tabla": fila["tabla"]})
                st.rerun()
    else:
        st.info("El inventario está vacío. Ve al módulo Administrador para cargar productos.")

    st.markdown("---")
    if st.session_state.carrito:
        df_carrito = pd.DataFrame(st.session_state.carrito)
        carrito_agrupado = df_carrito.groupby(["codigo", "nombre", "precio", "tabla"]).size().reset_index(name='cantidad')
        carrito_agrupado['subtotal'] = carrito_agrupado['cantidad'] * carrito_agrupado['precio']
        
        st.markdown("### 🛒 CARRITO DE COMPRAS")
        st.dataframe(carrito_agrupado[["nombre", "cantidad", "subtotal"]], use_container_width=True, hide_index=True)
        total = carrito_agrupado['subtotal'].sum()
        st.markdown(f"<h2 style='color: #10b981;'>Total a Cobrar: ${total:.2f}</h2>", unsafe_allow_html=True)
        
        st.markdown("### 💳 MÉTODO DE PAGO")
        metodo_pago = st.radio("Método:", ["Efectivo", "Transferencia", "Fiado"], horizontal=True)
        
        puede_cobrar = True
        cliente, monto_recibido, cambio = "", None, None
        
        if metodo_pago == "Efectivo":
            monto_recibido = st.number_input("💵 Monto recibido:", min_value=0.0, value=float(total), step=1.0)
            cambio = monto_recibido - total
            if monto_recibido < total:
                st.warning(f"⚠️ Faltan ${abs(cambio):.2f}")
                puede_cobrar = False
            else:
                st.success(f"💰 Cambio a devolver: **${cambio:.2f}**")
        elif metodo_pago == "Fiado":
            cliente = st.text_input("👤 Nombre del cliente (Requerido para Fiado):")
            if not cliente.strip():
                st.warning("⚠️ Escribe el nombre del cliente para dejarlo fiado.")
                puede_cobrar = False
            else:
                st.info(f"📝 Esta venta quedará como deuda de **{cliente}**")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with col2:
            if st.button("✅ COBRAR", type="primary", use_container_width=True, disabled=not puede_cobrar):
                ahora = datetime.now()
                detalle_fiado = ""
                for _, row in carrito_agrupado.iterrows():
                    query_db(f"UPDATE {row['tabla']} SET stock = stock - ? WHERE codigo_barras=?", (row['cantidad'], row['codigo']))
                    query_db("INSERT INTO ventas_historial (fecha, hora, codigo, producto, cantidad, precio_unit, total, metodo_pago, cliente) VALUES (?,?,?,?,?,?,?,?,?)",
                             (ahora.date(), ahora.strftime("%H:%M:%S"), row['codigo'], row['nombre'], row['cantidad'], row['precio'], row['subtotal'], metodo_pago, cliente))
                    detalle_fiado += f"{row['nombre']} x{row['cantidad']}, "
                if metodo_pago == "Fiado":
                    query_db("INSERT INTO fiados (fecha, hora, cliente, detalle, total) VALUES (?,?,?,?,?)",
                             (ahora.date(), ahora.strftime("%H:%M:%S"), cliente, detalle_fiado, total))
                
                ticket_str = generar_ticket(carrito_agrupado, total, metodo_pago, monto_recibido, cambio, cliente)
                st.session_state.ticket_texto = ticket_str
                st.session_state.ticket_link = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(ticket_str)
                st.session_state.carrito = []
                st.rerun()


# ==========================================
# 4. MÓDULO ADMINISTRADOR
# ==========================================
elif modo == "⚙️ Administrador":
    st.title("🥤 SODA PRO - ADMIN")
    tab_general, tab_bebidas, tab_joyeria, tab_reportes, tab_fiados = st.tabs(["📦 GENERAL", "🥤 BEBIDAS", "💎 JOYERÍA", "📈 REPORTES", "👥 FIADOS"])

    with tab_general:
        st.subheader("📦 Inventario General")
        with st.form("form_general", clear_on_submit=True):
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código (Vacio=Auto)")
            nombre = col2.text_input("Nombre")
            unidad = col1.selectbox("Unidad", ["Unidades", "Libras", "Kilos", "Paquete"])
            costo = col1.number_input("Costo", min_value=0.0)
            precio = col2.number_input("Precio", min_value=0.0)
            stock = col2.number_input("Stock Inicial", min_value=0.0)
            if st.form_submit_button("Agregar Producto"):
                cod = codigo.strip() or generar_codigo_ean13()
                try:
                    query_db("INSERT INTO inventario_general VALUES (?,?,?,?,?,?)", (cod, nombre, unidad, costo, precio, stock))
                    st.success(f"Guardado. Código: {cod}")
                except: st.error("El código ya existe.")
                
        st.markdown("---")
        with st.expander("📥 Carga Masiva (Importar Inventario Anterior)"):
            st.info("Sube aquí el archivo .csv descargado de tu Google Sheets.")
            archivo_csv = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
            if archivo_csv:
                if st.button("Cargar a la Base de Datos", type="primary"):
                    try:
                        df_import = pd.read_csv(archivo_csv, dtype=str) 
                        conn = sqlite3.connect("inventario.db")
                        c = conn.cursor()
                        agregados = 0
                        for _, row in df_import.iterrows():
                            cod = str(row.get("Codigo", generar_codigo_ean13())).strip()
                            if cod == "nan" or not cod: cod = generar_codigo_ean13()
                            nom = str(row.get("Producto", "Sin nombre")).strip()
                            if nom == "nan": nom = "Sin nombre"
                            uni = str(row.get("Unidad", "Unidades")).strip()
                            if uni == "nan": uni = "Unidades"
                            def limpiar_numero(val):
                                if pd.isna(val) or val == "nan" or not str(val).strip(): return 0.0
                                try: return float(str(val).replace("$", "").replace(",", ".").strip())
                                except: return 0.0
                            cost = limpiar_numero(row.get("Costo", 0))
                            prec = limpiar_numero(row.get("Precio_Venta", 0))
                            stk = limpiar_numero(row.get("Stock", 0))
                            try:
                                c.execute("INSERT INTO inventario_general VALUES (?,?,?,?,?,?)", (cod, nom, uni, cost, prec, stk))
                                agregados += 1
                            except sqlite3.IntegrityError: pass 
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Se cargaron {agregados} productos exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al leer el archivo: {e}")

        st.markdown("---")
        try:
            st.dataframe(pd.read_sql("SELECT * FROM inventario_general", sqlite3.connect("inventario.db")), use_container_width=True)
        except: pass

    with tab_bebidas:
        st.subheader("🥤 Inventario de Bebidas")
        with st.form("form_bebidas", clear_on_submit=True):
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código de Barras")
            nombre = col2.text_input("Nombre Bebida")
            marca = col1.text_input("Marca")
            ml = col2.number_input("Mililitros", min_value=0)
            fecha = col1.date_input("Caducidad")
            costo = col2.number_input("Costo", min_value=0.0)
            precio = col1.number_input("Precio", min_value=0.0)
            stock = col2.number_input("Stock", min_value=0.0)
            if st.form_submit_button("Agregar Bebida"):
                cod = codigo.strip() or generar_codigo_ean13()
                try:
                    query_db("INSERT INTO bebidas VALUES (?,?,?,?,?,?,?,?)", (cod, nombre, marca, ml, fecha, costo, precio, stock))
                    st.success("Bebida guardada.")
                except: st.error("El código ya existe.")
        try:
            st.dataframe(pd.read_sql("SELECT * FROM bebidas", sqlite3.connect("inventario.db")), use_container_width=True)
        except: pass

    with tab_joyeria:
        st.subheader("💎 Inventario de Joyería")
        with st.form("form_joya", clear_on_submit=True):
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código / SKU")
            nombre = col2.text_input("Descripción")
            material = col1.selectbox("Material", ["Oro 10k", "Oro 14k", "Plata 925", "Acero"])
            peso = col2.number_input("Peso (g)", min_value=0.0)
            pureza = col1.text_input("Pureza/Detalle")
            costo = col2.number_input("Costo", min_value=0.0)
            precio = col1.number_input("Precio", min_value=0.0)
            stock = col2.number_input("Stock", min_value=0.0)
            if st.form_submit_button("Agregar Joya"):
                cod = codigo.strip() or generar_codigo_ean13()
                try:
                    query_db("INSERT INTO joyeria VALUES (?,?,?,?,?,?,?,?)", (cod, nombre, material, peso, pureza, costo, precio, stock))
                    st.success("Joya guardada.")
                except: st.error("El código ya existe.")
        try:
            st.dataframe(pd.read_sql("SELECT * FROM joyeria", sqlite3.connect("inventario.db")), use_container_width=True)
        except: pass

    with tab_reportes:
        st.subheader("📈 Ventas Registradas")
        try:
            df_v = pd.read_sql("SELECT * FROM ventas_historial ORDER BY fecha DESC, hora DESC", sqlite3.connect("inventario.db"))
            st.metric("Total Histórico", f"${df_v['total'].sum():.2f}")
            st.dataframe(df_v, use_container_width=True)
        except:
            st.info("Aún no hay ventas registradas.")

    with tab_fiados:
        st.subheader("👥 Clientes con Fiado")
        try:
            df_f = pd.read_sql("SELECT * FROM fiados WHERE estado='Pendiente'", sqlite3.connect("inventario.db"))
            st.dataframe(df_f, use_container_width=True)
            if not df_f.empty:
                cliente_pagar = st.selectbox("Liquidar deuda de:", df_f['cliente'].unique())
                if st.button("Marcar como Pagado"):
                    query_db("UPDATE fiados SET estado='Pagado' WHERE cliente=?", (cliente_pagar,))
                    st.success("Deuda liquidada.")
                    st.rerun()
        except:
            st.info("Aún no hay fiados pendientes.")