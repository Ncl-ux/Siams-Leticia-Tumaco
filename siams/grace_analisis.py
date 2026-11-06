"""Cálculos GRACE/Leticia consolidados sin cambiar los métodos científicos.

Incluye correlaciones exploratorias, QC, validación mensual y diaria,
comparación estacional, Piper y estadística del semillero.
"""
from __future__ import annotations
from pathlib import Path
import calendar
import numpy as np
import pandas as pd
from .grace_datos import RAIZ, DATOS, ACTUALIZACION, DATOS_PUBLICOS, leer_csv_seguro, cargar_validacion

FUENTES_DIARIAS = {
    "IDEAM": "lluvia_ideam_mm",
    "CHIRPS v3": "lluvia_chirps_v3_mm",
    "IMERG Late V07": "lluvia_imerg_late_mm",
    "ERA5": "lluvia_era5_mm",
}


def _indice_meses(df: pd.DataFrame, fecha: str, columna: str) -> pd.Series:
    fechas = pd.to_datetime(df[fecha], errors="coerce").dt.to_period("M").dt.to_timestamp()
    valores = pd.to_numeric(df[columna], errors="coerce")
    tabla = pd.DataFrame({"Fecha": fechas, columna: valores}).dropna(subset=["Fecha"])
    if tabla.empty:
        return pd.Series(dtype=float, name=columna)
    # Duplicados de la misma fuente/mes se documentan por media, sin inventar fechas.
    return tabla.groupby("Fecha")[columna].mean().sort_index().rename(columna)

def combinar_grace_lluvia(grace: pd.DataFrame, chirps: pd.DataFrame,
                          nasa_diaria: pd.DataFrame) -> pd.DataFrame:
    """Alinea GWSa (cm) y precipitaciones mensuales (mm/mes) por mes nominal.

    NASA: solo meses con >= 90 % de días registrados, para evitar totales
    acumulados de meses claramente incompletos. No interpola ningún valor.
    """
    if not {'nominal_month', 'GWSA_B_standard_cm', 'GWSA_A_original_cm'}.issubset(grace):
        raise ValueError('GRACE sin columnas A/B y mes nominal')
    if not {'fecha', 'precipitacion_mm_mes'}.issubset(chirps):
        raise ValueError('CHIRPS sin fecha y precipitación mensual')
    if not {'fecha', 'precipitacion_mm_dia'}.issubset(nasa_diaria):
        raise ValueError('NASA POWER sin fecha y precipitación diaria')
    partes = [
        _indice_meses(grace, 'nominal_month', 'GWSA_B_standard_cm').rename('GWSA_B_cm'),
        _indice_meses(grace, 'nominal_month', 'GWSA_A_original_cm').rename('GWSA_A_cm'),
        _indice_meses(chirps, 'fecha', 'precipitacion_mm_mes').rename('CHIRPS_mm_mes'),
    ]
    n = nasa_diaria[['fecha', 'precipitacion_mm_dia']].copy()
    n['fecha'] = pd.to_datetime(n['fecha'], errors='coerce').dt.normalize()
    n['precipitacion_mm_dia'] = pd.to_numeric(n['precipitacion_mm_dia'], errors='coerce')
    n = n.dropna(subset=['fecha']).sort_values('fecha').drop_duplicates('fecha', keep='last')
    n['mes'] = n['fecha'].dt.to_period('M').dt.to_timestamp()
    diario = n.groupby('mes')['precipitacion_mm_dia'].agg(['sum', 'count'])
    esperado = pd.Series([calendar.monthrange(i.year, i.month)[1] for i in diario.index], index=diario.index)
    diario['sum'] = diario['sum'].where(diario['count'].ge((esperado * 0.9).apply(np.ceil)))
    partes.append(diario['sum'].rename('NASA_POWER_mm_mes'))
    tabla = pd.concat(partes, axis=1).sort_index()
    if tabla.empty:
        return pd.DataFrame(columns=['Fecha', 'GWSA_B_cm', 'GWSA_A_cm', 'CHIRPS_mm_mes', 'NASA_POWER_mm_mes'])
    meses = pd.date_range(tabla.index.min(), tabla.index.max(), freq='MS')
    return tabla.reindex(meses).rename_axis('Fecha').reset_index()

