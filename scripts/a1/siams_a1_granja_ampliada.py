"""SIAMS A1 | Análisis reproducible COCO EL vs GRANJA EL MIRA.

Insumos colocados en la misma carpeta:
- excel.zip (incluye excel/Ideam_Tumaco.xlsx)
- Reporte de información Hidrometeorológica de DHIME generado tumaco 1.zip
- Reporte de información Hidrometeorológica de DHIME generado tumaco 2.zip
- Reporte de información Hidrometeorológica de DHIME generado tumaco 3.zip
- _siams_a1_base.py (métodos SNHT, lectura XLSX estándar)

Ejecución: python siams_a1_granja_ampliada.py --base "C:/carpeta"
Requiere numpy y scipy; originales no son modificados.
"""
import argparse,zipfile,io,csv,math,calendar,json
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy import stats
from _siams_a1_base import read_xlsx,excel_date,snht_test

ZIP_FILES=('Reporte de información Hidrometeorológica de DHIME generado tumaco 2.zip',
           'Reporte de información Hidrometeorológica de DHIME generado tumaco 3.zip',
           'Reporte de información Hidrometeorológica de DHIME generado tumaco 1.zip')
MAIN_CODE='51030020'; REF_CODE='51025090'

def read_primary(path):
    with zipfile.ZipFile(path) as z:
        wb=z.read('excel/Ideam_Tumaco.xlsx')
        rows=read_xlsx(wb,['P_diaria'])['P_diaria']
    daily={}
    for row in rows[1:]:
        if len(row)<2 or not isinstance(row[0],(float,int)) or not isinstance(row[1],(float,int)):continue
        d=excel_date(row[0]);v=float(row[1])
        if np.isfinite(v) and v>=0:daily[d]=(v,'IDEAM COCO EL: aprobación no informada')
    return daily

def parse_zip(path):
    with zipfile.ZipFile(path) as z:
        data=z.read('descargaDhime.csv')
    rr=csv.DictReader(io.StringIO(data.decode('utf-8-sig')));d={};codes=set();bad=0
    for row in rr:
        codes.add(row['CodigoEstacion']);date=row['Fecha'][:10]
        try:
            from datetime import date as dtdate
            dte=dtdate.fromisoformat(date);v=float(row['Valor']);assert np.isfinite(v) and v>=0
            d[dte]=(v,row['NivelAprobacion'])
        except (ValueError,AssertionError):bad+=1
    if codes!={REF_CODE}:raise ValueError(f'Código no esperado en {path}: {codes}')
    return d,bad

def monthly_daily(d):
    daily=defaultdict(list)
    for date,(v,flag) in d.items():daily[f'{date.year:04d}-{date.month:02d}'].append((v,flag))
    mm={}
    for key,obs in daily.items():
        y,m=map(int,key.split('-')); n=calendar.monthrange(y,m)[1]
        mm[key]={'precip':float(sum(v for v,_ in obs)),'dias':len(obs),'calendario':n,
                 'cobertura':len(obs)/n,'aprobaciones':dict(Counter(s for _,s in obs))}
    return mm

def corrs(rows):
    if len(rows)<3:return {}
    x=np.array([r['coco_mm'] for r in rows]);y=np.array([r['granja_mm'] for r in rows]);
    month=np.array([int(r['mes'][5:7]) for r in rows]);xa=x.copy();ya=y.copy()
    for mo in range(1,13):
        im=month==mo
        xa[im]-=xa[im].mean();ya[im]-=ya[im].mean()
    return {'pearson':round(float(stats.pearsonr(x,y).statistic),5),
            'pearson_anomalias':round(float(np.corrcoef(xa,ya)[0,1]),5),
            'spearman':round(float(stats.spearmanr(x,y).statistic),5),
            'ratio_total_precipitacion':round(float(x.sum()/y.sum()),5)}

def statistical_period(rows,ini,end):
    return [r for r in rows if ini<=r['mes']<=end]

