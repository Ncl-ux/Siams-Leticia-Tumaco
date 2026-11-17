"""Series mensuales independientes; sin imputar ni extrapolar meses parciales."""
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ACTUALIZACION = RAIZ / 'data/processed/actualizacion'
LETICIA = RAIZ / 'data/processed/observatorio_leticia'
SEDES = {'Bogotá':'bogota','Leticia':'leticia','Tumaco':'tumaco','Medellín':'medellin',
         'San Andrés':'san_andres','Arauca':'arauca','La Paz':'la_paz'}
VALOR = 'precipitacion_mm_mes'


def ultimo_mes(hoy=None):
    return pd.Timestamp(hoy or pd.Timestamp.today()).normalize().replace(day=1) - pd.offsets.MonthBegin(1)


def mensual(df, fecha='fecha', valor=VALOR, hoy=None):
    f = pd.to_datetime(df[fecha], errors='raise').dt.to_period('M').dt.to_timestamp()
    if f.isna().any() or f.duplicated().any():
        raise ValueError('Meses inválidos o duplicados')
    v = pd.to_numeric(df[valor], errors='coerce')
    s = pd.Series(v.to_numpy(), index=pd.DatetimeIndex(f), dtype=float)
    s = s.where(np.isfinite(s) & s.ge(0)).sort_index()
    return s.loc[s.index <= ultimo_mes(hoy)]


def nasa_mensual(df, hoy=None):
    f = pd.to_datetime(df.fecha, errors='raise').dt.normalize()
    if f.isna().any() or f.duplicated().any():
        raise ValueError('Días NASA POWER inválidos o duplicados')
    v = pd.to_numeric(df.precipitacion_mm_dia, errors='coerce')
    s = pd.Series(v.to_numpy(), index=pd.DatetimeIndex(f), dtype=float).sort_index()
    s = s.where(np.isfinite(s) & s.ge(0))
    g = s.resample('MS')
    m = g.sum(min_count=1)
    return m.where(g.count().eq(m.index.days_in_month)).loc[:ultimo_mes(hoy)]


def fuentes(sede, raiz=None):
    base = Path(raiz) if raiz else ACTUALIZACION
    let = base.parent / 'observatorio_leticia'
    d = {'CHIRPS v3 Final':(base/f'chirps_{sede}.csv','fecha',VALOR),
         'IMERG Final V07B (NASA)' :(base/f'imerg_final_{sede}.csv','fecha',VALOR),
         'NASA POWER':(base/f'nasa_power_{sede}.csv','fecha','precipitacion_mm_dia')}
    if sede == 'leticia':
        d.update({'CHIRPS v2 (histórico Leticia)':(let/'chirps_v2_leticia_mensual.csv','month','Leticia'),
                  'IMERG Final V07 (histórico Leticia)':(let/'imerg_final_leticia_mensual.csv','month','Leticia')})
    return d


def cargar(sede, raiz=None, hoy=None):
    series, avisos = {}, {}
    for nombre,(ruta,fecha,valor) in fuentes(sede,raiz).items():
        try:
            df = pd.read_csv(ruta)
            s = nasa_mensual(df,hoy) if nombre == 'NASA POWER' else mensual(df,fecha,valor,hoy)
            if not s.notna().any():
                raise ValueError('Sin valores mensuales válidos')
            series[nombre] = s.rename(nombre)
        except (OSError,ValueError,KeyError) as e:
            avisos[nombre] = f'{ruta.name}: {e}'
    if not series:
        return pd.DataFrame(), avisos
    tabla = pd.concat(series.values(),axis=1).sort_index()
    tabla = tabla.reindex(pd.date_range(tabla.index.min(),tabla.index.max(),freq='MS'))
    tabla.index.name = 'fecha'
    return tabla, avisos


def inventario(tabla):
    filas = []
    for nombre in tabla:
        s = tabla[nombre].dropna()
        if s.empty: continue
        esperados = len(pd.date_range(s.index.min(),s.index.max(),freq='MS'))
        filas.append({'Fuente':nombre,'Inicio':s.index.min().strftime('%Y-%m'),'Último mes':s.index.max().strftime('%Y-%m'),
                      'Meses válidos':len(s),'Huecos internos':esperados-len(s),'Cobertura interna (%)':round(100*len(s)/esperados,2)})
    return pd.DataFrame(filas)


def pares(tabla, referencia):
    filas = []
    for col in tabla:
        if col == referencia: continue
        p = tabla[[referencia,col]].dropna()
        if p.empty: continue
        e = p[col]-p[referencia]
        filas.append({'Fuente':col,'Meses comunes':len(p),'Inicio':p.index.min().strftime('%Y-%m'),
                      'Fin':p.index.max().strftime('%Y-%m'),'Sesgo (mm)':e.mean(),'MAE (mm)':e.abs().mean(),
                      'RMSE (mm)':np.sqrt(e.pow(2).mean()),'r Pearson':p.corr().iloc[0,1] if len(p)>1 else np.nan})
    return pd.DataFrame(filas)


def ideam_bogota(codigo, raiz=None):
    from .ideam_bogota_clima_datos import meses_validos
    ruta = (Path(raiz) if raiz else ACTUALIZACION).parent/'ideam_bogota/mensual.csv'
    m = meses_validos(pd.read_csv(ruta,dtype={'CodigoEstacion':str}))
    m = m.loc[m.Variable.eq('Precipitación') & m.CodigoEstacion.eq(str(codigo))]
    return mensual(m,'MesFecha','Valor')


def ideam_leticia(raiz=None):
    # Mismo criterio y estación utilizados en la validación existente de GRACE.
    ruta = (Path(raiz) if raiz else ACTUALIZACION).parent/'observatorio_leticia/ideam_precip_mensual_qc.csv'
    m = pd.read_csv(ruta,dtype={'estacion':str})
    m = m.loc[m.estacion.str.lstrip('0').eq('48015050') & m.completo.astype(str).str.lower().eq('true')]
    return mensual(m,'mes','precip_mm_dias_validos')