def correlacion_mensual_desfase(df: pd.DataFrame, fuente: str, senal: str,
                                 max_lag: int = 6, min_pares: int = 12) -> pd.DataFrame:
    """r entre P(t-k) y GWSa(t), k=0..max_lag meses (asociación exploratoria)."""
    d = df.set_index('Fecha')[[fuente, senal]].sort_index()
    d = d.reindex(pd.date_range(d.index.min(), d.index.max(), freq='MS'))
    filas = []
    for lag in range(max_lag + 1):
        p = d[fuente].shift(lag)
        pares = pd.concat([p, d[senal]], axis=1).dropna()
        r = float(pares.iloc[:, 0].corr(pares.iloc[:, 1])) if len(pares) >= min_pares and \
            pares.iloc[:, 0].std() > 0 and pares.iloc[:, 1].std() > 0 else float('nan')
        filas.append({'Desfase (meses)': lag, 'r Pearson': r, 'Meses comunes': len(pares)})
    return pd.DataFrame(filas)

def preparar_numae_diario(datos: pd.DataFrame) -> pd.DataFrame:
    requeridas = {'fecha', 'columna_madrugada_m', 'fraccion_horas_bombeo', 'fraccion_horas_seco', *FUENTES_DIARIAS.values()}
    if not requeridas.issubset(datos.columns):
        raise ValueError('El CSV interno de Numae no tiene las columnas documentadas por el explorador')
    d = datos.copy()
    d['fecha'] = pd.to_datetime(d['fecha'], errors='coerce').dt.normalize()
    d = d.dropna(subset=['fecha']).sort_values('fecha').drop_duplicates('fecha', keep='last')
    for nombre in requeridas - {'fecha'}:
        d[nombre] = pd.to_numeric(d[nombre], errors='coerce')
    if d.empty:
        return d
    # Reindexar ANTES de diferenciar: un salto entre días ausentes no es cambio diario.
    d = d.set_index('fecha').reindex(pd.date_range(d['fecha'].min(), d['fecha'].max(), freq='D'))
    d.index.name = 'fecha'
    d['cambio_columna_m'] = d['columna_madrugada_m'].diff()
    return d.reset_index()

def correlacion_lluvia_cambio(d: pd.DataFrame, lluvia: str,
                               max_dias: int = 7, min_pares: int = 30) -> pd.DataFrame:
    """r de lluvia(t-k) vs Δcolumna(t), k en días; sin relleno temporal."""
    if d.empty:
        return pd.DataFrame(columns=['Desfase (días)', 'r Pearson', 'Pares válidos'])
    a = d.set_index('fecha').sort_index()
    filas = []
    for k in range(max_dias + 1):
        x = a[lluvia].shift(k)
        t = pd.concat([x.rename('lluvia'), a['cambio_columna_m']], axis=1).dropna()
        r = float(t['lluvia'].corr(t['cambio_columna_m'])) if len(t) >= min_pares and \
            t['lluvia'].std() > 0 and t['cambio_columna_m'].std() > 0 else float('nan')
        filas.append({'Desfase (días)': k, 'r Pearson': r, 'Pares válidos': len(t)})
    return pd.DataFrame(filas)

