"""Descargas puntuales compatibles con SIAMS. NASA POWER abierto conserva el histórico diario y el agregado mensual.
No altera los actualizadores generales ni los datos de otras sedes.
"""
import argparse,importlib.util,sys,json,tempfile
from pathlib import Path
import pandas as pd
RAIZ=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(RAIZ))
from siams.chingaza_datos import ACT,referencia,agregar_nasa

def cargar(nombre):
    p=RAIZ/'scripts'/nombre; spec=importlib.util.spec_from_file_location(p.stem,p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def nasa(lat,lon):
    mod=cargar('12_actualizacion_semanal.py'); mod.SALIDA=ACT
    hoy=pd.Timestamp.today().normalize()
    mod.nasa_power('chingaza',lat,lon,hoy)
    diario=ACT/'nasa_power_chingaza.csv'
    d=pd.read_csv(diario,parse_dates=['fecha'])
    m=agregar_nasa(d,hoy)
    if m.empty or m.drop(columns='fecha').notna().sum().min()==0: raise ValueError('NASA: variables sin meses completos')
    dest=ACT/'nasa_power_chingaza_mensual.csv'; tmp=dest.with_suffix('.csv.tmp'); m.to_csv(tmp,index=False,date_format='%Y-%m-%d'); tmp.replace(dest)
    consulta=json.loads(diario.with_suffix('.consulta.json').read_text(encoding='utf-8'))
    (ACT/'nasa_power_chingaza_mensual.consulta.json').write_text(json.dumps({'fuente':'NASA POWER AG','lat':lat,'lon':lon,'consulta':consulta,'agregacion':'meses completos; precipitación suma, otras variables promedio de registros diarios'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'NASA POWER Chingaza: {len(m)} meses calendario; {m.precipitacion_mm_mes.count()} meses válidos de P',flush=True)

def chirps(lat,lon):
    mod=cargar('12_actualizacion_semanal.py'); mod.SEDES={'chingaza':(lat,lon)}; mod.SALIDA=ACT
    print(mod.chirps_sedes(['chingaza'],pd.Timestamp.today().normalize()),flush=True)

def imerg(lat,lon,limite,no_interactivo):
    mod=cargar('16_actualizar_imerg.py'); mod.sedes=lambda:{'chingaza':(lat,lon)}
    # El JSON de consulta general se conserva intacto. Se guardan filas mensuales incrementalmente en la misma carpeta.
    # Utilizar un directorio temporal de trabajo con copia del histórico previo, después promover el resultado.
    import shutil
    with tempfile.TemporaryDirectory(prefix='siams_chingaza_imerg_') as tmp:
        mod.SALIDA=Path(tmp); name='imerg_final_chingaza.csv'; actual=ACT/name
        if actual.exists(): shutil.copy2(actual,mod.SALIDA/name)
        args=['--max-meses',str(limite)]+(['--no-interactivo'] if no_interactivo else [])
        try: return mod.main(args)
        finally:
            for src,dest in [(mod.SALIDA/name,actual),(mod.SALIDA/'imerg_consulta.json',ACT/'imerg_chingaza_consulta.json')]:
                if src.is_file():
                    p=dest.with_suffix(dest.suffix+'.tmp'); shutil.copy2(src,p); p.replace(dest)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--fuente',choices=['nasa_power','chirps','imerg'],required=True); p.add_argument('--max-meses',type=int,default=0); p.add_argument('--no-interactivo',action='store_true'); a=p.parse_args()
    ACT.mkdir(parents=True,exist_ok=True); r=referencia(); lat,lon=r['lat'],r['lon']; print(f'Referencia puntual PNN: {lat}, {lon}',flush=True)
    if a.fuente=='nasa_power': nasa(lat,lon)
    elif a.fuente=='chirps': chirps(lat,lon)
    else: return imerg(lat,lon,a.max_meses,a.no_interactivo)
if __name__=='__main__': raise SystemExit(main())
