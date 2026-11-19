"""Ejecutar localmente, dando la ruta externa del Excel EAAB. Solo exporta meses."""
import argparse, datetime, re, sys
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from siams.chingaza_datos import BASE, agregar_diario

def procesar(libro, salida=BASE):
    w=load_workbook(libro,read_only=True,data_only=True); series=[]; inventario=[]
    try:
        for s in w:
            rows=s.iter_rows(max_col=4,values_only=True); cab=[]; datos=[]
            for r in rows:
                a,b,f,_=r
                if isinstance(a,(datetime.datetime,datetime.date)):
                    datos.append((a,b,f))
                elif not datos: cab.append(r)
            param=str(cab[1][1]); m=re.match(r'(120|102)\s*-',param)
            if not m: raise ValueError(f'Parámetro desconocido: {s.title}')
            tipo,unidad,modo=('Precipitación','mm/mes','sum') if m[1]=='120' else ('Caudal','m³/s','mean')
            elem=next(str(r[1]) for r in cab if str(r[1]).startswith('ELEMENTO:'))
            codigo=re.match(r'ELEMENTO:\s*(\d+)',elem)[1]
            nombre=re.sub(r'^ELEMENTO:\s*\d+\s*(\([^)]*\))?\s*','',elem).strip()
            d=pd.DataFrame(datos,columns=['fecha','valor','flag']); mes=agregar_diario(d,modo)
            mes.insert(0,'variable',tipo); mes.insert(0,'estacion',codigo); mes['unidad']=unidad; series.append(mes)
            ok=mes.loc[mes.valor.notna(),'fecha']; inventario.append(dict(estacion=codigo,nombre=nombre,variable=tipo,unidad=unidad,meses_validos=len(ok),meses_calendario=len(mes),inicio=mes.fecha.min().strftime('%Y-%m'),fin=mes.fecha.max().strftime('%Y-%m'),fuente='EAAB E.S.P. · SIH · reporte 2024-02-02'))
    finally: w.close()
    out=pd.concat(series,ignore_index=True); inv=pd.DataFrame(inventario)
    if out.duplicated(['estacion','variable','fecha']).any(): raise ValueError('Estaciones duplicadas')
    salida=Path(salida); salida.mkdir(parents=True,exist_ok=True)
    out.to_csv(salida/'eaab_mensual.csv',index=False,date_format='%Y-%m-%d',float_format='%.6f'); inv.to_csv(salida/'eaab_estaciones.csv',index=False)
    print(f'{len(inv)} estaciones; {out.valor.notna().sum()} meses completos de {len(out)} meses calendario.')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('excel',type=Path); a=p.parse_args(); procesar(a.excel)
