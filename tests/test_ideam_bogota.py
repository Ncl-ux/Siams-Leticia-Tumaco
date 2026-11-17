import pandas as pd
from siams.ideam_bogota_datos import BASE, mensual, cargar_mensual


def test_mes_incompleto_no_se_anualiza():
    d=pd.DataFrame({'CodigoEstacion':'A','NombreEstacion':'A','Variable':'Precipitación','Fecha':pd.date_range('2020-02-01',periods=28),'Valor':1.,'NivelAprobacion':'Definitivo','Identificacion':'Explícita CSV'})
    m=mensual(d).iloc[0]
    assert m.DiasCalendario==29 and m.Dias==28
    assert pd.isna(m.Valor) and m.Valor90==28


def test_cero_es_precipitacion_valida():
    d=pd.DataFrame({'CodigoEstacion':'A','NombreEstacion':'A','Variable':'Precipitación','Fecha':pd.date_range('2020-02-01',periods=29),'Valor':0.,'NivelAprobacion':'Definitivo','Identificacion':'Explícita CSV'})
    assert mensual(d).iloc[0].Valor==0


def test_base_real_sin_duplicados_y_cobertura():
    d=pd.read_csv(BASE/'diario.csv',dtype={'CodigoEstacion':str})
    assert not d.empty
    assert not d.duplicated(['CodigoEstacion','Variable','Fecha']).any()
    m=cargar_mensual()
    assert set(m[m.Variable.eq('Precipitación')].CodigoEstacion)=={'21200610','21205012','21205230','21205520'}
    assert m.loc[m.Cobertura.lt(1),'Valor'].isna().all()
    assert m.loc[m.Cobertura.lt(.9),'Valor90'].isna().all()
    assert m.Dias.sum()==len(d)


def test_a1_diagnostico_real():
    r=pd.read_csv(BASE/'homogeneidad.csv',dtype={'estacion':str,'referencia':str})
    x=r[(r.variable=='Precipitación')&(r.estacion=='21205230')&(r.referencia=='—')&(r.criterio=='100%')].iloc[0]
    assert x.estado=='calculado' and x.n>=48 and 0<=x.p_bloques<=1
    assert r.loc[r.estado.eq('insuficiente'),'p_bloques'].isna().all()
