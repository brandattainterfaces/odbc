import streamlit as st
import pandas as pd
import mysql.connector
from io import BytesIO
from datetime import datetime, date

st.set_page_config(page_title="Filtro Contable", layout="wide")
st.title("Filtro de Fechas - andy")

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
    st.experimental_rerun()

desde = st.sidebar.date_input("Desde", value=date_min, min_value=date_min, max_value=date_max)
hasta = st.sidebar.date_input("Hasta", value=date_max, min_value=date_min, max_value=date_max)

cuentas_disponibles = df['Nomb_Cuenta'].dropna().unique()
cuenta_input = st.sidebar.selectbox("Cuenta", ["Todas"] + sorted(cuentas_disponibles.tolist()))

usuarios_disponibles = df['Usuario'].dropna().unique()
usuario_input = st.sidebar.selectbox("Usuario", ["Todos"] + sorted(usuarios_disponibles.tolist()))

empresas_disponibles = df['Empresa'].dropna().unique()
empresa_input = st.sidebar.selectbox("Empresa", ["Todas"] + sorted(empresas_disponibles.tolist()))

comps_disponibles = df['Comp.'].dropna().unique()
comp_input = st.sidebar.selectbox("Comp.", ["Todos"] + sorted(comps_disponibles.tolist()))

if desde > hasta:
    st.warning("La fecha 'Desde' debe ser anterior o igual a la fecha 'Hasta'.")
    st.stop()

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= desde) & (df['Fecha'] <= hasta)]
if cuenta_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Nomb_Cuenta'] == cuenta_input]
if usuario_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Usuario'] == usuario_input]
if comp_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Comp.'] == comp_input]
if empresa_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_input]

anteriores = df[(df['Fecha'] < desde)]
if cuenta_input != "Todas":
    anteriores = anteriores[anteriores['Nomb_Cuenta'] == cuenta_input]
if usuario_input != "Todos":
    anteriores = anteriores[anteriores['Usuario'] == usuario_input]
if comp_input != "Todos":
    anteriores = anteriores[anteriores['Comp.'] == comp_input]
if empresa_input != "Todas":
    anteriores = anteriores[anteriores['Empresa'] == empresa_input]

# Cálculos
suma_debe = anteriores['Debe'].sum()
suma_haber = anteriores['Haber'].sum()
inicial = suma_debe - suma_haber
resumen = pd.DataFrame([{
    "Acumulado Debe Previo": suma_debe,
    "Acumulado Haber Previo": suma_haber
}])

# Calcular columna acumulada
df_filtrado = df_filtrado.copy()
df_filtrado["Acumulado"] = df_filtrado.apply(
    lambda row: row["Debe"] - row["Haber"], axis=1
).cumsum() + inicial

# Insertar columna después de "Haber"
haber_index = df_filtrado.columns.get_loc("Haber")
cols = list(df_filtrado.columns)
cols.insert(haber_index + 1, cols.pop(cols.index("Acumulado")))
df_filtrado = df_filtrado[cols]

# Combinar resultados
resultado = pd.concat([resumen, df_filtrado], ignore_index=True)

# Mostrar resultados
st.subheader("Vista Previa de Resultados")
st.dataframe(resultado, height=500)

# Ajustar tamaño de fuente para la vista previa
st.markdown("""
    <style>
    .dataframe td, .dataframe th {
        font-size: 12px !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Exportar a Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultado')
    return output.getvalue()

excel_data = to_excel(resultado)
st.download_button(
    label="📥 Descargar Excel",
    data=excel_data,
    file_name="resultado_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("Archivo listo para descarga.")
