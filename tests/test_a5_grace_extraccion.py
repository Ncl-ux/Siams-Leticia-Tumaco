"""Pruebas mínimas del proceso A5 de extracción GRACE sin depender de datos del repositorio."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

h5py = pytest.importorskip('h5py')
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'extraer_grace_a5.py'
SPEC = importlib.util.spec_from_file_location('extraer_grace_a5', SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def _nc(ruta: Path):
    with h5py.File(ruta, 'w') as f:
        t = f.create_dataset('time', data=np.array([0., 31., 400.]))
        t.attrs['units'] = 'days since 2002-01-01T00:00:00+00:00'
        t.attrs['calendar'] = 'gregorian'
        f.create_dataset('lat', data=[8.,9.])
        f.create_dataset('lon', data=[-74., -73.])
        datos = np.array([[[1.,2.],[3.,4.]],[[5.,6.],[7.,8.]],[[np.nan,10.],[11.,12.]]])
        f.create_dataset('GWS_anom', data=datos)


def test_seleccion_y_saltos_preservados(tmp_path):
    nc = tmp_path / 'ejemplo.nc'; _nc(nc)
    filas, meta = MOD.extraer_serie(nc, 8.1, -73.1)
    assert len(filas) == 3
    assert [f['gws_anom_valor_original'] for f in filas] == [2.0, 6.0, 10.0]
    assert meta['longitud_celda'] == -73.0
    assert meta['saltos_temporales_mayores_45_dias'] == 1
    assert meta['observaciones_validas'] == 3
    assert meta['sha256_entrada'] == MOD.sha256_archivo(nc)


def test_no_se_sobrescribe_salida_existente(tmp_path):
    nc = tmp_path / 'ejemplo.nc'; _nc(nc)
    p1, p2, meta = MOD.exportar(nc, 8.1, -73.1, 'Aguachica', tmp_path)
    assert p1.exists() and p2.exists()
    with pytest.raises(FileExistsError):
        MOD.exportar(nc, 8.1, -73.1, 'Aguachica', tmp_path)
    assert meta['observaciones_totales'] == 3


def test_unidades_no_inventadas(tmp_path):
    nc=tmp_path/'ejemplo.nc'; _nc(nc)
    _, meta=MOD.extraer_serie(nc, 8., -74.)
    assert meta['unidades_en_variable_netcdf'] is None
    assert 'cm' in meta['unidades_desde_articulo_y_notebook']
