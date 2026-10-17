"""A5: verifica que un tercero pueda reconstruir un Excel desde los plot originales."""
import importlib.util
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _cargar():
    ruta = ROOT / 'scripts' / 'reproducir_excel_swot_a5.py'
    spec = importlib.util.spec_from_file_location('excel_swot_a5', ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_excel_generado_desde_raw_sin_tocar_productos(tmp_path):
    modulo = _cargar()
    salida = tmp_path / 'swot_test.xlsx'
    res = modulo.construir_excel(salida=salida)
    assert res['plot_originales'] == 80
    assert res['tramos'] == 20
    assert res['observaciones'] == 1957
    assert res['alertas_exploratorias'] == 76
    with pd.ExcelFile(salida) as libro:
        assert {'Resumen', 'Observaciones', 'Fuentes_raw', 'Diccionario', 'Metodologia'} == set(libro.sheet_names)
        obs = pd.read_excel(libro, 'Observaciones', dtype={'reach_id': str})
        fuentes = pd.read_excel(libro, 'Fuentes_raw')
        assert len(obs) == 1957
        assert len(fuentes) == 80
        assert fuentes.sha256.str.fullmatch('[a-f0-9]{64}').all()


def test_no_sobrescribir_excel_y_entradas_faltantes(tmp_path):
    import pytest
    modulo = _cargar()
    salida = tmp_path / 'existente.xlsx'
    salida.write_bytes(b'NO CAMBIAR')
    with pytest.raises(FileExistsError):
        modulo.construir_excel(salida=salida)
    assert salida.read_bytes() == b'NO CAMBIAR'
    with pytest.raises(FileNotFoundError):
        modulo.construir_excel(raw=tmp_path / 'no_existe', salida=tmp_path / 'nuevo.xlsx')
