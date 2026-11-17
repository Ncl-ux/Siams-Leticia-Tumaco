"""Build SIAMS-compatible NASA Excel from the weekly CSV; never modify original Excel.

The original observation windows are retained by default, extended to the latest
available date. Full history remains in the weekly CSV. The monthly climatology
excludes incomplete months per variable; the original daily data are unchanged.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams.estadistica import agregar_serie_anual, evaluar_homogeneidad

RUTA = RAIZ / 'data' / 'processed' / 'actualizacion'
INICIOS = {'bogota': '1981-01-01', 'leticia': '2000-01-01',
           'tumaco': '1992-01-01', 'arauca': '2000-01-01',
           'la_paz': '2000-01-01', 'medellin': '2000-01-01',
           'san_andres': '2000-01-01'}
_spec = importlib.util.spec_from_file_location('nasa_original', RAIZ / 'scripts' / '01_descarga_nasa_power.py')
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)
COLUMNAS = list(_original.PARAMETROS.values())


def leer_diario(ruta: Path, sede: str) -> pd.DataFrame:
    d = pd.read_csv(ruta, parse_dates=['fecha'])[['fecha', *COLUMNAS]]
    if d.empty or d.fecha.isna().any() or d.fecha.duplicated().any():
        raise ValueError('Serie vacía, fechas inválidas o duplicadas')
    d = d.sort_values('fecha').reset_index(drop=True)
    if not d.fecha.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError('Fechas calendario ausentes')
    if d.fecha.min() > pd.Timestamp(INICIOS[sede]):
        raise ValueError('No se cubre el inicio histórico requerido')
    for c in COLUMNAS:
        d[c] = pd.to_numeric(d[c], errors='raise').replace(-999.0, float('nan'))
        if not d[c].notna().any():
            raise ValueError(f'Variable sin datos: {c}')
    if (d.precipitacion_mm_dia.dropna() < 0).any() or not d.humedad_relativa_pct.dropna().between(0, 100).all():
        raise ValueError('Precipitación o humedad fuera de rango')
    return d.loc[d.fecha >= pd.Timestamp(INICIOS[sede])].reset_index(drop=True)


def construir_hojas(d: pd.DataFrame, sede: str, homogeneidad=True):
    hojas = _original.armar_hojas(d)
    diario = d.set_index('fecha')
    conteos = diario.resample('MS').count()
    completos = conteos.eq(conteos.index.days_in_month, axis=0)
    mascara = completos.reindex(diario.index.to_period('M').to_timestamp())
    mascara.index = diario.index
    filtrado = diario.where(mascara).reset_index()
    # Keep the original weighting/aggregation; only exclude incomplete months.
    clima = _original.armar_hojas(filtrado)
    for hoja in ('Regimen_P', 'Regimen_T', 'Regimen_HR', 'Climatologia_mensual'):
        hojas[hoja] = clima[hoja]
    hojas['Control_mensual'] = conteos.reset_index()
    hojas['Metodologia'] = pd.DataFrame({'Campo': ['Fuente', 'Sede', 'Inicio de análisis', 'Climatología', 'Histórico', 'Homogeneidad'],
        'Valor': ['NASA POWER AG; radiación MJ/m²/día', sede, INICIOS[sede],
                 'Solo meses completos por variable; medias y sumas del script 01',
                 'CSV semanal conserva el histórico desde 1981',
                 'Pettitt y SNHT absolutos sobre agregados anuales; no certifican homogeneidad']})
    if homogeneidad:
        filas = []
        # Match the current app: discard final year if the daily calendar is incomplete.
        final = d.fecha.max()
        base = d if (final.month, final.day) == (12, 31) else d[d.fecha.dt.year < final.year]
        for col in COLUMNAS:
            anual = agregar_serie_anual(base.rename(columns={'fecha': 'Fecha', col: 'Valor'}),
                                        'sum' if col == COLUMNAS[0] else 'mean')
            if len(anual) < 10:
                continue
            r = evaluar_homogeneidad(anual['Año'], anual['Valor'])
            filas.append({'variable': col, 'inicio': int(anual['Año'].min()), 'fin': int(anual['Año'].max()),
                          'n_anios': len(anual), **r})
        hojas['Homogeneidad_NASA'] = pd.DataFrame(filas)
    return hojas


def generar(sede: str, carpeta: Path = RUTA, homogeneidad=True) -> Path:
    origen = carpeta / f'nasa_power_{sede}.csv'
    destino = carpeta / f'nasa_power_{sede}_actualizado.xlsx'
    d = leer_diario(origen, sede)
    hojas = construir_hojas(d, sede, homogeneidad)
    temporal = destino.with_name(destino.stem + '.tmp.xlsx')
    try:
        with pd.ExcelWriter(temporal, engine='openpyxl') as w:
            for nombre, tabla in hojas.items():
                tabla.to_excel(w, sheet_name=nombre, index=nombre == 'Resumen_estadistico')
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sedes', default=','.join(INICIOS))
    a = ap.parse_args()
    for sede in a.sedes.split(','):
        print(generar(sede), flush=True)


if __name__ == '__main__':
    main()
