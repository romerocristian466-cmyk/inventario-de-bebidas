import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# CONFIGURACIÓN Y BASE DE DATOS
# ==========================================
st.set_page_config(page_title="Sistema POS e Inventario", layout="wide")

def init_db():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    # Tabla Bebidas
    c.execute('''CREATE TABLE IF NOT EXISTS bebidas (
        codigo_barras TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        marca TEXT,
        mililitros INTEGER,
        fecha_caducidad DATE,
        precio REAL NOT NULL,
        stock INTEGER NOT NULL
    )''')
    # Tabla Joyería
    c.execute('''CREATE TABLE IF NOT EXISTS joyeria (
        codigo_barras TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        material TEXT,
        peso_gramos REAL,
        pureza TEXT,
        precio REAL NOT NULL,
        stock INTEGER NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

def query_db(query, params=()):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute(query, params)
    result = c.fetchall()
    conn.commit()
    conn.close()
    return result

# Inicializar el carrito en sesión
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# ==========================================
# MÓDULO 1: PUNTO DE VENTA (VENDEDORA)
# ==========================================
def modulo_ventas():
    st.title("🛒 Punto de Venta")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Escanear Producto")
        # El formulario con clear_on_submit=True limpia la caja automáticamente al disparar el escáner
        with st.form("escaner_form", clear_on_submit=True):
            # CORREGIDO: Se quitó autofocus=True que causaba el error
            codigo = st.text_input("Código de barras (Usa el escáner aquí):")
            submitted = st.form_submit_button("Agregar")
            
            if submitted and codigo:
                # Buscar en Bebidas primero
                producto = query_db("SELECT nombre, precio FROM bebidas WHERE codigo_barras=?", (codigo,))
                # Si no está, buscar en Joyería
                if not producto:
                    producto = query_db("SELECT nombre, precio FROM joyeria WHERE codigo_barras=?", (codigo,))
                
                if producto:
                    st.session_state.carrito.append({
                        "codigo": codigo,
                        "nombre": producto[0][0],
                        "precio": producto[0][1]
                    })
                    st.rerun()
                else:
                    st.error("Producto no encontrado en el inventario.")

    with col2:
        st.markdown("### Detalle de la Venta")
        if st.session_state.carrito:
            df_carrito = pd.DataFrame(st.session_state.carrito)
            df_carrito.index = df_carrito.index + 1
            st.dataframe(df_carrito, use_container_width=True)
            
            total = df_carrito['precio'].sum()
            st.markdown(f"## Total a Cobrar: ${total:.2f}")
            
            if st.button("💰 Procesar Pago (Completar Venta)"):
                # Aquí puedes agregar luego la lógica para descontar del stock físico
                st.session_state.carrito = []
                st.success("¡Venta procesada con éxito!")
                st.rerun()
        else:
            st.info("El carrito está vacío. Escanea un producto para comenzar.")

# ==========================================
# MÓDULO 2: INVENTARIO DE BEBIDAS
# ==========================================
def modulo_bebidas():
    st.title("🥤 Inventario de Bebidas")
    
    with st.expander("➕ Registrar Nueva Bebida", expanded=False):
        with st.form("form_bebida"):
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código de Barras")
            nombre = col2.text_input("Nombre del Producto")
            marca = col1.text_input("Marca")
            ml = col2.number_input("Volumen (ml)", min_value=0)
            fecha = col1.date_input("Fecha de Caducidad")
            precio = col2.number_input("Precio ($)", min_value=0.0, format="%.2f")
            stock = col1.number_input("Stock Inicial", min_value=0)
            
            if st.form_submit_button("Guardar Bebida"):
                try:
                    query_db("INSERT INTO bebidas VALUES (?,?,?,?,?,?,?)", 
                             (codigo, nombre, marca, ml, fecha, precio, stock))
                    st.success("Bebida registrada correctamente.")
                except sqlite3.IntegrityError:
                    st.error("Error: Este código de barras ya existe.")

    st.markdown("### Existencias")
    try:
        df = pd.read_sql("SELECT * FROM bebidas", sqlite3.connect("inventario.db"))
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error cargando existencias: {e}")

# ==========================================
# MÓDULO 3: INVENTARIO DE JOYERÍA
# ==========================================
def modulo_joyeria():
    st.title("💎 Inventario de Joyería")
    
    with st.expander("➕ Registrar Nueva Joya", expanded=False):
        with st.form("form_joya"):
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código de Barras / SKU")
            nombre = col2.text_input("Descripción (Ej. Cadena oro cartier)")
            material = col1.selectbox("Material", ["Oro 10k", "Oro 14k", "Oro 18k", "Plata 925", "Acero Inoxidable"])
            peso = col2.number_input("Peso (gramos)", min_value=0.0, format="%.2f")
            pureza = col1.text_input("Pureza / Detalle adicional")
            precio = col2.number_input("Precio ($)", min_value=0.0, format="%.2f")
            stock = col1.number_input("Stock Inicial", min_value=0)
            
            if st.form_submit_button("Guardar Joya"):
                try:
                    query_db("INSERT INTO joyeria VALUES (?,?,?,?,?,?,?)", 
                             (codigo, nombre, material, peso, pureza, precio, stock))
                    st.success("Joya registrada correctamente.")
                except sqlite3.IntegrityError:
                    st.error("Error: Este código de barras ya existe.")

    st.markdown("### Existencias")
    try:
        df = pd.read_sql("SELECT * FROM joyeria", sqlite3.connect("inventario.db"))
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error cargando existencias: {e}")

# ==========================================
# MENÚ DE NAVEGACIÓN
# ==========================================
st.sidebar.title("Menú Principal")
menu = st.sidebar.radio("Ir a:", ["Ventas (Escáner)", "Inventario Bebidas", "Inventario Joyería"])

if menu == "Ventas (Escáner)":
    modulo_ventas()
elif menu == "Inventario Bebidas":
    modulo_bebidas()
elif menu == "Inventario Joyería":
    modulo_joyeria()