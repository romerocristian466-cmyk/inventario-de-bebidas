import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import urllib.parse

st.set_page_config(page_title="Soda Pro", page_icon="🥤", layout="wide")

# ==========================================
# 1. SISTEMA DE LOGIN
# ==========================================
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    st.markdown("""
        <div style='text-align:center; padding: 50px;'>
            <h1>🥤 SODA PRO</h1>
            <p>Inicia sesión para continuar</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                # Credenciales (puedes cambiarlas luego)
                if usuario == "admin" and clave == "admin123":
                    st.session_state.usuario_actual = "admin"
                    st.rerun()
                elif usuario == "venta" and clave == "venta123":
                    st.session_state.usuario_actual = "vendedora"
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# Botón para cerrar sesión (visible para ambos)
st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.pop("usuario_actual"))

# ==========================================
# 2. FUNCIONES DE BASE DE DATOS COMPARTIDAS
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

# ==========================================
# 3. ENRUTADOR DE PANTALLAS
# ==========================================
if st.session_state.usuario_actual == "admin":
    # ---------------------------------------------------------
    # AQUÍ PEGAS TODO EL CÓDIGO DEL ADMINISTRADOR (inventario 1.py)
    # (Desde donde dice "st.title('🥤 SODA PRO - ADMIN')" hacia abajo)
    # ---------------------------------------------------------
    st.title("🥤 SODA PRO - ADMIN")
    st.info("Pega aquí la lógica del administrador")
    
elif st.session_state.usuario_actual == "vendedora":
    # ---------------------------------------------------------
    # AQUÍ PEGAS TODO EL CÓDIGO DE LA VENDEDORA (vendedora 1.py)
    # (Desde donde dice "st.title('🛒 PUNTO DE VENTA')" hacia abajo)
    # ---------------------------------------------------------
    st.title("🛒 PUNTO DE VENTA")
    st.info("Pega aquí la lógica de la vendedora")