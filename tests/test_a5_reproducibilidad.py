"""Pruebas de rutas reproducibles sin sobrescribir resultados existentes."""
from pathlib import Path
import importlib.util
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def _modulo(path):
    spec=importlib.util.spec_from_file_location('siams_a5_script', ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_directorios_y_productos_a5():
    for sub in ('raw','processed'):
        assert (ROOT/'data'/sub).is_dir()
    assert len(list((ROOT/'data/raw/swot').rglob('plot_*.csv'))) == 80
    assert len(list((ROOT/'data/processed/swot').glob('SWOT_*_reach_*.csv'))) == 20
    assert len(list((ROOT/'data/processed/clima').glob('*.xlsx'))) == 8
    assert (ROOT/'data/processed/grace/COL_GWS_estimations.nc').exists()
    assert (ROOT/'Animaciones_SWOT').exists()
    assert (ROOT/'Tarjetas_SWOT/01_WSE_Leticia_SWOT.png').exists()

def test_swot_regeneracion_desde_raw(tmp_path):
    modulo=_modulo('scripts/procesar_swot.py')
    resultado=modulo.regenerar(salida=tmp_path)
    assert len(resultado)==20
    assert resultado.fechas_unicas.sum()==1957
    assert resultado.saltos_para_revisar.sum()==76
    assert (resultado.banderas_oficiales=='NO_PRESENTES').all()
    assert len(list(tmp_path.glob('SWOT_*_reach_*.csv')))==20
    ejemplo=pd.read_csv(tmp_path/'SWOT_Leticia_reach_62297600021.csv',dtype={'reach_id':str})
    assert len(ejemplo)==97
    assert ejemplo.fecha_utc.is_unique

def test_clima_y_hidrogeoquimica_respetan_rutas():
    import pytest
    pytest.importorskip('streamlit')
    from siams import utilidades, grace, hidrogeoquimica_datos as hd, mapbiomas, landsat
    assert utilidades.CARPETA_DATOS_HIDRO.samefile(ROOT/'data/processed/clima')
    assert grace.encontrar_archivo_gws().samefile(ROOT/'data/processed/grace/COL_GWS_estimations.nc')
    assert hd.BASE.samefile(ROOT/'data/processed/hidrogeoquimica/siams_fq_largo.csv')
    assert mapbiomas.encontrar_csv_coberturas('Leticia','L')['serie']
    assert landsat.inventario_landsat('Leticia')['areas'] is not None
