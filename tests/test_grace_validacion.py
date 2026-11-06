"""Pruebas reproducibles sin Streamlit, para datos de validación pluvial."""
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]
from siams import grace_analisis as mod


def test_identicos_doce_meses_kge_uno():
    x=pd.Series([11,15,24,13,17,18,37,21,22,23,18,27],dtype=float)
    m=mod.metricas_pares(x,x)
    assert m['n']==12
    assert abs(m['sesgo_mm_mes']) < 1e-9
    assert abs(m['rmse_mm_mes']) < 1e-9
    assert abs(m['r_pearson']-1) < 1e-9
    assert abs(m['kge_2009']-1) < 1e-9


def test_kge_no_publica_muestras_insuficientes():
    x=pd.Series([10,20,40,25],dtype=float)
    s=pd.Series([15,24,46,25],dtype=float)
    m=mod.metricas_pares(x,s)
    assert m['n']==4 and np.isnan(m['kge_2009'])
    assert abs(m['sesgo_mm_mes']-3.75)<1e-9


def test_pod_far_eventos_diarios():
    x=pd.Series([0,2,3,0,8,0],dtype=float)
    s=pd.Series([0,1,0,5,9,0],dtype=float)
    v=mod.pod_far_diario(x,s,umbral_mm=1.0)
    assert v['aciertos']==2 and v['omisiones']==1 and v['falsas_alarmas']==1
    assert abs(v['POD']-2/3)<1e-9 and abs(v['FAR']-1/3)<1e-9


def test_pares_reales_solo_meses_completos_y_pixeles_correctos():
    if not (RAIZ/'data/processed/actualizacion/chirps_leticia.csv').exists():
        return  # La suite completa de SIAMS con los datos externos verificará la unión.
    df=mod.cargar_validacion()
    assert len(df)==4, 'La estación 48015050 tiene 4 meses completos en la entrega revisada'
    assert not df.mes.duplicated().any()
    assert df.IDEAM_mm_mes.notna().all()
    t=mod.tabla_metricas(df)
    assert set(t.Producto)=={'CHIRPS v3','CHIRPS v2','IMERG Final V07','NASA POWER'}
    assert t['KGE 2009'].isna().all()
