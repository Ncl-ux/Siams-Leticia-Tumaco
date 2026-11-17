"""IDEAM Bogotá: importación trazable y agregación sin imputación."""
from pathlib import Path
import io
import re
import zipfile
import numpy as np
import pandas as pd
import openpyxl

BASE = Path(__file__).resolve().parents[1] / 'data/processed/ideam_bogota'
PARAM = {'Día pluviométrico (convencional)':'Precipitación', 'Temperatura seca media diaria':'Temperatura media', 'Temperatura máxima diaria':'Temperatura máxima', 'Temperatura mínima diaria':'Temperatura mínima', 'Humedad relativa del aire a 2 metros media diaria':'Humedad relativa'}
KEY = ['CodigoEstacion','Variable','Fecha']

def leer_zip(path):
    """Los XLSX multivariable se reconstruyen por orden de cabecera y reinicios de fecha."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(('.csv','.xlsx'))]
        if len(names)!=1: raise ValueError(f'Número inesperado de archivos: {path}')
        name=names[0]; payload=z.read(name)
    if name.lower().endswith('.csv'):
        d=pd.read_csv(io.BytesIO(payload),dtype={'CodigoEstacion':str})
        d['Identificacion']='Explícita CSV'
    else:
        w=openpyxl.load_workbook(io.BytesIO(payload),read_only=True,data_only=True)
        s=w.active;s.reset_dimensions(); rows=list(s.values);w.close()
        station=str(rows[1][1]); code=re.search(r'\[(\d+)\]',station).group(1)
        params=str(rows[6][1]).split(','); unit=rows[6][3]
        blocks=[[]]; previous=''
        for r in rows[8:]:
            date=str(r[0]);
            if not re.match(r'^\d{4}-\d\d-\d\d',date): continue
            if date<previous: blocks.append([])
            blocks[-1].append((date,r[2],r[4]));previous=date
        if len(blocks)!=len(params): raise ValueError(f'Bloques ambiguos: {path}')
        d=pd.DataFrame([(code,station,p,date,unit,value,flag,'Orden de bloques XLSX (inferido)' if len(params)>1 else 'Explícita XLSX') for p,b in zip(params,blocks) for date,value,flag in b],columns=['CodigoEstacion','NombreEstacion','Parametro','Fecha','Unidad','Valor','NivelAprobacion','Identificacion'])
    d['Variable']=d['Parametro'].map(PARAM)
    d['Archivo']=Path(path).name
    d['Fecha']=pd.to_datetime(d.Fecha,errors='coerce').dt.normalize()
    d['Valor']=pd.to_numeric(d.Valor.astype(str).str.replace(',','.',regex=False),errors='coerce')
    return d

def consolidar(paths):
    raw=pd.concat([leer_zip(p) for p in sorted(paths)],ignore_index=True)
    valid=raw.Variable.notna() & raw.Fecha.notna() & np.isfinite(raw.Valor)
    p=raw.Variable.eq('Precipitación'); h=raw.Variable.eq('Humedad relativa'); t=raw.Variable.str.startswith('Temperatura',na=False)
    valid &= (~p | (raw.Unidad.eq('mm') & raw.Valor.ge(0))) & (~h | (raw.Unidad.eq('%') & raw.Valor.between(0,100))) & (~t | (raw.Unidad.eq('degC') & raw.Valor.between(-30,50)))
    d=raw[valid].copy(); bad=raw[~valid].copy(); bad['Motivo']='Fecha, unidad, parámetro o rango inválido'
    # Prioridad: definitivo sobre preliminar; identificación explícita sobre inferida para empates.
    d['_rank']=d.NivelAprobacion.eq('Definitivo').astype(int)*2 + d.Identificacion.str.startswith('Explícita').astype(int)
    top=d[d._rank.eq(d.groupby(KEY)._rank.transform('max'))]
    conflict=top.groupby(KEY).Valor.transform('nunique').gt(1)
    conflicts=top[conflict].copy();conflicts['Motivo']='Conflicto de valores con igual prioridad; día excluido'
    clean=top[~conflict].drop_duplicates(KEY).drop(columns='_rank').sort_values(KEY)
    # No corregir incoherencia entre temperaturas; excluir los tres valores de ese día.
    ts=clean[clean.Variable.str.startswith('Temperatura')].pivot(index=['CodigoEstacion','Fecha'],columns='Variable',values='Valor')
    invalid=pd.Series(False,index=ts.index)
    for a,b in [('Temperatura mínima','Temperatura media'),('Temperatura media','Temperatura máxima'),('Temperatura mínima','Temperatura máxima')]:
        if a in ts and b in ts: invalid |= ts[a].gt(ts[b])
    mask=pd.MultiIndex.from_frame(clean[['CodigoEstacion','Fecha']]).isin(ts.index[invalid]) & clean.Variable.str.startswith('Temperatura')
    inco=clean[mask].copy();inco['Motivo']='Temperaturas incoherentes: Tmin <= Tmedia <= Tmax'
    clean=clean[~mask].copy()
    return clean, pd.concat([bad,conflicts,inco],ignore_index=True).drop(columns='_rank',errors='ignore')

def mensual(d):
    d=d.copy();d['MesFecha']=d.Fecha.dt.to_period('M').dt.to_timestamp()
    d['Def']=d.NivelAprobacion.eq('Definitivo');d['Inferida']=d.Identificacion.str.contains('inferido')
    m=d.groupby(['CodigoEstacion','NombreEstacion','Variable','MesFecha'],as_index=False).agg(Dias=('Valor','size'),Suma=('Valor','sum'),Media=('Valor','mean'),Definitivos=('Def','sum'),Inferidos=('Inferida','sum'))
    # Nombre puede variar entre exportaciones: mantener una etiqueta por código antes de llamar.
    m['DiasCalendario']=m.MesFecha.dt.days_in_month;m['Cobertura']=m.Dias/m.DiasCalendario
    m['ValorObservado']=np.where(m.Variable.eq('Precipitación'),m.Suma,m.Media)
    m['Valor']=m.ValorObservado.where(m.Cobertura.eq(1))
    m['Valor90']=m.ValorObservado.where(m.Cobertura.ge(.90))
    return m.drop(columns=['Suma','Media'])

def cargar_mensual():
    return pd.read_csv(BASE/'mensual.csv',dtype={'CodigoEstacion':str},parse_dates=['MesFecha'])

