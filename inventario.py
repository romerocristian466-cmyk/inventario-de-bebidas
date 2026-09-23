import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Soda Pro - Admin", page_icon="🥤", layout="wide")

# ==========================================
# BASE DE DATOS LOCAL
# ==========================================
def init_db():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_general (
        codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, unidad TEXT, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bebidas (
        codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, marca TEXT, mililitros INTEGER, fecha_caducidad DATE, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS joyeria (
        codigo_barras TEXT PRIMARY KEY, nombre TEXT NOT NULL, material TEXT, peso_gramos REAL, pureza TEXT, costo REAL, precio REAL NOT NULL, stock REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventas_historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE, hora TIME, codigo TEXT, producto TEXT, cantidad REAL, precio_unit REAL, total REAL, metodo_pago TEXT, cliente TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fiados (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE, hora TIME, cliente TEXT NOT NULL, detalle TEXT, total REAL NOT NULL, estado TEXT DEFAULT 'Pendiente')''')
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

st.title("🥤 SODA PRO - ADMIN")
tab_general, tab_bebidas, tab_joyeria, tab_reportes, tab_fiados = st.tabs(["📦 GENERAL", "🥤 BEBIDAS", "💎 JOYERÍA", "📈 REPORTES", "👥 FIADOS"])

# --- TAB GENERAL ---
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
    st.dataframe(pd.read_sql("SELECT * FROM inventario_general", sqlite3.connect("inventario.db")), use_container_width=True)

# --- TAB BEBIDAS ---
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
    st.dataframe(pd.read_sql("SELECT * FROM bebidas", sqlite3.connect("inventario.db")), use_container_width=True)

# --- TAB JOYERÍA ---
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
    st.dataframe(pd.read_sql("SELECT * FROM joyeria", sqlite3.connect("inventario.db")), use_container_width=True)

# --- REPORTES Y FIADOS ---
with tab_reportes:
    st.subheader("📈 Ventas Registradas")
    df_v = pd.read_sql("SELECT * FROM ventas_historial ORDER BY fecha DESC, hora DESC", sqlite3.connect("inventario.db"))
    st.metric("Total Histórico", f"${df_v['total'].sum():.2f}")
    st.dataframe(df_v, use_container_width=True)

with tab_fiados:
    st.subheader("👥 Clientes con Fiado")
    df_f = pd.read_sql("SELECT * FROM fiados WHERE estado='Pendiente'", sqlite3.connect("inventario.db"))
    st.dataframe(df_f, use_container_width=True)
    if not df_f.empty:
        cliente_pagar = st.selectbox("Liquidar deuda de:", df_f['cliente'].unique())
        if st.button("Marcar como Pagado"):
            query_db("UPDATE fiados SET estado='Pagado' WHERE cliente=?", (cliente_pagar,))
            st.success("Deuda liquidada.")
            st.rerun()