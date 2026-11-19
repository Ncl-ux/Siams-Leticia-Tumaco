import json
import pandas as pd
import pytest
from siams.chingaza_datos import BASE, agregar_diario, agregar_nasa, anual_completo, leer_eaab, NASA_COLUMNAS, referencia
from siams.precipitacion_satelital_datos import cargar

def test_eaab_productos_mensuales():
    d=leer_eaab(); assert d.estacion.nunique()==30 and d.valor.count()==9080
    assert d.loc[d.valor.notna(),'dias_validos'].eq(d.loc[d.valor.notna(),'dias_mes']).all()
    assert d.loc[d.dias_validos.ne(d.dias_mes),'valor'].isna().all()
    assert set(d.variable)=={'Precipitación','Caudal'}

def test_agregacion_precipitacion_y_caudal():
    f=pd.date_range('2024-01-01','2024-03-31'); d=pd.DataFrame(dict(fecha=f,valor=2.,flag=None)); d.loc[d.fecha.eq('2024-02-10'),'flag']='r'
    p=agregar_diario(d,'sum'); q=agregar_diario(d,'mean'); assert p.valor.iloc[0]==62 and q.valor.iloc[0]==2
    assert pd.isna(p.valor.iloc[1]) and p.dias_validos.iloc[1]==28 and p.valor.iloc[2]==62
    with pytest.raises(ValueError): agregar_diario(pd.concat([d,d]),'sum')

def test_nasa_meses_completos_y_sin_mes_en_curso(tmp_path):
    f=pd.date_range('2024-01-01','2024-03-20'); cols=list(NASA_COLUMNAS); cols[0]='precipitacion_mm_dia'; d=pd.DataFrame({'fecha':f,**{c:1. for c in cols}})
    d.loc[d.fecha.eq('2024-02-10'),'precipitacion_mm_dia']=-999
    m=agregar_nasa(d,'2024-03-20'); assert len(m)==2 and m.precipitacion_mm_mes.iloc[0]==31 and pd.isna(m.precipitacion_mm_mes.iloc[1]); assert m.temperatura_media_C.iloc[1]==1
    m.to_csv(tmp_path/'nasa_power_chingaza_mensual.csv',index=False); t,_=cargar('chingaza',tmp_path,hoy='2024-04-01'); assert t['NASA POWER'].iloc[0]==31

def test_anual_solo_doce_meses():
    d=pd.DataFrame({'fecha':pd.date_range('2023-01-01',periods=23,freq='MS'),'valor':2.}); a=anual_completo(d,'sum'); assert a.anio.tolist()==[2023] and a.valor.tolist()==[24]
    assert anual_completo(d,'mean').valor.tolist()==[2]

def test_cartografia_inventario():
    meta=json.loads((BASE/'cartografia.json').read_text(encoding='utf-8')); assert len(meta['capas'])==9
    assert sum(c['elementos'] for c in meta['capas'])==285
    for c in meta['capas']:
        g=json.loads((BASE/c['archivo']).read_text(encoding='utf-8')); assert len(g['features'])==c['elementos']
        assert all(set(f['properties'])=={'capa'} for f in g['features'])
    r=referencia(); assert 4<r['lat']<5 and -74<r['lon']<-73


@pytest.mark.parametrize('nombre', ['CHIRPS v3 Final', 'NASA POWER', 'IMERG Final V07B (NASA)', None])
def test_anual_desde_serie_nombre_original(nombre):
    from siams.chingaza_datos import anual_desde_serie
    serie = pd.Series(2., index=pd.date_range('2023-01-01', periods=23, freq='MS'), name=nombre)
    a = anual_desde_serie(serie, 'sum')
    assert a.anio.tolist() == [2023] and a.valor.tolist() == [24.]
    assert anual_desde_serie(serie, 'mean').valor.tolist() == [2.]
    assert serie.name == nombre


def test_comparacion_mensual_identidad_y_sesgo():
    from siams.chingaza_datos import comparar_precipitacion_mensual
    t = pd.DataFrame({'Observada':[1.,2.,3.,4.], 'Exacta':[1.,2.,3.,4.], 'Doble':[2.,4.,6.,8.]},
                     index=pd.date_range('2024-01-01', periods=4, freq='MS'))
    r = comparar_precipitacion_mensual(t).set_index('Fuente')
    assert r.loc['Exacta','KGE 2009'] == pytest.approx(1)
    assert r.loc['Exacta','NSE'] == pytest.approx(1)
    assert r.loc['Exacta','RMSE (mm)'] == 0
    assert r.loc['Doble','PBIAS (%)'] == pytest.approx(100)
    assert r.loc['Doble','Sesgo (mm)'] == pytest.approx(2.5)


def test_comparacion_mensual_faltantes_y_constantes():
    from siams.chingaza_datos import comparar_precipitacion_mensual
    t = pd.DataFrame({'Observada':[0.,0.,0.,0.], 'Producto':[0.,1.,None,-1.]},
                     index=pd.date_range('2024-01-01', periods=4, freq='MS'))
    r = comparar_precipitacion_mensual(t).iloc[0]
    assert r['Meses comunes'] == 2
    assert pd.isna(r['KGE 2009']) and pd.isna(r['NSE']) and pd.isna(r['PBIAS (%)'])
    assert r['MAE (mm)'] == pytest.approx(.5)
    with pytest.raises(ValueError):
        comparar_precipitacion_mensual(pd.concat([t,t]))


def test_ruta_homogeneidad_chingaza_activa():
    import ast
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    app = (raiz/'app.py').read_text(encoding='utf-8-sig').splitlines()
    activa = next(l for l in app if l.startswith('if territorio == "Chingaza" and seccion in {'))
    pendiente = next(l for l in app if l.startswith('elif territorio == "Chingaza" and seccion in {'))
    assert '"Homogeneidad (A1)"' in activa and '"Homogeneidad (A1)"' not in pendiente
    arbol = ast.parse((raiz/'siams/chingaza.py').read_text(encoding='utf-8-sig'))
    mostrar = next(n for n in arbol.body if isinstance(n,ast.FunctionDef) and n.name=='mostrar')
    assert any(isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(c,ast.Constant) and c.value=='Homogeneidad (A1)' for c in n.test.comparators) for n in ast.walk(mostrar))
