"""Niveles fluviales públicos existentes de Leticia; sin nuevas descargas."""
from pathlib import Path
import numpy as np
import pandas as pd
from .grace_datos import DATOS_PUBLICOS, RUTA, cargar, leer_csv_seguro

FUENTES = {
    'ANA Tabatinga': ('ana_diario.csv', 'cota_m', 'ana_cota_m'),
    'IDEAM Leticia': ('rio_diario.csv', 'nivel_m', 'ideam_nivel_m'),
}


def serie_diaria(df, columna):
    """Rechaza fechas duplicadas, conserva niveles negativos (referencia local)."""
    if not {'fecha', columna}.issubset(df.columns):
        raise ValueError(f'Columnas requeridas: fecha, {columna}')
    fechas = pd.to_datetime(df.fecha, errors='coerce').dt.normalize()
    if fechas.isna().any() or fechas.duplicated().any():
        raise ValueError('Fechas inválidas o duplicadas; revisar el archivo de origen.')
    valores = pd.to_numeric(df[columna], errors='coerce').replace([np.inf, -np.inf], np.nan)
    # Códigos explícitos de ausencia frecuentes; no se recortan niveles negativos reales.
    valores = valores.mask(valores.isin([-999, -9999]))
    s = pd.Series(valores.to_numpy(), index=pd.DatetimeIndex(fechas), name=columna).sort_index()
    if s.empty:
        return s
    return s.asfreq('D').rename_axis('fecha')


def cargar_series(raiz: Path = DATOS_PUBLICOS, alternativa: Path = RUTA):
    """Prefiere cada serie pública diaria; alternativa pública sin empalmar archivos."""
    series, origen, avisos = {}, {}, {}
    for nombre, (archivo, col, col_alt) in FUENTES.items():
        try:
            df = cargar(archivo, raiz=raiz)
            if df.empty:
                df = leer_csv_seguro(alternativa, {'fecha', col_alt})
                if df.empty:
                    raise FileNotFoundError(archivo)
                s = serie_diaria(df, col_alt)
                fuente = alternativa.name
            else:
                s = serie_diaria(df, col)
                fuente = archivo
            s = s.loc[s.first_valid_index():s.last_valid_index()] if s.notna().any() else s.iloc[:0]
            if s.empty:
                raise ValueError('Sin valores numéricos válidos')
            series[nombre] = s.rename(nombre)
            origen[nombre] = fuente
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            avisos[nombre] = str(exc)
    return series, origen, avisos


PERIODOS = ('Histórico completo', 'Últimos 10 años', 'Últimos 5 años',
            'Último año disponible', 'Personalizado')


def periodo_consulta(s, modo='Histórico completo', inicio=None, fin=None):
    """Límites inclusivos, anclados a la última observación de la estación."""
    valido = s.dropna()
    if valido.empty:
        raise ValueError('La estación no contiene observaciones válidas.')
    primero, ultimo = valido.index.min().normalize(), valido.index.max().normalize()
    if modo == 'Histórico completo':
        a, b = primero, ultimo
    elif modo in ('Últimos 10 años', 'Últimos 5 años'):
        n = 10 if modo == 'Últimos 10 años' else 5
        a, b = max(primero, ultimo - pd.DateOffset(years=n) + pd.Timedelta(days=1)), ultimo
    elif modo == 'Último año disponible':
        a, b = max(primero, ultimo.replace(month=1, day=1)), ultimo
    elif modo == 'Personalizado':
        a = primero if inicio is None else pd.Timestamp(inicio).normalize()
        b = ultimo if fin is None else pd.Timestamp(fin).normalize()
        if pd.isna(a) or pd.isna(b) or a < primero or b > ultimo or a > b:
            raise ValueError('Selecciona fechas ordenadas dentro del periodo disponible.')
    else:
        raise ValueError('Periodo de consulta desconocido.')
    return a, b


def resumen(s):
    d = s.dropna()
    if d.empty:
        return {'dias': 0, 'cobertura': 0., 'inicio': None, 'fin': None}
    esperado = (s.index.max() - s.index.min()).days + 1
    return {'dias': len(d), 'cobertura': 100 * len(d) / esperado,
            'inicio': d.index.min(), 'fin': d.index.max()}


def mensual(s):
    """Medias de nivel (m), no sumas ni caudales; solo meses completos."""
    if s.empty:
        return pd.DataFrame(columns=['nivel_m', 'dias_validos', 'dias_mes', 'cobertura_pct'])
    t = s.resample('MS').agg(['mean', 'count']).rename(columns={'mean':'nivel_m','count':'dias_validos'})
    t['dias_mes'] = t.index.days_in_month
    t['cobertura_pct'] = 100 * t.dias_validos / t.dias_mes
    t['nivel_m'] = t.nivel_m.where(t.dias_validos.eq(t.dias_mes))
    return t.rename_axis('mes')


def comparar(series):
    """Misma lógica relativa que grace_datos.cargar_y_comparar: fechas comunes y centrado."""
    if not set(FUENTES).issubset(series):
        return pd.DataFrame(), {'n': 0, 'r_pearson': np.nan}
    t = pd.concat([series[n] for n in FUENTES], axis=1).sort_index().asfreq('D')
    comunes = t.dropna()
    n = len(comunes)
    r = comunes.corr().iloc[0, 1] if n >= 30 else np.nan
    if n < 30:
        return pd.DataFrame(index=t.index), {'n': n, 'r_pearson': r}
    # Días no emparejados permanecen nulos en AMBAS curvas.
    relativas = (comunes - comunes.mean()).reindex(t.index)
    return relativas, {'n': n, 'r_pearson': r, 'inicio': comunes.index.min(), 'fin': comunes.index.max()}
