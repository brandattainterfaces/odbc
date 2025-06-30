import streamlit as st
import pandas as pd
import mysql.connector
from io import BytesIO
from datetime import datetime, date

st.set_page_config(page_title="Glam Mayores Multiempresa", layout="wide")
st.title("Andy Web App")

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

cod_cuentas_disponibles = df['Cuenta'].dropna().unique()
cod_cuenta_input = st.sidebar.selectbox(
    "Cod Cuenta",
    options=["Todos"] + sorted(cod_cuentas_disponibles.tolist()),
    index=0
)

centros_disponibles = df['OcrCode2'].dropna().unique()
centro_input = st.sidebar.selectbox(
    "Centro de Costo",
    options=["Todos"] + sorted(centros_disponibles.tolist()),
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

# Filtro robusto: Asiento
if "Asiento" in df.columns and not df["Asiento"].dropna().empty:
    asientos_disponibles = df['Asiento'].dropna().unique()
    asiento_input = st.sidebar.selectbox(
        "Asiento",
        options=["Todos"] + sorted(asientos_disponibles.tolist()),
        index=0
    )
else:
    asiento_input = "Todos"

if desde > hasta:
    st.warning("La fecha 'Desde' debe ser anterior o igual a la fecha 'Hasta'.")
    st.stop()

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= desde) & (df['Fecha'] <= hasta)]
if cuenta_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Nomb_Cuenta'] == cuenta_input]
if cod_cuenta_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Cuenta'] == cod_cuenta_input]
if centro_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['OcrCode2'] == centro_input]
if usuario_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Usuario'] == usuario_input]
if comp_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Comp'] == comp_input]
if empresa_input != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_input]
if asiento_input != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Asiento'] == asiento_input]

anteriores = df[(df['Fecha'] < desde)]
if cuenta_input != "Todas":
    anteriores = anteriores[anteriores['Nomb_Cuenta'] == cuenta_input]
if cod_cuenta_input != "Todos":
    anteriores = anteriores[anteriores['Cuenta'] == cod_cuenta_input]
if centro_input != "Todos":
    anteriores = anteriores[anteriores['OcrCode2'] == centro_input]
if usuario_input != "Todos":
    anteriores = anteriores[anteriores['Usuario'] == usuario_input]
if comp_input != "Todos":
    anteriores = anteriores[anteriores['Comp'] == comp_input]
if empresa_input != "Todas":
    anteriores = anteriores[anteriores['Empresa'] == empresa_input]
if asiento_input != "Todos":
    anteriores = anteriores[anteriores['Asiento'] == asiento_input]

# Cálculos
suma_debe = anteriores['Debe'].sum()
suma_haber = anteriores['Haber'].sum()
inicial = suma_debe - suma_haber

# Mostrar resumen previo como métricas encima de la tabla
st.subheader("Resumen Acumulado Previo")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Acumulado Debe Previo", f"${suma_debe:,.2f}")
col2.metric("🏦 Acumulado Haber Previo", f"${suma_haber:,.2f}")
col3.metric("📊 Balance Inicial", f"${inicial:,.2f}")

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

# Mostrar resultados con formato contable en pantalla
st.subheader("Vista Previa de Resultados")
st.dataframe(
    df_filtrado.style.format({
        "Debe": "$ {:,.2f}",
        "Haber": "$ {:,.2f}",
        "Acumulado": "$ {:,.2f}"
    }),
    height=500
)

# Ajustar estilo HTML
st.markdown("""
    <style>
    .dataframe td, .dataframe th {
        font-size: 12px !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Preparar resumen para exportar (solo para Excel)
resumen_row = {
    col: "" for col in df_filtrado.columns
}
resumen_row.update({
    "Debe": suma_debe,
    "Haber": suma_haber,
    "Acumulado": inicial,
    "Bajada": "Saldos Previos" if "Bajada" in df_filtrado.columns else "Resumen"
})
df_export = pd.concat([pd.DataFrame([resumen_row]), df_filtrado], ignore_index=True)

# Exportar a Excel con formato contable
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultado')
        workbook = writer.book
        worksheet = writer.sheets['Resultado']

        # Congelar encabezado
        worksheet.freeze_panes(1, 0)

        # Fila resumen en negrita
        bold_format = workbook.add_format({'bold': True})
        worksheet.set_row(1, None, bold_format)

        # Formato contable para campos calculados
        money_format = workbook.add_format({'num_format': '#.##0,00_);[Red](#.##0,00)'})
        for col_idx, col_name in enumerate(df.columns):
            if col_name in ["Debe", "Haber", "Acumulado"]:
                worksheet.set_column(col_idx, col_idx, 15, money_format)

    return output.getvalue()

excel_data = to_excel(df_export)
st.download_button(
    label="📥 Descargar Excel",
    data=excel_data,
    file_name="resultado_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("Archivo listo para descarga.")
