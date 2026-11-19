"""Visualizacion de insumos externos de rastreo de humedad; no recalcula los datos."""
from pathlib import Path
import unicodedata

CARPETA_HUMEDAD = Path(__file__).resolve().parents[1] / 'Humedad_Atmosferica'

def _normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', texto.casefold()) if not unicodedata.combining(c)).replace('_', ' ').replace('-', ' ').split())

CARPETAS = {'arauca': 'Arauca', 'la paz': 'La Paz', 'medellin': 'Medellin', 'tumaco': 'Tumaco'}

def buscar_humedad_territorio(territorio: str, raiz: Path | None = None) -> dict[str, Path]:
    carpeta = CARPETAS.get(_normalizar(territorio))
    if carpeta is None:
        return {}
    base = (CARPETA_HUMEDAD if raiz is None else Path(raiz)) / carpeta
    candidatos = {'video': base / 'origen_humedad_1990-2019.mp4', 'climatologia': base / 'climatologia_mensual.png'}
    return {k: p for k, p in candidatos.items() if p.is_file() and p.stat().st_size > 0}


def mostrar_humedad_territorio(territorio: str) -> None:
    import streamlit as st
    st.subheader(f'Origen de humedad atmosférica · {territorio}')
    st.markdown('Explora la distribución temporal y espacial de la humedad rastreada y su contribución promedio mensual desde regiones hidrográficas y océanos.')
    archivos = buscar_humedad_territorio(territorio)
    if not archivos:
        st.info(f'Aún no hay productos de rastreo de humedad disponibles para {territorio}.')
        return
    st.caption('Periodo del rastreo de humedad: 1990–2019. Productos visuales procesados externamente.')
    tab_video, tab_clima = st.tabs(['Rastreo temporal de humedad', 'Climatología y contribución de humedad'])
    clave = _normalizar(territorio).replace(' ', '_')
    with tab_video:
        st.markdown('#### Evolución mensual del rastreo de humedad')
        ruta = archivos.get('video')
        if ruta:
            st.video(str(ruta), format='video/mp4', loop=True, muted=True, autoplay=False)
            st.caption('360 meses · enero de 1990 a diciembre de 2019 · escala y leyenda del producto original.')
            st.download_button('Descargar animación MP4', data=ruta.read_bytes(), file_name=f'{clave}_origen_humedad_1990-2019.mp4', mime='video/mp4', key=f'humedad_video_{clave}')
        else:
            st.info('Animación no disponible.')
    with tab_clima:
        st.markdown('#### Precipitación y contribución promedio multianual de humedad')
        ruta = archivos.get('climatologia')
        if ruta:
            st.image(str(ruta), caption='Climatología mensual y contribuciones por cuencas y océanos. Unidades indicadas en la figura: mm.')
            st.download_button('Descargar gráfica PNG', data=ruta.read_bytes(), file_name=f'{clave}_climatologia_humedad.png', mime='image/png', key=f'humedad_clima_{clave}')
        else:
            st.info('Gráfica no disponible.')
        st.markdown('La gráfica permite comparar la estacionalidad de la precipitación con la humedad rastreada y distinguir las regiones de origen indicadas en la leyenda.')
    with st.expander('Metodología, alcance y fuente'):
        st.markdown('Los insumos representan un rastreo de humedad atmosférica para 1990–2019, con contribuciones agrupadas por cuencas de nivel 02 y océanos. La humedad rastreada no debe interpretarse automáticamente como la precipitación total observada ni como recarga de agua subterránea.')
        st.markdown('SIAMS presenta las animaciones y gráficas suministradas al proyecto, sin recalcular ni validar el modelo de rastreo. No se dispone todavía de la ficha metodológica, autoría específica, datos numéricos originales ni periodo de la serie de precipitación utilizado en cada figura; estos elementos deben documentarse antes de realizar análisis cuantitativos.')
        st.caption('Fuente: archivos de rastreo de humedad entregados al proyecto SIAMS. Créditos específicos pendientes de confirmar.')
