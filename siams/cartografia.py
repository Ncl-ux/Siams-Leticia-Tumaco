# Archivo reorganizado a partir de SIAMS V39.
# No modificar la lógica científica aquí sin pruebas y revisión metodológica.
from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from html import escape
import math
import unicodedata
import base64
import subprocess
import tempfile
import re

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    import numpy as np
    import xarray as xr
except ImportError:
    np = None
    xr = None

from .catalogo import TERRITORIOS
from .utilidades import buscar_archivo_exacto, normalizar_etiqueta
from .componentes import mostrar_tarjeta
from .mapas_datos import CARPETA_MAPAS, CARPETA_MAPAS_QGIS, FICHA_QGIS_REFERENCIA, MAPAS_BOGOTA, MAPAS_UBICACION_QGIS
from .swot import CARPETAS_BUSQUEDA_MAPAS

MAPAS_QGIS_NOMBRES_NUEVOS = {'Arauca  1-10000000.pdf': 'ubicacion_arauca_nivel_1_escala_1-10000000.pdf', 'Arauca  1-1500.pdf': 'ubicacion_arauca_nivel_3_escala_1-1500.pdf', 'Arauca  1-1500000.pdf': 'ubicacion_arauca_nivel_2_escala_1-1500000.pdf', 'Bogotá  1- 10000.pdf': 'ubicacion_bogota_nivel_3_escala_1-10000.pdf', 'Bogotá  1- 1500000.pdf': 'ubicacion_bogota_nivel_2_escala_1-1500000.pdf', 'Bogotá  1-10000000.pdf': 'ubicacion_bogota_nivel_1_escala_1-10000000.pdf', 'La Paz 1-2750000.pdf': 'ubicacion_la_paz_nivel_2_escala_1-2750000.pdf', 'La Paz 1-3000.pdf': 'ubicacion_la_paz_nivel_3_escala_1-3000.pdf', 'La Paz 1-7500000.pdf': 'ubicacion_la_paz_nivel_1_escala_1-7500000.pdf', 'Leticia 1-1400.pdf': 'ubicacion_leticia_nivel_3_escala_1-1400.pdf', 'Leticia 1-5300000.pdf': 'ubicacion_leticia_nivel_2_escala_1-5300000.pdf', 'Leticia 1-8250000.pdf': 'ubicacion_leticia_nivel_1_escala_1-8250000.pdf', 'Medellín  1-10000000.pdf': 'ubicacion_medellin_nivel_1_escala_1-10000000.pdf', 'Medellín  1-2500000.pdf': 'ubicacion_medellin_nivel_2_escala_1-2500000.pdf', 'Medellín  1-5000.pdf': 'ubicacion_medellin_nivel_3_escala_1-5000.pdf', 'San Andrés 1 - 10000000.pdf': 'ubicacion_san_andres_nivel_1_escala_1-10000000.pdf', 'San Andrés 1 - 75000.pdf': 'ubicacion_san_andres_nivel_2_escala_1-75000.pdf', 'Tumaco 1 - 10000000.pdf': 'ubicacion_tumaco_nivel_1_escala_1-10000000.pdf', 'Tumaco 1 - 1500000.pdf': 'ubicacion_tumaco_nivel_2_escala_1-1500000.pdf', 'Tumaco 1- 1500.pdf': 'ubicacion_tumaco_nivel_3_escala_1-1500.pdf'}

