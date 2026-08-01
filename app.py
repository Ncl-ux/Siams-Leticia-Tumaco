import streamlit as st

st.set_page_config(
    page_title="SIAMS",
    page_icon="💧",
    layout="wide"
)

st.title("💧 SIAMS — Leticia y Tumaco")

st.write(
    """
    Plataforma informativa para consultar características climáticas,
    hidrológicas y ambientales de los territorios estudiados por el semillero.
    """
)

territorio = st.selectbox(
    "Seleccione un territorio",
    ["Leticia", "Tumaco"]
)

st.success(f"Territorio seleccionado: {territorio}")