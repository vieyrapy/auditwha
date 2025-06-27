
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
Anulación: anular
Cambio de exámenes: cambio examen
Descuentos: descuento
Eliminación: eliminar, eliminación
Montos: monto, importe
Errores: error, fallo
Matrícula: matricula, matrícula
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
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    text = stringio.read()

    pattern = r'(\d{1,2}/\d{1,2}/\d{4}), (\d{2}:\d{2}) - ([^:]+): (.+)'
    matches = re.findall(pattern, text)

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

    st.dataframe(filtrado)

    csv = filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar resultados filtrados (CSV)", data=csv, file_name="auditoria_filtrada.csv", mime='text/csv')

else:
    st.info("Esperando que subas el archivo .txt exportado desde WhatsApp...")