def snht_relative(rows,ini,end,perms=999):
    filt=statistical_period(rows,ini,end)
    dic={r['mes']:math.log1p(r['coco_mm'])-math.log1p(r['granja_mm']) for r in filt}
    out=snht_test(dic,'Relativo log[(P_COCO+1)/(P_GRANJA+1)]',repeat=perms)
    return {k:v for k,v in out.items() if k not in ('anomalias','perfil')}

def annual_comparison(rows,early=(1985,1996),late=(1998,2005),nperm=30000):
    by=defaultdict(list)
    for r in rows:by[int(r['mes'][:4])].append(r)
    def take(period):
        years=[y for y in sorted(by) if period[0]<=y<=period[1] and len(by[y])>=9]
        return years,np.array([np.mean([x['ln_relativo'] for x in by[y]]) for y in years])
    ey,ev=take(early);ly,lv=take(late)
    if not len(ev) or not len(lv):return None
    obs=float(lv.mean()-ev.mean());v=np.r_[ev,lv];rng=np.random.default_rng(321);hits=0
    for _ in range(nperm):
        sample=rng.permutation(v);hits+=abs(sample[len(ev):].mean()-sample[:len(ev)].mean())>=abs(obs)
    bs=np.array([rng.choice(lv,len(lv),True).mean()-rng.choice(ev,len(ev),True).mean() for _ in range(nperm)])
    ci=np.quantile(bs,[.025,.975]);return {'antes_anios':ey,'despues_anios':ly,'n_antes':len(ey),'n_despues':len(ly),
        'log_promedio_antes':round(float(ev.mean()),6),'log_promedio_despues':round(float(lv.mean()),6),
        'delta_log':round(obs,6),'factor_relativo':round(float(math.exp(obs)),5),
        'p_permutacion_anual_bilateral':round((hits+1)/(nperm+1),6),
        'IC95_delta_log_bootstrap_anual':[round(float(ci[0]),6),round(float(ci[1]),6)],
        'periodos':f'{early[0]}-{early[1]} versus {late[0]}-{late[1]} (1997 excluido)',
        'nota':'Estimación descriptiva; no atribuye ruptura a una estación por sí sola'}

