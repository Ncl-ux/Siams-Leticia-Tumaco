"""Procedencia detallada de datos y fotografías, A6/A8 (sin inventar autorías)."""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
RAIZ = Path(__file__).resolve().parents[1]
NOMBRE_OFICIAL_SIAMS = "Semillero de Investigación de Aguas y Modelación Subterránea (SIAMS)"
RUTA_PROCEDENCIA = RAIZ / "docs" / "FUENTES_POR_SECCION_SIAMS.csv"
RUTA_AUTORES = RAIZ / "docs" / "AUTORES_SIAMS.csv"
RUTA_FOTOS = RAIZ / "docs" / "CREDITOS_FOTOS_SEDES.csv"
CARPETA_FOTOS = RAIZ / "Fotos_Sedes"
COLUMNAS_PROCEDENCIA = (
    "Sección de SIAMS", "Origen de la información", "Información que se muestra",
    "Precisiones", "Enlace oficial",
)
COLUMNAS_AUTORES = ("Nombre", "Rol", "Afiliación")
COLUMNAS_FOTOS = (
    "Sede", "Archivo", "Procedencia de la copia", "Autor/a de la foto",
    "Permiso de publicación", "Observaciones",
)


def leer_tabla_csv(ruta: Path, columnas: tuple[str, ...]) -> list[dict[str, str]]:
    """Lee y valida un CSV de referencia, sin transformarlo silenciosamente."""
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        cabeceras = tuple(lector.fieldnames or ())
        # El inventario fotográfico admite las dos columnas opcionales añadidas
        # por el ajuste de tarjetas. Las seis columnas originales siguen siendo
        # obligatorias y los demás inventarios mantienen su esquema estricto.
        columnas_foto_extra = ("Fuente original", "Enlace fuente original")
        esquemas_validos = (
            (columnas, columnas + columnas_foto_extra)
            if columnas == COLUMNAS_FOTOS else (columnas,)
        )
        if cabeceras not in esquemas_validos:
            raise ValueError(f"Encabezados inválidos en {ruta.name}: se esperaba uno de {esquemas_validos}")
        resultado = []
        for numero, fila in enumerate(lector, 2):
            if None in fila:
                raise ValueError(f"{ruta.name}:{numero}: columnas sobrantes")
            fila_limpia = {c: (fila[c] or "").strip() for c in cabeceras}
            if not any(fila_limpia.values()):
                continue
            if not all(fila_limpia.values()):
                # El inventario fotográfico permite completar la fuente
                # original y su enlace cuando se verifiquen.
                opcionales = {"Enlace oficial", *columnas_foto_extra}
                if any(not fila_limpia[c] for c in cabeceras if c not in opcionales):
                    raise ValueError(f"{ruta.name}:{numero}: registro incompleto")
            if "Enlace oficial" in columnas and fila_limpia.get("Enlace oficial"):
                p = urlparse(fila_limpia["Enlace oficial"])
                if p.scheme != "https" or not p.netloc:
                    raise ValueError(f"{ruta.name}:{numero}: URL oficial no válida")
            resultado.append(fila_limpia)
    return resultado


def mostrar_creditos_institucionales() -> None:
    import streamlit as st
    st.markdown(f"**{NOMBRE_OFICIAL_SIAMS}**")
    st.caption("Universidad Nacional de Colombia · Proyecto académico en desarrollo")
    st.markdown("**Equipo y contribuciones**")
    try:
        autores = leer_tabla_csv(RUTA_AUTORES, COLUMNAS_AUTORES)
    except (OSError, ValueError, csv.Error):
        logger.exception("Error al cargar registro de autores: %s", RUTA_AUTORES)
        st.warning("No se pudo cargar la lista de autores. Revise docs/AUTORES_SIAMS.csv.")
        return
    if autores:
        st.dataframe(autores, hide_index=True, width="stretch")
    else:
        st.info("Nombres y roles individuales: pendientes de confirmación por el equipo.")
    st.caption("Los productos de terceros conservan sus autorías y condiciones de uso originales.")


def _mostrar_fotos() -> None:
    import streamlit as st
    try:
        filas = leer_tabla_csv(RUTA_FOTOS, COLUMNAS_FOTOS)
    except (OSError, ValueError, csv.Error):
        logger.exception("Error al cargar registro fotográfico: %s", RUTA_FOTOS)
        st.warning("No se pudo consultar el inventario fotográfico de las sedes.")
        return
    st.caption("Las fotografías ya se utilizan en las tarjetas de sedes de Inicio. Esta vista documenta su procedencia.")
    st.dataframe(filas, hide_index=True, width="stretch")
    st.warning("Autoría y permisos de las fotografías por verificar antes de darlas por autorizadas para publicación pública.")
    for inicio in range(0, len(filas), 3):
        cols = st.columns(3)
        for col, fila in zip(cols, filas[inicio:inicio+3]):
            with col:
                foto = CARPETA_FOTOS / fila["Archivo"]
                if foto.is_file() and foto.resolve().parent == CARPETA_FOTOS.resolve():
                    st.image(str(foto), caption=fila["Sede"], width="stretch")
                else:
                    st.caption(f"{fila['Sede']}: fotografía no disponible")


def mostrar_fuentes_y_creditos() -> None:
    import streamlit as st
    st.subheader("Fuentes verificadas por módulo")
    st.caption(
        "Procedencia según los productos utilizados y los archivos identificados en SIAMS. "
        "IDEAM y NASA POWER se describen por separado; los periodos dependen de cada archivo local."
    )
    try:
        filas = leer_tabla_csv(RUTA_PROCEDENCIA, COLUMNAS_PROCEDENCIA)
        if not filas:
            raise ValueError("Inventario vacío")
        csv_descarga = RUTA_PROCEDENCIA.read_bytes()
    except (OSError, ValueError, csv.Error):
        logger.exception("Error al cargar procedencia: %s", RUTA_PROCEDENCIA)
        st.warning("No se pudo cargar el inventario. Revise docs/FUENTES_POR_SECCION_SIAMS.csv.")
    else:
        st.dataframe(
            filas, hide_index=True, width="stretch",
            column_config={
                "Enlace oficial": st.column_config.LinkColumn("Portal o referencia oficial", display_text="Abrir fuente")
            },
        )
        st.download_button(
            "Descargar inventario de fuentes (CSV)", csv_descarga,
            file_name=RUTA_PROCEDENCIA.name, mime="text/csv",
            key="siams_fuentes_creditos_csv",
        )
    with st.expander("Fotografías de las siete sedes y créditos", expanded=False):
        _mostrar_fotos()
    st.divider()
    mostrar_creditos_institucionales()
    st.info(
        "Una referencia de portal no equivale a identificar cada descarga individual. "
        "Conserve la estación, escena, colección o ID de producto; la licencia del código SIAMS "
        "y los permisos de fotos/datos se tramitan por separado."
    )
