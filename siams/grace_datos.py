"""Entrada a datos GRACE/Leticia. Fuentes y rutas; no se modifican valores originales.

Los CSV públicos permitidos son los derivados del HTML público del explorador.
No se leen sondeos privados desde este módulo.
"""
from __future__ import annotations
from pathlib import Path
import calendar
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed" / "observatorio_leticia"
ACTUALIZACION = RAIZ / "data" / "processed" / "actualizacion"
DATOS_PUBLICOS = DATOS / "explorador_publico"
RUTA = DATOS / "ana_ideam_rio_diario_publico.csv"



def leer_csv_seguro(ruta: Path, columnas: set[str]) -> pd.DataFrame:
    """Admite únicamente una ruta seleccionada por el llamador (no entrada web)."""
    if not ruta.is_file():
        return pd.DataFrame()
    datos = pd.read_csv(ruta, encoding="utf-8-sig", low_memory=False)
    if not columnas.issubset(datos.columns):
        faltan = sorted(columnas.difference(datos.columns))
        raise ValueError(f"Faltan columnas en {ruta.name}: {', '.join(faltan)}")
    return datos


def _mes(df: pd.DataFrame, fecha: str, valor: str, salida: str) -> pd.DataFrame:
    if not {fecha, valor}.issubset(df.columns):
        raise ValueError(f"Columnas faltantes: {fecha}, {valor}")
    s = pd.DataFrame({
        "mes": pd.to_datetime(df[fecha], errors="coerce").dt.to_period("M").dt.to_timestamp(),
        salida: pd.to_numeric(df[valor], errors="coerce"),
    }).dropna(subset=["mes"])
    if s.mes.duplicated().any():
        raise ValueError(f"Meses duplicados en {salida}; no se agregan sin justificar")
    return s

def cargar_validacion(estacion: str = "48015050") -> pd.DataFrame:
    """Usa estación 48015050, coincidente con píxel de serie 'Leticia'.

    La 48015040 requiere extraer su propio píxel de los NetCDF y no se debe
    comparar contra la serie de la sede como si estuviera en el mismo lugar.
    """
    ideam = DATOS / "ideam_precip_mensual_qc.csv"
    chirps3 = ACTUALIZACION / "chirps_leticia.csv"
    chirps2 = DATOS / "chirps_v2_leticia_mensual.csv"
    imerg = DATOS / "imerg_final_leticia_mensual.csv"
    nasa = ACTUALIZACION / "nasa_power_leticia.csv"
    archivos = [ideam, chirps3, chirps2, imerg, nasa]
    faltantes = [p.name for p in archivos if not p.is_file()]
    if faltantes:
        raise FileNotFoundError(", ".join(faltantes))
    df = pd.read_csv(ideam, encoding="utf-8-sig")
    df = df.loc[df.estacion.astype(str).str.lstrip("0").eq(str(estacion).lstrip("0"))].copy()
    # 'completo' en CSV puede llegar como bool o como cadena.
    df = df.loc[df["completo"].astype(str).str.lower().eq("true")].copy()
    obs = _mes(df, "mes", "precip_mm_dias_validos", "IDEAM_mm_mes")
    fuentes = [
        (_mes(pd.read_csv(chirps3), "fecha", "precipitacion_mm_mes", "CHIRPS_v3_mm_mes")),
        (_mes(pd.read_csv(chirps2), "month", "Leticia", "CHIRPS_v2_mm_mes")),
        (_mes(pd.read_csv(imerg), "month", "Leticia", "IMERG_Final_V07_mm_mes")),
    ]
    # NASA POWER: días con datos >=90 % del mes calendario, nunca sumar meses
    # incompletos como si fuesen totales mensuales válidos.
    nd = pd.read_csv(nasa, usecols=['fecha','precipitacion_mm_dia'])
    nd['fecha']=pd.to_datetime(nd['fecha'],errors='coerce').dt.normalize()
    nd['precipitacion_mm_dia']=pd.to_numeric(nd.precipitacion_mm_dia,errors='coerce')
    nd=nd.dropna(subset=['fecha']).drop_duplicates('fecha',keep='last')
    nd['mes']=nd.fecha.dt.to_period('M').dt.to_timestamp()
    nam=nd.groupby('mes').precipitacion_mm_dia.agg(['sum','count']).reset_index()
    esperado=nam.mes.apply(lambda x:calendar.monthrange(x.year,x.month)[1])
    nam['NASA_POWER_mm_mes']=nam['sum'].where(nam['count'] >= np.ceil(0.9*esperado))
    fuentes.append(nam[['mes','NASA_POWER_mm_mes']])
    for f in fuentes:
        obs = obs.merge(f, on="mes", how="left", validate="one_to_one")
    return obs.sort_values("mes").reset_index(drop=True)


def cargar(nombre: str, raiz: Path | None = None) -> pd.DataFrame:
    """Cargar un CSV concreto del paquete público; nombre fijo sin recorrido de rutas."""
    permitidos = {'rio_diario.csv', 'ana_diario.csv', 'sat_mensual.csv', 'grace.csv',
                  'rio_mensual.csv', 'lluvia_ideam_diaria.csv', 'lluvia_satelital_diaria.csv',
                  'transductores_diarios_publicos.csv', 'pozo_unal_manual.csv',
                  'calidad_muestras_publicas.csv', 'sitios_publicos.csv'}
    if nombre not in permitidos:
        raise ValueError('Archivo no autorizado en el paquete público')
    ruta = (raiz or DATOS_PUBLICOS) / nombre
    if not ruta.is_file():
        return pd.DataFrame()
    return pd.read_csv(ruta, encoding='utf-8-sig', low_memory=False)


def cargar_y_comparar(ruta: Path = RUTA) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    requeridas = {"fecha", "ana_cota_m", "ideam_nivel_m"}
    if not requeridas.issubset(df.columns):
        raise ValueError("Faltan columnas de ANA/IDEAM")
    df["fecha"] = pd.to_datetime(df.fecha, errors="coerce")
    if df.fecha.isna().any() or df.fecha.duplicated().any():
        raise ValueError("Las fechas de ANA/IDEAM deben ser únicas y válidas")
    for c in ("ana_cota_m", "ideam_nivel_m"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("fecha")
    comunes = df.dropna(subset=["ana_cota_m", "ideam_nivel_m"]).copy()
    if len(comunes) < 30:
        return comunes, {"n": len(comunes), "r_pearson": np.nan}
    # Cada estación se centra en su propia media del intervalo común.
    comunes["ANA_cambio_relativo_m"] = comunes.ana_cota_m - comunes.ana_cota_m.mean()
    comunes["IDEAM_cambio_relativo_m"] = comunes.ideam_nivel_m - comunes.ideam_nivel_m.mean()
    corr = comunes[["ana_cota_m", "ideam_nivel_m"]].corr().iloc[0, 1]
    return comunes, {"n": len(comunes), "r_pearson": float(corr),
                     "inicio": comunes.fecha.min(), "fin": comunes.fecha.max()}