def buscar_mapa(nombre_base: str):
    """Localiza mapas sin confundir escalas, sedes ni mapas temáticos."""
    objetivo = Path(nombre_base)
    extensiones = ('.pdf',) if objetivo.suffix.casefold() == '.pdf' else ('.png','.jpg','.jpeg','.webp','.pdf')
    for carpeta in CARPETAS_BUSQUEDA_MAPAS:
        alias = MAPAS_QGIS_NOMBRES_NUEVOS.get(nombre_base, '')
        directos = [nombre_base, alias]
        if not objetivo.suffix:
            directos += [nombre_base + ext for ext in extensiones]
        archivo = buscar_archivo_exacto(carpeta, *directos)
        if archivo is not None:
            return archivo

        # PDF QGIS renombrado 'Ubicacion_<sede> 1-<escala>.pdf': misma sede y misma escala.
        if objetivo.suffix.casefold() == '.pdf' and carpeta == CARPETA_MAPAS_QGIS and carpeta.is_dir():
            match = re.match(r'(.+?)\s+1\s*-\s*(\d+)\.pdf$', nombre_base, re.I)
            if match:
                sede, escala = normalizar_etiqueta(match.group(1)), match.group(2)
                encontrados = []
                for candidato in carpeta.glob('*.pdf'):
                    stem = normalizar_etiqueta(candidato.stem)
                    # Evitar 1:1500 confundido con 1:1.500.000 o viceversa.
                    if sede in stem.split('_') or stem.startswith(f'ubicacion_{sede}_'):
                        escalas = re.findall(r'1[_-]?(\d+)', candidato.stem)
                        if escala in escalas or stem.endswith(f'_1_{escala}'):
                            encontrados.append(candidato)
                if len(encontrados) == 1:
                    return encontrados[0]
    return None

def mostrar_pdf_mapa(ruta_pdf: Path, altura: int = 900) -> None:
    """Muestra un PDF de una sola página sin depender de un iframe del navegador.

    Se conserva el PDF original como fuente. Para visualizarlo dentro de Streamlit,
    primero se intenta el visor nativo ``st.pdf``. Si no está disponible, la primera
    página se rasteriza temporalmente en memoria (PyMuPDF, pypdfium2 o pdftoppm).
    Así se evita el cuadro blanco que algunos navegadores muestran con PDF embebidos.
    """
    ruta_pdf = Path(ruta_pdf)

    # 1) Visor PDF nativo de Streamlit, cuando está disponible.
    if hasattr(st, "pdf"):
        try:
            st.pdf(str(ruta_pdf), height=altura)
            return
        except Exception:
            pass

    imagen_png = None
    errores = []

    # 2) PyMuPDF / fitz.
    try:
        import fitz

        documento = fitz.open(str(ruta_pdf))
        pagina = documento.load_page(0)
        # ~200 ppp para que el mapa siga siendo legible al ampliar.
        matriz = fitz.Matrix(2.8, 2.8)
        pix = pagina.get_pixmap(matrix=matriz, alpha=False)
        imagen_png = pix.tobytes("png")
        documento.close()
    except Exception as error:
        errores.append(f"PyMuPDF: {error}")

    # 3) pypdfium2, si está instalado.
    if imagen_png is None:
        try:
            import io
            import pypdfium2 as pdfium

            documento = pdfium.PdfDocument(str(ruta_pdf))
            pagina = documento[0]
            bitmap = pagina.render(scale=2.8)
            pil_image = bitmap.to_pil()
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            imagen_png = buffer.getvalue()
            pagina.close()
            documento.close()
        except Exception as error:
            errores.append(f"pypdfium2: {error}")

    # 4) Poppler/pdftoppm, disponible en muchos Codespaces Linux.
    if imagen_png is None:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                salida_base = Path(tmp) / "mapa_bogota"
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-f", "1",
                        "-singlefile",
                        "-r", "200",
                        str(ruta_pdf),
                        str(salida_base),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                salida_png = salida_base.with_suffix(".png")
                if salida_png.exists():
                    imagen_png = salida_png.read_bytes()
        except Exception as error:
            errores.append(f"pdftoppm: {error}")

    if imagen_png is not None:
        st.image(
            imagen_png,
            caption=f"{ruta_pdf.name} · vista generada directamente desde el PDF original",
            use_container_width=True,
        )
        st.caption(
            "El archivo fuente sigue siendo PDF. La página se convierte temporalmente solo para "
            "mostrarla correctamente dentro del prototipo."
        )
    else:
        st.error(
            "El PDF sí fue encontrado, pero este Codespace no tiene un visor/rasterizador de PDF disponible."
        )
        st.code(
            'python -m pip install "streamlit[pdf]" pymupdf',
            language="bash",
        )
        with open(ruta_pdf, "rb") as archivo_pdf:
            st.download_button(
                "Abrir / descargar PDF original",
                data=archivo_pdf.read(),
                file_name=ruta_pdf.name,
                mime="application/pdf",
                key=f"pdf_bogota_{ruta_pdf.name}",
            )
        with st.expander("Ver diagnóstico del visor PDF", expanded=False):
            st.code("\n".join(errores) if errores else "Sin diagnóstico adicional", language=None)

