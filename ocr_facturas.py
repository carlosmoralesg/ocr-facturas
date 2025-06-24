import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

# 🌐 Configuración general
st.set_page_config(page_title="OCR de Facturas Electrónicas", layout="wide")

# Estilo visual
st.markdown("""
    <style>
        .stApp {
            background-color: #f2f2f2;
        }

        .block-container {
            background-color: #ffffff;
            padding: 2rem 3rem;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            color: #000000;
        }

        html, body, [class*="css"] {
            color: #000000 !important;
        }

        h1, h2, h3, label, .stTextInput label, .stFileUploader label {
            color: #000000 !important;
        }

        .stButton>button {
            background-color: #4a4a4a;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 0.5em 1.2em;
        }

        .stDownloadButton>button {
            background-color: #3a3a3a;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 0.4em 1em;
        }

        .separador {
            border-top: 2px solid #bbb;
            margin: 2.5rem 0 2rem 0;
        }
    </style>
""", unsafe_allow_html=True)


# 🧾 Título
st.markdown("<h1 style='text-align: center;'>📄 OCR de Facturas Electrónicas</h1>", unsafe_allow_html=True)
st.markdown("<div class='separador'></div>", unsafe_allow_html=True)

# 📥 Subida de archivos
st.subheader("📥 Subida de archivos PDF")
uploaded_files = st.file_uploader(
    "Seleccione una o varias facturas electrónicas en PDF",
    type="pdf",
    accept_multiple_files=True
)

# 🔍 Funciones de extracción
def buscar_valor_multiple(texto, clave, ocurrencia=1, cortar_en=None, usar_dos_puntos=True):
    contador = 0
    for line in texto.split("\n"):
        if clave.lower() in line.lower():
            contador += 1
            if contador == ocurrencia:
                index = line.lower().find(clave.lower())
                valor = line[index + len(clave):].strip()
                if usar_dos_puntos and valor.startswith(":"):
                    valor = valor[1:].strip()
                if cortar_en and cortar_en.lower() in valor.lower():
                    corte_idx = valor.lower().find(cortar_en.lower())
                    valor = valor[:corte_idx].strip()
                return valor
    return "No encontrado"

def buscar_siguiente_linea(texto, clave):
    lineas = texto.split("\n")
    for i, line in enumerate(lineas):
        if clave.lower() in line.lower():
            if i + 1 < len(lineas):
                return lineas[i + 1].strip()
    return "No encontrado"

def extraer_entre_claves_en_linea(texto, clave_inicio, clave_fin):
    for line in texto.split("\n"):
        if clave_inicio.lower() in line.lower() and clave_fin.lower() in line.lower():
            inicio_idx = line.lower().find(clave_inicio.lower()) + len(clave_inicio)
            fin_idx = line.lower().find(clave_fin.lower())
            return line[inicio_idx:fin_idx].strip()
    return "No encontrado"

# 📊 Procesamiento de facturas
resultados = []
if uploaded_files:
    for archivo in uploaded_files:
        with pdfplumber.open(archivo) as pdf:
            texto = ""
            for page in pdf.pages:
                texto += page.extract_text() + "\n"

        proveedor = buscar_valor_multiple(texto, "Razón Social:")
        nit_proveedor = buscar_valor_multiple(texto, "Número de Documento:", 1)
        doc_cliente = buscar_valor_multiple(texto, "Número de Documento:", 2, cortar_en="Ciudad:")
        fecha = buscar_valor_multiple(texto, "Fecha Factura:")
        linea_total = buscar_valor_multiple(texto, "Neto a Pagar", usar_dos_puntos=False)
        factura_num = buscar_siguiente_linea(texto, "FACTURA ELECTRÓNICA DE VENTA No.")
        cliente = extraer_entre_claves_en_linea(texto, "Cliente:", "Dirección:")

        total_match = re.search(r"\$?\s?\d[\d.,]*", linea_total)
        total = total_match.group().strip() if total_match else "No encontrado"

        resultados.append({
            "Número Factura": factura_num,
            "Razón Social Emisor": proveedor,
            "NIT Proveedor": nit_proveedor,
            "Fecha Factura": fecha,
            "Nombre ": cliente,
            "Nro. Documento Cliente": doc_cliente,
            "Total": total,
            "Nombre Archivo": archivo.name,
        })

    # 📋 Resultados con botón de descarga
    st.markdown("<div class='separador'></div>", unsafe_allow_html=True)
    st.subheader("📋 Resultados extraídos")
    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')
    st.download_button(
        label="📥 Descargar Excel",
        data=output.getvalue(),
        file_name="facturas_extraidas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 👋 Pie de página
st.markdown(
    "<div class='separador'></div>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; color: #888;'>Desarrollado por tu equipo de automatización · © 2025</p>",
    unsafe_allow_html=True
)
