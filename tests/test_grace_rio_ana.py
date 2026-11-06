from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
from siams import grace_datos as mod


def test_datos_publicos_y_fechas():
    d, m = mod.cargar_y_comparar()
    assert m['n'] >= 600
    assert d.fecha.is_unique
    assert np.isclose(d['ANA_cambio_relativo_m'].mean(), 0., atol=1e-10)
    assert np.isfinite(m['r_pearson'])


def test_ceros_diferentes_no_se_restan_como_cotas(tmp_path):
    p = tmp_path / 'test.csv'
    fechas = pd.date_range('2024-01-01', periods=40)
    pd.DataFrame({'fecha':fechas, 'ana_cota_m':np.arange(40.),
                  'ideam_nivel_m':np.arange(40.)+100.}).to_csv(p,index=False)
    a, m = mod.cargar_y_comparar(p)
    assert np.allclose(a['ANA_cambio_relativo_m'],a['IDEAM_cambio_relativo_m'])
    assert abs(m['r_pearson']-1)<1e-9