def calidad_horaria(datos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrega los registros que la profesora ya clasificó, sin reclasificarlos."""
    columnas = {'fecha', 'pozo_id', 'calidad'}
    if not columnas.issubset(datos):
        raise ValueError('Faltan campos de calidad horaria')
    d = datos.loc[datos['pozo_id'].eq('LET-NUMAE'), ['fecha', 'calidad']].copy()
    d['fecha'] = pd.to_datetime(d['fecha'], errors='coerce')
    d = d.dropna(subset=['fecha'])
    d['mes'] = d['fecha'].dt.to_period('M').dt.to_timestamp()
    d['hora'] = d['fecha'].dt.hour
    d['marcado'] = d['calidad'].ne('ok').astype(int)
    # Fracciones calculadas sobre observaciones disponibles, no sobre las horas ausentes.
    por_mes = d.groupby('mes').agg(registros=('marcado', 'size'),
                                   marcados=('marcado', 'sum')).reset_index()
    por_mes['fraccion_marcados_pct'] = 100 * por_mes['marcados'] / por_mes['registros']
    por_hora = d.groupby('hora').agg(registros=('marcado', 'size'),
                                     marcados=('marcado', 'sum')).reset_index()
    por_hora['fraccion_marcados_pct'] = 100 * por_hora['marcados'] / por_hora['registros']
    return por_mes, por_hora

def metricas_pares(obs: pd.Series, estimado: pd.Series, min_kge: int = 12) -> dict:
    """Sesgo = media(sim-obs), RMSE y r; KGE2009 para n>=12.

    No aplica KGE a muestras de solo cuatro meses ni a observaciones
    constantes; POD/FAR no son definibles sin pares diarios o subdiarios.
    """
    pares = pd.DataFrame({"obs": pd.to_numeric(obs, errors="coerce"),
                          "sim": pd.to_numeric(estimado, errors="coerce")}).replace(
                              [np.inf, -np.inf], np.nan).dropna()
    n = len(pares)
    salida = {"n": n, "sesgo_mm_mes": float("nan"), "rmse_mm_mes": float("nan"),
              "r_pearson": float("nan"), "kge_2009": float("nan")}
    if n == 0:
        return salida
    o, s = pares.obs.to_numpy(float), pares.sim.to_numpy(float)
    salida["sesgo_mm_mes"] = float(np.mean(s - o))
    salida["rmse_mm_mes"] = float(np.sqrt(np.mean((s - o)**2)))
    so, ss = float(np.std(o, ddof=1)) if n > 1 else 0., float(np.std(s, ddof=1)) if n > 1 else 0.
    if n >= 3 and so > 0 and ss > 0:
        r = float(np.corrcoef(o, s)[0, 1])
        salida["r_pearson"] = r
        if n >= min_kge and float(np.mean(o)) > 0:
            beta = float(np.mean(s) / np.mean(o))
            cv_obs, cv_sim = so / float(np.mean(o)), ss / float(np.mean(s)) if float(np.mean(s)) else float("nan")
            gamma = cv_sim / cv_obs if cv_obs else float("nan")
            if np.isfinite(gamma):
                salida["kge_2009"] = float(1 - np.sqrt((r - 1)**2 + (beta - 1)**2 + (gamma - 1)**2))
    return salida

def tabla_metricas(df: pd.DataFrame) -> pd.DataFrame:
    nombres = {"CHIRPS_v3_mm_mes": "CHIRPS v3", "CHIRPS_v2_mm_mes": "CHIRPS v2",
               "IMERG_Final_V07_mm_mes": "IMERG Final V07",
               "NASA_POWER_mm_mes": "NASA POWER"}
    filas = []
    for variable, etiqueta in nombres.items():
        resultado = metricas_pares(df["IDEAM_mm_mes"], df[variable])
        filas.append({"Producto": etiqueta, "Pares mensuales": resultado["n"],
                      "Sesgo (mm/mes)": resultado["sesgo_mm_mes"],
                      "RMSE (mm/mes)": resultado["rmse_mm_mes"],
                      "Pearson r": resultado["r_pearson"], "KGE 2009": resultado["kge_2009"]})
    return pd.DataFrame(filas)

def pod_far_diario(obs: pd.Series, estimado: pd.Series, umbral_mm: float = 1.) -> dict:
    """Probabilidad de detección y falsas alarmas, SOLO para pares diarios.

    Este método existe para una futura serie diaria satélite/estación;
    NO se aplica a los CSV mensuales distribuidos en este paquete.
    """
    pares = pd.DataFrame({"o": obs, "p": estimado}).apply(pd.to_numeric, errors="coerce").dropna()
    if pares.empty: return {"n":0,"POD":np.nan,"FAR":np.nan}
    o,p = pares.o.ge(umbral_mm), pares.p.ge(umbral_mm)
    h = int((o & p).sum()); m=int((o & ~p).sum()); f=int((~o & p).sum())
    return {"n":len(pares),"POD":h/(h+m) if h+m else np.nan,
            "FAR":f/(h+f) if h+f else np.nan,"aciertos":h,"omisiones":m,"falsas_alarmas":f}

def validar_lluvia_diaria(ideam: pd.DataFrame, sat: pd.DataFrame,
                          cobertura_minima: float = 75.) -> pd.DataFrame:
    """Pares diarios por fecha, conservando vacíos; filtra IDEAM por cobertura QC."""
    i = ideam[['fecha', 'mm', 'pct']].copy()
    i['fecha'] = pd.to_datetime(i.fecha, errors='coerce').dt.normalize()
    i['mm'] = pd.to_numeric(i.mm, errors='coerce')
    i['pct'] = pd.to_numeric(i.pct, errors='coerce')
    i = i.loc[i.pct.ge(cobertura_minima) & i.mm.ge(0)].dropna(subset=['fecha'])
    i = i.drop_duplicates('fecha', keep='last').rename(columns={'mm': 'IDEAM_mm'})
    s = sat.copy()
    s['fecha'] = pd.to_datetime(s.fecha, errors='coerce').dt.normalize()
    s = s.dropna(subset=['fecha']).drop_duplicates('fecha', keep='last')
    for nombre in s.columns.difference(['fecha']):
        s[nombre] = pd.to_numeric(s[nombre], errors='coerce')
    return i.merge(s, on='fecha', how='inner', validate='one_to_one').sort_values('fecha')

def indicadores_diarios(observado: pd.Series, estimado: pd.Series,
                         umbral: float = 1., min_kge: int = 12) -> dict:
    """Sesgo, RMSE, r, KGE2009, POD, FAR, CSI; solo pares simultáneos finitos."""
    z = pd.DataFrame({'o': pd.to_numeric(observado, errors='coerce'),
                      'e': pd.to_numeric(estimado, errors='coerce')})
    z = z.replace([np.inf, -np.inf], np.nan).dropna()
    z = z.loc[z.o.ge(0) & z.e.ge(0)]
    n = len(z)
    r = {'n': n, 'sesgo': np.nan, 'rmse': np.nan, 'pearson': np.nan,
         'kge': np.nan, 'POD': np.nan, 'FAR': np.nan, 'CSI': np.nan,
         'aciertos': 0, 'omisiones': 0, 'falsas_alarmas': 0}
    if not n:
        return r
    o, e = z.o.to_numpy(float), z.e.to_numpy(float)
    r['sesgo'] = float(np.mean(e-o))
    r['rmse'] = float(np.sqrt(np.mean((e-o)**2)))
    if n >= 3 and np.std(o) > 0 and np.std(e) > 0:
        r['pearson'] = float(np.corrcoef(o,e)[0,1])
        if n >= min_kge and np.mean(o) > 0 and np.mean(e) > 0:
            beta = np.mean(e)/np.mean(o)
            gamma = (np.std(e,ddof=1)/np.mean(e))/(np.std(o,ddof=1)/np.mean(o))
            r['kge'] = float(1-np.sqrt((r['pearson']-1)**2+(beta-1)**2+(gamma-1)**2))
    a, b = o >= umbral, e >= umbral
    h, m, f = int(np.sum(a&b)), int(np.sum(a&~b)), int(np.sum(~a&b))
    r.update(aciertos=h, omisiones=m, falsas_alarmas=f)
    r['POD'] = h/(h+m) if (h+m) else np.nan
    r['FAR'] = f/(h+f) if (h+f) else np.nan
    r['CSI'] = h/(h+m+f) if (h+m+f) else np.nan
    return r

def mensual_emparejado(pares: pd.DataFrame, producto: str,
                        minimo_dias: int = 20) -> pd.DataFrame:
    """Los acumulados satélite e IDEAM se suman solamente sobre los mismos días."""
    if pares.empty:
        return pd.DataFrame(columns=['mes', 'IDEAM_mm', 'Producto_mm', 'dias'])
    d = pares[['fecha','IDEAM_mm',producto]].copy()
    d[producto] = pd.to_numeric(d[producto], errors='coerce')
    d = d.dropna(subset=['IDEAM_mm', producto])
    d = d.loc[d[producto].ge(0)]
    d['mes'] = d.fecha.dt.to_period('M').dt.to_timestamp()
    t = d.groupby('mes').agg(IDEAM_mm=('IDEAM_mm','sum'),
                             Producto_mm=(producto,'sum'),dias=('fecha','nunique')).reset_index()
    return t.loc[t.dias.ge(minimo_dias)].reset_index(drop=True)

def series_pozos_publicas(niveles: pd.DataFrame) -> pd.DataFrame:
    """Tabla diaria del HTML público: conserva columnas de agua, no cotas absolutas."""
    t = niveles.copy()
    t['fecha'] = pd.to_datetime(t.fecha, errors='coerce').dt.normalize()
    for c in ['natural','max_diario','frac_bombeo','frac_seco']:
        if c not in t: t[c] = np.nan
        t[c] = pd.to_numeric(t[c],errors='coerce')
    return t.dropna(subset=['fecha']).sort_values(['pozo','fecha'])

def lag_lluvia_columna(pares: pd.DataFrame, variable_lluvia: str,
                        max_desfase: int=7, min_pares: int=25) -> pd.DataFrame:
    """r(P(t-k), delta columna(t)), sin unir días faltantes ni inferir causalidad."""
    if pares.empty:
        return pd.DataFrame(columns=['Desfase (días)','Pares','r'])
    d = pares[['fecha', 'natural',variable_lluvia]].copy().dropna(subset=['fecha'])
    d = d.drop_duplicates('fecha').set_index('fecha').sort_index()
    d = d.reindex(pd.date_range(d.index.min(),d.index.max(),freq='D'))
    d['delta'] = d.natural.diff()
    rows=[]
    for k in range(max_desfase+1):
        z = pd.concat([d[variable_lluvia].shift(k),d['delta']],axis=1).dropna()
        r = z.iloc[:,0].corr(z.iloc[:,1]) if len(z)>=min_pares and z.iloc[:,0].std()>0 and z.iloc[:,1].std()>0 else np.nan
        rows.append({'Desfase (días)':k,'Pares':len(z),'r':r})
    return pd.DataFrame(rows)

def anual_minimos(grace: pd.DataFrame, rio: pd.DataFrame) -> pd.DataFrame:
    """Mínimos observados por año y conteo de meses con dato, sin años incompletos disfrazados."""
    g=grace[['mes','gwsa_cm']].copy()
    g['mes']=pd.to_datetime(g.mes,errors='coerce')
    g['gwsa_cm']=pd.to_numeric(g.gwsa_cm,errors='coerce')
    g['año']=g.mes.dt.year
    ga=g.groupby('año').agg(gwsa_min_cm=('gwsa_cm','min'),meses_grace=('gwsa_cm','count')).reset_index()
    ri=rio[['mes','nivel_m']].copy();ri['mes']=pd.to_datetime(ri.mes,errors='coerce')
    ri['nivel_m']=pd.to_numeric(ri.nivel_m,errors='coerce');ri['año']=ri.mes.dt.year
    ri['mes_num']=ri.mes.dt.month
    rea=ri.groupby('año').agg(rio_min_m=('nivel_m','min'),meses_rio=('nivel_m','count')).reset_index()
    seca=ri.loc[ri.mes_num.isin([8,9,10])].groupby('año')['nivel_m'].count().rename('meses_rio_ago_oct').reset_index()
    return ga.merge(rea,on='año',how='outer').merge(seca,on='año',how='left').sort_values('año')

def coordenadas_piper(t: pd.DataFrame) -> pd.DataFrame:
    """Proyección Piper estándar desde porcentajes de carga ya publicados.

    Triángulos de cationes (Ca/Mg/Na+K) y aniones (HCO3/SO4/Cl),
    y rombo de familias Ca+Mg/Na+K frente a HCO3/Cl+SO4.
    Solo para muestras cuyo vector iónico público está completo.
    """
    cols=['cat_ca_pct','cat_mg_pct','cat_nak_pct',
          'an_hco3_pct','an_so4_pct','an_cl_pct']
    z=t.copy()
    for c in cols:z[c]=pd.to_numeric(z[c],errors='coerce')
    z=z.dropna(subset=cols).copy()
    for fila in [('cat_ca_pct','cat_mg_pct','cat_nak_pct'),
                 ('an_hco3_pct','an_so4_pct','an_cl_pct')]:
        total=z[list(fila)].sum(axis=1)
        z=z.loc[total.between(98,102)].copy()
    if z.empty:return z
    h=np.sqrt(3)/2
    ca,mg,nak=(z[c]/100 for c in cols[:3])
    hco3,so4,cl=(z[c]/100 for c in cols[3:])
    z['cat_x']=0.5*mg+nak
    z['cat_y']=h*mg
    z['an_x']=2+0.5*so4+cl
    z['an_y']=h*so4
    # El rombo crece hacia arriba al aumentar las fracciones de cationes
    # alcalinos y aniones de ácidos fuertes.
    fuertes=so4+cl
    z['diam_x']=1.5+0.55*(nak-fuertes)
    z['diam_y']=0.89+0.82*(nak+fuertes)/2
    return z
