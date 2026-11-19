"""Procesamiento local. Los originales permanecen fuera del repositorio público.
Uso: python scripts/22_procesar_ideam_chingaza.py --zip RUTA --catalogo-csv RUTA
El CSV es la exportación del CNE_IDEAM.xls original (primera hoja).
"""
import argparse, io, json, zipfile
from pathlib import Path
import pandas as pd
import numpy as np

VARIABLES = {
    'PTPM_CON': ('Precipitación','mm/mes','sum'),
    'TSSM_MEDIA_D': ('Temperatura seca media','°C','mean'),
    'THSM_MEDIA_D': ('Temperatura húmeda media','°C','mean'),
    'EVTE_CON': ('Evaporación convencional','mm/mes','sum'),
    'HRHG_CON': ('Humedad relativa (07, 13 y 19 h)','%','mean'),
}

def agregar(d, etiqueta):
    d=d.copy(); d['Fecha']=pd.to_datetime(d.Fecha,errors='coerce'); d=d.dropna(subset=['Fecha'])
    if d.empty: return pd.DataFrame(columns=['fecha','valor','dias_validos','dias_mes'])
    d['Valor']=pd.to_numeric(d.Valor,errors='coerce'); d['Valor']=d.Valor.where(np.isfinite(d.Valor))
    if etiqueta.startswith(('PTPM','EVTE')): d['Valor']=d.Valor.where(d.Valor.ge(0))
    elif etiqueta=='HRHG_CON': d['Valor']=d.Valor.where(d.Valor.between(0,100))
    else: d['Valor']=d.Valor.where(d.Valor.between(-40,60))
    # Conflicting or repeated timestamps are not silently averaged.
    d.loc[d.Fecha.duplicated(keep=False),'Valor']=np.nan
    d['dia']=d.Fecha.dt.normalize(); g=d.groupby('dia')
    if etiqueta=='HRHG_CON':
        d['hora']=d.Fecha.dt.hour
        d=d[d.hora.isin([7,13,19]) & d.Fecha.dt.minute.eq(0) & d.Fecha.dt.second.eq(0)]
        g=d.groupby('dia'); v=g.Valor.mean().where(g.Valor.count().eq(3)&g.hora.nunique().eq(3)&g.size().eq(3))
    else:
        v=g.Valor.first().where(g.size().eq(1))
    idx=pd.date_range(d.Fecha.min().normalize(),d.Fecha.max().normalize(),freq='D') if not d.empty else pd.DatetimeIndex([])
    v=v.reindex(idx); n=v.resample('MS').count(); agg=v.resample('MS').sum(min_count=1) if VARIABLES[etiqueta][2]=='sum' else v.resample('MS').mean()
    return pd.DataFrame({'fecha':n.index,'valor':agg.where(n.eq(n.index.days_in_month)).values,'dias_validos':n.values,'dias_mes':n.index.days_in_month})

def procesar(archivo,catalogo,base):
    from shapely.geometry import shape, Point
    base=Path(base); cat=pd.read_csv(catalogo,dtype=str).rename(columns={'Código':'Codigo'})
    cat['Codigo']=cat.Codigo.str.replace(r'\.0$','',regex=True)
    for x in ('Latitud','Longitud','Altitud'): cat[x]=pd.to_numeric(cat[x],errors='coerce')
    def geom(n):return shape(json.loads((base/n).read_text(encoding='utf-8'))['features'][0]['geometry'])
    area=geom('Chingaza_Buffer.geojson'); parque=geom('Chingaza.geojson')
    cat=cat.dropna(subset=['Latitud','Longitud']); cat=cat[cat.apply(lambda r:area.covers(Point(r.Longitud,r.Latitud)),axis=1)].copy()
    if cat.Codigo.duplicated().any(): raise ValueError('Códigos duplicados en el catálogo seleccionado')
    cat['zona']=cat.apply(lambda r:'PNN Chingaza' if parque.covers(Point(r.Longitud,r.Latitud)) else 'Zona de influencia',axis=1)
    cat=cat.rename(columns={'Codigo':'estacion','Nombre':'nombre','Latitud':'latitud','Longitud':'longitud','Altitud':'altitud_m','Municipio':'municipio','Departamento':'departamento','Estado':'estado_catalogo'})
    cat=cat[['estacion','nombre','latitud','longitud','altitud_m','municipio','departamento','estado_catalogo','zona']]
    chosen=set(cat.estacion); series=[]; inv=[]; keys=set()
    with zipfile.ZipFile(archivo) as z:
        for nested in z.namelist():
            if not nested.endswith('.zip'): continue
            with zipfile.ZipFile(io.BytesIO(z.read(nested))) as a:
                for f in sorted(a.namelist()):
                    if not f.endswith('.data'):continue
                    tag,code=Path(f).stem.split('@')
                    if code not in chosen:continue
                    if (code,tag) in keys:raise ValueError(f'Serie duplicada: {code}/{tag}')
                    keys.add((code,tag)); row={'estacion':code,'etiqueta':tag,'archivo_origen':Path(f).name}
                    if tag not in VARIABLES:
                        inv.append(dict(row,variable='Evaporación automática',unidad='',meses_validos=0,meses_calendario=0,estado='Pendiente verificar unidad y significado'));continue
                    var,unit,_=VARIABLES[tag]; m=agregar(pd.read_csv(io.BytesIO(a.read(f)),sep='|'),tag); m['estacion']=code;m['etiqueta']=tag;m['variable']=var;m['unidad']=unit
                    series.append(m); inv.append(dict(row,variable=var,unidad=unit,meses_validos=int(m.valor.count()),meses_calendario=len(m),estado='Agregado mensual preliminar'))
    out=pd.concat(series,ignore_index=True)[['estacion','etiqueta','variable','unidad','fecha','valor','dias_validos','dias_mes']].sort_values(['estacion','etiqueta','fecha']); inventory=pd.DataFrame(inv).sort_values(['estacion','etiqueta']); cat['series_en_entrega']=cat.estacion.isin(inventory.estacion)
    cat.sort_values('estacion').to_csv(base/'ideam_estaciones.csv',index=False);inventory.to_csv(base/'ideam_inventario.csv',index=False);out.to_csv(base/'ideam_mensual.csv',index=False,date_format='%Y-%m-%d',float_format='%.6f')
    print('Catálogo:',len(cat),'con archivos:',cat.series_en_entrega.sum(),'series:',len(inventory),'válidas:',out.valor.count());print(out.groupby('variable').valor.agg(['count','size']));print(out[out.valor.notna()].fecha.agg(['min','max']));print(cat.groupby(['zona','series_en_entrega']).size())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zip',required=True);p.add_argument('--catalogo-csv',required=True);p.add_argument('--base',default='data/processed/chingaza');a=p.parse_args();procesar(a.zip,a.catalogo_csv,a.base)
