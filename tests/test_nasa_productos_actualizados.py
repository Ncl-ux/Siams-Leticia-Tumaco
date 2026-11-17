import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ruta = Path(__file__).resolve().parents[1] / 'scripts' / '14_nasa_productos_actualizados.py'
spec = importlib.util.spec_from_file_location('productos_nasa', ruta)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def diario():
    fechas = pd.date_range('1981-01-01', '2001-02-03', freq='D')
    d = pd.DataFrame({'fecha': fechas})
    for c, v in zip(m.COLUMNAS, [1., 20., 25., 15., 80., 1., 90., 15.]):
        d[c] = v
    d.loc[d.fecha.dt.year < 1984, m.COLUMNAS[-1]] = float('nan')
    return d


def test_periodo_y_regimen(tmp_path):
    d = diario()
    ruta = tmp_path / 'nasa_power_leticia.csv'
    d.to_csv(ruta, index=False)
    base = m.leer_diario(ruta, 'leticia')
    assert base.fecha.min() == pd.Timestamp('2000-01-01')
    h = m.construir_hojas(base, 'leticia', homogeneidad=False)
    # February 2001 has only three days and must not dilute February 2000.
    assert h['Regimen_P'].set_index('mes').loc[2, 'precipitacion_mm_mes'] == 29
    assert h['Datos_diarios'].fecha.max() == pd.Timestamp('2001-02-03')
    assert h['P_mensual'].iloc[-1].precipitacion_mm_mes == 3
    archivo = m.generar('leticia', tmp_path, homogeneidad=False)
    assert archivo.exists()
    assert 'Climatologia_mensual' in pd.ExcelFile(archivo).sheet_names
    assert ruta.exists()


def test_rechaza_duplicados(tmp_path):
    d = diario(); ruta = tmp_path / 'nasa_power_bogota.csv'
    pd.concat([d, d.iloc[:1]]).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match='duplicadas'):
        m.leer_diario(ruta, 'bogota')


def test_homogeneidad_excluye_ultimo_anio(monkeypatch):
    d = diario(); llamados = []
    def evaluar(anios, valores):
        llamados.append((min(anios), max(anios)))
        return {'dictamen': 'prueba'}
    monkeypatch.setattr(m, 'evaluar_homogeneidad', evaluar)
    h = m.construir_hojas(d, 'bogota')
    assert len(h['Homogeneidad_NASA']) == 8
    assert all(fin == 2000 for _, fin in llamados)
    assert llamados[-1][0] == 1984


def test_sin_modificar_producto_anterior(tmp_path):
    ruta = tmp_path / 'nasa_power_bogota.csv'
    anterior = tmp_path / 'nasa_power_bogota_actualizado.xlsx'
    anterior.write_bytes(b'original')
    diario().drop(columns=m.COLUMNAS[-1]).to_csv(ruta,index=False)
    with pytest.raises(KeyError):
        m.generar('bogota', tmp_path)
    assert anterior.read_bytes() == b'original'
