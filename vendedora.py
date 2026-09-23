import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Punto de Venta", page_icon="🛒", layout="centered")

def query_db(query, params=(), fetch=False):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

if "carrito" not in st.session_state or type(st.session_state.carrito) is dict:
    st.session_state.carrito = []

def procesar_escaneo():
    codigo = st.session_state.escaner_input.strip()
    if codigo:
        # Buscar en las tres tablas
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
            st.error("Producto no encontrado")
    # Limpiar caja de texto automáticamente
    st.session_state.escaner_input = ""

st.title("🛒 PUNTO DE VENTA")

st.markdown("### 📷 ESCANEA EL PRODUCTO")
# El evento on_change hace que al escanear, se agregue directo al carrito
st.text_input("Apunta el escáner:", key="escaner_input", on_change=procesar_escaneo)

if st.session_state.carrito:
    df_carrito = pd.DataFrame(st.session_state.carrito)
    
    # Agrupar items repetidos
    carrito_agrupado = df_carrito.groupby(["codigo", "nombre", "precio", "tabla"]).size().reset_index(name='cantidad')
    carrito_agrupado['subtotal'] = carrito_agrupado['cantidad'] * carrito_agrupado['precio']
    
    st.markdown("### 🛒 CARRITO")
    st.dataframe(carrito_agrupado[["nombre", "cantidad", "subtotal"]], use_container_width=True)
    
    total = carrito_agrupado['subtotal'].sum()
    st.markdown(f"## Total a Cobrar: ${total:.2f}")
    
    metodo_pago = st.radio("Método:", ["Efectivo", "Transferencia", "Fiado"], horizontal=True)
    cliente = st.text_input("Nombre del cliente (Solo para Fiado):") if metodo_pago == "Fiado" else ""
    
    col1, col2 = st.columns(2)
    if col1.button("❌ CANCELAR", use_container_width=True):
        st.session_state.carrito = []
        st.rerun()
        
    if col2.button("✅ COBRAR", type="primary", use_container_width=True):
        if metodo_pago == "Fiado" and not cliente:
            st.error("Ingresa el nombre del cliente.")
        else:
            ahora = datetime.now()
            detalle_fiado = ""
            for _, row in carrito_agrupado.iterrows():
                # Descontar stock físico
                query_db(f"UPDATE {row['tabla']} SET stock = stock - ? WHERE codigo_barras=?", (row['cantidad'], row['codigo']))
                # Registrar historial
                query_db("INSERT INTO ventas_historial (fecha, hora, codigo, producto, cantidad, precio_unit, total, metodo_pago, cliente) VALUES (?,?,?,?,?,?,?,?,?)",
                         (ahora.date(), ahora.strftime("%H:%M:%S"), row['codigo'], row['nombre'], row['cantidad'], row['precio'], row['subtotal'], metodo_pago, cliente))
                detalle_fiado += f"{row['nombre']} x{row['cantidad']}, "
            
            if metodo_pago == "Fiado":
                query_db("INSERT INTO fiados (fecha, hora, cliente, detalle, total) VALUES (?,?,?,?,?)",
                         (ahora.date(), ahora.strftime("%H:%M:%S"), cliente, detalle_fiado, total))
            
            st.session_state.carrito = []
            st.success("✅ Venta completada!")
else:
    st.info("El carrito está vacío.")