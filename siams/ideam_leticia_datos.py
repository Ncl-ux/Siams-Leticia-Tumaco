"""Lectura y estadística verificable de precipitación mensual DHIME — Leticia.

No rellena meses faltantes, no anualiza periodos incompletos ni mezcla estaciones.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_IDEAM_LETICIA = (
    RAIZ / "data" / "raw" / "ideam" / "leticia" / "precipitacion_mensual_dhime.csv"
)
COLUMNAS = (
    "CodigoEstacion", "NombreEstacion", "Variable", "Parametro",
    "Fecha", "Unidad", "Valor", "NivelAprobacion",
)
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def leer_dhime(ruta: Path | str = ARCHIVO_IDEAM_LETICIA) -> pd.DataFrame:
    """Devuelve observaciones mensuales válidas sin alterar el CSV de origen.

    Un valor 0 es posible en precipitación: NO se considera faltante.
    Registros repetidos de la misma estación/mes provocan error para evitar doble suma.
    """
    ruta = Path(ruta)
    original = pd.read_csv(ruta, encoding="utf-8-sig", dtype={"CodigoEstacion": str})
    faltantes = set(COLUMNAS).difference(original.columns)
    if faltantes:
        raise ValueError("Al archivo DHIME le faltan columnas: " + ", ".join(sorted(faltantes)))
    df = original.loc[:, COLUMNAS].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    # Acepta tanto notación decimal con punto como con coma.
    df["Valor"] = pd.to_numeric(
        df["Valor"].astype(str).str.strip().str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["CodigoEstacion"] = df["CodigoEstacion"].astype(str).str.strip()
    if df["Fecha"].isna().any() or df["Valor"].isna().any():
        raise ValueError("Existen fechas o valores de precipitación inválidos; revisar el CSV.")
    if (df["Valor"] < 0).any():
        raise ValueError("Existen precipitaciones mensuales negativas; revisar el CSV.")
    if not df["Unidad"].astype(str).str.strip().str.lower().eq("mm").all():
        raise ValueError("El archivo debe contener exclusivamente precipitación en mm.")
    if not df["Parametro"].astype(str).str.contains("total mensual", case=False, na=False).all():
        raise ValueError("Hay parámetros distintos a precipitación total mensual.")
    df["Anio"] = df["Fecha"].dt.year.astype(int)
    df["Mes"] = df["Fecha"].dt.month.astype(int)
    dup = df.duplicated(subset=["CodigoEstacion", "Anio", "Mes"], keep=False)
    if dup.any():
        raise ValueError(f"Hay {int(dup.sum())} filas que comparten estación y mes: revisar duplicados.")
    return df.sort_values(["CodigoEstacion", "Fecha"]).reset_index(drop=True)


def catalogo_estaciones(df: pd.DataFrame) -> pd.DataFrame:
    """Cobertura relativa a cada intervalo observado; no al periodo global."""
    salida = []
    for codigo, g in df.groupby("CodigoEstacion", sort=True):
        minimo, maximo = g["Fecha"].min(), g["Fecha"].max()
        meses_posibles = len(pd.period_range(minimo.to_period("M"), maximo.to_period("M"), freq="M"))
        salida.append({
            "CodigoEstacion": codigo,
            "NombreEstacion": str(g["NombreEstacion"].iloc[0]).split(" [")[0].title(),
            "PrimeraFecha": minimo,
            "UltimaFecha": maximo,
            "Registros": len(g),
            "MesesPosibles": meses_posibles,
            "CoberturaPct": 100 * len(g) / meses_posibles,
        })
    return pd.DataFrame(salida).sort_values("Registros", ascending=False).reset_index(drop=True)


def tabla_anual(df_estacion: pd.DataFrame) -> pd.DataFrame:
    """Precipitación acumulada observada; solo 12 meses = total anual completo."""
    tabla = (
        df_estacion.groupby("Anio", as_index=False)
        .agg(Meses=("Mes", "nunique"), Precipitacion_mm=("Valor", "sum"))
    )
    tabla["Completo"] = tabla["Meses"].eq(12)
    return tabla.sort_values("Anio").reset_index(drop=True)


def climatologia_mensual(
    df_estacion: pd.DataFrame, inicio: int = 1990, fin: int = 2016,
    solo_anios_completos: bool = True,
) -> tuple[pd.DataFrame, list[int]]:
    """Promedio por mes de años completos; evita sesgos por meses ausentes."""
    rango = df_estacion[df_estacion["Anio"].between(inicio, fin)].copy()
    if solo_anios_completos:
        conteos = rango.groupby("Anio")["Mes"].nunique()
        permitidos = conteos[conteos.eq(12)].index.tolist()
        rango = rango[rango["Anio"].isin(permitidos)]
    else:
        permitidos = sorted(rango["Anio"].unique().tolist())
    media = rango.groupby("Mes")["Valor"].mean().reindex(range(1, 13))
    return pd.DataFrame({"Mes": range(1, 13), "Media_mm": media.to_numpy()}), permitidos


def ult_anio_completo(df_estacion: pd.DataFrame) -> int | None:
    tabla = tabla_anual(df_estacion)
    completa = tabla.loc[tabla["Completo"], "Anio"]
    return int(completa.max()) if not completa.empty else None


def serie_mensual_anio(df_estacion: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Doce posiciones, con NaN para meses faltantes, sin interpolación."""
    valores = df_estacion.loc[df_estacion["Anio"].eq(anio)].set_index("Mes")["Valor"]
    return pd.DataFrame({"Mes": range(1, 13), "Valor": valores.reindex(range(1, 13)).to_numpy()})


def matriz_calendario(df_estacion: pd.DataFrame) -> pd.DataFrame:
    """Años x meses; mantiene años y meses sin observaciones como NaN."""
    minimo, maximo = int(df_estacion["Anio"].min()), int(df_estacion["Anio"].max())
    tabla = df_estacion.pivot(index="Anio", columns="Mes", values="Valor")
    return tabla.reindex(index=range(minimo, maximo + 1), columns=range(1, 13))


def resumen_registros(df: pd.DataFrame) -> dict:
    estaciones = catalogo_estaciones(df)
    return {
        "registros": len(df),
        "estaciones": len(estaciones),
        "anio_min": int(df["Anio"].min()),
        "anio_max": int(df["Anio"].max()),
        "niveles_aprobacion": sorted(df["NivelAprobacion"].dropna().unique().tolist()),
    }
