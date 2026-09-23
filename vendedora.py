import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Punto de Venta", page_icon="🛒", layout="centered")

# ==========================================
# FUNCIONES DE BASE DE DATOS
# ==========================================
def query_db(query, params=(), fetch=False):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

def obtener_catalogo_completo():
    """Extrae todos los productos de las 3 tablas para el buscador manual"""
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

# Inicializar carrito
if "carrito" not in st.session_state or type(st.session_state.carrito) is dict:
    st.session_state.carrito = []

def procesar_escaneo():
    codigo = st.session_state.escaner_input.strip()
    if codigo:
        tablas = ["inventario_general", "bebidas", "joyeria"]
        encontrado = False
        for tabla in tablas:
            prod = query_db(f"SELECT nombre, precio, stock FROM {tabla} WHERE codigo_barras=?", (codigo,), fetch=True)
            if prod:
                st.session_state.carrito.append({
                    "codigo": codigo, "nombre": prod[0][0], "precio": prod[0][1], "tabla": tabla
                })
                encontrado = True
                break
        if not encontrado:
            st.error(f"El código {codigo} no existe en el inventario.")
    st.session_state.escaner_input = ""

# ==========================================
# INTERFAZ DE LA VENDEDORA
# ==========================================
st.title("🛒 PUNTO DE VENTA")

# 1. ESCÁNER RÁPIDO
st.markdown("### 📷 ESCANEA EL PRODUCTO")
st.text_input("Apunta el escáner (o escribe el código y presiona Enter):", key="escaner_input", on_change=procesar_escaneo)

st.markdown("---")

# 2. BÚSQUEDA MANUAL POR NOMBRE (Visible en todo momento)
st.markdown("### 🔎 BÚSQUEDA MANUAL")
catalogo_df = obtener_catalogo_completo()

if not catalogo_df.empty:
    opciones = ["--- Selecciona un producto ---"] + catalogo_df["nombre"].tolist()
    seleccion = st.selectbox("Busca por nombre si no tienes el código o el escáner falló:", opciones)
    
    if seleccion != "--- Selecciona un producto ---":
        if st.button("➕ Agregar al carrito", type="secondary", use_container_width=True):
            fila = catalogo_df[catalogo_df["nombre"] == seleccion].iloc[0]
            st.session_state.carrito.append({
                "codigo": fila["codigo_barras"], 
                "nombre": fila["nombre"], 
                "precio": fila["precio"], 
                "tabla": fila["tabla"]
            })
            st.rerun()
else:
    st.info("El inventario está vacío. Pídele al administrador que registre productos.")

st.markdown("---")

# 3. CARRITO Y COBRO (Solo aparece si hay productos)
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
    cliente = ""
    
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
    
    # BOTONES DE ACCIÓN
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
            
            st.session_state.carrito = []
            st.success(f"✅ Venta procesada exitosamente por ${total:.2f}")
            st.rerun()