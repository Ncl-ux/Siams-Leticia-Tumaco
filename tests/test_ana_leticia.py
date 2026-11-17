import numpy as np
import pandas as pd
import pytest
from siams.ana_leticia_datos import serie_diaria, mensual, comparar, cargar_series, resumen, periodo_consulta


def test_huecos_y_niveles_negativos():
    s=serie_diaria(pd.DataFrame({'fecha':['2024-01-01','2024-01-03','2024-01-04'],'nivel_m':[-1,2,-9999]}),'nivel_m')
    assert s.iloc[0]==-1 and pd.isna(s.iloc[1]) and pd.isna(s.iloc[3])
    assert resumen(s)['cobertura']==50


def test_duplicados_rechazados():
    with pytest.raises(ValueError):
        serie_diaria(pd.DataFrame({'fecha':['2024-01-01']*2,'nivel_m':[1,2]}),'nivel_m')


def test_mes_bisiesto_solo_completo_y_media():
    s=pd.Series(2.,index=pd.date_range('2024-01-02','2024-03-01'))
    m=mensual(s)
    assert pd.isna(m.nivel_m.iloc[0]) and m.nivel_m.iloc[1]==2 and pd.isna(m.nivel_m.iloc[2])
    assert m.dias_validos.iloc[1]==29


def test_compatible_con_ceros_distintos_y_vacios():
    idx=pd.date_range('2024-01-01',periods=40)
    a=pd.Series(np.arange(40,dtype=float),index=idx,name='ANA Tabatinga'); b=(a+80).rename('IDEAM Leticia')
    a.iloc[8]=np.nan
    r,m=comparar({'ANA Tabatinga':a,'IDEAM Leticia':b})
    assert m['n']==39 and m['r_pearson']==pytest.approx(1)
    assert r.iloc[8].isna().all() and np.allclose(r.iloc[:,0],r.iloc[:,1],equal_nan=True)
    assert r.mean().abs().max()<1e-10
    _,p=comparar({'ANA Tabatinga':a.iloc[:3],'IDEAM Leticia':b.iloc[:3]}); assert np.isnan(p['r_pearson'])


def test_reutiliza_serie_publica_y_alternativa_sin_empalmar(tmp_path):
    f=pd.date_range('2024-01-01',periods=4)
    pd.DataFrame({'fecha':f[:2],'cota_m':[3,4]}).to_csv(tmp_path/'ana_diario.csv',index=False)
    p=tmp_path/'comunes.csv';pd.DataFrame({'fecha':f,'ana_cota_m':[1,1,1,1],'ideam_nivel_m':[5,6,7,8]}).to_csv(p,index=False)
    s,o,a=cargar_series(tmp_path,p)
    assert not a and o['ANA Tabatinga']=='ana_diario.csv' and len(s['ANA Tabatinga'])==2 and len(s['IDEAM Leticia'])==4


def test_faltantes_no_bloquean_otra_estacion(tmp_path):
    pd.DataFrame({'fecha':['2024-01-01'],'nivel_m':[3]}).to_csv(tmp_path/'rio_diario.csv',index=False)
    s,o,a=cargar_series(tmp_path,tmp_path/'no.csv'); assert list(s)==['IDEAM Leticia'] and 'ANA Tabatinga' in a


@pytest.mark.parametrize('modo, inicio', [
    ('Histórico completo', '2000-01-01'),
    ('Últimos 10 años', '2015-09-16'),
    ('Últimos 5 años', '2020-09-16'),
    ('Último año disponible', '2025-01-01'),
])
def test_periodos_rapidos_anclados_a_observacion(modo, inicio):
    s = pd.Series(1., index=pd.date_range('2000-01-01', '2025-09-15'))
    assert periodo_consulta(s, modo) == (pd.Timestamp(inicio), pd.Timestamp('2025-09-15'))


def test_periodo_una_fecha_y_una_serie_corta():
    s = pd.Series([11.85], index=pd.to_datetime(['2026-01-01']))
    for modo in ('Histórico completo', 'Últimos 5 años', 'Últimos 10 años', 'Último año disponible', 'Personalizado'):
        assert periodo_consulta(s, modo) == (s.index[0], s.index[0])


def test_personalizado_valida_fechas():
    s = pd.Series(1., index=pd.date_range('2020-01-01', '2024-12-31'))
    assert periodo_consulta(s, 'Personalizado', '2021-01-01', '2022-12-31') == (pd.Timestamp('2021-01-01'), pd.Timestamp('2022-12-31'))
    for a,b in [('2022-01-01','2021-01-01'),('2019-01-01','2021-01-01'),('2021-01-01','2025-01-01')]:
        with pytest.raises(ValueError):
            periodo_consulta(s, 'Personalizado', a, b)


def test_periodo_no_incluye_extremos_sin_datos():
    s = pd.Series([np.nan, 2., np.nan, 3., np.nan], index=pd.date_range('2024-01-01', periods=5))
    assert periodo_consulta(s) == (s.index[1], s.index[3])
