"""NASA GES DISC GPM_3IMERGM V07B Final; una descarga mensual para siete sedes.

Credenciales por Earthdata Login, nunca se guardan en repo. Sin mezcla de productos.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ/'data/processed/actualizacion'
INICIO = pd.Timestamp('1998-01-01')
COL = 'precipitacion_mm_mes'
COLECCION = 'GPM_3IMERGM'


def sedes():
    spec = importlib.util.spec_from_file_location('actualizacion_siams',RAIZ/'scripts/12_actualizacion_semanal.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.SEDES


def mes_archivo(nombre):
    m = re.search(r'3B-MO\..*?\.3IMERG\.(\d{8})-S\d{6}-E\d{6}\..*?\.V07B(?:\.|$)', str(nombre))
    if not m: raise ValueError('Granule no reconocido como IMERG Final mensual V07B')
    f = pd.to_datetime(m.group(1),format='%Y%m%d')
    if f.day != 1: raise ValueError('Granule mensual no comienza el día 1')
    return f


def extraer(ruta, puntos):
    """HDF5 oficial: tasa mensual media mm/h × horas del mes calendario.
    Comprueba unidades, rejilla, orientación y factores CF declarados.
    """
    import h5py
    mes=mes_archivo(Path(ruta).name)
    with h5py.File(ruta,'r') as h:
        g=h['Grid']; lat=np.asarray(g['lat']).reshape(-1); lon=np.asarray(g['lon']).reshape(-1)
        v=g['precipitation']
        unidad=v.attrs.get('units','')
        if isinstance(unidad,np.ndarray): unidad=unidad.item()
        if isinstance(unidad,bytes): unidad=unidad.decode()
        if unidad.strip().lower() not in {'mm/hr','mm/h','mm h-1','mm hour-1','mm hr-1','mm/hour'}:
            raise ValueError(f'Unidad IMERG no reconocida: {unidad}')
        if len(lat)!=1800 or len(lon)!=3600 or not np.allclose(np.abs(np.diff(lat)),.1,atol=.0001) or not np.allclose(np.abs(np.diff(lon)),.1,atol=.0001):
            raise ValueError('Malla IMERG inesperada')
        if not np.allclose([lat.min(),lat.max(),lon.min(),lon.max()],[-89.95,89.95,-179.95,179.95],atol=.001):
            raise ValueError('Extensión IMERG inesperada')
        if v.shape==(1,len(lon),len(lat)): orden='lonlat'
        elif v.shape==(1,len(lat),len(lon)): orden='latlon'
        else: raise ValueError(f'Dimensiones inesperadas: {v.shape}')
        escala=float(np.asarray(v.attrs.get('scale_factor',1)).item()); offset=float(np.asarray(v.attrs.get('add_offset',0)).item())
        fill=np.asarray(v.attrs.get('_FillValue',-9999)).reshape(-1).tolist()+np.asarray(v.attrs.get('missing_value',-9999)).reshape(-1).tolist()
        res={}
        for sede,(y,x) in puntos.items():
            i=int(np.argmin(abs(lat-y)));j=int(np.argmin(abs(lon-x)))
            if abs(lat[i]-y)>.051 or abs(lon[j]-x)>.051: raise ValueError('Coordenada fuera de píxel IMERG')
            raw=float(v[0,j,i] if orden=='lonlat' else v[0,i,j]); val=raw*escala+offset
            if raw not in fill and raw>=0 and np.isfinite(val) and val>=0:
                res[sede]={'fecha':mes,COL:round(val*24*mes.days_in_month,4),'lat_pixel':float(lat[i]),'lon_pixel':float(lon[j]),'granulo':Path(ruta).name}
        return res


def leer(arch):
    if not arch.exists(): return pd.DataFrame(columns=['fecha',COL,'lat_pixel','lon_pixel','granulo'])
    d=pd.read_csv(arch,parse_dates=['fecha'])
    if d.fecha.isna().any() or d.fecha.duplicated().any() or not d.fecha.dt.day.eq(1).all(): raise ValueError(f'Fechas inválidas: {arch.name}')
    if not set(['fecha',COL,'lat_pixel','lon_pixel','granulo']).issubset(d.columns): raise ValueError(f'Esquema inválido: {arch.name}')
    if not d.granulo.astype(str).str.contains(r'\.V07B\.',regex=True).all(): raise ValueError('No se mezclan archivos de otras versiones')
    return d


def guardar(arch, fila):
    d=leer(arch)
    nuevo=pd.DataFrame([fila]); d=(nuevo if d.empty else pd.concat([d,nuevo],ignore_index=True)).drop_duplicates('fecha',keep='last').sort_values('fecha')
    tmp=arch.with_suffix('.csv.tmp'); d.to_csv(tmp,index=False,date_format='%Y-%m-%d'); os.replace(tmp,arch)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--desde',default='1998-01-01')
    ap.add_argument('--hasta',default=None)
    ap.add_argument('--max-meses',type=int,default=0,help='0: sin límite; actualizar histórico por bloques si se desea')
    ap.add_argument('--no-interactivo',action='store_true')
    ap.add_argument('--auditar',action='store_true',help='solo revisa archivos locales, no accede a NASA')
    args=ap.parse_args(argv)
    puntos=sedes(); SALIDA.mkdir(parents=True,exist_ok=True)
    paths={s:SALIDA/f'imerg_final_{s}.csv' for s in puntos}
    inicio=max(INICIO,pd.Timestamp(args.desde).replace(day=1))
    ultimo=pd.Timestamp.today().normalize().replace(day=1)-pd.offsets.MonthBegin(1)
    fin=min(ultimo,pd.Timestamp(args.hasta).replace(day=1)) if args.hasta else ultimo
    if fin<inicio or args.max_meses<0: ap.error('Periodo o límite inválido')
    vistos={}
    for sede,p in paths.items():
        d=leer(p); val=pd.to_numeric(d[COL],errors='coerce'); f=d.loc[val.ge(0)&np.isfinite(val),'fecha']
        vistos[sede]=set(f)
        print(sede, len(f),str(f.min()) if len(f) else '-',str(f.max()) if len(f) else '-',flush=True)
    if args.auditar:return 0
    import earthaccess
    auth=earthaccess.login(strategy='environment') if args.no_interactivo else earthaccess.login()
    if not auth.authenticated: raise RuntimeError('Earthdata Login no autorizado')
    # CMR devuelve los meses publicados, no se inventa un mes reciente.
    granulos=earthaccess.search_data(short_name=COLECCION,version='07',temporal=(inicio.strftime('%Y-%m-%d'),(fin+pd.offsets.MonthEnd(0)).strftime('%Y-%m-%dT23:59:59')),count=-1)
    por_mes={}
    for gran in granulos:
        nombre=gran['umm']['GranuleUR']
        try:f=mes_archivo(nombre)
        except ValueError:continue
        if inicio<=f<=fin:
            if f in por_mes:raise ValueError(f'Más de un granule V07B para {f:%Y-%m}; revisar CMR')
            por_mes[f]=gran
    if not por_mes: raise RuntimeError('CMR no devolvió meses Final V07B reconocidos; no se altera ningún CSV')
    recientes=set(sorted(por_mes)[-3:]); pendientes=[f for f in sorted(por_mes) if any(f not in v for v in vistos.values()) or f in recientes]
    # Priorizar meses nuevos o faltantes; si hay límite, procesar histórico progresivamente.
    pendientes.sort(key=lambda f:(not any(f not in v for v in vistos.values()),-f.value))
    if args.max_meses: pendientes=pendientes[:args.max_meses]
    errores=0; procesados=0
    for f in pendientes:
        try:
            with tempfile.TemporaryDirectory(prefix='siams_imerg_') as tmp:
                files=earthaccess.download([por_mes[f]],local_path=tmp,threads=1)
                if len(files)!=1:raise ValueError('Descarga ausente o múltiple')
                if mes_archivo(Path(files[0]).name)!=f:raise ValueError('Fecha de archivo no coincide con CMR')
                out=extraer(files[0],puntos)
                if not out:raise ValueError('Ningún píxel válido')
                for sede,fila in out.items():guardar(paths[sede],fila)
                if len(out)<len(puntos):
                    errores+=1; print(f'{f:%Y-%m}: sin valor en {sorted(set(puntos)-set(out))}',flush=True)
                procesados+=1; print(f'{f:%Y-%m}: {len(out)} sedes',flush=True)
        except Exception as e:
            errores+=1; print(f'{f:%Y-%m}: {type(e).__name__}: {e}',flush=True)
    meta={'coleccion':COLECCION,'version_archivo':'V07B','doi':'10.5067/GPM/IMERG/3B-MONTH/07','unidad':'mm/mes','ultimo_mes_publicado_CMR':str(max(por_mes).date()),'meses_procesados_en_corrida':procesados,'errores':errores,'pendientes_no_procesados':max(0,len([f for f in por_mes if any(f not in v for v in vistos.values()) or f in recientes])-len(pendientes)),'fecha_corrida_utc':pd.Timestamp.now(tz='UTC').isoformat()}
    (SALIDA/'imerg_consulta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return int(errores>0)

if __name__=='__main__':raise SystemExit(main())
