import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ============================================================
#  CONFIGURACIÓN
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

st.set_page_config(page_title="Inventario de Bebidas", page_icon="🥤", layout="wide")

# ============================================================
#  GOOGLE SHEETS
# ============================================================
def get_worksheet():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    return sh.get_worksheet(0)

@st.cache_data(ttl=30)
def leer_datos():
    ws = get_worksheet()
    registros = ws.get_all_records()
    if registros:
        return pd.DataFrame(registros)
    return pd.DataFrame(columns=["Codigo", "Producto", "Stock", "Ultima_Actualizacion"])

def guardar_datos(df):
    ws = get_worksheet()
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

# ============================================================
#  INTERFAZ
# ============================================================
st.title("🥤 Inventario de Bebidas")
menu = ["📦 Ver Stock", "➕ Ingreso (Entrada)", "🛒 Venta (Salida)"]
opcion = st.sidebar.selectbox("¿Qué deseas hacer?", menu)
st.sidebar.markdown("---")
st.sidebar.caption("Sistema de inventario en la nube")

if opcion == "📦 Ver Stock":
    st.subheader("📦 Stock Actual")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
    df = leer_datos()
    if df.empty:
        st.info("No hay productos registrados todavía.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total productos", len(df))
        try:
            col2.metric("Unidades totales", int(df["Stock"].astype(int).sum()))
            bajo_stock = df[df["Stock"].astype(int) <= 5]
            col3.metric("⚠️ Bajo stock (≤5)", len(bajo_stock))
        except:
            pass
        st.dataframe(df, use_container_width=True)
        try:
            if not bajo_stock.empty:
                st.warning("⚠️ Productos con stock bajo:")
                st.dataframe(bajo_stock[["Producto", "Stock"]], use_container_width=True)
        except:
            pass

else:
    es_venta = "Venta" in opcion
    icono = "🛒" if es_venta else "➕"
    st.subheader(f"{icono} {'Registrar Venta' if es_venta else 'Registrar Ingreso'}")
    df = leer_datos()

    if df.empty:
        st.warning("⚠️ No hay productos registrados. Primero crea productos en 'Ver Stock'.")
    else:
        # Dropdown de productos
        opciones = ["--- Selecciona un producto ---"] + df["Producto"].tolist()
        producto_seleccionado = st.selectbox("Producto:", opciones)

        if producto_seleccionado != "--- Selecciona un producto ---":
            # Obtener datos del producto seleccionado
            fila = df[df["Producto"] == producto_seleccionado].iloc[0]
            codigo = fila["Codigo"]
            stock_actual = int(fila["Stock"])

            st.info(f"📦 Código: **{codigo}** | Stock actual: **{stock_actual}** unidades")

            cantidad = st.number_input("Cantidad:", min_value=1, value=1)

            # Validación para ventas
            if es_venta and cantidad > stock_actual:
                st.error(f"❌ Stock insuficiente. Disponible: {stock_actual} unidades")
            else:
                if st.button(f"{'🛒 Confirmar Venta' if es_venta else '➕ Confirmar Ingreso'}", type="primary"):
                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                    ajuste = -cantidad if es_venta else cantidad
                    nuevo_stock = stock_actual + ajuste

                    df.loc[df["Producto"] == producto_seleccionado, "Stock"] = nuevo_stock
                    df.loc[df["Producto"] == producto_seleccionado, "Ultima_Actualizacion"] = ahora

                    guardar_datos(df)
                    st.cache_data.clear()
                    st.balloons()
                    st.success(f"✅ ¡{producto_seleccionado} actualizado! Nuevo stock: {nuevo_stock}")
