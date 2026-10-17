"""Regenera tablas exploratorias SWOT a partir de CSV plot_ID de HydroWeb.

Nunca atribuye banderas oficiales RiverSP a una exportación sin esos campos.
Las uniones por fecha admiten diferencias de segundos en el sello temporal.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'swot'
PROCESADOS = ROOT / 'data' / 'processed' / 'swot'
TOLERANCIA = pd.Timedelta(seconds=3)
COLUMNAS = {
    'wse': ('wse_m', 'wse_incertidumbre_m'),
    'ancho': ('ancho_m', 'ancho_incertidumbre_m'),
    'area': ('area_m2', 'area_incertidumbre_m2'),
    'pendiente': ('pendiente_m_m', 'pendiente_incertidumbre_m_m'),
}


def leer_plot(ruta: Path) -> tuple[str, str, pd.DataFrame]:
    cabecera = pd.read_csv(ruta, nrows=0, encoding='utf-8-sig').columns.tolist()
    if len(cabecera) < 3 or 'Date - UTC' not in cabecera[0]:
        raise ValueError(f'Encabezado HydroWeb no reconocido: {ruta}')
    titulo = cabecera[1].lower()
    if 'water surface elevation' in titulo:
        variable = 'wse'
    elif 'river reach width' in titulo:
        variable = 'ancho'
    elif 'total estimated water surface area' in titulo:
        variable = 'area'
    elif 'water surface slope' in titulo:
        variable = 'pendiente'
    else:
        raise ValueError(f'Variable no reconocida: {cabecera[1]} ({ruta.name})')
    match = re.search(r'plot_(\d+)',ruta.name,flags=re.I)
    if match is None: raise ValueError(f'Falta reach_id en nombre: {ruta}')
    reach = match.group(1)
    reach_en_cabecera=re.search(r'\b(\d{8,})\b',cabecera[1])
    if reach_en_cabecera and reach_en_cabecera.group(1)!=reach:
        raise ValueError(f'Reach en nombre y columna no coinciden: {ruta.name}')
    df=pd.read_csv(ruta,encoding='utf-8-sig',usecols=[0,1,2])
    df.columns=['fecha_utc',*COLUMNAS[variable]]
    df['fecha_utc']=pd.to_datetime(df['fecha_utc'],utc=True,errors='coerce')
    if df.fecha_utc.isna().any():raise ValueError(f'Fechas incorrectas: {ruta}')
    for columna in COLUMNAS[variable]:df[columna]=pd.to_numeric(df[columna],errors='coerce')
    if df.fecha_utc.duplicated().any():
        raise ValueError(f'Fechas duplicadas en variable {variable}: {ruta}')
    return reach,variable,df.sort_values('fecha_utc').reset_index(drop=True)


def unir_reach(reach: str, tablas: dict[str,pd.DataFrame], sede: str) -> pd.DataFrame:
    # Un sello de tiempo puede diferir ±1 s por variable; nunca unir por número de fila.
    fechas=pd.concat([t[['fecha_utc']] for t in tablas.values()],ignore_index=True)
    fechas=fechas.sort_values('fecha_utc').reset_index(drop=True)
    agrupaciones=[]
    for ts in fechas.fecha_utc:
        if not agrupaciones or ts-agrupaciones[-1][-1]>TOLERANCIA:
            agrupaciones.append([ts])
        else:
            agrupaciones[-1].append(ts)
    wse_fechas=set(tablas['wse'].fecha_utc) if 'wse' in tablas else set()
    anclas=[next((ts for ts in grp if ts in wse_fechas),grp[0]) for grp in agrupaciones]
    base=pd.DataFrame({'fecha_utc':pd.to_datetime(anclas,utc=True)}).sort_values('fecha_utc')
    for var in ['wse','ancho','area','pendiente']:
        if var not in tablas:
            for campo in COLUMNAS[var]:base[campo]=np.nan
            continue
        tabla=tablas[var]
        base=pd.merge_asof(base.sort_values('fecha_utc'),tabla.sort_values('fecha_utc'),
                           on='fecha_utc',direction='nearest',tolerance=TOLERANCIA)
    base.insert(0,'tramo','')
    base.insert(0,'reach_id',reach)
    base['dias_desde_anterior']=base.fecha_utc.diff().dt.total_seconds()/86400
    # Se calcula respecto de la última observación WSE disponible; una fecha
    # con otra variable pero WSE ausente no rompe la diferencia entre WSE válidas.
    base['cambio_wse_m']=base.wse_m.ffill().diff().where(base.wse_m.notna())
    # Si falta WSE, esa fecha no recibe cambio ni alerta.
    base['salto_absoluto_wse_m']=base.cambio_wse_m.abs()
    diferencias=base.salto_absoluto_wse_m.dropna()
    if len(diferencias)>3:
        med=float(diferencias.median())
        mad=float((diferencias-med).abs().median())
        umbral=med+6*1.4826*mad
    else:
        umbral=float('nan')
    base['umbral_robusto_salto_wse_m']=umbral
    marcas=base.salto_absoluto_wse_m.gt(umbral) if np.isfinite(umbral) else pd.Series(False,index=base.index)
    base['revisar_salto_wse']=np.where(marcas,'SI','NO')
    base['bandera_calidad_oficial']='NO_PRESENTE_EN_CSV'
    base['interpretacion_control']=np.where(marcas,'REVISAR_SALTO_EXPLORATORIO','SIN_ALERTA_EXPLORATORIA')
    base['tramos_con_alerta_misma_fecha']=0
    base['fecha_utc']=base.fecha_utc.dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return base


def regenerar(entrada: Path=RAW, salida:Path=PROCESADOS) -> pd.DataFrame:
    agrupados={}
    for p in sorted(entrada.rglob('plot_*.csv')):
        sede=p.parent.name
        reach,variable,datos=leer_plot(p)
        k=(sede,reach)
        if variable in agrupados.setdefault(k,{}):
            raise ValueError(f'Duplicación {sede}/{reach}/{variable}: {p}')
        agrupados[k][variable]=(datos,p)
    if not agrupados: raise FileNotFoundError(f'No hay archivos plot en {entrada}')
    tablas=[]
    for (sede,reach),sub in sorted(agrupados.items()):
        faltantes=set(COLUMNAS)-set(sub)
        if faltantes: raise ValueError(f'Faltan plot para {sede}/{reach}: {faltantes}')
        tabla=unir_reach(reach,{k:v[0] for k,v in sub.items()},sede)
        tablas.append((sede,reach,tabla,sub))
    # Fechas coincidentes entre reaches: no asumir sincronicidad si no son exactamente iguales.
    for sede in {s for s,_,_,_ in tablas}:
        seleccion=[t for t in tablas if t[0]==sede]
        cuenta={}
        for _,_,t,_ in seleccion:
            for f in t.loc[t.revisar_salto_wse=='SI','fecha_utc']:
                cuenta[f]=cuenta.get(f,0)+1
        for _,_,t,_ in seleccion:
            t['tramos_con_alerta_misma_fecha']=t.fecha_utc.map(cuenta).fillna(0).astype(int)
    salida.mkdir(parents=True,exist_ok=True)
    informe=[]
    for sede,reach,t,sub in tablas:
        ruta=salida/f'SWOT_{sede}_reach_{reach}.csv'
        t.to_csv(ruta,index=False,encoding='utf-8-sig',float_format='%.9g')
        wse=t.wse_m.dropna(); max_dif=t.salto_absoluto_wse_m.max()
        identificacion=f'Grupo {reach[:9]} (río por confirmar)' if sede=='Tumaco' else sede
        informe.append({
            'sede':sede,'reach_id':reach,'fechas_unicas':len(t),
            'wse_disponibles':int(wse.count()),
            'fechas_con_variables_incompletas':int(t[[a for cols in COLUMNAS.values() for a in cols[::2]]].isna().any(axis=1).sum()),
            'saltos_para_revisar':int((t.revisar_salto_wse=='SI').sum()),
            'salto_maximo_wse_m':round(float(max_dif),6) if pd.notna(max_dif) else None,
            'umbral_robusto_m':round(float(t.umbral_robusto_salto_wse_m.iloc[0]),6) if len(t) else None,
            'banderas_oficiales':'NO_PRESENTES',
            'grupo_reaches_por_prefijo':identificacion,
            'origen_archivos':' | '.join(p.relative_to(entrada).as_posix() for _,p in sub.values()),
        })
    resumen=pd.DataFrame(informe)
    resumen.to_csv(salida/'Resumen_Control_SWOT_M7.csv',index=False,encoding='utf-8-sig')
    return resumen


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,default=RAW)
    parser.add_argument('--out',type=Path,default=PROCESADOS)
    args=parser.parse_args()
    df=regenerar(args.raw,args.out)
    print(f'Listo: {len(df)} reaches, {int(df.fechas_unicas.sum())} fechas; '
          f'{int(df.saltos_para_revisar.sum())} saltos exploratorios. {args.out}')
