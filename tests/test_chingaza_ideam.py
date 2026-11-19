from pathlib import Path
import pandas as pd
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('procesar_ideam',ROOT/'scripts/22_procesar_ideam_chingaza.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_mes_completo_y_faltante():
    f=pd.date_range('2024-02-01','2024-03-30');d=pd.DataFrame({'Fecha':f,'Valor':1.})
    a=m.agregar(d,'PTPM_CON'); assert a.valor.iloc[0]==29 and pd.isna(a.valor.iloc[1])
def test_duplicados_no_publicados():
    f=pd.date_range('2024-02-01','2024-02-29');d=pd.DataFrame({'Fecha':f,'Valor':1.});a=m.agregar(pd.concat([d,d.iloc[:1]]),'PTPM_CON');assert pd.isna(a.valor.iloc[0])
def test_humedad_horarios():
    f=pd.date_range('2024-02-01','2024-02-29');d=pd.DataFrame({'Fecha':[v+pd.Timedelta(hours=h) for v in f for h in (7,13,19)],'Valor':70.});assert m.agregar(d,'HRHG_CON').valor.iloc[0]==70;assert pd.isna(m.agregar(d.iloc[1:],'HRHG_CON').valor.iloc[0])
def test_insumos_mensuales():
    b=ROOT/'data/processed/chingaza';d=pd.read_csv(b/'ideam_mensual.csv',parse_dates=['fecha']);i=pd.read_csv(b/'ideam_inventario.csv');e=pd.read_csv(b/'ideam_estaciones.csv');assert len(e)==82 and e.series_en_entrega.sum()==37 and len(i)==51;assert d.valor.count()==17637;assert d.fecha.dt.day.eq(1).all();assert not d.duplicated(['estacion','etiqueta','fecha']).any();assert d.loc[d.valor.notna(),'dias_validos'].eq(d.loc[d.valor.notna(),'dias_mes']).all();assert not d.etiqueta.str.startswith(('EV_AUT','EV_TT')).any()
