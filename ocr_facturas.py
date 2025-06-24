import streamlit as st
import pdfplumber
import pandas as pd
import io
import os
import re

st.set_page_config(page_title="OCR de Facturas Electrónicas", layout="wide")

# 🎨 Estilo visual
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
        h1, h2, h3, label {
            color: #000000 !important;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #4a4a4a;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 0.5em 1.2em;
            width: 100%;
            margin-top: 0.5em;
            transition: 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #5a5a5a !important;
            color: white !important;
            border: none;
        }
        .separador {
            border-top: 2px solid #bbb;
            margin: 2.5rem 0 2rem 0;
        }
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] * {
            color: white !important;
        }
        .stAlert>div {
            background-color: #d4edda !important;
            color: #000000 !important;
        }
        /* Botón toggle sidebar: ícono siempre blanco */
        button[aria-label="Toggle sidebar"] svg {
            stroke: white !important;
            fill: white !important;
        }
        button[aria-label="Toggle sidebar"]:hover svg {
            stroke: white !important;
            fill: white !important;
        }
        button[aria-label="Toggle sidebar"] {
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
        }
        button[aria-label="Toggle sidebar"]:hover {
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)

# Estado de navegación
for key in ["page", "df_actual", "confirmar_borrado", "guardado_exitoso"]:
    if key not in st.session_state:
        st.session_state[key] = {"page": "procesar", "df_actual": pd.DataFrame(), "confirmar_borrado": False, "guardado_exitoso": False}[key]

# Menú lateral
st.sidebar.markdown("## Menú Principal")
if st.sidebar.button("📄 Procesar Facturas"):
    st.session_state.page = "procesar"
if st.sidebar.button("📶 Ver Histórico"):
    st.session_state.page = "historico"

# Funciones de extracción
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

# Página de procesamiento
if st.session_state.page == "procesar":
    st.markdown("<h1 style='text-align: center;'>OCR de Facturas Electrónicas</h1>", unsafe_allow_html=True)
    st.markdown("<div class='separador'></div>", unsafe_allow_html=True)

    st.subheader("Subida de archivos PDF")
    uploaded_files = st.file_uploader(
        "Seleccione una o varias facturas electrónicas en PDF",
        type="pdf",
        accept_multiple_files=True
    )

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

        df = pd.DataFrame(resultados)
        st.session_state.df_actual = df

        st.markdown("<div class='separador'></div>", unsafe_allow_html=True)
        st.subheader("Resultados extraídos")
        st.dataframe(df, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Facturas')
        st.download_button(
            label="📊 Descargar Excel",
            data=output.getvalue(),
            file_name="facturas_extraidas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if st.button("💾 Guardar en histórico"):
            historico_path = "historico_facturas.xlsx"
            if os.path.exists(historico_path):
                df_hist = pd.read_excel(historico_path, engine='openpyxl')
                df_total = pd.concat([df_hist, df], ignore_index=True)
            else:
                df_total = df
            df_total.to_excel(historico_path, index=False, engine='openpyxl')
            st.success("Datos guardados en el histórico correctamente.")

# Página de histórico
elif st.session_state.page == "historico":
    st.markdown("<h1 style='text-align: center;'>🖓 Histórico de Facturas Procesadas</h1>", unsafe_allow_html=True)
    st.markdown("<div class='separador'></div>", unsafe_allow_html=True)

    historico_path = "historico_facturas.xlsx"
    if os.path.exists(historico_path):
        try:
            df_hist = pd.read_excel(historico_path, engine='openpyxl')
            if not df_hist.empty:
                st.subheader("📋 Facturas guardadas")
                selected_rows_df = st.data_editor(
                    df_hist,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="historico_editor"
                )

                if st.button("💾 Guardar cambios"):
                    df_hist = selected_rows_df.dropna(how="all")
                    df_hist.to_excel(historico_path, index=False, engine='openpyxl')
                    st.session_state["guardado_exitoso"] = True
                    st.rerun()

                if st.session_state.get("guardado_exitoso"):
                    st.success("Cambios guardados correctamente.")
                    st.session_state["guardado_exitoso"] = False

                if not st.session_state.confirmar_borrado:
                    if st.button("🗑️ Borrar todo el histórico"):
                        st.session_state.confirmar_borrado = True
                        st.rerun()
                else:
                    st.markdown("<p style='color: black;'>¿Estás seguro de que deseas borrar todo el histórico?</p>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmar eliminación"):
                            os.remove(historico_path)
                            st.session_state.confirmar_borrado = False
                            st.success("🗑️ Histórico eliminado completamente.")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancelar"):
                            st.session_state.confirmar_borrado = False
                            st.rerun()
            else:
                st.markdown("<p style='color: black;'>El archivo histórico está vacío. Procese facturas para comenzar.</p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"No se pudo leer el histórico: {e}")
    else:
        st.markdown("<p style='color: black;'>No se encontró ningún histórico. Procese algunas facturas primero.</p>", unsafe_allow_html=True)

# Pie de página
st.markdown("<div class='separador'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #888;'>Desarrollado por David Morales · © 2025</p>",
    unsafe_allow_html=True
)