def main(base, out):
    coco=read_primary(base/'excel.zip');sources=[];gran={};conflicts=[];overlaps=0;rejected=0
    for filename in ZIP_FILES:
        d,bad=parse_zip(base/filename);rejected+=bad
        sources.append({'archivo':filename,'n_filas_aceptadas':len(d),'min_fecha':str(min(d)),'max_fecha':str(max(d)),
                        'nivel_aprobacion':dict(Counter(status for _,status in d.values()))})
        for day,v in d.items():
            if day in gran:
                overlaps+=1
                if gran[day][0]!=v[0]:conflicts.append({'fecha':str(day),'previo':gran[day][0],'nuevo':v[0],'archivo':filename})
            gran[day]=v
    if conflicts:raise ValueError(f'Duplicados discordantes: {len(conflicts)}')
    mm0=monthly_daily(coco);mm1=monthly_daily(gran)
    common=sorted(set(mm0)&set(mm1));valid=[m for m in common if mm0[m]['cobertura']>=0.9 and mm1[m]['cobertura']>=0.9]
    daily=[]
    for month in valid:
        a,b=mm0[month],mm1[month]
        daily.append({'mes':month,'coco_mm':round(a['precip'],3),'granja_mm':round(b['precip'],3),
                      'dias_coco':a['dias'],'dias_granja':b['dias'],
                      'cobertura_coco_pct':round(a['cobertura']*100,2),'cobertura_granja_pct':round(b['cobertura']*100,2),
                      'diferencia_mm':round(a['precip']-b['precip'],3),
                      'ln_relativo':round(math.log1p(a['precip'])-math.log1p(b['precip']),7),
                      'posicion_corte_1997':'Antes' if month<'1997-06' else 'Despues'})
    yearly=[]
    for year in sorted({int(k[:4]) for k in mm1}):
        arr=[m for m in mm1 if int(m[:4])==year];v=[m for m in arr if mm1[m]['cobertura']>=.9]
        yearly.append({'anio':year,'dias_granja':sum(mm1[m]['dias'] for m in arr),
                       'meses_granja':len(arr),'meses_granja_90pct':len(v),'suma_mm_reportada':round(sum(mm1[m]['precip'] for m in arr),2),
                       'meses_coco_granja_comparables':sum(k.startswith(str(year)) for k in valid)})
    abs0={m:v['precip'] for m,v in mm0.items() if v['cobertura']>=.9}
    abs1={m:v['precip'] for m,v in mm1.items() if v['cobertura']>=.9 and '1985-01'<=m<='2025-07'}
    abs1local={m:v for m,v in abs1.items() if '1990-01'<=m<='2003-12'}
    out_json={'metadata':{'descripcion':'SIAMS A1: contraste IDEAM-IDEAM, COCO EL contra GRANJA EL MIRA, ampliado',
              'fecha_reporte':'2026-10-18','coco':'COCO EL [51030020]','granja':'GRANJA EL MIRA AUT [51025090]',
              'cobertura_mensual_minima':0.90,'unidad':'mm/mes','corte_indicativo':'1997-06',
              'fuente':'CSV diarios DHIME proporcionados; Excel IDEAM Tumaco del ZIP original',
              'metodo':'SNHT sobre anomalías estacionales mensuales del logaritmo de razón con pseudocuenta +1 mm; permutación de bloques-año'},
          'archivos_granja':sources,'control':{'dias_coco':len(coco),'dias_granja_unicos':len(gran),
          'filas_duplicadas_coincidentes':overlaps,'filas_duplicadas_discordantes':len(conflicts),
          'descartados_no_validos':rejected,'meses_coincidentes':len(common),'meses_validos':len(valid),
          'meses_rechazados':len(common)-len(valid),'meses_antes_1997':sum(k<'1997-06' for k in valid),
          'meses_desde_1997':sum(k>='1997-06' for k in valid)},'correlaciones':corrs(daily),
          'snht_relativo':{x:snht_relative(daily,*time) for x,time in {
                 'periodo_completo':('1985-01','2025-07'),'ventana_1985_2005':('1985-01','2005-12'),
                 'ventana_1990_2005':('1990-01','2005-12'),
                 'ventana_1992_2025':('1992-01','2025-07')}.items()},
          'snht_absoluto':{'COCO_EL_1985_2025':{k:v for k,v in snht_test(abs0,'COCO EL absoluto',999).items() if k not in ('perfil','anomalias')},
               'GRANJA_1985_2025':{k:v for k,v in snht_test(abs1,'GRANJA absoluto',999).items() if k not in ('perfil','anomalias')},
               'GRANJA_1990_2003':{k:v for k,v in snht_test(abs1local,'GRANJA absoluto ventana 1990-2003',999).items() if k not in ('perfil','anomalias')}},
          'comparacion_anual':{
              '1985_1996_vs_1998_2005':annual_comparison(daily,(1985,1996),(1998,2005)),
              '1990_1996_vs_1998_2005':annual_comparison(daily,(1990,1996),(1998,2005))},
          'comparables':daily,'cobertura_anual_granja':yearly,
          'conclusion':'La referencia sí cubre antes y después de 1997. Hay desplazamiento significativo del contraste relativo global, pero el máximo de SNHT relativo es de 1994-03. El método no identifica por sí solo la causa del cambio; series con aprobaciones preliminares/en revisión y sin metadatos de instrumentos. NO certificar homogeneidad definitiva ni corregir COCO EL automáticamente.'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'SIAMS_A1_Granja_Analisis_Ampliado.json').write_text(json.dumps(out_json,ensure_ascii=False,indent=2),encoding='utf-8')
    def writecsv(path,rows):
        with open(out/path,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    writecsv('SIAMS_A1_COCO_Granja_mensual.csv',daily)
    writecsv('SIAMS_A1_Cobertura_Granja_anual.csv',yearly)
    print(json.dumps({k:v for k,v in out_json.items() if k not in ['comparables','cobertura_anual_granja']},ensure_ascii=False,indent=2))
    return out_json
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path,default=None)
    arg=p.parse_args();main(arg.base,arg.out or arg.base)
