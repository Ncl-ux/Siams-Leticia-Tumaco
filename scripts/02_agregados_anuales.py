"""Agrega a escala anual las series diarias de los Excel procesados (NASA POWER e IDEAM).

Usa la misma regla que la app (``siams.estadistica.agregar_serie_anual``): un
año se conserva si tiene al menos el 75 % de los datos típicos por año. La
precipitación se suma (mm/año); las demás variables se promedian.

Salida: ``data/processed/anuales/<fuente>_<sede>_anual.csv`` con columnas
``anio, variable, unidad, valor, n_datos``.

Uso:
    python scripts/02_agregados_anuales.py
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from siams.estadistica import agregar_serie_anual  # noqa: E402

HIDRO = RAIZ / "Analisis Hidro"
SALIDA = RAIZ / "data" / "processed" / "anuales"

VARIABLES = {
    # columna: (variable, unidad anual, agregación)
    "precipitacion_mm_dia": ("precipitacion", "mm/año", "sum"),
    "temperatura_media_C": ("temperatura_media", "°C", "mean"),
    "temperatura_maxima_C": ("temperatura_maxima", "°C", "mean"),
    "temperatura_minima_C": ("temperatura_minima", "°C", "mean"),
    "humedad_relativa_pct": ("humedad_relativa", "%", "mean"),
    "viento_2m_m_s": ("viento_2m", "m/s", "mean"),
    "presion_superficie_kPa": ("presion_superficie", "kPa", "mean"),
    "radiacion_solar_MJ_m2_dia": ("radiacion_solar", "MJ/m²/día", "mean"),
    # IDEAM (Datos_diarios sin sufijo de unidad en temperatura y humedad)
    "temperatura_media": ("temperatura_media", "°C", "mean"),
    "temperatura_maxima": ("temperatura_maxima", "°C", "mean"),
    "temperatura_minima": ("temperatura_minima", "°C", "mean"),
    "humedad_relativa": ("humedad_relativa", "%", "mean"),
}


def _sede(nombre: str) -> str:
    base = unicodedata.normalize("NFKD", nombre)
    base = "".join(c for c in base if not unicodedata.combining(c)).lower()
    for token in ("nasa_power_", "analisis_hidrometeorologico_", "_final", " (2)", " (3)", ".xlsx"):
        base = base.replace(token, "")
    return base.strip().replace(" ", "_")


def procesar(ruta: Path) -> pd.DataFrame | None:
    xls = pd.ExcelFile(ruta)
    if "Datos_diarios" not in xls.sheet_names:
        return None
    d = pd.read_excel(ruta, sheet_name="Datos_diarios", parse_dates=["fecha"])
    filas = []
    for col, (var, unidad, agg) in VARIABLES.items():
        if col not in d.columns:
            continue
        anual = agregar_serie_anual(d.rename(columns={"fecha": "Fecha", col: "Valor"}), agg)
        for _, f in anual.iterrows():
            filas.append({"anio": int(f["Año"]), "variable": var, "unidad": unidad,
                          "valor": round(float(f["Valor"]), 4), "n_datos": int(f["N"])})
    return pd.DataFrame(filas)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    for ruta in sorted(HIDRO.glob("*.xlsx")):
        df = procesar(ruta)
        if df is None or df.empty:
            print(f"{ruta.name}: sin hoja Datos_diarios (se omite)")
            continue
        fuente = "nasa_power" if ruta.name.upper().startswith("NASA") else "ideam"
        destino = SALIDA / f"{fuente}_{_sede(ruta.name)}_anual.csv"
        df.to_csv(destino, index=False, encoding="utf-8")
        print(f"{ruta.name} → {destino.relative_to(RAIZ)} ({len(df)} filas)")


if __name__ == "__main__":
    main()
