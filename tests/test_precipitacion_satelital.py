import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from siams.precipitacion_satelital_datos import mensual,nasa_mensual,pares,cargar,inventario,SEDES

ROOT=Path(__file__).resolve().parents[1]
def mod(nombre):
    spec=importlib.util.spec_from_file_location('test_'+nombre,ROOT/'scripts'/nombre)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_meses_invalidos_y_curso():
    d=pd.DataFrame({'fecha':['2024-01-01','2024-02-01','2024-03-01'],'precipitacion_mm_mes':[0,-9999,150]})
    s=mensual(d,hoy='2024-03-12'); assert s.iloc[0]==0 and pd.isna(s.iloc[1]) and len(s)==2
    with pytest.raises(ValueError): mensual(pd.concat([d,d]))

def test_nasa_solo_meses_completos():
    f=pd.date_range('2024-01-01','2024-03-02')
    d=pd.DataFrame({'fecha':f,'precipitacion_mm_dia':1.})
    d.loc[d.fecha.eq('2024-02-10'),'precipitacion_mm_dia']=-999
    s=nasa_mensual(d,hoy='2024-03-04'); assert s.iloc[0]==31 and pd.isna(s.iloc[1]) and len(s)==2

def test_cargar_independiente(tmp_path):
    for f,v in [('chirps_bogota.csv',[10,np.nan,0]),('imerg_final_bogota.csv',[20,30,10])]:
        pd.DataFrame({'fecha':pd.date_range('2020-01-01',periods=3,freq='MS'),'precipitacion_mm_mes':v}).to_csv(tmp_path/f,index=False)
    t,avisos=cargar('bogota',tmp_path,hoy='2021-01-01'); assert len(t.columns)==2 and 'NASA POWER' in avisos
    r=pares(t,'CHIRPS v3 Final').iloc[0]; assert r['Meses comunes']==2 and r['Sesgo (mm)']==10
    assert inventario(t).iloc[0]['Huecos internos']==1
    assert len(SEDES)==8 and SEDES["Chingaza"]=="chingaza"

def test_chirps_no_reemplaza_valido_por_nulo(tmp_path,monkeypatch):
    m=mod('12_actualizacion_semanal.py'); m.SALIDA=tmp_path; m.INICIO['chirps']='2024-01-01'
    arch=tmp_path/'chirps_bogota.csv'
    pd.DataFrame({'fecha':['2024-01-01','2024-02-01'],'precipitacion_mm_mes':[5,np.nan]}).to_csv(arch,index=False)
    visto=[]
    def respuesta(a,b):
        visto.append(b);return {'bogota':{1:float('nan'),2:42,3:0}[b]}
    monkeypatch.setattr(m,'_chirps_mes',respuesta)
    assert m.chirps('bogota',0,0,pd.Timestamp('2024-04-15'))==3
    d=pd.read_csv(arch);assert d.precipitacion_mm_mes.tolist()==[5,42,0] and 4 not in visto
    anterior=arch.read_bytes();monkeypatch.setattr(m,'_chirps_mes',lambda *a:None)
    assert m.chirps('bogota',0,0,pd.Timestamp('2024-04-15'))==0 and arch.read_bytes()==anterior

def test_imerg_conversion_mensual_y_guarda(tmp_path):
    import h5py
    m=mod('16_actualizar_imerg.py')
    f=tmp_path/'3B-MO.MS.MRG.3IMERG.20240201-S000000-E235959.02.V07B.HDF5'
    with h5py.File(f,'w') as h:
        g=h.create_group('Grid');g['lat']=np.arange(-89.95,90,.1);g['lon']=np.arange(-179.95,180,.1)
        p=g.create_dataset('precipitation',shape=(1,3600,1800),dtype='f4',chunks=(1,10,10),fillvalue=-9999.)
        p.attrs['units']=b'mm/hr'; p.attrs['_FillValue']=-9999.;p[0,100,100]=.5
        y=g['lat'][100];x=g['lon'][100]
    fila=m.extraer(f,{'a':(y,x),'b':(0.,0.)}); assert set(fila)=={'a'} and fila['a'][m.COL]==348
    arch=tmp_path/'imerg_final_a.csv';m.guardar(arch,fila['a']);m.guardar(arch,fila['a']);assert len(m.leer(arch))==1
    with pytest.raises(ValueError):m.mes_archivo(str(f).replace('V07B','V06B'))


def test_chirps_compartido_y_guardado_incremental(tmp_path, monkeypatch):
    m = mod('12_actualizacion_semanal.py'); m.SALIDA = tmp_path
    m.INICIO['chirps'] = '2023-01-01'
    llamadas = []
    def respuesta(a,b):
        llamadas.append((a,b))
        if a == 2024:
            assert len(pd.read_csv(tmp_path/'chirps_medellin.csv')) == 12
            assert len(pd.read_csv(tmp_path/'chirps_san_andres.csv')) == 12
        return {'medellin': 10., 'san_andres': 20.}
    monkeypatch.setattr(m, '_chirps_mes', respuesta)
    sedes = ['medellin', 'san_andres']
    assert m.chirps_sedes(sedes, pd.Timestamp('2024-02-15')) == dict.fromkeys(sedes, 13)
    assert len(llamadas) == len(set(llamadas)) == 13
    llamadas.clear()
    # La siguiente ejecución solo consulta los tres meses de reproceso.
    monkeypatch.setattr(m, '_chirps_mes', lambda a,b: llamadas.append((a,b)) or {'medellin': 10., 'san_andres': 20.})
    assert m.chirps_sedes(sedes, pd.Timestamp('2024-02-15')) == dict.fromkeys(sedes, 13)
    assert len(llamadas) == 3
