"""Contraste IDEAM–POWER de Bogotá y series anuales independientes.

No modifica las series de origen ni las pruebas estadísticas de SIAMS.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from .ideam_bogota_datos import BASE

NASA = BASE.parent / 'actualizacion' / 'nasa_power_bogota.csv'
VARIABLES = {
    'Precipitación': ('precipitacion_mm_dia', 'mm'),
    'Temperatura media': ('temperatura_media_C', '°C'),
    'Temperatura máxima': ('temperatura_maxima_C', '°C'),
    'Temperatura mínima': ('temperatura_minima_C', '°C'),
    'Humedad relativa': ('humedad_relativa_pct', '%'),
}


def meses_validos(m):
    x = m.copy()
    x['MesFecha'] = pd.to_datetime(x.MesFecha, errors='raise')
    if x.duplicated(['CodigoEstacion', 'Variable', 'MesFecha']).any():
        raise ValueError('Meses duplicados por estación y variable')
    if not x.MesFecha.dt.day.eq(1).all():
        raise ValueError('La fecha mensual debe ser el primer día del mes')
    return x[x.Dias.eq(x.MesFecha.dt.days_in_month) & np.isfinite(x.Valor)].copy()


def nasa_mensual(diario, variable):
    col = VARIABLES[variable][0]
    d = diario[['fecha', col]].copy()
    d['fecha'] = pd.to_datetime(d.fecha, errors='raise').dt.normalize()
    if d.fecha.isna().any() or d.fecha.duplicated().any():
        raise ValueError('Fechas NASA inválidas o duplicadas')
    d[col] = pd.to_numeric(d[col], errors='coerce').replace(-999., np.nan)
    d.loc[~np.isfinite(d[col]), col] = np.nan
    if variable == 'Precipitación':
        d.loc[d[col].lt(0), col] = np.nan
    elif variable == 'Humedad relativa':
        d.loc[~d[col].between(0, 100), col] = np.nan
    d = d.set_index('fecha').sort_index()[col]
    g = d.resample('MS')
    v = g.sum(min_count=1) if variable == 'Precipitación' else g.mean()
    v = v.where(g.count().eq(v.index.days_in_month))
    return v.dropna().rename('NASA POWER').rename_axis('MesFecha').reset_index()


def pares_mensuales(m, diario, codigo, variable):
    x = meses_validos(m)
    x = x.loc[x.CodigoEstacion.astype(str).eq(str(codigo)) & x.Variable.eq(variable)]
    x = x[['MesFecha', 'Valor', 'Dias', 'Definitivos', 'Inferidos']].rename(columns={'Valor': 'IDEAM'})
    p = x.merge(nasa_mensual(diario, variable), on='MesFecha', how='inner', validate='one_to_one').sort_values('MesFecha')
    return p.reset_index(drop=True)


def regimen_pareado(p):
    """Mismas fechas para las dos fuentes; tamaño muestral visible por mes."""
    p = p.copy()
    p['Mes'] = p.MesFecha.dt.month
    r = p.groupby('Mes').agg(IDEAM=('IDEAM', 'mean'), NASA=('NASA POWER', 'mean'), Pares=('IDEAM', 'size'))
    r = r.reindex(range(1, 13))
    r['Pares'] = r.Pares.fillna(0).astype(int)
    return r.rename_axis('Mes').reset_index()


def anuales_ideam(m):
    """Doce meses completos, por código; T/HR ponderadas por días reales."""
    x = meses_validos(m)
    x['Anio'] = x.MesFecha.dt.year
    filas = []
    for (codigo, variable, anio), g in x.groupby(['CodigoEstacion', 'Variable', 'Anio']):
        if len(g) != 12 or g.MesFecha.dt.month.nunique() != 12:
            continue
        v = g.Valor.sum() if variable == 'Precipitación' else np.average(g.Valor, weights=g.Dias)
        filas.append((str(codigo), variable, int(anio), float(v), int(g.Dias.sum()), int(g.Definitivos.sum()), int(g.Inferidos.sum())))
    return pd.DataFrame(filas, columns=['CodigoEstacion','Variable','Anio','Valor','Dias','Definitivos','Inferidos'])


def paquetes_ideam(m, nombres):
    """El motor MK existente recibe una observación por año completo."""
    a = anuales_ideam(m)
    paquetes = {}
    for (codigo, variable), g in a.groupby(['CodigoEstacion', 'Variable']):
        if len(g) < 5 or variable not in VARIABLES:
            continue
        etiqueta = f'{variable} · {nombres.get(codigo, codigo)} [{codigo}] (IDEAM)'
        serie = g[['Anio','Valor']].copy()
        serie['Fecha'] = pd.to_datetime(serie.pop('Anio').astype(str) + '-01-01')
        serie = serie.sort_values('Fecha')[['Fecha','Valor']].reset_index(drop=True)
        paquetes[etiqueta] = {'serie': serie, 'unidad': VARIABLES[variable][1], 'agregacion': 'sum' if variable == 'Precipitación' else 'mean', 'fuente': 'IDEAM · exploratorio', 'archivo': 'mensual.csv', 'hoja': f'{codigo} · años completos sin imputación'}
    return paquetes
