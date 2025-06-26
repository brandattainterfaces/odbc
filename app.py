import streamlit as st
import pandas as pd
import pyodbc
from io import BytesIO
from datetime import datetime, date

st.set_page_config(page_title="Filtro Contable", layout="wide")
st.title("Filtro de Fechas - andy")

# Configurar conexión ODBC
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=clientes-dashboards.cssohkq7lsxq.us-east-1.rds.amazonaws.com;"
    "DATABASE=glam;"
    "UID=glam;"
    "PWD=glam1234;"
)

try:
    conn = pyodbc.connect(conn_str)
    query = "SELECT * FROM andy"  # Cambiar si es necesario
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

cuentas_disponibles = df['Nombre cuenta'].dropna().unique()
cuentas_seleccionadas = st.sidebar.multiselect(
    "Nombre cuenta",
    options=sorted(cuentas_disponibles.tolist()),
    default=cuentas_disponibles.tolist(),
    help="Buscá y seleccioná una o más cuentas"
)

usuario_input = st.sidebar.text_input("Filtrar por Usuario (contiene)")
comp_input = st.sidebar.text_input("Filtrar por Comp. (contiene)")

if desde > hasta:
    st.warning("La fecha 'Desde' debe ser anterior o igual a la fecha 'Hasta'.")
    st.stop()

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= desde) & (df['Fecha'] <= hasta)]
if cuentas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Nombre cuenta'].isin(cuentas_seleccionadas)]
if usuario_input:
    df_filtrado = df_filtrado[df_filtrado['Usuario'].astype(str).str.contains(usuario_input, case=False, na=False)]
if comp_input:
    df_filtrado = df_filtrado[df_filtrado['Comp.'].astype(str).str.contains(comp_input, case=False, na=False)]

anteriores = df[(df['Fecha'] < desde)]
if cuentas_seleccionadas:
    anteriores = anteriores[anteriores['Nombre cuenta'].isin(cuentas_seleccionadas)]
if usuario_input:
    anteriores = anteriores[anteriores['Usuario'].astype(str).str.contains(usuario_input, case=False, na=False)]
if comp_input:
    anteriores = anteriores[anteriores['Comp.'].astype(str).str.contains(comp_input, case=False, na=False)]

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
st.dataframe(resultado)

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
