"""A4: integridad cientifica, metadatos CF y cita del producto en SIAMS."""
from pathlib import Path
import hashlib
import numpy as np
from netCDF4 import Dataset

RAIZ = Path(__file__).resolve().parents[1]
NC = RAIZ / 'data' / 'processed' / 'grace' / 'COL_GWS_estimations.nc'
APP = RAIZ / 'app.py'
SHA_VALORES = 'a5562da4444f40b1c5c49de489a5cbc97c103edac8a3b63ce3cfea79f936359e'
SHA_EJES = {
    'lat': 'e47f4b55315f58f76642d2d8072540b6519eb3bfe23f3f45b8c246b9a48595b1',
    'lon': 'fa50a6ae06ae5b5dee57aac3f500f0bfa48dceed5ae12352decf3fbed8598337',
    'time': 'd31c240246aee5396de595c062d074fc2638fcc5530d6ac38ea424e0c827a6b3',
}


def test_a4_cf_y_fuente_documentada():
    assert NC.is_file()
    with Dataset(str(NC)) as ds:
        assert ds.getncattr('Conventions') == 'CF-1.8'
        assert '10.1016/j.ejrh.2025.102756' in ds.getncattr('references')
        assert 'no documentado' in ds.getncattr('anomaly_reference_period').lower()
        assert ds.variables['GWS_anom'].getncattr('units') == 'cm'
        assert ds.variables['lat'].getncattr('units') == 'degrees_north'
        assert ds.variables['lon'].getncattr('units') == 'degrees_east'
        assert ds.variables['GWS_anom'].getncattr('grid_mapping') == 'crs'
        assert ds.variables['crs'].getncattr('grid_mapping_name') == 'latitude_longitude'
        for eje in ('lat', 'lon', 'time'):
            var = ds.variables[eje]
            assert 'bounds' not in var.ncattrs() or var.getncattr('bounds') in ds.variables


def test_a4_matriz_gwsa_intacta():
    with Dataset(str(NC)) as ds:
        v = ds.variables['GWS_anom']
        assert v.shape == (244, 135, 99)
        valores = np.asarray(v[:], dtype=np.float64)
        assert hashlib.sha256(np.ascontiguousarray(valores).tobytes()).hexdigest() == SHA_VALORES
        for eje, checksum in SHA_EJES.items():
            e = np.asarray(ds.variables[eje][:], dtype=np.float64)
            assert hashlib.sha256(np.ascontiguousarray(e).tobytes()).hexdigest() == checksum


def test_a4_cita_visible_en_grace():
    contenido = APP.read_text(encoding='utf-8-sig')
    inicio = contenido.index('elif seccion == "Agua subterránea (GRACE)":')
    fin = contenido.index('elif seccion == "Hidrogeoquímica":', inicio)
    bloque = contenido[inicio:fin]
    assert 'SIAMS_A4_REFERENCIA_CF' in bloque
    assert 'https://doi.org/10.1016/j.ejrh.2025.102756' in bloque
