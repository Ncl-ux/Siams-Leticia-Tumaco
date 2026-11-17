import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def cargar():
    ruta = Path(__file__).resolve().parents[1] / 'scripts/12_actualizacion_semanal.py'
    spec = importlib.util.spec_from_file_location('actualizacion_prueba', ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_sedes_y_parametros():
    m = cargar()
    assert m.NASA_PARAM == m._nasa_original.PARAMETROS
    assert len(m.NASA_PARAM) == 8
    assert set(m.SEDES) == {'bogota', 'leticia', 'tumaco', 'arauca', 'la_paz', 'medellin', 'san_andres'}


def test_migracion_y_actualizacion(tmp_path, monkeypatch):
    m = cargar()
    m.SALIDA = tmp_path
    cols = list(m.NASA_PARAM.values())
    arch = tmp_path / 'nasa_power_bogota.csv'
    pd.DataFrame({'fecha': ['1981-01-01'], **{c: [9.] for c in cols[:5]}}).to_csv(arch, index=False)
    peticiones = []
    hoy = pd.Timestamp('1984-01-05')
    def descargar(lat, lon, inicio, fin):
        peticiones.append(inicio)
        df = pd.DataFrame({'fecha': pd.to_datetime([inicio, fin]), **{c: [1., 2.] for c in cols}})
        df.loc[0, cols[0]] = float('nan')
        df.loc[0, cols[-1]] = -999.
        return df, {'header': {}, 'parameters': {}}
    monkeypatch.setattr(m._nasa_original, 'descargar', descargar)
    m.nasa_power('bogota', 4.6, -74., hoy)
    d = pd.read_csv(arch)
    assert peticiones[0] == '1981-01-01'
    assert d.loc[0, cols[0]] == 9.
    assert pd.isna(d.loc[0, cols[-1]])
    assert d.fecha.is_unique
    assert len(d.columns) == 9
    m.nasa_power('bogota', 4.6, -74., hoy + pd.Timedelta(days=7))
    assert peticiones[1] == '1983-11-06'
    assert pd.read_csv(arch).fecha.is_unique


def test_respuesta_incompleta_no_sustituye_archivo(tmp_path, monkeypatch):
    m = cargar()
    m.SALIDA = tmp_path
    arch = tmp_path / 'nasa_power_bogota.csv'
    arch.write_text('fecha,precipitacion_mm_dia\n1981-01-01,2\n')
    anterior = arch.read_bytes()
    monkeypatch.setattr(m._nasa_original, 'descargar', lambda *args: (pd.DataFrame({'fecha': ['1981-01-01'], 'precipitacion_mm_dia': [3]}), {}))
    with pytest.raises(ValueError):
        m.nasa_power('bogota', 4.6, -74., pd.Timestamp('1984-01-05'))
    assert arch.read_bytes() == anterior
