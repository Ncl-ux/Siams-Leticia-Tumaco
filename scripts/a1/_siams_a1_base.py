"""SIAMS A1 | Auditoría reproducible SNHT y contraste entre fuentes.

Ejecución: python siams_a1_analisis.py excel.zip
Requiere numpy; usa exclusivamente Python estándar para leer XLSX.
Genera resultados_a1.json y 4 archivos CSV, sin modificar los originales.

Interpretación: SNHT absoluto y SNHT relativo a NASA son TAMIZAJES;
NO constituyen validación definitiva de homogeneidad instrumental.
"""
from __future__ import annotations
import argparse, calendar, csv, datetime as dt, io, json, math, os, re, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
EPOCH = dt.datetime(1899, 12, 30)

def excel_date(x):
    return (EPOCH + dt.timedelta(days=int(float(x)))).date()

def read_xlsx(payload, wanted):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        root=ET.fromstring(z.read('xl/workbook.xml'))
        refs={s.attrib['name']:s.attrib.get('{'+REL+'}id') for s in root.iter('{'+NS+'}sheet')}
        rels={r.attrib['Id']:r.attrib['Target'].lstrip('/') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            r=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.iter('{'+NS+'}t')) for si in r]
        out={}
        for sh in wanted:
            if sh not in refs: continue
            pp=rels[refs[sh]]
            if not pp.startswith('xl/'): pp='xl/'+pp
            root=ET.fromstring(z.read(pp))
            rows=[]
            for row in root.iter('{'+NS+'}row'):
                cols={}
                for c in row.iter('{'+NS+'}c'):
                    v=c.find('{'+NS+'}v'); ins=c.find('{'+NS+'}is')
                    val = v.text if v is not None else None
                    if c.attrib.get('t')=='inlineStr' and ins is not None:
                        val=''.join(t.text or '' for t in ins.iter('{'+NS+'}t'))
                    if val is None:continue
                    typ=c.attrib.get('t')
                    if typ=='s': val=shared[int(val)]
                    elif typ=='b':val=(val=='1')
                    elif typ not in ('str','e','inlineStr'):
                        try:val=float(val)
                        except (ValueError,TypeError): pass
                    label=re.match(r'[A-Z]+',c.attrib['r']).group(0)
                    i=0
                    for char in label:i=i*26+ord(char)-64
                    cols[i-1]=val
                if cols: rows.append([cols.get(i) for i in range(max(cols)+1)])
            out[sh]=rows
        return out

def build_monthly(rows):
    if not rows:return {}
    headers=rows[0];d={str(h):{} for h in headers[1:] if h is not None}
    for row in rows[1:]:
        if not row or not isinstance(row[0],(int,float)):continue
        date=excel_date(row[0]).isoformat()[:7]
        for j,h in enumerate(headers[1:],start=1):
            if h is None or j>=len(row):continue
            v=row[j]
            if isinstance(v,(int,float)) and np.isfinite(v):d[str(h)][date]=float(v)
    return d

def seasonal_z(dates,values):
    """Desestacionaliza y estandariza cada mes del año.

    Las observaciones se mantienen cronológicamente; mes con menos de 3
    observaciones o desviación estándar cero queda fuera.
    """
    month=np.array([int(d[5:7]) for d in dates],dtype=int)
    val=np.asarray(values,dtype=float); z=np.full(len(val),np.nan)
    for m in range(1,13):
        ix=np.where((month==m)&np.isfinite(val))[0]
        if len(ix)<3:continue
        sd=np.std(val[ix],ddof=1)
        if sd>0:z[ix]=(val[ix]-np.mean(val[ix]))/sd
    valid=np.isfinite(z)
    return [dates[i] for i in np.where(valid)[0]],z[valid]

