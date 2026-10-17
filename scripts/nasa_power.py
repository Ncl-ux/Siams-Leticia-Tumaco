"""NASA POWER: descargar respuesta JSON original y generar tablas SIAMS auditables.

Los Excel históricos de SIAMS NO se sobrescriben por defecto. Un archivo
regenerado debe compararse con la versión publicada antes de reemplazarla.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/nasa_power'
PROCESSED=ROOT/'data/processed/clima'
PARAMETROS={
  'PRECTOTCORR':'precipitacion_mm_dia',
  'T2M':'temperatura_media_C',
  'T2M_MAX':'temperatura_maxima_C',
  'T2M_MIN':'temperatura_minima_C',
  'RH2M':'humedad_relativa_pct',
  'WS2M':'viento_2m_m_s',
  'PS':'presion_superficie_kPa',
  'ALLSKY_SFC_SW_DWN':'radiacion_solar_MJ_m2_dia',
}


def descargar(sede,lat,lon,inicio,fin,out=None):
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Coordenadas inválidas')
    if not (len(inicio)==len(fin)==8 and inicio.isdigit() and fin.isdigit()):
        raise ValueError('Fechas en formato AAAAMMDD')
    q=urlencode(dict(community='AG',parameters=','.join(PARAMETROS),latitude=lat,
                     longitude=lon,start=inicio,end=fin,format='JSON'))
    url='https://power.larc.nasa.gov/api/temporal/daily/point?'+q
    req=Request(url,headers={'User-Agent':'SIAMS reproducibilidad A5 (uso académico)'})
    with urlopen(req,timeout=120) as r:respuesta=json.load(r)
    if 'properties' not in respuesta or 'parameter' not in respuesta['properties']:
        raise ValueError('Respuesta NASA POWER sin properties.parameter')
    out=Path(out) if out else RAW/f'nasa_power_{sede}_{inicio}_{fin}.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(respuesta,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def _unidad_radiacion(respuesta):
    try: u=respuesta['header']['parameter_information']['ALLSKY_SFC_SW_DWN']['units']
    except KeyError as e:raise ValueError('Falta unidad de radiación original en metadatos NASA; no se puede inferir.') from e
    u=str(u).lower().replace(' ','').replace('²','^2')
    if ('mj' in u and ('day' in u or 'd' in u)):
        return 1.0
    if ('kwh' in u or 'kw-hr' in u) and ('day' in u or 'd' in u):
        return 3.6  # kWh -> MJ
    raise ValueError(f'Unidad solar desconocida: {u!r}; revisar POWER antes de procesar')


def crear_diarios(respuesta):
    parametros=respuesta.get('properties',{}).get('parameter',{})
    faltantes=set(PARAMETROS)-set(parametros)
    if faltantes:raise ValueError(f'Variables NASA faltantes: {sorted(faltantes)}')
    radiacion_factor=_unidad_radiacion(respuesta)
    keys=sorted({k for serie in parametros.values() for k in serie})
    df=pd.DataFrame({'fecha':pd.to_datetime(keys,format='%Y%m%d',errors='raise')})
    for key,nombre in PARAMETROS.items():
        vals=[parametros[key].get(f,np.nan) for f in keys]
        df[nombre]=pd.to_numeric(pd.Series(vals),errors='coerce')
        df[nombre]=df[nombre].mask(df[nombre]<=-990)
        if key=='ALLSKY_SFC_SW_DWN':df[nombre]=df[nombre]*radiacion_factor
    return df


def procesar(ruta, salida):
    with Path(ruta).open(encoding='utf-8') as f: respuesta=json.load(f)
    df=crear_diarios(respuesta)
    if df.empty:raise ValueError('La consulta no devolvió fechas')
    df=df.sort_values('fecha').reset_index(drop=True)
    work=df.set_index('fecha')
    meses=work.resample('MS')
    years=work.resample('YS')
    pmes=meses['precipitacion_mm_dia'].sum(min_count=1).to_frame('precipitacion_acumulada_mm_mes').reset_index()
    panio=years['precipitacion_mm_dia'].sum(min_count=1).to_frame('precipitacion_acumulada_mm_anio').reset_index()
    panio['anio']=panio.fecha.dt.year
    tcols=['temperatura_media_C','temperatura_maxima_C','temperatura_minima_C']
    tmes=meses[tcols].mean().reset_index()
    hrmes=meses['humedad_relativa_pct'].mean().reset_index()
    viento=meses['viento_2m_m_s'].mean().reset_index()
    presion=meses['presion_superficie_kPa'].mean().reset_index()
    rad=meses['radiacion_solar_MJ_m2_dia'].mean().reset_index().rename(columns={'radiacion_solar_MJ_m2_dia':'radiacion_solar_media_MJ_m2_dia'})
    regimen_p=pmes.assign(mes=lambda x:x.fecha.dt.month).groupby('mes',as_index=False)['precipitacion_acumulada_mm_mes'].mean().rename(columns={'precipitacion_acumulada_mm_mes':'precipitacion_media_mensual_multianual_mm_mes'})
    reg_t=tmes.assign(mes=lambda x:x.fecha.dt.month).groupby('mes',as_index=False)[tcols].mean()
    reg_hr=hrmes.assign(mes=lambda x:x.fecha.dt.month).groupby('mes',as_index=False)['humedad_relativa_pct'].mean()
    clim=work.assign(mes=lambda x:x.index.month).groupby('mes',as_index=False).mean(numeric_only=True).rename(columns={'radiacion_solar_MJ_m2_dia':'radiacion_solar_media_diaria_MJ_m2_dia'})
    estad=work.describe().T.reset_index().rename(columns={'index':'variable'})
    indicadores=pd.DataFrame({'Indicador':['Fecha inicial','Fecha final','Registros','Fuente','Datos de entrada'],
                              'Valor':[str(df.fecha.min().date()),str(df.fecha.max().date()),len(df),'NASA POWER Daily',str(ruta)]})
    diccionario=pd.DataFrame([
        ('Datos_diarios',k,un,'Dato diario') for k,un in {
            'precipitacion_mm_dia':'mm/día','temperatura_media_C':'°C',
            'temperatura_maxima_C':'°C','temperatura_minima_C':'°C',
            'humedad_relativa_pct':'%','viento_2m_m_s':'m/s',
            'presion_superficie_kPa':'kPa','radiacion_solar_MJ_m2_dia':'MJ/m²/día'}.items()
    ] + [('P_mensual','precipitacion_acumulada_mm_mes','mm/mes','Suma diaria'),
         ('P_anual','precipitacion_acumulada_mm_anio','mm/año','Suma diaria'),
         ('Radiacion_mensual','radiacion_solar_media_MJ_m2_dia','MJ/m²/día','Media de valores diarios')],
        columns=['Hoja','Variable','Unidad','Agregación'])
    tablas={'Datos_diarios':df,'Resumen_estadistico':estad,'Indicadores':indicadores,
            'P_mensual':pmes,'P_anual':panio,'Regimen_P':regimen_p,
            'T_mensual':tmes,'Regimen_T':reg_t,'HR_mensual':hrmes,
            'Regimen_HR':reg_hr,'Viento_mensual':viento,'Presion_mensual':presion,
            'Radiacion_mensual':rad,'Climatologia_mensual':clim,
            'Diccionario':diccionario}
    salida=Path(salida);salida.parent.mkdir(parents=True,exist_ok=True)
    if salida.exists(): raise FileExistsError(f'No se sobrescribe un Excel existente: {salida}')
    with pd.ExcelWriter(salida,engine='openpyxl') as writer:
        for hoja,tabla in tablas.items():tabla.to_excel(writer,sheet_name=hoja,index=False)
    return salida


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='accion',required=True)
    d=sub.add_parser('descargar');d.add_argument('--sede',required=True)
    d.add_argument('--lat',type=float,required=True);d.add_argument('--lon',type=float,required=True)
    d.add_argument('--inicio',required=True);d.add_argument('--fin',required=True)
    d.add_argument('--out',type=Path)
    pr=sub.add_parser('procesar');pr.add_argument('--raw',type=Path,required=True)
    pr.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.accion=='descargar': print(descargar(args.sede,args.lat,args.lon,args.inicio,args.fin,args.out))
    else: print(procesar(args.raw,args.out))
