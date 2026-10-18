"""Verificaciones de trazabilidad real A6/A8 y créditos de imágenes."""
from pathlib import Path
from siams.fuentes_creditos import (
    leer_tabla_csv, COLUMNAS_PROCEDENCIA, RUTA_PROCEDENCIA,
    COLUMNAS_FOTOS, RUTA_FOTOS, CARPETA_FOTOS,
)

def test_fuentes_separadas_y_links():
    filas = leer_tabla_csv(RUTA_PROCEDENCIA, COLUMNAS_PROCEDENCIA)
    fuentes = {r['Sección de SIAMS']:r for r in filas}
    assert fuentes['Clima · IDEAM']['Enlace oficial'].startswith('https://')
    assert fuentes['Clima · NASA POWER']['Enlace oficial'].startswith('https://')
    for clave in ('Hidrología y ríos · SWOT','Cobertura y relieve · MapBiomas', 'Landsat','Sentinel-2'):
        assert fuentes[clave]['Enlace oficial'].startswith('https://')
    assert all(r['Origen de la información'] != 'IDEAM; NASA POWER' for r in filas)

def test_fotos_sedes_y_creditos_por_confirmar():
    fotos = leer_tabla_csv(RUTA_FOTOS, COLUMNAS_FOTOS)
    assert len(fotos) == 7
    assert len({f['Archivo'] for f in fotos}) == 7
    assert all((CARPETA_FOTOS / f['Archivo']).is_file() for f in fotos)
    assert all(f['Autor/a de la foto'] == 'Por confirmar' for f in fotos)
