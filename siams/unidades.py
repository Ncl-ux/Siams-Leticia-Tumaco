"""Unidades y nombres de columnas de los Excel procesados de SIAMS.

Corrección de la revisión (3.2.c): la radiación de NASA POWER (parámetro
ALLSKY_SFC_SW_DWN de la comunidad agroclimática ``AG``) viene en MJ/m²/día,
no en kWh/m²/día. Los valores NO se modifican; solo se corrige el rótulo.
1 kWh = 3,6 MJ.
"""

from __future__ import annotations

import pandas as pd

MJ_POR_KWH = 3.6

UNIDAD_RADIACION = "MJ/m²/día"


def kwh_a_mj(valor):
    """kWh/m²/día → MJ/m²/día."""
    return valor * MJ_POR_KWH


def mj_a_kwh(valor):
    """MJ/m²/día → kWh/m²/día."""
    return valor / MJ_POR_KWH


# Rango físico plausible de radiación solar diaria en superficie (trópico).
# El tope de la atmósfera en el ecuador ronda 37–38 MJ/m²/día (≈ 10,5 kWh/m²/día).
RANGO_RADIACION_MJ = (0.0, 38.0)
RANGO_RADIACION_KWH = (0.0, 38.0 / MJ_POR_KWH)


def radiacion_plausible(serie, unidad: str = "MJ") -> bool:
    """True si todos los valores caen en el rango físico de la unidad indicada."""
    s = pd.to_numeric(pd.Series(serie), errors="coerce").dropna()
    bajo, alto = RANGO_RADIACION_MJ if unidad.upper().startswith("MJ") else RANGO_RADIACION_KWH
    return bool(((s >= bajo) & (s <= alto)).all())


def unidad_radiacion_probable(serie) -> str:
    """Sugiere la unidad según la media: > 10 solo es posible en MJ/m²/día."""
    s = pd.to_numeric(pd.Series(serie), errors="coerce").dropna()
    if s.empty:
        return "desconocida"
    return "MJ/m²/día" if s.mean() > 10.5 else "kWh/m²/día"


# Nombres antiguos → nombres corregidos, por hoja. Se usan al leer los Excel
# para que la app funcione con los archivos viejos y con los corregidos.
COLUMNA_RADIACION_ANTIGUA = "radiacion_solar_kWh_m2_dia"
COLUMNA_RADIACION = "radiacion_solar_MJ_m2_dia"

RENOMBRES_NASA_POR_HOJA = {
    "Datos_diarios": {COLUMNA_RADIACION_ANTIGUA: COLUMNA_RADIACION},
    "Climatologia_mensual": {COLUMNA_RADIACION_ANTIGUA: COLUMNA_RADIACION},
    "Radiacion_mensual": {COLUMNA_RADIACION_ANTIGUA: COLUMNA_RADIACION},
    "P_mensual": {"precipitacion_mm_dia": "precipitacion_mm_mes"},
    "Regimen_P": {"precipitacion_mm_dia": "precipitacion_mm_mes"},
    "P_anual": {"precipitacion_mm_dia": "precipitacion_mm_anio"},
}

RENOMBRES_IDEAM_POR_HOJA = {
    "Datos_diarios": {"precipitacion": "precipitacion_mm_dia"},
    "P_diaria": {"precipitacion": "precipitacion_mm_dia"},
    "P_mensual": {"precipitacion": "precipitacion_mm_mes"},
    "P_anual": {"precipitacion": "precipitacion_mm_anio"},
    "Regimen_P": {"precipitacion": "precipitacion_mm_mes"},
}

# Filas de la hoja Resumen_estadistico (primera columna) que nombran variables.
RENOMBRES_FILAS_RESUMEN = {COLUMNA_RADIACION_ANTIGUA: COLUMNA_RADIACION}


def normalizar_columnas_nasa(df: pd.DataFrame, hoja: str) -> pd.DataFrame:
    """Aplica los nombres corregidos a una hoja NASA POWER (idempotente)."""
    return df.rename(columns=RENOMBRES_NASA_POR_HOJA.get(hoja, {}))


def normalizar_columnas_ideam(df: pd.DataFrame, hoja: str) -> pd.DataFrame:
    """Aplica los nombres corregidos a una hoja IDEAM procesada (idempotente)."""
    return df.rename(columns=RENOMBRES_IDEAM_POR_HOJA.get(hoja, {}))


# Diccionario de variables (se escribe como hoja ``Diccionario`` en cada Excel).
DICCIONARIO_NASA = [
    ("fecha", "Fecha (día calendario; NASA POWER usa días en hora local solar/UTC según la API: por confirmar)", "AAAA-MM-DD", "NASA POWER (diario)"),
    ("precipitacion_mm_dia", "Precipitación diaria corregida (PRECTOTCORR)", "mm/día", "NASA POWER"),
    ("precipitacion_mm_mes", "Precipitación total del mes (P_mensual) o total mensual climatológico (Regimen_P)", "mm/mes", "Agregación de precipitacion_mm_dia"),
    ("precipitacion_mm_anio", "Precipitación total del año", "mm/año", "Agregación de precipitacion_mm_dia"),
    ("temperatura_media_C", "Temperatura del aire a 2 m, media diaria (T2M)", "°C", "NASA POWER"),
    ("temperatura_maxima_C", "Temperatura máxima a 2 m (T2M_MAX)", "°C", "NASA POWER"),
    ("temperatura_minima_C", "Temperatura mínima a 2 m (T2M_MIN)", "°C", "NASA POWER"),
    ("humedad_relativa_pct", "Humedad relativa a 2 m (RH2M)", "%", "NASA POWER"),
    ("viento_2m_m_s", "Velocidad del viento a 2 m (WS2M)", "m/s", "NASA POWER"),
    ("presion_superficie_kPa", "Presión en superficie (PS)", "kPa", "NASA POWER"),
    ("radiacion_solar_MJ_m2_dia", "Radiación solar global en superficie, cielo real (ALLSKY_SFC_SW_DWN). Antes rotulada por error kWh/m²/día; 1 kWh = 3,6 MJ", "MJ/m²/día", "NASA POWER, comunidad AG (inferida por el rango de valores)"),
]

DICCIONARIO_IDEAM = [
    ("fecha", "Fecha del día pluviométrico IDEAM (ventana de 24 h que no coincide con el día calendario; ver metadatos DHIME)", "AAAA-MM-DD", "IDEAM – DHIME"),
    ("precipitacion_mm_dia", "Precipitación diaria (día pluviométrico)", "mm/día", "IDEAM – DHIME"),
    ("precipitacion_mm_mes", "Precipitación total del mes (P_mensual) o total mensual climatológico (Regimen_P)", "mm/mes", "Agregación"),
    ("precipitacion_mm_anio", "Precipitación total del año (incluye años incompletos: revisar Control_faltantes)", "mm/año", "Agregación"),
    ("temperatura_media / _maxima / _minima", "Temperatura del aire", "°C", "IDEAM – DHIME"),
    ("humedad_relativa", "Humedad relativa media", "%", "IDEAM – DHIME"),
]