def snht_curve(v, minblock=24):
    v=np.asarray(v,dtype=float)
    n=len(v)
    if n<2*minblock:return None
    sd=v.std(ddof=1)
    if sd < 1e-12:return None
    z=(v-v.mean())/sd
    k=np.arange(1,n)
    s=np.cumsum(z)[:-1]
    T=(s*s/k)+(s*s/(n-k))  # suma total estandarizada ~ cero
    window=max(minblock,int(math.ceil(.10*n)))
    valid=(k>=window)&(n-k>=window)
    T[~valid]=np.nan
    if not np.isfinite(T).any():return None
    ix=int(np.nanargmax(T));best=ix+1
    return float(T[ix]),best,[(int(i),float(a)) for i,a in zip(k,T) if np.isfinite(a)]

def block_permutation_p(dates, z, observed, repeat=999, seed=1637):
    """Permuta bloques-año; meses contiguos y valores faltantes juntos.
    Nulidad: años intercambiables. No valida independencia interanual.
    """
    by_year=defaultdict(list)
    for i,d in enumerate(dates):by_year[d[:4]].append(float(z[i]))
    arr=[np.asarray(a,dtype=float) for a in by_year.values()]
    if len(arr)<5:return None
    rng=np.random.default_rng(seed)
    ge=0
    for _ in range(repeat):
        order=rng.permutation(len(arr))
        sim=np.concatenate([arr[i] for i in order]);stats=snht_curve(sim)
        if stats and stats[0] >= observed-1e-10:ge+=1
    return (ge+1)/(repeat+1)

def snht_test(mdict,kind='absoluto',repeat=999):
    dates=sorted(mdict)
    if len(dates)<48: return {'estado':'insuficiente','n':len(dates)}
    sdates,z=seasonal_z(dates,[mdict[d] for d in dates])
    if len(z)<48 or len(set(d[:4] for d in sdates))<5:
        return {'estado':'insuficiente','n':len(z)}
    calc=snht_curve(z)
    if calc is None:return {'estado':'insuficiente','n':len(z)}
    T,k,curve=calc
    p=block_permutation_p(sdates,z,T,repeat=repeat)
    return {'estado':'calculado','tipo':kind,'n':len(z),'desde':sdates[0],
            'hasta':sdates[-1], 'T_SNHT':round(T,5),'corte':sdates[k-1],
            'p_bloques':round(p,5) if p is not None else None,
            'alerta':(p is not None and p<.05),
            'anomalias':[[d,round(float(x),5)] for d,x in zip(sdates,z)],
            'perfil':[[sdates[i-1],round(a,5)] for i,a in curve]}

def compare_monthly(obs,reference,metric):
    common=sorted(set(obs)&set(reference))
    if len(common)<48:return {'estado':'insuficiente','n':len(common)}
    x=np.asarray([obs[d] for d in common]);y=np.asarray([reference[d] for d in common])
    valid=np.isfinite(x)&np.isfinite(y)
    if metric=='P':
        valid &= (x>=0)&(y>=0)
        # Transformación relativa con seudocuenta de 1 mm para evitar log(0)
        contrasts=np.log((x[valid]+1)/(y[valid]+1))
    else:contrasts=x[valid]-y[valid]
    dates=[d for d,b in zip(common,valid) if b]
    test=snht_test(dict(zip(dates,contrasts)),'relativo NASA (exploratorio)')
    test.update({'n_coincidentes':len(dates), 'correlacion':round(float(np.corrcoef(x[valid],y[valid])[0,1]),4),
                 'sesgo_obs_menos_ref':round(float((x[valid]-y[valid]).mean()),4),
                 'transformacion':'log[(P IDEAM+1)/(P NASA+1)]' if metric=='P' else 'IDEAM - NASA',
                 'contrastes':[[d,round(float(a),5)] for d,a in zip(dates,contrasts)]})
    return test

