import pandas as pd
import numpy as np
import pytest
from siams.ideam_bogota_datos import cargar_mensual
from siams.ideam_bogota_clima_datos import nasa_mensual, pares_mensuales, regimen_pareado, anuales_ideam, paquetes_ideam


def meses(fecha, variable='Precipitación', codigo='A', valor=10):
    f = pd.date_range(fecha, periods=12, freq='MS')
    return pd.DataFrame({'CodigoEstacion':codigo,'Variable':variable,'MesFecha':f,'Dias':f.days_in_month,'Valor':valor,'Definitivos':f.days_in_month,'Inferidos':0})


def test_contraste_solo_meses_comunes_completos():
    m = meses('2020-01-01');m.loc[1,'Dias'] -= 1
    d = pd.DataFrame({'fecha':pd.date_range('2020-01-01','2020-03-30'),'precipitacion_mm_dia':1.})
    p = pares_mensuales(m,d,'A','Precipitación')
    assert len(p)==1 and p.iloc[0]['NASA POWER']==31 and p.iloc[0].IDEAM==10
    r = regimen_pareado(p)
    assert r.Pares.sum()==1 and pd.isna(r.loc[r.Mes.eq(2),'NASA']).all()


def test_cero_valido_y_faltante_nasa():
    d=pd.DataFrame({'fecha':pd.date_range('2020-01-01','2020-02-29'),'precipitacion_mm_dia':0.})
    d.loc[31,'precipitacion_mm_dia']=-999
    r=nasa_mensual(d,'Precipitación')
    assert len(r)==1 and r.iloc[0]['NASA POWER']==0
    with pytest.raises(ValueError): nasa_mensual(pd.concat([d,d.iloc[:1]]),'Precipitación')


def test_anuales_no_mezclar_ni_anualizar():
    a=meses('2020-01-01'); b=meses('2021-01-01'); b=b.iloc[:-1]
    c=meses('2021-01-01',codigo='B').iloc[-1:]
    r=anuales_ideam(pd.concat([a,b,c]))
    assert len(r)==1 and r.iloc[0].Valor==120 and r.iloc[0].Dias==366


def test_media_anual_ponderada():
    m=meses('2020-01-01','Temperatura media',valor=20);m.loc[1,'Valor']=10
    r=anuales_ideam(m)
    assert np.isclose(r.iloc[0].Valor,(20*337+10*29)/366)


def test_base_real_paquetes_sin_reemplazos():
    m=cargar_mensual(); p=paquetes_ideam(m,{})
    assert len(p)==3
    assert all(k.startswith('Precipitación') and 'IDEAM' in k for k in p)
    assert sorted(len(v['serie']) for v in p.values())==[6,19,20]
    assert all(v['serie'].Fecha.dt.month.eq(1).all() for v in p.values())