def _circulo_geografico(lat_centro: float, lon_centro: float, radio_km: float, puntos: int = 96):
    """Genera un círculo geográfico aproximado para visualizar un radio de contexto."""
    latitudes = []
    longitudes = []
    radio_tierra_km = 6371.0088
    lat0 = math.radians(lat_centro)
    lon0 = math.radians(lon_centro)
    distancia_angular = radio_km / radio_tierra_km

    for i in range(puntos + 1):
        rumbo = 2 * math.pi * i / puntos
        lat = math.asin(
            math.sin(lat0) * math.cos(distancia_angular)
            + math.cos(lat0) * math.sin(distancia_angular) * math.cos(rumbo)
        )
        lon = lon0 + math.atan2(
            math.sin(rumbo) * math.sin(distancia_angular) * math.cos(lat0),
            math.cos(distancia_angular) - math.sin(lat0) * math.sin(lat),
        )
        latitudes.append(math.degrees(lat))
        longitudes.append(math.degrees(lon))

    return latitudes, longitudes

def mostrar_mapa_interactivo_bogota() -> None:
    """Mapa web navegable de la Sede Bogotá sin requerir token de Mapbox."""
    lat_sede = TERRITORIOS["Bogotá"]["lat"]
    lon_sede = TERRITORIOS["Bogotá"]["lon"]

    c1, c2, c3 = st.columns([1.05, 1.05, 1.4])
    with c1:
        vista = st.selectbox(
            "Vista inicial",
            ["Campus", "Bogotá", "Región"],
            key="bogota_vista_interactiva",
        )
    with c2:
        estilo_nombre = st.selectbox(
            "Mapa base",
            ["Claro", "OpenStreetMap", "Oscuro"],
            key="bogota_estilo_interactivo",
        )
    with c3:
        radio_km = st.slider(
            "Radio de contexto",
            min_value=0.5,
            max_value=10.0,
            value=1.5,
            step=0.5,
            format="%.1f km",
            key="bogota_radio_interactivo",
        )

    zoom_por_vista = {
        "Campus": 14.6,
        "Bogotá": 10.4,
        "Región": 7.7,
    }
    estilos = {
        "Claro": "carto-positron",
        "OpenStreetMap": "open-street-map",
        "Oscuro": "carto-darkmatter",
    }

    lat_circulo, lon_circulo = _circulo_geografico(
        lat_sede, lon_sede, radio_km
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scattermap(
            lat=lat_circulo,
            lon=lon_circulo,
            mode="lines",
            name=f"Radio de contexto: {radio_km:.1f} km",
            hoverinfo="skip",
            line=dict(width=2),
        )
    )

    fig.add_trace(
        go.Scattermap(
            lat=[lat_sede],
            lon=[lon_sede],
            mode="markers",
            name="Sede Bogotá",
            marker=dict(size=18),
            text=[
                "Universidad Nacional de Colombia<br>"
                "Sede Bogotá · Ciudad Universitaria"
            ],
            hovertemplate="<b>%{text}</b><br>Lat: %{lat:.5f}<br>Lon: %{lon:.5f}<extra></extra>",
        )
    )

    fig.update_layout(
        map=dict(
            style=estilos[estilo_nombre],
            center=dict(lat=lat_sede, lon=lon_sede),
            zoom=zoom_por_vista[vista],
        ),
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        key="mapa_interactivo_sede_bogota",
    )

    st.caption(
        "Mapa web interactivo del piloto: permite mover, acercar, alejar y consultar la sede. "
        "El radio es únicamente una ayuda visual de contexto y no representa un límite oficial del campus."
    )

