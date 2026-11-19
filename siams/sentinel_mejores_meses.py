"""Visualizaciones mensuales multi-anuales de Sentinel-2, sin recalcular índices."""
from __future__ import annotations
import json
import os
import re
import unicodedata
from pathlib import Path

PRODUCTOS = {
    'NDVI': ('Estado de la vegetación', 'Índice espectral de vegetación; no es una medida directa de biomasa.'),
    'MNDWI': ('Detección de agua superficial', 'Máscara de candidatos a agua obtenida mediante MNDWI; depende del umbral y del procesamiento.'),
    'SCL': ('Clasificación de superficies y nubes', 'En esta animación se muestra la máscara de agua derivada de la clase 6 de Sentinel-2 Level-2A, no todas las clases SCL.'),
}


def clave_territorio(nombre):
    texto = unicodedata.normalize('NFKD', nombre.casefold())
    return '_'.join(re.findall(r'[a-z0-9]+', ''.join(c for c in texto if not unicodedata.combining(c))))


def cargar_coleccion(carpeta, territorio):
    base = Path(carpeta).resolve()
    ruta = base / 'mejores_meses_manifest.json'
    if not ruta.is_file():
        return None
    manifiesto = json.loads(ruta.read_text(encoding='utf-8'))
    entrada = manifiesto.get('territorios', {}).get(clave_territorio(territorio))
    if not entrada:
        return None
    archivos = {}
    for tipo, relativo in entrada['productos'].items():
        archivo = (base / relativo).resolve()
        if tipo in PRODUCTOS and archivo.is_relative_to(base) and archivo.suffix.lower() == '.mp4' and archivo.is_file():
            archivos[tipo] = archivo
    return entrada, archivos


def mostrar_seleccion_mensual(st, carpeta, territorio, anuales):
    """Devuelve True si ya se atendió el panel; False conserva la interfaz anual."""
    try:
        coleccion = cargar_coleccion(carpeta, territorio)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.warning('No se pudo leer el catálogo de selecciones mensuales Sentinel-2.')
        return False
    if not coleccion:
        return False
    entrada, archivos = coleccion
    confirmada = entrada.get('publicar') is True
    previa = os.environ.get('SIAMS_SENTINEL_PREVIA') == '1'
    if not confirmada and not previa:
        if not anuales:
            st.info('La selección mensual de este territorio está pendiente de confirmar su procedencia geográfica.')
            return True
        return False
    if not archivos:
        st.warning('No se encontraron los videos de la selección mensual.')
        return not bool(anuales)
    clave = clave_territorio(territorio)
    # SIAMS: una copia física puede servir a ambos accesos históricos.
    if anuales and any(
        Path(anual).resolve() == archivos[tipo].resolve()
        for grupo in anuales.values() for tipo, anual in grupo.items()
        if tipo in archivos
    ):
        st.info('Los accesos anual y de mejores meses comparten archivos idénticos. '
                'No son dos series independientes; verifica las fechas de los fotogramas. '
                'La etiqueta anual histórica no certifica que todas las escenas sean de 2025.')
    if anuales:
        modo = st.radio('Tipo de visualización', ['Selección de mejores meses', 'Animaciones por año'], horizontal=True, key=f'sentinel_coleccion_{clave}')
        if modo == 'Animaciones por año':
            return False
    st.markdown('### Selección de mejores meses')
    if not confirmada:
        st.warning('Vista preliminar: identificación territorial provisional. No usar como resultado validado.')
    st.caption('Las escenas seleccionadas pueden proceder de años distintos. Observa la fecha y el porcentaje de nubes indicado en cada fotograma. No representa una serie anual continua ni una climatología.')
    if clave == 'tumaco':
        st.warning('Producto exploratorio. La calidad y cobertura de las escenas, las áreas de agua y las tendencias cuantitativas requieren revisión; aquí solo se muestran los videos originales.')
    tabs = st.tabs([f'{titulo} · {tipo}' for tipo, (titulo, _) in PRODUCTOS.items()])
    for tab, (tipo, (titulo, descripcion)) in zip(tabs, PRODUCTOS.items()):
        with tab:
            st.markdown(f'#### {titulo} · {tipo}')
            st.caption(descripcion)
            ruta = archivos.get(tipo)
            if ruta is None:
                st.info('Video no disponible.')
                continue
            st.video(str(ruta), format='video/mp4', autoplay=True, loop=True, muted=True)
            st.download_button(f'Descargar animación {tipo}', data=ruta.read_bytes(), file_name=ruta.name, mime='video/mp4', key=f'sentinel_mensual_descarga_{clave}_{tipo}')
    st.caption('Fuente: Sentinel-2. Visualizaciones originales procesadas externamente e integradas en SIAMS; no se recalculan los índices.')
    return True
