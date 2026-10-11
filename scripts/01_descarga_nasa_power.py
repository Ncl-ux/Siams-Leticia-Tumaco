"""Descarga NASA POWER diario para una sede y arma el Excel procesado de SIAMS.

Reconstrucción del procesamiento de los archivos ``NASA_POWER_<SEDE>_FINAL*.xlsx``
(la revisión, observación 3.3.a, señaló que no estaba en el repositorio).
Se verificó con Tumaco (1992-01-01 a 2026-07-31): los valores diarios
descargados coinciden con la hoja ``Datos_diarios`` del Excel original
(ver ``tests/test_datos.py`` y CAMBIOS.md). Para las otras sedes las
coordenadas exactas usadas en la descarga original no quedaron registradas:
se usan las de ``TERRITORIOS`` en app.py (por confirmar).

Parámetros de la consulta (API POWER v2, comunidad AG, hora solar local LST):
PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, RH2M, WS2M, PS, ALLSKY_SFC_SW_DWN.
Unidades que declara la API: mm/day, C, %, m/s, kPa, MJ/m^2/day.

Uso:
    python scripts/01_descarga_nasa_power.py --sede tumaco --inicio 1992-01-01 --fin 2026-07-31
    python scripts/01_descarga_nasa_power.py --sede leticia --inicio 2000-01-01 --fin 2026-07-31 --salida data/processed/
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from siams.unidades import DICCIONARIO_NASA  # noqa: E402

API = "https://power.larc.nasa.gov/api/temporal/daily/point"
COMUNIDAD = "AG"

PARAMETROS = {
    "PRECTOTCORR": "precipitacion_mm_dia",
    "T2M": "temperatura_media_C",
    "T2M_MAX": "temperatura_maxima_C",
    "T2M_MIN": "temperatura_minima_C",
    "RH2M": "humedad_relativa_pct",
    "WS2M": "viento_2m_m_s",
    "PS": "presion_superficie_kPa",
    "ALLSKY_SFC_SW_DWN": "radiacion_solar_MJ_m2_dia",
}

# Coordenadas de referencia de cada sede (copiadas de TERRITORIOS en app.py).
SEDES = {
    "leticia": (-4.193717, -69.941001),
    "tumaco": (1.610206, -78.720520),
    "medellin": (6.260650, -75.579592),
    "san_andres": (12.536552, -81.707935),
    "arauca": (7.012222763876252, -70.74338825990411),
    "la_paz": (10.390218033322455, -73.20038917337925),
}


def descargar(lat: float, lon: float, inicio: str, fin: str) -> tuple[pd.DataFrame, dict]:
    """Devuelve el DataFrame diario y el encabezado JSON de la API."""
    url = (
        f"{API}?parameters={','.join(PARAMETROS)}&community={COMUNIDAD}"
        f"&longitude={lon}&latitude={lat}"
        f"&start={inicio.replace('-', '')}&end={fin.replace('-', '')}&format=JSON"
    )
    with urllib.request.urlopen(url, timeout=300) as resp:
        datos = json.load(resp)
    p = datos["properties"]["parameter"]
    df = pd.DataFrame({PARAMETROS[k]: pd.Series(v) for k, v in p.items()})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999.0, float("nan")).sort_index()
    df.index.name = "fecha"
    meta = {"url": url, "header": datos.get("header", {}), "parameters": datos.get("parameters", {})}
    return df.reset_index(), meta


def armar_hojas(diario: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Hojas con la misma estructura del Excel original y nombres de columna corregidos."""
    d = diario.set_index("fecha")
    p = d["precipitacion_mm_dia"]
    hojas: dict[str, pd.DataFrame] = {"Datos_diarios": diario}
    hojas["Resumen_estadistico"] = d.describe().T
    hojas["Indicadores"] = pd.DataFrame({
        "Indicador": [
            "Fecha inicial", "Fecha final", "Número de días descargados",
            "Días válidos de precipitación", "Días con precipitación > 0 mm",
            "Precipitación diaria máxima [mm/día]", "Temperatura media del periodo [°C]",
            "Humedad relativa media [%]", "Velocidad media del viento [m/s]",
        ],
        "Valor": [
            d.index.min(), d.index.max(), len(d), int(p.notna().sum()), int((p > 0).sum()),
            p.max(), d["temperatura_media_C"].mean(), d["humedad_relativa_pct"].mean(),
            d["viento_2m_m_s"].mean(),
        ],
    })
    pm = p.resample("MS").sum(min_count=1).rename("precipitacion_mm_mes")
    hojas["P_mensual"] = pm.reset_index()
    pa = p.resample("YS").sum(min_count=1).rename("precipitacion_mm_anio").reset_index()
    pa["anio"] = pa["fecha"].dt.year
    pa["dias_con_dato"] = p.resample("YS").count().values  # nuevo: permite descartar años incompletos
    hojas["P_anual"] = pa
    hojas["Regimen_P"] = pm.groupby(pm.index.month).mean().rename_axis("mes").reset_index()
    temps = ["temperatura_media_C", "temperatura_maxima_C", "temperatura_minima_C"]
    tm = d[temps].resample("MS").mean()
    hojas["T_mensual"] = tm.reset_index()
    hojas["Regimen_T"] = tm.groupby(tm.index.month).mean().rename_axis("mes").reset_index()
    for hoja, col in [("HR_mensual", "humedad_relativa_pct"), ("Viento_mensual", "viento_2m_m_s"),
                      ("Presion_mensual", "presion_superficie_kPa"),
                      ("Radiacion_mensual", "radiacion_solar_MJ_m2_dia")]:
        hojas[hoja] = d[col].resample("MS").mean().reset_index()
    hr = d["humedad_relativa_pct"].resample("MS").mean()
    hojas["Regimen_HR"] = hr.groupby(hr.index.month).mean().rename_axis("mes").reset_index()
    hojas["Climatologia_mensual"] = d.groupby(d.index.month).mean().rename_axis("mes").reset_index()
    hojas["Diccionario"] = pd.DataFrame(DICCIONARIO_NASA, columns=["columna", "descripcion", "unidad", "fuente"])
    return hojas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sede", required=True, choices=sorted(SEDES))
    ap.add_argument("--inicio", default="2000-01-01")
    ap.add_argument("--fin", default="2026-07-31")
    ap.add_argument("--salida", default=str(RAIZ / "data" / "processed"))
    a = ap.parse_args()
    lat, lon = SEDES[a.sede]
    diario, meta = descargar(lat, lon, a.inicio, a.fin)
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    nombre = f"nasa_power_{a.sede}_{a.inicio[:4]}-{a.fin[:4]}_v1"
    with pd.ExcelWriter(salida / f"{nombre}.xlsx") as w:
        for hoja, df in armar_hojas(diario).items():
            df.to_excel(w, sheet_name=hoja, index=(hoja == "Resumen_estadistico"))
    (salida / f"{nombre}.consulta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito {salida / (nombre + '.xlsx')} ({len(diario)} días)")


if __name__ == "__main__":
    main()
