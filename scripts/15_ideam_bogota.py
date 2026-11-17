"""Procesa los ZIP DHIME Bogotá y ejecuta los métodos existentes de A1."""
from pathlib import Path
import sys, argparse, json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from siams.ideam_bogota_datos import BASE, consolidar, mensual
from siams.estadistica import prueba_pettitt
from scripts.a1._siams_a1_base import snht_test, seasonal_z
from itertools import combinations

def dict_m(g,col):
    return dict(zip(g.MesFecha.dt.strftime('%Y-%m'),g[col]))

def prueba(d, tipo):
    d={k:float(v) for k,v in d.items() if pd.notna(v)}
    out=snht_test(d,tipo)
    if out['estado']=='calculado':
        dates,z=seasonal_z(sorted(d),[d[k] for k in sorted(d)])
        p=prueba_pettitt(z)
        out.update(pettitt_p=p['p'],pettitt_corte=dates[p['indice']],pettitt_K=p['K'])
    return {k:v for k,v in out.items() if k not in ('anomalias','perfil')}

def calcular(m):
    results=[]
    for variable, var in m.groupby('Variable'):
        groups={c:g for c,g in var.groupby('CodigoEstacion')}
        for col,criterion in [('Valor','100%'),('Valor90','≥90% (sensibilidad)')]:
            for code,g in groups.items():
                r=prueba(dict_m(g,col),'Absoluto')
                results.append({'variable':variable,'estacion':code,'referencia':'—','criterio':criterion,**r})
            for a,b in combinations(groups,2):
                x=groups[a].set_index('MesFecha')[col]; y=groups[b].set_index('MesFecha')[col]
                xy=pd.concat([x.rename('x'),y.rename('y')],axis=1,join='inner').dropna().sort_index()
                v=np.log1p(xy.x)-np.log1p(xy.y) if variable=='Precipitación' else xy.x-xy.y
                r=prueba(dict(zip(v.index.strftime('%Y-%m'),v)),'Relativo')
                an=xy-xy.groupby(xy.index.month).transform('mean')
                results.append({'variable':variable,'estacion':a,'referencia':b,'criterio':criterion,'meses_comunes':len(xy),'correlacion':xy.x.corr(xy.y) if len(xy)>2 else None,'correlacion_anomalias':an.x.corr(an.y) if len(xy)>2 else None,**r})
    return pd.DataFrame(results)

def main(paths):
    d,bad=consolidar(paths)
    labels=d.groupby('CodigoEstacion').NombreEstacion.first(); d['NombreEstacion']=d.CodigoEstacion.map(labels)
    m=mensual(d)
    BASE.mkdir(parents=True,exist_ok=True)
    d.to_csv(BASE/'diario.csv',index=False);bad.to_csv(BASE/'excluidos.csv',index=False);m.to_csv(BASE/'mensual.csv',index=False)
    q=d.groupby(['CodigoEstacion','Variable']).agg(Inicio=('Fecha','min'),Fin=('Fecha','max'),Dias=('Fecha','size'),Inferidos=('Identificacion',lambda s:s.str.contains('inferido').sum()),Definitivos=('NivelAprobacion',lambda s:s.eq('Definitivo').sum())).reset_index()
    q['CoberturaPct']=100*q.Dias/((q.Fin-q.Inicio).dt.days+1)
    a=m[m.Cobertura.eq(1)].assign(Anio=lambda x:x.MesFecha.dt.year).groupby(['CodigoEstacion','Variable','Anio']).size(); a=a[a.eq(12)].groupby(level=[0,1]).size().rename('AniosCompletos')
    q=q.merge(a.reset_index(),how='left').fillna({'AniosCompletos':0});q.to_csv(BASE/'inventario.csv',index=False)
    results=calcular(m);results.to_csv(BASE/'homogeneidad.csv',index=False)
    print(q.to_string(index=False));print(results[results.criterio.eq('100%')].to_string(index=False));print('Excluidos',len(bad))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zips',nargs='+',type=Path);args=p.parse_args();main(args.zips)
