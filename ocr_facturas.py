import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Lector de Facturas PDF", layout="centered")

st.title("🧾 Lector de Facturas en PDF")
st.write("Subí una factura en PDF y extraeremos los datos clave automáticamente.")

uploaded_file = st.file_uploader("📤 Subí tu factura PDF", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            texto_pagina = page.extract_text()
            if texto_pagina:
                text += texto_pagina + "\n"

    st.subheader("📝 Texto extraído (todas las páginas):")
    st.text(text)

    # Función mejorada: busca la N-ésima aparición y corta si aparece "Ciudad:"
    def buscar_valor_multiple(clave, ocurrencia=1, usar_dos_puntos=True, cortar_en=None):
        contador = 0
        for line in text.split("\n"):
            if clave.lower() in line.lower():
                contador += 1
                if contador == ocurrencia:
                    index = line.lower().find(clave.lower())
                    valor = line[index + len(clave):].strip()
                    if cortar_en and cortar_en.lower() in valor.lower():
                        corte_idx = valor.lower().find(cortar_en.lower())
                        valor = valor[:corte_idx].strip()
                    return valor
        return "No encontrado"

    def buscar_siguiente_linea(clave):
        lineas = text.split("\n")
        for i, line in enumerate(lineas):
            if clave.lower() in line.lower():
                if i + 1 < len(lineas):
                    return lineas[i + 1].strip()
        return "No encontrado"

    def extraer_entre_claves_en_lineas(clave_inicio, clave_fin):
        for line in text.split("\n"):
            if clave_inicio.lower() in line.lower() and clave_fin.lower() in line.lower():
                inicio_idx = line.lower().find(clave_inicio.lower()) + len(clave_inicio)
                fin_idx = line.lower().find(clave_fin.lower())
                return line[inicio_idx:fin_idx].strip()
        return "No encontrado"

    # Buscar campos
    proveedor = buscar_valor_multiple("Razón Social:")
    nit_proveedor = buscar_valor_multiple("Número de Documento:", 1)
    doc_cliente = buscar_valor_multiple("Número de Documento:", 2, cortar_en="Ciudad:")
    fecha = buscar_valor_multiple("Fecha Factura:")
    linea_total = buscar_valor_multiple("Neto a Pagar", usar_dos_puntos=False)
    factura_num = buscar_siguiente_linea("FACTURA ELECTRÓNICA DE VENTA No.")
    cliente = extraer_entre_claves_en_lineas("Cliente:", "Dirección:")

    # Buscar valor numérico del total
    total_match = re.search(r"\$?\s?\d[\d.,]*", linea_total)
    total = total_match.group().strip() if total_match else "No encontrado"

    # Mostrar resultados
    st.subheader("📋 Datos encontrados:")
    st.write(f"**Número de Factura:** {factura_num}")
    st.write(f"**Razón Social (Proveedor):** {proveedor}")
    st.write(f"**NIT Proveedor:** {nit_proveedor}")
    st.write(f"**Fecha Factura:** {fecha}")
    st.write(f"**Nombre Cliente:** {cliente}")
    st.write(f"**Documento Cliente:** {doc_cliente}")
    st.write(f"**Neto a Pagar:** {total}")
