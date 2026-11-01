"""Actualización semanal (GitHub Actions) de series abiertas por sede.

Fuentes activas:
  * NASA POWER diario (API v2, comunidad AG)           -> nasa_power_<sede>.csv
  * CHIRPS v3.0 mensual (UCSB-CHC, lectura puntual)     -> chirps_<sede>.csv
  * IDEAM en datos.gov.co (Socrata), verificados 2026-11-01:
      s54a-sgyg Precipitación, sbwg-7ju4 Temperatura Ambiente del Aire,
      bdmn-sqnh Nivel Instantáneo del Río               -> ideam_<sede>.csv
Fuentes desactivadas (documentadas, requieren credenciales o procesamiento pesado):
  * GRACE/GRACE-FO + GLDAS (scripts/06_gwsa_grace_gldas_extendido.py; Earthdata login)
  * ERA5-Land (Copernicus CDS; requiere clave CDSAPI)

Cada archivo es incremental: se descargan solo las fechas posteriores al último registro
(con una ventana de reproceso de 60 días para capturar correcciones de la fuente).
Escribe data/processed/actualizacion/metadatos.json con la fecha de 'última actualización'.

Uso:  python scripts/12_actualizacion_semanal.py [--fuentes nasa_power,chirps,ideam] [--sedes leticia,tumaco]
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "processed" / "actualizacion"
REPROCESO_DIAS = 60

SEDES = {  # mismas coordenadas de referencia de scripts/01_descarga_nasa_power.py
    "leticia": (-4.193717, -69.941001),
    "tumaco": (1.610206, -78.720520),
    "arauca": (7.012222763876252, -70.74338825990411),
    "la_paz": (10.390218033322455, -73.20038917337925),
    "bogota": (4.638193, -74.084046),
}
INICIO = {"nasa_power": "1981-01-01", "chirps": "1981-01-01", "ideam": "2026-01-01"}  # carga inicial corta: Socrata corta consultas agregadas largas

# Estaciones automáticas IDEAM con datos en datos.gov.co (consultado 2026-11-01).
ESTACIONES_IDEAM = {
    "leticia": {"precipitacion": "0048015050", "temperatura": "0048015050"},
    "tumaco": {"precipitacion": "0051039010", "temperatura": "0051039010", "nivel_rio": "0051027060"},
    "arauca": {"precipitacion": "3706500109", "temperatura": "3706500109"},
}
SOCRATA = {"precipitacion": "s54a-sgyg", "temperatura": "sbwg-7ju4", "nivel_rio": "bdmn-sqnh"}
AGREGADO = {"precipitacion": "sum(valorobservado)", "temperatura": "avg(valorobservado)", "nivel_rio": "avg(valorobservado)"}

NASA_PARAM = {"PRECTOTCORR": "precipitacion_mm_dia", "T2M": "temperatura_media_C",
              "T2M_MAX": "temperatura_maxima_C", "T2M_MIN": "temperatura_minima_C", "RH2M": "humedad_relativa_pct"}
CHIRPS_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/tifs/chirps-v3.0.{a:04d}.{m:02d}.tif"


def _json(url: str, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "SIAMS-UNAL/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def desde(archivo: Path, fuente: str) -> pd.Timestamp:
    if archivo.exists():
        f = pd.read_csv(archivo, usecols=["fecha"], parse_dates=["fecha"]).fecha.max()
        return max(pd.Timestamp(INICIO[fuente]), f - pd.Timedelta(days=REPROCESO_DIAS))
    return pd.Timestamp(INICIO[fuente])


def combinar(archivo: Path, nuevo: pd.DataFrame, claves=("fecha",)) -> int:
    if archivo.exists():
        viejo = pd.read_csv(archivo, parse_dates=["fecha"])
        nuevo = pd.concat([viejo, nuevo]).drop_duplicates(list(claves), keep="last")
    nuevo = nuevo.sort_values(list(claves))
    nuevo.to_csv(archivo, index=False, date_format="%Y-%m-%d")
    return len(nuevo)


def nasa_power(sede, lat, lon, hoy):
    arch = SALIDA / f"nasa_power_{sede}.csv"
    ini = desde(arch, "nasa_power")
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=" + ",".join(NASA_PARAM)
           + f"&community=AG&longitude={lon}&latitude={lat}&start={ini:%Y%m%d}&end={hoy:%Y%m%d}&format=JSON")
    p = _json(url)["properties"]["parameter"]
    df = pd.DataFrame({NASA_PARAM[k]: pd.Series(v) for k, v in p.items()}).replace(-999.0, float("nan"))
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.dropna(how="all").rename_axis("fecha").reset_index()
    return combinar(arch, df)


@functools.lru_cache(maxsize=None)
def _chirps_mes(a: int, m: int):
    """Lee el mes una sola vez para todas las sedes (lectura por rangos HTTP).

    Los GeoTIFF de CHIRPS v3.0 no traen geotransformación (GDAL ve la identidad):
    la malla es 0,05° de -180 a 180 E y de 60 N a -60 S (7200 × 2400), así que la
    celda se calcula a mano.
    """
    import time
    import warnings
    import rasterio
    from rasterio.windows import Window
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("GDAL_HTTP_TIMEOUT", "60")
    for intento in range(3):
        try:
            with warnings.catch_warnings(), rasterio.open("/vsicurl/" + CHIRPS_URL.format(a=a, m=m)) as r:
                warnings.simplefilter("ignore")
                assert (r.width, r.height) == (7200, 2400), "malla CHIRPS inesperada"
                out = {}
                for sede, (lat, lon) in SEDES.items():
                    col, fila = int((lon + 180) / 0.05), int((60 - lat) / 0.05)
                    out[sede] = float(r.read(1, window=Window(col, fila, 1, 1))[0, 0])
                return out
        except rasterio.errors.RasterioIOError:
            time.sleep(3 * (intento + 1))
    return None  # mes no publicado o no disponible (se cachea para no reintentar por cada sede)


def chirps(sede, lat, lon, hoy):
    arch = SALIDA / f"chirps_{sede}.csv"
    ini = desde(arch, "chirps").replace(day=1)
    meses = pd.date_range(ini, hoy, freq="MS")
    if arch.exists():  # rellena huecos de corridas anteriores (fallas transitorias del servidor)
        hechos = set(pd.read_csv(arch, parse_dates=["fecha"]).fecha)
        todos = pd.date_range(INICIO["chirps"], hoy, freq="MS")
        meses = pd.DatetimeIndex(sorted(set(meses) | {m for m in todos[:-2] if m not in hechos}))
    from concurrent.futures import ThreadPoolExecutor

    def _seguro(f):
        try:
            return _chirps_mes(f.year, f.month)
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=4) as ex:  # el lru_cache comparte los meses entre sedes
        list(ex.map(_seguro, meses))
    filas = []
    for f in meses:
        try:
            mes = _chirps_mes(f.year, f.month)
            if mes is None:
                continue
            v = mes[sede]
        except Exception:  # mes aún no publicado
            continue
        filas.append({"fecha": f, "precipitacion_mm_mes": None if v < 0 else round(v, 2)})
    return combinar(arch, pd.DataFrame(filas)) if filas else 0


def ideam(sede, hoy):
    if sede not in ESTACIONES_IDEAM:
        return 0
    arch = SALIDA / f"ideam_{sede}.csv"
    ini = desde(arch, "ideam")
    partes = []
    for var, est in ESTACIONES_IDEAM[sede].items():
        q = urllib.parse.urlencode({
            "$select": f"date_trunc_ymd(fechaobservacion) as fecha, {AGREGADO[var]} as valor, count(*) as n_obs, min(nombreestacion) as estacion",
            "$where": f"codigoestacion='{est}' and fechaobservacion >= '{ini:%Y-%m-%d}T00:00:00'",
            "$group": "fecha", "$order": "fecha", "$limit": 50000})
        d = pd.DataFrame(_json(f"https://www.datos.gov.co/resource/{SOCRATA[var]}.json?{q}"))
        if d.empty:
            continue
        d["variable"], d["codigoestacion"], d["dataset"] = var, est, SOCRATA[var]
        partes.append(d)
    if not partes:
        return 0
    df = pd.concat(partes)
    df["fecha"] = pd.to_datetime(df.fecha).dt.normalize()
    df["valor"] = pd.to_numeric(df.valor).round(3)
    return combinar(arch, df[["fecha", "variable", "valor", "n_obs", "codigoestacion", "estacion", "dataset"]],
                    claves=("fecha", "variable"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuentes", default="nasa_power,chirps,ideam")
    ap.add_argument("--sedes", default=",".join(SEDES))
    a = ap.parse_args(argv)
    SALIDA.mkdir(parents=True, exist_ok=True)
    hoy = pd.Timestamp(dt.date.today())
    metaf = SALIDA / "metadatos.json"
    meta = json.loads(metaf.read_text(encoding="utf-8")) if metaf.exists() else {"fuentes": {}}
    meta["desactivadas"] = {"grace_gldas": "Requiere Earthdata (scripts/06_*.py); se actualiza manualmente.",
                            "era5_land": "Requiere clave Copernicus CDS; no configurada."}
    errores = 0
    for fuente in a.fuentes.split(","):
        for sede in a.sedes.split(","):
            lat, lon = SEDES[sede]
            try:
                n = {"nasa_power": lambda: nasa_power(sede, lat, lon, hoy), "chirps": lambda: chirps(sede, lat, lon, hoy),
                     "ideam": lambda: ideam(sede, hoy)}[fuente]()
                estado = "ok"
            except Exception as e:  # una fuente caída no detiene las demás
                n, estado, errores = None, f"error: {e}"[:300], errores + 1
            meta["fuentes"].setdefault(fuente, {})[sede] = {"filas": n, "estado": estado,
                                                           "actualizado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            print(fuente, sede, n, estado, flush=True)
    meta["ultima_actualizacion"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    metaf.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if errores and errores == len(a.fuentes.split(",")) * len(a.sedes.split(",")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
