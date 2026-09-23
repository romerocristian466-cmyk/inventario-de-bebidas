import streamlit as st
import pandas as pd
import sqlite3
import streamlit.components.v1 as components
from datetime import datetime

# Función auxiliar para conectar a la DB
def ejecutar_query(query, params=(), fetch=False):
    conn = sqlite3.connect("inventario.db") # Asegúrate de usar la ruta correcta a tu DB
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

def page_punto_de_venta():
    st.title("🛒 Punto de Venta Rápido")

    # 1. Inicializar el carrito en la sesión si no existe
    if "carrito" not in st.session_state:
        st.session_state.carrito = {} # Usamos diccionario para agrupar cantidades rápido por código

    # 2. HACK PRO: Inyectar JavaScript para forzar el Autofocus en el campo del escáner
    components.html(
        """
        <script>
        const doc = window.parent.document;
        // Busca el primer input de texto en la pantalla y lo enfoca continuamente
        function setFocus() {
            const input = doc.querySelector('input[aria-label="Código de Barras (Escáner)"]');
            if(input) { input.focus(); }
        }
        setInterval(setFocus, 1000); // Re-enfoca cada segundo por si la vendedora da clic fuera
        </script>
        """,
        height=0
    )

    col_escaner, col_carrito = st.columns([1, 2])

    with col_escaner:
        st.markdown("### 🔍 Lector")
        st.info("El cursor está fijado automáticamente. Solo dispara el escáner.")
        
        # Formulario con clear_on_submit=True para lectura a ráfagas
        with st.form("escaner_form", clear_on_submit=True):
            codigo_ingresado = st.text_input("Código de Barras (Escáner)", label_visibility="collapsed", placeholder="Dispara el escáner aquí...")
            btn_agregar = st.form_submit_button("Agregar (Enter)", use_container_width=True)

            if btn_agregar and codigo_ingresado:
                codigo = codigo_ingresado.strip()
                
                # Buscar en Bebidas primero
                producto = ejecutar_query("SELECT nombre, precio, stock FROM bebidas WHERE codigo_barras=?", (codigo,), fetch=True)
                tabla_origen = "bebidas"
                
                # Si no está en Bebidas, buscar en Joyería
                if not producto:
                    producto = ejecutar_query("SELECT nombre, precio, stock FROM joyeria WHERE codigo_barras=?", (codigo,), fetch=True)
                    tabla_origen = "joyeria"

                if producto:
                    nombre, precio, stock_disponible = producto[0]
                    
                    # Calcular cuántos hay ya en el carrito para no exceder el stock físico
                    cantidad_en_carrito = st.session_state.carrito.get(codigo, {}).get("cantidad", 0)
                    
                    if cantidad_en_carrito < stock_disponible:
                        if codigo in st.session_state.carrito:
                            st.session_state.carrito[codigo]["cantidad"] += 1
                            st.session_state.carrito[codigo]["subtotal"] = st.session_state.carrito[codigo]["cantidad"] * precio
                        else:
                            st.session_state.carrito[codigo] = {
                                "nombre": nombre,
                                "precio": precio,
                                "cantidad": 1,
                                "subtotal": precio,
                                "origen": tabla_origen
                            }
                        st.rerun()
                    else:
                        st.error(f"¡Stock insuficiente! Solo quedan {stock_disponible} unidades de {nombre}.")
                else:
                    st.error("❌ Producto no encontrado.")

    with col_carrito:
        st.markdown("### 🛍️ Detalle de Venta")
        
        if st.session_state.carrito:
            # Convertir el diccionario a DataFrame para mostrarlo bonito
            df_carrito = pd.DataFrame(st.session_state.carrito.values())
            # Reordenar y renombrar columnas para la vendedora
            df_mostrar = df_carrito[["nombre", "precio", "cantidad", "subtotal"]]
            df_mostrar.columns = ["Producto", "Precio Unitario", "Cantidad", "Subtotal"]
            
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            total_pagar = df_carrito["subtotal"].sum()
            
            st.markdown(f"<h2 style='text-align: right; color: #10b981;'>Total a Cobrar: ${total_pagar:.2f}</h2>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🗑️ Vaciar Carrito", use_container_width=True):
                    st.session_state.carrito = {}
                    st.rerun()
                    
            with col_btn2:
                if st.button("💰 PROCESAR PAGO", type="primary", use_container_width=True):
                    # Iniciar transacción segura para descontar stock
                    conn = sqlite3.connect("inventario.db")
                    c = conn.cursor()
                    try:
                        for cod, data in st.session_state.carrito.items():
                            tabla = data["origen"]
                            cantidad_vendida = data["cantidad"]
                            
                            # Actualizar stock dinámicamente según la tabla origen
                            c.execute(f"UPDATE {tabla} SET stock = stock - ? WHERE codigo_barras = ?", 
                                      (cantidad_vendida, cod))
                        
                        # Aquí podrías insertar la transacción en una tabla 'ventas_historial'
                        # c.execute("INSERT INTO ventas (total, fecha) VALUES (?, ?)", (total_pagar, datetime.now()))
                        
                        conn.commit()
                        st.session_state.carrito = {} # Limpiar carrito tras pago exitoso
                        st.success("✅ Venta procesada y stock descontado.")
                        # Usar time.sleep(1.5) aquí si quieres que vea el mensaje antes de recargar
                        st.rerun()
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error crítico al procesar: {e}")
                    finally:
                        conn.close()
        else:
            st.info("El carrito está vacío. Escanea el primer producto.")