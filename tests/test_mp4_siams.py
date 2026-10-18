"""Pruebas de integración de los 23 MP4 sin intervenir cálculos de SIAMS."""
from pathlib import Path
import ast

RAIZ = Path(__file__).resolve().parents[1]


def test_mp4_siams_23_archivos_en_carpetas_existentes():
    swot = list((RAIZ / 'Animaciones_SWOT').glob('swot_*_ancho.mp4'))
    mapbiomas = list((RAIZ / 'Coberturas_MapBiomas').glob('*/mapbiomas_*.mp4'))
    assert len(swot) == 5, f'SWOT: encontrados {len(swot)} MP4, esperados 5'
    assert len(mapbiomas) == 18, f'MapBiomas: encontrados {len(mapbiomas)} MP4, esperados 18'
    assert all(p.stat().st_size > 1024 for p in swot + mapbiomas)


def test_mp4_siams_visores_mp4_y_fallback_gif():
    for nombre, funciones in {
        'swot.py': ('buscar_gif_swot', 'mostrar_gifs_swot'),
        'mapbiomas.py': ('buscar_gif_mapbiomas', '_mostrar_gif_mapbiomas'),
    }.items():
        texto = (RAIZ / 'siams' / nombre).read_text(encoding='utf-8')
        arbol = ast.parse(texto)
        for nombre_fun in funciones:
            fun = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == nombre_fun)
            codigo = ast.get_source_segment(texto, fun)
            assert 'SIAMS_M1_MP4_PRECEDENCIA' in codigo
        assert 'st.video(' in texto
        assert ('st.image(' in texto if nombre == 'swot.py' else 'st.markdown(' in texto)
