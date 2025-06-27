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
Anular Factura: anular factura, eliminar factura, anular pago, eliminar pago, cancelación pago, anulo pago, sacar pago
Crear Factura o Procesar Pago: crear factura, procesar pago, abonar, abono
Anulación Inscripción: anular inscripción, eliminar inscripción 
Cambio Examen: cambio examen, cambiar examen, cambiar monto examen, modificar monto examen, cambio de oportunidad, tercera oportunidad, segunda oportunidad, primera oportunidad, extraordinario, recuperatorio
Descuentos: descuento, beca, becado, 10% descuento, 50% descuento, egresada
Importe en Caja: monto, importe, gs (Guaraníes), dólares, total, diferencia, costo, precio 
Matrícula  e Inscripción: matricula, matrícula, matricular, inscripción, inscripto, preinscribió, inscribir
Resueltos Soporte: listo, Ya, ok
Imagen: <Multimedia omitido>
Consultas Académicas: Materias, módulos, curso, semestre, carrera, malla, didáctica, sociología, psicología, contabilidad, inglés, comunicación, física, historia, economía, derecho, emprendedurismo, anatomía, microbiología, auditoría, gerencia, comercio internacional, fisiología, etc.
Asistencia y Listas: lista, lista de asistencia, habilitados, no aparece en lista, verificar lista 
Gestión de Datos: cambiar nombre, cambiar apellido, cambiar datos, agregar correo electrónico, agregar RUC 
Informes y Reportes: reporte, ficha, informe académico, planilla
Gestión de Usuarios: crear usuario, resetear contraseña, habilitar acceso
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

def merge_multiline_whatsapp_messages(text):
    lines = text.strip().split("\n")
    merged_lines = []
    current = ""
    whatsapp_pattern = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}, \d{2}:\d{2} - ")

    for line in lines:
        if whatsapp_pattern.match(line):
            if current:
                merged_lines.append(current.strip())
            current = line
        else:
            current += " " + line.strip()
    if current:
        merged_lines.append(current.strip())
    return merged_lines

if uploaded_file:
    raw_bytes = uploaded_file.getvalue()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("utf-16")

    lines = merge_multiline_whatsapp_messages(text)
    pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4}), (\d{2}:\d{2}) - ([^:]+): (.+)')
    matches = [pattern.match(line) for line in lines if pattern.match(line)]

    st.write(f"📌 Mensajes detectados: {len(matches)}")

    records = []
    for match in matches:
        fecha, hora, usuario, mensaje = match.groups()
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
    palabra = st.text_input("Buscar palabra clave")

    filtrado = df.copy()
    if usuario != "Todos":
        filtrado = filtrado[filtrado['Usuario'] == usuario]
    if palabra:
        filtrado = filtrado[filtrado['Mensaje'].str.contains(palabra, case=False)]

    categorias_disponibles = sorted(filtrado['Categoría'].unique().tolist())
    if not categorias_disponibles:
        st.warning("⚠️ No hay categorías disponibles en los mensajes filtrados.")

    categoria = st.selectbox("Filtrar por categoría", ["Todos"] + categorias_disponibles)

    if categoria != "Todos":
        filtrado = filtrado[filtrado['Categoría'] == categoria]

    st.markdown(f"### ✉️ Mensajes filtrados: {len(filtrado)}")
    st.dataframe(filtrado)

    csv = filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar resultados filtrados (CSV)", data=csv, file_name="auditoria_filtrada.csv", mime='text/csv')

else:
    st.info("Esperando que subas el archivo .txt exportado desde WhatsApp...")