def mostrar_mapa_interactivo_territorio(nombre_territorio: str, info_territorio: dict) -> None:
    """Mapa web interactivo reutilizable para las sedes SIAMS distintas de Bogotá.

    Bogotá conserva su piloto multiescala con los PDF originales. Esta función
    usa las coordenadas ya definidas en TERRITORIOS para Leticia, Tumaco,
    Medellín, San Andrés, Arauca y La Paz.
    """
    lat_sede = float(info_territorio["lat"])
    lon_sede = float(info_territorio["lon"])

    # Zoom ajustado por territorio para que la sede, la ciudad y la región
    # se vean con una escala razonable desde el primer momento.
    zoom_por_territorio = {
        "Leticia": {
            "Sede": 14.2,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "Tumaco": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "Medellín": {
            "Sede": 14.0,
            "Ciudad / municipio": 10.5,
            "Región": 8.3,
        },
        "San Andrés": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.2,
            "Región": 9.4,
        },
        "Arauca": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "La Paz": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.2,
        },
    }

    zooms = zoom_por_territorio.get(
        nombre_territorio,
        {
            "Sede": 14.0,
            "Ciudad / municipio": 10.5,
            "Región": 8.0,
        },
    )

    radios_default = {
        "Leticia": 5.0,
        "Tumaco": 5.0,
        "Medellín": 3.0,
        "San Andrés": 3.0,
        "Arauca": 5.0,
        "La Paz": 5.0,
    }

    c1, c2, c3 = st.columns([1.05, 1.05, 1.4])

    with c1:
        vista = st.selectbox(
            "Vista inicial",
            ["Sede", "Ciudad / municipio", "Región"],
            key=f"vista_interactiva_{nombre_territorio}",
        )

    with c2:
        estilo_nombre = st.selectbox(
            "Mapa base",
            ["Claro", "OpenStreetMap", "Oscuro"],
            key=f"estilo_interactivo_{nombre_territorio}",
        )

    with c3:
        radio_km = st.slider(
            "Radio de contexto",
            min_value=1.0,
            max_value=50.0,
            value=float(radios_default.get(nombre_territorio, 5.0)),
            step=1.0,
            format="%.0f km",
            key=f"radio_interactivo_{nombre_territorio}",
        )

    estilos = {
        "Claro": "carto-positron",
        "OpenStreetMap": "open-street-map",
        "Oscuro": "carto-darkmatter",
    }

    lat_circulo, lon_circulo = _circulo_geografico(
        lat_sede,
        lon_sede,
        radio_km,
    )

    fig = go.Figure()

    # Radio de contexto visual.
    fig.add_trace(
        go.Scattermap(
            lat=lat_circulo,
            lon=lon_circulo,
            mode="lines",
            name=f"Radio: {radio_km:.0f} km",
            hoverinfo="skip",
            line=dict(width=2),
        )
    )

    # Punto de la sede.
    fig.add_trace(
        go.Scattermap(
            lat=[lat_sede],
            lon=[lon_sede],
            mode="markers",
            name=nombre_territorio,
            marker=dict(size=19),
            text=[
                f"<b>{info_territorio['sede']}</b><br>"
                f"{nombre_territorio} · {info_territorio['departamento']}<br>"
                f"Latitud: {lat_sede:.6f}<br>"
                f"Longitud: {lon_sede:.6f}"
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        map=dict(
            style=estilos[estilo_nombre],
            center=dict(lat=lat_sede, lon=lon_sede),
            zoom=zooms[vista],
        ),
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        key=f"mapa_interactivo_{nombre_territorio}",
    )

    st.caption(
        "Puedes mover el mapa, acercar o alejar y consultar el punto de la sede. "
        "El círculo es únicamente una referencia visual del radio seleccionado; "
        "no representa un límite oficial de la sede ni del área de estudio."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Sede de referencia",
            info_territorio["sede"],
            "📍",
        )

    with c2:
        mostrar_tarjeta(
            "Coordenadas",
            f"{lat_sede:.6f}, {lon_sede:.6f}",
            "🧭",
        )

    with c3:
        mostrar_tarjeta(
            "Contexto",
            info_territorio["contexto"],
            "🌎",
        )

def mostrar_ficha_tecnica_qgis(nombre_territorio: str, cfg: dict) -> None:
    """Ficha de referencia bajo cada mapa QGIS; no presume metadatos embebidos en el PDF."""
    base = FICHA_QGIS_REFERENCIA
    campo = lambda valor: escape(str(valor))
    st.markdown(
        '<div class="qgis-metadata-title">🧭 Información cartográfica del mapa</div>'
        '<div class="qgis-metadata-grid">'
        '<div class="qgis-metadata-card">'
        '<h4>📐 Sistema de coordenadas</h4>'
        f'<p><strong>SRC de referencia:</strong> {campo(base["src"])}<br>'
        f'<strong>Proyección:</strong> {campo(base["proyeccion"])}<br>'
        f'<strong>Unidades:</strong> {campo(base["unidades"])}</p>'
        '</div>'
        '<div class="qgis-metadata-card">'
        '<h4>🗺️ Fuentes de información</h4>'
        f'<p>{campo(base["fuentes"])}<br>'
        'Referencias declaradas en la ficha modelo aportada.</p>'
        '</div>'
        '<div class="qgis-metadata-card">'
        '<h4>🎓 Elaboración</h4>'
        f'<p>{campo(base["elaboracion"])}<br>'
        f'<strong>Año de elaboración:</strong> {campo(base["fecha"])}<br>'
        f'<strong>Sede:</strong> {campo(nombre_territorio)}<br>'
        f'<strong>Escala del mapa:</strong> {campo(cfg.get("escala", "Por verificar"))}</p>'
        '</div>'
        '</div>'
        '<p class="qgis-metadata-note">'
        'El SRC EPSG:9377 corresponde al proyecto QGIS mostrado en la captura. '
        'No se ha comprobado el SRC de exportación de cada PDF; '
        'Las fuentes indicadas proceden de la ficha de ejemplo y deben verificarse '
        'en cada mapa. Año de elaboración de los mapas SIAMS: 2026.'
        '</p>',
        unsafe_allow_html=True,
    )

def mostrar_navegador_ubicacion_bogota() -> None:
    """Navegador por niveles: Colombia → Bogotá → Campus → mapa interactivo."""
    st.markdown(
        dedent("""
        <div class="soft-box">
            <strong>Piloto de ubicación multiescala.</strong>
            Usa los botones para pasar de la ubicación nacional a la regional, después al campus
            y finalmente a una vista web interactiva. Los tres primeros niveles corresponden a
            los mapas cartográficos preparados en QGIS.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    if "nivel_ubicacion_bogota" not in st.session_state:
        st.session_state["nivel_ubicacion_bogota"] = "Colombia"

    botones = [
        ("🇨🇴 Colombia", "Colombia"),
        ("🏙️ Bogotá", "Bogotá"),
        ("🏫 Campus", "Campus"),
        ("🌎 Interactivo", "Interactivo"),
    ]
    columnas = st.columns(4)

    for columna, (etiqueta, valor) in zip(columnas, botones):
        with columna:
            if st.button(
                etiqueta,
                use_container_width=True,
                key=f"btn_ubicacion_bogota_{valor}",
            ):
                st.session_state["nivel_ubicacion_bogota"] = valor

    nivel = st.session_state["nivel_ubicacion_bogota"]

    pasos = ["Colombia", "Bogotá", "Campus", "Interactivo"]
    piezas = []
    for i, paso in enumerate(pasos):
        clase = "location-step active" if paso == nivel else "location-step"
        piezas.append(f'<span class="{clase}">{i + 1}. {paso}</span>')
        if i < len(pasos) - 1:
            piezas.append('<span class="location-arrow">→</span>')

    st.markdown(
        '<div class="location-progress">' + "".join(piezas) + "</div>",
        unsafe_allow_html=True,
    )

    configuracion = {
        "Colombia": {
            "clave": "ubicacion_colombia",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Bogotá D.C. dentro del contexto nacional.",
            "escala": "Escala cartográfica: 1:10.000.000",
        },
        "Bogotá": {
            "clave": "ubicacion_region",
            "titulo": "Nivel 2 · Bogotá y contexto regional",
            "detalle": "Acercamiento al Distrito Capital y su entorno regional.",
            "escala": "Escala cartográfica: 1:1.500.000",
        },
        "Campus": {
            "clave": "ubicacion_campus",
            "titulo": "Nivel 3 · Campus Ciudad Universitaria",
            "detalle": "Detalle de la Sede Bogotá y su entorno inmediato.",
            "escala": "Escala cartográfica: 1:10.000",
        },
    }

    st.markdown('<div class="location-shell">', unsafe_allow_html=True)

    if nivel == "Interactivo":
        st.markdown("### 🌎 Explorador interactivo de la Sede Bogotá")
        mostrar_mapa_interactivo_bogota()
    else:
        cfg = configuracion[nivel]
        st.markdown(f"### {cfg['titulo']}")
        st.caption(f"{cfg['detalle']} · {cfg['escala']}")

        nombre_archivo = MAPAS_BOGOTA[cfg["clave"]]
        ruta = buscar_mapa(nombre_archivo)

        if ruta is None:
            st.warning(
                f"No se encontró `{nombre_archivo}` en `Mapas_Qgis`."
            )
            st.code(str(CARPETA_MAPAS), language=None)
            st.info(
                "Pon los tres PDF originales dentro de `Mapas_Qgis`, conservando exactamente "
                "los nombres con los que los exportaste desde QGIS."
            )
        else:
            if ruta.suffix.casefold() == ".pdf":
                mostrar_pdf_mapa(ruta, altura=900)
            else:
                st.image(
                    str(ruta),
                    caption=f"{cfg['titulo']} · {cfg['escala']}",
                    use_container_width=True,
                )
            st.caption(f"Archivo: {ruta.name} · {cfg['escala']}")
            mostrar_ficha_tecnica_qgis("Bogotá", cfg)


    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        mostrar_tarjeta(
            "Sede",
            "Universidad Nacional de Colombia – Sede Bogotá.",
            "📍",
        )
    with c2:
        mostrar_tarjeta(
            "Navegación",
            "Colombia → Bogotá → Campus → explorador interactivo.",
            "🧭",
        )
    with c3:
        mostrar_tarjeta(
            "Uso del piloto",
            "Ubicación institucional y contexto espacial; no sustituye cartografía temática oficial.",
            "🗺️",
        )

def mostrar_navegador_ubicacion_qgis(nombre_territorio: str, info_territorio: dict) -> None:
    """Navegador multiescala QGIS para territorios con mapas disponibles."""
    niveles = MAPAS_UBICACION_QGIS.get(nombre_territorio, [])
    if not niveles:
        mostrar_mapa_interactivo_territorio(nombre_territorio, info_territorio)
        return

    st.markdown(
        dedent(f"""
        <div class="soft-box">
            <strong>Ubicación multiescala en QGIS.</strong>
            Explora los mapas cartográficos disponibles —desde el contexto nacional
            hasta la sede— y después abre el explorador interactivo de
            <strong>{escape(str(nombre_territorio))}</strong>.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    clave_estado = f"nivel_ubicacion_qgis_{normalizar_etiqueta(nombre_territorio)}"
    opciones = [nivel["paso"] for nivel in niveles] + ["Interactivo"]
    if clave_estado not in st.session_state or st.session_state[clave_estado] not in opciones:
        st.session_state[clave_estado] = opciones[0]

    etiquetas = []
    for i, nivel in enumerate(niveles):
        if i == 0:
            icono = "🇨🇴"
        elif i == len(niveles) - 1:
            icono = "🏫"
        else:
            icono = "🧭"
        etiquetas.append((f"{icono} {nivel['paso']}", nivel["paso"]))
    etiquetas.append(("🌎 Interactivo", "Interactivo"))

    columnas = st.columns(len(etiquetas))
    for columna, (etiqueta, valor) in zip(columnas, etiquetas):
        with columna:
            if st.button(
                etiqueta,
                use_container_width=True,
                key=f"btn_qgis_{normalizar_etiqueta(nombre_territorio)}_{normalizar_etiqueta(valor)}",
            ):
                st.session_state[clave_estado] = valor

    nivel_activo = st.session_state[clave_estado]
    piezas = []
    for i, paso in enumerate(opciones):
        clase = "location-step active" if paso == nivel_activo else "location-step"
        piezas.append(f'<span class="{clase}">{i + 1}. {escape(str(paso))}</span>')
        if i < len(opciones) - 1:
            piezas.append('<span class="location-arrow">→</span>')

    st.markdown(
        '<div class="location-progress">' + "".join(piezas) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="location-shell">', unsafe_allow_html=True)

    if nivel_activo == "Interactivo":
        st.markdown(f"### 🌎 Explorador interactivo de {nombre_territorio}")
        if nombre_territorio == "Bogotá":
            mostrar_mapa_interactivo_bogota()
        else:
            mostrar_mapa_interactivo_territorio(nombre_territorio, info_territorio)
    else:
        cfg = next(n for n in niveles if n["paso"] == nivel_activo)
        st.markdown(f"### {cfg['titulo']}")
        st.caption(f"{cfg['detalle']} · Escala cartográfica: {cfg['escala']}")

        ruta = buscar_mapa(cfg["archivo"])
        if ruta is None:
            st.warning(f"No se encontró `{cfg['archivo']}` dentro de `Mapas_Qgis`.")
            st.caption(f"Ruta esperada: {CARPETA_MAPAS_QGIS / cfg['archivo']}")
        elif ruta.suffix.casefold() == ".pdf":
            mostrar_pdf_mapa(ruta, altura=900)
            st.caption(f"Archivo: {ruta.name} · Escala {cfg['escala']}")
            mostrar_ficha_tecnica_qgis(nombre_territorio, cfg)
        else:
            st.image(
                str(ruta),
                caption=f"{cfg['titulo']} · Escala {cfg['escala']}",
                use_container_width=True,
            )
            mostrar_ficha_tecnica_qgis(nombre_territorio, cfg)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        mostrar_tarjeta("Sede de referencia", info_territorio["sede"], "📍")
    with c2:
        mostrar_tarjeta(
            "Navegación",
            " → ".join(opciones),
            "🧭",
        )
    with c3:
        mostrar_tarjeta(
            "Uso del visor",
            "Ubicación institucional y contexto espacial; no sustituye cartografía temática oficial.",
            "🗺️",
        )

__all__ = ['MAPAS_QGIS_NOMBRES_NUEVOS', 'buscar_mapa', 'mostrar_pdf_mapa', '_circulo_geografico', 'mostrar_mapa_interactivo_bogota', 'mostrar_mapa_interactivo_territorio', 'mostrar_ficha_tecnica_qgis', 'mostrar_navegador_ubicacion_bogota', 'mostrar_navegador_ubicacion_qgis']
