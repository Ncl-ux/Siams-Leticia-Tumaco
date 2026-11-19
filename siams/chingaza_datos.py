"""Insumos mensuales Chingaza. No leer datos diarios desde la aplicación pública."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / 'data/processed/chingaza'
ACT = RAIZ / 'data/processed/actualizacion'
NASA_COLUMNAS = {
    'precipitacion_mm_mes': 'Precipitación mensual (mm)',
    'temperatura_media_C': 'Temperatura media (°C)',
    'temperatura_maxima_C': 'Temperatura máxima (°C)',
    'temperatura_minima_C': 'Temperatura mínima (°C)',
    'humedad_relativa_pct': 'Humedad relativa (%)',
    'viento_2m_m_s': 'Viento a 2 m (m/s)',
    'presion_superficie_kPa': 'Presión superficial (kPa)',
    'radiacion_solar_MJ_m2_dia': 'Radiación solar (MJ/m²/día)',
}

def referencia(base=BASE):
    return json.loads((Path(base)/'cartografia.json').read_text(encoding='utf-8'))['referencia']

def leer_eaab(base=BASE):
    d = pd.read_csv(Path(base)/'eaab_mensual.csv', dtype={'estacion':str}, parse_dates=['fecha'])
    if d.fecha.isna().any() or not d.fecha.dt.day.eq(1).all() or d.duplicated(['estacion','variable','fecha']).any():
        raise ValueError('Claves mensuales EAAB inválidas')
    if d.loc[d.valor.notna(),'dias_validos'].ne(d.loc[d.valor.notna(),'fecha'].dt.days_in_month).any():
        raise ValueError('Mes EAAB incompleto con valor publicado')
    return d

def leer_nasa(base=ACT):
    p = Path(base)/'nasa_power_chingaza_mensual.csv'
    if not p.is_file(): return pd.DataFrame(columns=['fecha',*NASA_COLUMNAS])
    d=pd.read_csv(p,parse_dates=['fecha'])[['fecha',*NASA_COLUMNAS]]
    if d.fecha.isna().any() or d.fecha.duplicated().any() or not d.fecha.dt.day.eq(1).all():
        raise ValueError('Fechas NASA mensuales inválidas')
    return d.sort_values('fecha')

def climatologia_nasa(base=ACT):
    d=leer_nasa(base)
    if d.empty: return pd.DataFrame()
    mes=d.groupby(d.fecha.dt.month)[list(NASA_COLUMNAS)].mean().reindex(range(1,13)).rename(columns=NASA_COLUMNAS)
    mes.insert(0,'Mes',['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'])
    return mes.reset_index(drop=True)

def agregar_diario(d, modo):
    """Un valor por día, sin negativos ni marcas sin interpretar; meses completos."""
    d=d.copy()
    d['fecha']=pd.to_datetime(d.fecha,errors='raise').dt.normalize()
    if d.fecha.isna().any() or d.fecha.duplicated().any(): raise ValueError('Días inválidos o duplicados')
    v=pd.to_numeric(d.valor,errors='coerce')
    v=v.where(np.isfinite(v)&v.ge(0)&d.flag.fillna('').astype(str).str.strip().eq(''))
    s=pd.Series(v.to_numpy(),index=pd.DatetimeIndex(d.fecha)).sort_index()
    g=s.resample('MS'); n=g.count(); esperado=n.index.days_in_month
    m=g.sum(min_count=1) if modo=='sum' else g.mean()
    return pd.DataFrame({'fecha':n.index,'valor':m.where(n.eq(esperado)).values,'dias_validos':n.values,'dias_mes':esperado})

def agregar_nasa(d, hoy=None):
    d=d.copy(); d['fecha']=pd.to_datetime(d.fecha,errors='raise').dt.normalize()
    if d.fecha.isna().any() or d.fecha.duplicated().any(): raise ValueError('Fechas NASA duplicadas o inválidas')
    d=d.set_index('fecha').sort_index()
    d=d.rename(columns={'precipitacion_mm_dia':'precipitacion_mm_mes'})[list(NASA_COLUMNAS)].apply(pd.to_numeric,errors='coerce').replace(-999,np.nan)
    d=d.where(np.isfinite(d)); d['precipitacion_mm_mes']=d.precipitacion_mm_mes.where(d.precipitacion_mm_mes.ge(0)); d['humedad_relativa_pct']=d.humedad_relativa_pct.where(d.humedad_relativa_pct.between(0,100))
    g=d.resample('MS'); n=g.count(); out=g.mean(); out['precipitacion_mm_mes']=g.precipitacion_mm_mes.sum(min_count=1)
    out=out.where(n.eq(n.index.days_in_month,axis=0)); fin=pd.Timestamp(hoy or pd.Timestamp.today()).replace(day=1).normalize()
    return out.loc[out.index<fin].rename_axis('fecha').reset_index()

def anual_completo(d, modo):
    d=d[['fecha','valor']].dropna().copy(); d['fecha']=pd.to_datetime(d.fecha)
    if d.fecha.duplicated().any() or not d.fecha.dt.day.eq(1).all(): raise ValueError('Serie mensual no válida')
    g=d.groupby(d.fecha.dt.year); n=g.valor.count()
    if modo=='sum': v=g.valor.sum()
    else:
        d['peso']=d.fecha.dt.days_in_month; d['ponderado']=d.valor*d.peso
        v=d.groupby(d.fecha.dt.year).ponderado.sum()/d.groupby(d.fecha.dt.year).peso.sum()
    return v[n.eq(12)].rename('valor').rename_axis('anio').reset_index()

# SIAMS_CHINGAZA_VALIDACION_MENSUAL

def comparar_precipitacion_mensual(tabla, referencia='Observada'):
    """Métricas sobre pares mensuales válidos; no imputa ni cambia la serie."""
    if referencia not in tabla or tabla.index.has_duplicates:
        raise ValueError('Referencia ausente o fechas duplicadas')
    filas = []
    for fuente in tabla.columns:
        if fuente == referencia:
            continue
        par = tabla[[referencia, fuente]].apply(pd.to_numeric, errors='coerce')
        par = par.where(np.isfinite(par) & par.ge(0)).dropna()
        n = len(par)
        if not n:
            continue
        o, s = par[referencia].to_numpy(), par[fuente].to_numpy()
        e = s-o
        mo, ms = o.mean(), s.mean()
        so, ss = o.std(), s.std()
        r = np.corrcoef(o,s)[0,1] if n >= 3 and so > 0 and ss > 0 else np.nan
        nse = 1 - np.sum(e**2)/np.sum((o-mo)**2) if n >= 3 and so > 0 else np.nan
        kge = 1 - np.sqrt((r-1)**2+(ss/so-1)**2+(ms/mo-1)**2) if np.isfinite(r) and mo > 0 else np.nan
        filas.append({'Fuente':fuente,'Meses comunes':n,'Inicio':par.index.min().strftime('%Y-%m'),
                      'Fin':par.index.max().strftime('%Y-%m'),'Sesgo (mm)':e.mean(),
                      'PBIAS (%)':100*e.sum()/o.sum() if o.sum()>0 else np.nan,
                      'MAE (mm)':np.abs(e).mean(),'RMSE (mm)':np.sqrt(np.mean(e**2)),
                      'r Pearson':r,'NSE':nse,'KGE 2009':kge})
    return pd.DataFrame(filas)


def anual_desde_serie(serie, modo):
    """Adaptador para series mensuales de cualquier fuente; conserva las fechas y valores."""
    return anual_completo(serie.rename_axis('fecha').reset_index(name='valor'), modo)
