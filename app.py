import streamlit as st
import pandas as pd
import mysql.connector
from io import BytesIO
from datetime import datetime, date

st.set_page_config(page_title="Filtro Contable", layout="wide")
st.title("Andy Web App Multiempresa")

# Configurar conexión MySQL (puerto 3306)
try:
    conn = mysql.connector.connect(
        host="clientes-dashboards.cssohkq7lsxq.us-east-1.rds.amazonaws.com",
        user="glam",
        password="glam1234",
        database="glam",
        port=3306
    )
    query = "SELECT * FROM andy"
    df = pd.read_sql(query, conn)
    conn.close()
except Exception as e:
    st.error(f"Error al conectar a la base de datos: {e}")
    st.stop()

# Asegurar que las fechas sean objetos datetime.date
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
df = df.dropna(subset=['Fecha'])
df['Fecha'] = df['Fecha'].dt.date

# Fecha mínima y máxima para limitar selección
date_min = df['Fecha'].min()
date_max = df['Fecha'].max()
date_min = date_min if isinstance(date_min, date) else date_min.date()
date_max = date_max if isinstance(date_max, date) else date_max.date()

# Widgets para seleccionar filtros
st.sidebar.header("Filtros")
if st.sidebar.button("🔄 Limpiar filtros"):
    st.session_state.clear()
    st.rerun()

desde = st.sidebar.date_input("Desde", value=date_min, min_value=date_min, max_value=date_max)
hasta = st.sidebar.date_input("Hasta", value=date_max, min_value=date_min, max_value=date_max)

cuentas_disponibles = df['Nomb_Cuenta'].dropna().unique()
cuenta_input = st.sidebar.selectbox(
    "Cuenta",
    options=["Todas"] + sorted(cuentas_disponibles.tolist()),
    index=0
)

# 🚨 NUEVO FILTRO: Cod Cuenta
cod_cuentas_disponibles = df['Cuenta'].dropna().unique()
cod_cuenta_input = st.sidebar.selectbox(
    "Cod Cuenta",
    options=["Todos"] + sorted(cod_cuentas_disponibles.tolist()),
    index=0
)

usuarios_disponibles = df['Usuario'].dropna().unique()
usuario_input = st.sidebar.selectbox(
    "Usuario",
    options=["Todos"] + sorted(usuarios_disponibles.tolist()),
    index=0
)

empresas_disponibles = df['Empresa'].dropna().unique()
empresa_input = st.sidebar.selectbox(
    "Empresa",
    options=["Todas"] + sorted(empresas_disponibles.tolist()),
    index=0
)

comps_disponibles = df['Comp'].dropna().unique()
comp_input = st.sidebar.selectbox(
    "Comp",
    options=["Todos"] + sorted(comps_disponibles.tolist()),
    index=0
)

if desde > hasta:
    st.warning("La fecha 'Desde' debe ser anterior o igual a la fecha 'Hasta'.")
    st.stop()

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= desde) & (df['Fecha'] <= hasta)]
if cuenta_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Nomb_Cuenta'] == cuenta_input]
if cod_cuenta_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Cuenta'] == cod_cuenta_input]
if usuario_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Usuario'] == usuario_input]
if comp_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Comp'] == comp_input]
if empresa_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_input]

anteriores = df[(df['Fecha'] < desde)]
if cuenta_input != "Todas":
    anteriores = anteriores[anteriores['Nomb_Cuenta'] == cuenta_input]
if cod_cuenta_input != "Todos":
    anteriores = anteriores[anteriores['Cuenta'] == cod_cuenta_input]
if usuario_input != "Todos":
    anteriores = anteriores[anteriores['Usuario'] == usuario_input]
if comp_input != "Todos":
    anteriores = anteriores[anteriores['Comp'] == comp_input]
if empresa_input != "Todas":
    anteriores = anteriores[anteriores['Empresa'] == empresa_input]

# Mostrar por ahora solo resultados filtrados
st.subheader("Vista Previa de Resultados")
st.dataframe(df_filtrado, height=500)


