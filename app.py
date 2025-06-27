
import streamlit as st
import pandas as pd
import re
from io import StringIO

st.set_page_config(page_title="Auditoría de Grupo WhatsApp", layout="wide")
st.title("📋 Auditoría de Grupo de WhatsApp")

uploaded_file = st.file_uploader("Sube el archivo .txt exportado desde WhatsApp", type=["txt"])

st.sidebar.header("⚙️ Categorías personalizadas")
raw_rules = st.sidebar.text_area(
    "Definí tus categorías (una por línea, formato: Nombre: palabra1, palabra2)",
    """
Anular Factura: anular factura
Crear Factura: crear factura
Anulación: anular, anuló
Cambio de exámenes: cambio examen, examenes
Descuentos: descuento
Eliminación: eliminar, eliminación
Montos: monto, importe
Errores: error, fallo
Matrícula: matricula, matrícula
Resuelto Soporte: listo, Ya
Imagen: <Multimedia omitido>
Otros:
""".strip()
)

def parse_rules(text):
    rules = {}
    for line in text.strip().split("\n"):
        if ":" in line:
            cat, palabras = line.split(":", 1)
            rules[cat.strip()] = [p.strip().lower() for p in palabras.split(",") if p.strip()]
    return rules

rules_dict = parse_rules(raw_rules)

def categorizar_dinamico(mensaje):
    mensaje = mensaje.lower()
    for categoria, palabras in rules_dict.items():
        if any(palabra in mensaje for palabra in palabras):
            return categoria
    return "Otros"

if uploaded_file:
    # Leer contenido del archivo con soporte para UTF-8 y UTF-16
    raw_bytes = uploaded_file.getvalue()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("utf-16")

    # Patrones flexibles para distintas versiones de exportación
    pattern1 = r'(\d{1,2}/\d{1,2}/\d{4}), (\d{2}:\d{2}) - ([^:]+): (.+)'
    pattern2 = r'\[(\d{1,2}/\d{1,2}/\d{4}) (\d{2}:\d{2})\] ([^:]+): (.+)'

    matches1 = re.findall(pattern1, text)
    matches2 = re.findall(pattern2, text)
    matches = matches1 + matches2

    st.write(f"📌 Mensajes detectados: {len(matches)}")

    records = []
    for fecha, hora, usuario, mensaje in matches:
        categoria = categorizar_dinamico(mensaje)
        records.append({
            'Fecha': fecha,
            'Hora': hora,
            'Usuario': usuario,
            'Mensaje': mensaje,
            'Categoría': categoria
        })

    df = pd.DataFrame(records)
    df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d/%m/%Y", errors='coerce')

    st.subheader("📊 Resumen General")
    st.dataframe(df)

    st.subheader("🔎 Conteo por Categoría")
    resumen_cat = df['Categoría'].value_counts().reset_index()
    resumen_cat.columns = ['Categoría', 'Cantidad']
    st.dataframe(resumen_cat)

    st.subheader("👤 Actividad por Usuario")
    resumen_usr = df['Usuario'].value_counts().reset_index()
    resumen_usr.columns = ['Usuario', 'Mensajes']
    st.dataframe(resumen_usr)

    st.subheader("📑 Filtrar mensajes")
    col1, col2, col3 = st.columns(3)

    with col1:
        año = st.selectbox("Filtrar por año", ["Todos"] + sorted(df['Fecha'].dt.year.dropna().unique().astype(str).tolist()))
    with col2:
        mes = st.selectbox("Filtrar por mes", ["Todos"] + sorted(df['Fecha'].dt.strftime('%B').dropna().unique().tolist()))
    with col3:
        fecha_especifica = st.date_input("Filtrar por fecha específica", value=None)

    if año != "Todos":
        df = df[df['Fecha'].dt.year.astype(str) == año]
    if mes != "Todos":
        df = df[df['Fecha'].dt.strftime('%B') == mes]
    if fecha_especifica:
        df = df[df['Fecha'].dt.date == fecha_especifica]

    usuario = st.selectbox("Filtrar por usuario", ["Todos"] + df['Usuario'].unique().tolist())
    categoria = st.selectbox("Filtrar por categoría", ["Todos"] + df['Categoría'].unique().tolist())
    palabra = st.text_input("Buscar palabra clave")

    filtrado = df.copy()
    if usuario != "Todos":
        filtrado = filtrado[filtrado['Usuario'] == usuario]
    if categoria != "Todos":
        filtrado = filtrado[filtrado['Categoría'] == categoria]
    if palabra:
        filtrado = filtrado[filtrado['Mensaje'].str.contains(palabra, case=False)]

    st.markdown(f"### ✉️ Mensajes filtrados: {len(filtrado)}")
    st.dataframe(filtrado)

    csv = filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar resultados filtrados (CSV)", data=csv, file_name="auditoria_filtrada.csv", mime='text/csv')

else:
    st.info("Esperando que subas el archivo .txt exportado desde WhatsApp...")
