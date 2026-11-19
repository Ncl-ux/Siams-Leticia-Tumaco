import importlib.util
from pathlib import Path
import pytest
np=pytest.importorskip('numpy'); pytest.importorskip('rasterio');pytest.importorskip('matplotlib')
p=Path(__file__).resolve().parents[1]/'scripts/23_chingaza_relieve.py'
spec=importlib.util.spec_from_file_location('relieve_script',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_pendiente_plano():
    d=np.tile(np.arange(10)*30.,(10,1)); assert np.allclose(m.pendiente(d),45)
    d=np.full((10,10),2500.); assert np.allclose(m.pendiente(d),0)
def test_pendiente_nodata():
    d=np.ones((10,10));d[4,4]=np.nan; s=m.pendiente(d);assert np.isnan(s[4,4]) and np.isnan(s[4,3]) and np.isnan(s[3,4])