def main(archive_path,output_dir,repeat=999):
    os.makedirs(output_dir,exist_ok=True)
    extracted={}
    needed=['P_mensual','T_mensual','HR_mensual','Viento_mensual','Presion_mensual',
            'Radiacion_mensual','Pettitt_MK','P_estaciones_regimen','Fuentes','P_diaria']
    with zipfile.ZipFile(archive_path) as z:
        files=[f for f in z.namelist() if f.lower().endswith('.xlsx')]
        for path in files:
            name=os.path.basename(path)
            extracted[name]=read_xlsx(z.read(path),needed)
    results=[];monthly_all={}
    for fn,sheets in sorted(extracted.items()):
        mdata={}
        for sh in needed[:6]:
            for var,md in build_monthly(sheets.get(sh,[])).items():
                mdata[(sh,var)]=md
        monthly_all[fn]=mdata
        original=sheets.get('Pettitt_MK',[])
        pettitt={}
        if original:
            headings=original[0]
            for row in original[1:]:
                data=dict(zip(headings,row))
                key=(data.get('hoja'),data.get('columna_original'))
                if key not in pettitt:pettitt[key]=data
        if not mdata:
            results.append({'archivo':fn,'hoja':'-','variable':'Series mensuales ausentes',
                           'estado':'sin_serie_temporal','n':0,'nota':'No hay series por mes-año; solo climatologías'})
        for (sh,var),md in mdata.items():
            if len(md)<10:continue
            result=snht_test(md,repeat=repeat)
            previous=pettitt.get((sh,var),{})
            out={'archivo':fn,'hoja':sh,'variable':var,
                 'fuente':'IDEAM' if fn.lower().startswith('ideam') else 'NASA POWER',
                 'pettitt_p_original':previous.get('p_pettitt'),
                 'pettitt_fecha_original':excel_date(previous['fecha_cambio']).isoformat()[:7] if isinstance(previous.get('fecha_cambio'),(float,int)) else None,
                 **result}
            results.append(out)
    # Corrección de Benjamini-Hochberg para el barrido exploratorio de series.
    def bh(rows):
        candidates=[(i,r['p_bloques']) for i,r in enumerate(rows) if r.get('p_bloques') is not None]
        candidates.sort(key=lambda x:x[1]);m=len(candidates);best=1.0
        for rank in range(m,0,-1):
            i,p=candidates[rank-1];best=min(best,p*m/rank)
            rows[i]['q_BH']=round(best,5)
            rows[i]['alerta_BH']=best<0.05
    bh(results)
    # Comparación observación y simulación solo para el mismo par territorio-variable.
    ideam=monthly_all.get('Ideam_Tumaco.xlsx',{})
    nasa=monthly_all.get('Nasa_Power_Tumaco.xlsx',{})
    pairs=[('P_mensual','precipitacion','precipitacion_mm_dia','P','Precipitación (mm/mes)'),
           ('T_mensual','temperatura_media','temperatura_media_C','T','Temperatura media (°C)'),
           ('T_mensual','temperatura_maxima','temperatura_maxima_C','T','Temperatura máxima (°C)'),
           ('T_mensual','temperatura_minima','temperatura_minima_C','T','Temperatura mínima (°C)'),
           ('HR_mensual','humedad_relativa','humedad_relativa_pct','HR','Humedad relativa (%)')]
    relative=[]
    for sh,vo,vn,metric,label in pairs:
        rr=compare_monthly(ideam.get((sh,vo),{}),nasa.get((sh,vn),{}),metric)
        relative.append({'variable':label,'clave':vo,'referencia':'NASA POWER Tumaco',**rr})
    bh(relative)
    # Auditoría de cobertura diaria de precipitación IDEAM Tumaco.
    daily=extracted.get('Ideam_Tumaco.xlsx',{}).get('P_diaria',[])
    counts=defaultdict(int)
    for row in daily[1:]:
        if len(row)>1 and isinstance(row[0],(int,float)) and isinstance(row[1],(int,float)):
            d=excel_date(row[0]);counts[f'{d.year:04d}-{d.month:02d}']+=1
    pmonths=ideam.get(('P_mensual','precipitacion'),{})
    quality=[]
    for d in sorted(pmonths):
        y,m=map(int,d.split('-'));expected=calendar.monthrange(y,m)[1]
        n=counts.get(d,0);fraction=n/expected
        quality.append({'mes':d,'dias_observados':n,'dias_calendario':expected,
                        'cobertura':round(fraction,5), 'precipitacion_mm':pmonths[d],
                        'aceptado_90pct':fraction>=.90})
    good={d:v for d,v in pmonths.items() if counts.get(d,0)/calendar.monthrange(*map(int,d.split('-')))[1] >= .90}
    sensitivity=snht_test(good,kind='SNHT absoluto P, cobertura >=90%',repeat=repeat)
    sensitivity={k:v for k,v in sensitivity.items() if k not in ('anomalias','perfil')}
    # En Arauca hay normales mensuales, pero no registros por mes-año ni coincidencia temporal verificable.
    ara=extracted.get('Ideam_Arauca.xlsx',{}).get('P_estaciones_regimen',[])
    stations=[]; station_profile=[]
    if len(ara)>=13:
        labels=ara[0][1:4]; station_profile=[[int(r[0])]+list(map(float,r[1:4])) for r in ara[1:13]]
        x=np.asarray([row[1:] for row in station_profile]); primary=x[:,0]
        for j,nam in enumerate(labels):
            v=x[:,j]
            stations.append({'estacion':nam,'n_meses_climatologia':12,
                             'media_12_meses':round(float(v.mean()),3),
                             'total_12_medias':round(float(v.sum()),3),
                             'correlacion_patron_anual':round(float(np.corrcoef(primary,v)[0,1]),4),
                             'cociente_total_vs_matezamuro':round(float(v.sum()/primary.sum()),4),
                             'comentario':'Comparación de climatologías: NO verifica coincidencia de cambios en un año' })
    brief=[]
    for r in results:
        brief.append({k:v for k,v in r.items() if k not in ('anomalias','perfil')})
    briefrel=[{k:v for k,v in r.items() if k not in ('anomalias','perfil','contrastes')} for r in relative]
    output={'metadata':{'metodo':'SNHT absoluto sobre anomalías mensuales estacionales, p por permutación de bloques anuales',
                        'repeticiones':repeat,'alfa':0.05,'min_seg_meses':24,'min_segmento_proporcion':0.10,
                        'nota':'Prueba exploratoria: no demuestra origen instrumental del cambio ni reemplaza SNHT relativo IDEAM-IDEAM.'},
            'resumen':brief,'comparacion_tumaco':briefrel,'comparacion_arauca':stations,
            'climatologia_arauca':station_profile,'calidad_tumaco':quality,'snht_p_90pct':sensitivity,'perfiles':results,'relativos':relative}
    with open(os.path.join(output_dir,'resultados_a1.json'),'w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False,indent=2,allow_nan=False)
    def writecsv(file,rows):
        cols=list(dict.fromkeys(k for a in rows for k in a))
        with open(os.path.join(output_dir,file),'w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    writecsv('snht_absoluto.csv',brief)
    writecsv('contraste_tumaco.csv',briefrel)
    writecsv('contraste_arauca.csv',stations)
    writecsv('calidad_P_Tumaco.csv',quality)
    print('Analizadas:',len(results),'variables | SNHT calculados:',sum(r.get('estado')=='calculado' for r in results))
    print('Tumaco relativo:',[(r['clave'],r['estado'],r.get('corte'),r.get('p_bloques')) for r in relative])
    for r in results:
        if r['archivo']=='Ideam_Tumaco.xlsx':
            print('IDEAM Tumaco',r['variable'],r.get('T_SNHT'),r.get('corte'),r.get('p_bloques'))
    print('Ruta de resultados:',output_dir)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip',help='ZIP con archivos XLSX de NASA POWER e IDEAM')
    p.add_argument('--out',default='siams_a1_resultados');p.add_argument('--repeticiones',type=int,default=999)
    args=p.parse_args();main(args.zip,args.out,args.repeticiones)
